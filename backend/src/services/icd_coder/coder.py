"""ICD编码推荐引擎

核心流程：
1. 输入诊断/手术文本 → 候选编码召回（数据库精确匹配+模糊匹配+拼音检索）
2. 候选编码排序（语义相似度+频率+上下文）
3. LLM辅助编码推荐
4. 编码校验（性别/年龄约束、主次诊断逻辑、排除规则）
"""

import logging
from dataclasses import dataclass
import json
from pathlib import Path
from sqlalchemy import select, or_
from src.models.database import async_session
from src.models.icd import ICDCode, ICDVersion

logger = logging.getLogger(__name__)


def _load_icd_map(filename: str) -> dict[str, tuple[str, str]]:
    """从统一的 JSON 数据文件加载 ICD 编码映射（keyword → (code, name)）。

    数据文件位于 src/data/，是合并了 coder/seed_icd/seed_data 三处后的唯一权威源。
    """
    data_path = Path(__file__).parent.parent.parent / "data" / filename
    if not data_path.exists():
        logger.warning(f"ICD data file not found: {data_path}")
        return {}
    with open(data_path, "r", encoding="utf-8") as f:
        entries = json.load(f)
    mapping: dict[str, tuple[str, str]] = {}
    for entry in entries:
        code = entry["code"]
        name = entry["name"]
        if name not in mapping:
            mapping[name] = (code, name)
        for alias in entry.get("aliases", []):
            if alias not in mapping:
                mapping[alias] = (code, name)
    return mapping


# 内置常用编码映射（数据库不可用时的fallback，数据来自 src/data/icd_*.json）
_DIAGNOSIS_MAP = _load_icd_map("icd_diagnoses.json")
_PROCEDURE_MAP = _load_icd_map("icd_procedures.json")


@dataclass
class ICDCandidate:
    code: str
    name: str
    category: str
    score: float
    semantic_score: float = 0.0
    freq_score: float = 0.0


@dataclass
class CodingResult:
    primary_diagnosis: ICDCandidate | None
    secondary_diagnoses: list[ICDCandidate]
    procedures: list[ICDCandidate]
    suggestions: list[ICDCandidate]
    confidence: float
    warnings: list[str]


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]


def _get_pinyin_initials(text: str) -> str:
    """获取文本的拼音首字母"""
    try:
        from pypinyin import lazy_pinyin
        return "".join(w[0] for w in lazy_pinyin(text) if w)
    except Exception as e:
        logger.debug(f"pypinyin unavailable, falling back to ascii filter: {e}")
        return "".join(c for c in text if c.isascii())


class ICDCoder:
    """ICD编码器 - 支持数据库查询、本地fallback、向量语义搜索"""

    VALIDATION_RULES: dict = {
        "symptom_as_primary": ["R00-R09", "R10-R19", "R50-R69"],
        "never_primary": ["Z37", "Z38", "Z39", "Z51.0", "Z51.1"],
    }

    def __init__(self):
        self._vector_engine = None
        self._vector_ready = False
        self._index_built = False
        # Prefix index: first 1-3 chars → list of (keyword, code, name, category)
        self._prefix_index: dict[str, list[tuple[str, str, str, str]]] = {}
        # Reverse index: keyword → (code, name, category) for exact lookup
        self._exact_index: dict[str, tuple[str, str, str]] = {}

    def _build_local_index(self):
        """Build prefix and exact match indices for O(1) local lookups"""
        if self._index_built:
            return
        all_entries = [
            *[(k, v[0], v[1], "诊断") for k, v in _DIAGNOSIS_MAP.items()],
            *[(k, v[0], v[1], "手术操作") for k, v in _PROCEDURE_MAP.items()],
        ]
        for keyword, code, name, cat in all_entries:
            self._exact_index[keyword] = (code, name, cat)
            for n in (1, 2, 3):
                prefix = keyword[:n]
                if prefix not in self._prefix_index:
                    self._prefix_index[prefix] = []
                self._prefix_index[prefix].append((keyword, code, name, cat))
        self._index_built = True

    def _ensure_vector_index(self):
        """懒加载语义搜索索引"""
        if self._vector_ready:
            return
        try:
            from src.services.vector_search import vector_search_engine
            # 构建文档列表：诊断 + 手术
            docs = []
            seen = set()
            for name, (code, full_name) in _DIAGNOSIS_MAP.items():
                key = code
                if key not in seen:
                    seen.add(key)
                    docs.append({"code": code, "name": full_name, "category": "诊断"})
            for name, (code, full_name) in _PROCEDURE_MAP.items():
                key = code
                if key not in seen:
                    seen.add(key)
                    docs.append({"code": code, "name": full_name, "category": "手术操作"})
            vector_search_engine.build_index(docs)
            self._vector_engine = vector_search_engine
            self._vector_ready = True
        except Exception as e:
            logger.warning(f"Vector index build failed, semantic search disabled: {e}")

    async def recommend(self, diagnosis_text: str, context: dict | None = None, use_llm: bool = True) -> list[ICDCandidate]:
        """根据诊断文本推荐ICD编码（DB → 本地映射 → 语义搜索 → LLM）"""
        text = diagnosis_text.strip()
        if not text:
            return []

        # 1. Database + local map merged search
        db_results = await self._db_search(text)
        local_results = self._local_search(text)

        # Merge, deduplicate by code, keep highest score
        merged: dict[str, ICDCandidate] = {}
        for c in db_results + local_results:
            if c.code not in merged or c.score > merged[c.code].score:
                merged[c.code] = c
        candidates = sorted(merged.values(), key=lambda c: c.score, reverse=True)
        # Filter out very low quality matches (raised from 0.5 to reduce noise)
        candidates = [c for c in candidates if c.score >= 0.58]

        if candidates:
            return await self._llm_rerank(text, candidates, context, use_llm)

        # 3. Semantic vector search
        self._ensure_vector_index()
        if self._vector_ready and self._vector_engine:
            try:
                vec_results = self._vector_engine.hybrid_search(text, top_k=5)
                if vec_results:
                    return [ICDCandidate(
                        code=r.code, name=r.name, category=r.category,
                        score=r.score,
                    ) for r in vec_results]
            except Exception as e:
                logger.warning(f"Vector search failed for '{text}': {e}")

        # 4. LLM-only recommendation
        if use_llm:
            try:
                from src.services.llm_engine import llm_engine
                suggestion = await llm_engine.code_recommend(
                    text, [],
                    context=json.dumps(context, ensure_ascii=False) if context else "",
                )
                if suggestion and suggestion.code:
                    return [ICDCandidate(
                        code=suggestion.code, name=suggestion.name,
                        category="诊断", score=suggestion.confidence,
                    )]
            except Exception as e:
                logger.warning(f"LLM-only recommendation failed for '{text}': {e}")

        return []

    async def _llm_rerank(self, text: str, candidates: list, context: dict | None, use_llm: bool) -> list[ICDCandidate]:
        """使用LLM对候选编码重排序"""
        if not use_llm or len(candidates) <= 1:
            return candidates

        try:
            from src.services.llm_engine import llm_engine
            import json as _json
            ctx_str = _json.dumps(context, ensure_ascii=False)[:1000] if context else ""
            suggestion = await llm_engine.code_recommend(text, candidates, ctx_str)
            if suggestion:
                # 将LLM推荐的结果移到第一位
                for i, c in enumerate(candidates):
                    if c.code == suggestion.code:
                        c.score = max(c.score, suggestion.confidence)
                        candidates.insert(0, candidates.pop(i))
                        break
        except Exception as e:
            logger.warning(f"LLM rerank failed for '{text}': {e}")

        return candidates

    async def _db_search(self, text: str) -> list[ICDCandidate]:
        """从数据库检索ICD编码"""
        try:
            async with async_session() as session:
                py = _get_pinyin_initials(text)
                conditions = [
                    ICDCode.name == text,
                    ICDCode.name.ilike(f"%{text}%"),
                    ICDCode.code == text,
                ]
                # Only use pinyin search for meaningful-length codes (>= 3 chars)
                if len(py) >= 3:
                    conditions.append(ICDCode.py_code.ilike(f"%{py}%"))
                query = select(ICDCode).where(or_(*conditions)).limit(20)

                result = await session.execute(query)
                rows = result.scalars().all()

                # Base condition → complication subcode mapping (for penalty)
                _BASE_TO_COMPLICATION: dict[str, list[str]] = {
                    "E11": ["E11.2", "E11.3", "E11.4", "E11.5", "E11.6", "E11.7"],
                    "E10": ["E10.2", "E10.3", "E10.4", "E10.5", "E10.6", "E10.7"],
                    "I10": ["I10.x00", "I10.x01", "I10.x02", "I10.x03"],
                }

                candidates = []
                for row in rows:
                    # Score: exact match > partial match with word boundary > generic LIKE
                    if row.name == text:
                        score = 1.0
                    elif text in row.name and len(text) >= 3:
                        # Penalize if the matched text is only part of a longer word
                        # e.g. "糖尿病" matching "糖尿病肾病" should get lower score
                        idx = row.name.find(text)
                        after = row.name[idx + len(text):] if idx + len(text) < len(row.name) else ""
                        if after and after[0] not in "，,、()）)） " and not after.startswith("伴"):
                            score = 0.58  # Sub-word match, likely noise (e.g. 糖尿病变 → 糖尿病肾病)
                        else:
                            score = 0.78
                    else:
                        score = 0.50

                    # Penalize pregnancy/obstetric codes when search text is unrelated
                    if row.code and row.code[0] == "O" and not any(kw in text for kw in
                            ("妊娠", "孕", "产", "流产", "分娩", "剖宫", "胎", "羊水", "产后", "宫缩")):
                        score -= 0.8
                    # Penalize complication subcodes when search text only matches base condition
                    for base_prefix, comp_prefixes in _BASE_TO_COMPLICATION.items():
                        if any(row.code.startswith(cp) for cp in comp_prefixes):
                            if text in row.name and not any(kw in text for kw in ("肾病", "视网膜", "神经", "足", "眼", "肾")):
                                score -= 0.30
                            break
                    cat = "手术操作" if row.version == ICDVersion.ICD9_CM3 else "诊断"
                    candidates.append(ICDCandidate(
                        code=row.code, name=row.name, category=cat,
                        score=score, semantic_score=score, freq_score=0.7,
                    ))
                return sorted(candidates, key=lambda c: c.score, reverse=True)
        except Exception as e:
            logger.warning(f"DB search failed for '{text}': {e}")
            return []

    def _local_search(self, text: str) -> list[ICDCandidate]:
        """本地内置映射检索（使用预建索引加速）"""
        self._build_local_index()
        seen: set[str] = set()
        candidates: list[ICDCandidate] = []

        # Exact match via hash table
        if text in self._exact_index:
            code, name, cat = self._exact_index[text]
            seen.add(code)
            candidates.append(ICDCandidate(code=code, name=name, category=cat, score=0.95))

        # Prefix-indexed search: only scan entries sharing the first 2 chars
        prefix = text[:2]
        if prefix in self._prefix_index:
            for keyword, code, name, cat in self._prefix_index[prefix]:
                if code in seen:
                    continue
                if keyword != text and (keyword in text or text in keyword):
                    score = 0.72 if keyword in text else 0.62
                    seen.add(code)
                    candidates.append(ICDCandidate(code=code, name=name, category=cat, score=score))

        # Reverse substring match: for long entity names like "前降支PCI术",
        # check if any known keyword (length >= 2) is a substring of the query
        if not candidates and len(text) >= 3:
            for n in range(2, min(len(text), 6)):
                sub_prefix = text[n:n+2]
                if sub_prefix in self._prefix_index:
                    for keyword, code, name, cat in self._prefix_index[sub_prefix]:
                        if code in seen:
                            continue
                        if len(keyword) >= 2 and keyword in text:
                            score = 0.68
                            seen.add(code)
                            candidates.append(ICDCandidate(code=code, name=name, category=cat, score=score))

        return sorted(candidates, key=lambda c: c.score, reverse=True)

    def lookup_code(self, diagnosis_text: str) -> str:
        """快速查码（使用预建索引）"""
        self._build_local_index()
        if diagnosis_text in self._exact_index:
            return self._exact_index[diagnosis_text][0]
        # Fallback: prefix-based lookup
        prefix = diagnosis_text[:2]
        if prefix in self._prefix_index:
            for keyword, code, name, cat in self._prefix_index[prefix]:
                if keyword in diagnosis_text:
                    return code
        return "R69.900"

    async def auto_code(self, structured_record) -> CodingResult:
        diagnoses = structured_record.diagnoses
        surgeries = structured_record.surgeries

        diag_candidates = []
        for d in diagnoses:
            diag_candidates.extend(await self.recommend(d.text))

        proc_candidates = []
        for s in surgeries:
            proc_candidates.extend(await self.recommend(s.text))

        primary = diag_candidates[0] if diag_candidates else None
        secondaries = diag_candidates[1:] if len(diag_candidates) > 1 else []

        return CodingResult(
            primary_diagnosis=primary,
            secondary_diagnoses=secondaries,
            procedures=proc_candidates,
            suggestions=diag_candidates[:5],
            confidence=primary.score if primary else 0.0,
            warnings=[],
        )

    def validate(self, coding_result: CodingResult, patient_info: dict) -> ValidationResult:
        errors = []
        warnings = []
        gender = patient_info.get("gender")
        if coding_result.primary_diagnosis:
            code = coding_result.primary_diagnosis.code
            if gender == "male" and any(code.startswith(p) for p in ["N70", "N80", "O00"]):
                warnings.append(f"编码 {code} 可能不适用于男性患者")
            if gender == "female" and code.startswith("N40"):
                warnings.append(f"编码 {code} 可能不适用于女性患者")
            for prefix in self.VALIDATION_RULES.get("never_primary", []):
                if code.startswith(prefix):
                    warnings.append(f"编码 {code} 不应作为主要诊断")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    async def search_by_keyword(self, keyword: str, limit: int = 20) -> list[ICDCandidate]:
        """混合搜索ICD编码（数据库 + 本地关键词 + 语义向量）"""
        results = []
        seen_codes: set[str] = set()

        def add(candidates):
            for c in candidates:
                if c.code not in seen_codes:
                    seen_codes.add(c.code)
                    results.append(c)

        # 1. Database search
        try:
            async with async_session() as session:
                query = select(ICDCode).where(
                    or_(
                        ICDCode.name.ilike(f"%{keyword}%"),
                        ICDCode.code.ilike(f"%{keyword}%"),
                        ICDCode.py_code.ilike(f"%{keyword}%"),
                    )
                ).limit(limit * 2)
                result = await session.execute(query)
                for row in result.scalars().all():
                    cat = "手术操作" if row.version == ICDVersion.ICD9_CM3 else "诊断"
                    add([ICDCandidate(code=row.code, name=row.name, category=cat, score=0.85)])
        except Exception as e:
            logger.warning(f"DB search_by_keyword failed for '{keyword}': {e}")

        # 2. Local keyword search (indexed)
        self._build_local_index()
        kw = keyword.lower()
        prefix = keyword[:2]
        if prefix in self._prefix_index:
            for entry_keyword, code, full_name, cat in self._prefix_index[prefix]:
                if kw in entry_keyword.lower() or kw in code.lower() or kw in full_name.lower():
                    add([ICDCandidate(code=code, name=full_name, category=cat, score=0.70)])

        # 3. Semantic vector search
        self._ensure_vector_index()
        if self._vector_ready and self._vector_engine:
            try:
                vec_results = self._vector_engine.hybrid_search(keyword, top_k=limit)
                for r in vec_results:
                    add([ICDCandidate(code=r.code, name=r.name, category=r.category, score=r.score)])
            except Exception as e:
                logger.warning(f"Vector search_by_keyword failed for '{keyword}': {e}")

        return sorted(results, key=lambda c: c.score, reverse=True)[:limit]


icd_coder = ICDCoder()

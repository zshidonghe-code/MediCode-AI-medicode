"""NLP病历结构化引擎

将非结构化病历文本拆解为结构化数据：
1. SOAP拆分（主观、客观、评估、计划）
2. 医学实体识别（诊断、症状、手术、药品、检查结果）
3. 关键信息提取（入院时间、出院时间、科别、医生）
"""

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    import jieba

    _JIEBA_AVAILABLE = True
except ImportError:
    _JIEBA_AVAILABLE = False


# Clause delimiters used to keep negation inside its own clause. "、" is
# intentionally excluded: "无高血压、糖尿病史" negates every listed item.
_CLAUSE_SPLIT_RE = re.compile(r"[。；;，,！!？?\n]")
# Fallback-only matcher for the negation word 无 (no tokenizer available).
_BARE_WU_RE = re.compile(r"无(?!法|菌|需|痛|偿|效|关|意|条)")


@dataclass
class MedicalEntity:
    text: str
    entity_type: str  # diagnosis / symptom / surgery / drug / lab / imaging
    normalized: str  # 标准化后的名称
    start_pos: int = 0
    end_pos: int = 0
    confidence: float = 0.0


@dataclass
class SOAPSections:
    subjective: str = ""  # 主观资料：主诉、现病史、既往史
    objective: str = ""  # 客观资料：体格检查、辅助检查
    assessment: str = ""  # 评估：诊断、鉴别诊断
    plan: str = ""  # 计划：治疗方案、用药、随访

    def to_dict(self) -> dict:
        return {
            "subjective": self.subjective,
            "objective": self.objective,
            "assessment": self.assessment,
            "plan": self.plan,
        }


@dataclass
class StructuredRecord:
    record_type: str
    sopa: SOAPSections
    chief_complaint: str = ""
    present_illness: str = ""
    past_history: str = ""
    physical_exam: str = ""
    auxiliary_exams: list[dict] = field(default_factory=list)
    diagnoses: list[MedicalEntity] = field(default_factory=list)
    surgeries: list[MedicalEntity] = field(default_factory=list)
    medications: list[MedicalEntity] = field(default_factory=list)
    summary: str = ""


class MedicalTokenizer:
    """Jieba-based medical tokenizer with ICD dictionary augmentation"""

    def __init__(self):
        self._ready = _JIEBA_AVAILABLE
        if self._ready:
            self._load_medical_dict()

    def _load_medical_dict(self):
        """Load ICD diagnosis names as custom jieba dictionary"""
        try:
            import json
            from pathlib import Path

            data_path = Path(__file__).parent.parent.parent / "data" / "icd_diagnoses.json"
            if data_path.exists():
                with open(data_path, encoding="utf-8") as f:
                    entries = json.load(f)
                for entry in entries:
                    name = entry.get("name", "")
                    if len(name) >= 2:
                        jieba.add_word(name, freq=10, tag="dz")
                    for alias in entry.get("aliases", []):
                        if len(alias) >= 2:
                            jieba.add_word(alias, freq=8, tag="dz")
            proc_path = Path(__file__).parent.parent.parent / "data" / "icd_procedures.json"
            if proc_path.exists():
                with open(proc_path, encoding="utf-8") as f:
                    entries = json.load(f)
                for entry in entries:
                    name = entry.get("name", "")
                    if len(name) >= 2:
                        jieba.add_word(name, freq=10, tag="ss")
        except Exception as e:
            logger.debug(f"Failed to load medical dictionary for jieba: {e}")

    def tokenize(self, text: str) -> list[str]:
        if not self._ready:
            return list(text)
        return [w for w in jieba.cut(text) if len(w.strip()) >= 1]

    def find_entities(self, text: str, entity_type: str = "diagnosis") -> list[str]:
        """Use jieba POS-like tagging to find medical entities"""
        if not self._ready:
            return []
        import jieba.posseg as pseg

        tag = "dz" if entity_type == "diagnosis" else "ss"
        words = pseg.cut(text)
        return [
            w.word
            for w in words
            if len(w.word) >= 2 and w.flag == tag and w.word not in _STOP_ENTITIES
        ]


# Shared stop-words for entity extraction
_STOP_ENTITIES = {
    "现病",
    "入院",
    "出院",
    "既往",
    "个人",
    "家属",
    "体格",
    "辅助",
    "诊疗",
    "治疗",
    "医师",
}

# Singleton tokenizer
_medical_tokenizer = MedicalTokenizer()


class NLPParser:
    """病历文本解析器"""

    # SOAP section matching patterns
    SECTION_PATTERNS = {
        "chief_complaint": r"(主\s*诉[：:].*?)(?=现病史|既往史|个人史|体格检查|辅助检查|初步诊断|入院诊断|诊疗计划|$)",
        "present_illness": r"(现\s*病\s*史[：:].*?)(?=既往史|个人史|体格检查|辅助检查|初步诊断|入院诊断|诊疗计划|$)",
        "past_history": r"(既\s*往\s*史[：:].*?)(?=个人史|婚育史|家族史|体格检查|辅助检查|初步诊断|$)",
        "physical_exam": r"(体\s*格\s*检\s*查[：:].*?)(?=辅助检查|初步诊断|入院诊断|诊疗计划|$)",
        "diagnosis": r"((?:初步|入院|主要|补充|出院)\s*诊\s*断[：:].*?)(?=诊疗计划|治疗意见|出院医嘱|医师签名|$)",
    }

    # Known diagnosis keywords without standard suffixes (高血压, 糖尿病 don't end with 病/症/炎/...)
    KNOWN_DIAGNOSES = [
        "高血压",
        "糖尿病",
        "冠心病",
        "心绞痛",
        "心肌梗死",
        "心房颤动",
        "房颤",
        "高脂血症",
        "脂肪肝",
        "脑卒中",
        "骨质疏松",
        "慢性阻塞性肺疾病",
        "慢阻肺",
        "支气管哮喘",
        "哮喘",
        "前列腺增生",
        "肝硬化",
        "贫血",
        "肥胖",
    ]

    # False positive filter
    STOP_WORDS = {
        "现病",
        "入院",
        "出院",
        "既往",
        "个人",
        "家属",
        "体格",
        "辅助",
        "诊疗",
        "治疗",
        "医师",
    }

    # Key medical entities regex (suffix-based)
    DIAGNOSIS_PATTERNS = [
        r"([\w一-鿿]{2,}(?:病|症|炎|瘤|癌|骨折|损伤|出血|梗死|阻塞|衰竭|综合征|异常))",
    ]

    SURGERY_PATTERNS = [
        r"([\w一-鿿]{2,}(?:术|切除术|成形术|吻合术|置换术|固定术|修补术|引流术|穿刺术|切开))",
        r"(\bPCI\b术?)",
    ]

    # Stent and implant types. These do not end in 术, so the patterns above
    # never catch them, yet they decide the specific ICD-9-CM-3 code
    # (e.g. 药物洗脱支架 -> 36.0700 instead of the unspecified 36.0600).
    STENT_TYPES: list[str] = [
        "药物洗脱支架",
        "药物涂层支架",
        "裸金属支架",
        "金属裸支架",
        "可降解支架",
        "生物可吸收支架",
    ]

    # Sentence fragments that the suffix regex turns into fake surgery
    # entities, e.g. "在全身麻醉下接受手术" or "按标准术" (from 按标准术式操作).
    # Real procedure names never start with these function words or contain
    # 接受/标准, so matching ones are dropped before they reach the coder.
    SURGERY_NOISE_RE = re.compile(r"^在|^按|^予|接受|标准")

    def parse_soap(self, text: str) -> SOAPSections:
        """拆解病历为SOAP结构"""
        sections = SOAPSections()

        # Subjective: chief complaint + present illness + past history
        cc = self._extract_section(text, "chief_complaint")
        pi = self._extract_section(text, "present_illness")
        ph = self._extract_section(text, "past_history")
        sections.subjective = f"{cc or ''} {pi or ''} {ph or ''}"

        # Objective: physical exam + auxiliary exams
        pe = self._extract_section(text, "physical_exam")
        sections.objective = pe or ""

        # Assessment: diagnosis
        diag = self._extract_section(text, "diagnosis")
        sections.assessment = diag or ""

        return sections

    def extract_entities(self, text: str) -> list[MedicalEntity]:
        """提取医学实体"""
        entities = []
        entities.extend(self._extract_diagnoses(text))
        entities.extend(self._extract_surgeries(text))
        return entities

    def _extract_section(self, text: str, section_name: str) -> str:
        pattern = self.SECTION_PATTERNS.get(section_name)
        if not pattern:
            return ""
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    # Common negation patterns indicating the patient does NOT have a condition
    NEGATION_PATTERNS = [
        r"否认.{0,5}",
        r"无明确.{0,3}",
        r"排除.{0,3}",
        r"未见.{0,3}",
        r"无明显.{0,3}",
        r"未及.{0,3}",
        r"不伴.{0,2}",
    ]

    # Common context prefixes to strip (longer first to match greedily)
    _ENTITY_PREFIXES = [
        "否认有",
        "否认",
        "排除",
        "未见明显",
        "未见",
        "无明显",
        "既往有",
        "曾有",
        "既往",
        "有",
        "行",
        "拟行",
        "已行",
        "术后",
        "入院",
        "出院",
        "诊断为",
        # Exam-report prefixes: the greedy suffix regex swallows them into the
        # term (e.g. "X线示右股骨颈骨折"), which then fails dictionary lookup
        # and loses to unrelated candidates in primary selection.
        "心电图示",
        "心电图提示",
        "X线示",
        "CT示",
        "CT提示",
        "MRI示",
        "MRI提示",
        "MR示",
        "B超示",
        "超声示",
        "超声提示",
        "彩超示",
        "造影示",
        "提示",
        "考虑",
        "诊断",
        "再发",
        "新发",
        "未及",
        "无",
        "不伴",
    ]

    def _clean_entity(self, word: str) -> str:
        """Strip common context prefixes from extracted entities"""
        for p in self._ENTITY_PREFIXES:
            if word.startswith(p) and len(word) > len(p) + 1:
                word = word[len(p) :]
                break
        return word

    def _is_negated(self, entity: MedicalEntity, text: str) -> bool:
        """Check if an extracted entity appears in a negated context.

        Only the clause directly preceding the entity is inspected, so a
        negation word in an earlier clause cannot suppress a later finding
        (e.g. "无发热，咳嗽明显" must still keep 咳嗽).

        Note: "、" is deliberately not a delimiter, because in an enumeration
        such as "无高血压、糖尿病史" the negation applies to every item.
        """
        # Check the prefix context window (up to 20 chars before entity)
        start = max(0, entity.start_pos - 20)
        prefix_context = text[start : entity.start_pos]
        clauses = [c for c in _CLAUSE_SPLIT_RE.split(prefix_context) if c.strip()]
        context = clauses[-1] if clauses else prefix_context
        if _JIEBA_AVAILABLE:
            tokens = [w for w in jieba.cut(context) if len(w) >= 1]
            for kw in ("否认", "排除", "未见", "未及", "不伴", "无"):
                if kw in tokens:
                    return True
        else:
            for kw in ("否认", "排除", "未见", "未及", "不伴"):
                if kw in context:
                    return True
            # Without a tokenizer, 无法/无菌/无需/无痛 are not negations of a
            # finding, so they must not trigger on the bare character 无.
            if _BARE_WU_RE.search(context):
                return True
        return False

    def _extract_diagnoses(self, text: str) -> list[MedicalEntity]:
        entities = []
        seen = set()

        # Regex-based extraction (preserved for coverage)
        for pattern in self.DIAGNOSIS_PATTERNS:
            for match in re.finditer(pattern, text):
                raw = match.group(1).strip()
                if raw in self.STOP_WORDS or len(raw) < 3:
                    continue
                word = self._clean_entity(raw)
                if word not in seen and len(word) >= 2:
                    entity = MedicalEntity(
                        text=word,
                        entity_type="diagnosis",
                        normalized=word,
                        # Keep the window aligned with the cleaned term:
                        # start_pos must advance past the stripped prefix,
                        # otherwise negation detection looks at the wrong
                        # slice of text.
                        start_pos=match.start() + (len(raw) - len(word)),
                        end_pos=match.end(),
                        confidence=0.8,
                    )
                    if not self._is_negated(entity, text):
                        seen.add(word)
                        entities.append(entity)

        # Jieba-based extraction (higher precision for dictionary-known terms)
        if _JIEBA_AVAILABLE:
            for word in _medical_tokenizer.find_entities(text, "diagnosis"):
                if word not in seen and len(word) >= 2 and word not in self.STOP_WORDS:
                    seen.add(word)
                    # Find position in text
                    idx = text.find(word)
                    if idx >= 0:
                        entity = MedicalEntity(
                            text=word,
                            entity_type="diagnosis",
                            normalized=word,
                            start_pos=idx,
                            end_pos=idx + len(word),
                            confidence=0.82,
                        )
                        if not self._is_negated(entity, text):
                            entities.append(entity)

        # Keyword-based extraction (for terms without standard suffixes)
        for kw in self.KNOWN_DIAGNOSES:
            if kw not in seen:
                for match in re.finditer(re.escape(kw), text):
                    if kw not in seen:
                        entity = MedicalEntity(
                            text=kw,
                            entity_type="diagnosis",
                            normalized=kw,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            confidence=0.85,
                        )
                        if not self._is_negated(entity, text):
                            seen.add(kw)
                            entities.append(entity)
                        break
        return entities

    def _extract_surgeries(self, text: str) -> list[MedicalEntity]:
        entities = []
        seen = set()
        for pattern in self.SURGERY_PATTERNS:
            for match in re.finditer(pattern, text):
                word = match.group(1).strip()
                if word in seen or len(word) < 3:
                    continue
                word = self._clean_entity(word)
                if word not in seen and len(word) >= 2:
                    if self.SURGERY_NOISE_RE.search(word):
                        continue
                    seen.add(word)
                    entities.append(
                        MedicalEntity(
                            text=word,
                            entity_type="surgery",
                            normalized=word,
                            start_pos=match.start(),
                            end_pos=match.end(),
                            confidence=0.85,
                        )
                    )
        # Stent/implant types never end in 术, so the regex patterns above miss
        # them. They are matched literally to keep the full term intact
        # (a regex such as ".{2,}支架" would also swallow the leading verb).
        for stent in self.STENT_TYPES:
            if stent in seen or stent not in text:
                continue
            idx = text.find(stent)
            entity = MedicalEntity(
                text=stent,
                entity_type="surgery",
                normalized=stent,
                start_pos=idx,
                end_pos=idx + len(stent),
                confidence=0.9,
            )
            if not self._is_negated(entity, text):
                seen.add(stent)
                entities.append(entity)
        return entities

    def parse(self, record_type: str, content: str) -> StructuredRecord:
        """完整解析病历"""
        sopa = self.parse_soap(content)
        entities = self.extract_entities(content)

        return StructuredRecord(
            record_type=record_type,
            sopa=sopa,
            chief_complaint=self._extract_section(content, "chief_complaint"),
            present_illness=self._extract_section(content, "present_illness"),
            past_history=self._extract_section(content, "past_history"),
            physical_exam=self._extract_section(content, "physical_exam"),
            diagnoses=[e for e in entities if e.entity_type == "diagnosis"],
            surgeries=[e for e in entities if e.entity_type == "surgery"],
            summary=content[:500],
        )


# Singleton
nlp_parser = NLPParser()

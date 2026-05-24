"""LLM引擎 - 支持多后端（Ollama本地推理 + 规则增强回退）

架构：
- OllamaBackend: 调用本地Ollama大模型（qwen2.5 / deepseek-r1 等）
- RuleBasedBackend: 增强规则推理（无需GPU，兜底方案）
- LLMEngine: 统一接口，自动选择可用后端
"""

import json
import logging
import time
import httpx
import asyncio
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
from src.services.llm_engine.prompts import (
    ICD_CODING_SYSTEM, QC_SYSTEM, CODE_RECOMMEND_PROMPT,
    QC_SURGERY_DIAG_CONSISTENCY, QC_PRIMARY_DIAGNOSIS_VALIDITY,
    QC_CODE_TEXT_MATCH, QC_CODE_TEXT_MATCH_BATCH, QC_MISSED_DIAGNOSIS,
    DRG_ANALYSIS_PROMPT,
)


@dataclass
class LLMCodeSuggestion:
    code: str
    name: str
    confidence: float
    reasoning: str = ""


@dataclass
class LLMQCResult:
    rule_id: str
    rule_name: str
    severity: str
    description: str
    suggestion: str
    line_snippet: str = ""


@dataclass
class LLMDRGSuggestion:
    type: str
    code: str
    reason: str
    estimated_weight_change: str = ""


class OllamaBackend:
    """Ollama本地推理后端"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        self.base_url = base_url
        self.model = model
        self._available: bool | None = None
        self._last_check: float = 0.0
        self._cache_ttl: float = 60.0  # Re-check availability every 60s

    async def is_available(self) -> bool:
        now = time.time()
        if self._available is not None and (now - self._last_check) < self._cache_ttl:
            return self._available
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/api/tags")
                self._available = r.status_code == 200
        except Exception:
            self._available = False
        self._last_check = now
        return self._available

    async def generate(self, prompt: str, system: str = "", json_mode: bool = True) -> str:
        """调用Ollama生成文本"""
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        async with httpx.AsyncClient(timeout=120) as client:
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "keep_alive": 300,  # Keep model loaded for 5 min
                "options": {"temperature": 0.1, "num_predict": 1024},
            }
            if json_mode:
                payload["format"] = "json"
            r = await client.post(f"{self.base_url}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            return data.get("response", "")

    async def generate_json(self, prompt: str, system: str = "") -> dict:
        """调用Ollama并解析JSON响应（增强容错）"""
        text = await self.generate(prompt, system, json_mode=True)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Try to extract JSON from markdown code blocks
        import re
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        # Try to extract the first JSON object from raw text
        match = re.search(r'\{[^{}]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {"error": "json_parse_failed", "raw": text[:500]}


class RuleBasedBackend:
    """增强规则推理后端 - 当LLM不可用时的兜底方案"""

    async def is_available(self) -> bool:
        return True

    async def generate_json(self, prompt: str, system: str = "") -> dict:
        return {}  # 由各方法自行处理

    def code_recommend(self, entity_text: str, candidates: list, context: str = "") -> LLMCodeSuggestion | None:
        """基于规则增强的编码推荐"""
        if not candidates:
            return None

        best = candidates[0]  # 默认选分数最高的

        # 规则1: 精确匹配最可信
        for c in candidates:
            if c.name == entity_text:
                return LLMCodeSuggestion(
                    code=c.code, name=c.name, confidence=0.98,
                    reasoning=f"精确匹配：'{entity_text}' -> {c.code}",
                )

        # 规则2: 手术操作互斥检查
        if "剖宫" in entity_text:
            for c in candidates:
                if "74" in c.code or "剖宫" in c.name:
                    return LLMCodeSuggestion(
                        code=c.code, name=c.name, confidence=0.90,
                        reasoning=f"产科手术匹配：'{entity_text}' -> {c.code}",
                    )

        # 规则3: 部位一致性加权
        for c in candidates:
            # 如果候选编码名称和输入文本共享更多字符，提高可信度
            common = len(set(entity_text) & set(c.name))
            if common >= 3 and entity_text in c.name:
                return LLMCodeSuggestion(
                    code=c.code, name=c.name, confidence=0.92,
                    reasoning=f"部位匹配：'{entity_text}' ⊆ '{c.name}'",
                )

        # 默认：相信分数最高的
        return LLMCodeSuggestion(
            code=best.code, name=best.name, confidence=best.score,
            reasoning=f"排序最优：score={best.score:.2f}",
        )

    def qc_surgery_diag_consistency(self, diagnoses: list[str], surgeries: list[str]) -> list[LLMQCResult]:
        """QC-102: 手术与诊断一致性检查（规则版）"""
        results = []

        # 硬编码规则
        SURGERY_DIAG_PAIRS = {
            "阑尾": ["阑尾炎", "阑尾"],
            "胆囊": ["胆囊炎", "胆囊结石", "胆囊"],
            "剖宫": ["妊娠", "分娩", "剖宫产", "胎儿"],
            "子宫": ["子宫", "肌瘤", "妊娠"],
            "卵巢": ["卵巢", "囊肿", "妊娠"],
            "前列腺": ["前列腺", "增生"],
            "甲状腺": ["甲状腺", "结节", "甲亢"],
            "冠状动脉": ["冠心病", "心绞痛", "心肌梗死", "冠状动脉"],
            "全髋": ["髋", "股骨头", "骨折"],
            "全膝": ["膝", "骨关节炎", "骨折"],
            "胃": ["胃癌", "胃溃疡", "胃"],
            "肺叶": ["肺癌", "肺结节", "肺"],
            "PCI": ["冠心病", "心绞痛", "心肌梗死", "冠状动脉"],
        }

        for surgery in surgeries:
            matched = False
            for key, diag_keywords in SURGERY_DIAG_PAIRS.items():
                if key.lower() in surgery.lower() or surgery.lower() in key.lower():
                    for diag in diagnoses:
                        if any(kw in diag for kw in diag_keywords):
                            matched = True
                            break
                    if not matched:
                        results.append(LLMQCResult(
                            rule_id="QC-102", rule_name="手术与诊断一致性",
                            severity="CRITICAL",
                            description=f"手术'{surgery}'缺少对应的诊断支持",
                            suggestion=f"请确认'{surgery}'是否有对应的临床诊断，或补充相关诊断编码",
                            line_snippet=surgery,
                        ))
                    break
            else:
                # 没有匹配到已知规则，跳过
                pass

        return results

    def qc_primary_diagnosis_validity(self, content: str, primary_diag: str, all_diags: list[str]) -> list[LLMQCResult]:
        """QC-103: 主要诊断选择正确性（规则版）"""
        results = []

        SYMPTOM_CODES = {
            "发热": "R50", "咳嗽": "R05", "头痛": "R51", "腹痛": "R10",
            "胸痛": "R07", "头晕": "R42", "乏力": "R53", "消瘦": "R63",
            "恶心": "R11", "呕吐": "R11",
        }

        for symptom, code_prefix in SYMPTOM_CODES.items():
            if symptom in primary_diag and symptom in content:
                # 检查是否有更明确的病因诊断
                for diag in all_diags:
                    if diag != primary_diag and not any(s in diag for s in SYMPTOM_CODES):
                        results.append(LLMQCResult(
                            rule_id="QC-103", rule_name="主要诊断选择正确性",
                            severity="MAJOR",
                            description=f"主要诊断'{primary_diag}'是症状描述，建议选择病因诊断",
                            suggestion=f"考虑将'{diag}'作为主要诊断，当前主要诊断为症状编码",
                            line_snippet=primary_diag,
                        ))
                        break
                break

        return results

    def qc_code_text_match(self, code: str, code_name: str, diagnosis_text: str) -> list[LLMQCResult]:
        """QC-201: 编码与诊断文本匹配检查（规则版）"""
        results = []

        # 检查是否为未特指编码（以.9结尾或x00结尾）
        if (".9" in code or ".x00" in code) and len(diagnosis_text) > 4:
            # 未特指编码 + 详细的诊断文本 = 可能不够特异
            pass  # 仅提示，不强制执行

        # 检查部位关键词
        body_parts = {
            "左": "左侧", "右": "右侧", "双": "双侧",
            "上叶": "上叶", "中叶": "中叶", "下叶": "下叶",
            "近端": "近端", "中段": "中段", "远端": "远端",
        }
        for kw, desc in body_parts.items():
            if kw in diagnosis_text and desc not in code_name:
                # 诊断文本有具体部位但编码名称没体现
                pass  # 轻微提示

        return results

    def qc_missed_diagnosis(self, content: str, coded_diags: list[str]) -> list[LLMQCResult]:
        """QC-202: 漏编次要诊断检查（规则版）"""
        results = []

        # 常见易漏诊断关键词
        COMMON_MISSED = {
            "高血压": ("I10.x00", "原发性高血压"),
            "糖尿病": ("E11.900", "2型糖尿病"),
            "高脂血症": ("E78.500", "高脂血症"),
            "脂肪肝": ("K76.000", "脂肪肝"),
            "慢性胃炎": ("K29.500", "慢性胃炎"),
            "骨质疏松": ("M81.900", "骨质疏松"),
            "前列腺增生": ("N40.000", "前列腺增生"),
            "贫血": ("D64.900", "贫血"),
            "慢性肾病": ("N18.900", "慢性肾脏病"),
            "肝功能异常": ("R94.500", "肝功能异常"),
        }

        for keyword, (code, name) in COMMON_MISSED.items():
            if keyword in content and not any(keyword in d for d in coded_diags):
                results.append(LLMQCResult(
                    rule_id="QC-202", rule_name="漏编次要诊断检查",
                    severity="MAJOR",
                    description=f"病历中提到'{keyword}'但未在诊断编码中发现",
                    suggestion=f"建议补充编码 {code} - {name}",
                    line_snippet=keyword,
                ))

        return results

    def drg_analysis(self, diagnoses: list, procedures: list, current_drg: dict) -> list[LLMDRGSuggestion]:
        """DRG优化建议（规则版）"""
        suggestions = []

        # 检查有无MCC遗漏
        mcc_keywords = {
            "心力衰竭": ("I50.900", "心力衰竭", "MCC"),
            "呼吸衰竭": ("J96.900", "呼吸衰竭", "MCC"),
            "肾功能衰竭": ("N17.900", "急性肾损伤", "MCC"),
            "肝功能衰竭": ("K72.900", "肝功能衰竭", "MCC"),
            "败血症": ("A41.900", "败血症", "MCC"),
            "急性心肌梗死": ("I21.900", "急性心肌梗死", "MCC"),
        }

        for kw, (code, name, cc_type) in mcc_keywords.items():
            if kw in str(diagnoses) and not any(code in str(d) for d in diagnoses):
                suggestions.append(LLMDRGSuggestion(
                    type="add_diagnosis",
                    code=code,
                    reason=f"病历中存在'{name}'但未编码，补充后可提升为MCC",
                    estimated_weight_change="+0.5~1.0",
                ))

        return suggestions


class LLMEngine:
    """LLM引擎 - 统一推理接口"""

    def __init__(self):
        self._ollama: OllamaBackend | None = None
        self._rule_based = RuleBasedBackend()
        self._backend_type: str = "unknown"

    async def prewarm(self) -> str:
        """Pre-check backend availability (call on app startup)"""
        backend = await self._get_backend()
        return self._backend_type

    async def _get_backend(self):
        """自动检测并选择可用后端"""
        if self._ollama is None:
            self._ollama = OllamaBackend()
        if await self._ollama.is_available():
            self._backend_type = "ollama"
            return self._ollama
        self._backend_type = "rule_based"
        return self._rule_based

    @property
    def backend_type(self) -> str:
        return self._backend_type

    async def code_recommend(
        self, entity_text: str, candidates: list, context: str = ""
    ) -> LLMCodeSuggestion | None:
        """LLM增强的ICD编码推荐"""
        if not candidates:
            return None

        backend = await self._get_backend()

        if isinstance(backend, OllamaBackend):
            # 使用LLM推理
            cand_text = "\n".join(
                f"{i+1}. {c.code} - {c.name} (score={c.score:.2f})"
                for i, c in enumerate(candidates[:10])
            )
            prompt = CODE_RECOMMEND_PROMPT.format(
                context=context or "出院小结",
                entity_text=entity_text,
                candidates=cand_text,
            )
            try:
                result = await backend.generate_json(prompt, ICD_CODING_SYSTEM)
                if result and "selected_code" in result:
                    return LLMCodeSuggestion(
                        code=result["selected_code"],
                        name=result.get("selected_name", entity_text),
                        confidence=result.get("confidence", 0.8),
                        reasoning=result.get("reasoning", ""),
                    )
            except Exception as e:
                logger.warning(f"LLM code_recommend failed, using rule fallback: {e}")

        # 回退到规则引擎
        return backend.code_recommend(entity_text, candidates, context)

    async def qc_check(
        self, rule_id: str, **kwargs
    ) -> list[LLMQCResult]:
        """执行LLM驱动的质控检查"""
        backend = await self._get_backend()

        if isinstance(backend, RuleBasedBackend):
            return self._run_rule_qc(rule_id, **kwargs)

        # Ollama模式
        try:
            return await self._run_llm_qc(backend, rule_id, **kwargs)
        except Exception as e:
            logger.warning(f"LLM QC {rule_id} failed, using rule fallback: {e}")
            return self._run_rule_qc(rule_id, **kwargs)

    def _run_rule_qc(self, rule_id: str, **kwargs) -> list[LLMQCResult]:
        """规则引擎执行质控"""
        backend = self._rule_based

        if rule_id == "QC-102":
            return backend.qc_surgery_diag_consistency(
                kwargs.get("diagnoses", []),
                kwargs.get("surgeries", []),
            )
        elif rule_id == "QC-103":
            return backend.qc_primary_diagnosis_validity(
                kwargs.get("content", ""),
                kwargs.get("primary_diagnosis", ""),
                kwargs.get("all_diagnoses", []),
            )
        elif rule_id == "QC-201":
            return backend.qc_code_text_match(
                kwargs.get("code", ""),
                kwargs.get("code_name", ""),
                kwargs.get("diagnosis_text", ""),
            )
        elif rule_id == "QC-202":
            return backend.qc_missed_diagnosis(
                kwargs.get("content", ""),
                kwargs.get("coded_diagnoses", []),
            )
        return []

    async def _run_llm_qc(self, backend: OllamaBackend, rule_id: str, **kwargs) -> list[LLMQCResult]:
        """LLM驱动的质控检查"""
        results = []

        if rule_id == "QC-102":
            prompt = QC_SURGERY_DIAG_CONSISTENCY.format(
                diagnoses="\n".join(kwargs.get("diagnoses", [])),
                surgeries="\n".join(kwargs.get("surgeries", [])),
            )
            result = await backend.generate_json(prompt, QC_SYSTEM)
            if not result.get("consistent", True):
                for issue in result.get("issues", []):
                    results.append(LLMQCResult(
                        rule_id="QC-102", rule_name="手术与诊断一致性",
                        severity=issue.get("severity", "MAJOR"),
                        description=issue.get("problem", ""),
                        suggestion="请核实手术操作与诊断的关联性",
                        line_snippet=issue.get("surgery", ""),
                    ))

        elif rule_id == "QC-103":
            prompt = QC_PRIMARY_DIAGNOSIS_VALIDITY.format(
                content=kwargs.get("content", "")[:1000],
                primary_diagnosis=kwargs.get("primary_diagnosis", ""),
                all_diagnoses="\n".join(kwargs.get("all_diagnoses", [])[:10]),
            )
            result = await backend.generate_json(prompt, QC_SYSTEM)
            if not result.get("valid", True):
                results.append(LLMQCResult(
                    rule_id="QC-103", rule_name="主要诊断选择正确性",
                    severity=result.get("severity", "MAJOR"),
                    description=result.get("reasoning", ""),
                    suggestion=f"建议主诊断调整为: {result.get('suggested_primary', '')}",
                ))

        elif rule_id == "QC-201":
            coded_pairs = kwargs.get("coded_pairs", [])
            if not coded_pairs:
                return results
            # Batch all pairs into a single LLM call
            pairs_text = "\n".join(
                f"{i}. 编码: {p.get('code','')} - {p.get('name','')}  文本: {p.get('text','')[:200]}"
                for i, p in enumerate(coded_pairs[:6])
            )
            prompt = QC_CODE_TEXT_MATCH_BATCH.format(
                content=kwargs.get("content", "")[:800],
                pairs=pairs_text,
            )
            result = await backend.generate_json(prompt, QC_SYSTEM)
            for item in result.get("results", []):
                if not item.get("match", True):
                    idx = item.get("index", 0)
                    pair = coded_pairs[idx] if idx < len(coded_pairs) else {}
                    results.append(LLMQCResult(
                        rule_id="QC-201", rule_name="诊断编码与诊断文本匹配",
                        severity="MAJOR",
                        description=f"编码 {item.get('code', pair.get('code',''))} 与文本不匹配: {item.get('reasoning','')}",
                        suggestion=f"建议编码: {item.get('suggested_code', '')}",
                        line_snippet=pair.get("text", ""),
                    ))

        elif rule_id == "QC-202":
            prompt = QC_MISSED_DIAGNOSIS.format(
                content=kwargs.get("content", "")[:1500],
                coded_diagnoses="\n".join(kwargs.get("coded_diagnoses", [])[:15]),
            )
            result = await backend.generate_json(prompt, QC_SYSTEM)
            for missed in result.get("missed", []):
                results.append(LLMQCResult(
                    rule_id="QC-202", rule_name="漏编次要诊断检查",
                    severity="MAJOR",
                    description=f"可能遗漏诊断: {missed.get('diagnosis_text','')} ({missed.get('reasoning','')})",
                    suggestion=f"建议补充 {missed.get('suggested_code','')} - {missed.get('suggested_name','')}",
                    line_snippet=missed.get("diagnosis_text", ""),
                ))

        return results

    async def drg_optimize(
        self, diagnoses: list[str], procedures: list[str],
        primary_diag: str, patient_info: dict, current_drg: dict,
    ) -> list[LLMDRGSuggestion]:
        """DRG编码优化建议"""
        backend = await self._get_backend()

        if isinstance(backend, RuleBasedBackend):
            return backend.drg_analysis(diagnoses, procedures, current_drg)

        try:
            prompt = DRG_ANALYSIS_PROMPT.format(
                patient_info=json.dumps(patient_info, ensure_ascii=False),
                primary_diagnosis=primary_diag,
                secondary_diagnoses="\n".join(diagnoses),
                procedures="\n".join(procedures),
                current_drg=json.dumps(current_drg, ensure_ascii=False),
            )
            result = await backend.generate_json(prompt, ICD_CODING_SYSTEM)
            suggestions = []
            for s in result.get("suggestions", []):
                suggestions.append(LLMDRGSuggestion(
                    type=s.get("type", ""),
                    code=s.get("code", ""),
                    reason=s.get("reason", ""),
                    estimated_weight_change=s.get("estimated_weight_change", ""),
                ))
            return suggestions
        except Exception as e:
            logger.warning(f"LLM DRG optimize failed, using rule fallback: {e}")
            return backend.drg_analysis(diagnoses, procedures, current_drg)


# Singleton
llm_engine = LLMEngine()

"""NLP病历结构化引擎

将非结构化病历文本拆解为结构化数据：
1. SOAP拆分（主观、客观、评估、计划）
2. 医学实体识别（诊断、症状、手术、药品、检查结果）
3. 关键信息提取（入院时间、出院时间、科别、医生）
"""

from dataclasses import dataclass, field
import re


@dataclass
class MedicalEntity:
    text: str
    entity_type: str           # diagnosis / symptom / surgery / drug / lab / imaging
    normalized: str            # 标准化后的名称
    start_pos: int = 0
    end_pos: int = 0
    confidence: float = 0.0


@dataclass
class SOAPSections:
    subjective: str = ""       # 主观资料：主诉、现病史、既往史
    objective: str = ""        # 客观资料：体格检查、辅助检查
    assessment: str = ""       # 评估：诊断、鉴别诊断
    plan: str = ""             # 计划：治疗方案、用药、随访

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
        "高血压", "糖尿病", "冠心病", "心绞痛", "心肌梗死",
        "心房颤动", "房颤", "高脂血症", "脂肪肝", "脑卒中",
        "骨质疏松", "慢性阻塞性肺疾病", "慢阻肺", "支气管哮喘",
        "哮喘", "前列腺增生", "肝硬化", "贫血", "肥胖",
    ]

    # False positive filter
    STOP_WORDS = {"现病", "入院", "出院", "既往", "个人", "家属", "体格", "辅助", "诊疗", "治疗", "医师"}

    # Key medical entities regex (suffix-based)
    DIAGNOSIS_PATTERNS = [
        r"([\w一-鿿]{2,}(?:病|症|炎|瘤|癌|骨折|损伤|出血|梗死|阻塞|衰竭|综合征|异常))",
    ]

    SURGERY_PATTERNS = [
        r"([\w一-鿿]{2,}(?:术|切除术|成形术|吻合术|置换术|固定术|修补术|引流术|穿刺术|切开))",
        r"(\bPCI\b术?)",
    ]

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
        "否认有", "否认", "排除", "未见明显", "未见", "无明显",
        "既往有", "曾有", "既往", "有", "行", "拟行", "已行", "术后",
        "入院", "出院", "诊断为", "诊断", "再发", "新发", "未及",
    ]

    def _clean_entity(self, word: str) -> str:
        """Strip common context prefixes from extracted entities"""
        for p in self._ENTITY_PREFIXES:
            if word.startswith(p) and len(word) > len(p) + 1:
                word = word[len(p):]
                break
        return word

    def _is_negated(self, entity: MedicalEntity, text: str) -> bool:
        """Check if an extracted entity appears in a negated context"""
        # Check the full matched span (before cleaning) for negation keywords
        span_text = text[entity.start_pos:entity.end_pos]
        for kw in ("否认", "排除", "未见", "无明显", "未及", "不伴", "无明确"):
            if kw in span_text:
                return True
        # Check short prefix context (10 chars) — tight window to avoid false positives
        start = max(0, entity.start_pos - 10)
        prefix_context = text[start:entity.start_pos]
        for kw in ("否认", "排除", "未见", "未及", "不伴"):
            if kw in prefix_context:
                return True
        return False

    def _extract_diagnoses(self, text: str) -> list[MedicalEntity]:
        entities = []
        seen = set()

        # Regex-based extraction
        for pattern in self.DIAGNOSIS_PATTERNS:
            for match in re.finditer(pattern, text):
                word = match.group(1).strip()
                if word in self.STOP_WORDS or len(word) < 3:
                    continue
                word = self._clean_entity(word)
                if word not in seen and len(word) >= 2:
                    entity = MedicalEntity(
                        text=word, entity_type="diagnosis", normalized=word,
                        start_pos=match.start(), end_pos=match.end(), confidence=0.8,
                    )
                    if not self._is_negated(entity, text):
                        seen.add(word)
                        entities.append(entity)

        # Keyword-based extraction (for terms without standard suffixes)
        for kw in self.KNOWN_DIAGNOSES:
            if kw not in seen:
                for match in re.finditer(re.escape(kw), text):
                    if kw not in seen:
                        entity = MedicalEntity(
                            text=kw, entity_type="diagnosis", normalized=kw,
                            start_pos=match.start(), end_pos=match.end(), confidence=0.85,
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
                    seen.add(word)
                    entities.append(MedicalEntity(
                        text=word, entity_type="surgery", normalized=word,
                        start_pos=match.start(), end_pos=match.end(), confidence=0.85,
                    ))
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

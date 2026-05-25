"""病历内涵质控引擎

规则驱动 + AI语义检查的双层质控体系

规则层：100+预定义质控规则，快速检查结构性问题
语义层：LLM驱动的深度语义一致性检查
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
import re
import asyncio

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    CRITICAL = "critical"   # 严重缺陷(医保拒付风险)
    MAJOR = "major"         # 重要缺陷(影响DRG分组)
    MINOR = "minor"         # 一般缺陷
    INFO = "info"           # 提示


class RuleType(str, Enum):
    COMPLETENESS = "completeness"       # 完整性
    LOGIC = "logic"                     # 逻辑一致性
    CODING = "coding"                   # 编码一致性
    TIMELINESS = "timeliness"          # 时效性
    NORMALIZATION = "normalization"     # 规范表达
    SEMANTIC = "semantic"              # 语义质量


@dataclass
class QCIssue:
    rule_id: str
    rule_name: str
    rule_type: RuleType
    severity: Severity
    description: str
    line_snippet: str = ""
    suggestion: str = ""
    line_number: int = 0


@dataclass
class QCResult:
    record_id: int
    issues: list[QCIssue]
    total: int = 0
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    info_count: int = 0
    score: float = 100.0  # 0-100

    def __post_init__(self):
        self.total = len(self.issues)
        self.critical_count = sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
        self.major_count = sum(1 for i in self.issues if i.severity == Severity.MAJOR)
        self.minor_count = sum(1 for i in self.issues if i.severity == Severity.MINOR)
        self.info_count = sum(1 for i in self.issues if i.severity == Severity.INFO)
        # 扣分：严重-10, 重要-5, 一般-2, 提示-0.5
        deductions = (self.critical_count * 10 + self.major_count * 5 +
                      self.minor_count * 2 + self.info_count * 0.5)
        self.score = max(0.0, 100.0 - deductions)


class QCEngine:
    """病历质控引擎"""

    def __init__(self):
        self.rules: list[dict] = self._build_default_rules()

    def _build_default_rules(self) -> list[dict]:
        """构建默认质控规则集"""
        return [
            # ===== 完整性检查 =====
            {
                "id": "QC-001",
                "name": "出院小结完整性-出院诊断",
                "type": RuleType.COMPLETENESS,
                "severity": Severity.CRITICAL,
                "check_fn": self._check_section_exists,
                "params": {"section": "出院诊断"},
                "suggestion": "出院小结必须包含出院诊断",
            },
            {
                "id": "QC-002",
                "name": "出院小结完整性-入院情况",
                "type": RuleType.COMPLETENESS,
                "severity": Severity.MAJOR,
                "check_fn": self._check_section_exists,
                "params": {"section": "入院情况"},
                "suggestion": "出院小结必须包含入院情况描述",
            },
            {
                "id": "QC-003",
                "name": "出院小结完整性-诊疗经过",
                "type": RuleType.COMPLETENESS,
                "severity": Severity.MAJOR,
                "check_fn": self._check_section_exists,
                "params": {"section": "诊疗经过"},
                "suggestion": "出院小结必须包含诊疗经过",
            },
            {
                "id": "QC-004",
                "name": "出院小结完整性-出院医嘱",
                "type": RuleType.COMPLETENESS,
                "severity": Severity.CRITICAL,
                "check_fn": self._check_section_exists,
                "params": {"section": "出院医嘱"},
                "suggestion": "出院小结必须包含出院医嘱",
            },
            {
                "id": "QC-005",
                "name": "手术记录完整性-手术日期",
                "type": RuleType.COMPLETENESS,
                "severity": Severity.MAJOR,
                "check_fn": self._check_surgery_date,
                "params": {},
                "suggestion": "手术记录必须包含手术日期",
            },
            {
                "id": "QC-006",
                "name": "手术记录完整性-手术名称",
                "type": RuleType.COMPLETENESS,
                "severity": Severity.CRITICAL,
                "check_fn": self._check_surgery_name,
                "params": {},
                "suggestion": "手术记录必须包含手术名称且与编码一致",
            },
            {
                "id": "QC-007",
                "name": "手术记录完整性-关键字段集合",
                "type": RuleType.COMPLETENESS,
                "severity": Severity.MAJOR,
                "check_fn": self._check_surgery_record_completeness,
                "params": {
                    "required_fields": ["手术名称", "手术日期"],
                    "recommended_fields": ["手术者", "麻醉方式", "手术经过", "术前诊断", "术后诊断"],
                },
                "suggestion": "手术记录关键字段缺失，将直接影响手术编码准确率和DRG分组",
            },
            # ===== 逻辑一致性检查 =====
            {
                "id": "QC-101",
                "name": "诊断与性别一致性",
                "type": RuleType.LOGIC,
                "severity": Severity.CRITICAL,
                "check_fn": self._check_diagnosis_gender_consistency,
                "params": {},
                "suggestion": "诊断编码与患者性别不一致，请核实",
            },
            {
                "id": "QC-102",
                "name": "手术与诊断一致性",
                "type": RuleType.LOGIC,
                "severity": Severity.CRITICAL,
                "check_fn": self._check_surgery_diagnosis_consistency,
                "params": {},
                "suggestion": "手术部位与诊断部位不一致，请核实",
            },
            {
                "id": "QC-103",
                "name": "主要诊断选择正确性",
                "type": RuleType.LOGIC,
                "severity": Severity.CRITICAL,
                "check_fn": self._check_primary_diagnosis_validity,
                "params": {},
                "suggestion": "主要诊断应选择对健康危害最大、消耗医疗资源最多的诊断",
            },
            {
                "id": "QC-104",
                "name": "住院天数逻辑检查",
                "type": RuleType.LOGIC,
                "severity": Severity.MAJOR,
                "check_fn": self._check_length_of_stay,
                "params": {},
                "suggestion": "住院天数与诊断/手术复杂度不匹配",
            },
            # ===== 编码一致性检查 =====
            {
                "id": "QC-201",
                "name": "诊断编码与诊断文本匹配",
                "type": RuleType.CODING,
                "severity": Severity.MAJOR,
                "check_fn": self._check_code_text_consistency,
                "params": {},
                "suggestion": "ICD编码与病历中诊断描述不一致",
            },
            {
                "id": "QC-202",
                "name": "漏编次要诊断检查",
                "type": RuleType.CODING,
                "severity": Severity.MAJOR,
                "check_fn": self._check_missing_secondary_diagnosis,
                "params": {},
                "suggestion": "病历中存在可能遗漏的次要诊断编码",
            },
            # ===== 时效性检查 =====
            {
                "id": "QC-301",
                "name": "入院记录24h完成",
                "type": RuleType.TIMELINESS,
                "severity": Severity.MINOR,
                "check_fn": self._check_admission_record_timeliness,
                "params": {"hours": 24},
                "suggestion": "入院记录应在入院后24小时内完成",
            },
            {
                "id": "QC-302",
                "name": "手术记录术后即时完成",
                "type": RuleType.TIMELINESS,
                "severity": Severity.MINOR,
                "check_fn": self._check_surgery_record_timeliness,
                "params": {"hours": 24},
                "suggestion": "手术记录应在术后24小时内完成",
            },
            # ===== 规范表达检查 =====
            {
                "id": "QC-401",
                "name": "主要诊断为病因诊断",
                "type": RuleType.NORMALIZATION,
                "severity": Severity.MAJOR,
                "check_fn": self._check_primary_is_etiology,
                "params": {},
                "suggestion": "主要诊断应为病因诊断，不应选择症状或体征作为主要诊断",
            },
            {
                "id": "QC-402",
                "name": "诊断名称规范化",
                "type": RuleType.NORMALIZATION,
                "severity": Severity.MINOR,
                "check_fn": self._check_diagnosis_naming,
                "params": {},
                "suggestion": "诊断名称应使用标准医学名词，避免口语化或简写",
            },
        ]

    async def check(self, record_type: str, content: str, coding_result: dict | None = None,
              patient_info: dict | None = None, use_llm: bool = False) -> QCResult:
        """执行全部质控规则"""
        issues = []

        for rule in self.rules:
            if not self._rule_applies_to(rule, record_type):
                continue
            try:
                result_issues = rule["check_fn"](content, coding_result, patient_info, rule)
                if result_issues:
                    if isinstance(result_issues, list):
                        issues.extend(result_issues)
                    else:
                        issues.append(result_issues)
            except Exception as e:
                logger.warning(f"Rule {rule['id']} check failed: {e}")
                continue

        # LLM驱动的深度检查（仅在use_llm=True时执行）
        if use_llm:
            try:
                llm_issues = await self._run_llm_checks(content, coding_result, patient_info)
                issues.extend(llm_issues)
            except Exception as e:
                logger.warning(f"LLM QC checks failed: {e}")

        return QCResult(record_id=0, issues=issues)

    async def _run_llm_checks(self, content: str, coding_result: dict | None,
                               patient_info: dict | None) -> list[QCIssue]:
        """执行LLM驱动的深度质控检查 — 并行执行独立检查"""
        all_issues = []
        try:
            from src.services.llm_engine import llm_engine
        except Exception:
            return all_issues

        # 提取诊断和手术列表
        diagnoses = []
        surgeries = []
        if coding_result:
            pri = coding_result.get("primary_diagnosis")
            if pri:
                diagnoses.append(f"{pri.get('code', '')} {pri.get('name', '')}")
            for d in coding_result.get("secondary_diagnoses", []):
                diagnoses.append(f"{d.get('code', '')} {d.get('name', '')}")
            for p in coding_result.get("procedures", []):
                surgeries.append(f"{p.get('code', '')} {p.get('name', '')}")

        primary_diag_text = diagnoses[0] if diagnoses else ""

        # Prepare coded pairs for QC-201
        coded_pairs = []
        if coding_result:
            pri = coding_result.get("primary_diagnosis")
            if pri:
                coded_pairs.append({"code": pri.get("code", ""), "name": pri.get("name", ""), "text": content[:500]})
            for d in coding_result.get("secondary_diagnoses", [])[:3]:
                coded_pairs.append({"code": d.get("code", ""), "name": d.get("name", ""), "text": content[:500]})

        # Phase 1: Run independent checks in parallel (QC-102 + QC-103)
        phase1_tasks = []
        if surgeries:
            phase1_tasks.append(llm_engine.qc_check("QC-102", diagnoses=diagnoses, surgeries=surgeries))
        if primary_diag_text:
            phase1_tasks.append(llm_engine.qc_check("QC-103", content=content,
                primary_diagnosis=primary_diag_text, all_diagnoses=diagnoses))

        # Phase 2: Run independent checks in parallel (QC-201 + QC-202)
        phase2_tasks = []
        if coded_pairs:
            phase2_tasks.append(llm_engine.qc_check("QC-201", coded_pairs=coded_pairs))
        phase2_tasks.append(llm_engine.qc_check("QC-202", content=content, coded_diagnoses=[d for d in diagnoses]))

        # Execute both phases — phase2 can run concurrently with phase1
        all_tasks = phase1_tasks + phase2_tasks
        if all_tasks:
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            for result_list in results:
                if isinstance(result_list, list):
                    for r in result_list:
                        all_issues.append(self._to_qc_issue(r))

        return all_issues

    def _to_qc_issue(self, llm_result) -> QCIssue:
        """将LLMQCResult转换为QCIssue"""
        from src.services.llm_engine import LLMQCResult
        return QCIssue(
            rule_id=llm_result.rule_id,
            rule_name=llm_result.rule_name,
            rule_type=RuleType.LOGIC if llm_result.rule_id in ("QC-102", "QC-103") else RuleType.CODING,
            severity=Severity(llm_result.severity.lower()) if llm_result.severity.lower() in ["critical", "major", "minor", "info"] else Severity.MAJOR,
            description=llm_result.description,
            line_snippet=llm_result.line_snippet,
            suggestion=llm_result.suggestion,
        )

    # Rules that only apply to specific record types
    _RULE_RECORD_TYPE_MAP: dict[str, set[str]] = {
        "QC-001": {"discharge"}, "QC-002": {"discharge"},
        "QC-003": {"discharge"}, "QC-004": {"discharge"},
        "QC-005": {"surgery"}, "QC-006": {"surgery"},
        "QC-007": {"surgery"},
        "QC-102": {"surgery", "discharge"},  # surgery-diag consistency: needs procedure data
        "QC-301": {"admission"},
        "QC-302": {"surgery"},
    }

    def _rule_applies_to(self, rule: dict, record_type: str) -> bool:
        """检查规则是否适用于当前记录类型"""
        restricted = self._RULE_RECORD_TYPE_MAP.get(rule["id"])
        if restricted is not None:
            return record_type in restricted
        return True

    # ========== 规则检查函数 ==========

    def _check_section_exists(self, content: str, coding_result, patient_info, rule) -> QCIssue | None:
        section = rule["params"].get("section", "")
        patterns = {
            "出院诊断": r"出院\s*诊\s*断[：:]",
            "入院情况": r"入院\s*情\s*况[：:]",
            "诊疗经过": r"诊疗\s*经\s*过[：:]",
            "出院医嘱": r"出院\s*医\s*嘱[：:]",
        }
        pattern = patterns.get(section, section)
        if not re.search(pattern, content):
            return QCIssue(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_type=rule["type"],
                severity=rule["severity"],
                description=f"缺少{section}部分",
                suggestion=rule["suggestion"],
            )
        return None

    def _check_surgery_date(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        if "手术" not in content:
            return None
        if not re.search(r"手术\s*日期[：:]?\s*\d{4}[-/年]\d{1,2}[-/月]\d{1,2}", content):
            return QCIssue(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_type=rule["type"],
                severity=rule["severity"],
                description="手术记录中缺少手术日期",
                suggestion=rule["suggestion"],
            )
        return None

    def _check_surgery_name(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        if "手术" not in content:
            return None
        if not re.search(r"手术\s*名\s*称[：:]", content):
            return QCIssue(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_type=rule["type"],
                severity=rule["severity"],
                description="手术记录中缺少手术名称",
                suggestion=rule["suggestion"],
            )
        return None

    def _check_surgery_record_completeness(self, content, coding_result, patient_info, rule) -> list[QCIssue] | None:
        """检查手术记录关键字段完整性 —— 编码前置质量门。

        如果手术记录缺失关键字段（手术名称/日期/入路/麻醉等），编码员无法准确编码，
        导致手术编码 F1 大幅下降。此规则在编码之前即暴露缺陷，避免盲编。
        """
        if "手术" not in content:
            return None

        required_fields = rule["params"].get("required_fields", [])
        recommended_fields = rule["params"].get("recommended_fields", [])

        # Field pattern map: field name -> (regex, severity)
        field_patterns = {
            "手术名称": (r"手术\s*名\s*称[：:]", Severity.CRITICAL),
            "手术日期": (r"手术\s*日\s*期[：:]?\s*\d{4}", Severity.MAJOR),
            "手术者": (r"手术\s*者[：:]", Severity.MINOR),
            "麻醉方式": (r"麻醉\s*(方式|方法)[：:]", Severity.MINOR),
            "手术经过": (r"手术\s*(经过|过程|情况)[：:]", Severity.MAJOR),
            "术前诊断": (r"术前\s*诊\s*断[：:]", Severity.MAJOR),
            "术后诊断": (r"术后\s*诊\s*断[：:]", Severity.MAJOR),
        }

        issues = []
        for field in required_fields + recommended_fields:
            if field in field_patterns:
                pattern, severity = field_patterns[field]
                if not re.search(pattern, content):
                    is_required = field in required_fields
                    level = severity if is_required else Severity.MINOR
                    issues.append(QCIssue(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        rule_type=rule["type"],
                        severity=level,
                        description=f"手术记录缺少{'必须' if is_required else '建议'}字段「{field}」"
                                    f"{'，将影响手术编码准确性' if is_required else ''}",
                        suggestion=rule["suggestion"],
                    ))

        return issues if issues else None

    def _check_diagnosis_gender_consistency(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        if not patient_info or not coding_result:
            return None
        gender = patient_info.get("gender", "")
        # 女性专有诊断的性别检查
        female_only = ["卵巢", "子宫", "输卵管", "阴道", "宫颈", "乳腺", "妊娠", "分娩", "产褥"]
        if gender == "male":
            for term in female_only:
                if term in content:
                    return QCIssue(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        rule_type=rule["type"],
                        severity=rule["severity"],
                        description=f"病历中包含女性特有诊断描述'{term}'，与患者性别(男)不符",
                        suggestion=rule["suggestion"],
                    )
        male_only = ["前列腺", "睾丸", "阴茎", "附睾"]
        if gender == "female":
            for term in male_only:
                if term in content:
                    return QCIssue(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        rule_type=rule["type"],
                        severity=rule["severity"],
                        description=f"病历中包含男性特有诊断描述'{term}'，与患者性别(女)不符",
                        suggestion=rule["suggestion"],
                    )
        return None

    def _check_surgery_diagnosis_consistency(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        """检查手术部位与诊断部位的一致性"""
        if not coding_result:
            return None
        procedures = coding_result.get("procedures", [])
        if not procedures:
            return None
        # Extract all diagnosis codes
        diag_codes = set()
        primary = coding_result.get("primary_diagnosis")
        if primary:
            diag_codes.add(primary.get("code", "").replace(".", ""))
        for d in coding_result.get("secondary_diagnoses", []):
            diag_codes.add(d.get("code", "").replace(".", ""))
        # Anatomical body-system mapping: procedure prefix -> expected diagnosis prefix
        proc_diag_map = [
            # Cardiovascular procedures -> circulatory diagnoses
            ("35", "I"), ("36", "I"), ("37", "I"), ("38", "I"), ("39", "I"),
            # Neuro procedures -> neuro diagnoses
            ("01", "G"), ("02", "G"), ("03", "G"),
            # Respiratory procedures -> respiratory diagnoses
            ("30", "J"), ("31", "J"), ("32", "J"), ("33", "J"), ("34", "J"),
            # GI procedures -> digestive diagnoses
            ("42", "K"), ("43", "K"), ("44", "K"), ("45", "K"), ("46", "K"),
            ("47", "K"), ("48", "K"), ("49", "K"), ("50", "K"), ("51", "K"),
            ("52", "K"), ("53", "K"), ("54", "K"),
            # Urinary procedures -> genitourinary diagnoses
            ("55", "N"), ("56", "N"), ("57", "N"), ("58", "N"), ("59", "N"),
            # Orthopedic procedures -> musculoskeletal diagnoses
            ("78", "M"), ("79", "M"), ("80", "M"), ("81", "M"),
            # OB/GYN procedures -> pregnancy/gynecology diagnoses
            ("65", "O"), ("66", "O"), ("67", "O"), ("68", "O"),
            ("69", "O"), ("70", "O"), ("71", "O"), ("74", "O"),
        ]
        for proc in procedures:
            proc_code = proc.get("code", "").replace(".", "")
            for proc_prefix, diag_prefix in proc_diag_map:
                if proc_code.startswith(proc_prefix):
                    if not any(d.startswith(diag_prefix) for d in diag_codes):
                        return QCIssue(
                            rule_id=rule["id"], rule_name=rule["name"],
                            rule_type=rule["type"], severity=rule["severity"],
                            description=f"手术'{proc.get('name', proc_code)}'缺少对应系统({diag_prefix})的诊断",
                            suggestion=rule["suggestion"],
                        )
        return None

    def _check_primary_diagnosis_validity(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        """检查主要诊断选择的合理性"""
        if not coding_result:
            return None
        primary = coding_result.get("primary_diagnosis")
        if not primary:
            return None
        code = primary.get("code", "")
        name = primary.get("name", "")
        # Z-codes are rehab/follow-up — rarely appropriate as primary
        if code.startswith("Z"):
            return QCIssue(
                rule_id=rule["id"], rule_name=rule["name"],
                rule_type=rule["type"], severity=rule["severity"],
                description=f"主要诊断为Z编码'{name}'，Z编码通常不应用于主要诊断，除非有特殊说明",
                suggestion=rule["suggestion"],
            )
        # R-codes are symptoms — only appropriate if no cause is found
        if code.startswith("R") and not code.startswith("R5"):
            secondary_count = len(coding_result.get("secondary_diagnoses", []))
            if secondary_count > 0:
                return QCIssue(
                    rule_id=rule["id"], rule_name=rule["name"],
                    rule_type=rule["type"], severity=rule["severity"],
                    description=f"主要诊断为症状编码'{name}'，存在其他诊断时症状不应作为主要诊断",
                    suggestion=rule["suggestion"],
                )
        return None

    def _check_length_of_stay(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        if not patient_info:
            return None
        days = patient_info.get("days_of_stay", 0)
        if days == 1:
            return None  # 当日出入院是正常情况
        if days > 60:
            return QCIssue(
                rule_id=rule["id"],
                rule_name=rule["name"],
                rule_type=rule["type"],
                severity=rule["severity"],
                description=f"住院天数({days}天)异常偏长，请确认是否有特殊原因",
                suggestion=rule["suggestion"],
            )
        return None

    def _check_code_text_consistency(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        """检查ICD编码名称与病历文本的关键词匹配"""
        if not coding_result:
            return None
        issues = []
        # Check primary diagnosis
        primary = coding_result.get("primary_diagnosis")
        if primary:
            name = primary.get("name", "")
            code = primary.get("code", "")
            # Extract key clinical terms (2+ chars) from the diagnosis name
            terms = [t for t in re.findall(r"[\w一-鿿]{2,}", name) if t not in ("性", "型", "急性", "慢性", "原发性", "继发性", "先天性")]
            if terms and len(terms) >= 2:
                # At least one major clinical term should appear in the content
                found = any(term in content for term in terms[:3])
                if not found:
                    return QCIssue(
                        rule_id=rule["id"], rule_name=rule["name"],
                        rule_type=rule["type"], severity=rule["severity"],
                        description=f"诊断编码'{code} {name}'中的关键临床术语在病历文本中未找到，请核实编码准确性",
                        suggestion=rule["suggestion"],
                    )
        return None

    # Common chronic conditions worth flagging if present but uncoded
    _CHECKABLE_CHRONIC: dict[str, str] = {
        "高血压": "I10", "糖尿病": "E11",
        "冠心病": "I25.1", "心肌梗死": "I21",
        "心房颤动": "I48", "房颤": "I48",
        "心力衰竭": "I50", "心衰": "I50",
        "高脂血症": "E78", "高尿酸血症": "E79",
        "哮喘": "J45", "慢阻肺": "J44",
        "肝硬化": "K74", "慢性肾病": "N18",
        "脑卒中": "I64", "贫血": "D64",
        "骨质疏松": "M81",
    }

    def _check_missing_secondary_diagnosis(self, content, coding_result, patient_info, rule) -> list[QCIssue] | None:
        """检查病历中提及的常见慢性病是否已编码，返回所有漏编项"""
        if not coding_result:
            return None
        coded_names: set[str] = set()
        primary = coding_result.get("primary_diagnosis")
        if primary:
            coded_names.add(primary.get("name", ""))
        for d in coding_result.get("secondary_diagnoses", []):
            coded_names.add(d.get("name", ""))
        issues = []
        for keyword, expected_code in self._CHECKABLE_CHRONIC.items():
            if keyword in content:
                # 否认/排除/无 pattern negates the condition
                neg_match = re.search(rf"(?:否认|排除|未见|无|未及|不伴).{{0,5}}{keyword}", content)
                if neg_match:
                    continue
                already_coded = any(keyword in name for name in coded_names)
                if not already_coded:
                    issues.append(QCIssue(
                        rule_id=rule["id"], rule_name=rule["name"],
                        rule_type=rule["type"], severity=rule["severity"],
                        description=f"病历中提及'{keyword}'但未在诊断编码中找到，可能存在漏编",
                        suggestion=f"{rule['suggestion']}（建议编码{expected_code}）",
                    ))
        return issues if issues else None

    def _check_admission_record_timeliness(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        if "入院" not in content[:200]:
            return None
        dates = re.findall(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})', content)
        if len(dates) >= 2:
            from datetime import datetime
            try:
                def ps(s):
                    return datetime.strptime(s.replace('年','-').replace('月','-').replace('/','-')[:10], '%Y-%m-%d')
                d1, d2 = ps(dates[0]), ps(dates[1])
                if abs((d2 - d1).days) > 1:
                    return QCIssue(
                        rule_id=rule["id"], rule_name=rule["name"],
                        rule_type=rule["type"], severity=rule["severity"],
                        description=f"入院日期与记录日期相差{abs((d2-d1).days)}天，超过24h要求",
                        suggestion=rule["suggestion"],
                    )
            except ValueError:
                pass
        return None

    def _check_surgery_record_timeliness(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        if "手术" not in content:
            return None
        if re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}).*?手术', content):
            return None
        return QCIssue(
            rule_id=rule["id"], rule_name=rule["name"],
            rule_type=rule["type"], severity=rule["severity"],
            description="手术记录中缺少明确的手术日期，无法判断记录时效性",
            suggestion=rule["suggestion"],
        )

    def _check_primary_is_etiology(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        """检查主要诊断是否为病因诊断而非症状"""
        symptom_keywords = ["发热", "咳嗽", "头痛", "腹痛", "胸痛", "乏力", "恶心", "呕吐", "腹泻", "水肿", "黄疸"]
        primary = coding_result.get("primary_diagnosis") if coding_result else None
        if primary:
            primary_name = primary.get("name", "")
            primary_code = primary.get("code", "")
            # Check if the primary diagnosis name or code indicates a symptom rather than etiology
            combined = f"{primary_name} {primary_code}"
            for keyword in symptom_keywords:
                if keyword in combined:
                    return QCIssue(
                        rule_id=rule["id"],
                        rule_name=rule["name"],
                        rule_type=rule["type"],
                        severity=rule["severity"],
                        description=f"主要诊断'{primary_name}'可能为症状而非病因诊断，应尽可能选择病因诊断",
                        suggestion=rule["suggestion"],
                    )
        return None

    def _check_diagnosis_naming(self, content, coding_result, patient_info, rule) -> QCIssue | None:
        informal_pairs = [("感冒", "上呼吸道感染"), ("拉肚子", "腹泻"), ("发烧", "发热")]
        for slang, formal in informal_pairs:
            if slang in content:
                return QCIssue(
                    rule_id=rule["id"], rule_name=rule["name"],
                    rule_type=rule["type"], severity=rule["severity"],
                    description=f"诊断中使用了口语化表达'{slang}'，建议使用'{formal}'",
                    suggestion=rule["suggestion"],
                )
        return None


qc_engine = QCEngine()

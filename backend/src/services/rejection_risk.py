"""医保拒付风险预测引擎

在编码+DRG分组完成后，对编码组合进行拒付风险扫描。
国赛演示核心亮点：展示系统不仅能编码，还能**预见医保审核风险**。

规则来源：国家医保局飞行检查通报、DRG付费审核细则
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    HIGH = "high"  # 极高风险 — 大概率拒付
    MEDIUM = "medium"  # 中等风险 — 需要复核
    LOW = "low"  # 低风险 — 建议关注


RISK_SCORE_WEIGHTS = {
    RiskLevel.LOW: 10,
    RiskLevel.MEDIUM: 30,
    RiskLevel.HIGH: 60,
}


@dataclass
class RejectionRisk:
    rule_id: str
    rule_name: str
    risk_level: RiskLevel
    description: str
    affected_code: str = ""
    suggestion: str = ""
    estimated_loss: float = 0.0  # 预估拒付金额


@dataclass
class RejectionReport:
    overall_risk: RiskLevel
    risk_score: int  # 0-100, higher = greater rejection risk
    risks: list[RejectionRisk]
    preventable_amount: float = 0.0  # 可规避的拒付金额


# ── 拒付风险规则库 ──────────────────────────────────────────────
# 每条规则 = (id, name, risk_level, check_fn_key, description_template, suggestion)

REJECTION_RULES = [
    # === 编码一致性 ===
    {
        "id": "RR-001",
        "name": "主要诊断与DRG不匹配",
        "risk_level": RiskLevel.HIGH,
        "category": "coding_consistency",
        "check": "primary_drg_mismatch",
        "description": "主要诊断编码{primary_code}属于{primary_mdc}，但DRG分组为{drg_code}({drg_mdc})，跨MDC，审核必查",
        "suggestion": "核实主要诊断选择是否正确，或检查DRG分组逻辑",
    },
    {
        "id": "RR-002",
        "name": "手术操作无对应诊断",
        "risk_level": RiskLevel.HIGH,
        "category": "coding_consistency",
        "check": "procedure_without_indication",
        "description": "手术{proc_code} {proc_name}缺少对应的临床诊断支持，医保将认定为无指征操作",
        "suggestion": "补充对应诊断编码，或确认手术必要性记录",
    },
    {
        "id": "RR-003",
        "name": "次要诊断与主要诊断矛盾",
        "risk_level": RiskLevel.MEDIUM,
        "category": "coding_consistency",
        "check": "contradictory_diagnoses",
        "description": "诊断{d1}与{d2}在临床上可能矛盾，审核时会被质疑编码准确性",
        "suggestion": "核实两份诊断的临床依据，排除编码错误",
    },
    # === 升级诊断嫌疑 ===
    {
        "id": "RR-101",
        "name": "疑似诊断升级（MCC嫌疑）",
        "risk_level": RiskLevel.HIGH,
        "category": "upcoding",
        "check": "suspected_upcoding_mcc",
        "description": "次要诊断{diag}为MCC条目，大幅拉升DRG权重（+{weight_delta}），且病历中缺乏充分依据描述，飞行检查必查项",
        "suggestion": "确认{diag}的诊断依据是否充分记录在病历中：检查结果、会诊记录、病程描述",
    },
    {
        "id": "RR-102",
        "name": "高编手术操作等级",
        "risk_level": RiskLevel.HIGH,
        "category": "upcoding",
        "check": "procedure_level_inflated",
        "description": "手术{proc_code}的记录等级可能与实际不符，常见于分级诊疗审核",
        "suggestion": "核对手术记录中的实际操作范围、入路、时间与编码等级是否一致",
    },
    # === 分解住院 / 低码高套 ===
    {
        "id": "RR-201",
        "name": "短期再入院风险标记",
        "risk_level": RiskLevel.MEDIUM,
        "category": "unbundling",
        "check": "short_readmission_risk",
        "description": "患者本次入院距上次出院≤{days}天，同一MDC，医保可能认定为分解住院",
        "suggestion": "核实本次住院的必要性，病历中需明确记录再次入院原因",
    },
    {
        "id": "RR-202",
        "name": "费用与DRG权重偏离",
        "risk_level": RiskLevel.MEDIUM,
        "category": "unbundling",
        "check": "cost_weight_deviation",
        "description": "本次住院费用与DRG标准费用偏离{deviation}%，触发费用异常审核",
        "suggestion": "核查费用明细，排除过度医疗或费用转移",
    },
    # === 编码完整性 ===
    {
        "id": "RR-301",
        "name": "漏编并发症/合并症",
        "risk_level": RiskLevel.MEDIUM,
        "category": "completeness",
        "check": "missing_cc",
        "description": "病历中提及{condition}但未编码，遗漏CC/MCC将导致DRG分组降级、医院收入损失",
        "suggestion": "补充编码{expected_code}，预计可增加权重+{weight_gain}",
    },
    {
        "id": "RR-302",
        "name": "高值耗材无对应编码",
        "risk_level": RiskLevel.MEDIUM,
        "category": "completeness",
        "check": "high_value_device_uncoded",
        "description": "病历中涉及高值耗材{device}但缺少对应手术/操作编码",
        "suggestion": "补充操作编码以匹配耗材使用",
    },
    # === 合理性 ===
    {
        "id": "RR-401",
        "name": "住院天数与DRG不匹配",
        "risk_level": RiskLevel.LOW,
        "category": "reasonableness",
        "check": "los_drg_mismatch",
        "description": "住院{days}天，超出该DRG平均住院日{avg_days}天{excess}%，可能触发住院日异常审核",
        "suggestion": "病历中需记录延长住院的原因（并发症、社会因素等）",
    },
    {
        "id": "RR-402",
        "name": "出院带药与诊断不符",
        "risk_level": RiskLevel.LOW,
        "category": "reasonableness",
        "check": "discharge_med_mismatch",
        "description": "出院带药{med}与出院诊断关联性不足，可能被认定为不合理用药",
        "suggestion": "确认带药指征与诊断的对应关系",
    },
]


# ── 诊断矛盾对（临床上不应同时出现） ──────────────────────────
CONTRADICTORY_PAIRS: list[tuple[set[str], set[str], str]] = [
    ({"高血压"}, {"低血压", "休克"}, "血压状态矛盾"),
    ({"糖尿病"}, {"低血糖"}, "血糖状态矛盾，需明确是否为药物性"),
    ({"贫血"}, {"红细胞增多症"}, "红细胞状态矛盾"),
    ({"甲亢", "甲状腺功能亢进"}, {"甲减", "甲状腺功能减退"}, "甲状腺功能状态矛盾"),
    ({"肝硬化"}, {"正常肝功能"}, "肝功能状态矛盾"),
    ({"急性肾损伤", "肾功能衰竭"}, {"肾功能正常"}, "肾功能状态矛盾"),
]

# ── MCC关键词（诊断升级重点关注） ─────────────────────────────
MCC_FLAGS: dict[str, float] = {
    "心力衰竭": 0.8,
    "呼吸衰竭": 0.9,
    "肾功能衰竭": 0.8,
    "肝功能衰竭": 0.9,
    "败血症": 0.7,
    "急性心肌梗死": 0.6,
    "脑卒中": 0.5,
    "肺栓塞": 0.8,
    "多器官功能衰竭": 1.0,
    "休克": 0.7,
    "弥散性血管内凝血": 0.9,
    "急性胰腺炎": 0.4,
}

# ── 高值耗材关键词 ────────────────────────────────────────────
HIGH_VALUE_DEVICES: dict[str, str] = {
    "支架": "血管支架置入术",
    "起搏器": "心脏起搏器置入术",
    "人工关节": "人工关节置换术",
    "钢板": "骨折内固定术",
    "螺钉": "骨折内固定术",
    "射频消融": "射频消融术",
    "封堵器": "封堵器置入术",
    "人工晶体": "人工晶体植入术",
    "骨水泥": "椎体成形术",
}


class RejectionRiskEngine:
    """医保拒付风险预测引擎"""

    def __init__(self, drg_base_rate: float = 12000.0):
        self.drg_base_rate = drg_base_rate

    def assess(
        self,
        primary_diag: dict,  # {code, name}
        secondary_diags: list[dict],  # [{code, name}, ...]
        procedures: list[dict],  # [{code, name}, ...]
        drg_result: dict | None = None,  # {drg_code, drg_name, weight, ...}
        patient_info: dict | None = None,  # {age, gender, days_of_stay, ...}
        content: str = "",  # Raw medical record text
        hospital_cost: float = 0.0,  # Total hospitalization cost
    ) -> RejectionReport:
        risks = []

        # ── RR-001: 主要诊断MDC vs DRG MDC ──
        if primary_diag and drg_result:
            risk = self._check_primary_drg_mismatch(primary_diag, drg_result)
            if risk:
                risks.append(risk)

        # ── RR-002: 手术无对应诊断 ──
        if procedures and (primary_diag or secondary_diags):
            risks.extend(
                self._check_procedure_indications(procedures, primary_diag, secondary_diags)
            )

        # ── RR-003: 诊断矛盾 ──
        all_diags = [primary_diag] + secondary_diags if primary_diag else secondary_diags
        risks.extend(self._check_contradictory(all_diags))

        # ── RR-101: 疑似MCC升级 ──
        risks.extend(self._check_mcc_upcoding(secondary_diags, content))

        # ── RR-301: 漏编CC ── (from existing COMMON_MISSED logic)
        risks.extend(self._check_missing_cc(content, all_diags))

        # ── RR-401: 住院天数异常 ──
        if patient_info and drg_result:
            risk = self._check_los_mismatch(patient_info, drg_result)
            if risk:
                risks.append(risk)

        # ── 高值耗材检查 ──
        risks.extend(self._check_high_value_devices(content, procedures))

        # ── 费用偏离 ──
        if hospital_cost > 0 and drg_result:
            risk = self._check_cost_deviation(hospital_cost, drg_result)
            if risk:
                risks.append(risk)

        # Calculate overall risk
        score = min(100, sum(RISK_SCORE_WEIGHTS[r.risk_level] for r in risks))

        if score >= 60:
            overall = RiskLevel.HIGH
        elif score >= 30:
            overall = RiskLevel.MEDIUM
        else:
            overall = RiskLevel.LOW

        # Preventable amount estimate
        weight = drg_result.get("weight", 1.0) if drg_result else 1.0
        preventable = sum(
            r.estimated_loss for r in risks if r.risk_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)
        )
        if not preventable and overall != RiskLevel.LOW:
            preventable = self.drg_base_rate * weight * 0.15  # ~15% at risk

        return RejectionReport(
            overall_risk=overall,
            risk_score=score,
            risks=risks,
            preventable_amount=round(preventable, 2),
        )

    # ── Rule check methods ──

    # ICD前缀→DRG合法MDC映射（CHS-DRG 1.2标准）
    # 关键：DRG字母前缀≠ICD字母前缀。例如I(循环系统)的PCI→DRG F开头是合法的
    _ICD_TO_DRG_MDC: dict[str, set[str]] = {
        "I": {"F", "I"},  # 循环系统→MDCE(F开头)或MDCI
        "J": {"E", "J"},  # 呼吸→MDCD(E)或MDCJ
        "K": {"G", "H", "K"},  # 消化→MDCG(G/H)或MDCK
        "N": {"L", "N"},  # 泌尿→MDCL(L)或MDCN
        "M": {"I", "M"},  # 骨骼→MDCI(I)或MDCM
        "G": {"B", "G"},  # 神经→MDCA(B)或MDCG
        "O": {"O", "N"},  # 产科→MDCO(O)或MDCN
        "C": {"R", "C"},  # 肿瘤→MDCR(R)或MDCC
        "S": {"I", "S"},  # 外伤→MDCI(I)或MDCS
        "E": {"K", "E"},  # 内分泌→MDCK(K)或MDCE
        "A": {"A", "B"},  # 感染→MDCA
        "B": {"A", "B"},  # 感染
        "D": {"D", "F"},  # 血液→MDCD或MDCF
        "H": {"C", "H"},  # 眼科→MDCC或MDCH
        "L": {"J", "L"},  # 皮肤→MDCJ或MDCL
        "R": {"R", "F"},  # 症状→多MDC可能
        "Z": {"Z", "F", "O"},  # 健康因素→多MDC
    }

    def _check_primary_drg_mismatch(self, primary: dict, drg: dict) -> RejectionRisk | None:
        diag_code = primary.get("code", "")
        drg_code = drg.get("drg_code", "")

        if not diag_code or not drg_code:
            return None

        diag_prefix = diag_code[0].upper()
        drg_prefix = drg_code[0].upper()

        # Z/R codes are special — many MDCs possible, skip
        if diag_prefix in ("Z", "R"):
            return None

        # Check against CHS-DRG 1.2 valid ICD→DRG mapping
        valid_drg_prefixes = self._ICD_TO_DRG_MDC.get(diag_prefix)
        if valid_drg_prefixes is None:
            return None  # Unknown prefix, don't flag

        if drg_prefix not in valid_drg_prefixes:
            return RejectionRisk(
                rule_id="RR-001",
                rule_name="主要诊断与DRG不匹配",
                risk_level=RiskLevel.HIGH,
                description=(
                    f"主要诊断 {primary.get('code')} {primary.get('name', '')} "
                    f"({diag_prefix}类)与DRG {drg.get('drg_code', '')} ({drg_prefix}类)不在CHS-DRG标准映射中"
                ),
                suggestion="核实主要诊断是否正确，或确认DRG分组逻辑",
                affected_code=primary.get("code", ""),
                estimated_loss=self.drg_base_rate * drg.get("weight", 1.0),
            )
        return None

    def _check_procedure_indications(
        self, procedures: list, primary: dict, secondaries: list
    ) -> list[RejectionRisk]:
        risks = []
        all_diag_names = {primary.get("name", "")} if primary else set()
        for s in secondaries:
            all_diag_names.add(s.get("name", ""))

        # Body system mapping
        proc_body_map = {
            "心脏": ["冠心病", "心肌梗死", "心绞痛", "心力衰竭", "心脏", "心"],
            "冠状动脉": ["冠心病", "心肌梗死", "冠脉", "冠状动脉"],
            "肺": ["肺", "肺癌", "肺炎", "呼吸"],
            "胃": ["胃", "胃癌", "溃疡", "消化"],
            "肠": ["肠", "结肠", "直肠", "消化"],
            "肝": ["肝", "肝癌", "肝硬化", "消化"],
            "胆": ["胆囊", "胆结石", "胆囊炎"],
            "肾": ["肾", "肾癌", "结石", "泌尿"],
            "子宫": ["子宫", "肌瘤", "妇科"],
            "卵巢": ["卵巢", "囊肿", "妇科"],
            "髋": ["髋", "骨折", "股骨头", "骨科"],
            "膝": ["膝", "骨关节炎", "骨折", "骨科"],
            "脊柱": ["脊柱", "椎", "骨科", "神经"],
        }

        for proc in procedures:
            proc_name = proc.get("name", "")
            matched = False
            for kw, diag_kws in proc_body_map.items():
                if kw in proc_name:
                    if not any(any(dk in dn for dk in diag_kws) for dn in all_diag_names):
                        matched = False
                        break
                    matched = True
                    break
            else:
                matched = True  # No keyword match = skip check

            if not matched:
                risks.append(
                    RejectionRisk(
                        rule_id="RR-002",
                        rule_name="手术操作无对应诊断",
                        risk_level=RiskLevel.HIGH,
                        description=f"手术 {proc.get('code', '')} {proc_name} 缺少对应的临床诊断",
                        suggestion=f"请核实{proc_name}的临床指征，补充对应诊断编码",
                        affected_code=proc.get("code", ""),
                        estimated_loss=self.drg_base_rate * 0.5,
                    )
                )

        return risks

    def _check_contradictory(self, all_diags: list) -> list[RejectionRisk]:
        risks = []
        diag_names = {d.get("name", "") for d in all_diags if d}
        diag_text = " ".join(diag_names)

        for set_a, set_b, reason in CONTRADICTORY_PAIRS:
            matched_a = next((term for term in sorted(set_a) if term in diag_text), "")
            matched_b = next((term for term in sorted(set_b) if term in diag_text), "")
            if matched_a and matched_b:
                risks.append(
                    RejectionRisk(
                        rule_id="RR-003",
                        rule_name="诊断矛盾",
                        risk_level=RiskLevel.MEDIUM,
                        description=f"诊断中存在{reason}：{matched_a} vs {matched_b}",
                        suggestion="核实两份诊断的临床依据，排除编码错误或确认是否为药物性/一过性",
                    )
                )
        return risks[:2]  # Max 2 contradiction flags

    def _check_mcc_upcoding(self, secondary_diags: list, content: str) -> list[RejectionRisk]:
        risks = []
        for diag in secondary_diags:
            name = diag.get("name", "")
            for mcc_kw, weight_delta in MCC_FLAGS.items():
                # Check if content has strong evidence for this MCC.
                if mcc_kw in name and (mcc_kw not in content or len(content.split(mcc_kw)) < 3):
                    risks.append(
                        RejectionRisk(
                            rule_id="RR-101",
                            rule_name="疑似诊断升级（MCC嫌疑）",
                            risk_level=RiskLevel.HIGH,
                            description=f"MCC诊断 {diag.get('code', '')} {name} 在病历中缺乏详细依据描述",
                            suggestion=f"在病程记录中补充{name}的检查结果、会诊意见和治疗措施",
                            affected_code=diag.get("code", ""),
                            estimated_loss=self.drg_base_rate * weight_delta,
                        )
                    )
        return risks

    def _check_missing_cc(self, content: str, all_diags: list) -> list[RejectionRisk]:
        """Check for missed CC/MCC that could increase DRG weight"""
        from src.services.llm_engine.medical_rules import COMMON_MISSED

        risks = []
        coded_text = " ".join(d.get("name", "") for d in all_diags)

        for keyword, (code, name) in COMMON_MISSED.items():
            if keyword in content and keyword not in coded_text:
                risks.append(
                    RejectionRisk(
                        rule_id="RR-301",
                        rule_name="漏编并发症/合并症",
                        risk_level=RiskLevel.MEDIUM,
                        description=f"病历提及'{keyword}'但未编码，遗漏将导致DRG权重降低",
                        suggestion=f"补充编码 {code} - {name}，可提升DRG权重",
                        affected_code=code,
                        estimated_loss=self.drg_base_rate * 0.15,
                    )
                )
        return risks[:3]  # Max 3 missing CC flags

    def _check_los_mismatch(self, patient: dict, drg: dict) -> RejectionRisk | None:
        days = patient.get("days_of_stay", 0)
        avg_days = drg.get("avg_los", 7)
        if days > avg_days * 1.5:
            excess = (days - avg_days) / avg_days * 100
            return RejectionRisk(
                rule_id="RR-401",
                rule_name="住院天数与DRG不匹配",
                risk_level=RiskLevel.LOW,
                description=f"住院{days}天，超出该DRG平均{avg_days}天{excess:.0f}%",
                suggestion="病历中记录延长住院的具体原因",
            )
        return None

    def _check_high_value_devices(self, content: str, procedures: list) -> list[RejectionRisk]:
        risks = []
        proc_text = " ".join(p.get("name", "") for p in procedures)
        for device, expected_proc in HIGH_VALUE_DEVICES.items():
            if device in content and expected_proc not in proc_text:
                risks.append(
                    RejectionRisk(
                        rule_id="RR-302",
                        rule_name="高值耗材无对应编码",
                        risk_level=RiskLevel.MEDIUM,
                        description=f"病历涉及'{device}'但缺少对应操作编码({expected_proc})",
                        suggestion=f"补充操作编码{expected_proc}以匹配耗材使用",
                        estimated_loss=self.drg_base_rate * 0.3,
                    )
                )
        return risks

    def _check_cost_deviation(self, cost: float, drg: dict) -> RejectionRisk | None:
        weight = drg.get("weight", 1.0)
        expected = self.drg_base_rate * weight
        deviation = (cost - expected) / expected * 100
        if abs(deviation) > 30:
            level = RiskLevel.HIGH if abs(deviation) > 50 else RiskLevel.MEDIUM
            return RejectionRisk(
                rule_id="RR-202",
                rule_name="费用与DRG权重偏离",
                risk_level=level,
                description=f"费用{cost:.0f}元，偏离DRG标准{expected:.0f}元({deviation:+.0f}%)",
                suggestion="核查费用明细，排除编码错误或过度医疗",
                estimated_loss=abs(cost - expected) * 0.2 if deviation > 0 else 0,
            )
        return None


# Singleton
rejection_engine = RejectionRiskEngine()

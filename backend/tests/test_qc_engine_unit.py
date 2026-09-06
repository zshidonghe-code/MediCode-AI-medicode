"""QC Engine unit tests — no server required."""

import pytest

from src.services.qc_engine.engine import QCEngine, QCIssue, QCResult, RuleType, Severity


@pytest.fixture
def qc_engine():
    return QCEngine()


@pytest.mark.asyncio
async def test_qc_with_full_record_passes_check(qc_engine):
    content = (
        "入院情况：患者因'胸痛3天'入院。"
        "既往史：高血压病史5年。"
        "体格检查：BP150/90mmHg。"
        "辅助检查：心电图正常。"
        "诊疗经过：给予抗凝、降压等治疗。"
        "出院诊断：冠心病，不稳定型心绞痛，原发性高血压"
        "出院医嘱：1.阿司匹林100mg qd 2.一月后复查"
    )
    result = await qc_engine.check("discharge", content, None, None)
    assert result.score >= 0


@pytest.mark.asyncio
async def test_qc_section_completeness(qc_engine):
    content = "患者入院治疗。诊疗经过：给予药物治疗。出院医嘱：定期复查。"
    result = await qc_engine.check("discharge", content, None, None)
    has_missing_diag = any("出院诊断" in i.description for i in result.issues)
    assert has_missing_diag


def test_qc_score_calculation():
    issues = [
        QCIssue(rule_id="T1", rule_name="test", rule_type=RuleType.COMPLETENESS,
                severity=Severity.CRITICAL, description=""),
        QCIssue(rule_id="T2", rule_name="test", rule_type=RuleType.LOGIC,
                severity=Severity.MAJOR, description=""),
        QCIssue(rule_id="T3", rule_name="test", rule_type=RuleType.CODING,
                severity=Severity.MINOR, description=""),
    ]
    result = QCResult(record_id=1, issues=issues)
    # 1 critical (-10) + 1 major (-5) + 1 minor (-2) = 83
    assert result.score == 83.0
    assert result.critical_count == 1
    assert result.major_count == 1
    assert result.minor_count == 1
    assert result.total == 3


def test_qc_score_max_deduction():
    issues = [QCIssue(
        rule_id=f"T{i}", rule_name="test", rule_type=RuleType.COMPLETENESS,
        severity=Severity.CRITICAL, description="",
    ) for i in range(15)]
    result = QCResult(record_id=1, issues=issues)
    assert result.score == 0.0


@pytest.mark.asyncio
async def test_qc_diagnosis_gender_check(qc_engine):
    content = "患者因子宫肌瘤入院治疗。诊疗经过：给予药物保守治疗。出院诊断：子宫肌瘤。出院医嘱：定期复查。"
    result = await qc_engine.check(
        "discharge", content,
        coding_result={
            "primary_diagnosis": {"code": "D25.900", "name": "子宫平滑肌瘤"},
            "secondary_diagnoses": [],
            "procedures": [],
        },
        patient_info={"gender": "male"},
    )
    has_gender_issue = any("QC-101" in i.rule_id for i in result.issues)
    assert has_gender_issue


@pytest.mark.asyncio
async def test_qc_symptom_as_primary(qc_engine):
    content = "患者因发热入院。出院诊断：发热。出院医嘱：随访。"
    result = await qc_engine.check(
        "discharge", content,
        coding_result={
            "primary_diagnosis": {"code": "R50.900", "name": "发热"},
            "secondary_diagnoses": [
                {"code": "J18.900", "name": "社区获得性肺炎"},
            ],
            "procedures": [],
        },
    )
    has_primary_issue = any(
        i.rule_id in ("QC-103", "QC-401") for i in result.issues
    )
    assert has_primary_issue


@pytest.mark.asyncio
async def test_qc_missing_secondary_diagnosis(qc_engine):
    content = "患者有高血压、糖尿病史。出院诊断：冠心病。出院医嘱：长期服药。"
    result = await qc_engine.check(
        "discharge", content,
        coding_result={
            "primary_diagnosis": {"code": "I25.100", "name": "冠状动脉粥样硬化性心脏病"},
            "secondary_diagnoses": [],
            "procedures": [],
        },
    )
    has_missed = any("QC-202" in i.rule_id for i in result.issues)
    assert has_missed


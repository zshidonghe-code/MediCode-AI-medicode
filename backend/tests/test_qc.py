"""QC Quality Check API integration tests."""
import pytest


@pytest.fixture
def coding_result():
    return {
        "primary_diagnosis": {"code": "I21.900", "name": "急性心肌梗死"},
        "secondary_diagnoses": [
            {"code": "I25.100", "name": "冠状动脉粥样硬化性心脏病"},
            {"code": "I10.x00", "name": "原发性高血压"},
            {"code": "E11.900", "name": "2型糖尿病"},
        ],
        "procedures": [
            {"code": "36.0700", "name": "冠状动脉药物洗脱支架植入"},
        ],
    }


@pytest.mark.asyncio
async def test_qc_check_fast(client, pci_case, coding_result):
    """规则引擎QC应在500ms内完成（默认use_llm=False）"""
    r = await client.post("/api/v1/qc/check", json={
        **pci_case, "coding_result": coding_result,
        "patient_info": {"gender": "male", "age": 65, "days_of_stay": 7},
    })
    assert r.status_code == 200
    data = r.json()
    assert data["processing_time_ms"] < 500


@pytest.mark.asyncio
async def test_qc_score_range(client, pci_case, coding_result):
    """QC评分应在合理范围内"""
    r = await client.post("/api/v1/qc/check", json={
        **pci_case, "coding_result": coding_result,
        "patient_info": {"gender": "male", "age": 65, "days_of_stay": 7},
    })
    data = r.json()
    assert 0 <= data["qc_score"] <= 100


@pytest.mark.asyncio
async def test_qc_missing_discharge_instruction(client, pci_case, coding_result):
    """缺少出院医嘱应被检测为严重问题"""
    # Use content without 出院医嘱
    content_no_inst = pci_case["content"].split("出院医嘱")[0]
    r = await client.post("/api/v1/qc/check", json={
        "record_id": 9999, "record_type": "discharge", "content": content_no_inst,
        "coding_result": coding_result,
        "patient_info": {"gender": "male", "age": 65, "days_of_stay": 7},
    })
    data = r.json()
    has_issue = any(
        i["rule_id"] == "QC-004" and i["severity"] == "critical"
        for i in data["issues"]
    )
    assert has_issue, "QC-004 should flag missing discharge instruction"


@pytest.mark.asyncio
async def test_qc_rules_endpoint(client):
    """规则列表端点应返回所有规则"""
    r = await client.get("/api/v1/qc/rules")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] > 10
    assert len(data["rules"]) > 10


@pytest.mark.asyncio
async def test_qc_rules_filter(client):
    """规则列表应支持按类型过滤"""
    r = await client.get("/api/v1/qc/rules", params={"rule_type": "completeness"})
    assert r.status_code == 200
    data = r.json()
    for rule in data["rules"]:
        assert rule["type"] == "completeness"

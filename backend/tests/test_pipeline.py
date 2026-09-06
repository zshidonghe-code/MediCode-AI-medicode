"""Pipeline save API integration tests."""
import time

import pytest

UNIQUE = str(int(time.time() * 1000))[-6:]


def u(text):
    return f"[{UNIQUE}] {text}"


@pytest.mark.asyncio
async def test_pipeline_save_coding_only(client, pci_case):
    """POST /pipeline/save with only coding_result should succeed."""
    r = await client.post("/api/v1/pipeline/save", json={
        "content": u(pci_case["content"]),
        "record_type": "discharge",
        "coding_result": {
            "primary_diagnosis": {"code": "I21.900", "name": "急性心肌梗死"},
            "secondary_diagnoses": [
                {"code": "I25.100", "name": "冠状动脉粥样硬化性心脏病"},
            ],
            "procedures": [
                {"code": "36.0700", "name": "冠状动脉药物洗脱支架植入"},
            ],
            "total_confidence": 0.88,
        },
        "department": "智能编码",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["patient_id"].startswith("CODE")


@pytest.mark.asyncio
async def test_pipeline_save_full(client, pci_case):
    """POST /pipeline/save with coding + qc + drg results should persist all."""
    r = await client.post("/api/v1/pipeline/save", json={
        "content": u(pci_case["content"]),
        "record_type": "discharge",
        "coding_result": {
            "primary_diagnosis": {"code": "I21.900", "name": "急性心肌梗死"},
            "secondary_diagnoses": [
                {"code": "I10.x00", "name": "原发性高血压"},
            ],
            "procedures": [
                {"code": "36.0700", "name": "冠状动脉药物洗脱支架植入"},
            ],
            "total_confidence": 0.92,
        },
        "qc_result": {
            "issues": [
                {
                    "severity": "critical",
                    "line_snippet": "缺少出院医嘱",
                    "suggestion": "补充出院医嘱",
                },
            ],
        },
        "drg_result": {"drg_code": "FC19", "weight": 3.5},
        "department": "流水线",
        "patient_info": {"age": 65, "gender": "male"},
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["patient_id"].startswith("PIPE")
    assert data["record_id"] is not None
    assert data["coding_result_id"] is not None
    assert len(data["qc_result_ids"]) > 0


@pytest.mark.asyncio
async def test_pipeline_save_returns_record_id(client):
    """Response should contain patient_id, record_id, and coding_result_id."""
    r = await client.post("/api/v1/pipeline/save", json={
        "content": u("社区获得性肺炎，无手术史"),
        "coding_result": {
            "primary_diagnosis": {"code": "J18.900", "name": "社区获得性肺炎"},
            "total_confidence": 0.85,
        },
        "department": "智能编码",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["patient_id"] is not None
    assert data["record_id"] is not None
    assert data["coding_result_id"] is not None
    assert isinstance(data["qc_result_ids"], list)


@pytest.mark.asyncio
async def test_pipeline_save_drg_only(client):
    """POST /pipeline/save with only DRG result and ICD codes should succeed."""
    r = await client.post("/api/v1/pipeline/save", json={
        "content": u("DRG-only test case"),
        "drg_result": {"drg_code": "FC19", "weight": 3.5},
        "primary_diagnosis_code": "I21.900",
        "secondary_diagnosis_codes": ["I10.x00"],
        "procedure_codes": ["36.0700"],
        "department": "DRG分组",
        "patient_info": {"age": 65, "gender": "male"},
    })
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["patient_id"].startswith("DRG")
    assert data["coding_result_id"] is not None


@pytest.mark.asyncio
async def test_pipeline_save_duplicate_content(client):
    """Resubmitting identical content should succeed (find-or-create patient)."""
    content = u("Duplicate content test - same content twice")
    payload = {
        "content": content,
        "record_type": "discharge",
        "coding_result": {
            "primary_diagnosis": {"code": "J18.900", "name": "肺炎"},
            "total_confidence": 0.90,
        },
        "department": "智能编码",
    }
    # First save
    r1 = await client.post("/api/v1/pipeline/save", json=payload)
    assert r1.status_code == 200, f"First save failed: {r1.text}"
    d1 = r1.json()
    # Second save with identical content — should reuse patient, not crash
    r2 = await client.post("/api/v1/pipeline/save", json=payload)
    assert r2.status_code == 200, f"Second save (duplicate) failed: {r2.text}"
    d2 = r2.json()
    assert d2["success"] is True
    # Same patient_id (reused), different record_id (new record)
    assert d2["patient_id"] == d1["patient_id"]
    assert d2["record_id"] != d1["record_id"]


@pytest.mark.asyncio
async def test_pipeline_save_data_integrity(client):
    """Saved data should be retrievable and correct."""
    content = u("Data integrity verification test case")
    r = await client.post("/api/v1/pipeline/save", json={
        "content": content,
        "record_type": "discharge",
        "coding_result": {
            "primary_diagnosis": {"code": "I21.900", "name": "急性心肌梗死"},
            "secondary_diagnoses": [
                {"code": "I25.100", "name": "冠状动脉粥样硬化性心脏病"},
            ],
            "total_confidence": 0.88,
        },
        "qc_result": {
            "issues": [
                {"severity": "critical", "line_snippet": "缺项", "suggestion": "补全"},
            ],
        },
        "department": "流水线",
        "patient_info": {"age": 70, "gender": "male"},
    })
    assert r.status_code == 200, f"Save failed: {r.text}"
    data = r.json()
    record_id = data["record_id"]
    coding_result_id = data["coding_result_id"]

    # Verify data via dashboard overview (confirms records exist in aggregates)
    r2 = await client.get("/api/v1/dashboard/overview", params={"days": 9999})
    assert r2.status_code == 200
    overview = r2.json()
    assert overview["total_cases"] > 0
    # Verify coding result exists
    assert coding_result_id is not None
    assert len(data["qc_result_ids"]) > 0

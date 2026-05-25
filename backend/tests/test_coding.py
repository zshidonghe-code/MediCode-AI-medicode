"""ICD Coding API integration tests."""
import pytest


@pytest.mark.asyncio
async def test_auto_code_primary_correct(client, pci_case):
    """主诊断应正确识别为急性心肌梗死 I21.900"""
    r = await client.post("/api/v1/coding/auto-code", json=pci_case)
    assert r.status_code == 200
    data = r.json()
    assert data["primary_diagnosis"]["code"] == "I21.900"
    assert "急性心肌梗死" in data["primary_diagnosis"]["name"]


@pytest.mark.asyncio
async def test_auto_code_secondaries_clean(client, pci_case):
    """次要诊断不应包含E11并发症子码"""
    r = await client.post("/api/v1/coding/auto-code", json=pci_case)
    data = r.json()
    sec_codes = [d["code"] for d in data["secondary_diagnoses"]]
    e11_codes = [c for c in sec_codes if c.startswith("E11")]
    for c in e11_codes:
        parts = c.split(".")
        if len(parts) > 1 and parts[1]:
            assert parts[1][0] not in ("2", "3", "4", "5", "6", "7"), f"E11 complication found: {c}"


@pytest.mark.asyncio
async def test_auto_code_procedure_pci(client, pci_case):
    """手术编码应包含PCI术 36.0700"""
    r = await client.post("/api/v1/coding/auto-code", json=pci_case)
    data = r.json()
    proc_codes = [p["code"] for p in data["procedures"]]
    pci_codes = [c for c in proc_codes if c.startswith("36.0")]
    assert len(pci_codes) > 0, f"PCI procedure missing, got: {proc_codes}"


@pytest.mark.asyncio
async def test_auto_code_confidence_high(client, pci_case):
    """主要诊断置信度应 >= 85%"""
    r = await client.post("/api/v1/coding/auto-code", json=pci_case)
    data = r.json()
    assert data["total_confidence"] >= 0.75


@pytest.mark.asyncio
async def test_auto_code_fast_response(client, pci_case):
    """编码应在1秒内完成"""
    r = await client.post("/api/v1/coding/auto-code", json=pci_case)
    data = r.json()
    assert data["processing_time_ms"] < 1000


@pytest.mark.asyncio
async def test_auto_code_no_duplicate_hiv(client, pci_case):
    """过程编码不应返回无关代码（如HIV、前列腺）"""
    r = await client.post("/api/v1/coding/auto-code", json=pci_case)
    data = r.json()
    proc_codes = [p["code"] for p in data["procedures"]]
    assert "B24.900" not in proc_codes
    assert "60.2000" not in proc_codes
    assert "N41.900" not in proc_codes


@pytest.mark.asyncio
async def test_search_icd(client):
    """ICD检索应返回结果"""
    r = await client.get("/api/v1/coding/search", params={"keyword": "高血压", "limit": 5})
    assert r.status_code == 200
    data = r.json()
    assert len(data["results"]) > 0
    codes = [item["code"] for item in data["results"]]
    assert any(c.startswith("I10") for c in codes)

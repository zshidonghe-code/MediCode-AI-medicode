"""DRG Grouper API integration tests."""
import pytest


@pytest.mark.asyncio
async def test_drg_group_pci_surgical(client):
    """PCI术后应分组为外科DRG"""
    r = await client.post("/api/v1/drg/group", json={
        "patient_age": 65,
        "patient_gender": "male",
        "primary_diagnosis_code": "I21.900",
        "secondary_diagnosis_codes": ["I25.100", "I10.x00", "E11.900"],
        "procedure_codes": ["36.0700"],
        "days_of_stay": 7,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["is_surgical"] is True, "PCI should be surgical DRG"
    assert data["drg_code"].startswith("FC"), f"Expected FC* DRG, got {data['drg_code']}"
    assert data["weight"] > 2.0, f"PCI weight should be > 2.0, got {data['weight']}"
    assert data["estimated_payment"] > 20000


@pytest.mark.asyncio
async def test_drg_group_medical_no_procedure(client):
    """无手术操作应为内科DRG"""
    r = await client.post("/api/v1/drg/group", json={
        "patient_age": 45,
        "patient_gender": "female",
        "primary_diagnosis_code": "J18.900",
        "secondary_diagnosis_codes": [],
        "procedure_codes": [],
        "days_of_stay": 8,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["is_surgical"] is False
    assert data["weight"] < 2.0


@pytest.mark.asyncio
async def test_drg_payment_calculation(client):
    """费用 = 权重 × 费率"""
    r = await client.post("/api/v1/drg/group", json={
        "patient_age": 65,
        "patient_gender": "male",
        "primary_diagnosis_code": "I21.900",
        "secondary_diagnosis_codes": ["I25.100"],
        "procedure_codes": ["36.0700"],
        "days_of_stay": 7,
    })
    data = r.json()
    expected = data["weight"] * data["rate"]
    assert abs(data["estimated_payment"] - expected) < 1


@pytest.mark.asyncio
async def test_drg_detail_endpoint(client):
    """DRG详情端点应查询数据库"""
    r = await client.get("/api/v1/drg/group/FC1")
    assert r.status_code == 200
    data = r.json()
    assert "weight" in data
    assert data["weight"] > 0


@pytest.mark.asyncio
async def test_drg_compare_endpoint(client):
    """DRG对比端点应返回差异"""
    r = await client.get("/api/v1/drg/compare", params={
        "record_id": 1,
        "ai_drg": "FC1",
        "manual_drg": "FD1",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["same"] is False
    assert data["payment_gap"] > 0

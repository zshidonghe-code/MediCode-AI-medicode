"""Admin API integration tests."""
import pytest
import httpx

from .conftest import BASE_URL


@pytest.mark.asyncio
async def test_admin_reset_preview(client):
    """POST /admin/reset with confirm=false should return counts without deleting."""
    r = await client.post("/api/v1/admin/reset", json={"confirm": False})
    assert r.status_code == 200
    data = r.json()
    assert data["preview"] is True
    assert "counts" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_admin_reset_requires_admin():
    """Non-admin user (coder) should receive 403 on admin reset."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
        login_r = await c.post("/api/v1/auth/login", data={
            "username": "coder",
            "password": "MediCode@2025Demo#Coder",
        })
        assert login_r.status_code == 200
        token = login_r.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"
        r = await c.post("/api/v1/admin/reset", json={"confirm": False})
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_export_coding_results_json(client):
    """GET /admin/export/coding-results should return a JSON blob."""
    r = await client.get("/api/v1/admin/export/coding-results")
    assert r.status_code == 200
    assert "application/json" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_export_patient_summaries_csv(client):
    """GET /admin/export/patient-summaries?format=csv should return a CSV blob."""
    r = await client.get(
        "/api/v1/admin/export/patient-summaries", params={"format": "csv"}
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_admin_requires_auth():
    """Unauthenticated access to admin endpoints should return 401."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
        r = await c.post("/api/v1/admin/reset", json={"confirm": False})
        assert r.status_code == 401

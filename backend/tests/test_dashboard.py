"""Dashboard API integration tests."""
import httpx
import pytest

from .conftest import BASE_URL


@pytest.mark.asyncio
async def test_overview_returns_200(client):
    r = await client.get("/api/v1/dashboard/overview")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_department_ranking_returns_200(client):
    r = await client.get("/api/v1/dashboard/department-ranking")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_qc_trend_returns_200(client):
    r = await client.get("/api/v1/dashboard/qc-trend")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_coding_accuracy_returns_200(client):
    r = await client.get("/api/v1/dashboard/coding-accuracy")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_high_frequency_issues_returns_200(client):
    r = await client.get("/api/v1/dashboard/high-frequency-issues")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_revenue_analysis_returns_200(client):
    r = await client.get("/api/v1/dashboard/revenue-analysis")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_response_structure(client):
    """Verify the overview endpoint returns all expected top-level keys."""
    r = await client.get("/api/v1/dashboard/overview")
    assert r.status_code == 200
    data = r.json()
    expected_keys = [
        "total_cases", "total_weight", "cmi", "avg_cost",
        "avg_stay_days", "cost_consumption_index", "time_consumption_index",
        "low_risk_mortality_rate", "ai_coding_rate", "qc_pass_rate",
    ]
    for key in expected_keys:
        assert key in data, f"Missing key: {key}"


@pytest.mark.asyncio
async def test_dashboard_days_param(client):
    """Verify the days query parameter is accepted and returns a trend."""
    r = await client.get("/api/v1/dashboard/qc-trend", params={"days": 30})
    assert r.status_code == 200
    data = r.json()
    assert "trend" in data
    assert isinstance(data["trend"], list)


@pytest.mark.asyncio
async def test_dashboard_numeric_fields_are_valid(client):
    """Numeric fields in overview should be non-negative numbers."""
    r = await client.get("/api/v1/dashboard/overview", params={"days": 9999})
    assert r.status_code == 200
    data = r.json()
    numeric_fields = [
        "total_cases", "total_weight", "cmi",
        "low_risk_mortality_rate", "ai_coding_rate", "qc_pass_rate",
    ]
    for key in numeric_fields:
        if key in data:
            val = data[key]
            if isinstance(val, (int, float)):
                assert val >= 0, f"{key} should be >= 0, got {val}"


@pytest.mark.asyncio
async def test_dashboard_unauthenticated():
    """Dashboard endpoints should require authentication."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10, trust_env=False) as c:
        r = await c.get("/api/v1/dashboard/overview")
        assert r.status_code == 401

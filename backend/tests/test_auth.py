"""Authentication API integration tests."""
import os

import pytest
import httpx

from .conftest import BASE_URL

ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD", "123456")


@pytest.mark.asyncio
async def test_login_success():
    """Demo admin credentials should return 200 with user info."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10, trust_env=False) as c:
        r = await c.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": ADMIN_PASSWORD,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password():
    """Wrong password should return 401."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10, trust_env=False) as c:
        r = await c.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "wrongpassword",
        })
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user():
    """Non-existent username should return 401."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10, trust_env=False) as c:
        r = await c.post("/api/v1/auth/login", data={
            "username": "nonexistent",
            "password": "somepassword",
        })
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client):
    """GET /me with valid token should return the authenticated user's info."""
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"
    assert "name" in data


@pytest.mark.asyncio
async def test_me_unauthenticated():
    """GET /me without a token should return 401."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10, trust_env=False) as c:
        r = await c.get("/api/v1/auth/me")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_token_format():
    """Login response should contain access_token and token_type fields."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10, trust_env=False) as c:
        r = await c.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": ADMIN_PASSWORD,
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, student_user):
    resp = await client.post("/api/v2/auth/login", json={
        "email": student_user.email,
        "password": "TestPass@123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, student_user):
    resp = await client.post("/api/v2/auth/login", json={
        "email": student_user.email,
        "password": "WrongPassword",
    })
    assert resp.status_code == 401
    assert "Invalid" in resp.json()["error"]


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    resp = await client.post("/api/v2/auth/login", json={
        "email": "nobody@nowhere.com",
        "password": "SomePass@123",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, student_user):
    # Login first
    login = await client.post("/api/v2/auth/login", json={
        "email": student_user.email, "password": "TestPass@123",
    })
    token = login.json()["access_token"]

    resp = await client.get("/api/v2/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == student_user.email
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_missing_auth_header(client: AsyncClient):
    resp = await client.get("/api/v2/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    resp = await client.get("/api/v2/auth/me",
                            headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, student_user):
    login = await client.post("/api/v2/auth/login", json={
        "email": student_user.email, "password": "TestPass@123",
    })
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v2/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

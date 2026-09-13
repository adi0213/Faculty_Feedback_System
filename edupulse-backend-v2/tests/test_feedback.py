"""Tests for feedback submission endpoint."""
import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.faculty import FacultyProfile
from app.models.user import User


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/v2/auth/login", json={"email": email, "password": password})
    return resp.json().get("access_token", "")


@pytest.mark.asyncio
async def test_feedback_submit_success(client: AsyncClient, student_user: User, faculty_profile: FacultyProfile):
    token = await _login(client, student_user.email, "TestPass@123")
    resp = await client.post(
        "/api/v2/feedback/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "faculty_profile_id": faculty_profile.id,
            "term": "2025-S2",
            "scores": {"clarity": 3, "methodology": 2, "punctuality": 4,
                       "fairness": 3, "approachability": 4, "pacing": 2},
            "comment": "Good teacher but could explain more clearly with examples.",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_feedback_duplicate_blocked(client: AsyncClient, student_user: User, faculty_profile: FacultyProfile):
    """Second submission for same faculty/term must be rejected."""
    token = await _login(client, student_user.email, "TestPass@123")
    payload = {
        "faculty_profile_id": faculty_profile.id,
        "term": "2025-S2",
        "scores": {"clarity": 3},
    }
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v2/feedback/submit", headers=headers, json=payload)
    resp2 = await client.post("/api/v2/feedback/submit", headers=headers, json=payload)
    assert resp2.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_feedback_faculty_role_rejected(client: AsyncClient, faculty_user: User):
    """Faculty should not be able to submit feedback."""
    token = await _login(client, faculty_user.email, "TestPass@123")
    resp = await client.post(
        "/api/v2/feedback/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "faculty_profile_id": "some-id",
            "term": "2025-S2",
            "scores": {"clarity": 3},
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_feedback_invalid_dimension(client: AsyncClient, student_user: User, faculty_profile: FacultyProfile):
    """Unknown dimension should be rejected by validation."""
    token = await _login(client, student_user.email, "TestPass@123")
    resp = await client.post(
        "/api/v2/feedback/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "faculty_profile_id": faculty_profile.id,
            "term": "2025-S2",
            "scores": {"unknown_dim": 3},
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_feedback_status_not_submitted(client: AsyncClient, student_user: User, faculty_profile: FacultyProfile):
    token = await _login(client, student_user.email, "TestPass@123")
    resp = await client.get(
        f"/api/v2/feedback/status",
        headers={"Authorization": f"Bearer {token}"},
        params={"faculty_profile_id": faculty_profile.id, "term": "2025-S2"},
    )
    assert resp.status_code == 200
    assert resp.json()["submitted"] is False

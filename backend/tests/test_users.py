"""Tests for the /api/v1/users/ endpoints."""
import uuid
import pytest
from httpx import AsyncClient

from backend.tests.helpers import register_and_login, auth_headers


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def token(client: AsyncClient) -> str:
    return await register_and_login(client)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, token: str):
    """Authenticated GET /users/me returns the current user's details."""
    resp = await client.get("/api/v1/users/me", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    user = data["data"]
    assert "id" in user
    assert "email" in user
    assert "first_name" in user
    assert "last_name" in user
    assert "organization_id" in user
    assert "status" in user


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient, token: str):
    """PATCH /users/me with a new first_name returns the updated user."""
    hdrs = auth_headers(token)
    resp = await client.patch(
        "/api/v1/users/me",
        json={"first_name": "UpdatedFirst", "last_name": "UpdatedLast"},
        headers=hdrs,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["first_name"] == "UpdatedFirst"
    assert data["last_name"] == "UpdatedLast"


@pytest.mark.asyncio
async def test_list_users_requires_auth(client: AsyncClient):
    """GET /users/ without an Authorization header returns 401."""
    resp = await client.get("/api/v1/users/")
    assert resp.status_code == 401, (
        f"Expected 401 Unauthorized without token, got {resp.status_code}: {resp.text}"
    )


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, token: str):
    """A logged-in user can fetch their own user record by ID."""
    hdrs = auth_headers(token)
    # First get /me to find own ID
    me_resp = await client.get("/api/v1/users/me", headers=hdrs)
    assert me_resp.status_code == 200
    user_id = me_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/users/{user_id}", headers=hdrs)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["id"] == user_id


@pytest.mark.asyncio
async def test_list_users_returns_paginated_response(client: AsyncClient, token: str):
    """GET /users/ with a valid token returns a paginated list."""
    resp = await client.get("/api/v1/users/", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert "data" in body
    assert "total" in body
    assert "page" in body
    assert "per_page" in body
    assert body["total"] >= 1

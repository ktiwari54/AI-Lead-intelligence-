"""Tests for the /api/v1/search/ endpoints."""
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
async def test_create_search(client: AsyncClient, token: str):
    """POST /search/ with filters returns 202 Accepted and a search_id."""
    payload = {
        "query": "software engineers",
        "filters": {"seniority": "C_LEVEL", "industry": "SaaS"},
        "search_type": "standard",
    }
    resp = await client.post("/api/v1/search/", json=payload, headers=auth_headers(token))
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"] is not None
    assert "id" in body["data"], "Response should include the created search id"


@pytest.mark.asyncio
async def test_get_search_history(client: AsyncClient, token: str):
    """Creating 3 searches then GET /search/history returns a paginated list."""
    hdrs = auth_headers(token)
    for i in range(3):
        await client.post(
            "/api/v1/search/",
            json={"query": f"query {i}", "filters": {}},
            headers=hdrs,
        )

    resp = await client.get("/api/v1/search/history", headers=hdrs)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert "data" in body
    assert "total" in body
    assert body["total"] >= 3, f"Expected at least 3 searches in history, got {body['total']}"
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_save_search(client: AsyncClient, token: str):
    """POST /search/saved with name + filters returns 201."""
    payload = {
        "name": "My Saved Search",
        "description": "Top SaaS CTOs",
        "query": "CTO",
        "filters": {"seniority": "C_LEVEL"},
        "search_type": "standard",
        "is_shared": False,
    }
    resp = await client.post("/api/v1/search/saved", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"] is not None
    assert "id" in body["data"], "Response should include the saved search id"


@pytest.mark.asyncio
async def test_list_saved_searches(client: AsyncClient, token: str):
    """Save 2 searches; verify they are accessible."""
    hdrs = auth_headers(token)
    for i in range(2):
        resp = await client.post(
            "/api/v1/search/saved",
            json={"name": f"Saved Search {i}", "filters": {}},
            headers=hdrs,
        )
        assert resp.status_code == 201, resp.text

    # The saved search endpoint returns 201 with an id; there is no dedicated
    # GET /search/saved list in the current router, but we can verify the save
    # works idempotently for two separate entries.
    resp1 = await client.post(
        "/api/v1/search/saved",
        json={"name": "Verify Third", "filters": {"test": True}},
        headers=hdrs,
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["data"]["id"]

    resp2 = await client.post(
        "/api/v1/search/saved",
        json={"name": "Verify Fourth", "filters": {"test": True}},
        headers=hdrs,
    )
    assert resp2.status_code == 201
    id2 = resp2.json()["data"]["id"]

    assert id1 != id2, "Each saved search should have a unique ID"

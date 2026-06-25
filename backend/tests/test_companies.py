"""Tests for the /api/v1/companies/ endpoints."""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.tests.helpers import register_and_login, auth_headers
from backend.app.companies.models import Company


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
async def test_create_company(client: AsyncClient, token: str):
    """POST /companies/ with valid data returns 201 and the created company."""
    payload = {"company_name": "Acme Corp", "website": "https://acme.example.com"}
    resp = await client.post("/api/v1/companies/", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["company_name"] == "Acme Corp"
    assert "id" in data["data"]
    assert "organization_id" in data["data"]


@pytest.mark.asyncio
async def test_create_company_missing_name(client: AsyncClient, token: str):
    """POST /companies/ without company_name returns 422 Unprocessable Entity."""
    resp = await client.post("/api/v1/companies/", json={"website": "https://acme.example.com"}, headers=auth_headers(token))
    assert resp.status_code == 422, resp.text


@pytest.mark.asyncio
async def test_list_companies(client: AsyncClient, token: str):
    """Creating 3 companies then listing returns at least those 3 with pagination fields."""
    hdrs = auth_headers(token)
    for i in range(3):
        await client.post("/api/v1/companies/", json={"company_name": f"ListCo {i}"}, headers=hdrs)

    resp = await client.get("/api/v1/companies/", headers=hdrs)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert "data" in body
    assert "total" in body
    assert "page" in body
    assert "per_page" in body
    assert body["total"] >= 3
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_get_company(client: AsyncClient, token: str):
    """Create a company then GET by ID returns matching data."""
    hdrs = auth_headers(token)
    create_resp = await client.post("/api/v1/companies/", json={"company_name": "GetMe Corp"}, headers=hdrs)
    assert create_resp.status_code == 201
    company_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/companies/{company_id}", headers=hdrs)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["id"] == company_id
    assert resp.json()["data"]["company_name"] == "GetMe Corp"


@pytest.mark.asyncio
async def test_get_company_not_found(client: AsyncClient, token: str):
    """GET with a random UUID that doesn't exist returns 404."""
    random_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/companies/{random_id}", headers=auth_headers(token))
    assert resp.status_code == 404, resp.text


@pytest.mark.asyncio
async def test_update_company(client: AsyncClient, token: str):
    """PATCH an existing company and verify the field is updated."""
    hdrs = auth_headers(token)
    create_resp = await client.post("/api/v1/companies/", json={"company_name": "OldName Inc"}, headers=hdrs)
    assert create_resp.status_code == 201
    company_id = create_resp.json()["data"]["id"]

    patch_resp = await client.patch(
        f"/api/v1/companies/{company_id}",
        json={"company_name": "NewName Inc"},
        headers=hdrs,
    )
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["data"]["company_name"] == "NewName Inc"


@pytest.mark.asyncio
async def test_delete_company(client: AsyncClient, token: str):
    """DELETE a company, then GET returns 404."""
    hdrs = auth_headers(token)
    create_resp = await client.post("/api/v1/companies/", json={"company_name": "ToDelete LLC"}, headers=hdrs)
    assert create_resp.status_code == 201
    company_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/api/v1/companies/{company_id}", headers=hdrs)
    assert del_resp.status_code == 200, del_resp.text

    get_resp = await client.get(f"/api/v1/companies/{company_id}", headers=hdrs)
    assert get_resp.status_code == 404, "Deleted company should not be found"


@pytest.mark.asyncio
async def test_filter_companies_by_name(client: AsyncClient, token: str):
    """Filter companies by query string returns only matching companies."""
    hdrs = auth_headers(token)
    await client.post("/api/v1/companies/", json={"company_name": "FilterTarget Alpha"}, headers=hdrs)
    await client.post("/api/v1/companies/", json={"company_name": "FilterTarget Beta"}, headers=hdrs)
    await client.post("/api/v1/companies/", json={"company_name": "SomethingElse Corp"}, headers=hdrs)

    resp = await client.get("/api/v1/companies/?query=FilterTarget", headers=hdrs)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    names = [c["company_name"] for c in body["data"]]
    assert all("FilterTarget" in name for name in names), (
        f"Expected only FilterTarget companies, got: {names}"
    )
    assert len(names) >= 2


@pytest.mark.asyncio
async def test_company_soft_delete(client: AsyncClient, token: str, db_session: AsyncSession):
    """After DELETE via API the DB row should have deleted_at set (soft delete)."""
    hdrs = auth_headers(token)
    create_resp = await client.post("/api/v1/companies/", json={"company_name": "SoftDel Corp"}, headers=hdrs)
    assert create_resp.status_code == 201
    company_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/api/v1/companies/{company_id}", headers=hdrs)
    assert del_resp.status_code == 200

    # Refresh from DB (bypassing soft-delete filter used by the service)
    result = await db_session.execute(
        select(Company).where(Company.id == uuid.UUID(company_id))
    )
    company_row = result.scalar_one_or_none()
    assert company_row is not None, "Row should still exist in DB after soft delete"
    assert company_row.deleted_at is not None, "deleted_at should be set after soft delete"

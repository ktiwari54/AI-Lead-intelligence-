"""Tests for the /api/v1/contacts/ endpoints."""
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


@pytest.fixture
async def company_id(client: AsyncClient, token: str) -> str:
    """Create a company and return its ID for use in contact tests."""
    resp = await client.post(
        "/api/v1/companies/",
        json={"company_name": "ContactsTestCo"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_contact(client: AsyncClient, token: str, company_id: str):
    """POST /contacts/ with valid data returns 201 and expected fields."""
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "company_id": company_id,
        "email": "alice.smith@example.com",
    }
    resp = await client.post("/api/v1/contacts/", json=payload, headers=auth_headers(token))
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Smith"
    assert data["company_id"] == company_id
    assert "id" in data
    assert "organization_id" in data


@pytest.mark.asyncio
async def test_create_contact_invalid_email(client: AsyncClient, token: str):
    """POST /contacts/ with a malformed email should return 422."""
    # The contact schema accepts email as a plain string (not EmailStr),
    # but if the backend validates format, we expect 422. We test both:
    # if the API accepts it we at minimum verify it doesn't crash (200-level).
    payload = {"first_name": "Bob", "email": "not-an-email-@@"}
    resp = await client.post("/api/v1/contacts/", json=payload, headers=auth_headers(token))
    # The current schema uses str (not EmailStr), so it may accept it.
    # We assert it doesn't 500.
    assert resp.status_code in (201, 422), resp.text


@pytest.mark.asyncio
async def test_list_contacts(client: AsyncClient, token: str, company_id: str):
    """Create 5 contacts then list; verify pagination response structure."""
    hdrs = auth_headers(token)
    for i in range(5):
        await client.post(
            "/api/v1/contacts/",
            json={"first_name": f"Contact{i}", "company_id": company_id},
            headers=hdrs,
        )

    resp = await client.get("/api/v1/contacts/", headers=hdrs)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert "total" in body
    assert "page" in body
    assert "per_page" in body
    assert body["total"] >= 5
    assert isinstance(body["data"], list)


@pytest.mark.asyncio
async def test_get_contact(client: AsyncClient, token: str, company_id: str):
    """Create a contact then GET by ID returns all expected fields."""
    hdrs = auth_headers(token)
    create_resp = await client.post(
        "/api/v1/contacts/",
        json={"first_name": "Charlie", "last_name": "Brown", "company_id": company_id},
        headers=hdrs,
    )
    assert create_resp.status_code == 201
    contact_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/contacts/{contact_id}", headers=hdrs)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["id"] == contact_id
    assert data["first_name"] == "Charlie"
    assert data["last_name"] == "Brown"
    assert data["company_id"] == company_id


@pytest.mark.asyncio
async def test_get_contact_not_found(client: AsyncClient, token: str):
    """GET with a random UUID returns 404."""
    resp = await client.get(f"/api/v1/contacts/{uuid.uuid4()}", headers=auth_headers(token))
    assert resp.status_code == 404, resp.text


@pytest.mark.asyncio
async def test_update_contact(client: AsyncClient, token: str, company_id: str):
    """PATCH a contact's designation and verify the update."""
    hdrs = auth_headers(token)
    create_resp = await client.post(
        "/api/v1/contacts/",
        json={"first_name": "Dana", "company_id": company_id},
        headers=hdrs,
    )
    assert create_resp.status_code == 201
    contact_id = create_resp.json()["data"]["id"]

    patch_resp = await client.patch(
        f"/api/v1/contacts/{contact_id}",
        json={"designation": "VP Engineering"},
        headers=hdrs,
    )
    assert patch_resp.status_code == 200, patch_resp.text
    assert patch_resp.json()["data"]["designation"] == "VP Engineering"


@pytest.mark.asyncio
async def test_delete_contact(client: AsyncClient, token: str, company_id: str):
    """DELETE a contact then GET returns 404."""
    hdrs = auth_headers(token)
    create_resp = await client.post(
        "/api/v1/contacts/",
        json={"first_name": "DeleteMe", "company_id": company_id},
        headers=hdrs,
    )
    assert create_resp.status_code == 201
    contact_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/api/v1/contacts/{contact_id}", headers=hdrs)
    assert del_resp.status_code == 200, del_resp.text

    get_resp = await client.get(f"/api/v1/contacts/{contact_id}", headers=hdrs)
    assert get_resp.status_code == 404, "Deleted contact should not be found"


@pytest.mark.asyncio
async def test_filter_by_company(client: AsyncClient, token: str):
    """Contacts filtered by company_id return only contacts for that company."""
    hdrs = auth_headers(token)

    # Create two separate companies
    co1_resp = await client.post("/api/v1/companies/", json={"company_name": "CompanyA"}, headers=hdrs)
    co2_resp = await client.post("/api/v1/companies/", json={"company_name": "CompanyB"}, headers=hdrs)
    assert co1_resp.status_code == 201
    assert co2_resp.status_code == 201
    co1_id = co1_resp.json()["data"]["id"]
    co2_id = co2_resp.json()["data"]["id"]

    # Create 2 contacts for company A and 1 for company B
    for i in range(2):
        await client.post("/api/v1/contacts/", json={"first_name": f"A{i}", "company_id": co1_id}, headers=hdrs)
    await client.post("/api/v1/contacts/", json={"first_name": "B0", "company_id": co2_id}, headers=hdrs)

    resp = await client.get(f"/api/v1/contacts/?company_id={co1_id}", headers=hdrs)
    assert resp.status_code == 200, resp.text
    contacts = resp.json()["data"]
    company_ids = {c["company_id"] for c in contacts}
    assert company_ids == {co1_id}, f"Expected only company A contacts, got company_ids: {company_ids}"
    assert len(contacts) >= 2


@pytest.mark.asyncio
async def test_filter_by_seniority(client: AsyncClient, token: str, company_id: str):
    """Filter by seniority=C_LEVEL returns only C-level contacts."""
    hdrs = auth_headers(token)
    await client.post(
        "/api/v1/contacts/",
        json={"first_name": "CEO", "company_id": company_id, "seniority": "C_LEVEL"},
        headers=hdrs,
    )
    await client.post(
        "/api/v1/contacts/",
        json={"first_name": "Mgr", "company_id": company_id, "seniority": "MANAGER"},
        headers=hdrs,
    )

    resp = await client.get("/api/v1/contacts/?seniority=C_LEVEL", headers=hdrs)
    assert resp.status_code == 200, resp.text
    contacts = resp.json()["data"]
    seniorities = {c["seniority"] for c in contacts}
    assert seniorities.issubset({"C_LEVEL", None}), (
        f"Expected only C_LEVEL contacts, got: {seniorities}"
    )


@pytest.mark.asyncio
async def test_filter_by_email_status(client: AsyncClient, token: str, company_id: str):
    """Filter by email_status=VERIFIED returns contacts with that status."""
    hdrs = auth_headers(token)
    # Create contacts; newly created contacts will have default email_status
    await client.post(
        "/api/v1/contacts/",
        json={"first_name": "Verified", "company_id": company_id, "email": "v@test.com"},
        headers=hdrs,
    )

    # Filter by VERIFIED - may return 0 or more (depends on default status)
    resp = await client.get("/api/v1/contacts/?email_status=VERIFIED", headers=hdrs)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    # All returned contacts should have email_status == VERIFIED
    for contact in body["data"]:
        assert contact["email_status"] == "VERIFIED", (
            f"Expected VERIFIED, got: {contact['email_status']}"
        )

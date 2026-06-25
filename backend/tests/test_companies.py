import pytest
from httpx import AsyncClient


async def get_token(client: AsyncClient, email: str) -> str:
    await client.post("/api/v1/auth/register", json={
        "first_name": "Test", "last_name": "User",
        "email": email, "password": "password123",
        "organization_name": "Test Org",
    })
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_list_company(client: AsyncClient):
    token = await get_token(client, "comp_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.post("/api/v1/companies", json={"company_name": "Acme Corp", "domain": "acme.com"}, headers=headers)
    assert r.status_code == 201
    company_id = r.json()["id"]

    r = await client.get("/api/v1/companies", headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = await client.get(f"/api/v1/companies/{company_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["company_name"] == "Acme Corp"

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "password": "securepass",
        "organization_name": "Acme Corp",
    })
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob@example.com",
        "password": "mypassword",
        "organization_name": "Bob Inc",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "bob@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

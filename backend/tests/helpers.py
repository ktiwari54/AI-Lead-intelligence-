"""Shared test helpers for authentication and common setup."""
import uuid
from httpx import AsyncClient


async def register_and_login(client: AsyncClient, suffix: str | None = None) -> str:
    """
    Register a new user (with a unique email) and log in.
    Returns the Bearer access token string.
    """
    unique = suffix or str(uuid.uuid4())[:8]
    email = f"testuser_{unique}@example.com"
    org_name = f"TestOrg {unique}"

    reg_payload = {
        "organization_name": org_name,
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": "SecurePass123!",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "SecurePass123!"},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    return login_resp.json()["data"]["access_token"]


def auth_headers(token: str) -> dict:
    """Return headers dict with Authorization bearer token."""
    return {"Authorization": f"Bearer {token}"}

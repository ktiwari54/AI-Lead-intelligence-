"""API key authentication support."""
from __future__ import annotations
import hashlib
import secrets
from uuid import UUID

from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.users.models import APIKey, User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    """Hash an API key for storage. We store the hash, never the raw key."""
    return hashlib.sha256(key.encode()).hexdigest()


async def get_user_from_api_key(
    api_key: str, db: AsyncSession
) -> tuple[User, UUID] | None:
    """Validate an API key and return (User, org_id) or None."""
    if not api_key or not api_key.startswith("ali_"):
        return None

    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        )
    )
    api_key_obj = result.scalar_one_or_none()
    if not api_key_obj:
        return None

    # Update last used
    from datetime import datetime, timezone
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    await db.flush()

    user_result = await db.execute(
        select(User).where(User.id == api_key_obj.user_id, User.is_active == True)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        return None

    return user, user.organization_id


async def get_current_user_or_api_key(
    request: Request, db: AsyncSession
) -> User:
    """
    Attempt JWT auth first, then fall back to API key auth.
    Raises 401 if neither succeeds.
    """
    from backend.app.common.deps import get_current_user_from_token

    # Try JWT first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            return await get_current_user_from_token(token, db)
        except Exception:
            pass

    # Try API key
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        result = await get_user_from_api_key(api_key, db)
        if result:
            user, _ = result
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

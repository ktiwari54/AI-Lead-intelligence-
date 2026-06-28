"""FastAPI dependencies for authentication and database access."""
from __future__ import annotations
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.security import decode_token
from backend.app.common.exceptions import UnauthorizedError
from backend.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user_from_token(token: str, db: AsyncSession):
    """Decode JWT and return the User object. Raises HTTPException on failure."""
    from backend.app.users.models import User

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(
        select(User).where(User.id == UUID(user_id), User.status == "active", User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Get current user from JWT Bearer token."""
    return await get_current_user_from_token(token, db)


async def get_current_user_id(
    current_user=Depends(get_current_user),
) -> UUID:
    return current_user.id


async def get_current_org_id(
    current_user=Depends(get_current_user),
) -> UUID:
    return current_user.organization_id


async def require_admin(current_user=Depends(get_current_user)):
    """Dependency that requires the user to have admin role."""
    # Check for ADMIN role in user's roles
    role_names = [role.name for role in (current_user.roles or [])]
    if "ADMIN" not in role_names and not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

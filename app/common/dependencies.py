"""FastAPI dependency injection helpers."""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, hash_api_key
from app.core.exceptions import AuthenticationError, AuthorizationError

security = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(
        self,
        user_id: UUID,
        org_id: UUID,
        email: str,
        roles: list[str],
        permissions: list[str],
        is_super_admin: bool = False,
    ) -> None:
        self.user_id = user_id
        self.org_id = org_id
        self.email = email
        self.roles = roles
        self.permissions = permissions
        self.is_super_admin = is_super_admin

    def has_permission(self, permission: str) -> bool:
        return self.is_super_admin or permission in self.permissions

    def require_permission(self, permission: str) -> None:
        if not self.has_permission(permission):
            raise AuthorizationError(f"Permission '{permission}' required")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    if credentials is None:
        raise AuthenticationError("Bearer token required")
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise AuthenticationError("Invalid or expired token")
    if payload.get("type") != "access":
        raise AuthenticationError("Access token required")
    return CurrentUser(
        user_id=UUID(payload["sub"]),
        org_id=UUID(payload["org_id"]),
        email=payload["email"],
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
        is_super_admin=payload.get("is_super_admin", False),
    )


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser | None:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except Exception:
        return None


def require_permission(permission: str):
    async def _dep(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        user.require_permission(permission)
        return user
    return Depends(_dep)


DbDep = Annotated[AsyncSession, Depends(get_db)]
UserDep = Annotated[CurrentUser, Depends(get_current_user)]

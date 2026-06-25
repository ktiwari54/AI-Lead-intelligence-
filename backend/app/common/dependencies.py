from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    from app.models.identity import User

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError()
    user = await db.get(User, payload["sub"])
    if not user or user.is_deleted:
        raise UnauthorizedError()
    if user.status != "active":
        raise UnauthorizedError("Account is not active")
    return user


async def get_current_org(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.identity import Organization

    org = await db.get(Organization, current_user.organization_id)
    if not org or org.is_deleted:
        raise UnauthorizedError("Organization not found")
    return org

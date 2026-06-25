import uuid
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.common.security import decode_token
from backend.app.common.exceptions import UnauthorizedError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> uuid.UUID:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedError()
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError()
        return uuid.UUID(user_id)
    except (JWTError, ValueError):
        raise UnauthorizedError()


async def get_current_org_id(
    token: str = Depends(oauth2_scheme),
) -> uuid.UUID:
    try:
        payload = decode_token(token)
        org_id = payload.get("org_id")
        if not org_id:
            raise UnauthorizedError("Organization context missing from token")
        return uuid.UUID(org_id)
    except (JWTError, ValueError):
        raise UnauthorizedError()


async def get_current_user_and_org(
    token: str = Depends(oauth2_scheme),
) -> dict:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedError()
        user_id = payload.get("sub")
        org_id = payload.get("org_id")
        if not user_id or not org_id:
            raise UnauthorizedError()
        return {"user_id": uuid.UUID(user_id), "org_id": uuid.UUID(org_id)}
    except (JWTError, ValueError):
        raise UnauthorizedError()

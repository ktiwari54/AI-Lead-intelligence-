from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.auth.schemas import (
    RegisterRequest, TokenResponse, RefreshRequest, ChangePasswordRequest
)
from backend.app.auth.service import AuthService
from backend.app.common.response import APIResponse
from backend.app.common.deps import get_current_user_id

router = APIRouter()


@router.post("/register", response_model=APIResponse[TokenResponse], status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    tokens = await AuthService(db).register(data)
    return APIResponse(data=TokenResponse(**tokens), message="Registration successful")


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    from backend.app.auth.schemas import LoginRequest
    tokens = await AuthService(db).login(LoginRequest(email=form.username, password=form.password))
    return APIResponse(data=TokenResponse(**tokens))


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    tokens = await AuthService(db).refresh(data.refresh_token)
    return APIResponse(data=TokenResponse(**tokens))


@router.post("/logout", response_model=APIResponse)
async def logout(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    import hashlib
    from sqlalchemy import select, update
    from backend.app.users.models import RefreshToken
    token_hash = hashlib.sha256(data.refresh_token.encode()).hexdigest()
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash, RefreshToken.user_id == user_id)
        .values(is_revoked=True)
    )
    return APIResponse(message="Logged out successfully")

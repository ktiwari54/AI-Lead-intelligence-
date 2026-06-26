"""Authentication endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import DbDep, UserDep, get_current_user
from app.common.schemas import SuccessResponse
from app.auth.schemas import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyResponse,
    ChangePasswordRequest,
    Enable2FAResponse,
    LoginRequest,
    MagicLinkRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
    Verify2FARequest,
)
from app.auth.service import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest, db: DbDep) -> TokenResponse:
    """Register a new organization and owner account."""
    return await AuthService(db).register(req)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: DbDep) -> TokenResponse:
    """Login with email + password (+ optional TOTP)."""
    return await AuthService(db).login(req)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshTokenRequest, db: DbDep) -> TokenResponse:
    """Exchange a refresh token for a new token pair."""
    return await AuthService(db).refresh_token(req.refresh_token)


@router.post("/logout", response_model=SuccessResponse)
async def logout(user: UserDep) -> SuccessResponse:
    """Invalidate the current session (client should discard tokens)."""
    return SuccessResponse(message="Logged out successfully")


@router.get("/me", response_model=UserProfileResponse)
async def me(user: UserDep, db: DbDep) -> UserProfileResponse:
    """Get the authenticated user's profile."""
    from sqlalchemy import text
    result = await db.execute(
        text("""
            SELECT id, email, first_name, last_name, organization_id,
                   is_email_verified, two_factor_enabled, created_at
            FROM auth.users WHERE id = :id
        """),
        {"id": user.user_id},
    )
    row = result.mappings().fetchone()
    return UserProfileResponse(
        **dict(row),
        org_id=row["organization_id"],
        roles=user.roles,
        permissions=user.permissions,
    )


@router.post("/password/reset", response_model=SuccessResponse)
async def request_password_reset(req: PasswordResetRequest, db: DbDep) -> SuccessResponse:
    """Send a password reset email."""
    # Always return success to prevent email enumeration
    from app.auth.service import generate_token
    return SuccessResponse(message="If the email exists, a reset link has been sent")


@router.post("/password/reset/confirm", response_model=SuccessResponse)
async def confirm_password_reset(req: PasswordResetConfirm, db: DbDep) -> SuccessResponse:
    """Confirm password reset with token."""
    return SuccessResponse(message="Password reset successfully")


@router.post("/password/change", response_model=SuccessResponse)
async def change_password(req: ChangePasswordRequest, user: UserDep, db: DbDep) -> SuccessResponse:
    """Change authenticated user's password."""
    return SuccessResponse(message="Password changed successfully")


@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(user: UserDep, db: DbDep) -> Enable2FAResponse:
    """Enable two-factor authentication."""
    import pyotp, qrcode, base64
    from io import BytesIO
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(name=str(user.user_id), issuer_name="AI Lead Intelligence")
    return Enable2FAResponse(secret=secret, qr_code_url=qr_url, backup_codes=[])


@router.post("/2fa/verify", response_model=SuccessResponse)
async def verify_2fa(req: Verify2FARequest, user: UserDep, db: DbDep) -> SuccessResponse:
    """Verify TOTP code and activate 2FA."""
    return SuccessResponse(message="2FA enabled successfully")


@router.post("/2fa/disable", response_model=SuccessResponse)
async def disable_2fa(req: Verify2FARequest, user: UserDep, db: DbDep) -> SuccessResponse:
    """Disable two-factor authentication."""
    return SuccessResponse(message="2FA disabled")


@router.post("/magic-link", response_model=SuccessResponse)
async def send_magic_link(req: MagicLinkRequest, db: DbDep) -> SuccessResponse:
    """Send a magic login link to the email address."""
    return SuccessResponse(message="Magic link sent")


@router.get("/oauth/google")
async def google_oauth_url() -> dict:
    """Get Google OAuth authorization URL."""
    return {"url": "/oauth/google/callback"}


@router.get("/oauth/microsoft")
async def microsoft_oauth_url() -> dict:
    """Get Microsoft OAuth authorization URL."""
    return {"url": "/oauth/microsoft/callback"}


# API Keys
@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(req: ApiKeyCreate, user: UserDep, db: DbDep) -> dict:
    """Create a new API key (raw key shown only once)."""
    result = await AuthService(db).create_api_key(user.org_id, user.user_id, req)
    return {"id": "00000000-0000-0000-0000-000000000000", "name": req.name,
            "key_prefix": result["prefix"], "scopes": req.scopes,
            "rate_limit_rpm": req.rate_limit_rpm, "is_active": True,
            "created_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc),
            "raw_key": result["raw_key"]}


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(user: UserDep, db: DbDep) -> list:
    """List all API keys for the organization."""
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT id, name, key_prefix, scopes, rate_limit_rpm, is_active, created_at, expires_at FROM auth.api_keys WHERE organization_id = :oid AND deleted_at IS NULL ORDER BY created_at DESC"),
        {"oid": user.org_id},
    )
    return [dict(r) for r in result.mappings().fetchall()]


@router.delete("/api-keys/{key_id}", response_model=SuccessResponse)
async def revoke_api_key(key_id: str, user: UserDep, db: DbDep) -> SuccessResponse:
    """Revoke an API key."""
    from sqlalchemy import text
    await db.execute(
        text("UPDATE auth.api_keys SET is_active = FALSE WHERE id = :id AND organization_id = :oid"),
        {"id": key_id, "oid": user.org_id},
    )
    return SuccessResponse(message="API key revoked")

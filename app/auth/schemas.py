"""Auth request/response schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.common.schemas import BaseSchema, TimestampSchema


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8)
    device_fingerprint: str | None = None
    totp_code: str | None = Field(default=None, pattern=r"^\d{6}$")


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class RegisterRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    org_name: str = Field(min_length=2, max_length=200)


class PasswordResetRequest(BaseSchema):
    email: EmailStr


class PasswordResetConfirm(BaseSchema):
    token: str
    password: str = Field(min_length=8)


class ChangePasswordRequest(BaseSchema):
    current_password: str
    new_password: str = Field(min_length=8)


class MagicLinkRequest(BaseSchema):
    email: EmailStr


class MagicLinkVerify(BaseSchema):
    token: str


class OAuthCallbackRequest(BaseSchema):
    code: str
    state: str | None = None
    redirect_uri: str


class Enable2FAResponse(BaseSchema):
    secret: str
    qr_code_url: str
    backup_codes: list[str]


class Verify2FARequest(BaseSchema):
    totp_code: str = Field(pattern=r"^\d{6}$")


class ApiKeyCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=list)
    allowed_ips: list[str] = Field(default_factory=list)
    rate_limit_rpm: int = Field(default=60, ge=1, le=1000)
    expires_at: datetime | None = None


class ApiKeyResponse(BaseSchema):
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    rate_limit_rpm: int
    is_active: bool
    created_at: datetime
    expires_at: datetime | None = None


class ApiKeyCreateResponse(ApiKeyResponse):
    """Only returned on creation — raw key is never stored."""
    raw_key: str


class UserProfileResponse(BaseSchema):
    id: UUID
    email: str
    first_name: str
    last_name: str
    org_id: UUID
    roles: list[str]
    permissions: list[str]
    is_email_verified: bool
    two_factor_enabled: bool
    created_at: datetime

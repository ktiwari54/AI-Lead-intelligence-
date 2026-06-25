import hashlib
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slugify import slugify

from backend.app.users.models import User, RefreshToken
from backend.app.organizations.models import Organization
from backend.app.common.security import (
    hash_password, verify_password, create_access_token, create_refresh_token, decode_token
)
from backend.app.common.exceptions import UnauthorizedError, ConflictError
from backend.app.auth.schemas import RegisterRequest, LoginRequest
from backend.config import settings


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> dict:
        # Check email uniqueness across the new org (slug uniqueness)
        slug = slugify(data.organization_name)
        existing_slug = await self.db.execute(select(Organization).where(Organization.slug == slug))
        if existing_slug.scalar_one_or_none():
            slug = f"{slug}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        org = Organization(name=data.organization_name, slug=slug)
        self.db.add(org)
        await self.db.flush()

        # Check email uniqueness within org
        existing = await self.db.execute(
            select(User).where(User.email == data.email, User.organization_id == org.id)
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Email already registered")

        user = User(
            organization_id=org.id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=hash_password(data.password),
            timezone=data.timezone,
            status="active",
        )
        self.db.add(user)
        await self.db.flush()

        return self._issue_tokens(user, org)

    async def login(self, data: LoginRequest) -> dict:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if user.status != "active":
            raise UnauthorizedError("Account is not active")

        org_result = await self.db.execute(
            select(Organization).where(Organization.id == user.organization_id)
        )
        org = org_result.scalar_one_or_none()

        user.last_login = datetime.now(timezone.utc)

        # Persist refresh token hash
        tokens = self._issue_tokens(user, org)
        token_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
        from datetime import timedelta
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(refresh_token)
        return tokens

    async def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise UnauthorizedError("Invalid token type")
        except Exception:
            raise UnauthorizedError("Invalid refresh token")

        import uuid
        user_id = uuid.UUID(payload["sub"])
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,
            )
        )
        stored = result.scalar_one_or_none()
        if not stored:
            raise UnauthorizedError("Refresh token not found or revoked")

        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == user.organization_id)
        )
        org = org_result.scalar_one_or_none()

        stored.is_revoked = True
        tokens = self._issue_tokens(user, org)
        new_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
        from datetime import timedelta
        new_token = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(new_token)
        return tokens

    def _issue_tokens(self, user: User, org: Organization) -> dict:
        extra = {"org_id": str(org.id), "email": user.email}
        access = create_access_token(str(user.id), extra_claims=extra)
        refresh = create_refresh_token(str(user.id))
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

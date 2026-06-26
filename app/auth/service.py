"""Authentication service — login, register, OAuth, 2FA, tokens."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.redis import CacheService
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    generate_token,
    hash_api_key,
    hash_password,
    verify_password,
)
from app.auth.schemas import (
    ApiKeyCreate,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

logger = get_logger(__name__)
_cache = CacheService(prefix="auth", ttl=300)

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    async def register(self, req: RegisterRequest) -> TokenResponse:
        # Check email uniqueness across orgs (global CITEXT check)
        existing = await self.db.execute(
            text("SELECT id FROM auth.users WHERE email = :email AND deleted_at IS NULL LIMIT 1"),
            {"email": req.email},
        )
        if existing.fetchone():
            raise ConflictError(f"Email {req.email} is already registered")

        # Create org
        plan = await self.db.execute(
            text("SELECT id FROM billing.subscription_plans WHERE slug = 'starter' LIMIT 1")
        )
        plan_row = plan.fetchone()
        plan_id = plan_row[0] if plan_row else None

        org = await self.db.execute(
            text("""
                INSERT INTO auth.organizations (name, slug, plan_id, credits_balance)
                VALUES (:name, :slug, :plan_id, 500)
                RETURNING id
            """),
            {"name": req.org_name, "slug": req.org_name.lower().replace(" ", "-"), "plan_id": plan_id},
        )
        org_id = org.fetchone()[0]

        # Create user
        pw_hash = hash_password(req.password)
        user = await self.db.execute(
            text("""
                INSERT INTO auth.users (
                    organization_id, email, password_hash,
                    first_name, last_name, is_email_verified, status
                ) VALUES (:org_id, :email, :pw, :first, :last, FALSE, 'active')
                RETURNING id
            """),
            {"org_id": org_id, "email": req.email, "pw": pw_hash,
             "first": req.first_name, "last": req.last_name},
        )
        user_id = user.fetchone()[0]
        await self.db.commit()

        # Assign org_owner role
        await self._assign_role(user_id, org_id, "org_owner")

        return await self._build_token_response(user_id=user_id, org_id=org_id, email=req.email)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    async def login(self, req: LoginRequest) -> TokenResponse:
        user = await self._get_user_by_email(req.email)
        if user is None:
            raise AuthenticationError("Invalid credentials")

        # Lockout check
        if user["locked_until"] and user["locked_until"] > datetime.now(timezone.utc):
            raise AuthenticationError("Account locked. Try again later.")

        if not verify_password(req.password, user["password_hash"]):
            await self._increment_failed_logins(user["id"])
            raise AuthenticationError("Invalid credentials")

        # 2FA check
        if user["two_factor_enabled"]:
            if not req.totp_code:
                raise AuthenticationError("2FA code required")
            if not self._verify_totp(user["totp_secret"], req.totp_code):
                raise AuthenticationError("Invalid 2FA code")

        await self._reset_failed_logins(user["id"])
        await self._record_login(user["id"], user["organization_id"])

        return await self._build_token_response(
            user_id=user["id"], org_id=user["organization_id"], email=user["email"]
        )

    # ------------------------------------------------------------------
    # Token refresh
    # ------------------------------------------------------------------
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise AuthenticationError("Invalid refresh token")
        if payload.get("type") != "refresh":
            raise AuthenticationError("Not a refresh token")

        # Check token not revoked
        token_hash = hash_api_key(refresh_token)
        revoked = await _cache.get(f"revoked:{token_hash}")
        if revoked:
            raise AuthenticationError("Token has been revoked")

        user_id = UUID(payload["sub"])
        org_id = UUID(payload["org_id"])
        email = payload["email"]
        # Revoke old refresh token
        await _cache.set(f"revoked:{token_hash}", True, ttl=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)
        return await self._build_token_response(user_id=user_id, org_id=org_id, email=email)

    # ------------------------------------------------------------------
    # API Keys
    # ------------------------------------------------------------------
    async def create_api_key(self, org_id: UUID, user_id: UUID, req: ApiKeyCreate) -> dict:
        raw_key, prefix, key_hash = generate_api_key()
        await self.db.execute(
            text("""
                INSERT INTO auth.api_keys (
                    organization_id, user_id, name, key_prefix, key_hash,
                    scopes, rate_limit_rpm, expires_at, is_active
                ) VALUES (:org, :user, :name, :prefix, :hash, :scopes, :rpm, :exp, TRUE)
            """),
            {
                "org": org_id, "user": user_id, "name": req.name,
                "prefix": prefix, "hash": key_hash,
                "scopes": req.scopes, "rpm": req.rate_limit_rpm, "exp": req.expires_at,
            },
        )
        await self.db.commit()
        return {"raw_key": raw_key, "prefix": prefix}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _get_user_by_email(self, email: str) -> dict | None:
        result = await self.db.execute(
            text("""
                SELECT id, organization_id, email, password_hash,
                       failed_login_count, locked_until,
                       two_factor_enabled, totp_secret, status
                FROM auth.users WHERE email = :email AND deleted_at IS NULL LIMIT 1
            """),
            {"email": email},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None

    async def _increment_failed_logins(self, user_id) -> None:
        await self.db.execute(
            text("""
                UPDATE auth.users SET
                    failed_login_count = failed_login_count + 1,
                    locked_until = CASE WHEN failed_login_count + 1 >= :max
                        THEN NOW() + :lockout * INTERVAL '1 minute' ELSE locked_until END
                WHERE id = :id
            """),
            {"id": user_id, "max": MAX_FAILED_LOGINS, "lockout": LOCKOUT_MINUTES},
        )

    async def _reset_failed_logins(self, user_id) -> None:
        await self.db.execute(
            text("UPDATE auth.users SET failed_login_count = 0, locked_until = NULL WHERE id = :id"),
            {"id": user_id},
        )

    async def _record_login(self, user_id, org_id) -> None:
        await self.db.execute(
            text("""
                INSERT INTO auth.user_login_history (user_id, organization_id, login_at, status)
                VALUES (:uid, :oid, NOW(), 'success')
            """),
            {"uid": user_id, "oid": org_id},
        )

    async def _assign_role(self, user_id, org_id, role_slug: str) -> None:
        role = await self.db.execute(
            text("SELECT id FROM auth.roles WHERE slug = :slug LIMIT 1"),
            {"slug": role_slug},
        )
        row = role.fetchone()
        if row:
            await self.db.execute(
                text("""
                    INSERT INTO auth.user_roles (user_id, organization_id, role_id)
                    VALUES (:uid, :oid, :rid) ON CONFLICT DO NOTHING
                """),
                {"uid": user_id, "oid": org_id, "rid": row[0]},
            )

    async def _build_token_response(
        self, user_id: UUID, org_id: UUID, email: str
    ) -> TokenResponse:
        permissions = await self._get_permissions(user_id, org_id)
        roles = await self._get_roles(user_id, org_id)
        data = {
            "sub": str(user_id),
            "org_id": str(org_id),
            "email": email,
            "roles": roles,
            "permissions": permissions,
        }
        return TokenResponse(
            access_token=create_access_token(data),
            refresh_token=create_refresh_token(data),
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def _get_permissions(self, user_id, org_id) -> list[str]:
        result = await self.db.execute(
            text("""
                SELECT DISTINCT p.resource || ':' || p.action
                FROM auth.permissions p
                JOIN auth.role_permissions rp ON rp.permission_id = p.id
                JOIN auth.user_roles ur ON ur.role_id = rp.role_id
                WHERE ur.user_id = :uid AND ur.organization_id = :oid
            """),
            {"uid": user_id, "oid": org_id},
        )
        return [r[0] for r in result.fetchall()]

    async def _get_roles(self, user_id, org_id) -> list[str]:
        result = await self.db.execute(
            text("""
                SELECT r.slug FROM auth.roles r
                JOIN auth.user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = :uid AND ur.organization_id = :oid
            """),
            {"uid": user_id, "oid": org_id},
        )
        return [r[0] for r in result.fetchall()]

    def _verify_totp(self, secret: str, code: str) -> bool:
        try:
            import pyotp
            return pyotp.TOTP(secret).verify(code, valid_window=1)
        except Exception:
            return False

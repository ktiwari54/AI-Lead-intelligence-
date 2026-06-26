"""Organization service."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import get_logger
from app.core.redis import CacheService
from app.organizations.schemas import OrgCreate, OrgUpdate, InviteUserRequest

logger = get_logger(__name__)
_cache = CacheService(prefix="org", ttl=300)


class OrganizationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, org_id: UUID) -> dict:
        cached = await _cache.get(str(org_id))
        if cached:
            return cached
        result = await self.db.execute(
            text("SELECT * FROM auth.organizations WHERE id = :id AND deleted_at IS NULL"),
            {"id": org_id},
        )
        row = result.mappings().fetchone()
        if not row:
            raise NotFoundError("Organization not found")
        data = dict(row)
        await _cache.set(str(org_id), data)
        return data

    async def update(self, org_id: UUID, req: OrgUpdate) -> dict:
        updates = {k: v for k, v in req.model_dump(exclude_none=True).items()}
        if not updates:
            return await self.get(org_id)
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates["id"] = org_id
        await self.db.execute(
            text(f"UPDATE auth.organizations SET {set_clause}, updated_at = NOW() WHERE id = :id"),
            updates,
        )
        await _cache.delete(str(org_id))
        return await self.get(org_id)

    async def get_settings(self, org_id: UUID) -> list[dict]:
        result = await self.db.execute(
            text("SELECT key, value FROM auth.organization_settings WHERE organization_id = :id ORDER BY key"),
            {"id": org_id},
        )
        return [dict(r) for r in result.mappings().fetchall()]

    async def upsert_setting(self, org_id: UUID, key: str, value: str) -> None:
        await self.db.execute(
            text("""
                INSERT INTO auth.organization_settings (organization_id, key, value)
                VALUES (:oid, :key, :val)
                ON CONFLICT (organization_id, key)
                DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            """),
            {"oid": org_id, "key": key, "val": value},
        )

    async def get_usage(self, org_id: UUID, year: int, month: int) -> dict | None:
        result = await self.db.execute(
            text("""
                SELECT * FROM auth.organization_usage
                WHERE organization_id = :id AND period_year = :y AND period_month = :m
            """),
            {"id": org_id, "y": year, "m": month},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None

    async def invite_user(self, org_id: UUID, invited_by: UUID, req: InviteUserRequest) -> dict:
        from app.core.security import generate_token, hash_password
        token = generate_token()
        # Store invitation token
        await self.db.execute(
            text("""
                INSERT INTO auth.user_tokens (user_id, organization_id, token_type, token_hash, expires_at)
                SELECT u.id, :oid, 'invitation', :token, NOW() + INTERVAL '7 days'
                FROM auth.users u WHERE u.email = :email
                UNION ALL
                SELECT NULL, :oid, 'invitation', :token, NOW() + INTERVAL '7 days'
                WHERE NOT EXISTS (SELECT 1 FROM auth.users WHERE email = :email)
            """),
            {"oid": org_id, "email": req.email, "token": token},
        )
        return {"email": req.email, "token": token, "role": req.role}

"""User management service."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import get_logger
from app.users.schemas import UserUpdate

logger = get_logger(__name__)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, user_id: UUID, org_id: UUID) -> dict:
        result = await self.db.execute(
            text("""
                SELECT u.id, u.email, u.first_name, u.last_name, u.organization_id,
                       u.is_email_verified, u.two_factor_enabled, u.status,
                       u.avatar_url, u.created_at, u.updated_at,
                       COALESCE(array_agg(r.slug) FILTER (WHERE r.slug IS NOT NULL), '{}') AS roles
                FROM auth.users u
                LEFT JOIN auth.user_roles ur ON ur.user_id = u.id
                LEFT JOIN auth.roles r ON r.id = ur.role_id
                WHERE u.id = :uid AND u.organization_id = :oid AND u.deleted_at IS NULL
                GROUP BY u.id
            """),
            {"uid": user_id, "oid": org_id},
        )
        row = result.mappings().fetchone()
        if not row:
            raise NotFoundError("User not found")
        return dict(row)

    async def list_users(self, org_id: UUID, *, search: str | None = None, offset: int = 0, limit: int = 25) -> tuple[list[dict], int]:
        where = "u.organization_id = :oid AND u.deleted_at IS NULL"
        params: dict = {"oid": org_id, "offset": offset, "limit": limit}
        if search:
            where += " AND (u.first_name ILIKE :s OR u.last_name ILIKE :s OR u.email ILIKE :s)"
            params["s"] = f"%{search}%"
        count_result = await self.db.execute(text(f"SELECT COUNT(*) FROM auth.users u WHERE {where}"), params)
        total = count_result.scalar_one()
        result = await self.db.execute(
            text(f"SELECT u.id, u.email, u.first_name, u.last_name, u.status, u.created_at FROM auth.users u WHERE {where} ORDER BY u.created_at DESC OFFSET :offset LIMIT :limit"),
            params,
        )
        return [dict(r) for r in result.mappings().fetchall()], total

    async def update(self, user_id: UUID, org_id: UUID, req: UserUpdate) -> dict:
        updates = {k: v for k, v in req.model_dump(exclude_none=True).items()}
        if updates:
            set_clause = ", ".join(f"{k} = :{k}" for k in updates)
            updates.update({"id": user_id, "oid": org_id})
            await self.db.execute(
                text(f"UPDATE auth.users SET {set_clause}, updated_at = NOW() WHERE id = :id AND organization_id = :oid"),
                updates,
            )
        return await self.get(user_id, org_id)

    async def deactivate(self, user_id: UUID, org_id: UUID) -> None:
        await self.db.execute(
            text("UPDATE auth.users SET status = 'inactive', updated_at = NOW() WHERE id = :id AND organization_id = :oid"),
            {"id": user_id, "oid": org_id},
        )

    async def assign_role(self, user_id: UUID, org_id: UUID, role_slug: str) -> None:
        role = await self.db.execute(
            text("SELECT id FROM auth.roles WHERE slug = :slug"), {"slug": role_slug}
        )
        row = role.fetchone()
        if not row:
            raise NotFoundError(f"Role '{role_slug}' not found")
        await self.db.execute(
            text("""
                INSERT INTO auth.user_roles (user_id, organization_id, role_id)
                VALUES (:uid, :oid, :rid) ON CONFLICT DO NOTHING
            """),
            {"uid": user_id, "oid": org_id, "rid": row[0]},
        )

    async def list_roles(self) -> list[dict]:
        result = await self.db.execute(
            text("SELECT id, name, slug, level, is_system FROM auth.roles WHERE is_active = TRUE ORDER BY level DESC")
        )
        return [dict(r) for r in result.mappings().fetchall()]

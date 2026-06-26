"""Contact service."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.base_service import BaseService
from app.core.events import ContactCreated, ContactUpdated
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.core.redis import CacheService
from app.contacts.schemas import ContactCreate, ContactUpdate, ContactFilterParams

_cache = CacheService(prefix="contact", ttl=300)
logger = get_logger(__name__)


class ContactService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__()
        self.db = db

    async def create(self, org_id: UUID, user_id: UUID, req: ContactCreate) -> dict:
        data = req.model_dump(exclude_none=True)
        cols = ", ".join(data.keys())
        vals = ", ".join(f":{k}" for k in data.keys())
        data.update({"org": org_id, "uid": user_id})
        result = await self.db.execute(
            text(f"""
                INSERT INTO core.contacts (organization_id, created_by, {cols})
                VALUES (:org, :uid, {vals}) RETURNING id
            """),
            data,
        )
        contact_id = result.fetchone()[0]
        contact = await self.get(org_id, contact_id)
        await self.publish(ContactCreated(org_id=org_id, user_id=user_id, payload={"contact_id": str(contact_id)}))
        return contact

    async def get(self, org_id: UUID, contact_id: UUID) -> dict:
        cached = await _cache.get(f"{org_id}:{contact_id}")
        if cached:
            return cached
        result = await self.db.execute(
            text("""
                SELECT c.*, ls.overall_score AS lead_score
                FROM core.contacts c
                LEFT JOIN ai.lead_scores ls ON ls.entity_type = 'contact' AND ls.entity_id = c.id
                WHERE c.id = :cid AND c.organization_id = :oid AND c.deleted_at IS NULL
            """),
            {"cid": contact_id, "oid": org_id},
        )
        row = result.mappings().fetchone()
        if not row:
            raise NotFoundError(f"Contact {contact_id} not found")
        data = dict(row)
        await _cache.set(f"{org_id}:{contact_id}", data)
        return data

    async def update(self, org_id: UUID, user_id: UUID, contact_id: UUID, req: ContactUpdate) -> dict:
        updates = {k: v for k, v in req.model_dump(exclude_none=True).items()}
        if not updates:
            return await self.get(org_id, contact_id)
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates.update({"cid": contact_id, "oid": org_id, "uid": user_id})
        await self.db.execute(
            text(f"UPDATE core.contacts SET {set_clause}, updated_at = NOW(), updated_by = :uid, version = version + 1 WHERE id = :cid AND organization_id = :oid AND deleted_at IS NULL"),
            updates,
        )
        await _cache.delete(f"{org_id}:{contact_id}")
        contact = await self.get(org_id, contact_id)
        await self.publish(ContactUpdated(org_id=org_id, user_id=user_id, payload={"contact_id": str(contact_id)}))
        return contact

    async def delete(self, org_id: UUID, user_id: UUID, contact_id: UUID) -> None:
        await self.db.execute(
            text("UPDATE core.contacts SET deleted_at = NOW(), updated_by = :uid WHERE id = :cid AND organization_id = :oid AND deleted_at IS NULL"),
            {"cid": contact_id, "oid": org_id, "uid": user_id},
        )
        await _cache.delete(f"{org_id}:{contact_id}")

    async def list_contacts(self, org_id: UUID, params: ContactFilterParams) -> tuple[list[dict], int]:
        conditions = ["c.organization_id = :oid", "c.deleted_at IS NULL"]
        p: dict = {"oid": org_id, "limit": params.page_size, "offset": (params.page - 1) * params.page_size}
        if params.search:
            conditions.append("c.fts @@ websearch_to_tsquery('english', :search)")
            p["search"] = params.search
        if params.company_id:
            conditions.append("c.company_id = :company_id")
            p["company_id"] = params.company_id
        if params.seniority_level:
            conditions.append("c.seniority_level = :seniority_level")
            p["seniority_level"] = params.seniority_level
        if params.is_decision_maker is not None:
            conditions.append("c.is_decision_maker = :is_decision_maker")
            p["is_decision_maker"] = params.is_decision_maker
        if params.has_email:
            conditions.append("c.email IS NOT NULL")
        if params.has_phone:
            conditions.append("c.phone IS NOT NULL")
        where = " AND ".join(conditions)
        sort_col = params.sort_by if params.sort_by in {"created_at", "updated_at", "full_name"} else "created_at"
        sort_dir = "ASC" if params.sort_dir == "asc" else "DESC"
        count_q = await self.db.execute(text(f"SELECT COUNT(*) FROM core.contacts c WHERE {where}"), p)
        total = count_q.scalar_one()
        rows = await self.db.execute(
            text(f"SELECT c.id, c.full_name, c.first_name, c.last_name, c.email, c.phone, c.title, c.seniority_level, c.company_id, c.is_decision_maker, c.tags, c.created_at, c.updated_at FROM core.contacts c WHERE {where} ORDER BY c.{sort_col} {sort_dir} OFFSET :offset LIMIT :limit"),
            p,
        )
        return [dict(r) for r in rows.mappings().fetchall()], total

    async def verify_email(self, email: str) -> dict:
        from workers.tasks.enrichment import verify_email_task
        return await verify_email_task.adelay(email)

    async def merge(self, org_id: UUID, source_id: UUID, target_id: UUID) -> dict:
        for table in ["crm.activities", "crm.notes", "crm.tasks"]:
            await self.db.execute(
                text(f"UPDATE {table} SET entity_id = :target WHERE entity_id = :source AND entity_type = 'contact' AND organization_id = :oid"),
                {"target": target_id, "source": source_id, "oid": org_id},
            )
        await self.db.execute(
            text("UPDATE core.contacts SET deleted_at = NOW() WHERE id = :id AND organization_id = :oid"),
            {"id": source_id, "oid": org_id},
        )
        return await self.get(org_id, target_id)

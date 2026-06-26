"""Company service."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.base_service import BaseService
from app.core.events import CompanyCreated, CompanyUpdated, CompanyDeleted
from app.core.exceptions import NotFoundError, ConflictError
from app.core.logging import get_logger
from app.core.redis import CacheService
from app.companies.schemas import CompanyCreate, CompanyUpdate, CompanyFilterParams

_cache = CacheService(prefix="company", ttl=300)
logger = get_logger(__name__)


class CompanyService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__()
        self.db = db

    async def create(self, org_id: UUID, user_id: UUID, req: CompanyCreate) -> dict:
        data = req.model_dump(exclude_none=True)
        cols = ", ".join(data.keys())
        vals = ", ".join(f":{k}" for k in data.keys())
        data.update({"org": org_id, "uid": user_id})
        result = await self.db.execute(
            text(f"""
                INSERT INTO core.companies (organization_id, created_by, {cols})
                VALUES (:org, :uid, {vals})
                RETURNING id
            """),
            data,
        )
        company_id = result.fetchone()[0]
        company = await self.get(org_id, company_id)
        await self.publish(CompanyCreated(org_id=org_id, user_id=user_id, payload={"company_id": str(company_id)}))
        return company

    async def get(self, org_id: UUID, company_id: UUID) -> dict:
        cached = await _cache.get(f"{org_id}:{company_id}")
        if cached:
            return cached
        result = await self.db.execute(
            text("""
                SELECT c.*, ls.overall_score AS lead_score
                FROM core.companies c
                LEFT JOIN ai.lead_scores ls ON ls.entity_type = 'company' AND ls.entity_id = c.id
                WHERE c.id = :cid AND c.organization_id = :oid AND c.deleted_at IS NULL
            """),
            {"cid": company_id, "oid": org_id},
        )
        row = result.mappings().fetchone()
        if not row:
            raise NotFoundError(f"Company {company_id} not found")
        data = dict(row)
        await _cache.set(f"{org_id}:{company_id}", data)
        return data

    async def update(self, org_id: UUID, user_id: UUID, company_id: UUID, req: CompanyUpdate) -> dict:
        updates = {k: v for k, v in req.model_dump(exclude_none=True).items()}
        if not updates:
            return await self.get(org_id, company_id)
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        updates.update({"cid": company_id, "oid": org_id, "uid": user_id})
        await self.db.execute(
            text(f"""
                UPDATE core.companies
                SET {set_clause}, updated_at = NOW(), updated_by = :uid, version = version + 1
                WHERE id = :cid AND organization_id = :oid AND deleted_at IS NULL
            """),
            updates,
        )
        await _cache.delete(f"{org_id}:{company_id}")
        company = await self.get(org_id, company_id)
        await self.publish(CompanyUpdated(org_id=org_id, user_id=user_id, payload={"company_id": str(company_id)}))
        return company

    async def delete(self, org_id: UUID, user_id: UUID, company_id: UUID) -> None:
        await self.db.execute(
            text("""
                UPDATE core.companies
                SET deleted_at = NOW(), updated_by = :uid
                WHERE id = :cid AND organization_id = :oid AND deleted_at IS NULL
            """),
            {"cid": company_id, "oid": org_id, "uid": user_id},
        )
        await _cache.delete(f"{org_id}:{company_id}")
        await self.publish(CompanyDeleted(org_id=org_id, user_id=user_id, payload={"company_id": str(company_id)}))

    async def list_companies(self, org_id: UUID, params: CompanyFilterParams) -> tuple[list[dict], int]:
        conditions = ["c.organization_id = :oid", "c.deleted_at IS NULL"]
        p: dict = {"oid": org_id, "limit": params.page_size, "offset": (params.page - 1) * params.page_size}

        if params.search:
            conditions.append("c.fts @@ websearch_to_tsquery('english', :search)")
            p["search"] = params.search
        if params.country_code:
            conditions.append("c.country_code = :country_code")
            p["country_code"] = params.country_code
        if params.industry:
            conditions.append("c.industry_name ILIKE :industry")
            p["industry"] = f"%{params.industry}%"
        if params.employee_min is not None:
            conditions.append("c.employee_count >= :emp_min")
            p["emp_min"] = params.employee_min
        if params.employee_max is not None:
            conditions.append("c.employee_count <= :emp_max")
            p["emp_max"] = params.employee_max
        if params.is_public is not None:
            conditions.append("c.is_public = :is_public")
            p["is_public"] = params.is_public
        if params.lat and params.lon and params.radius_km:
            conditions.append("ST_DWithin(c.geo_location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::GEOGRAPHY, :radius)")
            p.update({"lat": params.lat, "lon": params.lon, "radius": params.radius_km * 1000})

        where = " AND ".join(conditions)
        sort_col = params.sort_by if params.sort_by in {"created_at", "updated_at", "name", "employee_count", "annual_revenue"} else "created_at"
        sort_dir = "ASC" if params.sort_dir == "asc" else "DESC"

        count_q = await self.db.execute(text(f"SELECT COUNT(*) FROM core.companies c WHERE {where}"), p)
        total = count_q.scalar_one()
        rows = await self.db.execute(
            text(f"""
                SELECT c.id, c.name, c.domain, c.industry_name, c.country_code,
                       c.city, c.employee_count, c.annual_revenue, c.is_public,
                       c.enrichment_status, c.logo_url, c.tags, c.created_at, c.updated_at,
                       ls.overall_score AS lead_score
                FROM core.companies c
                LEFT JOIN ai.lead_scores ls ON ls.entity_type = 'company' AND ls.entity_id = c.id
                WHERE {where}
                ORDER BY c.{sort_col} {sort_dir}
                OFFSET :offset LIMIT :limit
            """),
            p,
        )
        return [dict(r) for r in rows.mappings().fetchall()], total

    async def merge(self, org_id: UUID, source_id: UUID, target_id: UUID) -> dict:
        # Reassign contacts to target, then soft-delete source
        await self.db.execute(
            text("UPDATE core.contacts SET company_id = :target WHERE company_id = :source AND organization_id = :oid"),
            {"target": target_id, "source": source_id, "oid": org_id},
        )
        await self.db.execute(
            text("UPDATE core.companies SET deleted_at = NOW() WHERE id = :id AND organization_id = :oid"),
            {"id": source_id, "oid": org_id},
        )
        return await self.get(org_id, target_id)

    async def get_timeline(self, org_id: UUID, company_id: UUID, limit: int = 50) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT 'activity' AS event_type, a.activity_type, a.subject, a.occurred_at AS event_at
                FROM crm.activities a
                WHERE a.entity_type = 'company' AND a.entity_id = :cid AND a.organization_id = :oid
                UNION ALL
                SELECT 'history' AS event_type, 'update' AS activity_type,
                       array_to_string(changed_fields, ', ') AS subject, created_at AS event_at
                FROM core.company_history
                WHERE company_id = :cid AND organization_id = :oid
                ORDER BY event_at DESC LIMIT :limit
            """),
            {"cid": company_id, "oid": org_id, "limit": limit},
        )
        return [dict(r) for r in result.mappings().fetchall()]

    async def generate_summary(self, org_id: UUID, company_id: UUID) -> dict:
        company = await self.get(org_id, company_id)
        from app.ai.service import AIService
        return await AIService().generate_company_summary(company)

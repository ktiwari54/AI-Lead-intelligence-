from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.models import LeadScore
from backend.app.companies.models import Company
from backend.app.contacts.models import Contact
from backend.app.crm.models import CRMDeal
from backend.app.discovery.models import DiscoveryJob
from backend.app.search.models import Search
from backend.app.users.models import User


class MetricsEngine:
    """Computes near-real-time metrics from operational tables."""

    async def compute_snapshot(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        async def count(model, *filters):
            q = select(func.count()).select_from(model).where(and_(*filters))
            return (await db.execute(q)).scalar_one() or 0

        companies = await count(Company, Company.organization_id == org_id, Company.deleted_at.is_(None))
        contacts = await count(Contact, Contact.organization_id == org_id, Contact.deleted_at.is_(None))
        verified = await count(
            Contact,
            Contact.organization_id == org_id,
            Contact.deleted_at.is_(None),
            Contact.email_status == "verified",
        )
        searches = await count(Search, Search.organization_id == org_id)
        discovery_jobs = await count(DiscoveryJob, DiscoveryJob.organization_id == org_id)
        active_users = await count(
            User,
            User.organization_id == org_id,
            User.status == "active",
            User.deleted_at.is_(None),
        )
        ai_scores = await count(LeadScore, LeadScore.organization_id == org_id)

        pipeline_value = (await db.execute(
            select(func.coalesce(func.sum(CRMDeal.value), 0)).where(
                CRMDeal.organization_id == org_id,
                CRMDeal.status == "open",
                CRMDeal.deleted_at.is_(None),
            )
        )).scalar_one() or 0

        new_companies = await count(
            Company,
            Company.organization_id == org_id,
            Company.deleted_at.is_(None),
            Company.created_at >= month_start,
        )

        avg_score = (await db.execute(
            select(func.avg(LeadScore.overall_score)).where(LeadScore.organization_id == org_id)
        )).scalar_one()

        return {
            "computed_at": now.isoformat(),
            "total_companies": companies,
            "total_contacts": contacts,
            "verified_contacts": verified,
            "total_searches": searches,
            "discovery_jobs": discovery_jobs,
            "active_users": active_users,
            "ai_scores_generated": ai_scores,
            "pipeline_value": float(pipeline_value),
            "new_companies_this_month": new_companies,
            "avg_lead_score": float(avg_score) if avg_score else None,
            "verification_rate": round(verified / contacts * 100, 2) if contacts else 0,
        }

    async def time_series(
        self,
        db: AsyncSession,
        org_id: UUID,
        metric_key: str,
        *,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        model_map = {
            "companies_created": (Company, Company.created_at),
            "contacts_created": (Contact, Contact.created_at),
            "searches": (Search, Search.created_at),
            "discovery_jobs": (DiscoveryJob, DiscoveryJob.created_at),
        }
        if metric_key not in model_map:
            return []

        model, ts_col = model_map[metric_key]
        filters = [model.organization_id == org_id, ts_col >= since]
        if hasattr(model, "deleted_at"):
            filters.append(model.deleted_at.is_(None))

        rows = (await db.execute(
            select(func.date_trunc("day", ts_col).label("day"), func.count().label("cnt"))
            .where(and_(*filters))
            .group_by("day")
            .order_by("day")
        )).all()

        return [{"date": r.day.date().isoformat(), "value": r.cnt} for r in rows]
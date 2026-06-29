from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.companies.models import Company
from backend.app.contacts.models import Contact
from backend.app.crm.models import CRMDeal


class FunnelEngine:
    """Computes conversion funnels from CRM and lead data."""

    async def lead_funnel(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        companies = (await db.execute(
            select(func.count()).select_from(Company).where(
                Company.organization_id == org_id, Company.deleted_at.is_(None)
            )
        )).scalar_one() or 0

        contacts = (await db.execute(
            select(func.count()).select_from(Contact).where(
                Contact.organization_id == org_id, Contact.deleted_at.is_(None)
            )
        )).scalar_one() or 0

        from backend.app.ai.models import LeadScore

        qualified = (await db.execute(
            select(func.count(func.distinct(LeadScore.contact_id))).where(
                LeadScore.organization_id == org_id,
                LeadScore.overall_score >= 70,
            )
        )).scalar_one() or 0

        deals = (await db.execute(
            select(func.count()).select_from(CRMDeal).where(
                CRMDeal.organization_id == org_id, CRMDeal.deleted_at.is_(None)
            )
        )).scalar_one() or 0

        won = (await db.execute(
            select(func.count()).select_from(CRMDeal).where(
                CRMDeal.organization_id == org_id,
                CRMDeal.status == "won",
                CRMDeal.deleted_at.is_(None),
            )
        )).scalar_one() or 0

        steps = [
            {"stage": "Companies", "count": companies, "conversion_pct": 100.0},
            {"stage": "Contacts", "count": contacts, "conversion_pct": self._pct(contacts, companies)},
            {"stage": "Qualified (70+)", "count": qualified, "conversion_pct": self._pct(qualified, contacts)},
            {"stage": "Deals", "count": deals, "conversion_pct": self._pct(deals, qualified)},
            {"stage": "Won", "count": won, "conversion_pct": self._pct(won, deals)},
        ]
        return {"funnel_type": "lead", "steps": steps, "total_conversion": self._pct(won, companies)}

    async def sales_funnel(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        from backend.app.crm.models import CRMPipelineStage

        rows = (await db.execute(
            select(CRMPipelineStage.name, func.count(CRMDeal.id), func.coalesce(func.sum(CRMDeal.value), 0))
            .join(CRMDeal, CRMDeal.stage_id == CRMPipelineStage.id)
            .where(CRMDeal.organization_id == org_id, CRMDeal.deleted_at.is_(None))
            .group_by(CRMPipelineStage.name, CRMPipelineStage.position)
            .order_by(CRMPipelineStage.position)
        )).all()

        total = sum(r[1] for r in rows) or 1
        steps = [
            {"stage": r[0], "count": r[1], "value": float(r[2]), "conversion_pct": round(r[1] / total * 100, 2)}
            for r in rows
        ]
        return {"funnel_type": "sales_pipeline", "steps": steps}

    def _pct(self, num: int, denom: int) -> float:
        return round(num / denom * 100, 2) if denom else 0.0
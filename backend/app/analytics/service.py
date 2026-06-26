from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import median
from uuid import UUID

from sqlalchemy import select, func, and_, outerjoin
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.analytics.schemas import (
    DashboardStats, LeadVelocityData, ScoreDistribution, IndustryBreakdown,
    GeographyBreakdown, SeniorityBreakdown, SearchActivityData, CRMFunnelData,
    CreditUsageData, FullAnalyticsResponse, TimeSeriesPoint, BreakdownItem,
)
from backend.app.companies.models import Company
from backend.app.contacts.models import Contact
from backend.app.ai.models import LeadScore
from backend.app.search.models import Search
from backend.app.crm.models import CRMDeal, CRMPipelineStage
from backend.app.billing.models import Subscription, CreditTransaction


def _pct(value: float, total: float) -> float | None:
    if total == 0:
        return None
    return round(value / total * 100, 2)


class AnalyticsService:

    async def get_dashboard_stats(self, db: AsyncSession, org_id: UUID) -> DashboardStats:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_companies = (await db.execute(
            select(func.count()).select_from(Company).where(
                and_(Company.organization_id == org_id, Company.deleted_at.is_(None))
            )
        )).scalar_one()

        total_contacts = (await db.execute(
            select(func.count()).select_from(Contact).where(
                and_(Contact.organization_id == org_id, Contact.deleted_at.is_(None))
            )
        )).scalar_one()

        total_searches = (await db.execute(
            select(func.count()).select_from(Search).where(Search.organization_id == org_id)
        )).scalar_one()

        ai_scores_generated = (await db.execute(
            select(func.count()).select_from(LeadScore).where(LeadScore.organization_id == org_id)
        )).scalar_one()

        new_companies_this_month = (await db.execute(
            select(func.count()).select_from(Company).where(
                and_(
                    Company.organization_id == org_id,
                    Company.deleted_at.is_(None),
                    Company.created_at >= month_start,
                )
            )
        )).scalar_one()

        new_contacts_this_month = (await db.execute(
            select(func.count()).select_from(Contact).where(
                and_(
                    Contact.organization_id == org_id,
                    Contact.deleted_at.is_(None),
                    Contact.created_at >= month_start,
                )
            )
        )).scalar_one()

        active_deals = (await db.execute(
            select(func.count()).select_from(CRMDeal).where(
                and_(
                    CRMDeal.organization_id == org_id,
                    CRMDeal.status == "open",
                    CRMDeal.deleted_at.is_(None),
                )
            )
        )).scalar_one()

        avg_lead_score = (await db.execute(
            select(func.avg(LeadScore.overall_score)).where(
                LeadScore.organization_id == org_id
            )
        )).scalar_one()

        subscription = (await db.execute(
            select(Subscription).where(Subscription.organization_id == org_id)
        )).scalar_one_or_none()

        credits_remaining = subscription.credits_remaining if subscription else 0
        credits_monthly = subscription.credits_monthly if subscription else 0

        return DashboardStats(
            total_companies=total_companies,
            total_contacts=total_contacts,
            total_searches=total_searches,
            ai_scores_generated=ai_scores_generated,
            credits_remaining=credits_remaining,
            credits_monthly=credits_monthly,
            active_deals=active_deals,
            new_companies_this_month=new_companies_this_month,
            new_contacts_this_month=new_contacts_this_month,
            avg_lead_score=float(avg_lead_score) if avg_lead_score is not None else None,
        )

    async def get_lead_velocity(self, db: AsyncSession, org_id: UUID, days: int = 30) -> LeadVelocityData:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        company_rows = (await db.execute(
            select(
                func.date_trunc("day", Company.created_at).label("day"),
                func.count().label("cnt"),
            )
            .where(
                and_(
                    Company.organization_id == org_id,
                    Company.deleted_at.is_(None),
                    Company.created_at >= since,
                )
            )
            .group_by("day")
            .order_by("day")
        )).all()

        contact_rows = (await db.execute(
            select(
                func.date_trunc("day", Contact.created_at).label("day"),
                func.count().label("cnt"),
            )
            .where(
                and_(
                    Contact.organization_id == org_id,
                    Contact.deleted_at.is_(None),
                    Contact.created_at >= since,
                )
            )
            .group_by("day")
            .order_by("day")
        )).all()

        companies = [
            TimeSeriesPoint(date=row.day.strftime("%Y-%m-%d"), value=row.cnt)
            for row in company_rows
        ]
        contacts = [
            TimeSeriesPoint(date=row.day.strftime("%Y-%m-%d"), value=row.cnt)
            for row in contact_rows
        ]

        return LeadVelocityData(companies=companies, contacts=contacts, period_days=days)

    async def get_score_distribution(self, db: AsyncSession, org_id: UUID) -> ScoreDistribution:
        scores = (await db.execute(
            select(LeadScore.overall_score).where(LeadScore.organization_id == org_id)
        )).scalars().all()

        scores = [float(s) for s in scores if s is not None]
        total = len(scores)

        buckets_def = [
            ("0-20", 0, 20, "#ef4444"),
            ("21-40", 21, 40, "#f97316"),
            ("41-60", 41, 60, "#eab308"),
            ("61-80", 61, 80, "#22c55e"),
            ("81-100", 81, 100, "#10b981"),
        ]

        buckets = []
        for label, low, high, color in buckets_def:
            count = sum(1 for s in scores if low <= s <= high)
            buckets.append(BreakdownItem(
                label=label,
                value=count,
                percentage=_pct(count, total),
                color=color,
            ))

        avg_score = sum(scores) / total if total else 0.0
        med_score = float(median(scores)) if total else 0.0

        return ScoreDistribution(
            buckets=buckets,
            avg_score=round(avg_score, 2),
            median_score=round(med_score, 2),
            total_scored=total,
        )

    async def get_industry_breakdown(self, db: AsyncSession, org_id: UUID) -> IndustryBreakdown:
        company_rows = (await db.execute(
            select(Company.industry, func.count().label("cnt"))
            .where(
                and_(Company.organization_id == org_id, Company.deleted_at.is_(None))
            )
            .group_by(Company.industry)
            .order_by(func.count().desc())
            .limit(10)
        )).all()

        contact_rows = (await db.execute(
            select(Company.industry, func.count().label("cnt"))
            .join(Contact, Contact.company_id == Company.id)
            .where(
                and_(
                    Contact.organization_id == org_id,
                    Contact.deleted_at.is_(None),
                    Company.deleted_at.is_(None),
                )
            )
            .group_by(Company.industry)
            .order_by(func.count().desc())
            .limit(10)
        )).all()

        c_total = sum(r.cnt for r in company_rows)
        ct_total = sum(r.cnt for r in contact_rows)

        companies_by_industry = [
            BreakdownItem(label=r.industry or "Unknown", value=r.cnt, percentage=_pct(r.cnt, c_total))
            for r in company_rows
        ]
        contacts_by_industry = [
            BreakdownItem(label=r.industry or "Unknown", value=r.cnt, percentage=_pct(r.cnt, ct_total))
            for r in contact_rows
        ]

        return IndustryBreakdown(
            companies_by_industry=companies_by_industry,
            contacts_by_industry=contacts_by_industry,
        )

    async def get_geography_breakdown(self, db: AsyncSession, org_id: UUID) -> GeographyBreakdown:
        company_rows = (await db.execute(
            select(Company.country, func.count().label("cnt"))
            .where(
                and_(Company.organization_id == org_id, Company.deleted_at.is_(None))
            )
            .group_by(Company.country)
            .order_by(func.count().desc())
            .limit(15)
        )).all()

        contact_rows = (await db.execute(
            select(Contact.country, func.count().label("cnt"))
            .where(
                and_(Contact.organization_id == org_id, Contact.deleted_at.is_(None))
            )
            .group_by(Contact.country)
            .order_by(func.count().desc())
            .limit(15)
        )).all()

        c_total = sum(r.cnt for r in company_rows)
        ct_total = sum(r.cnt for r in contact_rows)

        return GeographyBreakdown(
            companies_by_country=[
                BreakdownItem(label=r.country or "Unknown", value=r.cnt, percentage=_pct(r.cnt, c_total))
                for r in company_rows
            ],
            contacts_by_country=[
                BreakdownItem(label=r.country or "Unknown", value=r.cnt, percentage=_pct(r.cnt, ct_total))
                for r in contact_rows
            ],
        )

    async def get_seniority_breakdown(self, db: AsyncSession, org_id: UUID) -> SeniorityBreakdown:
        SENIORITY_COLORS: dict[str, str] = {
            "C_LEVEL": "#7c3aed",
            "VP": "#2563eb",
            "DIRECTOR": "#0891b2",
            "MANAGER": "#059669",
            "INDIVIDUAL": "#65a30d",
        }

        rows = (await db.execute(
            select(Contact.seniority_level, func.count().label("cnt"))
            .where(
                and_(Contact.organization_id == org_id, Contact.deleted_at.is_(None))
            )
            .group_by(Contact.seniority_level)
            .order_by(func.count().desc())
        )).all()

        total = sum(r.cnt for r in rows)

        contacts_by_seniority = [
            BreakdownItem(
                label=r.seniority_level or "Unknown",
                value=r.cnt,
                percentage=_pct(r.cnt, total),
                color=SENIORITY_COLORS.get(r.seniority_level or "", None),
            )
            for r in rows
        ]

        return SeniorityBreakdown(contacts_by_seniority=contacts_by_seniority)

    async def get_search_activity(self, db: AsyncSession, org_id: UUID, days: int = 30) -> SearchActivityData:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        daily_rows = (await db.execute(
            select(
                func.date_trunc("day", Search.created_at).label("day"),
                func.count().label("cnt"),
            )
            .where(
                and_(
                    Search.organization_id == org_id,
                    Search.created_at >= since,
                )
            )
            .group_by("day")
            .order_by("day")
        )).all()

        total_searches = (await db.execute(
            select(func.count()).select_from(Search).where(Search.organization_id == org_id)
        )).scalar_one()

        avg_results = (await db.execute(
            select(func.avg(Search.result_count)).where(Search.organization_id == org_id)
        )).scalar_one()

        searches_over_time = [
            TimeSeriesPoint(date=row.day.strftime("%Y-%m-%d"), value=row.cnt)
            for row in daily_rows
        ]

        return SearchActivityData(
            searches_over_time=searches_over_time,
            top_queries=[],
            total_searches=total_searches,
            avg_results_per_search=round(float(avg_results), 2) if avg_results else 0.0,
        )

    async def get_crm_funnel(self, db: AsyncSession, org_id: UUID) -> CRMFunnelData:
        stage_rows = (await db.execute(
            select(
                CRMPipelineStage.name,
                CRMPipelineStage.order,
                func.count(CRMDeal.id).label("deal_count"),
                func.coalesce(func.sum(CRMDeal.value), 0).label("stage_value"),
            )
            .select_from(CRMPipelineStage)
            .outerjoin(
                CRMDeal,
                and_(
                    CRMDeal.stage_id == CRMPipelineStage.id,
                    CRMDeal.deleted_at.is_(None),
                )
            )
            .where(CRMPipelineStage.organization_id == org_id)
            .group_by(CRMPipelineStage.name, CRMPipelineStage.order)
            .order_by(CRMPipelineStage.order)
        )).all()

        total_deals_val = sum(r.deal_count for r in stage_rows)
        stages = [
            BreakdownItem(
                label=r.name,
                value=r.deal_count,
                percentage=_pct(r.deal_count, total_deals_val),
            )
            for r in stage_rows
        ]

        total_value = float(sum(r.stage_value for r in stage_rows))
        avg_deal_value = total_value / total_deals_val if total_deals_val else 0.0

        status_rows = (await db.execute(
            select(CRMDeal.status, func.count().label("cnt"))
            .where(
                and_(CRMDeal.organization_id == org_id, CRMDeal.deleted_at.is_(None))
            )
            .group_by(CRMDeal.status)
            .order_by(func.count().desc())
        )).all()

        status_total = sum(r.cnt for r in status_rows)
        deals_by_status = [
            BreakdownItem(label=r.status or "Unknown", value=r.cnt, percentage=_pct(r.cnt, status_total))
            for r in status_rows
        ]

        return CRMFunnelData(
            stages=stages,
            total_deals=total_deals_val,
            total_value=total_value,
            avg_deal_value=round(avg_deal_value, 2),
            deals_by_status=deals_by_status,
        )

    async def get_credit_usage(self, db: AsyncSession, org_id: UUID, days: int = 30) -> CreditUsageData:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        daily_rows = (await db.execute(
            select(
                func.date_trunc("day", CreditTransaction.created_at).label("day"),
                func.sum(func.abs(CreditTransaction.amount)).label("used"),
            )
            .where(
                and_(
                    CreditTransaction.organization_id == org_id,
                    CreditTransaction.amount < 0,
                    CreditTransaction.created_at >= since,
                )
            )
            .group_by("day")
            .order_by("day")
        )).all()

        type_rows = (await db.execute(
            select(
                CreditTransaction.transaction_type,
                func.sum(func.abs(CreditTransaction.amount)).label("used"),
            )
            .where(
                and_(
                    CreditTransaction.organization_id == org_id,
                    CreditTransaction.amount < 0,
                )
            )
            .group_by(CreditTransaction.transaction_type)
            .order_by(func.sum(func.abs(CreditTransaction.amount)).desc())
        )).all()

        total_used_month = (await db.execute(
            select(func.sum(func.abs(CreditTransaction.amount))).where(
                and_(
                    CreditTransaction.organization_id == org_id,
                    CreditTransaction.amount < 0,
                    CreditTransaction.created_at >= month_start,
                )
            )
        )).scalar_one() or 0

        subscription = (await db.execute(
            select(Subscription).where(Subscription.organization_id == org_id)
        )).scalar_one_or_none()

        credits_remaining = subscription.credits_remaining if subscription else 0

        type_total = sum(float(r.used) for r in type_rows)
        usage_by_type = [
            BreakdownItem(
                label=r.transaction_type or "Unknown",
                value=float(r.used),
                percentage=_pct(float(r.used), type_total),
            )
            for r in type_rows
        ]

        usage_over_time = [
            TimeSeriesPoint(date=row.day.strftime("%Y-%m-%d"), value=float(row.used))
            for row in daily_rows
        ]

        return CreditUsageData(
            usage_over_time=usage_over_time,
            usage_by_type=usage_by_type,
            total_used_this_month=int(total_used_month),
            total_remaining=credits_remaining,
        )

    async def get_full_analytics(self, db: AsyncSession, org_id: UUID) -> FullAnalyticsResponse:
        dashboard_stats = await self.get_dashboard_stats(db, org_id)
        lead_velocity = await self.get_lead_velocity(db, org_id)
        score_distribution = await self.get_score_distribution(db, org_id)
        industry_breakdown = await self.get_industry_breakdown(db, org_id)
        geography = await self.get_geography_breakdown(db, org_id)
        seniority = await self.get_seniority_breakdown(db, org_id)
        search_activity = await self.get_search_activity(db, org_id)
        crm_funnel = await self.get_crm_funnel(db, org_id)
        credit_usage = await self.get_credit_usage(db, org_id)

        return FullAnalyticsResponse(
            dashboard_stats=dashboard_stats,
            lead_velocity=lead_velocity,
            score_distribution=score_distribution,
            industry_breakdown=industry_breakdown,
            geography=geography,
            seniority=seniority,
            search_activity=search_activity,
            crm_funnel=crm_funnel,
            credit_usage=credit_usage,
            generated_at=datetime.now(timezone.utc),
        )

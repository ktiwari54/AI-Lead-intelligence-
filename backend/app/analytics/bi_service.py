from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.analytics.engines import (
    AIInsightEngine,
    AnomalyEngine,
    ForecastEngine,
    FunnelEngine,
    KPIEngine,
    MetricsEngine,
)
from backend.app.analytics.models import Alert, AlertRule, Dashboard, Report
from backend.app.analytics.service import AnalyticsService
from backend.app.discovery.models import DiscoveryJob


class BIService:
    def __init__(self) -> None:
        self._metrics = MetricsEngine()
        self._kpi = KPIEngine()
        self._forecast = ForecastEngine()
        self._anomaly = AnomalyEngine()
        self._funnel = FunnelEngine()
        self._insights = AIInsightEngine()
        self._legacy = AnalyticsService()

    async def executive_dashboard(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        snapshot = await self._metrics.compute_snapshot(db, org_id)
        kpis = self._kpi.build_executive_kpis(snapshot)
        company_series = await self._metrics.time_series(db, org_id, "companies_created", days=90)
        contact_series = await self._metrics.time_series(db, org_id, "contacts_created", days=90)
        forecasts = self._forecast.forecast_metric("companies_created", company_series, periods=30)
        insights = self._insights.summarize_dashboard(snapshot, kpis)

        return {
            "dashboard_type": "executive",
            "snapshot": snapshot,
            "kpis": kpis,
            "growth": {
                "monthly_companies": snapshot.get("new_companies_this_month", 0),
                "company_trend": company_series[-30:],
                "contact_trend": contact_series[-30:],
            },
            "forecasts": forecasts,
            "executive_summary": insights,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def sales_analytics(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        funnel = await self._funnel.lead_funnel(db, org_id)
        pipeline = await self._funnel.sales_funnel(db, org_id)
        crm = await self._legacy.get_crm_funnel(db, org_id)
        velocity = await self._legacy.get_lead_velocity(db, org_id, 30)
        return {
            "lead_funnel": funnel,
            "sales_pipeline": pipeline,
            "crm_funnel": crm.model_dump(),
            "lead_velocity": velocity.model_dump(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def discovery_analytics(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        total = (await db.execute(
            select(func.count()).select_from(DiscoveryJob).where(DiscoveryJob.organization_id == org_id)
        )).scalar_one() or 0

        completed = (await db.execute(
            select(func.count()).select_from(DiscoveryJob).where(
                DiscoveryJob.organization_id == org_id, DiscoveryJob.status == "completed"
            )
        )).scalar_one() or 0

        failed = (await db.execute(
            select(func.count()).select_from(DiscoveryJob).where(
                DiscoveryJob.organization_id == org_id, DiscoveryJob.status == "failed"
            )
        )).scalar_one() or 0

        avg_time = (await db.execute(
            select(func.avg(DiscoveryJob.took_ms)).where(
                DiscoveryJob.organization_id == org_id, DiscoveryJob.took_ms.isnot(None)
            )
        )).scalar_one()

        avg_results = (await db.execute(
            select(func.avg(DiscoveryJob.result_count)).where(
                DiscoveryJob.organization_id == org_id, DiscoveryJob.result_count.isnot(None)
            )
        )).scalar_one()

        series = await self._metrics.time_series(db, org_id, "discovery_jobs", days=30)

        return {
            "total_jobs": total,
            "completed_jobs": completed,
            "failed_jobs": failed,
            "success_rate": round(completed / total * 100, 2) if total else 0,
            "avg_search_time_ms": float(avg_time) if avg_time else None,
            "avg_results_per_search": float(avg_results) if avg_results else 0,
            "jobs_over_time": series,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def ai_analytics(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        legacy = await self._legacy.get_dashboard_stats(db, org_id)
        scores = await self._legacy.get_score_distribution(db, org_id)
        return {
            "ai_requests": legacy.ai_scores_generated,
            "avg_lead_score": legacy.avg_lead_score,
            "score_distribution": scores.model_dump(),
            "credits_remaining": legacy.credits_remaining,
            "credits_monthly": legacy.credits_monthly,
            "token_usage": {"stub": True, "total_tokens": legacy.ai_scores_generated * 1500},
            "model_usage": [{"model": "default", "requests": legacy.ai_scores_generated}],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def workflow_analytics(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        from backend.app.workflows.repository import get_analytics as wf_analytics

        data = await wf_analytics(db, org_id, days=30)
        return {**data, "generated_at": datetime.now(timezone.utc).isoformat()}

    async def platform_analytics(self, db: AsyncSession, org_id: UUID) -> dict[str, Any]:
        snapshot = await self._metrics.compute_snapshot(db, org_id)
        search_activity = await self._legacy.get_search_activity(db, org_id, 30)
        return {
            "active_users": snapshot.get("active_users", 0),
            "total_searches": snapshot.get("total_searches", 0),
            "discovery_jobs": snapshot.get("discovery_jobs", 0),
            "search_activity": search_activity.model_dump(),
            "feature_adoption": {
                "companies": snapshot.get("total_companies", 0) > 0,
                "contacts": snapshot.get("total_contacts", 0) > 0,
                "discovery": snapshot.get("discovery_jobs", 0) > 0,
                "ai_scoring": snapshot.get("ai_scores_generated", 0) > 0,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def detect_anomalies(self, db: AsyncSession, org_id: UUID) -> list[dict[str, Any]]:
        metrics = {
            "companies_created": await self._metrics.time_series(db, org_id, "companies_created", days=60),
            "contacts_created": await self._metrics.time_series(db, org_id, "contacts_created", days=60),
            "searches": await self._metrics.time_series(db, org_id, "searches", days=60),
        }
        return self._anomaly.scan_metrics(metrics)

    async def ask_insights(self, db: AsyncSession, org_id: UUID, question: str) -> dict[str, Any]:
        snapshot = await self._metrics.compute_snapshot(db, org_id)
        return self._insights.answer_question(question, {"snapshot": snapshot})

    async def list_dashboards(self, db: AsyncSession, org_id: UUID) -> list[Dashboard]:
        result = await db.execute(
            select(Dashboard).where(
                Dashboard.organization_id == org_id, Dashboard.deleted_at.is_(None)
            ).order_by(Dashboard.name)
        )
        return list(result.scalars().all())

    async def get_dashboard(self, db: AsyncSession, dashboard_id: UUID, org_id: UUID) -> Dashboard | None:
        result = await db.execute(
            select(Dashboard).where(
                Dashboard.id == dashboard_id,
                Dashboard.organization_id == org_id,
                Dashboard.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_alerts(self, db: AsyncSession, org_id: UUID, *, acknowledged: bool | None = None) -> list[Alert]:
        q = select(Alert).where(Alert.organization_id == org_id, Alert.deleted_at.is_(None))
        if acknowledged is not None:
            q = q.where(Alert.is_acknowledged == acknowledged)
        result = await db.execute(q.order_by(Alert.created_at.desc()).limit(50))
        return list(result.scalars().all())

    async def list_alert_rules(self, db: AsyncSession, org_id: UUID) -> list[AlertRule]:
        result = await db.execute(
            select(AlertRule).where(AlertRule.organization_id == org_id, AlertRule.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def list_reports(self, db: AsyncSession, org_id: UUID) -> list[Report]:
        result = await db.execute(
            select(Report).where(Report.organization_id == org_id, Report.deleted_at.is_(None))
        )
        return list(result.scalars().all())
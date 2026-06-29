from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.analytics.bi_service import BIService
from backend.app.analytics.schemas import DashboardCreateRequest, InsightQuestionRequest
from backend.app.common.cache import cache_get, cache_set
from backend.app.common.deps import get_current_user, get_db
from backend.app.common.response import APIResponse
from backend.app.users.models import User

router = APIRouter(tags=["Analytics BI"])
_bi = BIService()
CACHE_TTL = 300


def _cache_key(org_id, endpoint: str, **kwargs) -> str:
    suffix = "_".join(f"{k}{v}" for k, v in kwargs.items())
    return f"bi:{org_id}:{endpoint}:{suffix}" if suffix else f"bi:{org_id}:{endpoint}"


@router.get("/executive", response_model=APIResponse)
async def executive_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = _cache_key(current_user.organization_id, "executive")
    cached = await cache_get(key)
    if cached:
        return APIResponse(data=json.loads(cached))
    data = await _bi.executive_dashboard(db, current_user.organization_id)
    await cache_set(key, json.dumps(data), ttl=CACHE_TTL)
    return APIResponse(data=data)


@router.get("/sales", response_model=APIResponse)
async def sales_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _bi.sales_analytics(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/discovery", response_model=APIResponse)
async def discovery_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _bi.discovery_analytics(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/ai", response_model=APIResponse)
async def ai_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _bi.ai_analytics(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/workflows", response_model=APIResponse)
async def workflow_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _bi.workflow_analytics(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/platform", response_model=APIResponse)
async def platform_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _bi.platform_analytics(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/anomalies", response_model=APIResponse)
async def anomaly_detection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _bi.detect_anomalies(db, current_user.organization_id)
    return APIResponse(data=data)


@router.post("/insights/ask", response_model=APIResponse)
async def ask_insights(
    body: InsightQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _bi.ask_insights(db, current_user.organization_id, body.question)
    return APIResponse(data=data)


@router.get("/dashboards/custom", response_model=APIResponse)
async def list_custom_dashboards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dashboards = await _bi.list_dashboards(db, current_user.organization_id)
    return APIResponse(data=[
        {
            "id": str(d.id),
            "name": d.name,
            "slug": d.slug,
            "dashboard_type": d.dashboard_type,
            "is_system": d.is_system,
        }
        for d in dashboards
    ])


@router.get("/alerts", response_model=APIResponse)
async def list_alerts(
    acknowledged: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    alerts = await _bi.list_alerts(db, current_user.organization_id, acknowledged=acknowledged)
    return APIResponse(data=[
        {
            "id": str(a.id),
            "title": a.title,
            "severity": a.severity,
            "message": a.message,
            "is_acknowledged": a.is_acknowledged,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ])


@router.get("/alert-rules", response_model=APIResponse)
async def list_alert_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rules = await _bi.list_alert_rules(db, current_user.organization_id)
    return APIResponse(data=[
        {
            "id": str(r.id),
            "name": r.name,
            "metric_key": r.metric_key,
            "condition": r.condition,
            "threshold": float(r.threshold),
            "severity": r.severity,
            "is_active": r.is_active,
        }
        for r in rules
    ])


@router.get("/reports", response_model=APIResponse)
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reports = await _bi.list_reports(db, current_user.organization_id)
    return APIResponse(data=[
        {"id": str(r.id), "name": r.name, "slug": r.slug, "is_scheduled": r.is_scheduled}
        for r in reports
    ])


@router.get("/forecasts/{metric_key}", response_model=APIResponse)
async def get_forecast(
    metric_key: str,
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.analytics.engines import ForecastEngine, MetricsEngine

    series = await MetricsEngine().time_series(db, current_user.organization_id, metric_key, days=days)
    forecast = ForecastEngine().forecast_metric(metric_key, series, periods=30)
    return APIResponse(data=forecast)
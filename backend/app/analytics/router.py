from __future__ import annotations
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.analytics.schemas import (
    CRMFunnelData, CreditUsageData, DashboardStats, FullAnalyticsResponse,
    GeographyBreakdown, IndustryBreakdown, LeadVelocityData, ScoreDistribution,
    SearchActivityData, SeniorityBreakdown,
)
from backend.app.analytics.service import AnalyticsService
from backend.app.common.cache import cache_get, cache_set
from backend.app.common.deps import get_current_user, get_db
from backend.app.common.response import APIResponse
from backend.app.users.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])
_service = AnalyticsService()
CACHE_TTL = 300  # 5 minutes


def _cache_key(org_id: UUID, endpoint: str, **kwargs) -> str:
    suffix = "_".join(f"{k}{v}" for k, v in kwargs.items())
    return f"analytics:{org_id}:{endpoint}:{suffix}" if suffix else f"analytics:{org_id}:{endpoint}"


@router.get("/dashboard", response_model=APIResponse[DashboardStats])
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = _cache_key(current_user.organization_id, "dashboard")
    cached = await cache_get(key)
    if cached:
        return APIResponse(data=DashboardStats(**json.loads(cached)))
    data = await _service.get_dashboard_stats(db, current_user.organization_id)
    await cache_set(key, json.dumps(data.model_dump()), ttl=CACHE_TTL)
    return APIResponse(data=data)


@router.get("/lead-velocity", response_model=APIResponse[LeadVelocityData])
async def get_lead_velocity(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = _cache_key(current_user.organization_id, "lead_velocity", days=days)
    cached = await cache_get(key)
    if cached:
        return APIResponse(data=LeadVelocityData(**json.loads(cached)))
    data = await _service.get_lead_velocity(db, current_user.organization_id, days)
    await cache_set(key, json.dumps(data.model_dump()), ttl=CACHE_TTL)
    return APIResponse(data=data)


@router.get("/score-distribution", response_model=APIResponse[ScoreDistribution])
async def get_score_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = _cache_key(current_user.organization_id, "score_dist")
    cached = await cache_get(key)
    if cached:
        return APIResponse(data=ScoreDistribution(**json.loads(cached)))
    data = await _service.get_score_distribution(db, current_user.organization_id)
    await cache_set(key, json.dumps(data.model_dump()), ttl=CACHE_TTL)
    return APIResponse(data=data)


@router.get("/industry", response_model=APIResponse[IndustryBreakdown])
async def get_industry(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _service.get_industry_breakdown(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/geography", response_model=APIResponse[GeographyBreakdown])
async def get_geography(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _service.get_geography_breakdown(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/seniority", response_model=APIResponse[SeniorityBreakdown])
async def get_seniority(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _service.get_seniority_breakdown(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/search-activity", response_model=APIResponse[SearchActivityData])
async def get_search_activity(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _service.get_search_activity(db, current_user.organization_id, days)
    return APIResponse(data=data)


@router.get("/crm-funnel", response_model=APIResponse[CRMFunnelData])
async def get_crm_funnel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _service.get_crm_funnel(db, current_user.organization_id)
    return APIResponse(data=data)


@router.get("/credits", response_model=APIResponse[CreditUsageData])
async def get_credit_usage(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await _service.get_credit_usage(db, current_user.organization_id, days)
    return APIResponse(data=data)


@router.get("/full", response_model=APIResponse[FullAnalyticsResponse])
async def get_full_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    key = _cache_key(current_user.organization_id, "full")
    cached = await cache_get(key)
    if cached:
        raw = json.loads(cached)
        raw["generated_at"] = datetime.fromisoformat(raw["generated_at"])
        return APIResponse(data=FullAnalyticsResponse(**raw))
    data = await _service.get_full_analytics(db, current_user.organization_id)
    payload = data.model_dump()
    payload["generated_at"] = data.generated_at.isoformat()
    await cache_set(key, json.dumps(payload), ttl=CACHE_TTL)
    return APIResponse(data=data)

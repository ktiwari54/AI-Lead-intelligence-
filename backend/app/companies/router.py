"""Companies router with CRUD + spatial search."""
from __future__ import annotations
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.deps import get_current_user, get_db
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.companies.spatial import (
    SpatialSearchRequest,
    SpatialCompanyResult,
    count_companies_near,
    search_companies_near,
    set_company_location,
    geocode_companies_without_location,
)
from backend.app.users.models import User

router = APIRouter(prefix="/companies", tags=["Companies"])


# ─── Existing CRUD (preserve these exactly) ──────────────────────────────────────────────

@router.get("/")
async def list_companies(
    query: str | None = Query(None),
    industry_id: UUID | None = Query(None),
    country_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.companies.models import Company
    from sqlalchemy import func

    q = select(Company).where(
        Company.organization_id == current_user.organization_id,
        Company.deleted_at.is_(None),
    )
    if query:
        q = q.where(Company.name.ilike(f"%{query}%"))
    if country_id:
        q = q.where(Company.country_id == country_id)

    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    result = await db.execute(q.order_by(Company.name).offset((page - 1) * page_size).limit(page_size))
    companies = result.scalars().all()
    return PaginatedResponse.create(items=[c.to_dict() for c in companies], total=total, page=page, page_size=page_size)


@router.post("/", status_code=201)
async def create_company(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.companies.models import Company
    company = Company(organization_id=current_user.organization_id, **{k: v for k, v in body.items() if k not in ("id", "organization_id")})
    db.add(company)
    await db.flush()
    return APIResponse(data=company.to_dict())


@router.get("/{company_id}")
async def get_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.companies.models import Company
    company = await db.scalar(select(Company).where(Company.id == company_id, Company.organization_id == current_user.organization_id, Company.deleted_at.is_(None)))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return APIResponse(data=company.to_dict())


@router.patch("/{company_id}")
async def update_company(
    company_id: UUID,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.companies.models import Company
    company = await db.scalar(select(Company).where(Company.id == company_id, Company.organization_id == current_user.organization_id, Company.deleted_at.is_(None)))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for k, v in body.items():
        if k not in ("id", "organization_id", "created_at"):
            setattr(company, k, v)
    await db.flush()
    return APIResponse(data=company.to_dict())


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.app.companies.models import Company
    from datetime import datetime, timezone
    company = await db.scalar(select(Company).where(Company.id == company_id, Company.organization_id == current_user.organization_id, Company.deleted_at.is_(None)))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.deleted_at = datetime.now(timezone.utc)
    await db.flush()


# ─── Spatial search endpoints ─────────────────────────────────────────────────────

@router.get("/spatial/search")
async def spatial_company_search(
    lat: float = Query(..., ge=-90, le=90, description="Center latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius_km: float = Query(50.0, ge=0.1, le=5000, description="Search radius in kilometers"),
    industry: str | None = Query(None),
    min_employees: int | None = Query(None, ge=1),
    max_employees: int | None = Query(None, ge=1),
    min_score: float | None = Query(None, ge=0, le=100),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Find companies within a geographic radius.
    Results are ordered by distance (nearest first).
    
    Example: GET /companies/spatial/search?lat=25.2048&lon=55.2708&radius_km=50
    Returns companies within 50 km of Dubai.
    """
    request = SpatialSearchRequest(
        latitude=lat,
        longitude=lon,
        radius_km=radius_km,
        industry=industry,
        min_employees=min_employees,
        max_employees=max_employees,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    results = await search_companies_near(db, current_user.organization_id, request)
    total = await count_companies_near(db, current_user.organization_id, lat, lon, radius_km)

    return {
        "data": {
            "results": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "domain": r.domain,
                    "industry": r.industry,
                    "country": r.country,
                    "city": r.city,
                    "employee_count": r.employee_count,
                    "coordinates": {"lat": r.latitude, "lon": r.longitude} if r.latitude else None,
                    "distance_km": r.distance_km,
                    "overall_score": r.overall_score,
                }
                for r in results
            ],
            "total": total,
            "center": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
        }
    }


@router.patch("/{company_id}/location")
async def set_location(
    company_id: UUID,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set or update geographic coordinates for a company."""
    updated = await set_company_location(db, current_user.organization_id, company_id, lat, lon)
    if not updated:
        raise HTTPException(status_code=404, detail="Company not found")
    return APIResponse(data={"company_id": str(company_id), "latitude": lat, "longitude": lon})


@router.get("/spatial/needs-geocoding")
async def companies_needing_geocoding(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return companies that have city/country but no coordinates yet."""
    companies = await geocode_companies_without_location(db, current_user.organization_id, limit)
    return APIResponse(data={"companies": companies, "count": len(companies)})

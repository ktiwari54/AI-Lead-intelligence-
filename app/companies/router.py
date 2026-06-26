"""Company endpoints."""
from uuid import UUID

from fastapi import APIRouter, Query

from app.common.dependencies import DbDep, UserDep
from app.common.schemas import Page, PageParams, SuccessResponse
from app.companies.schemas import (
    CompanyCreate,
    CompanyFilterParams,
    CompanyMergeRequest,
    CompanyResponse,
    CompanySummaryResponse,
    CompanyUpdate,
)
from app.companies.service import CompanyService

router = APIRouter()


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(req: CompanyCreate, user: UserDep, db: DbDep) -> dict:
    """Create a new company."""
    user.require_permission("companies:create")
    return await CompanyService(db).create(user.org_id, user.user_id, req)


@router.get("", response_model=Page[CompanyResponse])
async def list_companies(
    user: UserDep,
    db: DbDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = Query(default=None),
    country_code: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    employee_min: int | None = Query(default=None),
    employee_max: int | None = Query(default=None),
    is_public: bool | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
) -> Page:
    """List companies with filters, search, and pagination."""
    user.require_permission("companies:read")
    params = CompanyFilterParams(
        page=page, page_size=page_size, search=search,
        country_code=country_code, industry=industry,
        employee_min=employee_min, employee_max=employee_max,
        is_public=is_public, sort_by=sort_by, sort_dir=sort_dir,
    )
    items, total = await CompanyService(db).list_companies(user.org_id, params)
    return Page.create(items, total, PageParams(page=page, page_size=page_size))


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: UUID, user: UserDep, db: DbDep) -> dict:
    """Get a company by ID."""
    user.require_permission("companies:read")
    return await CompanyService(db).get(user.org_id, company_id)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: UUID, req: CompanyUpdate, user: UserDep, db: DbDep) -> dict:
    """Update a company."""
    user.require_permission("companies:update")
    return await CompanyService(db).update(user.org_id, user.user_id, company_id, req)


@router.delete("/{company_id}", response_model=SuccessResponse)
async def delete_company(company_id: UUID, user: UserDep, db: DbDep) -> SuccessResponse:
    """Soft-delete a company."""
    user.require_permission("companies:delete")
    await CompanyService(db).delete(user.org_id, user.user_id, company_id)
    return SuccessResponse(message="Company deleted")


@router.post("/merge", response_model=CompanyResponse)
async def merge_companies(req: CompanyMergeRequest, user: UserDep, db: DbDep) -> dict:
    """Merge two companies (source into target)."""
    user.require_permission("companies:update")
    return await CompanyService(db).merge(user.org_id, req.source_id, req.target_id)


@router.get("/{company_id}/timeline")
async def get_timeline(
    company_id: UUID,
    user: UserDep,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=200),
) -> list:
    """Get activity timeline for a company."""
    user.require_permission("companies:read")
    return await CompanyService(db).get_timeline(user.org_id, company_id, limit)


@router.post("/{company_id}/summary", response_model=CompanySummaryResponse)
async def generate_summary(company_id: UUID, user: UserDep, db: DbDep) -> dict:
    """Generate an AI-powered company intelligence summary."""
    user.require_permission("companies:read")
    return await CompanyService(db).generate_summary(user.org_id, company_id)

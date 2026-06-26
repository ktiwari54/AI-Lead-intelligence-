import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.companies.schemas import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyFilter
from backend.app.companies.service import CompanyService
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_org_id

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[CompanyResponse])
async def list_companies(
    query: str | None = Query(None),
    industry_id: uuid.UUID | None = Query(None),
    country_id: uuid.UUID | None = Query(None),
    employee_range: str | None = Query(None),
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    filters = CompanyFilter(
        query=query, industry_id=industry_id, country_id=country_id, employee_range=employee_range
    )
    companies, total = await CompanyService(db).list_companies(org_id, pagination, filters)
    return PaginatedResponse.create(
        data=[CompanyResponse.model_validate(c) for c in companies],
        total=total, page=pagination.page, per_page=pagination.per_page,
    )


@router.post("/", response_model=APIResponse[CompanyResponse], status_code=201)
async def create_company(
    data: CompanyCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    company = await CompanyService(db).create(org_id, data)
    return APIResponse(data=CompanyResponse.model_validate(company), message="Company created")


@router.get("/{company_id}", response_model=APIResponse[CompanyResponse])
async def get_company(
    company_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    company = await CompanyService(db).get_by_id(company_id, org_id)
    return APIResponse(data=CompanyResponse.model_validate(company))


@router.patch("/{company_id}", response_model=APIResponse[CompanyResponse])
async def update_company(
    company_id: uuid.UUID,
    data: CompanyUpdate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    company = await CompanyService(db).update(company_id, org_id, data)
    return APIResponse(data=CompanyResponse.model_validate(company))


@router.delete("/{company_id}", response_model=APIResponse)
async def delete_company(
    company_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    await CompanyService(db).delete(company_id, org_id)
    return APIResponse(message="Company deleted")

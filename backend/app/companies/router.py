from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.common.dependencies import get_current_org
from app.companies import service
from app.companies.schemas import CompanyCreate, CompanyUpdate, CompanyOut, CompanyListOut

router = APIRouter()


@router.get("", response_model=CompanyListOut)
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    org=Depends(get_current_org),
):
    return await service.list_companies(org.id, page, page_size, db)


@router.post("", response_model=CompanyOut, status_code=201)
async def create_company(data: CompanyCreate, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    return await service.create_company(data, org.id, db)


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(company_id: UUID, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    return await service.get_company(company_id, org.id, db)


@router.patch("/{company_id}", response_model=CompanyOut)
async def update_company(company_id: UUID, data: CompanyUpdate, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    return await service.update_company(company_id, data, org.id, db)


@router.delete("/{company_id}", status_code=204)
async def delete_company(company_id: UUID, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    await service.delete_company(company_id, org.id, db)

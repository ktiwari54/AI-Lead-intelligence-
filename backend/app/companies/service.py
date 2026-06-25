from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.companies import Company
from app.companies.schemas import CompanyCreate, CompanyUpdate
from app.core.exceptions import NotFoundError


async def list_companies(org_id: UUID, page: int, page_size: int, db: AsyncSession) -> dict:
    offset = (page - 1) * page_size
    base_q = select(Company).where(Company.organization_id == org_id, Company.is_deleted == False)
    total = (await db.execute(select(func.count()).select_from(base_q.subquery()))).scalar()
    items = (await db.execute(
        base_q.options(selectinload(Company.social_profiles)).offset(offset).limit(page_size)
    )).scalars().all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def get_company(company_id: UUID, org_id: UUID, db: AsyncSession) -> Company:
    result = await db.execute(
        select(Company)
        .where(Company.id == company_id, Company.organization_id == org_id, Company.is_deleted == False)
        .options(selectinload(Company.social_profiles), selectinload(Company.technologies))
    )
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Company not found")
    return company


async def create_company(data: CompanyCreate, org_id: UUID, db: AsyncSession) -> Company:
    company = Company(**data.model_dump(exclude_none=True), organization_id=org_id)
    db.add(company)
    await db.flush()
    return company


async def update_company(company_id: UUID, data: CompanyUpdate, org_id: UUID, db: AsyncSession) -> Company:
    company = await get_company(company_id, org_id, db)
    for k, v in data.model_dump(exclude_none=True, exclude_unset=True).items():
        setattr(company, k, v)
    return company


async def delete_company(company_id: UUID, org_id: UUID, db: AsyncSession) -> None:
    company = await get_company(company_id, org_id, db)
    company.is_deleted = True

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from backend.app.companies.models import Company
from backend.app.companies.schemas import CompanyCreate, CompanyUpdate, CompanyFilter
from backend.app.common.exceptions import NotFoundError
from backend.app.common.pagination import PaginationParams


class CompanyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, company_id: uuid.UUID, org_id: uuid.UUID) -> Company:
        result = await self.db.execute(
            select(Company)
            .options(selectinload(Company.social_profiles), selectinload(Company.technologies))
            .where(Company.id == company_id, Company.organization_id == org_id, Company.deleted_at.is_(None))
        )
        company = result.scalar_one_or_none()
        if not company:
            raise NotFoundError("Company not found")
        return company

    async def list_companies(
        self, org_id: uuid.UUID, pagination: PaginationParams, filters: CompanyFilter
    ) -> tuple[list[Company], int]:
        stmt = select(Company).where(
            Company.organization_id == org_id, Company.deleted_at.is_(None)
        )
        if filters.query:
            stmt = stmt.where(
                or_(
                    Company.company_name.ilike(f"%{filters.query}%"),
                    Company.domain.ilike(f"%{filters.query}%"),
                )
            )
        if filters.industry_id:
            stmt = stmt.where(Company.industry_id == filters.industry_id)
        if filters.country_id:
            stmt = stmt.where(Company.country_id == filters.country_id)
        if filters.employee_range:
            stmt = stmt.where(Company.employee_range == filters.employee_range)

        count = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count.scalar()
        result = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
        return result.scalars().all(), total

    async def create(self, org_id: uuid.UUID, data: CompanyCreate) -> Company:
        company = Company(organization_id=org_id, **data.model_dump(exclude_none=True))
        self.db.add(company)
        await self.db.flush()
        return company

    async def update(self, company_id: uuid.UUID, org_id: uuid.UUID, data: CompanyUpdate) -> Company:
        company = await self.get_by_id(company_id, org_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(company, field, value)
        return company

    async def delete(self, company_id: uuid.UUID, org_id: uuid.UUID) -> None:
        from datetime import datetime, timezone
        company = await self.get_by_id(company_id, org_id)
        company.deleted_at = datetime.now(timezone.utc)

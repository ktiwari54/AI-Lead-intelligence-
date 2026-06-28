from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.companies.models import Company
from backend.infrastructure.repositories.base import BaseRepository, Page, PageParams


@dataclass
class CompanyFilters:
    query: str | None = None
    industry: list[str] | None = None
    country: list[str] | None = None
    employee_min: int | None = None
    employee_max: int | None = None
    lead_score_min: float | None = None


class SQLAlchemyCompanyRepository(BaseRepository[Company]):
    model = Company

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_domain(self, domain: str, org_id: UUID) -> Company | None:
        result = await self.session.execute(
            self._base_query(org_id).where(Company.domain == domain)
        )
        return result.scalar_one_or_none()

    async def list_filtered(
        self, org_id: UUID, filters: CompanyFilters, page: PageParams
    ) -> Page[Company]:
        query = self._base_query(org_id)

        if filters.query:
            pattern = f"%{filters.query}%"
            query = query.where(
                or_(Company.name.ilike(pattern), Company.domain.ilike(pattern))
            )
        if filters.industry:
            query = query.where(Company.industry.in_(filters.industry))
        if filters.country:
            query = query.where(Company.country.in_(filters.country))
        if filters.employee_min is not None:
            query = query.where(Company.employee_count >= filters.employee_min)
        if filters.employee_max is not None:
            query = query.where(Company.employee_count <= filters.employee_max)
        if filters.lead_score_min is not None:
            query = query.where(Company.lead_score >= filters.lead_score_min)

        query = query.order_by(Company.created_at.desc())
        items, total = await self.paginate(query, page)
        return Page(items=items, total=total, page=page.page, page_size=page.page_size)

    async def create(self, company: Company) -> Company:
        self.session.add(company)
        await self.session.flush()
        await self.session.refresh(company)
        return company

    async def update(self, company: Company) -> Company:
        await self.session.flush()
        await self.session.refresh(company)
        return company
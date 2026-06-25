import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.organizations.models import Organization
from backend.app.organizations.schemas import OrganizationUpdate
from backend.app.common.exceptions import NotFoundError, ForbiddenError


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, org_id: uuid.UUID) -> Organization:
        result = await self.db.execute(
            select(Organization).where(
                Organization.id == org_id, Organization.deleted_at.is_(None)
            )
        )
        org = result.scalar_one_or_none()
        if not org:
            raise NotFoundError("Organization not found")
        return org

    async def update(self, org_id: uuid.UUID, data: OrganizationUpdate) -> Organization:
        org = await self.get_by_id(org_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(org, field, value)
        return org

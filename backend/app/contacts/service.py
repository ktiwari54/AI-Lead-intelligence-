import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from backend.app.contacts.models import Contact
from backend.app.contacts.schemas import ContactCreate, ContactUpdate, ContactFilter
from backend.app.common.exceptions import NotFoundError
from backend.app.common.pagination import PaginationParams


class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, contact_id: uuid.UUID, org_id: uuid.UUID) -> Contact:
        result = await self.db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.organization_id == org_id,
                Contact.deleted_at.is_(None),
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            raise NotFoundError("Contact not found")
        return contact

    async def list_contacts(
        self, org_id: uuid.UUID, pagination: PaginationParams, filters: ContactFilter
    ) -> tuple[list[Contact], int]:
        stmt = select(Contact).where(
            Contact.organization_id == org_id, Contact.deleted_at.is_(None)
        )
        if filters.query:
            stmt = stmt.where(
                or_(
                    Contact.first_name.ilike(f"%{filters.query}%"),
                    Contact.last_name.ilike(f"%{filters.query}%"),
                    Contact.email.ilike(f"%{filters.query}%"),
                    Contact.designation.ilike(f"%{filters.query}%"),
                )
            )
        if filters.company_id:
            stmt = stmt.where(Contact.company_id == filters.company_id)
        if filters.country_id:
            stmt = stmt.where(Contact.country_id == filters.country_id)
        if filters.designation:
            stmt = stmt.where(Contact.designation.ilike(f"%{filters.designation}%"))
        if filters.department:
            stmt = stmt.where(Contact.department.ilike(f"%{filters.department}%"))
        if filters.email_status:
            stmt = stmt.where(Contact.email_status == filters.email_status)

        count = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count.scalar()
        result = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
        return result.scalars().all(), total

    async def create(self, org_id: uuid.UUID, data: ContactCreate) -> Contact:
        contact = Contact(organization_id=org_id, **data.model_dump(exclude_none=True))
        self.db.add(contact)
        await self.db.flush()
        return contact

    async def update(self, contact_id: uuid.UUID, org_id: uuid.UUID, data: ContactUpdate) -> Contact:
        contact = await self.get_by_id(contact_id, org_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(contact, field, value)
        return contact

    async def delete(self, contact_id: uuid.UUID, org_id: uuid.UUID) -> None:
        contact = await self.get_by_id(contact_id, org_id)
        contact.deleted_at = datetime.now(timezone.utc)

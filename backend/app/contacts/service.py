from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.models.contacts import Contact
from app.contacts.schemas import ContactCreate, ContactUpdate
from app.core.exceptions import NotFoundError


async def list_contacts(org_id: UUID, page: int, page_size: int, db: AsyncSession) -> dict:
    offset = (page - 1) * page_size
    base_q = select(Contact).where(Contact.organization_id == org_id, Contact.is_deleted == False)
    total = (await db.execute(select(func.count()).select_from(base_q.subquery()))).scalar()
    items = (await db.execute(
        base_q.options(selectinload(Contact.social_profiles)).offset(offset).limit(page_size)
    )).scalars().all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


async def get_contact(contact_id: UUID, org_id: UUID, db: AsyncSession) -> Contact:
    result = await db.execute(
        select(Contact)
        .where(Contact.id == contact_id, Contact.organization_id == org_id, Contact.is_deleted == False)
        .options(selectinload(Contact.social_profiles))
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise NotFoundError("Contact not found")
    return contact


async def create_contact(data: ContactCreate, org_id: UUID, db: AsyncSession) -> Contact:
    payload = data.model_dump(exclude_none=True)
    payload["full_name"] = f"{payload['first_name']} {payload.get('last_name', '')}".strip()
    contact = Contact(**payload, organization_id=org_id)
    db.add(contact)
    await db.flush()
    return contact


async def update_contact(contact_id: UUID, data: ContactUpdate, org_id: UUID, db: AsyncSession) -> Contact:
    contact = await get_contact(contact_id, org_id, db)
    for k, v in data.model_dump(exclude_none=True, exclude_unset=True).items():
        setattr(contact, k, v)
    contact.full_name = f"{contact.first_name} {contact.last_name or ''}".strip()
    return contact


async def delete_contact(contact_id: UUID, org_id: UUID, db: AsyncSession) -> None:
    contact = await get_contact(contact_id, org_id, db)
    contact.is_deleted = True

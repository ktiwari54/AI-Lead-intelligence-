from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.common.dependencies import get_current_org
from app.contacts import service
from app.contacts.schemas import ContactCreate, ContactUpdate, ContactOut, ContactListOut

router = APIRouter()


@router.get("", response_model=ContactListOut)
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    org=Depends(get_current_org),
):
    return await service.list_contacts(org.id, page, page_size, db)


@router.post("", response_model=ContactOut, status_code=201)
async def create_contact(data: ContactCreate, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    return await service.create_contact(data, org.id, db)


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(contact_id: UUID, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    return await service.get_contact(contact_id, org.id, db)


@router.patch("/{contact_id}", response_model=ContactOut)
async def update_contact(contact_id: UUID, data: ContactUpdate, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    return await service.update_contact(contact_id, data, org.id, db)


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(contact_id: UUID, db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    await service.delete_contact(contact_id, org.id, db)

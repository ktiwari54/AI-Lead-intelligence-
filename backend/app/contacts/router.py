import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.contacts.schemas import ContactCreate, ContactUpdate, ContactResponse, ContactFilter
from backend.app.contacts.service import ContactService
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_org_id

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ContactResponse])
async def list_contacts(
    query: str | None = Query(None),
    company_id: uuid.UUID | None = Query(None),
    country_id: uuid.UUID | None = Query(None),
    designation: str | None = Query(None),
    department: str | None = Query(None),
    seniority: str | None = Query(None),
    email_status: str | None = Query(None),
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    filters = ContactFilter(
        query=query, company_id=company_id, country_id=country_id,
        designation=designation, department=department, seniority=seniority,
        email_status=email_status,
    )
    contacts, total = await ContactService(db).list_contacts(org_id, pagination, filters)
    return PaginatedResponse.create(
        data=[ContactResponse.model_validate(c) for c in contacts],
        total=total, page=pagination.page, per_page=pagination.per_page,
    )


@router.post("/", response_model=APIResponse[ContactResponse], status_code=201)
async def create_contact(
    data: ContactCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    contact = await ContactService(db).create(org_id, data)
    return APIResponse(data=ContactResponse.model_validate(contact), message="Contact created")


@router.get("/{contact_id}", response_model=APIResponse[ContactResponse])
async def get_contact(
    contact_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    contact = await ContactService(db).get_by_id(contact_id, org_id)
    return APIResponse(data=ContactResponse.model_validate(contact))


@router.patch("/{contact_id}", response_model=APIResponse[ContactResponse])
async def update_contact(
    contact_id: uuid.UUID,
    data: ContactUpdate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    contact = await ContactService(db).update(contact_id, org_id, data)
    return APIResponse(data=ContactResponse.model_validate(contact))


@router.delete("/{contact_id}", response_model=APIResponse)
async def delete_contact(
    contact_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    await ContactService(db).delete(contact_id, org_id)
    return APIResponse(message="Contact deleted")

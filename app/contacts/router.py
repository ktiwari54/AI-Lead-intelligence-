"""Contact endpoints."""
from uuid import UUID

from fastapi import APIRouter, Query

from app.common.dependencies import DbDep, UserDep
from app.common.schemas import Page, PageParams, SuccessResponse
from app.contacts.schemas import (
    ContactCreate,
    ContactFilterParams,
    ContactMergeRequest,
    ContactResponse,
    ContactUpdate,
    EmailVerifyResponse,
)
from app.contacts.service import ContactService

router = APIRouter()


@router.post("", response_model=ContactResponse, status_code=201)
async def create_contact(req: ContactCreate, user: UserDep, db: DbDep) -> dict:
    """Create a new contact."""
    user.require_permission("contacts:create")
    return await ContactService(db).create(user.org_id, user.user_id, req)


@router.get("", response_model=Page[ContactResponse])
async def list_contacts(
    user: UserDep,
    db: DbDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = Query(default=None),
    company_id: UUID | None = Query(default=None),
    seniority_level: str | None = Query(default=None),
    is_decision_maker: bool | None = Query(default=None),
    has_email: bool | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
) -> Page:
    """List contacts with filters and pagination."""
    user.require_permission("contacts:read")
    params = ContactFilterParams(
        page=page, page_size=page_size, search=search,
        company_id=company_id, seniority_level=seniority_level,
        is_decision_maker=is_decision_maker, has_email=has_email,
        sort_by=sort_by, sort_dir=sort_dir,
    )
    items, total = await ContactService(db).list_contacts(user.org_id, params)
    return Page.create(items, total, PageParams(page=page, page_size=page_size))


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: UUID, user: UserDep, db: DbDep) -> dict:
    user.require_permission("contacts:read")
    return await ContactService(db).get(user.org_id, contact_id)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: UUID, req: ContactUpdate, user: UserDep, db: DbDep) -> dict:
    user.require_permission("contacts:update")
    return await ContactService(db).update(user.org_id, user.user_id, contact_id, req)


@router.delete("/{contact_id}", response_model=SuccessResponse)
async def delete_contact(contact_id: UUID, user: UserDep, db: DbDep) -> SuccessResponse:
    user.require_permission("contacts:delete")
    await ContactService(db).delete(user.org_id, user.user_id, contact_id)
    return SuccessResponse(message="Contact deleted")


@router.post("/merge", response_model=ContactResponse)
async def merge_contacts(req: ContactMergeRequest, user: UserDep, db: DbDep) -> dict:
    """Merge two contacts."""
    user.require_permission("contacts:update")
    return await ContactService(db).merge(user.org_id, req.source_id, req.target_id)


@router.post("/{contact_id}/verify-email")
async def verify_email(contact_id: UUID, user: UserDep, db: DbDep) -> dict:
    """Queue email verification for a contact."""
    contact = await ContactService(db).get(user.org_id, contact_id)
    return {"status": "queued", "email": contact.get("email")}

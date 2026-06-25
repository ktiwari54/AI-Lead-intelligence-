import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from backend.database import get_db
from backend.app.common.response import APIResponse
from backend.app.common.deps import get_current_org_id

router = APIRouter()


class EmailVerifyRequest(BaseModel):
    emails: list[EmailStr]
    contact_id: uuid.UUID | None = None


class EnrichContactRequest(BaseModel):
    contact_id: uuid.UUID


class EnrichCompanyRequest(BaseModel):
    company_id: uuid.UUID


@router.post("/email/verify", response_model=APIResponse)
async def verify_emails(
    request: EmailVerifyRequest,
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    from backend.workers.tasks.enrichment import verify_emails_task
    verify_emails_task.delay(request.emails, str(org_id), str(request.contact_id) if request.contact_id else None)
    return APIResponse(message=f"{len(request.emails)} email(s) queued for verification")


@router.post("/contact", response_model=APIResponse)
async def enrich_contact(
    request: EnrichContactRequest,
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    from backend.workers.tasks.enrichment import enrich_contact_task
    enrich_contact_task.delay(str(request.contact_id), str(org_id))
    return APIResponse(message="Contact enrichment queued")


@router.post("/company", response_model=APIResponse)
async def enrich_company(
    request: EnrichCompanyRequest,
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    from backend.workers.tasks.enrichment import enrich_company_task
    enrich_company_task.delay(str(request.company_id), str(org_id))
    return APIResponse(message="Company enrichment queued")

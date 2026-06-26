from __future__ import annotations
import uuid
from urllib.parse import unquote

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.enrichment.schemas import (
    BulkVerifyRequest,
    EmailVerificationResponse,
    EnrichCompanyRequest,
    EnrichContactRequest,
    EnrichmentTaskResponse,
    VerifyEmailRequest,
)
from backend.app.enrichment.service import EnrichmentService
from backend.app.common.deps import get_current_user_id, get_current_org_id
from backend.app.common.pagination import PaginationParams, pagination_params
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.exceptions import NotFoundError

router = APIRouter()

enrichment_service = EnrichmentService()


@router.post("/email/verify", response_model=APIResponse, status_code=status.HTTP_202_ACCEPTED)
async def verify_email(
    body: VerifyEmailRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    from backend.workers.tasks.enrichment import verify_emails_task

    verification = await enrichment_service.verify_email(db, org_id, body)
    await db.commit()

    task = verify_emails_task.delay(
        body.email,
        str(body.contact_id) if body.contact_id else None,
    )
    result = EnrichmentTaskResponse(
        task_id=task.id,
        status="queued",
        entity_id=body.email,
        entity_type="email",
    )
    return APIResponse(data=result.model_dump(), message="Email verification queued")


@router.post("/email/bulk-verify", response_model=APIResponse, status_code=status.HTTP_202_ACCEPTED)
async def bulk_verify_emails(
    body: BulkVerifyRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
) -> APIResponse:
    from backend.workers.tasks.enrichment import verify_emails_task

    task_ids: list[str] = []
    for idx, email in enumerate(body.emails):
        contact_id: uuid.UUID | None = None
        if body.contact_ids and idx < len(body.contact_ids):
            contact_id = body.contact_ids[idx]
        task = verify_emails_task.delay(email, str(contact_id) if contact_id else None)
        task_ids.append(task.id)

    return APIResponse(
        data={"task_ids": task_ids, "queued": len(task_ids)},
        message=f"{len(task_ids)} email(s) queued for verification",
    )


@router.get("/email/{email:path}", response_model=APIResponse)
async def get_email_verification(
    email: str,
    _: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    email = unquote(email)
    verification = await enrichment_service.get_verification(db, email)
    if not verification:
        raise NotFoundError(f"No verification found for {email}")
    return APIResponse(data=EmailVerificationResponse.model_validate(verification).model_dump())


@router.get("/contact/{contact_id}/verifications", response_model=PaginatedResponse)
async def list_contact_verifications(
    contact_id: uuid.UUID,
    pagination: PaginationParams = Depends(pagination_params),
    _: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    items, total = await enrichment_service.list_verifications(
        db, contact_id, page=pagination.page, page_size=pagination.per_page
    )
    data = [EmailVerificationResponse.model_validate(i).model_dump() for i in items]
    return PaginatedResponse.create(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.post("/contact/enrich", response_model=APIResponse, status_code=status.HTTP_202_ACCEPTED)
async def enrich_contact(
    body: EnrichContactRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    from backend.workers.tasks.enrichment import enrich_contact_task

    await enrichment_service.enrich_contact(db, org_id, body)
    await db.commit()

    task = enrich_contact_task.delay(str(body.contact_id), str(org_id), body.provider)
    result = EnrichmentTaskResponse(
        task_id=task.id,
        status="queued",
        entity_id=str(body.contact_id),
        entity_type="contact",
    )
    return APIResponse(data=result.model_dump(), message="Contact enrichment queued")


@router.post("/company/enrich", response_model=APIResponse, status_code=status.HTTP_202_ACCEPTED)
async def enrich_company(
    body: EnrichCompanyRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    from backend.workers.tasks.enrichment import enrich_company_task

    await enrichment_service.enrich_company(db, org_id, body)
    await db.commit()

    task = enrich_company_task.delay(str(body.company_id), str(org_id), body.provider)
    result = EnrichmentTaskResponse(
        task_id=task.id,
        status="queued",
        entity_id=str(body.company_id),
        entity_type="company",
    )
    return APIResponse(data=result.model_dump(), message="Company enrichment queued")

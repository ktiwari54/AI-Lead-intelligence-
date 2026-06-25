import uuid
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.app.ai.models import LeadScore
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.deps import get_current_org_id

router = APIRouter()


@router.post("/score/contact/{contact_id}", response_model=APIResponse)
async def score_contact(
    contact_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    from backend.workers.tasks.scoring import score_contact_task
    score_contact_task.delay(str(contact_id), str(org_id))
    return APIResponse(message="Scoring job queued")


@router.post("/score/company/{company_id}", response_model=APIResponse)
async def score_company(
    company_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    org_id: uuid.UUID = Depends(get_current_org_id),
):
    from backend.workers.tasks.scoring import score_company_task
    score_company_task.delay(str(company_id), str(org_id))
    return APIResponse(message="Scoring job queued")


@router.get("/scores/contact/{contact_id}", response_model=APIResponse)
async def get_contact_score(
    contact_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LeadScore)
        .where(LeadScore.contact_id == contact_id, LeadScore.organization_id == org_id)
        .order_by(LeadScore.created_at.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        return APIResponse(data=None, message="No score available")
    return APIResponse(data=score.to_dict())

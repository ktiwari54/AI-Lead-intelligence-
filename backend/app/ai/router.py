from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.schemas import BulkScoreRequest, LeadScoreResponse, ScoreRequest
from backend.app.ai.service import AIService
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.database import get_db
from backend.workers.tasks.scoring import score_contact_task, score_company_task

router = APIRouter(prefix="/ai", tags=["AI Scoring"])


@router.post("/score/contact/{contact_id}", response_model=LeadScoreResponse)
async def score_contact(
    contact_id: UUID,
    body: ScoreRequest = ScoreRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService()
    lead_score = await service.score_contact(
        db, current_user.organization_id, contact_id, body.icp_profile
    )
    return lead_score


@router.post("/score/company/{company_id}", response_model=LeadScoreResponse)
async def score_company(
    company_id: UUID,
    body: ScoreRequest = ScoreRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService()
    lead_score = await service.score_company(
        db, current_user.organization_id, company_id, body.icp_profile
    )
    return lead_score


@router.get("/scores/contact/{contact_id}", response_model=list[LeadScoreResponse])
async def get_contact_scores(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService()
    return await service.get_contact_scores(db, current_user.organization_id, contact_id)


@router.get("/scores/company/{company_id}", response_model=list[LeadScoreResponse])
async def get_company_scores(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AIService()
    return await service.get_company_scores(db, current_user.organization_id, company_id)


@router.post("/score/bulk")
async def bulk_score(
    body: BulkScoreRequest,
    current_user: User = Depends(get_current_user),
):
    task_ids = []
    org_id = str(current_user.organization_id)

    for contact_id in body.contact_ids or []:
        task = score_contact_task.delay(str(contact_id), org_id, body.icp_profile)
        task_ids.append(task.id)

    for company_id in body.company_ids or []:
        task = score_company_task.delay(str(company_id), org_id, body.icp_profile)
        task_ids.append(task.id)

    return {"task_ids": task_ids}

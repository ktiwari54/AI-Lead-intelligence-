"""AI module router: scoring + vector semantic search."""
from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.schemas import BulkScoreRequest, LeadScoreResponse, ScoreRequest
from backend.app.ai.service import AIService
from backend.app.ai.vector_search import (
    find_similar_companies,
    find_similar_contacts,
    semantic_search_companies,
    semantic_search_contacts,
)
from backend.app.common.deps import get_current_user, get_db
from backend.app.common.response import APIResponse
from backend.app.users.models import User

router = APIRouter(prefix="/ai", tags=["AI Scoring"])
_service = AIService()


# ─── Scoring endpoints ────────────────────────────────────────────────────────────────────────────────

@router.post("/score/contact/{contact_id}", response_model=APIResponse[LeadScoreResponse])
async def score_contact(
    contact_id: UUID,
    body: ScoreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    score = await _service.score_contact(db, current_user.organization_id, contact_id, body.icp_profile)
    return APIResponse(data=LeadScoreResponse.model_validate(score))


@router.post("/score/company/{company_id}", response_model=APIResponse[LeadScoreResponse])
async def score_company(
    company_id: UUID,
    body: ScoreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    score = await _service.score_company(db, current_user.organization_id, company_id, body.icp_profile)
    return APIResponse(data=LeadScoreResponse.model_validate(score))


@router.get("/scores/contact/{contact_id}", response_model=APIResponse[list[LeadScoreResponse]])
async def get_contact_scores(
    contact_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scores = await _service.get_contact_scores(db, current_user.organization_id, contact_id)
    return APIResponse(data=[LeadScoreResponse.model_validate(s) for s in scores])


@router.get("/scores/company/{company_id}", response_model=APIResponse[list[LeadScoreResponse]])
async def get_company_scores(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scores = await _service.get_company_scores(db, current_user.organization_id, company_id)
    return APIResponse(data=[LeadScoreResponse.model_validate(s) for s in scores])


@router.post("/score/bulk")
async def bulk_score(
    body: BulkScoreRequest,
    current_user: User = Depends(get_current_user),
):
    from backend.workers.tasks.scoring import score_contact_task, score_company_task
    task_ids = []
    for cid in (body.contact_ids or []):
        t = score_contact_task.delay(str(cid), str(current_user.organization_id), body.icp_profile)
        task_ids.append(t.id)
    for cid in (body.company_ids or []):
        t = score_company_task.delay(str(cid), str(current_user.organization_id), body.icp_profile)
        task_ids.append(t.id)
    return {"task_ids": task_ids, "queued": len(task_ids)}


# ─── Vector search endpoints ──────────────────────────────────────────────────────────────────────────

@router.get("/search/companies")
async def vector_search_companies(
    q: str = Query(..., min_length=1, description="Natural language search query"),
    limit: int = Query(20, ge=1, le=100),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic company search using vector embeddings."""
    results = await semantic_search_companies(
        db, current_user.organization_id, q, limit, min_similarity
    )
    return APIResponse(data={
        "query": q,
        "results": [{"id": str(r.id), "entity_type": r.entity_type, "similarity": r.similarity, "data": r.data} for r in results],
        "total": len(results),
        "embedding_model": "text-embedding-3-small",
    })


@router.get("/search/contacts")
async def vector_search_contacts(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Semantic contact search using vector embeddings."""
    results = await semantic_search_contacts(
        db, current_user.organization_id, q, limit, min_similarity
    )
    return APIResponse(data={
        "query": q,
        "results": [{"id": str(r.id), "entity_type": r.entity_type, "similarity": r.similarity, "data": r.data} for r in results],
        "total": len(results),
        "embedding_model": "text-embedding-3-small",
    })


@router.get("/similar/companies/{company_id}")
async def similar_companies(
    company_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Find companies similar to a given company (More Like This)."""
    results = await find_similar_companies(db, current_user.organization_id, company_id, limit)
    return APIResponse(data={"results": [{"id": str(r.id), "similarity": r.similarity, "data": r.data} for r in results], "total": len(results)})


@router.get("/similar/contacts/{contact_id}")
async def similar_contacts(
    contact_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Find contacts similar to a given contact."""
    results = await find_similar_contacts(db, current_user.organization_id, contact_id, limit)
    return APIResponse(data={"results": [{"id": str(r.id), "similarity": r.similarity, "data": r.data} for r in results], "total": len(results)})

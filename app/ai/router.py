"""AI service endpoints."""
from uuid import UUID

from fastapi import APIRouter

from app.common.dependencies import DbDep, UserDep
from app.ai.schemas import (
    BulkScoreRequest,
    DuplicateCheckRequest,
    LeadScoreRequest,
    LeadScoreResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.ai.service import AIService

router = APIRouter()


@router.post("/score", response_model=LeadScoreResponse)
async def score_lead(req: LeadScoreRequest, user: UserDep, db: DbDep) -> LeadScoreResponse:
    """Score a company or contact as a sales lead."""
    user.require_permission("ai_scores:create")
    return await AIService(db).score_lead(user.org_id, req.entity_type, req.entity_id, req.force_refresh)


@router.post("/score/bulk")
async def bulk_score(req: BulkScoreRequest, user: UserDep, db: DbDep) -> dict:
    """Queue bulk lead scoring for multiple entities."""
    user.require_permission("ai_scores:create")
    from workers.tasks.ai import bulk_score_task
    task = bulk_score_task.delay(str(user.org_id), req.entity_type, [str(i) for i in req.entity_ids])
    return {"job_id": task.id, "entity_count": len(req.entity_ids), "status": "queued"}


@router.get("/score/{entity_type}/{entity_id}", response_model=LeadScoreResponse)
async def get_score(entity_type: str, entity_id: UUID, user: UserDep, db: DbDep) -> LeadScoreResponse:
    """Get existing lead score for an entity."""
    user.require_permission("ai_scores:read")
    return await AIService(db).score_lead(user.org_id, entity_type, entity_id, force_refresh=False)


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(req: RecommendationRequest, user: UserDep, db: DbDep) -> RecommendationResponse:
    """Get similar entity recommendations based on vector similarity."""
    user.require_permission("ai_scores:read")
    return await AIService(db).get_recommendations(user.org_id, req.entity_type, req.seed_entity_id, req.limit)


@router.post("/duplicates")
async def find_duplicates(req: DuplicateCheckRequest, user: UserDep, db: DbDep) -> list:
    """Find potential duplicate entities using vector similarity."""
    user.require_permission("companies:read")
    return await AIService(db).find_duplicates(user.org_id, req.entity_type, req.entity_id, req.threshold)


@router.post("/embed/{entity_type}/{entity_id}")
async def generate_embedding(entity_type: str, entity_id: UUID, user: UserDep, db: DbDep) -> dict:
    """Generate and store vector embedding for an entity."""
    from sqlalchemy import text
    table = "core.companies" if entity_type == "company" else "core.contacts"
    name_col = "name" if entity_type == "company" else "full_name"
    result = await db.execute(
        text(f"SELECT {name_col}, description FROM {table} WHERE id = :id AND organization_id = :oid"),
        {"id": entity_id, "oid": user.org_id},
    )
    row = result.fetchone()
    if not row:
        from app.core.exceptions import NotFoundError
        raise NotFoundError()
    text_content = f"{row[0]} {row[1] or ''}"
    await AIService(db).generate_embeddings(user.org_id, entity_type, entity_id, text_content)
    return {"status": "embedded", "entity_id": str(entity_id)}

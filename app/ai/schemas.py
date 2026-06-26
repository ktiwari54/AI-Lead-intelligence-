"""AI service schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.common.schemas import BaseSchema


class LeadScoreRequest(BaseSchema):
    entity_type: str = Field(pattern="^(company|contact)$")
    entity_id: UUID
    force_refresh: bool = False


class LeadScoreResponse(BaseSchema):
    entity_type: str
    entity_id: UUID
    overall_score: int
    quality_score: int | None = None
    fit_score: int | None = None
    intent_score: int | None = None
    engagement_score: int | None = None
    timing_score: int | None = None
    recommendation: str
    score_reasons: list[str] = []
    model_id: str
    scored_at: datetime


class BulkScoreRequest(BaseSchema):
    entity_type: str = Field(pattern="^(company|contact)$")
    entity_ids: list[UUID] = Field(min_length=1, max_length=100)


class RecommendationRequest(BaseSchema):
    entity_type: str = Field(pattern="^(company|contact)$")
    seed_entity_id: UUID
    limit: int = Field(default=10, ge=1, le=50)


class RecommendationResponse(BaseSchema):
    seed_entity_id: UUID
    recommendations: list[dict]
    model_id: str


class DuplicateCheckRequest(BaseSchema):
    entity_type: str = Field(pattern="^(company|contact)$")
    entity_id: UUID
    threshold: float = Field(default=0.85, ge=0.0, le=1.0)


class CompanySummaryRequest(BaseSchema):
    company_id: UUID

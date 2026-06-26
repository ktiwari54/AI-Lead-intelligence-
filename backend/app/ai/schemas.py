from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    reasoning: str
    strengths: list[str]
    weaknesses: list[str]
    recommendation: Literal["HOT", "WARM", "COLD", "DISQUALIFIED"]


class LeadScoreResponse(BaseModel):
    id: UUID
    contact_id: UUID | None = None
    company_id: UUID | None = None
    overall_score: float
    seniority_score: float
    company_score: float
    engagement_score: float
    technology_score: float
    industry_score: float
    fit_score: float
    score_breakdown: ScoreBreakdown
    model_used: str
    created_at: datetime

    class Config:
        from_attributes = True


class ScoreRequest(BaseModel):
    icp_profile: dict | None = None


class BulkScoreRequest(BaseModel):
    contact_ids: list[UUID] | None = None
    company_ids: list[UUID] | None = None
    icp_profile: dict | None = None

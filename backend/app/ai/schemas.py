from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID


class ScoreRequest(BaseModel):
    contact_id: Optional[UUID] = None
    company_id: Optional[UUID] = None


class ScoreResponse(BaseModel):
    overall_score: float
    industry_score: float
    company_score: float
    engagement_score: float
    technology_score: float
    fit_score: float
    grade: str
    scoring_reasons: List[str]


class NLQueryRequest(BaseModel):
    query: str


class NLQueryResponse(BaseModel):
    interpreted_filters: Dict[str, Any]
    suggested_query: str
    confidence: float

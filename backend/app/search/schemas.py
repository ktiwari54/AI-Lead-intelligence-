from __future__ import annotations
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str | None = None
    entity_type: Literal["companies", "contacts", "both"] = "both"
    industries: list[str] = []
    countries: list[str] = []
    seniority_levels: list[str] = []
    departments: list[str] = []
    technologies: list[str] = []
    min_employees: int | None = None
    max_employees: int | None = None
    min_revenue: int | None = None
    max_revenue: int | None = None
    min_score: float | None = None
    email_status: str | None = None
    has_phone: bool | None = None
    has_linkedin: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort_by: str = "overall_score"
    sort_order: Literal["asc", "desc"] = "desc"


class SearchHitResponse(BaseModel):
    id: UUID
    entity_type: str
    score: float
    data: dict
    highlight: dict = {}


class SearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    hits: list[SearchHitResponse]
    took_ms: int
    aggregations: dict = {}


class SavedSearchCreate(BaseModel):
    name: str
    description: str | None = None
    filters: dict


class SavedSearchResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    filters: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SearchHistoryResponse(BaseModel):
    id: UUID
    filters: dict
    result_count: int | None
    created_at: datetime

    class Config:
        from_attributes = True

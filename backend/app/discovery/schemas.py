from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DiscoveryRequest(BaseModel):
    query: str | None = None
    entity_type: Literal["company", "contact", "both"] = "both"
    filters: dict[str, Any] = Field(default_factory=dict)
    connectors: list[str] | None = None
    enrich: bool = True
    verify_contacts: bool = False
    schedule_id: UUID | None = None


class DiscoveryJobResponse(BaseModel):
    id: UUID
    status: Literal["pending", "running", "completed", "failed", "partial"]
    query: str | None
    entity_type: str
    connectors_used: list[str]
    result_count: int | None = None
    credits_used: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    stages: dict[str, str] = Field(default_factory=dict)
    progress_pct: int = 0


class DiscoveryResultHit(BaseModel):
    id: UUID
    entity_type: Literal["company", "contact"]
    confidence: float
    source_trust: float
    field_completeness: float
    verification_status: str | None = None
    data: dict[str, Any]
    provenance: list[dict[str, Any]] = Field(default_factory=list)
    explanation: dict[str, Any] = Field(default_factory=dict)


class DiscoveryResultResponse(BaseModel):
    job_id: UUID
    total: int
    hits: list[DiscoveryResultHit]
    took_ms: int
    connectors: list[dict[str, Any]] = Field(default_factory=list)


class ConfidenceExplanation(BaseModel):
    overall: float
    source_trust: float
    field_completeness: float
    cross_source_validation: float
    recency: float
    verification_status: float
    normalization_quality: float
    duplicate_resolution: float
    factors: list[dict[str, Any]] = Field(default_factory=list)
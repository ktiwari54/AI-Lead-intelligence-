from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr


class EmailVerificationResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    contact_id: UUID | None = None
    email: str
    is_deliverable: bool | None = None
    is_role_address: bool | None = None
    is_disposable: bool | None = None
    is_catch_all: bool | None = None
    smtp_check: bool | None = None
    confidence: float | None = None
    provider: str | None = None
    created_at: datetime


class VerifyEmailRequest(BaseModel):
    email: str
    contact_id: UUID | None = None


class BulkVerifyRequest(BaseModel):
    emails: list[str]
    contact_ids: list[UUID] | None = None


class EnrichContactRequest(BaseModel):
    contact_id: UUID
    provider: str = "hunter"  # hunter, apollo, clearbit


class EnrichCompanyRequest(BaseModel):
    company_id: UUID
    provider: str = "clearbit"


class EnrichmentTaskResponse(BaseModel):
    task_id: str
    status: str = "queued"
    entity_id: str
    entity_type: str

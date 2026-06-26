"""Contact schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.common.schemas import BaseSchema, TimestampSchema


class ContactCreate(BaseSchema):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    seniority_level: str | None = None
    department: str | None = None
    company_id: UUID | None = None
    linkedin_url: str | None = None
    location_city: str | None = None
    location_country: str | None = Field(default=None, min_length=2, max_length=2)
    is_decision_maker: bool = False
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ContactUpdate(BaseSchema):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    seniority_level: str | None = None
    department: str | None = None
    company_id: UUID | None = None
    linkedin_url: str | None = None
    is_decision_maker: bool | None = None
    opt_out_email: bool | None = None
    tags: list[str] | None = None
    metadata: dict | None = None


class ContactResponse(TimestampSchema):
    id: UUID
    organization_id: UUID
    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    seniority_level: str | None = None
    department: str | None = None
    company_id: UUID | None = None
    linkedin_url: str | None = None
    location_city: str | None = None
    location_country: str | None = None
    is_decision_maker: bool = False
    opt_out_email: bool = False
    is_verified: bool = False
    enrichment_status: str = "pending"
    lead_score: int | None = None
    tags: list[str] = []
    avatar_url: str | None = None
    status: str


class ContactFilterParams(BaseSchema):
    search: str | None = None
    company_id: UUID | None = None
    seniority_level: str | None = None
    department: str | None = None
    location_country: str | None = None
    is_decision_maker: bool | None = None
    has_email: bool | None = None
    has_phone: bool | None = None
    tags: list[str] | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort_by: str = "created_at"
    sort_dir: str = "desc"


class EmailVerifyResponse(BaseSchema):
    email: str
    is_valid: bool
    is_deliverable: bool | None = None
    is_disposable: bool | None = None
    is_role_account: bool | None = None
    mx_found: bool | None = None
    provider: str
    checked_at: datetime


class ContactMergeRequest(BaseSchema):
    source_id: UUID
    target_id: UUID

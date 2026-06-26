"""Company schemas."""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, HttpUrl, field_validator

from app.common.schemas import BaseSchema, TimestampSchema


class CompanyCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=500)
    domain: str | None = None
    website: str | None = None
    industry_id: UUID | None = None
    industry_name: str | None = None
    description: str | None = None
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    employee_count: int | None = Field(default=None, ge=0)
    annual_revenue: Decimal | None = Field(default=None, ge=0)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    city: str | None = None
    state: str | None = None
    linkedin_url: str | None = None
    phone: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class CompanyUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=500)
    domain: str | None = None
    website: str | None = None
    industry_id: UUID | None = None
    industry_name: str | None = None
    description: str | None = None
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    employee_count: int | None = Field(default=None, ge=0)
    annual_revenue: Decimal | None = Field(default=None, ge=0)
    country_code: str | None = None
    city: str | None = None
    state: str | None = None
    linkedin_url: str | None = None
    phone: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None


class CompanyResponse(TimestampSchema):
    id: UUID
    organization_id: UUID
    name: str
    domain: str | None = None
    website: str | None = None
    industry_name: str | None = None
    description: str | None = None
    founded_year: int | None = None
    employee_count: int | None = None
    employee_range: str | None = None
    annual_revenue: Decimal | None = None
    country_code: str | None = None
    city: str | None = None
    state: str | None = None
    linkedin_url: str | None = None
    phone: str | None = None
    logo_url: str | None = None
    is_public: bool = False
    is_verified: bool = False
    enrichment_status: str = "pending"
    data_confidence: int | None = None
    tags: list[str] = []
    lead_score: int | None = None
    status: str


class CompanyBulkCreate(BaseSchema):
    companies: list[CompanyCreate] = Field(min_length=1, max_length=500)


class CompanyMergeRequest(BaseSchema):
    source_id: UUID
    target_id: UUID
    fields_to_keep: dict[str, str] = Field(default_factory=dict)


class CompanyFilterParams(BaseSchema):
    industry: str | None = None
    country_code: str | None = None
    employee_min: int | None = None
    employee_max: int | None = None
    revenue_min: Decimal | None = None
    revenue_max: Decimal | None = None
    technology: str | None = None
    is_public: bool | None = None
    enrichment_status: str | None = None
    tags: list[str] | None = None
    lat: float | None = None
    lon: float | None = None
    radius_km: float | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort_by: str = "created_at"
    sort_dir: str = "desc"
    search: str | None = None


class CompanySummaryResponse(BaseSchema):
    company_id: UUID
    summary: str
    key_facts: list[str]
    strengths: list[str]
    risks: list[str]
    generated_at: datetime

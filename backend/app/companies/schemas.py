import uuid
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class CompanyCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=500)
    legal_name: str | None = None
    website: str | None = None
    domain: str | None = None
    industry_id: uuid.UUID | None = None
    country_id: uuid.UUID | None = None
    state_id: uuid.UUID | None = None
    city_id: uuid.UUID | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    employee_count: int | None = None
    employee_range: str | None = None
    revenue: float | None = None
    revenue_range: str | None = None
    ownership_type: str | None = None
    founded_year: int | None = None
    description: str | None = None


class CompanyUpdate(CompanyCreate):
    company_name: str | None = None


class CompanySocialProfileResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    platform: str
    profile_url: str
    handle: str | None


class CompanyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    organization_id: uuid.UUID
    company_name: str
    legal_name: str | None
    website: str | None
    domain: str | None
    industry_id: uuid.UUID | None
    country_id: uuid.UUID | None
    state_id: uuid.UUID | None
    city_id: uuid.UUID | None
    address: str | None
    employee_count: int | None
    employee_range: str | None
    revenue: float | None
    revenue_range: str | None
    ownership_type: str | None
    founded_year: int | None
    description: str | None
    logo_url: str | None
    confidence_score: float | None
    enrichment_status: str
    created_at: datetime
    updated_at: datetime


class CompanyFilter(BaseModel):
    query: str | None = None
    industry_id: uuid.UUID | None = None
    country_id: uuid.UUID | None = None
    employee_range: str | None = None
    revenue_range: str | None = None
    technology_ids: list[uuid.UUID] | None = None

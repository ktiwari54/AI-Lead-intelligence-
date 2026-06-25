import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class ContactCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=200)
    last_name: str | None = None
    company_id: uuid.UUID | None = None
    designation: str | None = None
    department: str | None = None
    seniority: str | None = None
    email: str | None = None
    phone: str | None = None
    country_id: uuid.UUID | None = None
    city_id: uuid.UUID | None = None
    linkedin_url: str | None = None


class ContactUpdate(ContactCreate):
    first_name: str | None = None


class ContactResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    organization_id: uuid.UUID
    company_id: uuid.UUID | None
    first_name: str
    last_name: str | None
    designation: str | None
    department: str | None
    seniority: str | None
    email: str | None
    email_status: str
    phone: str | None
    phone_status: str
    country_id: uuid.UUID | None
    city_id: uuid.UUID | None
    linkedin_url: str | None
    confidence_score: float | None
    enrichment_status: str
    created_at: datetime
    updated_at: datetime


class ContactFilter(BaseModel):
    query: str | None = None
    company_id: uuid.UUID | None = None
    country_id: uuid.UUID | None = None
    designation: str | None = None
    department: str | None = None
    seniority: str | None = None
    email_status: str | None = None

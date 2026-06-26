import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    website: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    website: str | None = None
    logo_url: str | None = None
    settings: dict | None = None


class OrganizationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    status: str
    subscription_plan: str
    credits: int
    logo_url: str | None
    website: str | None
    created_at: datetime

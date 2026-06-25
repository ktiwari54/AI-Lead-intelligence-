from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    subscription_plan: str
    credits: int
    website: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None

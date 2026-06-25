from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class SocialProfileOut(BaseModel):
    id: UUID
    platform: str
    profile_url: str
    handle: Optional[str] = None
    model_config = {"from_attributes": True}


class ContactBase(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    designation: Optional[str] = None
    seniority: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_type: Optional[str] = None
    company_id: Optional[UUID] = None
    country_id: Optional[UUID] = None
    city_id: Optional[UUID] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    first_name: Optional[str] = None


class ContactOut(ContactBase):
    id: UUID
    organization_id: UUID
    full_name: Optional[str] = None
    email_status: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    is_decision_maker: bool = False
    social_profiles: List[SocialProfileOut] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ContactListOut(BaseModel):
    items: List[ContactOut]
    total: int
    page: int
    page_size: int

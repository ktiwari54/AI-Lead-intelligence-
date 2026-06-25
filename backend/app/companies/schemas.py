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


class CompanyBase(BaseModel):
    company_name: str
    legal_name: Optional[str] = None
    website: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    revenue: Optional[Decimal] = None
    revenue_range: Optional[str] = None
    ownership_type: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    industry_id: Optional[UUID] = None
    country_id: Optional[UUID] = None
    state_id: Optional[UUID] = None
    city_id: Optional[UUID] = None
    address: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    company_name: Optional[str] = None


class CompanyOut(CompanyBase):
    id: UUID
    organization_id: UUID
    confidence_score: Optional[Decimal] = None
    social_profiles: List[SocialProfileOut] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CompanyListOut(BaseModel):
    items: List[CompanyOut]
    total: int
    page: int
    page_size: int

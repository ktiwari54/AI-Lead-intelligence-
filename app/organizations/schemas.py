"""Organization schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.common.schemas import BaseSchema, TimestampSchema


class OrgCreate(BaseSchema):
    name: str = Field(min_length=2, max_length=200)
    website: str | None = None
    industry: str | None = None
    size: str | None = None


class OrgUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    website: str | None = None
    industry: str | None = None
    logo_url: str | None = None
    size: str | None = None


class OrgResponse(TimestampSchema):
    id: UUID
    name: str
    slug: str
    website: str | None = None
    industry: str | None = None
    logo_url: str | None = None
    credits_balance: int
    status: str
    plan_id: UUID | None = None


class OrgSettingUpdate(BaseSchema):
    key: str
    value: str


class OrgUsageResponse(BaseSchema):
    period_year: int
    period_month: int
    credits_used: int
    searches: int
    exports: int
    enrichments: int
    api_calls: int


class InviteUserRequest(BaseSchema):
    email: EmailStr
    role: str = "member"
    first_name: str | None = None
    last_name: str | None = None

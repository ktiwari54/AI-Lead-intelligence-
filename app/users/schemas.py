"""User schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.common.schemas import BaseSchema, TimestampSchema, Page


class UserResponse(TimestampSchema):
    id: UUID
    email: str
    first_name: str
    last_name: str
    organization_id: UUID
    is_email_verified: bool
    two_factor_enabled: bool
    status: str
    avatar_url: str | None = None
    roles: list[str] = []


class UserUpdate(BaseSchema):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_url: str | None = None
    timezone: str | None = None
    language: str | None = None


class UserListParams(BaseSchema):
    page: int = 1
    page_size: int = 25
    search: str | None = None
    status: str | None = None
    role: str | None = None


class AssignRoleRequest(BaseSchema):
    role_slug: str


class RoleResponse(BaseSchema):
    id: UUID
    name: str
    slug: str
    level: int
    is_system: bool

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    timezone: str = "UTC"
    language: str = "en"


class UserUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    timezone: str | None = None
    language: str | None = None
    avatar_url: str | None = None


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    organization_id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    status: str
    timezone: str
    language: str
    last_login: datetime | None
    avatar_url: str | None
    created_at: datetime

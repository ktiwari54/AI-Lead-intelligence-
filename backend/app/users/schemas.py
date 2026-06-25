from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserOut(BaseModel):
    id: UUID
    organization_id: UUID
    first_name: str
    last_name: str
    email: str
    status: str
    timezone: str
    language: str
    last_login: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

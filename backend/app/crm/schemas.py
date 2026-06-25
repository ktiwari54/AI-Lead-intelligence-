from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ActivityCreate(BaseModel):
    contact_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    activity_type: str
    description: Optional[str] = None
    occurred_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    outcome: Optional[str] = None


class ActivityOut(ActivityCreate):
    id: UUID
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class NoteCreate(BaseModel):
    contact_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    note: str
    is_pinned: bool = False


class NoteOut(NoteCreate):
    id: UUID
    organization_id: UUID
    created_by: UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str
    color: Optional[str] = None


class TagOut(TagCreate):
    id: UUID
    organization_id: UUID
    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    contact_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    assigned_to: Optional[UUID] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None


class TaskOut(TaskCreate):
    id: UUID
    organization_id: UUID
    created_by: UUID
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}

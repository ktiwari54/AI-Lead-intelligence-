from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class NotificationOut(BaseModel):
    id: UUID
    type: str
    title: str
    body: Optional[str] = None
    status: str
    channel: str
    read_at: Optional[datetime] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    items: List[NotificationOut]
    total: int
    unread_count: int

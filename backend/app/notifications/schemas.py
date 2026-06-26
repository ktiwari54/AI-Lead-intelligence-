from __future__ import annotations
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    channel: str
    type: str
    title: str
    message: str
    status: str
    read_at: datetime | None = None
    metadata: dict = {}
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: UUID
    channel: Literal["EMAIL", "IN_APP", "WEBHOOK", "SLACK"] = "IN_APP"
    type: str
    title: str
    message: str
    metadata: dict = {}


class MarkReadRequest(BaseModel):
    notification_ids: list[UUID]


class UnreadCountResponse(BaseModel):
    unread_count: int

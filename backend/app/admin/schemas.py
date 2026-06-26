from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    organization_id: UUID
    user_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    old_values: dict | None = None
    new_values: dict | None = None
    ip_address: str | None = None
    created_at: datetime


class SystemSettingResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    key: str
    value: Any
    description: str | None = None
    is_public: bool
    is_editable: bool
    updated_at: datetime


class SystemSettingUpdate(BaseModel):
    value: Any
    description: str | None = None


class FeatureFlagResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    key: str
    name: str
    description: str | None = None
    is_enabled: bool
    rollout_percentage: int
    allowed_org_ids: list[str] = []
    updated_at: datetime


class FeatureFlagUpdate(BaseModel):
    is_enabled: bool | None = None
    rollout_percentage: int | None = None
    allowed_org_ids: list[str] | None = None


class AdminStatsResponse(BaseModel):
    total_organizations: int
    total_users: int
    total_companies: int
    total_contacts: int
    total_searches_today: int
    total_exports_pending: int

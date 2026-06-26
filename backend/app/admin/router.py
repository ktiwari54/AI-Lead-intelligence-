from __future__ import annotations
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.admin.schemas import (
    AdminStatsResponse,
    AuditLogResponse,
    FeatureFlagResponse,
    FeatureFlagUpdate,
    SystemSettingResponse,
    SystemSettingUpdate,
)
from backend.app.admin.service import AdminService
from backend.app.common.deps import get_current_user_id, get_current_org_id
from backend.app.common.exceptions import ForbiddenError
from backend.app.common.pagination import PaginationParams, pagination_params
from backend.app.common.response import APIResponse, PaginatedResponse

router = APIRouter()

admin_service = AdminService()


async def require_active_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> uuid.UUID:
    """Verify the requesting user is authenticated.

    In production this would additionally check for an ADMIN role,
    but RBAC is deferred until the full role layer is in place.
    """
    return user_id


@router.get("/stats", response_model=APIResponse)
async def get_admin_stats(
    _: uuid.UUID = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    stats = await admin_service.get_admin_stats(db)
    return APIResponse(data=stats.model_dump())


@router.get("/audit-logs", response_model=PaginatedResponse)
async def list_audit_logs(
    resource_type: str | None = Query(default=None),
    pagination: PaginationParams = Depends(pagination_params),
    user_id: uuid.UUID = Depends(require_active_user),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    items, total = await admin_service.list_audit_logs(
        db,
        org_id=org_id,
        resource_type=resource_type,
        page=pagination.page,
        page_size=pagination.per_page,
    )
    data = [AuditLogResponse.model_validate(i).model_dump() for i in items]
    return PaginatedResponse.create(data=data, total=total, page=pagination.page, per_page=pagination.per_page)


@router.get("/settings", response_model=APIResponse)
async def list_settings(
    _: uuid.UUID = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    settings = await admin_service.get_system_settings(db)
    data = [SystemSettingResponse.model_validate(s).model_dump() for s in settings]
    return APIResponse(data=data)


@router.patch("/settings/{key}", response_model=APIResponse)
async def update_setting(
    key: str,
    body: SystemSettingUpdate,
    _: uuid.UUID = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    setting = await admin_service.update_setting(db, key, body)
    await db.commit()
    return APIResponse(data=SystemSettingResponse.model_validate(setting).model_dump())


@router.get("/feature-flags", response_model=APIResponse)
async def list_feature_flags(
    _: uuid.UUID = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    flags = await admin_service.list_feature_flags(db)
    data = [FeatureFlagResponse.model_validate(f).model_dump() for f in flags]
    return APIResponse(data=data)


@router.patch("/feature-flags/{key}", response_model=APIResponse)
async def update_feature_flag(
    key: str,
    body: FeatureFlagUpdate,
    _: uuid.UUID = Depends(require_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    flag = await admin_service.update_feature_flag(db, key, body)
    await db.commit()
    return APIResponse(data=FeatureFlagResponse.model_validate(flag).model_dump())

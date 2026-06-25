import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.app.admin.models import AuditLog, SystemSetting, FeatureFlag
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_org_id

router = APIRouter()


@router.get("/audit-logs", response_model=PaginatedResponse)
async def list_audit_logs(
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).where(
        AuditLog.organization_id == org_id
    ).order_by(AuditLog.created_at.desc())
    count = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count.scalar()
    result = await db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
    logs = [l.to_dict() for l in result.scalars().all()]
    return PaginatedResponse.create(data=logs, total=total, page=pagination.page, per_page=pagination.per_page)


@router.get("/settings", response_model=APIResponse)
async def get_settings(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SystemSetting).where(SystemSetting.is_public == True))
    settings = {s.key: s.value for s in result.scalars().all()}
    return APIResponse(data=settings)


@router.get("/feature-flags", response_model=APIResponse)
async def get_feature_flags(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FeatureFlag).where(FeatureFlag.organization_id == org_id)
    )
    flags = {f.key: f.is_enabled for f in result.scalars().all()}
    return APIResponse(data=flags)

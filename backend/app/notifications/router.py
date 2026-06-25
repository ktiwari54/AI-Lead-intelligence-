import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from backend.database import get_db
from backend.app.notifications.models import Notification
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_user_id, get_current_org_id

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_notifications(
    pagination: PaginationParams = Depends(pagination_params),
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(
        Notification.user_id == user_id,
        Notification.organization_id == org_id,
        Notification.deleted_at.is_(None),
    ).order_by(Notification.created_at.desc())
    count = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count.scalar()
    result = await db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
    notifications = [n.to_dict() for n in result.scalars().all()]
    return PaginatedResponse.create(
        data=notifications, total=total, page=pagination.page, per_page=pagination.per_page
    )


@router.post("/{notification_id}/read", response_model=APIResponse)
async def mark_read(
    notification_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(status="read", read_at=datetime.now(timezone.utc))
    )
    return APIResponse(message="Notification marked as read")


@router.post("/read-all", response_model=APIResponse)
async def mark_all_read(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.status == "unread")
        .values(status="read", read_at=datetime.now(timezone.utc))
    )
    return APIResponse(message="All notifications marked as read")

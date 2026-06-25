from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.common.dependencies import get_current_user
from app.models.system import Notification
from app.notifications.schemas import NotificationOut, NotificationListOut

router = APIRouter()


@router.get("", response_model=NotificationListOut)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    offset = (page - 1) * page_size
    base_q = select(Notification).where(Notification.user_id == user.id, Notification.is_deleted == False)
    total = (await db.execute(select(func.count()).select_from(base_q.subquery()))).scalar()
    unread = (await db.execute(
        select(func.count()).select_from(
            select(Notification).where(Notification.user_id == user.id, Notification.status == "unread").subquery()
        )
    )).scalar()
    items = (await db.execute(base_q.order_by(Notification.created_at.desc()).offset(offset).limit(page_size))).scalars().all()
    return {"items": items, "total": total, "unread_count": unread}


@router.post("/{notification_id}/read", status_code=204)
async def mark_read(notification_id: UUID, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    notif = await db.get(Notification, notification_id)
    if notif and notif.user_id == user.id:
        notif.status = "read"
        notif.read_at = datetime.now(timezone.utc)

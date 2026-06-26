from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.notifications.models import Notification
from backend.app.notifications.schemas import NotificationCreate


class NotificationService:

    async def create(self, db: AsyncSession, org_id: UUID, data: NotificationCreate) -> Notification:
        notif = Notification(
            organization_id=org_id,
            user_id=data.user_id,
            channel=data.channel,
            type=data.type,
            title=data.title,
            message=data.message,
            status="PENDING",
            metadata=data.metadata,
        )
        db.add(notif)
        await db.flush()
        return notif

    async def list_for_user(
        self, db: AsyncSession, org_id: UUID, user_id: UUID,
        unread_only: bool = False, page: int = 1, page_size: int = 25
    ) -> tuple[list[Notification], int]:
        q = select(Notification).where(
            Notification.organization_id == org_id,
            Notification.user_id == user_id,
        )
        if unread_only:
            q = q.where(Notification.read_at.is_(None))

        total = await db.scalar(
            select(func.count()).select_from(q.subquery())
        ) or 0

        result = await db.execute(
            q.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total

    async def mark_read(
        self, db: AsyncSession, org_id: UUID, user_id: UUID, notification_ids: list[UUID]
    ) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.organization_id == org_id,
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc), status="READ")
        )
        return result.rowcount

    async def mark_all_read(self, db: AsyncSession, org_id: UUID, user_id: UUID) -> int:
        result = await db.execute(
            update(Notification)
            .where(
                Notification.organization_id == org_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc), status="READ")
        )
        return result.rowcount

    async def get_unread_count(self, db: AsyncSession, org_id: UUID, user_id: UUID) -> int:
        return await db.scalar(
            select(func.count()).select_from(Notification)
            .where(
                Notification.organization_id == org_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        ) or 0

    async def delete(self, db: AsyncSession, org_id: UUID, notification_id: UUID) -> bool:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.organization_id == org_id,
            )
        )
        notif = result.scalar_one_or_none()
        if not notif:
            return False
        await db.delete(notif)
        return True

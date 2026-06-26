from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.dependencies import get_current_user, get_db
from backend.app.common.schemas import PaginatedResponse
from backend.app.notifications.schemas import (
    MarkReadRequest,
    NotificationResponse,
    UnreadCountResponse,
)
from backend.app.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])
service = NotificationService()


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    items, total = await service.list_for_user(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[NotificationResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = await service.get_unread_count(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return UnreadCountResponse(unread_count=count)


@router.post("/mark-read")
async def mark_read(
    body: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    marked = await service.mark_read(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        notification_ids=body.notification_ids,
    )
    await db.commit()
    return {"marked": marked}


@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    marked = await service.mark_all_read(
        db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
    )
    await db.commit()
    return {"marked": marked}


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted = await service.delete(
        db,
        org_id=current_user.organization_id,
        notification_id=notification_id,
    )
    await db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")

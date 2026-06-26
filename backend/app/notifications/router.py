from __future__ import annotations
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.deps import get_current_user, get_db
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.notifications.schemas import (
    MarkReadRequest, NotificationCreate, NotificationResponse, UnreadCountResponse,
)
from backend.app.notifications.service import NotificationService
from backend.app.notifications.websocket import handle_websocket, manager
from backend.app.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])
_service = NotificationService()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket endpoint for real-time notifications.
    Connect with: ws://host/api/v1/notifications/ws?token=<jwt>
    """
    from backend.app.common.deps import get_current_user_from_token
    try:
        user = await get_current_user_from_token(token, db)
    except HTTPException:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await handle_websocket(websocket, str(user.id), str(user.organization_id))


@router.get("/ws/stats")
async def websocket_stats(current_user: User = Depends(get_current_user)):
    """Admin endpoint to see active WebSocket connections."""
    return {
        "connected_users": len(manager.get_connected_users()),
        "total_connections": manager.get_connection_count(),
    }


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notifications, total = await _service.list_for_user(
        db, current_user.organization_id, current_user.id,
        unread_only=unread_only, page=page, page_size=page_size,
    )
    items = [NotificationResponse.model_validate(n) for n in notifications]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/unread-count", response_model=APIResponse[UnreadCountResponse])
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await _service.get_unread_count(db, current_user.organization_id, current_user.id)
    return APIResponse(data=UnreadCountResponse(unread_count=count))


@router.post("/mark-read", response_model=APIResponse[dict])
async def mark_read(
    body: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    marked = await _service.mark_read(db, current_user.organization_id, current_user.id, body.notification_ids)
    return APIResponse(data={"marked": marked})


@router.post("/mark-all-read", response_model=APIResponse[dict])
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    marked = await _service.mark_all_read(db, current_user.organization_id, current_user.id)
    return APIResponse(data={"marked": marked})


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await _service.delete(db, current_user.organization_id, notification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.deps import get_current_user, get_db
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.platform import service
from backend.app.platform.schemas import (
    DeveloperAccountCreateRequest,
    OAuthAppCreateRequest,
    PluginInstallRequest,
    WebhookCreateRequest,
    WebhookTestRequest,
    WebhookUpdateRequest,
)
from backend.app.users.models import User

router = APIRouter(prefix="/platform", tags=["Platform"])


@router.get("/health", response_model=APIResponse)
async def platform_health():
    return APIResponse(data=service.platform_health())


@router.get("/capabilities", response_model=APIResponse)
async def platform_capabilities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.get_capabilities(db, current_user.organization_id)
    return APIResponse(data=data)


@router.post("/webhooks", response_model=APIResponse)
async def create_webhook(
    body: WebhookCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.create_webhook(
        db, current_user.organization_id, current_user.id, body.model_dump()
    )
    return APIResponse(data=data)


@router.get("/webhooks", response_model=PaginatedResponse)
async def list_webhooks(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_webhooks(
        db, current_user.organization_id, page=page, page_size=per_page
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/webhooks/{webhook_id}", response_model=APIResponse)
async def get_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.get_webhook(db, webhook_id, current_user.organization_id))


@router.patch("/webhooks/{webhook_id}", response_model=APIResponse)
async def update_webhook(
    webhook_id: UUID,
    body: WebhookUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.update_webhook(
        db, webhook_id, current_user.organization_id, body.model_dump(exclude_unset=True)
    )
    return APIResponse(data=data)


@router.delete("/webhooks/{webhook_id}", response_model=APIResponse)
async def delete_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_webhook(db, webhook_id, current_user.organization_id)
    return APIResponse(data={"deleted": True})


@router.post("/webhooks/{webhook_id}/test", response_model=APIResponse)
async def test_webhook(
    webhook_id: UUID,
    body: WebhookTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.test_webhook(
        db, webhook_id, current_user.organization_id, body.event_type
    )
    return APIResponse(data=data)


@router.get("/webhooks/{webhook_id}/deliveries", response_model=PaginatedResponse)
async def list_webhook_deliveries(
    webhook_id: UUID,
    status: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_deliveries(
        db, webhook_id, current_user.organization_id,
        status=status, page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.post("/oauth/apps", response_model=APIResponse)
async def create_oauth_app(
    body: OAuthAppCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.create_oauth_app(
        db, current_user.organization_id, current_user.id, body.model_dump()
    )
    return APIResponse(data=data)


@router.get("/oauth/apps", response_model=PaginatedResponse)
async def list_oauth_apps(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_oauth_apps(
        db, current_user.organization_id, page=page, page_size=per_page
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.delete("/oauth/apps/{client_id}", response_model=APIResponse)
async def revoke_oauth_app(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.revoke_oauth_app(db, client_id, current_user.organization_id)
    return APIResponse(data={"revoked": True})


@router.get("/usage", response_model=APIResponse)
async def get_usage(
    period: str = Query("30d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.get_usage(db, current_user.organization_id, period))


@router.post("/plugins/install", response_model=APIResponse)
async def install_plugin(
    body: PluginInstallRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.install_plugin(
        db, current_user.organization_id, current_user.id, body.model_dump()
    )
    return APIResponse(data=data)


@router.get("/plugins", response_model=APIResponse)
async def list_plugins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.list_plugins(db, current_user.organization_id))


@router.get("/marketplace", response_model=PaginatedResponse)
async def list_marketplace(
    item_type: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_marketplace(
        db, item_type=item_type, page=page, page_size=per_page
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.post("/developer/register", response_model=APIResponse)
async def register_developer(
    body: DeveloperAccountCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.register_developer(db, current_user, body.model_dump())
    return APIResponse(data=data)
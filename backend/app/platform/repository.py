from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.platform.models import (
    ApiUsageLog,
    DeveloperAccount,
    MarketplaceListing,
    OAuthApplication,
    PluginInstallation,
    UsageQuota,
    WebhookDelivery,
    WebhookSubscription,
)


async def get_quota(db: AsyncSession, org_id: UUID) -> UsageQuota | None:
    result = await db.execute(select(UsageQuota).where(UsageQuota.organization_id == org_id))
    return result.scalar_one_or_none()


async def ensure_quota(db: AsyncSession, org_id: UUID) -> UsageQuota:
    quota = await get_quota(db, org_id)
    if quota:
        return quota
    quota = UsageQuota(organization_id=org_id)
    db.add(quota)
    await db.flush()
    return quota


async def list_webhooks(
    db: AsyncSession, org_id: UUID, *, page: int = 1, page_size: int = 25
) -> tuple[list[WebhookSubscription], int]:
    q = select(WebhookSubscription).where(
        WebhookSubscription.organization_id == org_id,
        WebhookSubscription.deleted_at.is_(None),
    )
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(
        q.order_by(WebhookSubscription.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_webhook(db: AsyncSession, webhook_id: UUID, org_id: UUID) -> WebhookSubscription | None:
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.organization_id == org_id,
            WebhookSubscription.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_deliveries(
    db: AsyncSession,
    subscription_id: UUID,
    org_id: UUID,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[WebhookDelivery], int]:
    q = select(WebhookDelivery).where(
        WebhookDelivery.subscription_id == subscription_id,
        WebhookDelivery.organization_id == org_id,
    )
    if status:
        q = q.where(WebhookDelivery.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(
        q.order_by(WebhookDelivery.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_delivery(db: AsyncSession, delivery_id: UUID, org_id: UUID) -> WebhookDelivery | None:
    result = await db.execute(
        select(WebhookDelivery).where(
            WebhookDelivery.id == delivery_id,
            WebhookDelivery.organization_id == org_id,
        )
    )
    return result.scalar_one_or_none()


async def list_oauth_apps(
    db: AsyncSession, org_id: UUID, *, page: int = 1, page_size: int = 25
) -> tuple[list[OAuthApplication], int]:
    q = select(OAuthApplication).where(
        OAuthApplication.organization_id == org_id,
        OAuthApplication.deleted_at.is_(None),
    )
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(
        q.order_by(OAuthApplication.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_oauth_app(db: AsyncSession, client_id: str, org_id: UUID) -> OAuthApplication | None:
    result = await db.execute(
        select(OAuthApplication).where(
            OAuthApplication.client_id == client_id,
            OAuthApplication.organization_id == org_id,
            OAuthApplication.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_plugins(db: AsyncSession, org_id: UUID) -> list[PluginInstallation]:
    result = await db.execute(
        select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def get_plugin(db: AsyncSession, org_id: UUID, plugin_id: str) -> PluginInstallation | None:
    result = await db.execute(
        select(PluginInstallation).where(
            PluginInstallation.organization_id == org_id,
            PluginInstallation.plugin_id == plugin_id,
            PluginInstallation.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_marketplace(
    db: AsyncSession, *, item_type: str | None = None, page: int = 1, page_size: int = 25
) -> tuple[list[MarketplaceListing], int]:
    q = select(MarketplaceListing).where(
        MarketplaceListing.is_published == True,  # noqa: E712
        MarketplaceListing.deleted_at.is_(None),
    )
    if item_type:
        q = q.where(MarketplaceListing.item_type == item_type)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(
        q.order_by(MarketplaceListing.install_count.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_usage_summary(db: AsyncSession, org_id: UUID, days: int = 30) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.count(ApiUsageLog.id),
            func.count(ApiUsageLog.id).filter(ApiUsageLog.status_code >= 400),
            func.avg(ApiUsageLog.response_time_ms),
        ).where(
            ApiUsageLog.organization_id == org_id,
            ApiUsageLog.created_at >= since,
        )
    )
    row = result.one()
    total, errors, avg_ms = row[0] or 0, row[1] or 0, float(row[2] or 0)

    endpoint_result = await db.execute(
        select(ApiUsageLog.endpoint, func.count())
        .where(ApiUsageLog.organization_id == org_id, ApiUsageLog.created_at >= since)
        .group_by(ApiUsageLog.endpoint)
        .order_by(func.count().desc())
        .limit(20)
    )
    by_endpoint = {ep: cnt for ep, cnt in endpoint_result.all()}

    return {
        "total_requests": total,
        "error_count": errors,
        "avg_response_ms": round(avg_ms, 2),
        "by_endpoint": by_endpoint,
    }


async def get_developer_account(db: AsyncSession, user_id: UUID) -> DeveloperAccount | None:
    result = await db.execute(
        select(DeveloperAccount).where(
            DeveloperAccount.user_id == user_id,
            DeveloperAccount.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()
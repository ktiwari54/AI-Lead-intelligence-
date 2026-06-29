from __future__ import annotations

import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.api_key_auth import hash_api_key
from backend.app.platform import repository as repo
from backend.app.platform.constants import DEFAULT_SCOPES
from backend.app.platform.models import (
    DeveloperAccount,
    MarketplaceListing,
    OAuthApplication,
    PluginInstallation,
    WebhookSubscription,
)
from backend.app.platform.webhooks import deliver_webhook, generate_webhook_secret, hash_secret
from backend.app.users.models import User


def _check_platform_permission(user: User, permission: str = "platform:read") -> None:
    role_names = {r.name.lower() for r in (user.roles or [])}
    if "admin" in role_names or "owner" in role_names:
        return
    if permission == "platform:read":
        return
    if permission == "platform:write" and ("developer" in role_names or "manager" in role_names):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires {permission}")


def platform_health() -> dict:
    return {
        "status": "healthy",
        "gateway_version": "4.0",
        "subsystems": {
            "webhooks": "healthy",
            "oauth": "healthy",
            "plugins": "healthy",
            "event_bus": "healthy",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def get_capabilities(db: AsyncSession, org_id: UUID) -> dict:
    quota = await repo.ensure_quota(db, org_id)
    return {
        "api_version": "v1",
        "feature_flags": ["integration_platform_v4", "graphql_enabled"],
        "auth_methods": ["jwt", "api_key", "oauth2"],
        "available_scopes": DEFAULT_SCOPES,
        "rate_limit": {
            "limit": quota.requests_per_minute,
            "window_seconds": 60,
        },
    }


def _webhook_response(sub: WebhookSubscription, *, secret: str | None = None) -> dict:
    return {
        "id": str(sub.id),
        "url": sub.url,
        "events": sub.events,
        "description": sub.description,
        "is_active": sub.is_active,
        "failure_count": sub.failure_count,
        "last_delivery_at": sub.last_delivery_at.isoformat() if sub.last_delivery_at else None,
        "created_at": sub.created_at.isoformat(),
        "secret": secret,
    }


async def create_webhook(
    db: AsyncSession, org_id: UUID, user_id: UUID, data: dict
) -> dict:
    _check_platform_permission(await _get_user(db, user_id), "platform:write")
    quota = await repo.ensure_quota(db, org_id)
    webhooks, total = await repo.list_webhooks(db, org_id, page_size=1000)
    if total >= quota.max_webhooks:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Webhook quota exceeded")

    secret = data.get("secret") or generate_webhook_secret()
    sub = WebhookSubscription(
        organization_id=org_id,
        created_by=user_id,
        url=data["url"],
        secret_hash=hash_secret(secret),
        events=data["events"],
        description=data.get("description"),
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return _webhook_response(sub, secret=secret)


async def list_webhooks(db: AsyncSession, org_id: UUID, *, page: int, page_size: int) -> tuple[list[dict], int]:
    subs, total = await repo.list_webhooks(db, org_id, page=page, page_size=page_size)
    return [_webhook_response(s) for s in subs], total


async def get_webhook(db: AsyncSession, webhook_id: UUID, org_id: UUID) -> dict:
    sub = await repo.get_webhook(db, webhook_id, org_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return _webhook_response(sub)


async def update_webhook(db: AsyncSession, webhook_id: UUID, org_id: UUID, data: dict) -> dict:
    sub = await repo.get_webhook(db, webhook_id, org_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook not found")
    if data.get("url") is not None:
        sub.url = data["url"]
    if data.get("events") is not None:
        sub.events = data["events"]
    if data.get("description") is not None:
        sub.description = data["description"]
    if data.get("is_active") is not None:
        sub.is_active = data["is_active"]
    await db.commit()
    await db.refresh(sub)
    return _webhook_response(sub)


async def delete_webhook(db: AsyncSession, webhook_id: UUID, org_id: UUID) -> None:
    sub = await repo.get_webhook(db, webhook_id, org_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook not found")
    sub.deleted_at = datetime.now(timezone.utc)
    sub.is_active = False
    await db.commit()


async def test_webhook(
    db: AsyncSession, webhook_id: UUID, org_id: UUID, event_type: str, secret: str | None = None
) -> dict:
    sub = await repo.get_webhook(db, webhook_id, org_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook not found")
    delivery = await deliver_webhook(
        db, sub,
        event_type=event_type,
        payload={"test": True, "message": "Webhook test delivery"},
        secret=secret,
    )
    await db.commit()
    return {
        "delivery_id": str(delivery.id),
        "status": delivery.status,
        "response_status": delivery.response_status,
    }


async def list_deliveries(
    db: AsyncSession, webhook_id: UUID, org_id: UUID, *, status: str | None, page: int, page_size: int
) -> tuple[list[dict], int]:
    sub = await repo.get_webhook(db, webhook_id, org_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Webhook not found")
    deliveries, total = await repo.list_deliveries(
        db, webhook_id, org_id, status=status, page=page, page_size=page_size
    )
    return [
        {
            "id": str(d.id),
            "event_type": d.event_type,
            "status": d.status,
            "attempt_count": d.attempt_count,
            "response_status": d.response_status,
            "response_time_ms": d.response_time_ms,
            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
            "created_at": d.created_at.isoformat(),
        }
        for d in deliveries
    ], total


async def create_oauth_app(db: AsyncSession, org_id: UUID, user_id: UUID, data: dict) -> dict:
    _check_platform_permission(await _get_user(db, user_id), "platform:write")
    quota = await repo.ensure_quota(db, org_id)
    apps, total = await repo.list_oauth_apps(db, org_id, page_size=1000)
    if total >= quota.max_oauth_apps:
        raise HTTPException(status_code=429, detail="OAuth app quota exceeded")

    client_id = f"ali_app_{secrets.token_hex(8)}"
    client_secret = f"ali_sec_{secrets.token_hex(24)}"
    app = OAuthApplication(
        organization_id=org_id,
        client_id=client_id,
        client_secret_hash=hash_api_key(client_secret),
        name=data["name"],
        description=data.get("description"),
        redirect_uris=data["redirect_uris"],
        grant_types=data.get("grant_types", ["authorization_code", "refresh_token"]),
        scopes=data["scopes"],
        created_by=user_id,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return {
        "client_id": app.client_id,
        "client_secret": client_secret,
        "name": app.name,
        "redirect_uris": app.redirect_uris,
        "scopes": app.scopes,
        "grant_types": app.grant_types,
        "is_active": app.is_active,
        "created_at": app.created_at.isoformat(),
    }


async def list_oauth_apps(db: AsyncSession, org_id: UUID, *, page: int, page_size: int) -> tuple[list[dict], int]:
    apps, total = await repo.list_oauth_apps(db, org_id, page=page, page_size=page_size)
    return [
        {
            "client_id": a.client_id,
            "name": a.name,
            "redirect_uris": a.redirect_uris,
            "scopes": a.scopes,
            "grant_types": a.grant_types,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat(),
        }
        for a in apps
    ], total


async def revoke_oauth_app(db: AsyncSession, client_id: str, org_id: UUID) -> None:
    app = await repo.get_oauth_app(db, client_id, org_id)
    if not app:
        raise HTTPException(status_code=404, detail="OAuth app not found")
    app.is_active = False
    app.deleted_at = datetime.now(timezone.utc)
    await db.commit()


async def install_plugin(db: AsyncSession, org_id: UUID, user_id: UUID, data: dict) -> dict:
    _check_platform_permission(await _get_user(db, user_id), "platform:write")
    existing = await repo.get_plugin(db, org_id, data["plugin_id"])
    if existing:
        existing.version = data.get("version", "1.0.0")
        existing.config = data.get("config", {})
        existing.status = "active"
        await db.commit()
        inst = existing
    else:
        inst = PluginInstallation(
            organization_id=org_id,
            plugin_id=data["plugin_id"],
            version=data.get("version", "1.0.0"),
            config=data.get("config", {}),
            installed_by=user_id,
        )
        db.add(inst)
        await db.commit()
        await db.refresh(inst)
    return {
        "id": str(inst.id),
        "plugin_id": inst.plugin_id,
        "version": inst.version,
        "status": inst.status,
        "installed_at": inst.installed_at.isoformat(),
    }


async def list_plugins(db: AsyncSession, org_id: UUID) -> list[dict]:
    plugins = await repo.list_plugins(db, org_id)
    return [
        {
            "id": str(p.id),
            "plugin_id": p.plugin_id,
            "version": p.version,
            "status": p.status,
            "installed_at": p.installed_at.isoformat(),
        }
        for p in plugins
    ]


async def list_marketplace(
    db: AsyncSession, *, item_type: str | None, page: int, page_size: int
) -> tuple[list[dict], int]:
    listings, total = await repo.list_marketplace(db, item_type=item_type, page=page, page_size=page_size)
    return [
        {
            "id": str(l.id),
            "slug": l.slug,
            "name": l.name,
            "item_type": l.item_type,
            "version": l.version,
            "description": l.description,
            "install_count": l.install_count,
            "is_published": l.is_published,
        }
        for l in listings
    ], total


async def get_usage(db: AsyncSession, org_id: UUID, period: str = "30d") -> dict:
    days = int(period.rstrip("d")) if period.endswith("d") else 30
    summary = await repo.get_usage_summary(db, org_id, days=days)
    quota = await repo.ensure_quota(db, org_id)
    return {
        "period": period,
        **summary,
        "quota": {
            "tier": quota.tier,
            "requests_per_minute": quota.requests_per_minute,
            "max_webhooks": quota.max_webhooks,
            "max_oauth_apps": quota.max_oauth_apps,
        },
    }


async def register_developer(
    db: AsyncSession, user: User, data: dict
) -> dict:
    existing = await repo.get_developer_account(db, user.id)
    if existing:
        return {
            "id": str(existing.id),
            "display_name": existing.display_name,
            "is_verified": existing.is_verified,
        }
    account = DeveloperAccount(
        user_id=user.id,
        organization_id=user.organization_id,
        display_name=data["display_name"],
        company=data.get("company"),
        website=data.get("website"),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return {
        "id": str(account.id),
        "display_name": account.display_name,
        "is_verified": account.is_verified,
    }


async def _get_user(db: AsyncSession, user_id: UUID) -> User:
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def seed_marketplace_items(db: AsyncSession) -> int:
    """Seed default marketplace listings (idempotent)."""
    from sqlalchemy import select

    defaults = [
        {"slug": "salesforce-connector", "name": "Salesforce CRM", "item_type": "connector"},
        {"slug": "hubspot-connector", "name": "HubSpot CRM", "item_type": "connector"},
        {"slug": "lead-qualification-pack", "name": "Lead Qualification Pack", "item_type": "workflow_template"},
        {"slug": "executive-dashboard-template", "name": "Executive Dashboard", "item_type": "dashboard_template"},
    ]
    count = 0
    for item in defaults:
        existing = await db.execute(
            select(MarketplaceListing).where(MarketplaceListing.slug == item["slug"])
        )
        if existing.scalar_one_or_none():
            continue
        db.add(MarketplaceListing(
            slug=item["slug"],
            name=item["name"],
            item_type=item["item_type"],
            description=f"Official {item['name']} integration",
            is_published=True,
            manifest={"version": "1.0.0"},
        ))
        count += 1
    if count:
        await db.commit()
    return count
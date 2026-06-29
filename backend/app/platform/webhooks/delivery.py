from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.uuid7 import uuid7
from backend.app.platform.constants import MAX_WEBHOOK_ATTEMPTS, WEBHOOK_RETRY_DELAYS, WebhookDeliveryStatus
from backend.app.platform.models import WebhookDelivery, WebhookSubscription
from backend.app.platform.webhooks.signing import sign_payload


async def deliver_webhook(
    db: AsyncSession,
    subscription: WebhookSubscription,
    *,
    event_type: str,
    payload: dict,
    secret: str | None = None,
) -> WebhookDelivery:
    """Create and attempt delivery of a webhook event."""
    event_id = uuid7()
    delivery = WebhookDelivery(
        subscription_id=subscription.id,
        organization_id=subscription.organization_id,
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        status=WebhookDeliveryStatus.PENDING.value,
    )
    db.add(delivery)
    await db.flush()

    await _attempt_delivery(db, subscription, delivery, secret=secret)
    return delivery


async def _attempt_delivery(
    db: AsyncSession,
    subscription: WebhookSubscription,
    delivery: WebhookDelivery,
    *,
    secret: str | None = None,
) -> None:
    body = json.dumps({
        "id": str(delivery.event_id),
        "type": delivery.event_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data": delivery.payload,
    }).encode()

    headers = {"Content-Type": "application/json", "User-Agent": "ALI-Webhook/4.0"}
    if secret:
        headers["X-ALI-Signature"] = sign_payload(secret, body)

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(subscription.url, content=body, headers=headers)
        elapsed = int((time.monotonic() - start) * 1000)
        delivery.response_status = resp.status_code
        delivery.response_body = resp.text[:2000]
        delivery.response_time_ms = elapsed
        delivery.attempt_count += 1

        if 200 <= resp.status_code < 300:
            delivery.status = WebhookDeliveryStatus.DELIVERED.value
            delivery.delivered_at = datetime.now(timezone.utc)
            subscription.failure_count = 0
            subscription.last_delivery_at = delivery.delivered_at
        else:
            _schedule_retry(delivery, subscription)
    except Exception as exc:
        delivery.attempt_count += 1
        delivery.response_body = str(exc)[:2000]
        delivery.response_time_ms = int((time.monotonic() - start) * 1000)
        _schedule_retry(delivery, subscription)


def _schedule_retry(delivery: WebhookDelivery, subscription: WebhookSubscription) -> None:
    if delivery.attempt_count >= MAX_WEBHOOK_ATTEMPTS:
        delivery.status = WebhookDeliveryStatus.FAILED.value
        subscription.failure_count += 1
        return

    delay_idx = min(delivery.attempt_count - 1, len(WEBHOOK_RETRY_DELAYS) - 1)
    delay = WEBHOOK_RETRY_DELAYS[delay_idx]
    delivery.status = WebhookDeliveryStatus.RETRYING.value
    delivery.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
    subscription.failure_count += 1


async def process_pending_deliveries(db: AsyncSession) -> int:
    """Process webhook deliveries due for retry."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(WebhookDelivery, WebhookSubscription).join(
            WebhookSubscription, WebhookDelivery.subscription_id == WebhookSubscription.id
        ).where(
            WebhookDelivery.status == WebhookDeliveryStatus.RETRYING.value,
            WebhookDelivery.next_retry_at <= now,
            WebhookSubscription.is_active == True,  # noqa: E712
            WebhookSubscription.deleted_at.is_(None),
        ).limit(50)
    )
    count = 0
    for delivery, subscription in result.all():
        await _attempt_delivery(db, subscription, delivery)
        count += 1
    if count:
        await db.commit()
    return count
from __future__ import annotations

import asyncio

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(name="platform.process_webhook_retries")
def process_webhook_retries():
    """Retry pending webhook deliveries."""
    logger.info("Processing webhook delivery retries")

    async def _process():
        from backend.database import AsyncSessionLocal
        from backend.app.platform.webhooks.delivery import process_pending_deliveries

        async with AsyncSessionLocal() as db:
            return await process_pending_deliveries(db)

    try:
        count = _run_async(_process())
        return {"status": "completed", "processed": count}
    except Exception as exc:
        logger.exception("Webhook retry processing failed: %s", exc)
        raise
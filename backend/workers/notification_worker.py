import asyncio
import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.notification_worker.send_notification")
def send_notification(user_id: str, org_id: str, type: str, title: str, body: str = None, channel: str = "in_app"):
    asyncio.run(_send_notification(user_id, org_id, type, title, body, channel))


async def _send_notification(user_id, org_id, ntype, title, body, channel):
    from app.core.database import AsyncSessionLocal
    from app.models.system import Notification

    async with AsyncSessionLocal() as db:
        db.add(Notification(
            user_id=user_id, organization_id=org_id,
            type=ntype, title=title, body=body, channel=channel, status="unread",
        ))
        await db.commit()
        logger.info("Notification queued for user %s: %s", user_id, title)

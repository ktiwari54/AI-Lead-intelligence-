from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_process_init

from backend.config import settings


@worker_process_init.connect
def _reset_async_engine_after_fork(**_kwargs) -> None:
    """Drop inherited asyncpg connections so each worker process gets a fresh pool."""
    import asyncio

    from backend.database import engine

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(engine.dispose())
    finally:
        loop.close()

celery_app = Celery(
    "ai_lead_intel",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "backend.workers.tasks.enrichment",
        "backend.workers.tasks.export",
        "backend.workers.tasks.scoring",
        "backend.workers.tasks.notifications",
        "backend.workers.tasks.discovery",
        "backend.workers.tasks.workflows",
        "backend.workers.tasks.analytics",
        "backend.workers.tasks.platform",
        "backend.workers.tasks.security",
    ],
)

# Ensure discovery tasks register on worker startup
import backend.workers.tasks.discovery  # noqa: F401, E402

# Register all ORM models so Celery workers can resolve FK metadata and mappers
import backend.app.orm_registry  # noqa: F401, E402
import backend.connectors  # noqa: F401, E402

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_max_retries=3,
    task_default_retry_delay=60,
    result_expires=86400,
    beat_schedule={
        # Daily lead scoring refresh
        "score-stale-leads": {
            "task": "backend.workers.tasks.scoring.score_stale_leads",
            "schedule": crontab(hour=2, minute=0),
        },
        # Daily connector health check
        "check-connector-health": {
            "task": "backend.workers.tasks.discovery.check_connector_health",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "run-scheduled-discovery": {
            "task": "backend.workers.tasks.discovery.run_scheduled_searches",
            "schedule": crontab(minute="*/15"),
        },
        # Cleanup expired exports
        "cleanup-exports": {
            "task": "backend.workers.tasks.export.cleanup_expired_exports",
            "schedule": crontab(hour=3, minute=0),
        },
        "run-scheduled-workflows": {
            "task": "backend.workers.tasks.workflows.run_scheduled_workflows",
            "schedule": crontab(minute="*/5"),
        },
        "aggregate-daily-metrics": {
            "task": "backend.workers.tasks.analytics.aggregate_daily_metrics",
            "schedule": crontab(hour=1, minute=0),
        },
        "check-analytics-alerts": {
            "task": "backend.workers.tasks.analytics.check_alert_rules",
            "schedule": crontab(minute="*/30"),
        },
        "refresh-analytics-forecasts": {
            "task": "backend.workers.tasks.analytics.refresh_forecasts",
            "schedule": crontab(hour=4, minute=0),
        },
        "process-webhook-retries": {
            "task": "backend.workers.tasks.platform.process_webhook_retries",
            "schedule": crontab(minute="*/2"),
        },
        "run-security-compliance": {
            "task": "backend.workers.tasks.security.run_compliance_checks",
            "schedule": crontab(hour=5, minute=0),
        },
        "process-soc-alerts": {
            "task": "backend.workers.tasks.security.process_soc_alerts",
            "schedule": crontab(minute="*/15"),
        },
    },
)

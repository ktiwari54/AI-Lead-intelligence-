from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "leadintel",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "workers.lead_scoring_worker",
        "workers.enrichment_worker",
        "workers.export_worker",
        "workers.notification_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "workers.lead_scoring_worker.*": {"queue": "scoring"},
        "workers.enrichment_worker.*": {"queue": "enrichment"},
        "workers.export_worker.*": {"queue": "exports"},
        "workers.notification_worker.*": {"queue": "notifications"},
    },
)

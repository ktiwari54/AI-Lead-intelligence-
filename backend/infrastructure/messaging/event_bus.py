from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol
from uuid import UUID

from backend.app.common.uuid7 import uuid7


class DomainEvent(str, Enum):
    COMPANY_CREATED = "company.created"
    COMPANY_UPDATED = "company.updated"
    COMPANY_MERGED = "company.merged"
    CONTACT_CREATED = "contact.created"
    CONTACT_UPDATED = "contact.updated"
    CONTACT_MERGED = "contact.merged"
    SEARCH_COMPLETED = "search.completed"
    CONNECTOR_FINISHED = "connector.finished"
    LEAD_SCORED = "lead.scored"
    EXPORT_COMPLETED = "export.completed"
    IMPORT_COMPLETED = "import.completed"
    NOTIFICATION_SENT = "notification.sent"
    WORKFLOW_EXECUTED = "workflow.executed"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    EMAIL_VERIFIED = "email.verified"


@dataclass
class EventEnvelope:
    event_id: UUID
    event_type: DomainEvent
    aggregate_type: str
    aggregate_id: UUID
    organization_id: UUID
    actor_id: UUID | None
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        event_type: DomainEvent,
        aggregate_type: str,
        aggregate_id: UUID,
        organization_id: UUID,
        payload: dict[str, Any],
        *,
        actor_id: UUID | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> EventEnvelope:
        return cls(
            event_id=uuid7(),
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            organization_id=organization_id,
            actor_id=actor_id,
            payload=payload,
            metadata={
                "request_id": request_id,
                "correlation_id": correlation_id,
            },
        )


class EventBusPort(Protocol):
    async def publish(self, event: EventEnvelope) -> None: ...


class EventBus:
    """
    Outbox-backed event bus.

    Phase 3 flow:
    1. Service writes event to event_store (same DB transaction)
    2. Outbox poller publishes to Celery
    3. Subscribers process asynchronously
    """

    def __init__(self, session_factory, celery_app=None):
        self._session_factory = session_factory
        self._celery = celery_app

    async def publish(self, event: EventEnvelope) -> None:
        from backend.app.common.event_store import publish_event

        async with self._session_factory() as session:
            await publish_event(
                db=session,
                event_type=event.event_type.value,
                aggregate_type=event.aggregate_type,
                aggregate_id=str(event.aggregate_id),
                data=event.payload,
                actor_id=str(event.actor_id) if event.actor_id else None,
                org_id=str(event.organization_id),
                correlation_id=event.metadata.get("correlation_id"),
                metadata=event.metadata,
            )
            await session.commit()

        if self._celery:
            self._celery.send_task(
                "messaging.dispatch_event",
                args=[event.event_type.value, str(event.event_id)],
            )
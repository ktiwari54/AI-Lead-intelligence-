"""Domain event bus (in-process + Celery fanout)."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    org_id: UUID | None = None
    user_id: UUID | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


@dataclass
class CompanyCreated(DomainEvent): pass
@dataclass
class CompanyUpdated(DomainEvent): pass
@dataclass
class CompanyDeleted(DomainEvent): pass
@dataclass
class ContactCreated(DomainEvent): pass
@dataclass
class ContactUpdated(DomainEvent): pass
@dataclass
class SearchCompleted(DomainEvent): pass
@dataclass
class ConnectorFinished(DomainEvent): pass
@dataclass
class LeadScored(DomainEvent): pass
@dataclass
class ExportCompleted(DomainEvent): pass
@dataclass
class NotificationSent(DomainEvent): pass
@dataclass
class WorkflowExecuted(DomainEvent): pass
@dataclass
class SubscriptionUpdated(DomainEvent): pass
@dataclass
class CreditDeducted(DomainEvent): pass


class EventBus:
    _handlers: dict[str, list] = {}

    @classmethod
    def subscribe(cls, event_type: type[DomainEvent]):
        def decorator(fn):
            cls._handlers.setdefault(event_type.__name__, []).append(fn)
            return fn
        return decorator

    @classmethod
    async def publish(cls, event: DomainEvent) -> None:
        logger.info("event_published", event_type=event.event_type, event_id=str(event.event_id))
        for handler in cls._handlers.get(event.event_type, []):
            try:
                await handler(event)
            except Exception as e:
                logger.error("event_handler_failed", event_type=event.event_type, error=str(e))


event_bus = EventBus()

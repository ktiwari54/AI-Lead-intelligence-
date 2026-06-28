from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RequestContext:
    """Propagated from middleware through every service call."""

    request_id: str
    correlation_id: str
    organization_id: UUID
    user_id: UUID
    roles: frozenset[str]
    permissions: frozenset[str]
    ip_address: str | None = None
    user_agent: str | None = None
    idempotency_key: str | None = None

    def has_permission(self, permission: str) -> bool:
        if "*" in self.permissions:
            return True
        return permission in self.permissions

    def has_any_permission(self, *permissions: str) -> bool:
        return any(self.has_permission(p) for p in permissions)

    def has_role(self, role: str) -> bool:
        return role in self.roles
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from backend.app.core.context import RequestContext
from backend.app.core.exceptions import ForbiddenException

ROLE_HIERARCHY: dict[str, int] = {
    "viewer": 0,
    "member": 1,
    "manager": 2,
    "admin": 3,
    "owner": 4,
}

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "viewer": frozenset({
        "companies:read", "contacts:read", "search:read", "ai:read",
        "crm:read", "analytics:read", "enrichment:read",
    }),
    "member": frozenset({
        "companies:read", "companies:write", "contacts:read", "contacts:write",
        "search:execute", "search:read", "ai:read", "ai:score",
        "crm:read", "crm:write", "enrichment:execute", "enrichment:read",
        "exports:create", "exports:read", "analytics:read",
    }),
    "manager": frozenset({
        "companies:read", "companies:write", "companies:merge",
        "contacts:read", "contacts:write", "contacts:merge", "contacts:verify",
        "search:execute", "search:read", "search:write",
        "ai:read", "ai:score", "crm:read", "crm:write", "crm:sync",
        "enrichment:execute", "enrichment:read",
        "exports:create", "exports:read", "imports:create", "imports:read",
        "connectors:read", "connectors:write",
        "workflows:read", "workflows:write", "workflows:execute",
        "analytics:read", "billing:read",
    }),
    "admin": frozenset({"*"}),
    "owner": frozenset({"*"}),
}


def resolve_permissions(roles: frozenset[str], explicit: frozenset[str] | None = None) -> frozenset[str]:
    perms: set[str] = set(explicit or ())
    for role in roles:
        perms.update(ROLE_PERMISSIONS.get(role, frozenset()))
    return frozenset(perms)


def require_permission(*permissions: str) -> Callable:
    """Decorator for service methods requiring specific permissions."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(ctx: RequestContext, *args: Any, **kwargs: Any) -> Any:
            if not ctx.has_any_permission(*permissions):
                raise ForbiddenException(
                    f"Requires one of: {', '.join(permissions)}",
                    code="FORBIDDEN",
                )
            return await fn(ctx, *args, **kwargs)

        return wrapper

    return decorator


def evaluate_abac(
    ctx: RequestContext,
    resource_owner_id: str | None = None,
    required_permission: str = "",
) -> bool:
    """Attribute-based access: owner can access own resources with write permission."""
    if ctx.has_permission(required_permission):
        return True
    if resource_owner_id and str(ctx.user_id) == resource_owner_id:
        base = required_permission.rsplit(":", 1)[0]
        return ctx.has_permission(f"{base}:write:own")
    return False
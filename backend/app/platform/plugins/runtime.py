from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class PluginHandler(Protocol):
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]: ...


class PluginRuntime:
    """In-process plugin runtime for backend extensions."""

    def __init__(self) -> None:
        self._registry: dict[str, PluginHandler] = {}

    def register(self, plugin_id: str, handler: PluginHandler) -> None:
        self._registry[plugin_id] = handler

    def unregister(self, plugin_id: str) -> None:
        self._registry.pop(plugin_id, None)

    async def invoke(
        self,
        plugin_id: str,
        context: dict[str, Any],
        *,
        organization_id: UUID | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        handler = self._registry.get(plugin_id)
        if not handler:
            return {"error": f"Plugin '{plugin_id}' not registered", "status": "not_found"}

        enriched = {**context, "organization_id": str(organization_id) if organization_id else None}
        if config:
            enriched["config"] = config
        return await handler.execute(enriched)

    def list_registered(self) -> list[str]:
        return list(self._registry.keys())


plugin_runtime = PluginRuntime()
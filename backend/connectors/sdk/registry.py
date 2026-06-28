from __future__ import annotations

from typing import Any, Type

from backend.connectors.sdk.base import ConnectorSDKBase


class SDKConnectorRegistry:
    """Registry for Phase 5 SDK v2 connectors."""

    _registry: dict[str, Type[ConnectorSDKBase]] = {}

    @classmethod
    def register(cls, connector_class: Type[ConnectorSDKBase]) -> Type[ConnectorSDKBase]:
        cls._registry[connector_class.name] = connector_class
        return connector_class

    @classmethod
    def get(cls, name: str, config: dict[str, Any] | None = None) -> ConnectorSDKBase | None:
        connector_class = cls._registry.get(name)
        if not connector_class:
            return None
        return connector_class(config or {})

    @classmethod
    def list_available(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": klass.name,
                "display_name": klass.display_name,
                "version": klass.version,
                "category": klass.category.value,
                "source_type": klass.source_type.value,
                "capabilities": [c.value for c in klass.capabilities],
                "sdk_version": "2.0",
            }
            for klass in cls._registry.values()
        ]

    @classmethod
    def all(cls) -> dict[str, Type[ConnectorSDKBase]]:
        return dict(cls._registry)
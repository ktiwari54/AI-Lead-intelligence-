from typing import Type
from backend.connectors.base import BaseConnector


class ConnectorRegistry:
    _registry: dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, connector_class: Type[BaseConnector]) -> Type[BaseConnector]:
        """Register a connector class. Can be used as a decorator."""
        cls._registry[connector_class.name] = connector_class
        return connector_class

    @classmethod
    def get(cls, name: str, config: dict | None = None) -> BaseConnector | None:
        """Instantiate and return a connector by name."""
        connector_class = cls._registry.get(name)
        if not connector_class:
            return None
        return connector_class(config or {})

    @classmethod
    def list_available(cls) -> list[dict]:
        """Return metadata for all registered connectors."""
        return [
            {
                "name": klass.name,
                "display_name": klass.display_name,
                "version": klass.version,
                "supports_search": klass.supports_search,
                "supports_lookup": klass.supports_lookup,
                "supports_enrich": klass.supports_enrich,
            }
            for klass in cls._registry.values()
        ]

    @classmethod
    def all(cls) -> dict[str, BaseConnector]:
        """Return all registered connector classes (not instances)."""
        return dict(cls._registry)


# ─── Example stub connector ────────────────────────────────────────────────────────────

@ConnectorRegistry.register
class MockEmailVerifierConnector(BaseConnector):
    name = "email_verifier"
    display_name = "Email Verifier (Mock)"
    version = "1.0"
    supports_search = False
    supports_lookup = True
    supports_enrich = True

    def authenticate(self) -> bool:
        return True

    def search(self, query: str, filters: dict):
        from backend.connectors.base import ConnectorResult
        return ConnectorResult(success=True, data=[])

    def lookup(self, identifier: str, identifier_type: str = "email"):
        from backend.connectors.base import ConnectorResult
        return ConnectorResult(
            success=True,
            data=[{"email": identifier, "status": "valid", "confidence": 0.95}],
            source=self.name,
        )

    def enrich(self, data: dict):
        from backend.connectors.base import ConnectorResult
        emails = data.get("emails", [])
        results = [{"email": e, "status": "valid", "confidence": 0.90} for e in emails]
        return ConnectorResult(success=True, data=results, source=self.name)

    def normalize(self, raw: dict) -> dict:
        return raw

    def health_check(self) -> dict:
        return {"healthy": True, "latency_ms": 0}

    def get_rate_limit(self):
        from backend.connectors.base import RateLimitInfo
        return RateLimitInfo(requests_remaining=10000, requests_limit=10000)

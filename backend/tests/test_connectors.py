"""Unit tests for the connector framework.

These tests do NOT require a running database; they test the connector
registry and normalization logic using mocks.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.connectors.registry import ConnectorRegistry
from backend.connectors.base import BaseConnector, ConnectorResult, RateLimitInfo


# ---------------------------------------------------------------------------
# Helper: minimal concrete connector for testing
# ---------------------------------------------------------------------------

class _StubConnector(BaseConnector):
    """A minimal concrete connector used only in these tests."""
    name = "_stub"
    display_name = "Stub"
    version = "0.1"
    supports_search = True
    supports_lookup = True
    supports_enrich = True

    def authenticate(self) -> bool:
        return True

    def search(self, query: str, filters: dict) -> ConnectorResult:
        return ConnectorResult(success=True, data=[], source=self.name)

    def lookup(self, identifier: str, identifier_type: str = "email") -> ConnectorResult:
        return ConnectorResult(success=True, data=[{"id": identifier}], source=self.name)

    def enrich(self, data: dict) -> ConnectorResult:
        return ConnectorResult(success=True, data=[data], source=self.name)

    def normalize(self, raw: dict) -> dict:
        return {"normalized": True, **raw}

    def health_check(self) -> dict:
        return {"healthy": True, "latency_ms": 1}

    def get_rate_limit(self) -> RateLimitInfo:
        return RateLimitInfo(requests_remaining=500, requests_limit=1000)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_connector_registry_contains_email_verifier():
    """The mock email_verifier stub connector should be registered by default."""
    available = ConnectorRegistry.list_available()
    names = [c["name"] for c in available]
    assert "email_verifier" in names, (
        f"Expected 'email_verifier' in registry, got: {names}"
    )


def test_connector_registry_register_and_get():
    """Registering a connector class allows retrieval and instantiation via get()."""
    ConnectorRegistry.register(_StubConnector)
    instance = ConnectorRegistry.get("_stub", config={"key": "value"})
    assert instance is not None, "Registry.get() should return an instance"
    assert isinstance(instance, _StubConnector)
    assert instance.config == {"key": "value"}


def test_connector_registry_get_unknown_returns_none():
    """Requesting an unregistered connector name returns None."""
    instance = ConnectorRegistry.get("nonexistent_xyz_connector")
    assert instance is None


def test_connector_registry_list_available_structure():
    """list_available() returns dicts with required metadata keys."""
    available = ConnectorRegistry.list_available()
    assert len(available) >= 1
    required_keys = {"name", "display_name", "version", "supports_search", "supports_lookup", "supports_enrich"}
    for entry in available:
        missing = required_keys - set(entry.keys())
        assert not missing, f"Connector entry missing keys: {missing}, got: {entry}"


def test_stub_normalize_person():
    """normalize() on a stub connector maps raw fields into the canonical schema."""
    connector = _StubConnector(config={})
    raw = {"first_name": "Jane", "last_name": "Doe", "title": "CTO", "email": "jane@example.com"}
    result = connector.normalize(raw)
    assert result["normalized"] is True
    assert result["first_name"] == "Jane"
    assert result["email"] == "jane@example.com"


def test_stub_normalize_company():
    """normalize() on a stub connector handles org/company raw data."""
    connector = _StubConnector(config={})
    raw = {"name": "Acme Corp", "domain": "acme.com", "employee_count": 500}
    result = connector.normalize(raw)
    assert result["normalized"] is True
    assert result["name"] == "Acme Corp"
    assert result["domain"] == "acme.com"


def test_stub_rate_limit():
    """get_rate_limit() returns a RateLimitInfo with correct values."""
    connector = _StubConnector(config={})
    rate_limit = connector.get_rate_limit()
    assert isinstance(rate_limit, RateLimitInfo)
    assert rate_limit.requests_remaining == 500
    assert rate_limit.requests_limit == 1000
    assert rate_limit.requests_remaining <= rate_limit.requests_limit


def test_stub_health_check():
    """health_check() returns a dict indicating healthy status."""
    connector = _StubConnector(config={})
    health = connector.health_check()
    assert health["healthy"] is True
    assert "latency_ms" in health


def test_stub_authenticate():
    """authenticate() returns True for the stub connector."""
    connector = _StubConnector(config={})
    assert connector.authenticate() is True


def test_stub_lookup():
    """lookup() returns a ConnectorResult with the identifier in data."""
    connector = _StubConnector(config={})
    result = connector.lookup("jane@example.com", identifier_type="email")
    assert isinstance(result, ConnectorResult)
    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0]["id"] == "jane@example.com"


def test_stub_search():
    """search() returns an empty ConnectorResult for the stub."""
    connector = _StubConnector(config={})
    result = connector.search(query="engineers", filters={"seniority": "C_LEVEL"})
    assert isinstance(result, ConnectorResult)
    assert result.success is True
    assert result.data == []


def test_stub_enrich():
    """enrich() returns the same dict wrapped in a ConnectorResult."""
    connector = _StubConnector(config={})
    data = {"email": "bob@example.com", "domain": "example.com"}
    result = connector.enrich(data)
    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0]["email"] == "bob@example.com"


def test_email_verifier_lookup_via_registry():
    """The email_verifier connector returned from registry performs lookup correctly."""
    connector = ConnectorRegistry.get("email_verifier", config={})
    assert connector is not None
    result = connector.lookup("test@example.com")
    assert result.success is True
    assert len(result.data) >= 1
    assert result.data[0]["email"] == "test@example.com"
    assert result.data[0]["status"] == "valid"


def test_connector_result_defaults():
    """ConnectorResult has sensible defaults."""
    result = ConnectorResult(success=True)
    assert result.data == []
    assert result.errors == []
    assert result.credits_used == 0
    assert result.source == ""


def test_parse_response_dict():
    """parse_response() with a plain dict returns it unchanged."""
    connector = _StubConnector(config={})
    raw = {"key": "value"}
    assert connector.parse_response(raw) == raw


def test_parse_response_json_string():
    """parse_response() with a JSON string returns the parsed dict."""
    connector = _StubConnector(config={})
    assert connector.parse_response('{"foo": 42}') == {"foo": 42}

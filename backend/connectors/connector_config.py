"""Resolve connector credentials from application settings."""

from __future__ import annotations

from backend.config import settings

_CONNECTOR_ENV_KEYS: dict[str, str] = {
    "apollo": "APOLLO_API_KEY",
    "clearbit": "CLEARBIT_API_KEY",
    "hunter": "HUNTER_API_KEY",
}


def connector_config_for(name: str) -> dict[str, str]:
    """Build the config dict passed to connector constructors."""
    env_key = _CONNECTOR_ENV_KEYS.get(name)
    if not env_key:
        return {}
    api_key = getattr(settings, env_key, "") or ""
    return {"api_key": api_key} if api_key else {}


def has_configured_providers() -> bool:
    """True when at least one licensed provider has an API key."""
    return any(connector_config_for(name) for name in _CONNECTOR_ENV_KEYS)


def should_use_mock_connectors() -> bool:
    """Use mock discovery data when explicitly enabled or no provider keys in dev."""
    if settings.USE_MOCK_CONNECTORS:
        return True
    return settings.ENVIRONMENT == "development" and not has_configured_providers()
"""Unit tests for Phase 10 Integration Platform."""
from __future__ import annotations

import json

import pytest

from backend.app.platform.constants import DEFAULT_SCOPES, WebhookDeliveryStatus
from backend.app.platform.plugins.runtime import PluginRuntime
from backend.app.platform.service import platform_health
from backend.app.platform.webhooks.signing import generate_webhook_secret, hash_secret, sign_payload, verify_signature


@pytest.fixture
def plugin_runtime():
    return PluginRuntime()


class EchoPlugin:
    async def execute(self, context: dict) -> dict:
        return {"echo": context.get("input"), "status": "ok"}


def test_platform_health():
    health = platform_health()
    assert health["status"] == "healthy"
    assert health["gateway_version"] == "4.0"
    assert "webhooks" in health["subsystems"]


def test_webhook_secret_generation():
    secret = generate_webhook_secret()
    assert secret.startswith("whsec_")
    assert len(secret) > 20


def test_webhook_signing_and_verification():
    secret = "whsec_test_secret"
    payload = json.dumps({"type": "contact.created"}).encode()
    signature = sign_payload(secret, payload)
    assert verify_signature(secret, payload, signature)


def test_webhook_hash_secret():
    h1 = hash_secret("whsec_abc")
    h2 = hash_secret("whsec_abc")
    assert h1 == h2
    assert h1 != hash_secret("whsec_xyz")


def test_default_scopes():
    assert "crm:read" in DEFAULT_SCOPES
    assert "webhooks:manage" in DEFAULT_SCOPES


def test_webhook_delivery_status_enum():
    assert WebhookDeliveryStatus.PENDING.value == "pending"
    assert WebhookDeliveryStatus.DELIVERED.value == "delivered"


@pytest.mark.asyncio
async def test_plugin_runtime_invoke(plugin_runtime):
    plugin_runtime.register("echo", EchoPlugin())
    result = await plugin_runtime.invoke("echo", {"input": "hello"})
    assert result["echo"] == "hello"
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_plugin_runtime_not_found(plugin_runtime):
    result = await plugin_runtime.invoke("missing", {})
    assert result["status"] == "not_found"


def test_plugin_runtime_list(plugin_runtime):
    plugin_runtime.register("a", EchoPlugin())
    plugin_runtime.register("b", EchoPlugin())
    assert set(plugin_runtime.list_registered()) == {"a", "b"}
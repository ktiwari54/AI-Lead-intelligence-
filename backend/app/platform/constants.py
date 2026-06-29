from __future__ import annotations

from enum import Enum


class WebhookDeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class OAuthGrantType(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"


class PluginStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


class MarketplaceItemType(str, Enum):
    CONNECTOR = "connector"
    PLUGIN = "plugin"
    WORKFLOW_TEMPLATE = "workflow_template"
    DASHBOARD_TEMPLATE = "dashboard_template"
    AI_PROMPT = "ai_prompt"
    WIDGET = "widget"


DEFAULT_SCOPES = [
    "crm:read", "crm:write", "contacts:read", "contacts:write",
    "search:read", "search:write", "workflows:execute",
    "analytics:read", "webhooks:manage", "platform:read", "platform:write",
]

WEBHOOK_RETRY_DELAYS = [60, 300, 1800, 7200, 86400]
MAX_WEBHOOK_ATTEMPTS = 5
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class PlatformHealthResponse(BaseModel):
    status: str
    gateway_version: str
    subsystems: dict[str, str]
    timestamp: str


class PlatformCapabilitiesResponse(BaseModel):
    api_version: str
    feature_flags: list[str]
    auth_methods: list[str]
    available_scopes: list[str]
    rate_limit: dict[str, int]


class WebhookCreateRequest(BaseModel):
    url: str
    events: list[str]
    description: str | None = None
    secret: str | None = None


class WebhookUpdateRequest(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    description: str | None = None
    is_active: bool | None = None


class WebhookSubscriptionResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    description: str | None
    is_active: bool
    failure_count: int
    last_delivery_at: str | None
    created_at: str
    secret: str | None = None

    model_config = {"from_attributes": True}


class WebhookTestRequest(BaseModel):
    event_type: str = "contact.created"


class WebhookDeliveryResponse(BaseModel):
    id: str
    event_type: str
    status: str
    attempt_count: int
    response_status: int | None
    response_time_ms: int | None
    delivered_at: str | None
    created_at: str


class OAuthAppCreateRequest(BaseModel):
    name: str
    redirect_uris: list[str]
    scopes: list[str]
    grant_types: list[str] = ["authorization_code", "refresh_token"]
    description: str | None = None


class OAuthAppResponse(BaseModel):
    client_id: str
    name: str
    redirect_uris: list[str]
    scopes: list[str]
    grant_types: list[str]
    is_active: bool
    created_at: str
    client_secret: str | None = None


class PluginInstallRequest(BaseModel):
    plugin_id: str
    version: str = "1.0.0"
    config: dict = Field(default_factory=dict)


class PluginInstallationResponse(BaseModel):
    id: str
    plugin_id: str
    version: str
    status: str
    installed_at: str


class MarketplaceListingResponse(BaseModel):
    id: str
    slug: str
    name: str
    item_type: str
    version: str
    description: str | None
    install_count: int
    is_published: bool


class UsageSummaryResponse(BaseModel):
    period: str
    total_requests: int
    error_count: int
    avg_response_ms: float
    by_endpoint: dict[str, int]
    quota: dict[str, int | str]


class DeveloperAccountCreateRequest(BaseModel):
    display_name: str
    company: str | None = None
    website: str | None = None
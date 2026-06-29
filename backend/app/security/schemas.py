from __future__ import annotations

from pydantic import BaseModel, Field


class SecuritySettingsUpdate(BaseModel):
    mfa_required: bool | None = None
    mfa_grace_days: int | None = None
    ip_allowlist: list[str] | None = None
    session_max_concurrent: int | None = None
    export_requires_approval: bool | None = None
    ai_pii_redaction: bool | None = None
    compliance_profile: str | None = None


class SecurityEventCreate(BaseModel):
    event_type: str
    severity: str = "info"
    resource: str | None = None
    action: str | None = None
    metadata: dict = Field(default_factory=dict)


class IncidentCreateRequest(BaseModel):
    title: str
    severity: str
    incident_type: str
    description: str | None = None
    event_ids: list[str] = Field(default_factory=list)


class IncidentUpdateRequest(BaseModel):
    status: str | None = None
    severity: str | None = None
    assigned_to: str | None = None


class IncidentCloseRequest(BaseModel):
    root_cause: str
    remediation: str
    status: str = "closed"


class IncidentTimelineRequest(BaseModel):
    action: str
    notes: str


class MfaDeviceCreateRequest(BaseModel):
    type: str = "totp"
    label: str


class MfaVerifyRequest(BaseModel):
    device_id: str
    code: str


class PolicyCreateRequest(BaseModel):
    name: str
    category: str
    rules: dict
    description: str | None = None
    priority: int = 100


class PolicyAssignRequest(BaseModel):
    target_type: str
    target_id: str
    effective_from: str | None = None


class PrivacyRequestCreate(BaseModel):
    request_type: str
    subject_email: str | None = None
    subject_id: str | None = None
    details: str | None = None


class ConsentCreateRequest(BaseModel):
    subject_type: str
    subject_id: str
    purpose: str
    legal_basis: str
    status: str = "granted"


class AlertAcknowledgeRequest(BaseModel):
    notes: str | None = None
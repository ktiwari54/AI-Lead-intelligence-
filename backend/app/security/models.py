from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.common.base import BaseModel


class SecurityEvent(BaseModel):
    __tablename__ = "security_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), server_default="info", nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    actor_type: Mapped[str] = mapped_column(String(30), server_default="user", nullable=False)
    resource: Mapped[str | None] = mapped_column(String(200))
    action: Mapped[str | None] = mapped_column(String(100))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(100))
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    source_ip: Mapped[str | None] = mapped_column(String(45))

    __table_args__ = (
        Index("ix_sec_events_org_created", "organization_id", "created_at"),
        Index("ix_sec_events_type", "event_type"),
        Index("ix_sec_events_severity", "severity"),
    )


class SecurityIncident(BaseModel):
    __tablename__ = "security_incidents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(30), server_default="open", nullable=False)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    contained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timeline: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text)
    remediation: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (
        Index("ix_sec_incidents_org_status", "organization_id", "status"),
        Index("ix_sec_incidents_severity", "severity"),
    )


class RiskScore(BaseModel):
    __tablename__ = "risk_scores"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    subject_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    factors: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("organization_id", "subject_type", "subject_id", name="uq_risk_scores_subject"),
        Index("ix_risk_scores_level", "level"),
    )


class SecurityAccessLog(BaseModel):
    __tablename__ = "security_access_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    auth_method: Mapped[str | None] = mapped_column(String(30))
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_score: Mapped[int | None] = mapped_column(Integer)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    policy_ids: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(100))
    source_ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_access_logs_org_created", "organization_id", "created_at"),
        Index("ix_access_logs_decision", "decision"),
    )


class AuthenticationLog(BaseModel):
    __tablename__ = "authentication_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(200))
    mfa_method: Mapped[str | None] = mapped_column(String(30))
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    geo_location: Mapped[str | None] = mapped_column(String(200))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (
        Index("ix_auth_logs_org_created", "organization_id", "created_at"),
        Index("ix_auth_logs_user", "user_id"),
    )


class AuthorizationLog(BaseModel):
    __tablename__ = "authorization_logs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    resource: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[str] = mapped_column(String(10), nullable=False)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str | None] = mapped_column(String(500))
    risk_score: Mapped[int | None] = mapped_column(Integer)
    request_id: Mapped[str | None] = mapped_column(String(100))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (
        Index("ix_authz_logs_org_created", "organization_id", "created_at"),
        Index("ix_authz_logs_decision", "decision"),
    )


class MfaDevice(BaseModel):
    __tablename__ = "mfa_devices"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    secret_encrypted: Mapped[str | None] = mapped_column(Text)
    credential_id: Mapped[str | None] = mapped_column(String(500))
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_mfa_devices_user", "user_id"),)


class TrustedDevice(BaseModel):
    __tablename__ = "trusted_devices"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    device_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(200))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    trust_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    is_revoked: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "device_fingerprint", name="uq_trusted_devices_fingerprint"),
        Index("ix_trusted_devices_user", "user_id"),
    )


class SecretsMetadata(BaseModel):
    __tablename__ = "secrets_metadata"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)
    provider: Mapped[str] = mapped_column(String(50), server_default="env", nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="active", nullable=False)
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (UniqueConstraint("name", "version", name="uq_secrets_name_version"),)


class PolicyDefinition(BaseModel):
    __tablename__ = "policy_definitions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, server_default="100", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    __table_args__ = (
        Index("ix_policies_org_active", "organization_id", "is_active"),
        Index("ix_policies_category", "category"),
    )


class PolicyAssignment(BaseModel):
    __tablename__ = "policy_assignments"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policy_definitions.id", ondelete="CASCADE"), nullable=False
    )
    target_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_policy_assignments_target", "organization_id", "target_type", "target_id"),
        Index("ix_policy_assignments_policy", "policy_id"),
    )


class ConsentRecord(BaseModel):
    __tablename__ = "consent_records"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    subject_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    purpose: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_basis: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="granted", nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (Index("ix_consent_subject", "organization_id", "subject_type", "subject_id"),)


class PrivacyRequest(BaseModel):
    __tablename__ = "privacy_requests"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    request_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subject_email: Mapped[str | None] = mapped_column(String(254))
    subject_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(30), server_default="received", nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_notes: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (Index("ix_privacy_org_status", "organization_id", "status"),)


class ComplianceCheck(BaseModel):
    __tablename__ = "compliance_checks"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    framework: Mapped[str] = mapped_column(String(30), nullable=False)
    control_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    remediation: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_compliance_org_framework", "organization_id", "framework"),)


class VulnerabilityReport(BaseModel):
    __tablename__ = "vulnerability_reports"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cve_id: Mapped[str | None] = mapped_column(String(30))
    cvss_score: Mapped[float | None] = mapped_column(Numeric(3, 1))
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    affected_component: Mapped[str | None] = mapped_column(String(500))
    affected_version: Mapped[str | None] = mapped_column(String(100))
    fixed_version: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), server_default="open", nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    remediated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    remediation_notes: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (Index("ix_vuln_status_severity", "status", "severity"),)


class SecurityAlert(BaseModel):
    __tablename__ = "security_alerts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), server_default="active", nullable=False)
    source_event_ids: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (
        Index("ix_sec_alerts_org_status", "organization_id", "status"),
        Index("ix_sec_alerts_severity", "severity"),
    )
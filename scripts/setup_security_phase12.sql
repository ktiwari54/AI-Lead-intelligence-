-- Idempotent Phase 12 enterprise security schema bootstrap
-- Use when alembic upgrade fails on partial dev databases

CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    actor_id UUID,
    actor_type VARCHAR(30) NOT NULL DEFAULT 'user',
    resource VARCHAR(200),
    action VARCHAR(100),
    metadata JSONB NOT NULL DEFAULT '{}',
    request_id VARCHAR(100),
    correlation_id VARCHAR(100),
    source_ip VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_sec_events_org_created ON security_events(organization_id, created_at);
CREATE INDEX IF NOT EXISTS ix_sec_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS ix_sec_events_severity ON security_events(severity);

CREATE TABLE IF NOT EXISTS security_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    severity VARCHAR(10) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    incident_type VARCHAR(100) NOT NULL,
    assigned_to UUID,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    contained_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    timeline JSONB NOT NULL DEFAULT '[]',
    root_cause TEXT,
    remediation TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_sec_incidents_org_status ON security_incidents(organization_id, status);
CREATE INDEX IF NOT EXISTS ix_sec_incidents_severity ON security_incidents(severity);

CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    subject_type VARCHAR(30) NOT NULL,
    subject_id UUID NOT NULL,
    score INTEGER NOT NULL,
    level VARCHAR(20) NOT NULL,
    factors JSONB NOT NULL DEFAULT '[]',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (organization_id, subject_type, subject_id)
);
CREATE INDEX IF NOT EXISTS ix_risk_scores_level ON risk_scores(level);

CREATE TABLE IF NOT EXISTS security_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID,
    auth_method VARCHAR(30),
    endpoint VARCHAR(500) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    risk_score INTEGER,
    decision VARCHAR(20) NOT NULL,
    policy_ids JSONB NOT NULL DEFAULT '[]',
    request_id VARCHAR(100),
    source_ip VARCHAR(45),
    user_agent VARCHAR(500),
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_access_logs_org_created ON security_access_logs(organization_id, created_at);
CREATE INDEX IF NOT EXISTS ix_access_logs_decision ON security_access_logs(decision);

CREATE TABLE IF NOT EXISTS authentication_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID,
    event_type VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(200),
    mfa_method VARCHAR(30),
    device_id UUID,
    source_ip VARCHAR(45),
    user_agent VARCHAR(500),
    geo_location VARCHAR(200),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_auth_logs_org_created ON authentication_logs(organization_id, created_at);
CREATE INDEX IF NOT EXISTS ix_auth_logs_user ON authentication_logs(user_id);

CREATE TABLE IF NOT EXISTS authorization_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID,
    resource VARCHAR(200) NOT NULL,
    action VARCHAR(100) NOT NULL,
    decision VARCHAR(10) NOT NULL,
    policy_id UUID,
    reason VARCHAR(500),
    risk_score INTEGER,
    request_id VARCHAR(100),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_authz_logs_org_created ON authorization_logs(organization_id, created_at);
CREATE INDEX IF NOT EXISTS ix_authz_logs_decision ON authorization_logs(decision);

CREATE TABLE IF NOT EXISTS mfa_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(30) NOT NULL,
    label VARCHAR(200) NOT NULL,
    secret_encrypted TEXT,
    credential_id VARCHAR(500),
    is_verified BOOLEAN NOT NULL DEFAULT false,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_mfa_devices_user ON mfa_devices(user_id);

CREATE TABLE IF NOT EXISTS trusted_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_fingerprint VARCHAR(64) NOT NULL,
    device_name VARCHAR(200),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    trust_expires_at TIMESTAMPTZ NOT NULL,
    last_ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    is_revoked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (user_id, device_fingerprint)
);
CREATE INDEX IF NOT EXISTS ix_trusted_devices_user ON trusted_devices(user_id);

CREATE TABLE IF NOT EXISTS secrets_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID,
    name VARCHAR(200) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    provider VARCHAR(50) NOT NULL DEFAULT 'env',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    rotated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS policy_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    rules JSONB NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_policies_org_active ON policy_definitions(organization_id, is_active);
CREATE INDEX IF NOT EXISTS ix_policies_category ON policy_definitions(category);

CREATE TABLE IF NOT EXISTS policy_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    policy_id UUID NOT NULL REFERENCES policy_definitions(id) ON DELETE CASCADE,
    target_type VARCHAR(30) NOT NULL,
    target_id UUID NOT NULL,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_policy_assignments_target ON policy_assignments(organization_id, target_type, target_id);
CREATE INDEX IF NOT EXISTS ix_policy_assignments_policy ON policy_assignments(policy_id);

CREATE TABLE IF NOT EXISTS consent_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    subject_type VARCHAR(30) NOT NULL,
    subject_id UUID NOT NULL,
    purpose VARCHAR(100) NOT NULL,
    legal_basis VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'granted',
    granted_at TIMESTAMPTZ,
    withdrawn_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    evidence JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_consent_subject ON consent_records(organization_id, subject_type, subject_id);

CREATE TABLE IF NOT EXISTS privacy_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    request_type VARCHAR(30) NOT NULL,
    subject_email VARCHAR(254),
    subject_id UUID,
    status VARCHAR(30) NOT NULL DEFAULT 'received',
    details TEXT,
    assigned_to UUID,
    due_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    response_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_privacy_org_status ON privacy_requests(organization_id, status);

CREATE TABLE IF NOT EXISTS compliance_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    framework VARCHAR(30) NOT NULL,
    control_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}',
    remediation TEXT,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    next_check_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_compliance_org_framework ON compliance_checks(organization_id, framework);

CREATE TABLE IF NOT EXISTS vulnerability_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID,
    source VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    cve_id VARCHAR(30),
    cvss_score NUMERIC(3, 1),
    severity VARCHAR(20) NOT NULL,
    affected_component VARCHAR(500),
    affected_version VARCHAR(100),
    fixed_version VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    assigned_to UUID,
    discovered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    remediated_at TIMESTAMPTZ,
    remediation_notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_vuln_status_severity ON vulnerability_reports(status, severity);

CREATE TABLE IF NOT EXISTS security_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    source_event_ids JSONB NOT NULL DEFAULT '[]',
    incident_id UUID,
    acknowledged_by UUID,
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_sec_alerts_org_status ON security_alerts(organization_id, status);
CREATE INDEX IF NOT EXISTS ix_sec_alerts_severity ON security_alerts(severity);
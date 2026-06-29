-- Idempotent Phase 8 + hybrid orchestration schema bootstrap
-- Use when alembic upgrade fails on partial dev databases

ALTER TABLE workflows ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS run_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS orchestration_mode VARCHAR(30) NOT NULL DEFAULT 'event_driven';

ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(100);
ALTER TABLE workflow_executions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100);

CREATE INDEX IF NOT EXISTS ix_workflows_orchestration_mode ON workflows(orchestration_mode);
CREATE INDEX IF NOT EXISTS ix_workflow_executions_status ON workflow_executions(status);

CREATE TABLE IF NOT EXISTS workflow_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    canvas JSONB NOT NULL DEFAULT '{}',
    compiled_plan JSONB,
    changelog TEXT,
    published_at TIMESTAMPTZ,
    published_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (workflow_id, version_number)
);
CREATE INDEX IF NOT EXISTS ix_workflow_versions_workflow_id ON workflow_versions(workflow_id);

CREATE TABLE IF NOT EXISTS workflow_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    workflow_version_id UUID NOT NULL REFERENCES workflow_versions(id) ON DELETE CASCADE,
    node_key VARCHAR(100) NOT NULL,
    node_type VARCHAR(50) NOT NULL,
    label VARCHAR(255),
    config JSONB NOT NULL DEFAULT '{}',
    position JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (workflow_version_id, node_key)
);
CREATE INDEX IF NOT EXISTS ix_workflow_nodes_version_id ON workflow_nodes(workflow_version_id);

CREATE TABLE IF NOT EXISTS workflow_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    workflow_version_id UUID NOT NULL REFERENCES workflow_versions(id) ON DELETE CASCADE,
    source_node_key VARCHAR(100) NOT NULL,
    target_node_key VARCHAR(100) NOT NULL,
    condition JSONB,
    label VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_workflow_edges_version_id ON workflow_edges(workflow_version_id);

CREATE TABLE IF NOT EXISTS workflow_variables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    var_type VARCHAR(50) NOT NULL DEFAULT 'string',
    default_value JSONB,
    is_secret BOOLEAN NOT NULL DEFAULT false,
    scope VARCHAR(20) NOT NULL DEFAULT 'workflow',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (workflow_id, name)
);
CREATE INDEX IF NOT EXISTS ix_workflow_variables_workflow_id ON workflow_variables(workflow_id);

CREATE TABLE IF NOT EXISTS workflow_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    node_key VARCHAR(100),
    level VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_workflow_execution_logs_execution_id ON workflow_execution_logs(execution_id);
CREATE INDEX IF NOT EXISTS ix_workflow_execution_logs_created_at ON workflow_execution_logs(created_at);

CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    slug VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL DEFAULT 'general',
    canvas JSONB NOT NULL DEFAULT '{}',
    trigger_type VARCHAR(50) NOT NULL,
    orchestration_mode VARCHAR(30) NOT NULL DEFAULT 'event_driven',
    is_system BOOLEAN NOT NULL DEFAULT false,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_workflow_templates_slug ON workflow_templates(slug);
CREATE INDEX IF NOT EXISTS ix_workflow_templates_category ON workflow_templates(category);

CREATE TABLE IF NOT EXISTS workflow_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    schedule_type VARCHAR(20) NOT NULL,
    cron_expression VARCHAR(100),
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    config JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_workflow_schedules_workflow_id ON workflow_schedules(workflow_id);
CREATE INDEX IF NOT EXISTS ix_workflow_schedules_next_run ON workflow_schedules(next_run_at);

CREATE TABLE IF NOT EXISTS workflow_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    node_key VARCHAR(100) NOT NULL,
    approver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approval_type VARCHAR(30) NOT NULL DEFAULT 'sequential',
    comment TEXT,
    decided_at TIMESTAMPTZ,
    due_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_workflow_approvals_execution_id ON workflow_approvals(execution_id);
CREATE INDEX IF NOT EXISTS ix_workflow_approvals_status ON workflow_approvals(status);

CREATE TABLE IF NOT EXISTS workflow_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    correlation_id VARCHAR(100),
    idempotency_key VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_workflow_events_org_id ON workflow_events(organization_id);
CREATE INDEX IF NOT EXISTS ix_workflow_events_event_type ON workflow_events(event_type);
CREATE INDEX IF NOT EXISTS ix_workflow_events_correlation_id ON workflow_events(correlation_id);

CREATE TABLE IF NOT EXISTS workflow_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    principal_type VARCHAR(20) NOT NULL,
    principal_id UUID NOT NULL,
    permission VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (workflow_id, principal_type, principal_id, permission)
);
CREATE INDEX IF NOT EXISTS ix_workflow_permissions_workflow_id ON workflow_permissions(workflow_id);

CREATE TABLE IF NOT EXISTS workflow_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    metric_date TIMESTAMPTZ NOT NULL,
    runs_total INTEGER NOT NULL DEFAULT 0,
    runs_success INTEGER NOT NULL DEFAULT 0,
    runs_failed INTEGER NOT NULL DEFAULT 0,
    avg_duration_ms INTEGER,
    ai_nodes_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    UNIQUE (workflow_id, metric_date)
);
CREATE INDEX IF NOT EXISTS ix_workflow_metrics_workflow_date ON workflow_metrics(workflow_id, metric_date);

CREATE TABLE IF NOT EXISTS workflow_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    node_key VARCHAR(100),
    error_code VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    is_resolved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_workflow_errors_execution_id ON workflow_errors(execution_id);

UPDATE alembic_version SET version_num = '015' WHERE version_num = '013';
INSERT INTO alembic_version (version_num) SELECT '015' WHERE NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '015');
"""Phase 2: CRM, Analytics, and Connectors

Revision ID: 010
Revises: 009
Create Date: 2024-01-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    -- ============================================================
    -- CRM SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS crm.pipelines (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        description     TEXT,
        currency        CHAR(3) NOT NULL DEFAULT 'USD',
        is_default      BOOLEAN NOT NULL DEFAULT FALSE,
        is_active       BOOLEAN NOT NULL DEFAULT TRUE,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS crm.stages (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        pipeline_id     UUID NOT NULL REFERENCES crm.pipelines(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        position        INTEGER NOT NULL DEFAULT 0,
        probability     INTEGER NOT NULL DEFAULT 0 CHECK (probability BETWEEN 0 AND 100),
        stage_type      TEXT NOT NULL DEFAULT 'open' CHECK (stage_type IN ('open','won','lost')),
        color           TEXT,
        is_active       BOOLEAN NOT NULL DEFAULT TRUE,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS crm.deals (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        pipeline_id     UUID NOT NULL REFERENCES crm.pipelines(id),
        stage_id        UUID NOT NULL REFERENCES crm.stages(id),
        company_id      UUID REFERENCES core.companies(id),
        contact_id      UUID REFERENCES core.contacts(id),
        owner_id        UUID REFERENCES auth.users(id),
        name            TEXT NOT NULL,
        description     TEXT,
        amount          NUMERIC(20, 2),
        currency        CHAR(3) NOT NULL DEFAULT 'USD',
        probability     INTEGER CHECK (probability BETWEEN 0 AND 100),
        priority        TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low','medium','high','critical')),
        expected_close_date DATE,
        actual_close_date   DATE,
        lost_reason     TEXT,
        tags            TEXT[],
        fts             TSVECTOR GENERATED ALWAYS AS (
                            setweight(to_tsvector('english', coalesce(name,'')), 'A') ||
                            setweight(to_tsvector('english', coalesce(description,'')), 'B')
                        ) STORED,
        status          TEXT NOT NULL DEFAULT 'open',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_deals_fts ON crm.deals USING GIN(fts);
    CREATE INDEX IF NOT EXISTS idx_deals_pipeline_stage ON crm.deals(pipeline_id, stage_id) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_deals_owner_org ON crm.deals(owner_id, organization_id) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_deals_status_org ON crm.deals(status, organization_id, updated_at DESC) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_deals_close_date ON crm.deals(expected_close_date) WHERE deleted_at IS NULL;

    CREATE TABLE IF NOT EXISTS crm.activities (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id         UUID REFERENCES auth.users(id),
        entity_type     TEXT NOT NULL,
        entity_id       UUID NOT NULL,
        activity_type   TEXT NOT NULL CHECK (activity_type IN ('call','email','meeting','note','task','linkedin','sms','demo')),
        direction       TEXT CHECK (direction IN ('inbound','outbound')),
        subject         TEXT,
        body            TEXT,
        duration_secs   INTEGER,
        outcome         TEXT,
        occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (id, created_at)
    ) PARTITION BY RANGE (created_at);
    SELECT create_monthly_partition('crm.activities', NOW());
    SELECT create_monthly_partition('crm.activities', NOW() + INTERVAL '1 month');

    CREATE TABLE IF NOT EXISTS crm.tasks (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        owner_id        UUID REFERENCES auth.users(id),
        entity_type     TEXT,
        entity_id       UUID,
        title           TEXT NOT NULL,
        description     TEXT,
        due_at          TIMESTAMPTZ,
        reminder_at     TIMESTAMPTZ,
        priority        TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low','medium','high','critical')),
        completed_at    TIMESTAMPTZ,
        status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','in_progress','completed','cancelled','overdue')),
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_tasks_owner_status ON crm.tasks(owner_id, status) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON crm.tasks(due_at) WHERE deleted_at IS NULL AND completed_at IS NULL;

    CREATE TABLE IF NOT EXISTS crm.notes (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id         UUID REFERENCES auth.users(id),
        entity_type     TEXT NOT NULL,
        entity_id       UUID NOT NULL,
        title           TEXT,
        content         TEXT,
        rich_content    JSONB,
        is_pinned       BOOLEAN NOT NULL DEFAULT FALSE,
        is_private      BOOLEAN NOT NULL DEFAULT FALSE,
        fts             TSVECTOR GENERATED ALWAYS AS (
                            setweight(to_tsvector('english', coalesce(title,'')), 'A') ||
                            setweight(to_tsvector('english', coalesce(content,'')), 'B')
                        ) STORED,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_notes_fts ON crm.notes USING GIN(fts);
    CREATE INDEX IF NOT EXISTS idx_notes_entity ON crm.notes(entity_type, entity_id) WHERE deleted_at IS NULL;

    CREATE TABLE IF NOT EXISTS crm.meetings (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        organizer_id    UUID REFERENCES auth.users(id),
        entity_type     TEXT,
        entity_id       UUID,
        title           TEXT NOT NULL,
        description     TEXT,
        start_at        TIMESTAMPTZ NOT NULL,
        end_at          TIMESTAMPTZ NOT NULL,
        location        TEXT,
        meeting_url     TEXT,
        attendees       JSONB NOT NULL DEFAULT '[]',
        recording_url   TEXT,
        transcript      TEXT,
        outcome         TEXT,
        status          TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','completed','cancelled','no_show')),
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS crm.lists (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        owner_id        UUID REFERENCES auth.users(id),
        name            TEXT NOT NULL,
        description     TEXT,
        list_type       TEXT NOT NULL DEFAULT 'static' CHECK (list_type IN ('static','dynamic')),
        entity_type     TEXT NOT NULL DEFAULT 'company',
        filters         JSONB NOT NULL DEFAULT '{}',
        item_count      INTEGER NOT NULL DEFAULT 0,
        last_computed_at TIMESTAMPTZ,
        is_shared       BOOLEAN NOT NULL DEFAULT FALSE,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS crm.list_items (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        list_id         UUID NOT NULL REFERENCES crm.lists(id) ON DELETE CASCADE,
        entity_type     TEXT NOT NULL,
        entity_id       UUID NOT NULL,
        added_by        UUID,
        sort_order      INTEGER,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(list_id, entity_type, entity_id)
    );

    CREATE TABLE IF NOT EXISTS crm.segments (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        description     TEXT,
        entity_type     TEXT NOT NULL DEFAULT 'company',
        filters         JSONB NOT NULL DEFAULT '{}',
        member_count    INTEGER NOT NULL DEFAULT 0,
        last_computed_at TIMESTAMPTZ,
        is_active       BOOLEAN NOT NULL DEFAULT TRUE,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS crm.workflows (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        description     TEXT,
        trigger_type    TEXT NOT NULL,
        trigger_config  JSONB NOT NULL DEFAULT '{}',
        conditions      JSONB NOT NULL DEFAULT '[]',
        actions         JSONB NOT NULL DEFAULT '[]',
        is_active       BOOLEAN NOT NULL DEFAULT FALSE,
        run_count       INTEGER NOT NULL DEFAULT 0,
        last_run_at     TIMESTAMPTZ,
        status          TEXT NOT NULL DEFAULT 'draft',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS crm.automation_logs (
        id                  UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        workflow_id         UUID NOT NULL REFERENCES crm.workflows(id) ON DELETE CASCADE,
        entity_type         TEXT,
        entity_id           UUID,
        trigger_data        JSONB NOT NULL DEFAULT '{}',
        actions_executed    JSONB[] NOT NULL DEFAULT '{}',
        error_message       TEXT,
        duration_ms         INTEGER,
        status              TEXT NOT NULL DEFAULT 'success',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (id, created_at)
    ) PARTITION BY RANGE (created_at);
    SELECT create_monthly_partition('crm.automation_logs', NOW());
    SELECT create_monthly_partition('crm.automation_logs', NOW() + INTERVAL '1 month');

    CREATE TABLE IF NOT EXISTS crm.tags (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        color           TEXT,
        entity_types    TEXT[] NOT NULL DEFAULT '{}',
        use_count       INTEGER NOT NULL DEFAULT 0,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, name)
    );

    CREATE TABLE IF NOT EXISTS crm.attachments (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        entity_type     TEXT NOT NULL,
        entity_id       UUID NOT NULL,
        file_name       TEXT NOT NULL,
        storage_key     TEXT NOT NULL,
        storage_bucket  TEXT NOT NULL,
        mime_type       TEXT,
        file_size       BIGINT,
        uploaded_by     UUID,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    -- ============================================================
    -- CONNECTOR SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS connector.connectors (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        name                TEXT NOT NULL UNIQUE,
        display_name        TEXT NOT NULL,
        description         TEXT,
        connector_type      TEXT NOT NULL,
        supports_search     BOOLEAN NOT NULL DEFAULT FALSE,
        supports_enrich     BOOLEAN NOT NULL DEFAULT FALSE,
        supports_sync       BOOLEAN NOT NULL DEFAULT FALSE,
        rate_limit_rpm      INTEGER NOT NULL DEFAULT 60,
        credit_cost         INTEGER NOT NULL DEFAULT 1,
        config_schema       JSONB NOT NULL DEFAULT '{}',
        is_active           BOOLEAN NOT NULL DEFAULT TRUE,
        is_system           BOOLEAN NOT NULL DEFAULT FALSE,
        logo_url            TEXT,
        docs_url            TEXT,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS connector.connector_configs (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        connector_id    UUID NOT NULL REFERENCES connector.connectors(id),
        credentials     JSONB NOT NULL DEFAULT '{}',
        config          JSONB NOT NULL DEFAULT '{}',
        is_active       BOOLEAN NOT NULL DEFAULT TRUE,
        last_sync_at    TIMESTAMPTZ,
        sync_status     TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, connector_id)
    );

    CREATE TABLE IF NOT EXISTS connector.connector_jobs (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        config_id       UUID NOT NULL REFERENCES connector.connector_configs(id),
        job_type        TEXT NOT NULL,
        entity_type     TEXT,
        entity_id       UUID,
        payload         JSONB NOT NULL DEFAULT '{}',
        result          JSONB,
        error_message   TEXT,
        retry_count     INTEGER NOT NULL DEFAULT 0,
        max_retries     INTEGER NOT NULL DEFAULT 3,
        next_retry_at   TIMESTAMPTZ,
        started_at      TIMESTAMPTZ,
        completed_at    TIMESTAMPTZ,
        credits_used    INTEGER NOT NULL DEFAULT 0,
        status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','failed','retrying','cancelled')),
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS connector.connector_logs (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        config_id       UUID NOT NULL REFERENCES connector.connector_configs(id),
        job_id          UUID,
        method          TEXT,
        path            TEXT,
        http_status     INTEGER,
        request_data    JSONB,
        response_data   JSONB,
        duration_ms     INTEGER,
        error_message   TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (id, created_at)
    ) PARTITION BY RANGE (created_at);
    SELECT create_monthly_partition('connector.connector_logs', NOW());
    SELECT create_monthly_partition('connector.connector_logs', NOW() + INTERVAL '1 month');

    CREATE TABLE IF NOT EXISTS connector.connector_rate_limits (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        config_id       UUID NOT NULL REFERENCES connector.connector_configs(id) ON DELETE CASCADE,
        window_type     TEXT NOT NULL CHECK (window_type IN ('minute','hour','day')),
        window_start    TIMESTAMPTZ NOT NULL,
        request_count   INTEGER NOT NULL DEFAULT 0,
        limit_value     INTEGER NOT NULL,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(config_id, window_type, window_start)
    );

    CREATE TABLE IF NOT EXISTS connector.connector_cache (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        connector_id    UUID NOT NULL REFERENCES connector.connectors(id),
        cache_key       TEXT NOT NULL,
        response_data   JSONB NOT NULL DEFAULT '{}',
        expires_at      TIMESTAMPTZ NOT NULL,
        hit_count       INTEGER NOT NULL DEFAULT 0,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(connector_id, cache_key)
    );
    CREATE INDEX IF NOT EXISTS idx_connector_cache_expires ON connector.connector_cache(expires_at);

    -- ============================================================
    -- ANALYTICS SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS analytics.dashboard_metrics (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        metric_key      TEXT NOT NULL,
        period_type     TEXT NOT NULL CHECK (period_type IN ('day','week','month','quarter','year')),
        period_start    DATE NOT NULL,
        period_end      DATE NOT NULL,
        value           NUMERIC(20, 4) NOT NULL DEFAULT 0,
        previous_value  NUMERIC(20, 4),
        change_pct      NUMERIC(8, 4),
        breakdown       JSONB NOT NULL DEFAULT '{}',
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, metric_key, period_type, period_start)
    );

    CREATE TABLE IF NOT EXISTS analytics.company_statistics (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        period_date     DATE NOT NULL,
        total_companies INTEGER NOT NULL DEFAULT 0,
        new_companies   INTEGER NOT NULL DEFAULT 0,
        enriched_count  INTEGER NOT NULL DEFAULT 0,
        verified_count  INTEGER NOT NULL DEFAULT 0,
        by_industry     JSONB NOT NULL DEFAULT '{}',
        by_country      JSONB NOT NULL DEFAULT '{}',
        by_size         JSONB NOT NULL DEFAULT '{}',
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, period_date)
    );

    CREATE TABLE IF NOT EXISTS analytics.contact_statistics (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        period_date     DATE NOT NULL,
        total_contacts  INTEGER NOT NULL DEFAULT 0,
        new_contacts    INTEGER NOT NULL DEFAULT 0,
        enriched_count  INTEGER NOT NULL DEFAULT 0,
        decision_makers INTEGER NOT NULL DEFAULT 0,
        by_seniority    JSONB NOT NULL DEFAULT '{}',
        by_department   JSONB NOT NULL DEFAULT '{}',
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, period_date)
    );

    CREATE TABLE IF NOT EXISTS analytics.usage_statistics (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        period_date     DATE NOT NULL,
        searches        INTEGER NOT NULL DEFAULT 0,
        exports         INTEGER NOT NULL DEFAULT 0,
        enrichments     INTEGER NOT NULL DEFAULT 0,
        api_calls       INTEGER NOT NULL DEFAULT 0,
        credits_used    INTEGER NOT NULL DEFAULT 0,
        active_users    INTEGER NOT NULL DEFAULT 0,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, period_date)
    );

    CREATE TABLE IF NOT EXISTS analytics.api_statistics (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        period_date     DATE NOT NULL,
        total_requests  INTEGER NOT NULL DEFAULT 0,
        success_count   INTEGER NOT NULL DEFAULT 0,
        error_count     INTEGER NOT NULL DEFAULT 0,
        avg_latency_ms  NUMERIC(10,2),
        by_endpoint     JSONB NOT NULL DEFAULT '{}',
        by_status_code  JSONB NOT NULL DEFAULT '{}',
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, period_date)
    );

    -- Triggers
    CREATE OR REPLACE TRIGGER trg_pipelines_updated_at BEFORE UPDATE ON crm.pipelines FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_stages_updated_at BEFORE UPDATE ON crm.stages FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_deals_updated_at BEFORE UPDATE ON crm.deals FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_tasks_updated_at BEFORE UPDATE ON crm.tasks FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_notes_updated_at BEFORE UPDATE ON crm.notes FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_meetings_updated_at BEFORE UPDATE ON crm.meetings FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_lists_updated_at BEFORE UPDATE ON crm.lists FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_workflows_updated_at BEFORE UPDATE ON crm.workflows FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_connectors_updated_at BEFORE UPDATE ON connector.connectors FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_connector_configs_updated_at BEFORE UPDATE ON connector.connector_configs FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_connector_jobs_updated_at BEFORE UPDATE ON connector.connector_jobs FOR EACH ROW EXECUTE FUNCTION set_updated_at();

    -- RLS
    ALTER TABLE crm.deals ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS deals_org_isolation ON crm.deals;
    CREATE POLICY deals_org_isolation ON crm.deals USING (organization_id = current_org_id());

    ALTER TABLE crm.notes ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS notes_org_isolation ON crm.notes;
    CREATE POLICY notes_org_isolation ON crm.notes USING (organization_id = current_org_id());

    ALTER TABLE crm.tasks ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tasks_org_isolation ON crm.tasks;
    CREATE POLICY tasks_org_isolation ON crm.tasks USING (organization_id = current_org_id());

    ALTER TABLE crm.lists ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS lists_org_isolation ON crm.lists;
    CREATE POLICY lists_org_isolation ON crm.lists USING (organization_id = current_org_id());
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS analytics.api_statistics CASCADE;
    DROP TABLE IF EXISTS analytics.usage_statistics CASCADE;
    DROP TABLE IF EXISTS analytics.contact_statistics CASCADE;
    DROP TABLE IF EXISTS analytics.company_statistics CASCADE;
    DROP TABLE IF EXISTS analytics.dashboard_metrics CASCADE;
    DROP TABLE IF EXISTS connector.connector_cache CASCADE;
    DROP TABLE IF EXISTS connector.connector_rate_limits CASCADE;
    DROP TABLE IF EXISTS connector.connector_logs CASCADE;
    DROP TABLE IF EXISTS connector.connector_jobs CASCADE;
    DROP TABLE IF EXISTS connector.connector_configs CASCADE;
    DROP TABLE IF EXISTS connector.connectors CASCADE;
    DROP TABLE IF EXISTS crm.attachments CASCADE;
    DROP TABLE IF EXISTS crm.tags CASCADE;
    DROP TABLE IF EXISTS crm.automation_logs CASCADE;
    DROP TABLE IF EXISTS crm.workflows CASCADE;
    DROP TABLE IF EXISTS crm.segments CASCADE;
    DROP TABLE IF EXISTS crm.list_items CASCADE;
    DROP TABLE IF EXISTS crm.lists CASCADE;
    DROP TABLE IF EXISTS crm.meetings CASCADE;
    DROP TABLE IF EXISTS crm.notes CASCADE;
    DROP TABLE IF EXISTS crm.tasks CASCADE;
    DROP TABLE IF EXISTS crm.activities CASCADE;
    DROP TABLE IF EXISTS crm.deals CASCADE;
    DROP TABLE IF EXISTS crm.stages CASCADE;
    DROP TABLE IF EXISTS crm.pipelines CASCADE;
    """)

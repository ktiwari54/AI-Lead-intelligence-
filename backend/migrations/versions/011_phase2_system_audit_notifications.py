"""Phase 2: System, Audit, Notifications, and Export/Import

Revision ID: 011
Revises: 010
Create Date: 2024-01-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    -- ============================================================
    -- SYSTEM SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS system.feature_flags (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        key                 TEXT NOT NULL UNIQUE,
        description         TEXT,
        is_enabled          BOOLEAN NOT NULL DEFAULT FALSE,
        rollout_percent     INTEGER NOT NULL DEFAULT 0 CHECK (rollout_percent BETWEEN 0 AND 100),
        allowed_orgs        UUID[] NOT NULL DEFAULT '{}',
        blocked_orgs        UUID[] NOT NULL DEFAULT '{}',
        conditions          JSONB NOT NULL DEFAULT '{}',
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS system.system_settings (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID,
        category        TEXT NOT NULL,
        key             TEXT NOT NULL,
        value           JSONB NOT NULL,
        data_type       TEXT NOT NULL DEFAULT 'string',
        is_sensitive    BOOLEAN NOT NULL DEFAULT FALSE,
        description     TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(category, key)
    );

    CREATE TABLE IF NOT EXISTS system.files (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID REFERENCES auth.organizations(id) ON DELETE CASCADE,
        file_name       TEXT NOT NULL,
        original_name   TEXT,
        storage_key     TEXT NOT NULL,
        storage_bucket  TEXT NOT NULL,
        storage_provider TEXT NOT NULL DEFAULT 's3',
        mime_type       TEXT,
        file_size       BIGINT,
        checksum        TEXT,
        is_public       BOOLEAN NOT NULL DEFAULT FALSE,
        url_expires_at  TIMESTAMPTZ,
        entity_type     TEXT,
        entity_id       UUID,
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

    CREATE TABLE IF NOT EXISTS system.templates (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        template_type   TEXT NOT NULL CHECK (template_type IN ('email','export','report','notification','document')),
        subject         TEXT,
        body            TEXT,
        variables       JSONB NOT NULL DEFAULT '[]',
        is_system       BOOLEAN NOT NULL DEFAULT FALSE,
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

    CREATE TABLE IF NOT EXISTS system.webhooks (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        url             TEXT NOT NULL,
        events          TEXT[] NOT NULL DEFAULT '{}',
        secret          TEXT,
        retry_count     INTEGER NOT NULL DEFAULT 3,
        timeout_seconds INTEGER NOT NULL DEFAULT 30,
        failure_count   INTEGER NOT NULL DEFAULT 0,
        last_triggered_at TIMESTAMPTZ,
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

    CREATE TABLE IF NOT EXISTS system.webhook_logs (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        webhook_id      UUID NOT NULL REFERENCES system.webhooks(id) ON DELETE CASCADE,
        event_type      TEXT NOT NULL,
        payload         JSONB NOT NULL DEFAULT '{}',
        http_status     INTEGER,
        response_body   TEXT,
        attempt_count   INTEGER NOT NULL DEFAULT 1,
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
    SELECT create_monthly_partition('system.webhook_logs', NOW());
    SELECT create_monthly_partition('system.webhook_logs', NOW() + INTERVAL '1 month');

    CREATE TABLE IF NOT EXISTS system.rate_limits (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        identifier          TEXT NOT NULL,
        identifier_type     TEXT NOT NULL CHECK (identifier_type IN ('ip','user','org','api_key')),
        endpoint            TEXT NOT NULL,
        window_type         TEXT NOT NULL CHECK (window_type IN ('second','minute','hour','day')),
        window_start        TIMESTAMPTZ NOT NULL,
        request_count       INTEGER NOT NULL DEFAULT 0,
        limit_value         INTEGER NOT NULL,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        UNIQUE(identifier, identifier_type, endpoint, window_type, window_start)
    );

    CREATE TABLE IF NOT EXISTS system.scheduled_jobs (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID,
        name            TEXT NOT NULL,
        job_type        TEXT NOT NULL,
        cron_expression TEXT NOT NULL,
        payload         JSONB NOT NULL DEFAULT '{}',
        next_run_at     TIMESTAMPTZ NOT NULL,
        last_run_at     TIMESTAMPTZ,
        last_run_status TEXT,
        last_error      TEXT,
        run_count       INTEGER NOT NULL DEFAULT 0,
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
    CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_next_run ON system.scheduled_jobs(next_run_at) WHERE is_active = TRUE;

    -- ============================================================
    -- NOTIFICATION SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS notification.notification_types (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID,
        key             TEXT NOT NULL UNIQUE,
        display_name    TEXT NOT NULL,
        description     TEXT,
        channels        TEXT[] NOT NULL DEFAULT '{in_app}',
        template_id     UUID REFERENCES system.templates(id),
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

    CREATE TABLE IF NOT EXISTS notification.notifications (
        id                  UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        notification_type_id UUID REFERENCES notification.notification_types(id),
        title               TEXT NOT NULL,
        body                TEXT,
        action_url          TEXT,
        actor_id            UUID,
        entity_type         TEXT,
        entity_id           UUID,
        channel             TEXT NOT NULL DEFAULT 'in_app',
        is_read             BOOLEAN NOT NULL DEFAULT FALSE,
        read_at             TIMESTAMPTZ,
        is_dismissed        BOOLEAN NOT NULL DEFAULT FALSE,
        dismissed_at        TIMESTAMPTZ,
        expires_at          TIMESTAMPTZ,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (id, created_at)
    ) PARTITION BY RANGE (created_at);
    SELECT create_monthly_partition('notification.notifications', NOW());
    SELECT create_monthly_partition('notification.notifications', NOW() + INTERVAL '1 month');
    CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notification.notifications(user_id, created_at DESC) WHERE is_read = FALSE;
    CREATE INDEX IF NOT EXISTS idx_notifications_user_undismissed ON notification.notifications(user_id, created_at DESC) WHERE is_dismissed = FALSE;

    CREATE TABLE IF NOT EXISTS notification.notification_preferences (
        id                      UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id         UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id                 UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
        notification_type_id    UUID NOT NULL REFERENCES notification.notification_types(id),
        in_app_enabled          BOOLEAN NOT NULL DEFAULT TRUE,
        email_enabled           BOOLEAN NOT NULL DEFAULT TRUE,
        sms_enabled             BOOLEAN NOT NULL DEFAULT FALSE,
        push_enabled            BOOLEAN NOT NULL DEFAULT FALSE,
        status                  TEXT NOT NULL DEFAULT 'active',
        metadata                JSONB NOT NULL DEFAULT '{}',
        created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at              TIMESTAMPTZ,
        created_by              UUID,
        updated_by              UUID,
        version                 INTEGER NOT NULL DEFAULT 1,
        UNIQUE(user_id, notification_type_id)
    );

    CREATE TABLE IF NOT EXISTS notification.notification_queue (
        id                  UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id             UUID REFERENCES auth.users(id),
        notification_type_id UUID REFERENCES notification.notification_types(id),
        channel             TEXT NOT NULL,
        recipient           TEXT NOT NULL,
        subject             TEXT,
        body                TEXT NOT NULL,
        template_data       JSONB NOT NULL DEFAULT '{}',
        scheduled_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        sent_at             TIMESTAMPTZ,
        attempt_count       INTEGER NOT NULL DEFAULT 0,
        max_attempts        INTEGER NOT NULL DEFAULT 3,
        next_attempt_at     TIMESTAMPTZ,
        error_message       TEXT,
        status              TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','sent','failed','cancelled')),
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (id, created_at)
    ) PARTITION BY RANGE (created_at);
    SELECT create_monthly_partition('notification.notification_queue', NOW());
    SELECT create_monthly_partition('notification.notification_queue', NOW() + INTERVAL '1 month');
    CREATE INDEX IF NOT EXISTS idx_notification_queue_pending ON notification.notification_queue(next_attempt_at)
        WHERE status IN ('pending', 'retry');

    -- ============================================================
    -- EXPORT / IMPORT SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS export.exports (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id         UUID REFERENCES auth.users(id),
        export_type     TEXT NOT NULL,
        format          TEXT NOT NULL CHECK (format IN ('csv','xlsx','json','parquet')),
        filters         JSONB NOT NULL DEFAULT '{}',
        columns         TEXT[],
        row_count       INTEGER,
        file_key        TEXT,
        download_url    TEXT,
        url_expires_at  TIMESTAMPTZ,
        credits_used    INTEGER NOT NULL DEFAULT 0,
        error_message   TEXT,
        started_at      TIMESTAMPTZ,
        completed_at    TIMESTAMPTZ,
        status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','completed','failed','expired')),
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS export.export_templates (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        export_type     TEXT NOT NULL,
        format          TEXT NOT NULL,
        filters         JSONB NOT NULL DEFAULT '{}',
        columns         TEXT[],
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

    CREATE TABLE IF NOT EXISTS export.imports (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id             UUID REFERENCES auth.users(id),
        import_type         TEXT NOT NULL,
        file_key            TEXT NOT NULL,
        file_name           TEXT,
        format              TEXT NOT NULL CHECK (format IN ('csv','xlsx','json')),
        column_mapping      JSONB NOT NULL DEFAULT '{}',
        total_rows          INTEGER NOT NULL DEFAULT 0,
        processed_rows      INTEGER NOT NULL DEFAULT 0,
        created_rows        INTEGER NOT NULL DEFAULT 0,
        updated_rows        INTEGER NOT NULL DEFAULT 0,
        skipped_rows        INTEGER NOT NULL DEFAULT 0,
        error_rows          INTEGER NOT NULL DEFAULT 0,
        validation_errors   JSONB[] NOT NULL DEFAULT '{}',
        started_at          TIMESTAMPTZ,
        completed_at        TIMESTAMPTZ,
        error_message       TEXT,
        status              TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','validating','processing','completed','failed','cancelled')),
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS export.import_rows (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        import_id       UUID NOT NULL REFERENCES export.imports(id) ON DELETE CASCADE,
        row_number      INTEGER NOT NULL,
        raw_data        JSONB NOT NULL DEFAULT '{}',
        mapped_data     JSONB NOT NULL DEFAULT '{}',
        entity_id       UUID,
        action          TEXT CHECK (action IN ('created','updated','skipped','error')),
        error_messages  TEXT[],
        status          TEXT NOT NULL DEFAULT 'pending',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_import_rows_import ON export.import_rows(import_id, row_number);

    -- ============================================================
    -- AUDIT SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS audit.audit_logs (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL,
        user_id         UUID,
        action          TEXT NOT NULL,
        resource_type   TEXT NOT NULL,
        resource_id     UUID,
        old_values      JSONB,
        new_values      JSONB,
        ip_address      INET,
        user_agent      TEXT,
        request_id      UUID,
        duration_ms     INTEGER,
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
    SELECT create_monthly_partition('audit.audit_logs', NOW());
    SELECT create_monthly_partition('audit.audit_logs', NOW() + INTERVAL '1 month');
    CREATE INDEX IF NOT EXISTS idx_audit_logs_brin ON audit.audit_logs USING BRIN(created_at);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit.audit_logs(resource_type, resource_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_org_user ON audit.audit_logs(organization_id, user_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS audit.api_logs (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL,
        user_id         UUID,
        api_key_id      UUID,
        method          TEXT NOT NULL,
        path            TEXT NOT NULL,
        query_params    JSONB,
        request_body    JSONB,
        response_status INTEGER,
        response_body   JSONB,
        ip_address      INET,
        user_agent      TEXT,
        duration_ms     INTEGER,
        credits_used    INTEGER NOT NULL DEFAULT 0,
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
    SELECT create_monthly_partition('audit.api_logs', NOW());
    SELECT create_monthly_partition('audit.api_logs', NOW() + INTERVAL '1 month');
    CREATE INDEX IF NOT EXISTS idx_api_logs_path ON audit.api_logs(path, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_api_logs_api_key ON audit.api_logs(api_key_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_api_logs_org ON audit.api_logs(organization_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS audit.security_logs (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID,
        user_id         UUID,
        event_type      TEXT NOT NULL,
        severity        TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('debug','info','warning','error','critical')),
        description     TEXT,
        ip_address      INET,
        user_agent      TEXT,
        details         JSONB NOT NULL DEFAULT '{}',
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
    SELECT create_monthly_partition('audit.security_logs', NOW());
    SELECT create_monthly_partition('audit.security_logs', NOW() + INTERVAL '1 month');

    CREATE TABLE IF NOT EXISTS audit.entity_history (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL,
        entity_type     TEXT NOT NULL,
        entity_id       UUID NOT NULL,
        action          TEXT NOT NULL CHECK (action IN ('created','updated','deleted','restored')),
        snapshot        JSONB NOT NULL DEFAULT '{}',
        changed_fields  TEXT[],
        changed_by      UUID,
        change_source   TEXT,
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
    SELECT create_monthly_partition('audit.entity_history', NOW());
    SELECT create_monthly_partition('audit.entity_history', NOW() + INTERVAL '1 month');
    CREATE INDEX IF NOT EXISTS idx_entity_history_entity ON audit.entity_history(entity_type, entity_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_entity_history_org ON audit.entity_history(organization_id, created_at DESC);

    -- Triggers
    CREATE OR REPLACE TRIGGER trg_feature_flags_updated_at BEFORE UPDATE ON system.feature_flags FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_system_settings_updated_at BEFORE UPDATE ON system.system_settings FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_webhooks_updated_at BEFORE UPDATE ON system.webhooks FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_templates_updated_at BEFORE UPDATE ON system.templates FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_notification_types_updated_at BEFORE UPDATE ON notification.notification_types FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_notification_preferences_updated_at BEFORE UPDATE ON notification.notification_preferences FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_exports_updated_at BEFORE UPDATE ON export.exports FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_imports_updated_at BEFORE UPDATE ON export.imports FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_import_rows_updated_at BEFORE UPDATE ON export.import_rows FOR EACH ROW EXECUTE FUNCTION set_updated_at();

    -- RLS
    ALTER TABLE export.exports ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS exports_org_isolation ON export.exports;
    CREATE POLICY exports_org_isolation ON export.exports USING (organization_id = current_org_id());

    ALTER TABLE export.imports ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS imports_org_isolation ON export.imports;
    CREATE POLICY imports_org_isolation ON export.imports USING (organization_id = current_org_id());

    ALTER TABLE system.webhooks ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS webhooks_org_isolation ON system.webhooks;
    CREATE POLICY webhooks_org_isolation ON system.webhooks USING (organization_id = current_org_id());
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS audit.entity_history CASCADE;
    DROP TABLE IF EXISTS audit.security_logs CASCADE;
    DROP TABLE IF EXISTS audit.api_logs CASCADE;
    DROP TABLE IF EXISTS audit.audit_logs CASCADE;
    DROP TABLE IF EXISTS export.import_rows CASCADE;
    DROP TABLE IF EXISTS export.imports CASCADE;
    DROP TABLE IF EXISTS export.export_templates CASCADE;
    DROP TABLE IF EXISTS export.exports CASCADE;
    DROP TABLE IF EXISTS notification.notification_queue CASCADE;
    DROP TABLE IF EXISTS notification.notification_preferences CASCADE;
    DROP TABLE IF EXISTS notification.notifications CASCADE;
    DROP TABLE IF EXISTS notification.notification_types CASCADE;
    DROP TABLE IF EXISTS system.scheduled_jobs CASCADE;
    DROP TABLE IF EXISTS system.rate_limits CASCADE;
    DROP TABLE IF EXISTS system.webhook_logs CASCADE;
    DROP TABLE IF EXISTS system.webhooks CASCADE;
    DROP TABLE IF EXISTS system.templates CASCADE;
    DROP TABLE IF EXISTS system.files CASCADE;
    DROP TABLE IF EXISTS system.system_settings CASCADE;
    DROP TABLE IF EXISTS system.feature_flags CASCADE;
    """)

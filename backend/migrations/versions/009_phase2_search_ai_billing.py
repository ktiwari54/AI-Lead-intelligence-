"""Phase 2: Search, AI, and Billing

Revision ID: 009
Revises: 008
Create Date: 2024-01-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    -- ============================================================
    -- SEARCH SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS search.search_requests (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id         UUID REFERENCES auth.users(id),
        search_type     TEXT NOT NULL DEFAULT 'company',
        query           TEXT,
        filters         JSONB NOT NULL DEFAULT '{}',
        sort_by         TEXT,
        sort_dir        TEXT DEFAULT 'desc',
        page            INTEGER NOT NULL DEFAULT 1,
        page_size       INTEGER NOT NULL DEFAULT 25,
        result_count    INTEGER,
        execution_ms    INTEGER,
        cache_hit       BOOLEAN NOT NULL DEFAULT FALSE,
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
    SELECT create_monthly_partition('search.search_requests', NOW());
    SELECT create_monthly_partition('search.search_requests', NOW() + INTERVAL '1 month');
    CREATE INDEX IF NOT EXISTS idx_search_requests_filters ON search.search_requests USING GIN(filters);
    CREATE INDEX IF NOT EXISTS idx_search_requests_org ON search.search_requests(organization_id, created_at DESC);

    CREATE TABLE IF NOT EXISTS search.search_filters (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        filter_type     TEXT NOT NULL,
        filter_operator TEXT NOT NULL CHECK (filter_operator IN ('eq','neq','gt','lt','gte','lte','in','nin','contains','not_contains','between')),
        display_label   TEXT,
        is_active       BOOLEAN NOT NULL DEFAULT TRUE,
        sort_order      INTEGER NOT NULL DEFAULT 0,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS search.saved_searches (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id         UUID REFERENCES auth.users(id),
        name            TEXT NOT NULL,
        search_type     TEXT NOT NULL DEFAULT 'company',
        query           TEXT,
        filters         JSONB NOT NULL DEFAULT '{}',
        sort_by         TEXT,
        sort_dir        TEXT DEFAULT 'desc',
        alert_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
        alert_frequency TEXT,
        last_alerted_at TIMESTAMPTZ,
        is_shared       BOOLEAN NOT NULL DEFAULT FALSE,
        use_count       INTEGER NOT NULL DEFAULT 0,
        last_used_at    TIMESTAMPTZ,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS search.scheduled_searches (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        saved_search_id UUID NOT NULL REFERENCES search.saved_searches(id) ON DELETE CASCADE,
        cron_expression TEXT NOT NULL,
        next_run_at     TIMESTAMPTZ NOT NULL,
        last_run_at     TIMESTAMPTZ,
        last_result_count INTEGER,
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
    CREATE INDEX IF NOT EXISTS idx_scheduled_searches_next_run ON search.scheduled_searches(next_run_at) WHERE is_active = TRUE;

    CREATE TABLE IF NOT EXISTS search.search_cache (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        cache_key       TEXT NOT NULL,
        search_type     TEXT NOT NULL,
        query_hash      TEXT NOT NULL,
        result_data     JSONB NOT NULL DEFAULT '{}',
        result_count    INTEGER NOT NULL DEFAULT 0,
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
        UNIQUE(cache_key)
    );
    CREATE INDEX IF NOT EXISTS idx_search_cache_expires ON search.search_cache(expires_at);

    CREATE TABLE IF NOT EXISTS search.search_statistics (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        period_date     DATE NOT NULL,
        search_type     TEXT NOT NULL,
        total_searches  INTEGER NOT NULL DEFAULT 0,
        unique_queries  INTEGER NOT NULL DEFAULT 0,
        cache_hits      INTEGER NOT NULL DEFAULT 0,
        avg_results     NUMERIC(10,2),
        avg_exec_ms     NUMERIC(10,2),
        credits_used    INTEGER NOT NULL DEFAULT 0,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, period_date, search_type)
    );

    CREATE TABLE IF NOT EXISTS search.query_embeddings (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        query_hash      TEXT NOT NULL,
        query_text      TEXT NOT NULL,
        embedding       vector(1536),
        model           TEXT NOT NULL DEFAULT 'text-embedding-3-small',
        use_count       INTEGER NOT NULL DEFAULT 1,
        last_used_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, query_hash)
    );
    CREATE INDEX IF NOT EXISTS idx_query_embeddings_hnsw ON search.query_embeddings
        USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

    -- ============================================================
    -- AI SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS ai.ai_models (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID,
        provider        TEXT NOT NULL,
        model_id        TEXT NOT NULL UNIQUE,
        model_type      TEXT NOT NULL CHECK (model_type IN ('embedding','completion','scoring','classification')),
        display_name    TEXT NOT NULL,
        input_dims      INTEGER,
        output_dims     INTEGER,
        max_tokens      INTEGER,
        cost_per_token  NUMERIC(12, 8),
        config          JSONB NOT NULL DEFAULT '{}',
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

    CREATE TABLE IF NOT EXISTS ai.embeddings (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        entity_type     TEXT NOT NULL CHECK (entity_type IN ('company','contact','deal','note','search_query')),
        entity_id       UUID NOT NULL,
        embedding       vector(1536) NOT NULL,
        model_id        TEXT NOT NULL DEFAULT 'text-embedding-3-small',
        checksum        TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, entity_type, entity_id)
    );
    CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw ON ai.embeddings
        USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

    CREATE TABLE IF NOT EXISTS ai.lead_scores (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        entity_type     TEXT NOT NULL CHECK (entity_type IN ('company','contact')),
        entity_id       UUID NOT NULL,
        overall_score   INTEGER NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
        quality_score   INTEGER CHECK (quality_score BETWEEN 0 AND 100),
        fit_score       INTEGER CHECK (fit_score BETWEEN 0 AND 100),
        intent_score    INTEGER CHECK (intent_score BETWEEN 0 AND 100),
        engagement_score INTEGER CHECK (engagement_score BETWEEN 0 AND 100),
        timing_score    INTEGER CHECK (timing_score BETWEEN 0 AND 100),
        recommendation  TEXT NOT NULL CHECK (recommendation IN ('hot','warm','cold','not_a_fit')),
        score_reasons   JSONB NOT NULL DEFAULT '[]',
        model_id        TEXT NOT NULL DEFAULT 'claude-haiku-4-5-20251001',
        query_embedding vector(1536),
        scored_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        expires_at      TIMESTAMPTZ,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, entity_type, entity_id)
    );

    CREATE TABLE IF NOT EXISTS ai.recommendations (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        user_id             UUID REFERENCES auth.users(id),
        recommendation_type TEXT NOT NULL,
        entity_type         TEXT NOT NULL,
        seed_entity_id      UUID,
        recommended_ids     UUID[] NOT NULL DEFAULT '{}',
        accepted_ids        UUID[] NOT NULL DEFAULT '{}',
        dismissed_ids       UUID[] NOT NULL DEFAULT '{}',
        model_id            TEXT NOT NULL DEFAULT 'claude-haiku-4-5-20251001',
        expires_at          TIMESTAMPTZ,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS ai.duplicates (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        entity_type     TEXT NOT NULL CHECK (entity_type IN ('company','contact')),
        entity_id_a     UUID NOT NULL,
        entity_id_b     UUID NOT NULL,
        similarity      NUMERIC(5,4) NOT NULL CHECK (similarity BETWEEN 0 AND 1),
        match_fields    TEXT[] NOT NULL DEFAULT '{}',
        resolution      TEXT CHECK (resolution IN ('merge','keep_both','ignore')),
        resolved_by     UUID,
        resolved_at     TIMESTAMPTZ,
        status          TEXT NOT NULL DEFAULT 'pending',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, entity_type, entity_id_a, entity_id_b)
    );

    CREATE TABLE IF NOT EXISTS ai.ai_predictions (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        entity_type         TEXT NOT NULL,
        entity_id           UUID NOT NULL,
        prediction_type     TEXT NOT NULL CHECK (prediction_type IN ('churn_risk','upsell_potential','deal_close_probability','contact_response_rate')),
        prediction_value    NUMERIC(8,4) NOT NULL,
        confidence          NUMERIC(5,4) CHECK (confidence BETWEEN 0 AND 1),
        model_id            TEXT NOT NULL DEFAULT 'claude-haiku-4-5-20251001',
        feature_importance  JSONB NOT NULL DEFAULT '{}',
        predicted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        expires_at          TIMESTAMPTZ,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS ai.classification (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        entity_type     TEXT NOT NULL,
        entity_id       UUID NOT NULL,
        classifier      TEXT NOT NULL,
        label           TEXT NOT NULL,
        confidence      NUMERIC(5,4) CHECK (confidence BETWEEN 0 AND 1),
        all_labels      JSONB NOT NULL DEFAULT '{}',
        model_id        TEXT NOT NULL DEFAULT 'claude-haiku-4-5-20251001',
        classified_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS ai.intent_detection (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        entity_type     TEXT NOT NULL,
        entity_id       UUID NOT NULL,
        intent_type     TEXT NOT NULL CHECK (intent_type IN ('hiring','expansion','technology_change','fundraising','partnership','acquisition')),
        signal_strength NUMERIC(5,4) CHECK (signal_strength BETWEEN 0 AND 1),
        signals         JSONB NOT NULL DEFAULT '[]',
        detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        expires_at      TIMESTAMPTZ,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS ai.note_embeddings (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        note_id         UUID NOT NULL,
        embedding       vector(1536) NOT NULL,
        model_id        TEXT NOT NULL DEFAULT 'text-embedding-3-small',
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(note_id)
    );
    CREATE INDEX IF NOT EXISTS idx_note_embeddings_hnsw ON ai.note_embeddings
        USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

    -- ============================================================
    -- BILLING SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS billing.subscriptions (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE UNIQUE,
        plan_id             UUID NOT NULL REFERENCES billing.subscription_plans(id),
        stripe_customer_id  TEXT,
        stripe_sub_id       TEXT UNIQUE,
        billing_cycle       TEXT NOT NULL DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly','annual')),
        current_period_start TIMESTAMPTZ,
        current_period_end  TIMESTAMPTZ,
        trial_start         TIMESTAMPTZ,
        trial_end           TIMESTAMPTZ,
        cancel_at           TIMESTAMPTZ,
        canceled_at         TIMESTAMPTZ,
        ended_at            TIMESTAMPTZ,
        seats               INTEGER NOT NULL DEFAULT 1,
        status              TEXT NOT NULL DEFAULT 'trialing',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS billing.invoices (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        subscription_id     UUID REFERENCES billing.subscriptions(id),
        stripe_invoice_id   TEXT UNIQUE,
        invoice_number      TEXT,
        subtotal            NUMERIC(12, 2) NOT NULL DEFAULT 0,
        tax                 NUMERIC(12, 2) NOT NULL DEFAULT 0,
        discount            NUMERIC(12, 2) NOT NULL DEFAULT 0,
        total               NUMERIC(12, 2) NOT NULL DEFAULT 0,
        currency            CHAR(3) NOT NULL DEFAULT 'USD',
        paid_at             TIMESTAMPTZ,
        due_date            DATE,
        pdf_url             TEXT,
        billing_reason      TEXT,
        status              TEXT NOT NULL DEFAULT 'draft',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS billing.credit_transactions (
        id                  UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        transaction_type    TEXT NOT NULL CHECK (transaction_type IN ('purchase','deduction','refund','bonus','expiry','adjustment')),
        amount              INTEGER NOT NULL,
        balance_before      INTEGER NOT NULL,
        balance_after       INTEGER NOT NULL CHECK (balance_after >= 0),
        description         TEXT,
        reference_type      TEXT,
        reference_id        UUID,
        performed_by        UUID,
        status              TEXT NOT NULL DEFAULT 'completed',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY (id, created_at)
    ) PARTITION BY RANGE (created_at);
    SELECT create_monthly_partition('billing.credit_transactions', NOW());
    SELECT create_monthly_partition('billing.credit_transactions', NOW() + INTERVAL '1 month');

    CREATE TABLE IF NOT EXISTS billing.payment_methods (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        stripe_pm_id        TEXT UNIQUE,
        payment_type        TEXT NOT NULL DEFAULT 'card',
        brand               TEXT,
        last4               CHAR(4),
        exp_month           INTEGER,
        exp_year            INTEGER,
        is_default          BOOLEAN NOT NULL DEFAULT FALSE,
        billing_name        TEXT,
        billing_email       TEXT,
        billing_address     JSONB,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS billing.coupons (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        code                TEXT NOT NULL UNIQUE,
        discount_type       TEXT NOT NULL CHECK (discount_type IN ('percentage','fixed_amount','credits')),
        discount_value      NUMERIC(12, 2) NOT NULL,
        currency            CHAR(3),
        max_redemptions     INTEGER,
        redemption_count    INTEGER NOT NULL DEFAULT 0,
        applicable_plans    UUID[],
        valid_from          TIMESTAMPTZ,
        valid_until         TIMESTAMPTZ,
        is_active           BOOLEAN NOT NULL DEFAULT TRUE,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    -- Triggers
    CREATE OR REPLACE TRIGGER trg_saved_searches_updated_at BEFORE UPDATE ON search.saved_searches FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_search_cache_updated_at BEFORE UPDATE ON search.search_cache FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_ai_models_updated_at BEFORE UPDATE ON ai.ai_models FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_lead_scores_updated_at BEFORE UPDATE ON ai.lead_scores FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_subscriptions_updated_at BEFORE UPDATE ON billing.subscriptions FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_invoices_updated_at BEFORE UPDATE ON billing.invoices FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_payment_methods_updated_at BEFORE UPDATE ON billing.payment_methods FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_coupons_updated_at BEFORE UPDATE ON billing.coupons FOR EACH ROW EXECUTE FUNCTION set_updated_at();

    -- RLS
    ALTER TABLE search.saved_searches ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS saved_searches_org_isolation ON search.saved_searches;
    CREATE POLICY saved_searches_org_isolation ON search.saved_searches
        USING (organization_id = current_org_id());

    ALTER TABLE ai.lead_scores ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS lead_scores_org_isolation ON ai.lead_scores;
    CREATE POLICY lead_scores_org_isolation ON ai.lead_scores
        USING (organization_id = current_org_id());

    ALTER TABLE billing.subscriptions ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS subscriptions_org_isolation ON billing.subscriptions;
    CREATE POLICY subscriptions_org_isolation ON billing.subscriptions
        USING (organization_id = current_org_id());

    ALTER TABLE billing.invoices ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS invoices_org_isolation ON billing.invoices;
    CREATE POLICY invoices_org_isolation ON billing.invoices
        USING (organization_id = current_org_id());
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS billing.coupons CASCADE;
    DROP TABLE IF EXISTS billing.payment_methods CASCADE;
    DROP TABLE IF EXISTS billing.credit_transactions CASCADE;
    DROP TABLE IF EXISTS billing.invoices CASCADE;
    DROP TABLE IF EXISTS billing.subscriptions CASCADE;
    DROP TABLE IF EXISTS ai.note_embeddings CASCADE;
    DROP TABLE IF EXISTS ai.intent_detection CASCADE;
    DROP TABLE IF EXISTS ai.classification CASCADE;
    DROP TABLE IF EXISTS ai.ai_predictions CASCADE;
    DROP TABLE IF EXISTS ai.duplicates CASCADE;
    DROP TABLE IF EXISTS ai.recommendations CASCADE;
    DROP TABLE IF EXISTS ai.lead_scores CASCADE;
    DROP TABLE IF EXISTS ai.embeddings CASCADE;
    DROP TABLE IF EXISTS ai.ai_models CASCADE;
    DROP TABLE IF EXISTS search.query_embeddings CASCADE;
    DROP TABLE IF EXISTS search.search_statistics CASCADE;
    DROP TABLE IF EXISTS search.search_cache CASCADE;
    DROP TABLE IF EXISTS search.scheduled_searches CASCADE;
    DROP TABLE IF EXISTS search.saved_searches CASCADE;
    DROP TABLE IF EXISTS search.search_filters CASCADE;
    DROP TABLE IF EXISTS search.search_requests CASCADE;
    """)

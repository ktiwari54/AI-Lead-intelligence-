"""phase2_search_ai_billing: search, AI/ML, and billing schemas

Revision ID: 009
Revises: 008
Create Date: 2026-01-01
"""
from __future__ import annotations
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════
    # SEARCH DOMAIN
    # ═══════════════════════════════════════════════════════════

    op.execute("""
        CREATE TABLE IF NOT EXISTS search.search_requests (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            user_id         UUID REFERENCES auth.users(id),
            search_type     VARCHAR(50) NOT NULL DEFAULT 'company',  -- company, contact, combined
            query           TEXT,
            filters         JSONB NOT NULL DEFAULT '{}',
            sort_field      VARCHAR(100),
            sort_direction  VARCHAR(10) NOT NULL DEFAULT 'desc',
            page            INTEGER NOT NULL DEFAULT 1,
            page_size       INTEGER NOT NULL DEFAULT 25,
            result_count    INTEGER,
            total_count     INTEGER,
            execution_ms    INTEGER,
            is_cached       BOOLEAN NOT NULL DEFAULT FALSE,
            cache_key       VARCHAR(255),
            source          VARCHAR(50) NOT NULL DEFAULT 'ui',  -- ui, api, scheduled
            session_id      UUID,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}'
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("CREATE TABLE search.search_requests_2026_06 PARTITION OF search.search_requests FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')")
    op.execute("CREATE TABLE search.search_requests_2026_07 PARTITION OF search.search_requests FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')")
    op.execute("CREATE TABLE search.search_requests_future PARTITION OF search.search_requests FOR VALUES FROM ('2026-08-01') TO ('2030-01-01')")
    op.execute("CREATE INDEX idx_search_req_org ON search.search_requests(organization_id, created_at DESC)")
    op.execute("CREATE INDEX idx_search_req_user ON search.search_requests(user_id, created_at DESC)")
    op.execute("CREATE INDEX idx_search_req_filters ON search.search_requests USING GIN(filters)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS search.search_filters (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            search_id       UUID NOT NULL,  -- references search_requests.id (partitioned)
            filter_group    VARCHAR(50) NOT NULL,
            filter_key      VARCHAR(100) NOT NULL,
            filter_operator VARCHAR(50) NOT NULL DEFAULT 'eq',  -- eq, neq, gt, lt, gte, lte, in, contains
            filter_value    JSONB NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_search_filters_search ON search.search_filters(search_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS search.search_results (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            search_id       UUID NOT NULL,
            result_type     VARCHAR(50) NOT NULL,  -- company, contact
            result_id       UUID NOT NULL,
            rank            INTEGER,
            score           NUMERIC(10,6),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}'
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("CREATE TABLE search.search_results_2026_06 PARTITION OF search.search_results FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')")
    op.execute("CREATE TABLE search.search_results_future PARTITION OF search.search_results FOR VALUES FROM ('2026-07-01') TO ('2030-01-01')")
    op.execute("CREATE INDEX idx_search_results_search ON search.search_results(search_id)")
    op.execute("CREATE INDEX idx_search_results_result ON search.search_results(result_type, result_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS search.saved_searches (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            name            VARCHAR(255) NOT NULL,
            description     TEXT,
            search_type     VARCHAR(50) NOT NULL DEFAULT 'company',
            query           TEXT,
            filters         JSONB NOT NULL DEFAULT '{}',
            sort_field      VARCHAR(100),
            sort_direction  VARCHAR(10) NOT NULL DEFAULT 'desc',
            is_shared       BOOLEAN NOT NULL DEFAULT FALSE,
            alert_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
            alert_frequency VARCHAR(20),   -- daily, weekly
            last_run_at     TIMESTAMPTZ,
            last_result_count INTEGER,
            run_count       INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_saved_searches_user ON search.saved_searches(user_id, organization_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_saved_searches_filters ON search.saved_searches USING GIN(filters)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS search.scheduled_searches (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            saved_search_id UUID NOT NULL REFERENCES search.saved_searches(id) ON DELETE CASCADE,
            frequency       VARCHAR(20) NOT NULL DEFAULT 'daily',
            cron_expression VARCHAR(100),
            next_run_at     TIMESTAMPTZ,
            last_run_at     TIMESTAMPTZ,
            last_run_status VARCHAR(50),
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS search.search_cache (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            cache_key       VARCHAR(255) NOT NULL UNIQUE,
            organization_id UUID REFERENCES auth.organizations(id),
            search_type     VARCHAR(50),
            query_hash      VARCHAR(64) NOT NULL,
            result_count    INTEGER,
            results         JSONB NOT NULL DEFAULT '[]',
            hit_count       INTEGER NOT NULL DEFAULT 0,
            expires_at      TIMESTAMPTZ NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_search_cache_key ON search.search_cache(cache_key)")
    op.execute("CREATE INDEX idx_search_cache_expires ON search.search_cache(expires_at)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS search.search_statistics (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            period_date     DATE NOT NULL,
            search_type     VARCHAR(50) NOT NULL,
            total_searches  INTEGER NOT NULL DEFAULT 0,
            unique_queries  INTEGER NOT NULL DEFAULT 0,
            avg_result_count NUMERIC(10,2),
            avg_execution_ms NUMERIC(10,2),
            cache_hits      INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(organization_id, period_date, search_type)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS search.query_embeddings (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            query_text      TEXT NOT NULL,
            query_hash      VARCHAR(64) NOT NULL,
            embedding       vector(1536),
            model           VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at      TIMESTAMPTZ,
            UNIQUE(organization_id, query_hash)
        )
    """)
    op.execute("CREATE INDEX idx_query_embeddings_hnsw ON search.query_embeddings USING hnsw(embedding vector_cosine_ops) WHERE embedding IS NOT NULL")

    # ═══════════════════════════════════════════════════════════
    # AI DOMAIN
    # ═══════════════════════════════════════════════════════════

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.ai_models (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            name            VARCHAR(255) NOT NULL,
            version         VARCHAR(50) NOT NULL,
            provider        VARCHAR(100) NOT NULL,  -- openai, anthropic, custom
            model_type      VARCHAR(100) NOT NULL,  -- embedding, scoring, classification, generation
            endpoint        VARCHAR(500),
            input_dims      INTEGER,
            output_dims     INTEGER,
            max_tokens      INTEGER,
            cost_per_token  NUMERIC(10,8),
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            is_default      BOOLEAN NOT NULL DEFAULT FALSE,
            config          JSONB NOT NULL DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version_num     INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(name, version)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.embeddings (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            entity_type     VARCHAR(50) NOT NULL,   -- company, contact, note, search
            entity_id       UUID NOT NULL,
            model_id        UUID REFERENCES ai.ai_models(id),
            model_name      VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
            embedding       vector(1536) NOT NULL,
            text_hash       VARCHAR(64),
            token_count     INTEGER,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version_num     INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(organization_id, entity_type, entity_id)
        )
    """)
    op.execute("CREATE INDEX idx_embeddings_hnsw ON ai.embeddings USING hnsw(embedding vector_cosine_ops) WITH (m=16, ef_construction=64) WHERE embedding IS NOT NULL")
    op.execute("CREATE INDEX idx_embeddings_entity ON ai.embeddings(entity_type, entity_id)")
    op.execute("CREATE INDEX idx_embeddings_org ON ai.embeddings(organization_id, entity_type)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.lead_scores (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            entity_type     VARCHAR(50) NOT NULL,   -- company, contact
            entity_id       UUID NOT NULL,
            company_id      UUID REFERENCES core.companies(id) ON DELETE SET NULL,
            contact_id      UUID REFERENCES core.contacts(id) ON DELETE SET NULL,
            model_id        UUID REFERENCES ai.ai_models(id),
            model_used      VARCHAR(100),
            overall_score   NUMERIC(5,2) NOT NULL,   -- 0-100
            quality_score   NUMERIC(5,2),
            fit_score       NUMERIC(5,2),
            intent_score    NUMERIC(5,2),
            engagement_score NUMERIC(5,2),
            timing_score    NUMERIC(5,2),
            score_breakdown JSONB NOT NULL DEFAULT '{}',
            recommendation  VARCHAR(50),   -- hot, warm, cold, not_a_fit
            reasoning       TEXT,
            confidence      NUMERIC(5,2),
            query_context   TEXT,
            query_embedding vector(1536),
            scored_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_lead_scores_entity ON ai.lead_scores(entity_type, entity_id, organization_id)")
    op.execute("CREATE INDEX idx_lead_scores_company ON ai.lead_scores(company_id, overall_score DESC)")
    op.execute("CREATE INDEX idx_lead_scores_contact ON ai.lead_scores(contact_id, overall_score DESC)")
    op.execute("CREATE INDEX idx_lead_scores_score ON ai.lead_scores(organization_id, overall_score DESC, recommendation)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.recommendations (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            user_id         UUID REFERENCES auth.users(id),
            rec_type        VARCHAR(50) NOT NULL,  -- similar_companies, next_best_action, at_risk
            entity_type     VARCHAR(50) NOT NULL,
            entity_id       UUID NOT NULL,
            recommended_ids UUID[] NOT NULL DEFAULT '{}',
            scores          JSONB NOT NULL DEFAULT '{}',
            reasoning       TEXT,
            model_used      VARCHAR(100),
            accepted        BOOLEAN,
            accepted_at     TIMESTAMPTZ,
            dismissed       BOOLEAN NOT NULL DEFAULT FALSE,
            dismissed_at    TIMESTAMPTZ,
            expires_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_recommendations_entity ON ai.recommendations(entity_type, entity_id, organization_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.duplicates (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            entity_type     VARCHAR(50) NOT NULL,
            entity_id_a     UUID NOT NULL,
            entity_id_b     UUID NOT NULL,
            similarity      NUMERIC(5,4) NOT NULL,   -- 0.0000 - 1.0000
            match_fields    TEXT[] NOT NULL DEFAULT '{}',
            status          VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, merged, dismissed
            merged_into     UUID,
            resolved_by     UUID REFERENCES auth.users(id),
            resolved_at     TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(organization_id, entity_type, entity_id_a, entity_id_b)
        )
    """)
    op.execute("CREATE INDEX idx_duplicates_entity_a ON ai.duplicates(entity_type, entity_id_a)")
    op.execute("CREATE INDEX idx_duplicates_status ON ai.duplicates(organization_id, status, entity_type)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.ai_predictions (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            prediction_type VARCHAR(100) NOT NULL,  -- churn_risk, upsell_potential, deal_close_probability
            entity_type     VARCHAR(50) NOT NULL,
            entity_id       UUID NOT NULL,
            prediction      JSONB NOT NULL DEFAULT '{}',
            probability     NUMERIC(5,4),
            model_used      VARCHAR(100),
            features_used   JSONB NOT NULL DEFAULT '{}',
            valid_until     TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_ai_predictions_entity ON ai.ai_predictions(entity_type, entity_id, organization_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.classification (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            entity_type     VARCHAR(50) NOT NULL,
            entity_id       UUID NOT NULL,
            classifier      VARCHAR(100) NOT NULL,  -- industry, intent, seniority
            label           VARCHAR(255) NOT NULL,
            confidence      NUMERIC(5,4) NOT NULL,
            all_labels      JSONB NOT NULL DEFAULT '{}',
            model_used      VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.intent_detection (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID REFERENCES core.companies(id) ON DELETE SET NULL,
            intent_type     VARCHAR(100) NOT NULL,  -- hiring, expansion, technology_change
            signal          TEXT NOT NULL,
            signal_source   VARCHAR(100),
            confidence      NUMERIC(5,4) NOT NULL,
            detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            valid_until     TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_intent_company ON ai.intent_detection(company_id, detected_at DESC)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS ai.note_embeddings (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            note_id         UUID NOT NULL,
            entity_type     VARCHAR(50) NOT NULL,
            entity_id       UUID NOT NULL,
            embedding       vector(1536) NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(note_id)
        )
    """)
    op.execute("CREATE INDEX idx_note_embeddings_hnsw ON ai.note_embeddings USING hnsw(embedding vector_cosine_ops) WITH (m=16, ef_construction=64)")

    # ═══════════════════════════════════════════════════════════
    # BILLING DOMAIN
    # ═══════════════════════════════════════════════════════════

    op.execute("""
        CREATE TABLE IF NOT EXISTS billing.subscriptions (
            id                  UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id     UUID NOT NULL UNIQUE REFERENCES auth.organizations(id) ON DELETE CASCADE,
            plan_id             UUID NOT NULL REFERENCES billing.subscription_plans(id),
            stripe_customer_id  VARCHAR(255),
            stripe_sub_id       VARCHAR(255) UNIQUE,
            billing_cycle       VARCHAR(20) NOT NULL DEFAULT 'monthly',  -- monthly, annual
            current_period_start TIMESTAMPTZ,
            current_period_end   TIMESTAMPTZ,
            trial_start         TIMESTAMPTZ,
            trial_end           TIMESTAMPTZ,
            canceled_at         TIMESTAMPTZ,
            cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
            cancelation_reason  TEXT,
            credits_balance     INTEGER NOT NULL DEFAULT 0,
            credits_included    INTEGER NOT NULL DEFAULT 0,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at          TIMESTAMPTZ,
            created_by          UUID REFERENCES auth.users(id),
            version             INTEGER NOT NULL DEFAULT 1,
            status              VARCHAR(50) NOT NULL DEFAULT 'trialing',
            metadata            JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_subscriptions_stripe ON billing.subscriptions(stripe_sub_id)")
    op.execute("CREATE INDEX idx_subscriptions_plan ON billing.subscriptions(plan_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS billing.invoices (
            id                  UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            subscription_id     UUID REFERENCES billing.subscriptions(id),
            stripe_invoice_id   VARCHAR(255) UNIQUE,
            invoice_number      VARCHAR(100),
            amount              NUMERIC(10,2) NOT NULL,
            currency            VARCHAR(10) NOT NULL DEFAULT 'USD',
            tax_amount          NUMERIC(10,2) NOT NULL DEFAULT 0,
            discount_amount     NUMERIC(10,2) NOT NULL DEFAULT 0,
            total_amount        NUMERIC(10,2) NOT NULL,
            due_date            DATE,
            paid_at             TIMESTAMPTZ,
            payment_method      VARCHAR(100),
            billing_reason      VARCHAR(100),
            pdf_url             VARCHAR(1000),
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version             INTEGER NOT NULL DEFAULT 1,
            status              VARCHAR(50) NOT NULL DEFAULT 'draft',
            metadata            JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS billing.credit_transactions (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            subscription_id UUID REFERENCES billing.subscriptions(id),
            transaction_type VARCHAR(50) NOT NULL,  -- deduct, add, refund, expire, bonus
            amount          INTEGER NOT NULL,         -- negative = deduction
            balance_before  INTEGER NOT NULL,
            balance_after   INTEGER NOT NULL,
            description     VARCHAR(500) NOT NULL,
            reference_type  VARCHAR(100),            -- search, export, enrichment, api_call
            reference_id    UUID,
            actor_id        UUID REFERENCES auth.users(id),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}'
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("CREATE TABLE billing.credit_transactions_2026_06 PARTITION OF billing.credit_transactions FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')")
    op.execute("CREATE TABLE billing.credit_transactions_future PARTITION OF billing.credit_transactions FOR VALUES FROM ('2026-07-01') TO ('2030-01-01')")
    op.execute("CREATE INDEX idx_credit_tx_org ON billing.credit_transactions(organization_id, created_at DESC)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS billing.payment_methods (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            stripe_pm_id    VARCHAR(255) UNIQUE,
            method_type     VARCHAR(50) NOT NULL,  -- card, bank_account
            brand           VARCHAR(50),
            last4           VARCHAR(4),
            exp_month       SMALLINT,
            exp_year        SMALLINT,
            is_default      BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS billing.coupons (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            code            VARCHAR(100) NOT NULL UNIQUE,
            description     TEXT,
            discount_type   VARCHAR(20) NOT NULL,  -- percentage, fixed_amount, credits
            discount_value  NUMERIC(10,2) NOT NULL,
            currency        VARCHAR(10),
            max_redemptions INTEGER,
            redemption_count INTEGER NOT NULL DEFAULT 0,
            applies_to_plans TEXT[] NOT NULL DEFAULT '{}',
            valid_from      TIMESTAMPTZ,
            valid_until     TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)


def downgrade() -> None:
    for tbl in [
        "billing.coupons", "billing.payment_methods", "billing.credit_transactions",
        "billing.invoices", "billing.subscriptions",
        "ai.note_embeddings", "ai.intent_detection", "ai.classification",
        "ai.ai_predictions", "ai.duplicates", "ai.recommendations",
        "ai.lead_scores", "ai.embeddings", "ai.ai_models",
        "search.query_embeddings", "search.search_statistics",
        "search.search_cache", "search.scheduled_searches",
        "search.saved_searches", "search.search_results",
        "search.search_filters", "search.search_requests"
    ]:
        op.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")

"""Phase 2: Materialized Views, Stored Functions, Enrichment

Revision ID: 012
Revises: 011
Create Date: 2024-01-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    -- ============================================================
    -- ENRICHMENT SCHEMA
    -- ============================================================

    CREATE TABLE IF NOT EXISTS enrichment.enrichment_jobs (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        entity_type         TEXT NOT NULL CHECK (entity_type IN ('company','contact')),
        entity_id           UUID NOT NULL,
        connector_id        UUID REFERENCES connector.connectors(id),
        fields_requested    TEXT[] NOT NULL DEFAULT '{}',
        fields_enriched     TEXT[] NOT NULL DEFAULT '{}',
        result_data         JSONB NOT NULL DEFAULT '{}',
        credits_used        INTEGER NOT NULL DEFAULT 0,
        error_message       TEXT,
        started_at          TIMESTAMPTZ,
        completed_at        TIMESTAMPTZ,
        status              TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','failed','partial')),
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_enrichment_jobs_entity ON enrichment.enrichment_jobs(entity_type, entity_id);
    CREATE INDEX IF NOT EXISTS idx_enrichment_jobs_org_status ON enrichment.enrichment_jobs(organization_id, status);
    CREATE OR REPLACE TRIGGER trg_enrichment_jobs_updated_at BEFORE UPDATE ON enrichment.enrichment_jobs FOR EACH ROW EXECUTE FUNCTION set_updated_at();

    ALTER TABLE enrichment.enrichment_jobs ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS enrichment_jobs_org_isolation ON enrichment.enrichment_jobs;
    CREATE POLICY enrichment_jobs_org_isolation ON enrichment.enrichment_jobs
        USING (organization_id = current_org_id());

    -- ============================================================
    -- MATERIALIZED VIEWS
    -- ============================================================

    CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_top_companies AS
    SELECT
        c.organization_id,
        c.id AS company_id,
        c.name,
        c.domain,
        c.industry_name,
        c.country_code,
        c.employee_count,
        c.annual_revenue,
        c.enrichment_status,
        ls.overall_score AS lead_score,
        ls.recommendation,
        c.updated_at
    FROM core.companies c
    LEFT JOIN ai.lead_scores ls ON ls.entity_type = 'company' AND ls.entity_id = c.id
    WHERE c.deleted_at IS NULL
    WITH NO DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_top_companies_pk
        ON analytics.mv_top_companies(organization_id, company_id);
    CREATE INDEX IF NOT EXISTS idx_mv_top_companies_score
        ON analytics.mv_top_companies(organization_id, lead_score DESC NULLS LAST);

    CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_top_industries AS
    SELECT
        c.organization_id,
        c.industry_name,
        COUNT(*) AS company_count,
        AVG(c.employee_count) AS avg_employees,
        AVG(c.annual_revenue) AS avg_revenue,
        AVG(ls.overall_score) AS avg_lead_score
    FROM core.companies c
    LEFT JOIN ai.lead_scores ls ON ls.entity_type = 'company' AND ls.entity_id = c.id
    WHERE c.deleted_at IS NULL AND c.industry_name IS NOT NULL
    GROUP BY c.organization_id, c.industry_name
    WITH NO DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_top_industries_pk
        ON analytics.mv_top_industries(organization_id, industry_name);

    CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_country_statistics AS
    SELECT
        co.organization_id,
        co.country_code,
        cn.name AS country_name,
        cn.continent,
        COUNT(DISTINCT co.id) AS company_count,
        COUNT(DISTINCT ct.id) AS contact_count,
        AVG(ls.overall_score) AS avg_lead_score
    FROM core.companies co
    LEFT JOIN core.countries cn ON cn.iso2 = co.country_code
    LEFT JOIN core.contacts ct ON ct.organization_id = co.organization_id AND ct.company_id = co.id AND ct.deleted_at IS NULL
    LEFT JOIN ai.lead_scores ls ON ls.entity_type = 'company' AND ls.entity_id = co.id
    WHERE co.deleted_at IS NULL AND co.country_code IS NOT NULL
    GROUP BY co.organization_id, co.country_code, cn.name, cn.continent
    WITH NO DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_country_statistics_pk
        ON analytics.mv_country_statistics(organization_id, country_code);

    CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_technology_statistics AS
    SELECT
        ct.organization_id,
        ct.technology_name,
        ct.category,
        COUNT(DISTINCT ct.company_id) AS company_count,
        AVG(ls.overall_score) AS avg_lead_score
    FROM core.company_technologies ct
    LEFT JOIN ai.lead_scores ls ON ls.entity_type = 'company' AND ls.entity_id = ct.company_id
    WHERE ct.deleted_at IS NULL
    GROUP BY ct.organization_id, ct.technology_name, ct.category
    WITH NO DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_technology_statistics_pk
        ON analytics.mv_technology_statistics(organization_id, technology_name);

    CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_lead_score_summary AS
    SELECT
        ls.organization_id,
        ls.entity_type,
        COUNT(*) AS total_scored,
        AVG(ls.overall_score) AS avg_score,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ls.overall_score) AS median_score,
        COUNT(*) FILTER (WHERE ls.recommendation = 'hot') AS hot_count,
        COUNT(*) FILTER (WHERE ls.recommendation = 'warm') AS warm_count,
        COUNT(*) FILTER (WHERE ls.recommendation = 'cold') AS cold_count,
        COUNT(*) FILTER (WHERE ls.recommendation = 'not_a_fit') AS not_a_fit_count
    FROM ai.lead_scores ls
    WHERE ls.deleted_at IS NULL
    GROUP BY ls.organization_id, ls.entity_type
    WITH NO DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_lead_score_summary_pk
        ON analytics.mv_lead_score_summary(organization_id, entity_type);

    CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_recently_updated_companies AS
    SELECT
        c.organization_id,
        c.id AS company_id,
        c.name,
        c.domain,
        c.industry_name,
        c.country_code,
        c.enrichment_status,
        c.updated_at
    FROM core.companies c
    WHERE c.deleted_at IS NULL
      AND c.updated_at >= NOW() - INTERVAL '7 days'
    WITH NO DATA;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_recently_updated_companies_pk
        ON analytics.mv_recently_updated_companies(organization_id, company_id);

    -- ============================================================
    -- STORED FUNCTIONS
    -- ============================================================

    CREATE OR REPLACE FUNCTION analytics.refresh_all_materialized_views()
    RETURNS VOID LANGUAGE plpgsql AS $$
    BEGIN
        REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_top_companies;
        REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_top_industries;
        REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_country_statistics;
        REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_technology_statistics;
        REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_lead_score_summary;
        REFRESH MATERIALIZED VIEW CONCURRENTLY analytics.mv_recently_updated_companies;
    END;
    $$;

    CREATE OR REPLACE FUNCTION audit.capture_entity_history()
    RETURNS TRIGGER LANGUAGE plpgsql AS $$
    DECLARE
        v_changed_fields TEXT[] := '{}';
        v_old_json JSONB;
        v_new_json JSONB;
        v_key TEXT;
    BEGIN
        v_old_json := to_jsonb(OLD);
        v_new_json := to_jsonb(NEW);
        FOR v_key IN SELECT jsonb_object_keys(v_new_json) LOOP
            IF v_old_json->v_key IS DISTINCT FROM v_new_json->v_key THEN
                v_changed_fields := array_append(v_changed_fields, v_key);
            END IF;
        END LOOP;
        IF array_length(v_changed_fields, 1) > 0 THEN
            INSERT INTO audit.entity_history (
                organization_id, entity_type, entity_id, action,
                snapshot, changed_fields, changed_by, change_source, created_at
            ) VALUES (
                NEW.organization_id,
                TG_ARGV[0],
                NEW.id,
                'updated',
                v_new_json,
                v_changed_fields,
                NEW.updated_by,
                'trigger',
                NOW()
            );
        END IF;
        RETURN NEW;
    END;
    $$;

    CREATE OR REPLACE TRIGGER trg_companies_history
        AFTER UPDATE ON core.companies
        FOR EACH ROW EXECUTE FUNCTION audit.capture_entity_history('company');

    CREATE OR REPLACE TRIGGER trg_contacts_history
        AFTER UPDATE ON core.contacts
        FOR EACH ROW EXECUTE FUNCTION audit.capture_entity_history('contact');

    CREATE OR REPLACE FUNCTION billing.check_credit_balance()
    RETURNS TRIGGER LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.balance_after < 0 THEN
            RAISE EXCEPTION 'Insufficient credit balance. Current: %, Required: %',
                NEW.balance_before, ABS(NEW.amount);
        END IF;
        RETURN NEW;
    END;
    $$;

    CREATE OR REPLACE FUNCTION search.increment_search_stats()
    RETURNS TRIGGER LANGUAGE plpgsql AS $$
    BEGIN
        INSERT INTO search.search_statistics (
            organization_id, period_date, search_type,
            total_searches, credits_used
        ) VALUES (
            NEW.organization_id, CURRENT_DATE, NEW.search_type,
            1, NEW.credits_used
        )
        ON CONFLICT (organization_id, period_date, search_type)
        DO UPDATE SET
            total_searches = search.search_statistics.total_searches + 1,
            credits_used = search.search_statistics.credits_used + EXCLUDED.credits_used,
            updated_at = NOW();
        RETURN NEW;
    END;
    $$;

    CREATE OR REPLACE FUNCTION auth.update_org_usage()
    RETURNS TRIGGER LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.transaction_type = 'deduction' THEN
            INSERT INTO auth.organization_usage (
                organization_id, period_year, period_month,
                credits_used
            ) VALUES (
                NEW.organization_id,
                EXTRACT(YEAR FROM NOW())::INTEGER,
                EXTRACT(MONTH FROM NOW())::INTEGER,
                ABS(NEW.amount)
            )
            ON CONFLICT (organization_id, period_year, period_month)
            DO UPDATE SET
                credits_used = auth.organization_usage.credits_used + ABS(EXCLUDED.credits_used),
                updated_at = NOW();
        END IF;
        RETURN NEW;
    END;
    $$;

    -- ============================================================
    -- SEARCH FUNCTIONS
    -- ============================================================

    CREATE OR REPLACE FUNCTION core.search_companies(
        p_org_id    UUID,
        p_query     TEXT,
        p_limit     INTEGER DEFAULT 25,
        p_offset    INTEGER DEFAULT 0
    )
    RETURNS TABLE (
        id UUID, name TEXT, domain TEXT, industry_name TEXT,
        country_code TEXT, employee_count INTEGER, annual_revenue NUMERIC,
        rank REAL
    ) LANGUAGE sql STABLE AS $$
        SELECT
            c.id, c.name, c.domain, c.industry_name,
            c.country_code, c.employee_count, c.annual_revenue,
            ts_rank(c.fts, websearch_to_tsquery('english', p_query)) AS rank
        FROM core.companies c
        WHERE c.organization_id = p_org_id
          AND c.deleted_at IS NULL
          AND (
              c.fts @@ websearch_to_tsquery('english', p_query)
              OR c.name ILIKE '%' || p_query || '%'
          )
        ORDER BY rank DESC, c.updated_at DESC
        LIMIT p_limit OFFSET p_offset;
    $$;

    CREATE OR REPLACE FUNCTION core.search_contacts(
        p_org_id    UUID,
        p_query     TEXT,
        p_limit     INTEGER DEFAULT 25,
        p_offset    INTEGER DEFAULT 0
    )
    RETURNS TABLE (
        id UUID, full_name TEXT, email CITEXT, title TEXT,
        company_id UUID, seniority_level TEXT, rank REAL
    ) LANGUAGE sql STABLE AS $$
        SELECT
            c.id, c.full_name, c.email, c.title,
            c.company_id, c.seniority_level,
            ts_rank(c.fts, websearch_to_tsquery('english', p_query)) AS rank
        FROM core.contacts c
        WHERE c.organization_id = p_org_id
          AND c.deleted_at IS NULL
          AND (
              c.fts @@ websearch_to_tsquery('english', p_query)
              OR c.full_name ILIKE '%' || p_query || '%'
          )
        ORDER BY rank DESC, c.updated_at DESC
        LIMIT p_limit OFFSET p_offset;
    $$;

    CREATE OR REPLACE FUNCTION core.companies_near(
        p_org_id        UUID,
        p_lat           DOUBLE PRECISION,
        p_lon           DOUBLE PRECISION,
        p_radius_km     DOUBLE PRECISION DEFAULT 50
    )
    RETURNS TABLE (
        id UUID, name TEXT, domain TEXT, city TEXT,
        country_code TEXT, distance_km DOUBLE PRECISION
    ) LANGUAGE sql STABLE AS $$
        SELECT
            c.id, c.name, c.domain, c.city, c.country_code,
            ST_Distance(
                c.geo_location,
                ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::GEOGRAPHY
            ) / 1000.0 AS distance_km
        FROM core.companies c
        WHERE c.organization_id = p_org_id
          AND c.deleted_at IS NULL
          AND ST_DWithin(
              c.geo_location,
              ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::GEOGRAPHY,
              p_radius_km * 1000
          )
        ORDER BY distance_km ASC;
    $$;

    -- ============================================================
    -- RLS on remaining tables
    -- ============================================================

    ALTER TABLE connector.connector_configs ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS connector_configs_org_isolation ON connector.connector_configs;
    CREATE POLICY connector_configs_org_isolation ON connector.connector_configs
        USING (organization_id = current_org_id());

    ALTER TABLE analytics.dashboard_metrics ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS dashboard_metrics_org_isolation ON analytics.dashboard_metrics;
    CREATE POLICY dashboard_metrics_org_isolation ON analytics.dashboard_metrics
        USING (organization_id = current_org_id());

    ALTER TABLE notification.notification_preferences ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS notification_prefs_org_isolation ON notification.notification_preferences;
    CREATE POLICY notification_prefs_org_isolation ON notification.notification_preferences
        USING (organization_id = current_org_id());
    """)


def downgrade() -> None:
    op.execute("""
    DROP FUNCTION IF EXISTS core.companies_near(UUID, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION) CASCADE;
    DROP FUNCTION IF EXISTS core.search_contacts(UUID, TEXT, INTEGER, INTEGER) CASCADE;
    DROP FUNCTION IF EXISTS core.search_companies(UUID, TEXT, INTEGER, INTEGER) CASCADE;
    DROP FUNCTION IF EXISTS auth.update_org_usage() CASCADE;
    DROP FUNCTION IF EXISTS search.increment_search_stats() CASCADE;
    DROP FUNCTION IF EXISTS billing.check_credit_balance() CASCADE;
    DROP FUNCTION IF EXISTS audit.capture_entity_history() CASCADE;
    DROP FUNCTION IF EXISTS analytics.refresh_all_materialized_views() CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS analytics.mv_recently_updated_companies CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS analytics.mv_lead_score_summary CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS analytics.mv_technology_statistics CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS analytics.mv_country_statistics CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS analytics.mv_top_industries CASCADE;
    DROP MATERIALIZED VIEW IF EXISTS analytics.mv_top_companies CASCADE;
    DROP TABLE IF EXISTS enrichment.enrichment_jobs CASCADE;
    """)

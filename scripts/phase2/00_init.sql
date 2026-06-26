-- ============================================================
-- AI Lead Intelligence Platform - Phase 2 Enterprise Database
-- Core Infrastructure: Extensions, Schemas, Base Types
-- PostgreSQL 16+
-- ============================================================

-- ── Extensions ───────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "postgis_topology";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "tablefunc";
CREATE EXTENSION IF NOT EXISTS "hstore";
CREATE EXTENSION IF NOT EXISTS "citext";

-- ── UUID v7 Function ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS uuid
LANGUAGE plpgsql
AS $$
DECLARE
    unix_ms   BIGINT;
    rand_bytes BYTEA;
    hi        BIGINT;
    lo        BIGINT;
BEGIN
    unix_ms    := (EXTRACT(EPOCH FROM clock_timestamp()) * 1000)::BIGINT;
    rand_bytes := gen_random_bytes(10);
    hi := (unix_ms << 16) | ((get_byte(rand_bytes,0) & x'0F'::INT) << 12) | x'7000'::INT;
    lo := ((x'80'::INT | (get_byte(rand_bytes,1) & x'3F'::INT)) << 56)
        | (get_byte(rand_bytes,2)::BIGINT << 48)
        | (get_byte(rand_bytes,3)::BIGINT << 40)
        | (get_byte(rand_bytes,4)::BIGINT << 32)
        | (get_byte(rand_bytes,5)::BIGINT << 24)
        | (get_byte(rand_bytes,6)::BIGINT << 16)
        | (get_byte(rand_bytes,7)::BIGINT << 8)
        | get_byte(rand_bytes,8)::BIGINT;
    RETURN encode(
        set_byte(set_byte(
            int8send(hi) || int8send(lo), 6,
            (get_byte(int8send(hi) || int8send(lo), 6) & x'0F'::INT) | x'70'::INT
        ), 8,
            (get_byte(int8send(hi) || int8send(lo), 8) & x'3F'::INT) | x'80'::INT
        ),
    'hex')::uuid;
END;
$$;

-- ── Schemas ───────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS auth;          -- identity, auth, roles
CREATE SCHEMA IF NOT EXISTS core;          -- companies, contacts, locations
CREATE SCHEMA IF NOT EXISTS crm;           -- deals, pipelines, tasks, activities
CREATE SCHEMA IF NOT EXISTS search;        -- searches, filters, cache
CREATE SCHEMA IF NOT EXISTS ai;            -- scores, embeddings, models
CREATE SCHEMA IF NOT EXISTS analytics;     -- dashboards, stats, metrics
CREATE SCHEMA IF NOT EXISTS connector;     -- data connectors
CREATE SCHEMA IF NOT EXISTS audit;         -- audit, logs, history
CREATE SCHEMA IF NOT EXISTS billing;       -- subscriptions, credits, payments
CREATE SCHEMA IF NOT EXISTS notification;  -- alerts, templates, queue
CREATE SCHEMA IF NOT EXISTS system;        -- settings, feature flags, files
CREATE SCHEMA IF NOT EXISTS enrichment;    -- enrichment jobs
CREATE SCHEMA IF NOT EXISTS export;        -- exports / imports

-- ── Grant schema usage to app role ───────────────────────────
DO $$
DECLARE
    s TEXT;
BEGIN
    FOR s IN SELECT unnest(ARRAY[
        'auth','core','crm','search','ai','analytics',
        'connector','audit','billing','notification',
        'system','enrichment','export'
    ]) LOOP
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO PUBLIC', s);
    END LOOP;
END;
$$;

-- ── Updated_at auto-trigger function ────────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.version    = COALESCE(OLD.version, 0) + 1;
    RETURN NEW;
END;
$$;

-- ── Soft-delete helper ───────────────────────────────────────
CREATE OR REPLACE FUNCTION soft_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.deleted_at = NOW();
    NEW.status     = 'deleted';
    RETURN NEW;
END;
$$;

-- ── Row-level security helper ─────────────────────────────────
-- Sets app.current_org_id session variable (called from app middleware)
CREATE OR REPLACE FUNCTION set_org_context(p_org_id UUID)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    PERFORM set_config('app.current_org_id', p_org_id::TEXT, TRUE);
END;
$$;

CREATE OR REPLACE FUNCTION current_org_id() RETURNS UUID LANGUAGE sql AS $$
    SELECT NULLIF(current_setting('app.current_org_id', TRUE), '')::UUID;
$$;

CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID LANGUAGE sql AS $$
    SELECT NULLIF(current_setting('app.current_user_id', TRUE), '')::UUID;
$$;

-- ── PII masking function ──────────────────────────────────────
CREATE OR REPLACE FUNCTION mask_email(email TEXT) RETURNS TEXT LANGUAGE sql AS $$
    SELECT regexp_replace(email, '^(.).*(.)(@.*)$', '\1***\2\3');
$$;

CREATE OR REPLACE FUNCTION mask_phone(phone TEXT) RETURNS TEXT LANGUAGE sql AS $$
    SELECT regexp_replace(phone, '(\d{3})\d+(\d{2})', '\1****\2');
$$;

-- ── Partition management ─────────────────────────────────────
CREATE OR REPLACE FUNCTION create_monthly_partition(
    p_parent TEXT,
    p_schema TEXT,
    p_year   INT,
    p_month  INT
) RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    tbl   TEXT := p_parent || '_' || to_char(make_date(p_year, p_month, 1), 'YYYY_MM');
    start DATE := make_date(p_year, p_month, 1);
    stop  DATE := start + INTERVAL '1 month';
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = p_schema AND c.relname = tbl
    ) THEN
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I.%I PARTITION OF %I.%I FOR VALUES FROM (%L) TO (%L)',
            p_schema, tbl, p_schema, p_parent, start, stop
        );
    END IF;
END;
$$;

-- ── CITEXT domain for case-insensitive email ─────────────────
CREATE DOMAIN IF NOT EXISTS email_citext AS citext
    CHECK (VALUE ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- AI Lead Intelligence Platform - Database Initialization
-- Run this script once as a superuser before running Alembic migrations.

-- ─── Extensions ───────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";        -- gen_random_bytes(), crypt()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- trigram similarity search
CREATE EXTENSION IF NOT EXISTS "unaccent";        -- accent-insensitive search
CREATE EXTENSION IF NOT EXISTS "vector";          -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "postgis";         -- spatial types and functions
CREATE EXTENSION IF NOT EXISTS "btree_gist";      -- GiST index for exclusion constraints

-- ─── UUID v7 helper function ───────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS uuid
LANGUAGE plpgsql
AS $$
DECLARE
    unix_ms bigint;
    hex_ms  text;
    rand1   text;
    rand2   text;
BEGIN
    unix_ms := (EXTRACT(EPOCH FROM clock_timestamp()) * 1000)::bigint;
    hex_ms  := lpad(to_hex(unix_ms), 12, '0');
    rand1   := encode(gen_random_bytes(2), 'hex');
    rand2   := encode(gen_random_bytes(8), 'hex');
    -- version nibble = 7, variant bits = 10xxxxxx
    RETURN (
        substring(hex_ms, 1, 8) || '-' ||
        substring(hex_ms, 9, 4) || '-' ||
        '7' || substring(rand1, 2, 3) || '-' ||
        to_hex((('x' || substring(rand2, 1, 2))::bit(8) & 'x3f'::bit(8) | 'x80'::bit(8))::int) ||
        substring(rand2, 3, 2) || '-' ||
        substring(rand2, 5, 12)
    )::uuid;
END;
$$;

-- ─── Schemas ────────────────────────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS crm;
CREATE SCHEMA IF NOT EXISTS search;
CREATE SCHEMA IF NOT EXISTS ai;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS connector;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS notification;
CREATE SCHEMA IF NOT EXISTS system;
CREATE SCHEMA IF NOT EXISTS enrichment;
CREATE SCHEMA IF NOT EXISTS export;

-- ─── Search path ───────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ali_user') THEN
        EXECUTE 'ALTER ROLE ali_user SET search_path TO auth, core, crm, search, ai, analytics, connector, audit, billing, notification, system, enrichment, export, public';
    END IF;
END;
$$;

-- ─── Permissions ───────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    s text;
BEGIN
    FOREACH s IN ARRAY ARRAY['auth','core','crm','search','ai','analytics','connector','audit','billing','notification','system','enrichment','export']
    LOOP
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO PUBLIC', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON TABLES TO PUBLIC', s);
        EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT ALL ON SEQUENCES TO PUBLIC', s);
    END LOOP;
END;
$$;

\echo 'Database initialized successfully with all extensions and schemas.'

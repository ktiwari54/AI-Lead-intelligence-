-- Minimal schema for local discovery platform testing
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS uuid LANGUAGE plpgsql AS $$
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

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'trial',
    subscription_plan VARCHAR(50) NOT NULL DEFAULT 'free',
    credits INTEGER NOT NULL DEFAULT 0,
    logo_url VARCHAR(500),
    website VARCHAR(255),
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_superadmin BOOLEAN NOT NULL DEFAULT FALSE,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    last_login TIMESTAMPTZ,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    avatar_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_org ON users(email, organization_id);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at TIMESTAMPTZ NOT NULL,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS discovery_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    query TEXT,
    entity_type VARCHAR(20) NOT NULL DEFAULT 'both',
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    connectors_used JSONB NOT NULL DEFAULT '[]'::jsonb,
    stages JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_count INTEGER,
    credits_used INTEGER NOT NULL DEFAULT 0,
    took_ms INTEGER,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_discovery_jobs_organization_id ON discovery_jobs(organization_id);
CREATE INDEX IF NOT EXISTS ix_discovery_jobs_status ON discovery_jobs(status);

CREATE TABLE IF NOT EXISTS discovery_job_hits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    job_id UUID NOT NULL REFERENCES discovery_jobs(id) ON DELETE CASCADE,
    entity_type VARCHAR(20) NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    source_trust NUMERIC(5,4) NOT NULL DEFAULT 0.85,
    field_completeness NUMERIC(5,4) NOT NULL DEFAULT 0.5,
    verification_status VARCHAR(50),
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance JSONB NOT NULL DEFAULT '[]'::jsonb,
    explanation JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_discovery_job_hits_job_id ON discovery_job_hits(job_id);

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
INSERT INTO alembic_version (version_num) VALUES ('013')
ON CONFLICT (version_num) DO UPDATE SET version_num = EXCLUDED.version_num;
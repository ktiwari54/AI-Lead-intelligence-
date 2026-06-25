-- =============================================================================
-- AI Lead Intelligence Platform -- Physical Schema DDL
-- PostgreSQL 16 | UTC timestamps | UUID PKs | Soft delete | Row-level security
-- =============================================================================

BEGIN;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- =============================================================================
-- IDENTITY
-- =============================================================================

CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255)    NOT NULL,
    slug            VARCHAR(100)    NOT NULL UNIQUE,
    status          VARCHAR(20)     NOT NULL DEFAULT 'trial'
                        CHECK (status IN ('active','suspended','trial','cancelled')),
    subscription_plan VARCHAR(50)   NOT NULL DEFAULT 'free',
    credits         INTEGER         NOT NULL DEFAULT 100 CHECK (credits >= 0),
    settings        JSONB           NOT NULL DEFAULT '{}',
    logo_url        VARCHAR(500),
    website         VARCHAR(255),
    -- audit
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN         NOT NULL DEFAULT FALSE
);

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id     UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    status              VARCHAR(20)  NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('active','inactive','pending','suspended')),
    timezone            VARCHAR(50)  NOT NULL DEFAULT 'UTC',
    language            VARCHAR(10)  NOT NULL DEFAULT 'en',
    avatar_url          VARCHAR(500),
    last_login          TIMESTAMPTZ,
    email_verified      BOOLEAN      NOT NULL DEFAULT FALSE,
    email_verified_at   TIMESTAMPTZ,
    preferences         JSONB        NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE roles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        REFERENCES organizations(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    is_system       BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE permissions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module      VARCHAR(100) NOT NULL,
    action      VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (module, action)
);

CREATE TABLE role_permissions (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id       UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at    TIMESTAMPTZ,
    is_deleted    BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (role_id, permission_id)
);

CREATE TABLE user_roles (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id    UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (user_id, role_id)
);

CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    key_hash        VARCHAR(255) NOT NULL UNIQUE,
    key_prefix      VARCHAR(10)  NOT NULL,
    scopes          JSONB        NOT NULL DEFAULT '[]',
    expires_at      TIMESTAMPTZ,
    last_used_at    TIMESTAMPTZ,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE
);

-- =============================================================================
-- REFERENCE DATA
-- =============================================================================

CREATE TABLE industries (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    industry_name     VARCHAR(200) NOT NULL UNIQUE,
    parent_industry_id UUID        REFERENCES industries(id),
    description       TEXT,
    sic_code          VARCHAR(10),
    naics_code        VARCHAR(10),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ,
    is_deleted        BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE countries (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(100) NOT NULL UNIQUE,
    iso2        CHAR(2)      NOT NULL UNIQUE,
    iso3        CHAR(3)      NOT NULL UNIQUE,
    phone_code  VARCHAR(10),
    currency    VARCHAR(10),
    continent   VARCHAR(50),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE states (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    country_id  UUID        NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    code        VARCHAR(10),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE cities (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state_id    UUID        REFERENCES states(id) ON DELETE CASCADE,
    country_id  UUID        NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,
    latitude    NUMERIC(9,6),
    longitude   NUMERIC(9,6),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE technologies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    technology_name VARCHAR(200) NOT NULL UNIQUE,
    category        VARCHAR(100),
    vendor          VARCHAR(200),
    description     TEXT,
    logo_url        VARCHAR(500),
    website         VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

-- =============================================================================
-- COMPANY INTELLIGENCE
-- =============================================================================

CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    company_name    VARCHAR(500) NOT NULL,
    legal_name      VARCHAR(500),
    website         VARCHAR(500),
    domain          VARCHAR(255),
    industry_id     UUID        REFERENCES industries(id),
    country_id      UUID        REFERENCES countries(id),
    state_id        UUID        REFERENCES states(id),
    city_id         UUID        REFERENCES cities(id),
    address         TEXT,
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6),
    employee_count  INTEGER,
    employee_range  VARCHAR(50),
    revenue         NUMERIC(20,2),
    revenue_range   VARCHAR(50),
    ownership_type  VARCHAR(50),
    company_size    VARCHAR(50),
    description     TEXT,
    founded_year    SMALLINT,
    phone           VARCHAR(50),
    email           VARCHAR(255),
    confidence_score NUMERIC(5,2) DEFAULT 0.0,
    source          VARCHAR(100),
    external_id     VARCHAR(255),
    enriched_at     TIMESTAMPTZ,
    metadata        JSONB        NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE company_social_profiles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id  UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    platform    VARCHAR(50)  NOT NULL,
    profile_url VARCHAR(500) NOT NULL,
    handle      VARCHAR(200),
    followers   INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (company_id, platform)
);

CREATE TABLE company_technologies (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id    UUID        NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    technology_id UUID        NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
    confidence    NUMERIC(5,2) DEFAULT 1.0,
    detected_at   TIMESTAMPTZ,
    source        VARCHAR(100),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at    TIMESTAMPTZ,
    is_deleted    BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (company_id, technology_id)
);

-- =============================================================================
-- CONTACT INTELLIGENCE
-- =============================================================================

CREATE TABLE contacts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID        REFERENCES companies(id) ON DELETE SET NULL,
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100),
    full_name       VARCHAR(255),
    designation     VARCHAR(255),
    seniority       VARCHAR(50),
    department      VARCHAR(100),
    email           VARCHAR(255),
    email_status    VARCHAR(50),
    phone           VARCHAR(50),
    phone_type      VARCHAR(20),
    country_id      UUID        REFERENCES countries(id),
    city_id         UUID        REFERENCES cities(id),
    confidence_score NUMERIC(5,2) DEFAULT 0.0,
    is_decision_maker BOOLEAN   NOT NULL DEFAULT FALSE,
    source          VARCHAR(100),
    external_id     VARCHAR(255),
    enriched_at     TIMESTAMPTZ,
    metadata        JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE contact_social_profiles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id  UUID        NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    platform    VARCHAR(50)  NOT NULL,
    profile_url VARCHAR(500) NOT NULL,
    handle      VARCHAR(200),
    connections VARCHAR(50),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (contact_id, platform)
);

-- =============================================================================
-- SEARCH
-- =============================================================================

CREATE TABLE searches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    query           TEXT,
    filters         JSONB       NOT NULL DEFAULT '{}',
    search_type     VARCHAR(20) NOT NULL DEFAULT 'mixed'
                        CHECK (search_type IN ('company','contact','mixed')),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','running','completed','failed')),
    result_count    INTEGER     NOT NULL DEFAULT 0,
    execution_time_ms INTEGER,
    credits_used    INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE saved_searches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    name            VARCHAR(255) NOT NULL,
    query           TEXT,
    filters         JSONB       NOT NULL DEFAULT '{}',
    search_type     VARCHAR(20),
    alert_enabled   BOOLEAN     NOT NULL DEFAULT FALSE,
    alert_frequency VARCHAR(20),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE search_results (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_id   UUID        NOT NULL REFERENCES searches(id) ON DELETE CASCADE,
    company_id  UUID        REFERENCES companies(id),
    contact_id  UUID        REFERENCES contacts(id),
    score       FLOAT       NOT NULL DEFAULT 0.0,
    rank        INTEGER,
    source      VARCHAR(100),
    metadata    JSONB       NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE lead_scores (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id      UUID UNIQUE REFERENCES contacts(id) ON DELETE CASCADE,
    company_id      UUID UNIQUE REFERENCES companies(id) ON DELETE CASCADE,
    overall_score   FLOAT   NOT NULL DEFAULT 0.0,
    industry_score  FLOAT   NOT NULL DEFAULT 0.0,
    company_score   FLOAT   NOT NULL DEFAULT 0.0,
    engagement_score FLOAT  NOT NULL DEFAULT 0.0,
    technology_score FLOAT  NOT NULL DEFAULT 0.0,
    fit_score       FLOAT   NOT NULL DEFAULT 0.0,
    grade           VARCHAR(2),
    scoring_version VARCHAR(20),
    model_inputs    JSONB   NOT NULL DEFAULT '{}',
    scoring_reasons JSONB   NOT NULL DEFAULT '[]',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_lead_score_entity CHECK (contact_id IS NOT NULL OR company_id IS NOT NULL)
);

-- =============================================================================
-- ENRICHMENT
-- =============================================================================

CREATE TABLE email_verifications (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id  UUID        NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    email       VARCHAR(255) NOT NULL,
    status      VARCHAR(50),
    provider    VARCHAR(100),
    verified_at TIMESTAMPTZ,
    confidence  NUMERIC(5,2),
    mx_record   BOOLEAN,
    smtp_valid  BOOLEAN,
    disposable  BOOLEAN,
    role_based  BOOLEAN,
    free_provider BOOLEAN,
    raw_response  JSONB     NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE
);

-- =============================================================================
-- CRM
-- =============================================================================

CREATE TABLE activities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id      UUID        REFERENCES contacts(id) ON DELETE CASCADE,
    company_id      UUID        REFERENCES companies(id) ON DELETE CASCADE,
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    activity_type   VARCHAR(50) NOT NULL,
    description     TEXT,
    occurred_at     TIMESTAMPTZ,
    duration_minutes INTEGER,
    outcome         VARCHAR(100),
    metadata        JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE notes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id      UUID        REFERENCES contacts(id) ON DELETE CASCADE,
    company_id      UUID        REFERENCES companies(id) ON DELETE CASCADE,
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    note            TEXT        NOT NULL,
    is_pinned       BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE tags (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    color           CHAR(7),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (organization_id, name)
);

CREATE TABLE entity_tags (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tag_id      UUID        NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    entity_type VARCHAR(50)  NOT NULL CHECK (entity_type IN ('contact','company')),
    entity_id   UUID        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (tag_id, entity_type, entity_id)
);

CREATE TABLE tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    assigned_to     UUID        REFERENCES users(id),
    contact_id      UUID        REFERENCES contacts(id) ON DELETE SET NULL,
    company_id      UUID        REFERENCES companies(id) ON DELETE SET NULL,
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    status          VARCHAR(50)  NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open','in_progress','completed','cancelled')),
    priority        VARCHAR(20)  NOT NULL DEFAULT 'medium'
                        CHECK (priority IN ('low','medium','high','urgent')),
    due_date        TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE lists (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    list_type       VARCHAR(20)  NOT NULL DEFAULT 'static'
                        CHECK (list_type IN ('static','dynamic')),
    filters         JSONB        NOT NULL DEFAULT '{}',
    entity_type     VARCHAR(20)  NOT NULL CHECK (entity_type IN ('contact','company')),
    member_count    INTEGER      NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE list_members (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    list_id     UUID        NOT NULL REFERENCES lists(id) ON DELETE CASCADE,
    entity_type VARCHAR(20)  NOT NULL,
    entity_id   UUID        NOT NULL,
    added_by    UUID        REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    UNIQUE (list_id, entity_id)
);

-- =============================================================================
-- BILLING
-- =============================================================================

CREATE TABLE subscriptions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id         UUID        NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
    plan                    VARCHAR(50)  NOT NULL DEFAULT 'free',
    status                  VARCHAR(50)  NOT NULL DEFAULT 'trialing'
                                CHECK (status IN ('active','cancelled','past_due','trialing','paused')),
    credits_included        INTEGER      NOT NULL DEFAULT 100,
    credits_remaining       INTEGER      NOT NULL DEFAULT 100,
    renewal_date            TIMESTAMPTZ,
    trial_end_date          TIMESTAMPTZ,
    external_subscription_id VARCHAR(255),
    external_customer_id    VARCHAR(255),
    metadata                JSONB        NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ,
    is_deleted              BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE credit_transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID        NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID        REFERENCES users(id),
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('debit','credit','refund','adjustment')),
    credits         INTEGER     NOT NULL,
    balance_after   INTEGER     NOT NULL,
    description     VARCHAR(500),
    entity_type     VARCHAR(50),
    entity_id       UUID,
    metadata        JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

-- =============================================================================
-- SYSTEM
-- =============================================================================

CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        REFERENCES organizations(id),
    user_id         UUID        REFERENCES users(id),
    entity          VARCHAR(100) NOT NULL,
    entity_id       UUID,
    action          VARCHAR(100) NOT NULL,
    changes         JSONB       NOT NULL DEFAULT '{}',
    ip_address      VARCHAR(50),
    user_agent      TEXT,
    device          VARCHAR(100),
    request_id      VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID        NOT NULL REFERENCES organizations(id),
    type            VARCHAR(100) NOT NULL,
    title           VARCHAR(500) NOT NULL,
    body            TEXT,
    status          VARCHAR(20)  NOT NULL DEFAULT 'unread'
                        CHECK (status IN ('unread','read','archived')),
    read_at         TIMESTAMPTZ,
    channel         VARCHAR(50)  NOT NULL DEFAULT 'in_app',
    metadata        JSONB        NOT NULL DEFAULT '{}',
    entity_type     VARCHAR(50),
    entity_id       UUID,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE exports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    export_type     VARCHAR(50),
    format          VARCHAR(20)  NOT NULL DEFAULT 'csv'
                        CHECK (format IN ('csv','xlsx','json')),
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','processing','completed','failed')),
    file_path       VARCHAR(500),
    file_size_bytes INTEGER,
    record_count    INTEGER,
    filters         JSONB        NOT NULL DEFAULT '{}',
    credits_used    INTEGER      NOT NULL DEFAULT 0,
    error_message   TEXT,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE import_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    import_type     VARCHAR(50),
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
    file_path       VARCHAR(500),
    total_rows      INTEGER      NOT NULL DEFAULT 0,
    processed_rows  INTEGER      NOT NULL DEFAULT 0,
    success_rows    INTEGER      NOT NULL DEFAULT 0,
    error_rows      INTEGER      NOT NULL DEFAULT 0,
    field_mapping   JSONB        NOT NULL DEFAULT '{}',
    error_log       JSONB        NOT NULL DEFAULT '[]',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE connector_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        REFERENCES organizations(id),
    connector       VARCHAR(100) NOT NULL,
    job_type        VARCHAR(50),
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    retry_count     INTEGER      NOT NULL DEFAULT 0,
    max_retries     INTEGER      NOT NULL DEFAULT 3,
    input_params    JSONB        NOT NULL DEFAULT '{}',
    result_summary  JSONB        NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE connector_configs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    connector_name  VARCHAR(100) NOT NULL,
    is_enabled      BOOLEAN      NOT NULL DEFAULT TRUE,
    credentials     JSONB        NOT NULL DEFAULT '{}',
    settings        JSONB        NOT NULL DEFAULT '{}',
    last_health_check TIMESTAMPTZ,
    health_status   VARCHAR(20),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE,
    UNIQUE (organization_id, connector_name)
);

CREATE TABLE system_settings (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key         VARCHAR(200) NOT NULL UNIQUE,
    value       JSONB,
    description TEXT,
    is_public   BOOLEAN      NOT NULL DEFAULT FALSE,
    category    VARCHAR(100),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_deleted  BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE workflows (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID        NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID        NOT NULL REFERENCES users(id),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    trigger_type    VARCHAR(100),
    trigger_config  JSONB        NOT NULL DEFAULT '{}',
    actions         JSONB        NOT NULL DEFAULT '[]',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    execution_count INTEGER      NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE workflow_executions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id         UUID        NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status              VARCHAR(20)  NOT NULL DEFAULT 'running',
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    trigger_entity_type VARCHAR(50),
    trigger_entity_id   UUID,
    action_results      JSONB        NOT NULL DEFAULT '[]',
    error_message       TEXT,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE
);

COMMIT;

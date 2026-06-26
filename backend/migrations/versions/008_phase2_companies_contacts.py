"""Phase 2: Companies, Contacts, and Reference Data

Revision ID: 008
Revises: 007
Create Date: 2024-01-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    -- ============================================================
    -- REFERENCE / LOOKUP TABLES
    -- ============================================================

    CREATE TABLE IF NOT EXISTS core.countries (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        iso2                CHAR(2) NOT NULL UNIQUE,
        iso3                CHAR(3) NOT NULL UNIQUE,
        name                TEXT NOT NULL,
        phone_code          TEXT,
        currency            CHAR(3),
        continent           TEXT,
        capital             TEXT,
        region              TEXT,
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

    CREATE TABLE IF NOT EXISTS core.states (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        country_id          UUID NOT NULL REFERENCES core.countries(id),
        code                TEXT,
        name                TEXT NOT NULL,
        is_active           BOOLEAN NOT NULL DEFAULT TRUE,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        UNIQUE(country_id, code)
    );

    CREATE TABLE IF NOT EXISTS core.cities (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        country_id          UUID NOT NULL REFERENCES core.countries(id),
        state_id            UUID REFERENCES core.states(id),
        name                TEXT NOT NULL,
        geo_location        GEOGRAPHY(POINT, 4326),
        timezone            TEXT,
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
    CREATE INDEX IF NOT EXISTS idx_cities_geo ON core.cities USING GIST(geo_location);
    CREATE INDEX IF NOT EXISTS idx_cities_country ON core.cities(country_id);

    -- ============================================================
    -- INDUSTRIES
    -- ============================================================

    CREATE TABLE IF NOT EXISTS core.industries (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        parent_id           UUID REFERENCES core.industries(id),
        name                TEXT NOT NULL,
        slug                TEXT NOT NULL UNIQUE,
        naics_code          TEXT,
        sic_code            TEXT,
        description         TEXT,
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

    -- ============================================================
    -- TECHNOLOGIES
    -- ============================================================

    CREATE TABLE IF NOT EXISTS core.technology_categories (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        name                TEXT NOT NULL,
        slug                TEXT NOT NULL UNIQUE,
        description         TEXT,
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

    CREATE TABLE IF NOT EXISTS core.technologies (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        category_id         UUID REFERENCES core.technology_categories(id),
        name                TEXT NOT NULL,
        slug                TEXT NOT NULL UNIQUE,
        vendor              TEXT,
        website             TEXT,
        description         TEXT,
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

    -- ============================================================
    -- DESIGNATIONS
    -- ============================================================

    CREATE TABLE IF NOT EXISTS core.designations (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID,
        title               TEXT NOT NULL,
        slug                TEXT NOT NULL UNIQUE,
        level               TEXT NOT NULL CHECK (level IN ('c_suite','vp','director','manager','individual','senior','lead')),
        department_hint     TEXT,
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

    -- ============================================================
    -- COMPANIES
    -- ============================================================

    CREATE TABLE IF NOT EXISTS core.companies (
        id                      UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id         UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        name                    TEXT NOT NULL,
        legal_name              TEXT,
        domain                  TEXT,
        website                 TEXT,
        industry_id             UUID REFERENCES core.industries(id),
        industry_name           TEXT,
        sub_industry            TEXT,
        description             TEXT,
        founded_year            INTEGER,
        employee_count          INTEGER CHECK (employee_count >= 0),
        employee_range          TEXT,
        annual_revenue          NUMERIC(20, 2) CHECK (annual_revenue >= 0),
        revenue_range           TEXT,
        currency                CHAR(3) DEFAULT 'USD',
        country_id              UUID REFERENCES core.countries(id),
        country_code            CHAR(2),
        state                   TEXT,
        city                    TEXT,
        address                 TEXT,
        postal_code             TEXT,
        geo_location            GEOGRAPHY(POINT, 4326),
        timezone                TEXT,
        phone                   TEXT,
        email                   TEXT,
        linkedin_url            TEXT,
        twitter_url             TEXT,
        facebook_url            TEXT,
        stock_symbol            TEXT,
        stock_exchange          TEXT,
        is_public               BOOLEAN NOT NULL DEFAULT FALSE,
        total_funding           NUMERIC(20, 2),
        last_funding_date       DATE,
        last_funding_type       TEXT,
        last_funding_amount     NUMERIC(20, 2),
        duns_number             TEXT,
        lei_number              TEXT,
        tax_id                  TEXT,
        data_source             TEXT,
        data_confidence         INTEGER CHECK (data_confidence BETWEEN 0 AND 100),
        enrichment_status       TEXT NOT NULL DEFAULT 'pending',
        last_enriched_at        TIMESTAMPTZ,
        is_verified             BOOLEAN NOT NULL DEFAULT FALSE,
        logo_url                TEXT,
        tags                    TEXT[],
        fts                     TSVECTOR GENERATED ALWAYS AS (
                                    setweight(to_tsvector('english', coalesce(name,'')), 'A') ||
                                    setweight(to_tsvector('english', coalesce(domain,'')), 'B') ||
                                    setweight(to_tsvector('english', coalesce(description,'')), 'C')
                                ) STORED,
        status                  TEXT NOT NULL DEFAULT 'active',
        metadata                JSONB NOT NULL DEFAULT '{}',
        created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at              TIMESTAMPTZ,
        created_by              UUID,
        updated_by              UUID,
        version                 INTEGER NOT NULL DEFAULT 1
    );

    CREATE INDEX IF NOT EXISTS idx_companies_fts ON core.companies USING GIN(fts);
    CREATE INDEX IF NOT EXISTS idx_companies_name_trgm ON core.companies USING GIN(name gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_companies_domain_trgm ON core.companies USING GIN(domain gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_companies_geo ON core.companies USING GIST(geo_location);
    CREATE INDEX IF NOT EXISTS idx_companies_org_status ON core.companies(organization_id, status) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_companies_org_industry ON core.companies(organization_id, industry_id) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_companies_org_country ON core.companies(organization_id, country_code) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_companies_org_employees ON core.companies(organization_id, employee_count) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_companies_org_revenue ON core.companies(organization_id, annual_revenue) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_companies_metadata ON core.companies USING GIN(metadata);

    CREATE TABLE IF NOT EXISTS core.company_aliases (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        alias           TEXT NOT NULL,
        alias_type      TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(company_id, alias)
    );

    CREATE TABLE IF NOT EXISTS core.company_domains (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        domain          TEXT NOT NULL,
        is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
        is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(company_id, domain)
    );

    CREATE TABLE IF NOT EXISTS core.company_locations (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        location_type   TEXT NOT NULL DEFAULT 'office',
        is_headquarters BOOLEAN NOT NULL DEFAULT FALSE,
        address         TEXT,
        city            TEXT,
        state           TEXT,
        postal_code     TEXT,
        country_code    CHAR(2),
        country_id      UUID REFERENCES core.countries(id),
        geo_location    GEOGRAPHY(POINT, 4326),
        phone           TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_company_locations_geo ON core.company_locations USING GIST(geo_location);

    CREATE TABLE IF NOT EXISTS core.company_technologies (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        technology_id   UUID REFERENCES core.technologies(id),
        technology_name TEXT NOT NULL,
        category        TEXT,
        detected_at     TIMESTAMPTZ,
        confidence      INTEGER CHECK (confidence BETWEEN 0 AND 100),
        source          TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(company_id, technology_name)
    );

    CREATE TABLE IF NOT EXISTS core.company_social_profiles (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        platform        TEXT NOT NULL,
        url             TEXT NOT NULL,
        handle          TEXT,
        followers_count INTEGER,
        is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(company_id, platform)
    );

    CREATE TABLE IF NOT EXISTS core.company_financials (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        fiscal_year     INTEGER NOT NULL,
        revenue         NUMERIC(20, 2),
        gross_profit    NUMERIC(20, 2),
        net_income      NUMERIC(20, 2),
        ebitda          NUMERIC(20, 2),
        total_assets    NUMERIC(20, 2),
        total_debt      NUMERIC(20, 2),
        cash            NUMERIC(20, 2),
        currency        CHAR(3) DEFAULT 'USD',
        source          TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(company_id, fiscal_year)
    );

    CREATE TABLE IF NOT EXISTS core.company_growth (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id          UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        period_type         TEXT NOT NULL CHECK (period_type IN ('month','quarter','year')),
        period_date         DATE NOT NULL,
        headcount_growth    NUMERIC(8,4),
        revenue_growth      NUMERIC(8,4),
        web_traffic_growth  NUMERIC(8,4),
        job_openings        INTEGER,
        news_mentions       INTEGER,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        UNIQUE(company_id, period_type, period_date)
    );

    CREATE TABLE IF NOT EXISTS core.company_keywords (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        keyword         TEXT NOT NULL,
        weight          NUMERIC(5,4) NOT NULL DEFAULT 1.0,
        source          TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS idx_company_keywords_trgm ON core.company_keywords USING GIN(keyword gin_trgm_ops);

    CREATE TABLE IF NOT EXISTS core.company_tags (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        tag             TEXT NOT NULL,
        tagged_by       UUID,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, company_id, tag)
    );

    CREATE TABLE IF NOT EXISTS core.company_history (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL,
        company_id      UUID NOT NULL,
        changed_fields  TEXT[],
        old_values      JSONB,
        new_values      JSONB,
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
    SELECT create_monthly_partition('core.company_history', NOW());
    SELECT create_monthly_partition('core.company_history', NOW() + INTERVAL '1 month');

    CREATE TABLE IF NOT EXISTS core.company_relationships (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id          UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        related_company_id  UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
        relationship_type   TEXT NOT NULL CHECK (relationship_type IN ('parent','subsidiary','partner','competitor','investor','acquirer')),
        since_date          DATE,
        notes               TEXT,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, company_id, related_company_id, relationship_type)
    );

    -- ============================================================
    -- CONTACTS
    -- ============================================================

    CREATE TABLE IF NOT EXISTS core.contacts (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        company_id          UUID REFERENCES core.companies(id),
        first_name          TEXT,
        last_name           TEXT,
        full_name           TEXT GENERATED ALWAYS AS (trim(coalesce(first_name,'') || ' ' || coalesce(last_name,''))) STORED,
        email               CITEXT,
        phone               TEXT,
        mobile              TEXT,
        title               TEXT,
        seniority_level     TEXT,
        department          TEXT,
        designation_id      UUID REFERENCES core.designations(id),
        linkedin_url        TEXT,
        twitter_url         TEXT,
        location_city       TEXT,
        location_state      TEXT,
        location_country    CHAR(2),
        country_id          UUID REFERENCES core.countries(id),
        geo_location        GEOGRAPHY(POINT, 4326),
        timezone            TEXT,
        is_decision_maker   BOOLEAN NOT NULL DEFAULT FALSE,
        opt_out_email       BOOLEAN NOT NULL DEFAULT FALSE,
        opt_out_phone       BOOLEAN NOT NULL DEFAULT FALSE,
        opt_out_at          TIMESTAMPTZ,
        lead_score          INTEGER CHECK (lead_score BETWEEN 0 AND 100),
        data_source         TEXT,
        data_confidence     INTEGER CHECK (data_confidence BETWEEN 0 AND 100),
        enrichment_status   TEXT NOT NULL DEFAULT 'pending',
        last_enriched_at    TIMESTAMPTZ,
        is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
        avatar_url          TEXT,
        tags                TEXT[],
        fts                 TSVECTOR GENERATED ALWAYS AS (
                                setweight(to_tsvector('english', coalesce(first_name,'')||' '||coalesce(last_name,'')), 'A') ||
                                setweight(to_tsvector('english', coalesce(email::text,'')), 'B') ||
                                setweight(to_tsvector('english', coalesce(title,'')), 'C')
                            ) STORED,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1
    );

    CREATE INDEX IF NOT EXISTS idx_contacts_fts ON core.contacts USING GIN(fts);
    CREATE INDEX IF NOT EXISTS idx_contacts_fullname_trgm ON core.contacts USING GIN(full_name gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_contacts_email_trgm ON core.contacts USING GIN((email::text) gin_trgm_ops);
    CREATE INDEX IF NOT EXISTS idx_contacts_geo ON core.contacts USING GIST(geo_location);
    CREATE INDEX IF NOT EXISTS idx_contacts_org_company ON core.contacts(organization_id, company_id) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_contacts_org_status ON core.contacts(organization_id, status) WHERE deleted_at IS NULL;

    CREATE TABLE IF NOT EXISTS core.contact_emails (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
        email           CITEXT NOT NULL,
        email_type      TEXT DEFAULT 'work',
        is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
        is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
        deliverability  TEXT,
        deliverability_checked_at TIMESTAMPTZ,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(contact_id, email)
    );

    CREATE TABLE IF NOT EXISTS core.contact_phones (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
        phone           TEXT NOT NULL,
        phone_type      TEXT DEFAULT 'work',
        is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
        is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
        country_code    CHAR(2),
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS core.contact_social_profiles (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
        platform        TEXT NOT NULL,
        url             TEXT NOT NULL,
        handle          TEXT,
        followers_count INTEGER,
        is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(contact_id, platform)
    );

    CREATE TABLE IF NOT EXISTS core.contact_history (
        id              UUID NOT NULL DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL,
        contact_id      UUID NOT NULL,
        changed_fields  TEXT[],
        old_values      JSONB,
        new_values      JSONB,
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
    SELECT create_monthly_partition('core.contact_history', NOW());
    SELECT create_monthly_partition('core.contact_history', NOW() + INTERVAL '1 month');

    CREATE TABLE IF NOT EXISTS core.contact_skills (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
        skill           TEXT NOT NULL,
        proficiency     TEXT,
        years_of_exp    INTEGER,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(contact_id, skill)
    );

    CREATE TABLE IF NOT EXISTS core.contact_certifications (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
        name            TEXT NOT NULL,
        issuer          TEXT,
        issued_date     DATE,
        expiry_date     DATE,
        credential_url  TEXT,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS core.contact_tags (
        id              UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
        tag             TEXT NOT NULL,
        tagged_by       UUID,
        status          TEXT NOT NULL DEFAULT 'active',
        metadata        JSONB NOT NULL DEFAULT '{}',
        created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at      TIMESTAMPTZ,
        created_by      UUID,
        updated_by      UUID,
        version         INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, contact_id, tag)
    );

    CREATE TABLE IF NOT EXISTS core.contact_relationships (
        id                  UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
        organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
        contact_id          UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
        related_contact_id  UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
        relationship_type   TEXT NOT NULL,
        notes               TEXT,
        status              TEXT NOT NULL DEFAULT 'active',
        metadata            JSONB NOT NULL DEFAULT '{}',
        created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at          TIMESTAMPTZ,
        created_by          UUID,
        updated_by          UUID,
        version             INTEGER NOT NULL DEFAULT 1,
        UNIQUE(organization_id, contact_id, related_contact_id, relationship_type)
    );

    -- ============================================================
    -- TRIGGERS
    -- ============================================================

    CREATE OR REPLACE FUNCTION core.sync_location_from_lat_lon()
    RETURNS TRIGGER LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.geo_location IS NOT NULL THEN
            RETURN NEW;
        END IF;
        RETURN NEW;
    END;
    $$;

    -- updated_at triggers
    CREATE OR REPLACE TRIGGER trg_countries_updated_at BEFORE UPDATE ON core.countries FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_states_updated_at BEFORE UPDATE ON core.states FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_cities_updated_at BEFORE UPDATE ON core.cities FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_industries_updated_at BEFORE UPDATE ON core.industries FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_technologies_updated_at BEFORE UPDATE ON core.technologies FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_designations_updated_at BEFORE UPDATE ON core.designations FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_companies_updated_at BEFORE UPDATE ON core.companies FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_contacts_updated_at BEFORE UPDATE ON core.contacts FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_company_locations_updated_at BEFORE UPDATE ON core.company_locations FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    CREATE OR REPLACE TRIGGER trg_contact_emails_updated_at BEFORE UPDATE ON core.contact_emails FOR EACH ROW EXECUTE FUNCTION set_updated_at();

    -- ============================================================
    -- RLS
    -- ============================================================

    ALTER TABLE core.companies ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS companies_org_isolation ON core.companies;
    CREATE POLICY companies_org_isolation ON core.companies
        USING (organization_id = current_org_id());

    ALTER TABLE core.contacts ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS contacts_org_isolation ON core.contacts;
    CREATE POLICY contacts_org_isolation ON core.contacts
        USING (organization_id = current_org_id());

    ALTER TABLE core.company_tags ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS company_tags_org_isolation ON core.company_tags;
    CREATE POLICY company_tags_org_isolation ON core.company_tags
        USING (organization_id = current_org_id());

    ALTER TABLE core.contact_tags ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS contact_tags_org_isolation ON core.contact_tags;
    CREATE POLICY contact_tags_org_isolation ON core.contact_tags
        USING (organization_id = current_org_id());
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS core.contact_relationships CASCADE;
    DROP TABLE IF EXISTS core.contact_tags CASCADE;
    DROP TABLE IF EXISTS core.contact_certifications CASCADE;
    DROP TABLE IF EXISTS core.contact_skills CASCADE;
    DROP TABLE IF EXISTS core.contact_history CASCADE;
    DROP TABLE IF EXISTS core.contact_social_profiles CASCADE;
    DROP TABLE IF EXISTS core.contact_phones CASCADE;
    DROP TABLE IF EXISTS core.contact_emails CASCADE;
    DROP TABLE IF EXISTS core.contacts CASCADE;
    DROP TABLE IF EXISTS core.company_relationships CASCADE;
    DROP TABLE IF EXISTS core.company_history CASCADE;
    DROP TABLE IF EXISTS core.company_tags CASCADE;
    DROP TABLE IF EXISTS core.company_keywords CASCADE;
    DROP TABLE IF EXISTS core.company_growth CASCADE;
    DROP TABLE IF EXISTS core.company_financials CASCADE;
    DROP TABLE IF EXISTS core.company_social_profiles CASCADE;
    DROP TABLE IF EXISTS core.company_technologies CASCADE;
    DROP TABLE IF EXISTS core.company_locations CASCADE;
    DROP TABLE IF EXISTS core.company_domains CASCADE;
    DROP TABLE IF EXISTS core.company_aliases CASCADE;
    DROP TABLE IF EXISTS core.companies CASCADE;
    DROP TABLE IF EXISTS core.designations CASCADE;
    DROP TABLE IF EXISTS core.technologies CASCADE;
    DROP TABLE IF EXISTS core.technology_categories CASCADE;
    DROP TABLE IF EXISTS core.industries CASCADE;
    DROP TABLE IF EXISTS core.cities CASCADE;
    DROP TABLE IF EXISTS core.states CASCADE;
    DROP TABLE IF EXISTS core.countries CASCADE;
    """)

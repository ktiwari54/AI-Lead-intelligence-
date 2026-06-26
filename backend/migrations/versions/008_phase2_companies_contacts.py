"""phase2_companies_contacts: enterprise companies and contacts schema

Revision ID: 008
Revises: 007
Create Date: 2026-01-01
"""
from __future__ import annotations
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Reference Tables ───────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.countries (
            id          UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            name        VARCHAR(255) NOT NULL,
            iso2        CHAR(2) NOT NULL UNIQUE,
            iso3        CHAR(3) NOT NULL UNIQUE,
            phone_code  VARCHAR(10),
            currency    VARCHAR(10),
            continent   VARCHAR(50),
            region      VARCHAR(100),
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            location    GEOGRAPHY(POINT, 4326),
            bounding_box GEOGRAPHY(POLYGON, 4326),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata    JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_countries_iso2 ON core.countries(iso2)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.states (
            id          UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            country_id  UUID NOT NULL REFERENCES core.countries(id),
            name        VARCHAR(255) NOT NULL,
            code        VARCHAR(20),
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            location    GEOGRAPHY(POINT, 4326),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata    JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_states_country ON core.states(country_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.cities (
            id          UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            state_id    UUID REFERENCES core.states(id),
            country_id  UUID NOT NULL REFERENCES core.countries(id),
            name        VARCHAR(255) NOT NULL,
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            location    GEOGRAPHY(POINT, 4326),
            latitude    DOUBLE PRECISION,
            longitude   DOUBLE PRECISION,
            timezone    VARCHAR(100),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata    JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_cities_country ON core.cities(country_id)")
    op.execute("CREATE INDEX idx_cities_state ON core.cities(state_id)")
    op.execute("CREATE INDEX idx_cities_location ON core.cities USING GIST(location) WHERE location IS NOT NULL")
    op.execute("CREATE INDEX idx_cities_name_trgm ON core.cities USING GIN(name gin_trgm_ops)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.industries (
            id          UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            name        VARCHAR(255) NOT NULL UNIQUE,
            slug        VARCHAR(255) NOT NULL UNIQUE,
            parent_id   UUID REFERENCES core.industries(id),
            description TEXT,
            naics_code  VARCHAR(20),
            sic_code    VARCHAR(20),
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata    JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.technology_categories (
            id          UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            name        VARCHAR(255) NOT NULL UNIQUE,
            slug        VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            icon_url    VARCHAR(500),
            parent_id   UUID REFERENCES core.technology_categories(id),
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata    JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.technologies (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            category_id     UUID REFERENCES core.technology_categories(id),
            name            VARCHAR(255) NOT NULL,
            slug            VARCHAR(255) NOT NULL UNIQUE,
            vendor          VARCHAR(255),
            description     TEXT,
            website         VARCHAR(500),
            logo_url        VARCHAR(1000),
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_technologies_name_trgm ON core.technologies USING GIN(name gin_trgm_ops)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.designations (
            id          UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            title       VARCHAR(255) NOT NULL UNIQUE,
            level       VARCHAR(50),   -- junior, mid, senior, lead, manager, director, vp, c-suite
            department  VARCHAR(100),
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata    JSONB NOT NULL DEFAULT '{}'
        )
    """)

    # ── Companies ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.companies (
            id                  UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            name                VARCHAR(500) NOT NULL,
            legal_name          VARCHAR(500),
            domain              VARCHAR(255),
            website             VARCHAR(1000),
            logo_url            VARCHAR(1000),
            description         TEXT,
            short_description   VARCHAR(500),
            tagline             VARCHAR(300),
            founded_year        SMALLINT,
            industry_id         UUID REFERENCES core.industries(id),
            industry            VARCHAR(255),          -- denormalized
            sub_industry        VARCHAR(255),
            company_type        VARCHAR(50),           -- private, public, nonprofit, government
            stock_symbol        VARCHAR(20),
            stock_exchange      VARCHAR(50),
            employee_count      INTEGER,
            employee_range      VARCHAR(50),           -- '1-10', '11-50', '51-200', etc.
            revenue             NUMERIC(18,2),
            revenue_range       VARCHAR(50),
            revenue_currency    VARCHAR(10) NOT NULL DEFAULT 'USD',
            total_funding       NUMERIC(18,2),
            last_funding_round  VARCHAR(50),
            last_funding_date   DATE,
            country_id          UUID REFERENCES core.countries(id),
            country             VARCHAR(100),          -- denormalized
            state               VARCHAR(100),
            city                VARCHAR(100),
            zip_code            VARCHAR(20),
            address             TEXT,
            location            GEOGRAPHY(POINT, 4326),
            latitude            DOUBLE PRECISION,
            longitude           DOUBLE PRECISION,
            phone               VARCHAR(50),
            email               citext,
            linkedin_url        VARCHAR(500),
            twitter_url         VARCHAR(500),
            facebook_url        VARCHAR(500),
            crunchbase_url      VARCHAR(500),
            sic_code            VARCHAR(20),
            naics_code          VARCHAR(20),
            duns_number         VARCHAR(50),
            lei_number          VARCHAR(50),
            vat_number          VARCHAR(50),
            is_public           BOOLEAN NOT NULL DEFAULT FALSE,
            is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
            verified_at         TIMESTAMPTZ,
            data_source         VARCHAR(100),
            data_source_id      VARCHAR(255),
            data_confidence     NUMERIC(5,2),         -- 0-100
            last_enriched_at    TIMESTAMPTZ,
            enrichment_status   VARCHAR(50),
            fts                 TSVECTOR GENERATED ALWAYS AS (
                                    setweight(to_tsvector('english', coalesce(name,'')), 'A') ||
                                    setweight(to_tsvector('english', coalesce(description,'')), 'B') ||
                                    setweight(to_tsvector('english', coalesce(industry,'')), 'C') ||
                                    setweight(to_tsvector('english', coalesce(country,'')), 'D')
                                ) STORED,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at          TIMESTAMPTZ,
            created_by          UUID REFERENCES auth.users(id),
            updated_by          UUID REFERENCES auth.users(id),
            version             INTEGER NOT NULL DEFAULT 1,
            status              VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata            JSONB NOT NULL DEFAULT '{}'
        )
    """)
    # Core indexes
    op.execute("CREATE INDEX idx_companies_org ON core.companies(organization_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_companies_domain ON core.companies(domain) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_companies_country ON core.companies(country_id, organization_id)")
    op.execute("CREATE INDEX idx_companies_industry ON core.companies(industry_id, organization_id)")
    op.execute("CREATE INDEX idx_companies_fts ON core.companies USING GIN(fts)")
    op.execute("CREATE INDEX idx_companies_name_trgm ON core.companies USING GIN(name gin_trgm_ops)")
    op.execute("CREATE INDEX idx_companies_location ON core.companies USING GIST(location) WHERE location IS NOT NULL AND deleted_at IS NULL")
    op.execute("CREATE INDEX idx_companies_employee ON core.companies(employee_count, organization_id)")
    op.execute("CREATE INDEX idx_companies_revenue ON core.companies(revenue, organization_id)")
    op.execute("CREATE INDEX idx_companies_status ON core.companies(status, organization_id, updated_at DESC)")
    op.execute("CREATE INDEX idx_companies_data_source ON core.companies(data_source, data_source_id)")
    op.execute("CREATE INDEX idx_companies_metadata ON core.companies USING GIN(metadata)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_aliases (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            alias           VARCHAR(500) NOT NULL,
            alias_type      VARCHAR(50),  -- former_name, trade_name, abbreviation
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(company_id, alias)
        )
    """)
    op.execute("CREATE INDEX idx_company_aliases_trgm ON core.company_aliases USING GIN(alias gin_trgm_ops)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_domains (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            domain          VARCHAR(255) NOT NULL,
            is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
            is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_company_domains_domain ON core.company_domains(domain)")
    op.execute("CREATE INDEX idx_company_domains_company ON core.company_domains(company_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_locations (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            location_type   VARCHAR(50) NOT NULL DEFAULT 'headquarters',  -- hq, branch, remote
            address_line1   VARCHAR(500),
            address_line2   VARCHAR(500),
            city            VARCHAR(255),
            state           VARCHAR(255),
            zip_code        VARCHAR(20),
            country         VARCHAR(100),
            country_id      UUID REFERENCES core.countries(id),
            location        GEOGRAPHY(POINT, 4326),
            latitude        DOUBLE PRECISION,
            longitude       DOUBLE PRECISION,
            is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
            employee_count  INTEGER,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_company_locations_company ON core.company_locations(company_id)")
    op.execute("CREATE INDEX idx_company_locations_geo ON core.company_locations USING GIST(location) WHERE location IS NOT NULL")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_technologies (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            technology_id   UUID REFERENCES core.technologies(id),
            technology_name VARCHAR(255) NOT NULL,   -- denormalized
            category        VARCHAR(100),
            confidence      NUMERIC(5,2),
            first_detected  DATE,
            last_confirmed  DATE,
            is_current      BOOLEAN NOT NULL DEFAULT TRUE,
            source          VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(company_id, technology_name)
        )
    """)
    op.execute("CREATE INDEX idx_company_tech_company ON core.company_technologies(company_id)")
    op.execute("CREATE INDEX idx_company_tech_name ON core.company_technologies USING GIN(technology_name gin_trgm_ops)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_social_profiles (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            platform        VARCHAR(50) NOT NULL,   -- linkedin, twitter, facebook, instagram, youtube
            profile_url     VARCHAR(1000) NOT NULL,
            handle          VARCHAR(255),
            followers       INTEGER,
            verified        BOOLEAN NOT NULL DEFAULT FALSE,
            last_synced_at  TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(company_id, platform)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_financials (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            fiscal_year     SMALLINT NOT NULL,
            revenue         NUMERIC(18,2),
            gross_profit    NUMERIC(18,2),
            net_income      NUMERIC(18,2),
            ebitda          NUMERIC(18,2),
            total_assets    NUMERIC(18,2),
            total_debt      NUMERIC(18,2),
            cash_position   NUMERIC(18,2),
            currency        VARCHAR(10) NOT NULL DEFAULT 'USD',
            source          VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(company_id, fiscal_year)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_growth (
            id                  UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id          UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            period              VARCHAR(20) NOT NULL,  -- '2024-Q1', '2024'
            headcount_start     INTEGER,
            headcount_end       INTEGER,
            headcount_growth_pct NUMERIC(6,2),
            revenue_growth_pct  NUMERIC(6,2),
            web_traffic_growth  NUMERIC(6,2),
            job_postings        INTEGER,
            source              VARCHAR(100),
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version             INTEGER NOT NULL DEFAULT 1,
            metadata            JSONB NOT NULL DEFAULT '{}',
            UNIQUE(company_id, period)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_keywords (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            keyword         VARCHAR(255) NOT NULL,
            weight          NUMERIC(5,2) NOT NULL DEFAULT 1.0,
            source          VARCHAR(50),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(company_id, keyword)
        )
    """)
    op.execute("CREATE INDEX idx_company_keywords_trgm ON core.company_keywords USING GIN(keyword gin_trgm_ops)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_tags (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            tag             VARCHAR(100) NOT NULL,
            color           VARCHAR(20),
            created_by      UUID REFERENCES auth.users(id),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(organization_id, company_id, tag)
        )
    """)
    op.execute("CREATE INDEX idx_company_tags_org ON core.company_tags(organization_id, tag)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_history (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id      UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            changed_fields  TEXT[] NOT NULL,
            old_values      JSONB NOT NULL DEFAULT '{}',
            new_values      JSONB NOT NULL DEFAULT '{}',
            change_source   VARCHAR(100),  -- user, enrichment, import
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID REFERENCES auth.users(id),
            metadata        JSONB NOT NULL DEFAULT '{}'
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("CREATE TABLE core.company_history_2026_06 PARTITION OF core.company_history FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')")
    op.execute("CREATE TABLE core.company_history_2026_07 PARTITION OF core.company_history FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')")
    op.execute("CREATE TABLE core.company_history_future PARTITION OF core.company_history FOR VALUES FROM ('2026-08-01') TO ('2030-01-01')")
    op.execute("CREATE INDEX idx_company_history_company ON core.company_history(company_id, created_at DESC)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.company_relationships (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            from_company_id UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            to_company_id   UUID NOT NULL REFERENCES core.companies(id) ON DELETE CASCADE,
            relationship    VARCHAR(100) NOT NULL,  -- parent, subsidiary, partner, competitor, investor, acquirer
            notes           TEXT,
            started_at      DATE,
            ended_at        DATE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_company_rel_from ON core.company_relationships(from_company_id)")
    op.execute("CREATE INDEX idx_company_rel_to ON core.company_relationships(to_company_id)")

    # ── Contacts ────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contacts (
            id                  UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            company_id          UUID REFERENCES core.companies(id) ON DELETE SET NULL,
            first_name          VARCHAR(100),
            last_name           VARCHAR(100),
            full_name           VARCHAR(255) GENERATED ALWAYS AS (
                                    TRIM(COALESCE(first_name,'') || ' ' || COALESCE(last_name,''))
                                ) STORED,
            email               citext,
            email_verified      BOOLEAN NOT NULL DEFAULT FALSE,
            phone               VARCHAR(50),
            phone_verified      BOOLEAN NOT NULL DEFAULT FALSE,
            designation         VARCHAR(255),
            designation_id      UUID REFERENCES core.designations(id),
            department          VARCHAR(100),
            seniority_level     VARCHAR(50),    -- c_suite, vp, director, manager, individual
            decision_maker      BOOLEAN NOT NULL DEFAULT FALSE,
            linkedin_url        VARCHAR(500),
            twitter_url         VARCHAR(500),
            github_url          VARCHAR(500),
            website_url         VARCHAR(500),
            avatar_url          VARCHAR(1000),
            bio                 TEXT,
            location            VARCHAR(255),
            city                VARCHAR(100),
            state               VARCHAR(100),
            country             VARCHAR(100),
            country_id          UUID REFERENCES core.countries(id),
            geo_location        GEOGRAPHY(POINT, 4326),
            skills              TEXT[],
            languages           TEXT[],
            interests           TEXT[],
            is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
            verified_at         TIMESTAMPTZ,
            opt_out_email       BOOLEAN NOT NULL DEFAULT FALSE,
            opt_out_phone       BOOLEAN NOT NULL DEFAULT FALSE,
            opt_out_at          TIMESTAMPTZ,
            data_source         VARCHAR(100),
            data_source_id      VARCHAR(255),
            data_confidence     NUMERIC(5,2),
            last_enriched_at    TIMESTAMPTZ,
            enrichment_status   VARCHAR(50),
            fts                 TSVECTOR GENERATED ALWAYS AS (
                                    setweight(to_tsvector('english', coalesce(first_name,'')), 'A') ||
                                    setweight(to_tsvector('english', coalesce(last_name,'')), 'A') ||
                                    setweight(to_tsvector('english', coalesce(email::TEXT,'')), 'B') ||
                                    setweight(to_tsvector('english', coalesce(designation,'')), 'C')
                                ) STORED,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at          TIMESTAMPTZ,
            created_by          UUID REFERENCES auth.users(id),
            updated_by          UUID REFERENCES auth.users(id),
            version             INTEGER NOT NULL DEFAULT 1,
            status              VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata            JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_contacts_org ON core.contacts(organization_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_contacts_company ON core.contacts(company_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_contacts_email ON core.contacts(email) WHERE deleted_at IS NULL AND email IS NOT NULL")
    op.execute("CREATE INDEX idx_contacts_fts ON core.contacts USING GIN(fts)")
    op.execute("CREATE INDEX idx_contacts_name_trgm ON core.contacts USING GIN(full_name gin_trgm_ops)")
    op.execute("CREATE INDEX idx_contacts_email_trgm ON core.contacts USING GIN((email::TEXT) gin_trgm_ops) WHERE email IS NOT NULL")
    op.execute("CREATE INDEX idx_contacts_designation ON core.contacts(designation_id, organization_id)")
    op.execute("CREATE INDEX idx_contacts_seniority ON core.contacts(seniority_level, organization_id)")
    op.execute("CREATE INDEX idx_contacts_status ON core.contacts(status, organization_id, updated_at DESC)")
    op.execute("CREATE INDEX idx_contacts_metadata ON core.contacts USING GIN(metadata)")
    op.execute("CREATE INDEX idx_contacts_geo ON core.contacts USING GIST(geo_location) WHERE geo_location IS NOT NULL")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contact_emails (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            email           citext NOT NULL,
            email_type      VARCHAR(50) NOT NULL DEFAULT 'work',  -- work, personal, other
            is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
            is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
            verified_at     TIMESTAMPTZ,
            is_deliverable  BOOLEAN,
            deliverability_checked_at TIMESTAMPTZ,
            opt_out         BOOLEAN NOT NULL DEFAULT FALSE,
            opt_out_at      TIMESTAMPTZ,
            source          VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(contact_id, email)
        )
    """)
    op.execute("CREATE INDEX idx_contact_emails_email ON core.contact_emails(email)")
    op.execute("CREATE INDEX idx_contact_emails_contact ON core.contact_emails(contact_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contact_phones (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            phone           VARCHAR(50) NOT NULL,
            phone_type      VARCHAR(50) NOT NULL DEFAULT 'work',  -- work, mobile, home, fax
            country_code    VARCHAR(10),
            is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
            is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
            is_valid        BOOLEAN,
            opt_out         BOOLEAN NOT NULL DEFAULT FALSE,
            source          VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(contact_id, phone)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contact_social_profiles (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            platform        VARCHAR(50) NOT NULL,
            profile_url     VARCHAR(1000) NOT NULL,
            handle          VARCHAR(255),
            followers       INTEGER,
            is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
            last_synced_at  TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(contact_id, platform)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contact_history (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            changed_fields  TEXT[] NOT NULL,
            old_values      JSONB NOT NULL DEFAULT '{}',
            new_values      JSONB NOT NULL DEFAULT '{}',
            change_source   VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      UUID REFERENCES auth.users(id),
            metadata        JSONB NOT NULL DEFAULT '{}'
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("CREATE TABLE core.contact_history_2026_06 PARTITION OF core.contact_history FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')")
    op.execute("CREATE TABLE core.contact_history_future PARTITION OF core.contact_history FOR VALUES FROM ('2026-07-01') TO ('2030-01-01')")
    op.execute("CREATE INDEX idx_contact_history_contact ON core.contact_history(contact_id, created_at DESC)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contact_skills (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            skill           VARCHAR(255) NOT NULL,
            proficiency     VARCHAR(50),   -- beginner, intermediate, advanced, expert
            years           SMALLINT,
            source          VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(contact_id, skill)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contact_certifications (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            name            VARCHAR(255) NOT NULL,
            issuer          VARCHAR(255),
            issued_at       DATE,
            expires_at      DATE,
            credential_id   VARCHAR(255),
            credential_url  VARCHAR(1000),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contact_tags (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            contact_id      UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            tag             VARCHAR(100) NOT NULL,
            color           VARCHAR(20),
            created_by      UUID REFERENCES auth.users(id),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(organization_id, contact_id, tag)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS core.contact_relationships (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            from_contact_id UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            to_contact_id   UUID NOT NULL REFERENCES core.contacts(id) ON DELETE CASCADE,
            relationship    VARCHAR(100) NOT NULL,  -- reports_to, colleague, knows
            strength        NUMERIC(3,2),           -- 0.0 - 1.0
            notes           TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    # ── Location sync triggers ────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION sync_location_from_lat_lon()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
                NEW.location := ST_GeographyFromText(
                    'SRID=4326;POINT(' || NEW.longitude || ' ' || NEW.latitude || ')'
                );
            END IF;
            RETURN NEW;
        END;
        $$
    """)

    for tbl, col in [("core.companies", "location"), ("core.company_locations", "location")]:
        name = tbl.split(".")[1]
        op.execute(f"""
            DROP TRIGGER IF EXISTS trg_{name}_sync_location ON {tbl};
            CREATE TRIGGER trg_{name}_sync_location
            BEFORE INSERT OR UPDATE OF latitude, longitude ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION sync_location_from_lat_lon()
        """)

    # ── Updated_at triggers ───────────────────────────────────────────────
    for tbl in ["core.companies", "core.contacts", "core.company_locations", "core.company_technologies", "core.contact_emails"]:
        name = tbl.split(".")[1]
        op.execute(f"""
            CREATE OR REPLACE TRIGGER trg_{name}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """)

    # ── RLS ───────────────────────────────────────────────────────────────
    for tbl in ["core.companies", "core.contacts", "core.company_tags", "core.contact_tags"]:
        name = tbl.split(".")[1]
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY {name}_org_isolation ON {tbl}
            USING (organization_id = current_org_id())
        """)


def downgrade() -> None:
    for tbl in ["core.contact_relationships", "core.contact_tags", "core.contact_certifications",
                "core.contact_skills", "core.contact_history", "core.contact_social_profiles",
                "core.contact_phones", "core.contact_emails", "core.contacts",
                "core.company_relationships", "core.company_tags", "core.company_history",
                "core.company_keywords", "core.company_growth", "core.company_financials",
                "core.company_social_profiles", "core.company_technologies", "core.company_locations",
                "core.company_domains", "core.company_aliases", "core.companies",
                "core.designations", "core.technologies", "core.technology_categories",
                "core.industries", "core.cities", "core.states", "core.countries"]:
        op.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")
    op.execute("DROP FUNCTION IF EXISTS sync_location_from_lat_lon() CASCADE")

"""phase2_identity: complete identity, auth, org, user domain

Revision ID: 007
Revises: 006
Create Date: 2026-01-01
"""
from __future__ import annotations
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Subscription Plans (needed by orgs) ────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS billing.subscription_plans (
            id              UUID        NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            name            VARCHAR(100) NOT NULL,
            slug            VARCHAR(100) NOT NULL UNIQUE,
            description     TEXT,
            price_monthly   NUMERIC(10,2) NOT NULL DEFAULT 0,
            price_annual    NUMERIC(10,2) NOT NULL DEFAULT 0,
            credits_monthly INTEGER NOT NULL DEFAULT 0,
            max_users       INTEGER NOT NULL DEFAULT 5,
            max_exports     INTEGER NOT NULL DEFAULT 100,
            max_api_calls   INTEGER NOT NULL DEFAULT 10000,
            features        JSONB NOT NULL DEFAULT '{}',
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            sort_order      INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    # ── Organizations ───────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organizations (
            id                  UUID        NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            name                VARCHAR(255) NOT NULL,
            slug                VARCHAR(255) NOT NULL UNIQUE,
            display_name        VARCHAR(255),
            description         TEXT,
            website             VARCHAR(500),
            logo_url            VARCHAR(1000),
            industry            VARCHAR(100),
            company_size        VARCHAR(50),
            country             VARCHAR(100),
            timezone            VARCHAR(100) NOT NULL DEFAULT 'UTC',
            locale              VARCHAR(20) NOT NULL DEFAULT 'en',
            currency            VARCHAR(10) NOT NULL DEFAULT 'USD',
            plan_id             UUID REFERENCES billing.subscription_plans(id),
            plan_started_at     TIMESTAMPTZ,
            trial_ends_at       TIMESTAMPTZ,
            is_trial            BOOLEAN NOT NULL DEFAULT TRUE,
            is_active           BOOLEAN NOT NULL DEFAULT TRUE,
            is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
            verified_at         TIMESTAMPTZ,
            suspended_at        TIMESTAMPTZ,
            suspension_reason   TEXT,
            max_users           INTEGER NOT NULL DEFAULT 5,
            max_companies       INTEGER NOT NULL DEFAULT 10000,
            max_contacts        INTEGER NOT NULL DEFAULT 50000,
            max_exports_monthly INTEGER NOT NULL DEFAULT 100,
            credits_balance     INTEGER NOT NULL DEFAULT 0,
            credits_used        INTEGER NOT NULL DEFAULT 0,
            owner_id            UUID,  -- FK to users added after users table
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at          TIMESTAMPTZ,
            created_by          UUID,
            updated_by          UUID,
            version             INTEGER NOT NULL DEFAULT 1,
            status              VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata            JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_organizations_slug ON auth.organizations(slug)")
    op.execute("CREATE INDEX idx_organizations_status ON auth.organizations(status) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_organizations_plan ON auth.organizations(plan_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organization_settings (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            key             VARCHAR(255) NOT NULL,
            value           JSONB NOT NULL DEFAULT '{}',
            category        VARCHAR(100),
            is_public       BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            created_by      UUID,
            updated_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(organization_id, key)
        )
    """)
    op.execute("CREATE INDEX idx_org_settings_org ON auth.organization_settings(organization_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organization_domains (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            domain          VARCHAR(255) NOT NULL,
            is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
            is_verified     BOOLEAN NOT NULL DEFAULT FALSE,
            verified_at     TIMESTAMPTZ,
            dns_token       VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            created_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(domain)
        )
    """)
    op.execute("CREATE INDEX idx_org_domains_org ON auth.organization_domains(organization_id)")
    op.execute("CREATE INDEX idx_org_domains_domain ON auth.organization_domains(domain)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organization_branding (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL UNIQUE REFERENCES auth.organizations(id) ON DELETE CASCADE,
            primary_color   VARCHAR(20),
            secondary_color VARCHAR(20),
            logo_url        VARCHAR(1000),
            favicon_url     VARCHAR(1000),
            banner_url      VARCHAR(1000),
            email_header    TEXT,
            email_footer    TEXT,
            custom_css      TEXT,
            font_family     VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organization_security (
            id                      UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id         UUID NOT NULL UNIQUE REFERENCES auth.organizations(id) ON DELETE CASCADE,
            enforce_mfa             BOOLEAN NOT NULL DEFAULT FALSE,
            allowed_ip_ranges       TEXT[],
            max_session_hours       INTEGER NOT NULL DEFAULT 24,
            password_min_length     INTEGER NOT NULL DEFAULT 8,
            password_require_upper  BOOLEAN NOT NULL DEFAULT TRUE,
            password_require_number BOOLEAN NOT NULL DEFAULT TRUE,
            password_require_symbol BOOLEAN NOT NULL DEFAULT FALSE,
            sso_enabled             BOOLEAN NOT NULL DEFAULT FALSE,
            sso_provider            VARCHAR(50),
            sso_config              JSONB NOT NULL DEFAULT '{}',
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version                 INTEGER NOT NULL DEFAULT 1,
            metadata                JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organization_features (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            feature_key     VARCHAR(100) NOT NULL,
            is_enabled      BOOLEAN NOT NULL DEFAULT FALSE,
            config          JSONB NOT NULL DEFAULT '{}',
            expires_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(organization_id, feature_key)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organization_integrations (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            integration_key VARCHAR(100) NOT NULL,
            provider        VARCHAR(100) NOT NULL,
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            credentials     JSONB NOT NULL DEFAULT '{}',  -- encrypted at app layer
            settings        JSONB NOT NULL DEFAULT '{}',
            last_synced_at  TIMESTAMPTZ,
            sync_status     VARCHAR(50),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            created_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(organization_id, integration_key)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organization_storage (
            id                  UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id     UUID NOT NULL UNIQUE REFERENCES auth.organizations(id) ON DELETE CASCADE,
            storage_used_bytes  BIGINT NOT NULL DEFAULT 0,
            storage_limit_bytes BIGINT NOT NULL DEFAULT 5368709120,  -- 5GB
            files_count         INTEGER NOT NULL DEFAULT 0,
            exports_count       INTEGER NOT NULL DEFAULT 0,
            last_calculated_at  TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version             INTEGER NOT NULL DEFAULT 1,
            metadata            JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.organization_usage (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            period_start    DATE NOT NULL,
            period_end      DATE NOT NULL,
            searches_count  INTEGER NOT NULL DEFAULT 0,
            api_calls_count INTEGER NOT NULL DEFAULT 0,
            exports_count   INTEGER NOT NULL DEFAULT 0,
            credits_used    INTEGER NOT NULL DEFAULT 0,
            enrichments     INTEGER NOT NULL DEFAULT 0,
            ai_calls        INTEGER NOT NULL DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(organization_id, period_start)
        )
    """)
    op.execute("CREATE INDEX idx_org_usage_period ON auth.organization_usage(organization_id, period_start DESC)")

    # ── Roles & Permissions ─────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.roles (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID REFERENCES auth.organizations(id) ON DELETE CASCADE,  -- NULL = system role
            name            VARCHAR(100) NOT NULL,
            slug            VARCHAR(100) NOT NULL,
            description     TEXT,
            is_system       BOOLEAN NOT NULL DEFAULT FALSE,
            is_default      BOOLEAN NOT NULL DEFAULT FALSE,
            level           INTEGER NOT NULL DEFAULT 0,  -- higher = more privileged
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(organization_id, slug)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.permissions (
            id          UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            resource    VARCHAR(100) NOT NULL,  -- e.g. 'companies'
            action      VARCHAR(100) NOT NULL,  -- e.g. 'read', 'write', 'delete', 'export'
            scope       VARCHAR(50) NOT NULL DEFAULT 'org',  -- 'own', 'org', 'all'
            description TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version     INTEGER NOT NULL DEFAULT 1,
            metadata    JSONB NOT NULL DEFAULT '{}',
            UNIQUE(resource, action, scope)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.role_permissions (
            id            UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            role_id       UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
            permission_id UUID NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by    UUID,
            UNIQUE(role_id, permission_id)
        )
    """)
    op.execute("CREATE INDEX idx_role_permissions_role ON auth.role_permissions(role_id)")
    op.execute("CREATE INDEX idx_role_permissions_perm ON auth.role_permissions(permission_id)")

    # ── Teams & Departments ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.departments (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            name            VARCHAR(255) NOT NULL,
            description     TEXT,
            parent_id       UUID REFERENCES auth.departments(id),
            head_user_id    UUID,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            created_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_departments_org ON auth.departments(organization_id) WHERE deleted_at IS NULL")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.teams (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            department_id   UUID REFERENCES auth.departments(id),
            name            VARCHAR(255) NOT NULL,
            description     TEXT,
            is_default      BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            created_by      UUID,
            updated_by      UUID,
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_teams_org ON auth.teams(organization_id) WHERE deleted_at IS NULL")

    # ── Users ──────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.users (
            id                  UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id     UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            email               citext NOT NULL,
            email_verified      BOOLEAN NOT NULL DEFAULT FALSE,
            email_verified_at   TIMESTAMPTZ,
            password_hash       TEXT,
            first_name          VARCHAR(100),
            last_name           VARCHAR(100),
            display_name        VARCHAR(200),
            avatar_url          VARCHAR(1000),
            phone               VARCHAR(50),
            phone_verified      BOOLEAN NOT NULL DEFAULT FALSE,
            timezone            VARCHAR(100) NOT NULL DEFAULT 'UTC',
            locale              VARCHAR(20) NOT NULL DEFAULT 'en',
            department_id       UUID REFERENCES auth.departments(id),
            team_id             UUID REFERENCES auth.teams(id),
            job_title           VARCHAR(200),
            is_active           BOOLEAN NOT NULL DEFAULT TRUE,
            is_owner            BOOLEAN NOT NULL DEFAULT FALSE,
            last_login_at       TIMESTAMPTZ,
            last_active_at      TIMESTAMPTZ,
            login_count         INTEGER NOT NULL DEFAULT 0,
            failed_login_count  INTEGER NOT NULL DEFAULT 0,
            locked_until        TIMESTAMPTZ,
            deactivated_at      TIMESTAMPTZ,
            deactivated_by      UUID,
            invited_by          UUID REFERENCES auth.users(id),
            invited_at          TIMESTAMPTZ,
            invitation_accepted_at TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at          TIMESTAMPTZ,
            created_by          UUID,
            updated_by          UUID,
            version             INTEGER NOT NULL DEFAULT 1,
            status              VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata            JSONB NOT NULL DEFAULT '{}',
            UNIQUE(organization_id, email)
        )
    """)
    op.execute("CREATE INDEX idx_users_email ON auth.users(email) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_users_org ON auth.users(organization_id) WHERE deleted_at IS NULL")
    op.execute("CREATE INDEX idx_users_status ON auth.users(status, organization_id)")
    op.execute("CREATE INDEX idx_users_name_trgm ON auth.users USING GIN((first_name || ' ' || last_name) gin_trgm_ops) WHERE deleted_at IS NULL")

    # Add FK from organizations.owner_id
    op.execute("ALTER TABLE auth.organizations ADD CONSTRAINT fk_organizations_owner FOREIGN KEY (owner_id) REFERENCES auth.users(id)")
    op.execute("ALTER TABLE auth.organizations ADD CONSTRAINT fk_organizations_created_by FOREIGN KEY (created_by) REFERENCES auth.users(id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_profiles (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id         UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
            bio             TEXT,
            linkedin_url    VARCHAR(500),
            twitter_url     VARCHAR(500),
            website_url     VARCHAR(500),
            skills          TEXT[],
            languages       TEXT[],
            location        VARCHAR(255),
            date_of_birth   DATE,
            gender          VARCHAR(50),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_preferences (
            id                      UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id                 UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
            theme                   VARCHAR(20) NOT NULL DEFAULT 'light',
            notifications_email     BOOLEAN NOT NULL DEFAULT TRUE,
            notifications_browser   BOOLEAN NOT NULL DEFAULT TRUE,
            notifications_sms       BOOLEAN NOT NULL DEFAULT FALSE,
            default_page_size       INTEGER NOT NULL DEFAULT 25,
            date_format             VARCHAR(50) NOT NULL DEFAULT 'YYYY-MM-DD',
            time_format             VARCHAR(20) NOT NULL DEFAULT '24h',
            ai_suggestions          BOOLEAN NOT NULL DEFAULT TRUE,
            digest_frequency        VARCHAR(20) NOT NULL DEFAULT 'daily',
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version                 INTEGER NOT NULL DEFAULT 1,
            metadata                JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_sessions (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            token_hash      VARCHAR(255) NOT NULL UNIQUE,
            refresh_token_hash VARCHAR(255),
            ip_address      INET,
            user_agent      TEXT,
            device_id       UUID,
            location        VARCHAR(255),
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            expires_at      TIMESTAMPTZ NOT NULL,
            last_active_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            revoked_at      TIMESTAMPTZ,
            revoke_reason   VARCHAR(100),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_sessions_user ON auth.user_sessions(user_id) WHERE is_active = TRUE")
    op.execute("CREATE INDEX idx_sessions_token ON auth.user_sessions(token_hash)")
    op.execute("CREATE INDEX idx_sessions_expires ON auth.user_sessions(expires_at) WHERE is_active = TRUE")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_devices (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            device_name     VARCHAR(255),
            device_type     VARCHAR(50),
            os              VARCHAR(50),
            browser         VARCHAR(50),
            fingerprint     VARCHAR(255) UNIQUE,
            is_trusted      BOOLEAN NOT NULL DEFAULT FALSE,
            last_seen_at    TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_devices_user ON auth.user_devices(user_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_two_factor (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id         UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
            method          VARCHAR(50) NOT NULL DEFAULT 'totp',  -- totp, sms, email
            secret_encrypted TEXT,
            backup_codes    TEXT[],
            is_enabled      BOOLEAN NOT NULL DEFAULT FALSE,
            enabled_at      TIMESTAMPTZ,
            last_used_at    TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            version         INTEGER NOT NULL DEFAULT 1,
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_tokens (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            token_type      VARCHAR(50) NOT NULL,  -- email_verify, password_reset, invitation
            token_hash      VARCHAR(255) NOT NULL UNIQUE,
            expires_at      TIMESTAMPTZ NOT NULL,
            is_used         BOOLEAN NOT NULL DEFAULT FALSE,
            used_at         TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_user_tokens_hash ON auth.user_tokens(token_hash)")
    op.execute("CREATE INDEX idx_user_tokens_user ON auth.user_tokens(user_id, token_type)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_login_history (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            organization_id UUID NOT NULL,
            ip_address      INET,
            user_agent      TEXT,
            location        VARCHAR(255),
            country         VARCHAR(100),
            success         BOOLEAN NOT NULL DEFAULT TRUE,
            failure_reason  VARCHAR(255),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("CREATE TABLE auth.user_login_history_2026_06 PARTITION OF auth.user_login_history FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')")
    op.execute("CREATE TABLE auth.user_login_history_2026_07 PARTITION OF auth.user_login_history FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')")
    op.execute("CREATE TABLE auth.user_login_history_future PARTITION OF auth.user_login_history FOR VALUES FROM ('2026-08-01') TO ('2030-01-01')")
    op.execute("CREATE INDEX idx_login_history_user ON auth.user_login_history(user_id, created_at DESC)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_roles (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            role_id         UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            assigned_by     UUID REFERENCES auth.users(id),
            assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB NOT NULL DEFAULT '{}',
            UNIQUE(user_id, role_id, organization_id)
        )
    """)
    op.execute("CREATE INDEX idx_user_roles_user ON auth.user_roles(user_id)")
    op.execute("CREATE INDEX idx_user_roles_org ON auth.user_roles(organization_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.user_permissions (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            permission_id   UUID NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            granted         BOOLEAN NOT NULL DEFAULT TRUE,  -- FALSE = explicit deny
            granted_by      UUID REFERENCES auth.users(id),
            granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at      TIMESTAMPTZ,
            UNIQUE(user_id, permission_id, organization_id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.team_members (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            team_id         UUID NOT NULL REFERENCES auth.teams(id) ON DELETE CASCADE,
            user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            role            VARCHAR(50) NOT NULL DEFAULT 'member',
            joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(team_id, user_id)
        )
    """)
    op.execute("CREATE INDEX idx_team_members_team ON auth.team_members(team_id)")
    op.execute("CREATE INDEX idx_team_members_user ON auth.team_members(user_id)")

    # ── API Keys ─────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.api_keys (
            id              UUID NOT NULL DEFAULT uuid_generate_v7() PRIMARY KEY,
            organization_id UUID NOT NULL REFERENCES auth.organizations(id) ON DELETE CASCADE,
            user_id         UUID REFERENCES auth.users(id),
            name            VARCHAR(255) NOT NULL,
            key_prefix      VARCHAR(20) NOT NULL,   -- e.g. 'sk_live_abc123'
            key_hash        VARCHAR(255) NOT NULL UNIQUE,
            scopes          TEXT[] NOT NULL DEFAULT '{}',
            allowed_ips     INET[],
            rate_limit_rpm  INTEGER NOT NULL DEFAULT 100,
            last_used_at    TIMESTAMPTZ,
            use_count       BIGINT NOT NULL DEFAULT 0,
            expires_at      TIMESTAMPTZ,
            revoked_at      TIMESTAMPTZ,
            revoked_by      UUID,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            created_by      UUID REFERENCES auth.users(id),
            version         INTEGER NOT NULL DEFAULT 1,
            status          VARCHAR(50) NOT NULL DEFAULT 'active',
            metadata        JSONB NOT NULL DEFAULT '{}'
        )
    """)
    op.execute("CREATE INDEX idx_api_keys_hash ON auth.api_keys(key_hash)")
    op.execute("CREATE INDEX idx_api_keys_org ON auth.api_keys(organization_id) WHERE deleted_at IS NULL")

    # ── Updated_at triggers ───────────────────────────────────────────────
    tables = [
        "auth.organizations", "auth.users", "auth.roles", "auth.teams",
        "auth.departments", "auth.api_keys", "auth.user_sessions"
    ]
    for tbl in tables:
        schema, name = tbl.split(".")
        op.execute(f"""
            CREATE OR REPLACE TRIGGER trg_{name}_updated_at
            BEFORE UPDATE ON {tbl}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """)

    # ── RLS ─────────────────────────────────────────────────────────
    for tbl in ["auth.users", "auth.teams", "auth.departments", "auth.api_keys"]:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")
        schema, name = tbl.split(".")
        op.execute(f"""
            CREATE POLICY {name}_org_isolation ON {tbl}
            USING (organization_id = current_org_id())
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS auth.api_keys CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.team_members CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_roles CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_login_history CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_tokens CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_two_factor CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_devices CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_preferences CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.user_profiles CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.users CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.role_permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.permissions CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.roles CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.teams CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.departments CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organization_usage CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organization_storage CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organization_integrations CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organization_features CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organization_security CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organization_branding CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organization_domains CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organization_settings CASCADE")
    op.execute("DROP TABLE IF EXISTS auth.organizations CASCADE")
    op.execute("DROP TABLE IF EXISTS billing.subscription_plans CASCADE")

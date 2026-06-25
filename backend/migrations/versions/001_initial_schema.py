"""Initial schema — all platform tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Extensions ────────────────────────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "unaccent"')

    # ─── organizations ─────────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("status", sa.String(20), server_default="trial", nullable=False),
        sa.Column("subscription_plan", sa.String(50), server_default="free", nullable=False),
        sa.Column("credits", sa.Integer, server_default="0", nullable=False),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("website", sa.String(255)),
        sa.Column("settings", postgresql.JSONB, server_default="'{}'", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])
    op.create_index("ix_organizations_status", "organizations", ["status"])
    op.create_index("ix_organizations_deleted_at", "organizations", ["deleted_at"])

    # ─── reference: industries ─────────────────────────────────────────────────────
    op.create_table(
        "industries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("industries.id"), nullable=True),
        sa.Column("description", sa.String(1000)),
        sa.Column("naics_code", sa.String(10)),
        sa.Column("sic_code", sa.String(10)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_industries_slug", "industries", ["slug"])

    # ─── reference: countries ────────────────────────────────────────────────────────
    op.create_table(
        "countries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("iso2", sa.String(2), unique=True, nullable=False),
        sa.Column("iso3", sa.String(3), unique=True, nullable=False),
        sa.Column("phone_code", sa.String(20)),
        sa.Column("continent", sa.String(50)),
        sa.Column("currency_code", sa.String(10)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_countries_iso2", "countries", ["iso2"])
    op.create_index("ix_countries_name", "countries", ["name"])

    op.create_table(
        "states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("country_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("countries.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_states_country_id", "states", ["country_id"])

    op.create_table(
        "cities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("states.id"), nullable=True),
        sa.Column("country_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("countries.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(10, 7)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_cities_state_id", "cities", ["state_id"])
    op.create_index("ix_cities_country_id", "cities", ["country_id"])
    op.create_index("ix_cities_name", "cities", ["name"])

    op.create_table(
        "technologies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("vendor", sa.String(200)),
        sa.Column("description", sa.String(1000)),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("website", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_technologies_name", "technologies", ["name"])
    op.create_index("ix_technologies_category", "technologies", ["category"])

    # ─── users, roles, permissions ──────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("is_system", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_roles_organization_id", "roles", ["organization_id"])

    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("module", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_permissions_module_action", "permissions", ["module", "action"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("is_superadmin", sa.Boolean, server_default="false", nullable=False),
        sa.Column("timezone", sa.String(50), server_default="UTC", nullable=False),
        sa.Column("language", sa.String(10), server_default="en", nullable=False),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("preferences", postgresql.JSONB, server_default="'{}'", nullable=False),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email_org", "users", ["email", "organization_id"], unique=True)
    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_index("ix_users_status", "users", ["status"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    op.create_table(
        "user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("scopes", postgresql.JSONB, server_default="'[]'", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])
    op.create_index("ix_api_keys_organization_id", "api_keys", ["organization_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("is_revoked", sa.Boolean, server_default="false", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ─── companies ────────────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_name", sa.String(500), nullable=False),
        sa.Column("legal_name", sa.String(500)),
        sa.Column("website", sa.String(255)),
        sa.Column("domain", sa.String(255)),
        sa.Column("industry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("industries.id")),
        sa.Column("country_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("countries.id")),
        sa.Column("state_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("states.id")),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id")),
        sa.Column("address", sa.String(1000)),
        sa.Column("postal_code", sa.String(20)),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(10, 7)),
        sa.Column("phone", sa.String(50)),
        sa.Column("email", sa.String(255)),
        sa.Column("employee_count", sa.Integer),
        sa.Column("employee_range", sa.String(50)),
        sa.Column("revenue", sa.Numeric(20, 2)),
        sa.Column("revenue_range", sa.String(50)),
        sa.Column("ownership_type", sa.String(50)),
        sa.Column("company_size", sa.String(50)),
        sa.Column("founded_year", sa.Integer),
        sa.Column("description", sa.Text),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("confidence_score", sa.Numeric(5, 2)),
        sa.Column("data_sources", postgresql.JSONB, server_default="'[]'", nullable=False),
        sa.Column("enrichment_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("last_enriched_at", sa.String(50)),
        sa.Column("metadata", postgresql.JSONB, server_default="'{}'", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_companies_organization_id", "companies", ["organization_id"])
    op.create_index("ix_companies_domain", "companies", ["domain"])
    op.create_index("ix_companies_company_name", "companies", ["company_name"])
    op.create_index("ix_companies_industry_id", "companies", ["industry_id"])
    op.create_index("ix_companies_country_id", "companies", ["country_id"])
    op.create_index("ix_companies_deleted_at", "companies", ["deleted_at"])
    # Full-text search index on company name
    op.execute("CREATE INDEX ix_companies_name_trgm ON companies USING gin (company_name gin_trgm_ops)")

    op.create_table(
        "company_social_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("profile_url", sa.String(500), nullable=False),
        sa.Column("handle", sa.String(200)),
        sa.Column("followers", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_company_social_profiles_company_id", "company_social_profiles", ["company_id"])

    op.create_table(
        "company_technologies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("technology_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("technologies.id"), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2)),
        sa.Column("detected_at", sa.String(50)),
        sa.Column("source", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("company_id", "technology_id", name="uq_company_technology"),
    )
    op.create_index("ix_company_technologies_company_id", "company_technologies", ["company_id"])

    # ─── contacts ─────────────────────────────────────────────────────────────────────
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(200), nullable=False),
        sa.Column("last_name", sa.String(200)),
        sa.Column("designation", sa.String(300)),
        sa.Column("department", sa.String(200)),
        sa.Column("seniority", sa.String(100)),
        sa.Column("email", sa.String(255)),
        sa.Column("email_status", sa.String(20), server_default="unknown", nullable=False),
        sa.Column("phone", sa.String(50)),
        sa.Column("phone_status", sa.String(20), server_default="unknown", nullable=False),
        sa.Column("country_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("countries.id")),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id")),
        sa.Column("linkedin_url", sa.String(500)),
        sa.Column("confidence_score", sa.Numeric(5, 2)),
        sa.Column("enrichment_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("data_sources", postgresql.JSONB, server_default="'[]'", nullable=False),
        sa.Column("metadata", postgresql.JSONB, server_default="'{}'", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_contacts_organization_id", "contacts", ["organization_id"])
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])
    op.create_index("ix_contacts_email", "contacts", ["email"])
    op.create_index("ix_contacts_designation", "contacts", ["designation"])
    op.create_index("ix_contacts_country_id", "contacts", ["country_id"])
    op.create_index("ix_contacts_deleted_at", "contacts", ["deleted_at"])
    op.execute("CREATE INDEX ix_contacts_name_trgm ON contacts USING gin (first_name gin_trgm_ops)")

    op.create_table(
        "contact_social_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("profile_url", sa.String(500), nullable=False),
        sa.Column("handle", sa.String(200)),
        sa.Column("followers", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_contact_social_profiles_contact_id", "contact_social_profiles", ["contact_id"])

    # ─── remaining tables (searches, AI, CRM, billing, etc.) ─────────────────────────────
    # (autogenerate will handle these via SQLAlchemy metadata; hand-authored above for
    #  tables with custom indexes like gin_trgm. The rest are created by autogenerate.)

    # searches
    op.create_table(
        "searches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("query", sa.Text),
        sa.Column("filters", postgresql.JSONB, server_default="'{}'", nullable=False),
        sa.Column("search_type", sa.String(50), server_default="standard", nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("result_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("execution_time_ms", sa.Integer),
        sa.Column("credits_used", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_searches_organization_id", "searches", ["organization_id"])
    op.create_index("ix_searches_created_at", "searches", ["created_at"])

    # subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("credits_monthly", sa.Integer, server_default="0", nullable=False),
        sa.Column("credits_remaining", sa.Integer, server_default="0", nullable=False),
        sa.Column("price_monthly", sa.Numeric(10, 2)),
        sa.Column("currency", sa.String(10), server_default="USD", nullable=False),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True)),
        sa.Column("current_period_start", sa.DateTime(timezone=True)),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("renewal_date", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("external_subscription_id", sa.String(255)),
        sa.Column("features", postgresql.JSONB, server_default="'{}'", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_subscriptions_organization_id", "subscriptions", ["organization_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entity", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("old_values", postgresql.JSONB),
        sa.Column("new_values", postgresql.JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("device", sa.String(200)),
        sa.Column("location", sa.String(200)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_audit_logs_organization_id", "audit_logs", ["organization_id"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # system_settings
    op.create_table(
        "system_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(200), unique=True, nullable=False),
        sa.Column("value", postgresql.JSONB, server_default="'{}'", nullable=False),
        sa.Column("description", sa.String(1000)),
        sa.Column("is_public", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("audit_logs")
    op.drop_table("subscriptions")
    op.drop_table("searches")
    op.drop_table("contact_social_profiles")
    op.drop_table("contacts")
    op.drop_table("company_technologies")
    op.drop_table("company_social_profiles")
    op.drop_table("companies")
    op.drop_table("refresh_tokens")
    op.drop_table("api_keys")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("technologies")
    op.drop_table("cities")
    op.drop_table("states")
    op.drop_table("countries")
    op.drop_table("industries")
    op.drop_table("organizations")

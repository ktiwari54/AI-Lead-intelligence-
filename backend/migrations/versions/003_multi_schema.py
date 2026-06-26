"""multi_schema: move tables into bounded-context schemas

Revision ID: 003
Revises: 002
Create Date: 2025-01-01
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

SCHEMAS = [
    "auth", "core", "crm", "search", "ai", "analytics",
    "connector", "audit", "billing", "notification", "system",
    "enrichment", "export",
]

# (table_name, target_schema)
TABLE_SCHEMA_MAP = [
    # auth
    ("users", "auth"),
    ("roles", "auth"),
    ("permissions", "auth"),
    ("role_permissions", "auth"),
    ("user_roles", "auth"),
    ("api_keys", "auth"),
    ("refresh_tokens", "auth"),
    # core
    ("organizations", "core"),
    ("industries", "core"),
    ("countries", "core"),
    ("states", "core"),
    ("cities", "core"),
    ("technologies", "core"),
    ("companies", "core"),
    ("company_social_profiles", "core"),
    ("company_technologies", "core"),
    ("contacts", "core"),
    ("contact_social_profiles", "core"),
    # crm
    ("crm_pipelines", "crm"),
    ("crm_pipeline_stages", "crm"),
    ("crm_deals", "crm"),
    ("crm_tasks", "crm"),
    ("tags", "crm"),
    ("contact_tags", "crm"),
    ("company_tags", "crm"),
    ("activities", "crm"),
    ("notes", "crm"),
    ("lead_lists", "crm"),
    ("lead_list_contacts", "crm"),
    # search
    ("searches", "search"),
    ("search_results", "search"),
    ("saved_searches", "search"),
    # ai
    ("lead_scores", "ai"),
    # connector
    ("connector_configs", "connector"),
    ("connector_jobs", "connector"),
    # audit
    ("audit_logs", "audit"),
    ("workflows", "audit"),
    ("workflow_executions", "audit"),
    # billing
    ("subscriptions", "billing"),
    ("credit_transactions", "billing"),
    # notification
    ("notifications", "notification"),
    # system
    ("system_settings", "system"),
    ("feature_flags", "system"),
    # enrichment
    ("email_verifications", "enrichment"),
    # export
    ("exports", "export"),
    ("import_jobs", "export"),
]


def upgrade() -> None:
    # 1. Create all schemas
    for schema in SCHEMAS:
        op.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    
    # 2. Grant usage to the application role (adjust role name as needed)
    for schema in SCHEMAS:
        op.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO PUBLIC')
        op.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA "{schema}" GRANT ALL ON TABLES TO PUBLIC')
    
    # 3. Move tables. PostgreSQL ALTER TABLE SET SCHEMA moves the table and
    #    automatically updates sequences owned by the table. Cross-schema
    #    FK references are preserved by PostgreSQL automatically.
    for table_name, target_schema in TABLE_SCHEMA_MAP:
        op.execute(f'ALTER TABLE IF EXISTS public."{table_name}" SET SCHEMA "{target_schema}"')
    
    # 4. Update search_path comment in alembic_version so future migrations
    #    can find tables. In env.py, set include_schemas=True.
    op.execute("""
        COMMENT ON DATABASE CURRENT_CATALOG IS 
        'AI Lead Intelligence Platform - multi-schema architecture'
    """)


def downgrade() -> None:
    # Move all tables back to public
    for table_name, source_schema in reversed(TABLE_SCHEMA_MAP):
        op.execute(f'ALTER TABLE IF EXISTS "{source_schema}"."{table_name}" SET SCHEMA public')
    
    # Drop schemas (only if empty)
    for schema in reversed(SCHEMAS):
        op.execute(f'DROP SCHEMA IF EXISTS "{schema}"')

"""
PostgreSQL schema constants for multi-schema organization.

Each bounded context lives in its own schema instead of the public schema.
This improves separation of concerns, allows per-schema permissions (GRANT USAGE ON SCHEMA),
and makes pg_dump/restore per-domain trivial.
"""
from __future__ import annotations


class DBSchema:
    AUTH = "auth"           # users, roles, permissions, api_keys, refresh_tokens
    CORE = "core"           # organizations, industries, countries, states, cities, technologies
    CRM = "crm"             # pipelines, stages, deals, tasks, tags, activities, notes, lead_lists
    SEARCH = "search"       # searches, search_results, saved_searches
    AI = "ai"               # lead_scores
    ANALYTICS = "analytics" # (reserved for future materialized views and analytics tables)
    CONNECTOR = "connector" # connector_configs, connector_jobs
    AUDIT = "audit"         # audit_logs, workflow_executions, workflows
    BILLING = "billing"     # subscriptions, credit_transactions
    NOTIFICATION = "notification"  # notifications
    SYSTEM = "system"       # system_settings, feature_flags
    ENRICHMENT = "enrichment"      # email_verifications
    EXPORT = "export"       # exports, import_jobs


ALL_SCHEMAS = [
    DBSchema.AUTH,
    DBSchema.CORE,
    DBSchema.CRM,
    DBSchema.SEARCH,
    DBSchema.AI,
    DBSchema.ANALYTICS,
    DBSchema.CONNECTOR,
    DBSchema.AUDIT,
    DBSchema.BILLING,
    DBSchema.NOTIFICATION,
    DBSchema.SYSTEM,
    DBSchema.ENRICHMENT,
    DBSchema.EXPORT,
]


def schema_table(schema: str, table: str) -> str:
    """Return fully-qualified table reference: 'schema.table'"""
    return f"{schema}.{table}"

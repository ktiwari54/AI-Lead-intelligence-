"""event_store: immutable append-only event log with monthly partitioning

Revision ID: 006
Revises: 005
Create Date: 2025-01-01

The event_store is the centerpiece of event sourcing:
- Append-only (no updates or deletes)
- Partitioned by month (RANGE on occurred_at) for query performance
- UUID v7 primary keys for time-ordered inserts
- BRIN index on occurred_at (works well on append-only data)
- GIN index on data JSONB for payload queries
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Parent partitioned table
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store (
            id              uuid            NOT NULL DEFAULT uuid_generate_v7(),
            event_type      varchar(255)    NOT NULL,
            aggregate_type  varchar(100)    NOT NULL,
            aggregate_id    varchar(255)    NOT NULL,
            sequence_number integer         NOT NULL DEFAULT 1,
            data            jsonb           NOT NULL DEFAULT '{}',
            actor_id        uuid,
            organization_id uuid,
            correlation_id  uuid,
            causation_id    uuid,
            metadata        jsonb           NOT NULL DEFAULT '{}',
            occurred_at     timestamptz     NOT NULL DEFAULT now(),
            PRIMARY KEY (id, occurred_at)
        ) PARTITION BY RANGE (occurred_at)
    """)

    # Create initial partitions: last month, current month, next month
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_01
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-01-01') TO ('2025-02-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_02
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-02-01') TO ('2025-03-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_03
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-03-01') TO ('2025-04-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_04
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-04-01') TO ('2025-05-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_05
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-05-01') TO ('2025-06-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_06
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-06-01') TO ('2025-07-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_07
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-07-01') TO ('2025-08-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_08
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-08-01') TO ('2025-09-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_09
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-09-01') TO ('2025-10-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_10
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-10-01') TO ('2025-11-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_11
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-11-01') TO ('2025-12-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2025_12
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2025-12-01') TO ('2026-01-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2026_01
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2026-01-01') TO ('2026-02-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2026_06
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_2026_07
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.event_store_future
        PARTITION OF audit.event_store
        FOR VALUES FROM ('2026-08-01') TO ('2030-01-01')
    """)

    # Indexes on parent table (propagate to all partitions)
    # BRIN is ideal for append-only time-series data
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_store_occurred_at_brin
        ON audit.event_store
        USING brin(occurred_at)
        WITH (pages_per_range = 128)
    """)

    # B-tree index for aggregate replay queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_store_aggregate
        ON audit.event_store(aggregate_type, aggregate_id, sequence_number)
    """)

    # Index for org-scoped event queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_store_org
        ON audit.event_store(organization_id, occurred_at DESC)
        WHERE organization_id IS NOT NULL
    """)

    # Index for event type filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_store_event_type
        ON audit.event_store(event_type, occurred_at DESC)
    """)

    # GIN index for JSONB payload queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_store_data_gin
        ON audit.event_store
        USING gin(data)
    """)

    # Correlation/causation indexes for event chain tracing
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_event_store_correlation
        ON audit.event_store(correlation_id)
        WHERE correlation_id IS NOT NULL
    """)

    # Row-level security: organizations can only see their own events
    op.execute("ALTER TABLE audit.event_store ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY event_store_org_isolation ON audit.event_store
        USING (organization_id IS NULL OR organization_id::text = current_setting('app.current_org_id', true))
    """)

    # Function to auto-create next month's partition
    op.execute("""
        CREATE OR REPLACE FUNCTION audit.create_event_store_partition_if_needed()
        RETURNS void
        LANGUAGE plpgsql
        AS $$
        DECLARE
            next_month date := date_trunc('month', now() + interval '1 month');
            partition_name text;
            start_date text;
            end_date text;
        BEGIN
            partition_name := 'event_store_' || to_char(next_month, 'YYYY_MM');
            start_date := to_char(next_month, 'YYYY-MM-DD');
            end_date := to_char(next_month + interval '1 month', 'YYYY-MM-DD');
            
            IF NOT EXISTS (
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'audit' AND c.relname = partition_name
            ) THEN
                EXECUTE format(
                    'CREATE TABLE IF NOT EXISTS audit.%I PARTITION OF audit.event_store FOR VALUES FROM (%L) TO (%L)',
                    partition_name, start_date, end_date
                );
                RAISE NOTICE 'Created partition: audit.%', partition_name;
            END IF;
        END;
        $$;
    """)

    # Prevent any UPDATE or DELETE on event_store (immutability enforcement)
    op.execute("""
        CREATE OR REPLACE RULE event_store_no_update AS
        ON UPDATE TO audit.event_store DO INSTEAD NOTHING;
    """)
    op.execute("""
        CREATE OR REPLACE RULE event_store_no_delete AS
        ON DELETE TO audit.event_store DO INSTEAD NOTHING;
    """)


def downgrade() -> None:
    op.execute("DROP RULE IF EXISTS event_store_no_delete ON audit.event_store")
    op.execute("DROP RULE IF EXISTS event_store_no_update ON audit.event_store")
    op.execute("DROP FUNCTION IF EXISTS audit.create_event_store_partition_if_needed()")
    op.execute("DROP TABLE IF EXISTS audit.event_store CASCADE")

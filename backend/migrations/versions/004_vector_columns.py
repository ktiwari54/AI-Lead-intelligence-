"""vector_columns: add embedding columns for pgvector semantic search

Revision ID: 004
Revises: 003
Create Date: 2025-01-01
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None

EMBEDDING_DIMS = 1536  # text-embedding-3-small


def upgrade() -> None:
    # Ensure vector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column to companies
    op.execute(f"""
        ALTER TABLE core.companies 
        ADD COLUMN IF NOT EXISTS embedding vector({EMBEDDING_DIMS})
    """)
    
    # Add embedding column to contacts
    op.execute(f"""
        ALTER TABLE core.contacts 
        ADD COLUMN IF NOT EXISTS embedding vector({EMBEDDING_DIMS})
    """)

    # Create HNSW indexes for approximate nearest-neighbor search
    # HNSW is faster than IVFFlat for most workloads and doesn't require training
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_companies_embedding_hnsw
        ON core.companies
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL AND deleted_at IS NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_contacts_embedding_hnsw
        ON core.contacts
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        WHERE embedding IS NOT NULL AND deleted_at IS NULL
    """)

    # Add embedding to ai.lead_scores for score explanation similarity
    op.execute(f"""
        ALTER TABLE ai.lead_scores
        ADD COLUMN IF NOT EXISTS query_embedding vector({EMBEDDING_DIMS})
    """)

    # Add notes embedding table (separate table to avoid bloating core tables)
    op.execute(f"""
        CREATE TABLE IF NOT EXISTS ai.note_embeddings (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v7(),
            note_id uuid NOT NULL,
            organization_id uuid NOT NULL,
            content_hash varchar(64) NOT NULL,
            embedding vector({EMBEDDING_DIMS}) NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (note_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_note_embeddings_hnsw
        ON ai.note_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Search query embeddings for query suggestion / related searches
    op.execute(f"""
        ALTER TABLE search.searches
        ADD COLUMN IF NOT EXISTS query_embedding vector({EMBEDDING_DIMS})
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_companies_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_contacts_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_note_embeddings_hnsw")
    op.execute("DROP TABLE IF EXISTS ai.note_embeddings")
    op.execute("ALTER TABLE core.companies DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE core.contacts DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE ai.lead_scores DROP COLUMN IF EXISTS query_embedding")
    op.execute("ALTER TABLE search.searches DROP COLUMN IF EXISTS query_embedding")

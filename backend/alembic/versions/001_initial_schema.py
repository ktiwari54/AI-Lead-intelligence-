"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "unaccent";')
    # Tables are created via SQLAlchemy models / create_all in development.
    # For production use the DDL in migrations/ddl/001_create_tables.sql.
    # This migration serves as a marker for the baseline schema version.


def downgrade() -> None:
    pass

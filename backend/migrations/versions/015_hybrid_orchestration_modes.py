"""Hybrid orchestration modes — event-driven, scheduled, human-in-the-loop

Revision ID: 015
Revises: 014
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflows",
        sa.Column("orchestration_mode", sa.String(30), server_default="event_driven", nullable=False),
    )
    op.create_index("ix_workflows_orchestration_mode", "workflows", ["orchestration_mode"])

    op.add_column(
        "workflow_templates",
        sa.Column("orchestration_mode", sa.String(30), server_default="event_driven", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("workflow_templates", "orchestration_mode")
    op.drop_index("ix_workflows_orchestration_mode", table_name="workflows")
    op.drop_column("workflows", "orchestration_mode")
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.common.base import BaseModel


class DiscoveryJob(BaseModel):
    __tablename__ = "discovery_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False)
    query: Mapped[str | None] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(String(20), server_default="both", nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    connectors_used: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    stages: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    result_count: Mapped[int | None] = mapped_column(Integer)
    credits_used: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    took_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_discovery_jobs_organization_id", "organization_id"),
        Index("ix_discovery_jobs_status", "status"),
        Index("ix_discovery_jobs_created_at", "created_at"),
    )

    hits: Mapped[list["DiscoveryJobHit"]] = relationship(
        "DiscoveryJobHit", back_populates="job", cascade="all, delete-orphan"
    )


class DiscoveryJobHit(BaseModel):
    __tablename__ = "discovery_job_hits"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discovery_jobs.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    source_trust: Mapped[float] = mapped_column(Numeric(5, 4), server_default="0.85", nullable=False)
    field_completeness: Mapped[float] = mapped_column(Numeric(5, 4), server_default="0.5", nullable=False)
    verification_status: Mapped[str | None] = mapped_column(String(50))
    data: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    provenance: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    explanation: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (
        Index("ix_discovery_job_hits_job_id", "job_id"),
        Index("ix_discovery_job_hits_confidence", "confidence"),
    )

    job: Mapped["DiscoveryJob"] = relationship("DiscoveryJob", back_populates="hits")
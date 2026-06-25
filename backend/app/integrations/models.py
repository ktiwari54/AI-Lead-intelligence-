import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Index, Integer, DateTime, Boolean, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class ConnectorConfig(BaseModel):
    __tablename__ = "connector_configs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    connector_type: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    credentials: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    settings: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    health_status: Mapped[str] = mapped_column(String(20), server_default="unknown", nullable=False)
    rate_limit_remaining: Mapped[int | None] = mapped_column(Integer)
    rate_limit_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_connector_configs_organization_id", "organization_id"),
        Index("ix_connector_configs_connector_type", "connector_type"),
        Index("uq_connector_config_org_type", "organization_id", "connector_type", unique=True),
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="connector_configs"
    )
    jobs: Mapped[list["ConnectorJob"]] = relationship(
        "ConnectorJob", back_populates="connector_config"
    )


class ConnectorJob(BaseModel):
    __tablename__ = "connector_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    connector_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connector_configs.id", ondelete="SET NULL"), nullable=True
    )
    connector_type: Mapped[str] = mapped_column(String(100), nullable=False)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, server_default="3", nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    job_metadata: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    result: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (
        Index("ix_connector_jobs_organization_id", "organization_id"),
        Index("ix_connector_jobs_status", "status"),
        Index("ix_connector_jobs_connector_type", "connector_type"),
        Index("ix_connector_jobs_created_at", "created_at"),
    )

    connector_config: Mapped["ConnectorConfig | None"] = relationship(
        "ConnectorConfig", back_populates="jobs"
    )

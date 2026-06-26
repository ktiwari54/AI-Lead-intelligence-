import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Index, Integer, DateTime, BigInteger, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class Export(BaseModel):
    __tablename__ = "exports"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000))
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    record_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(2000))
    credits_used: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    __table_args__ = (
        Index("ix_exports_organization_id", "organization_id"),
        Index("ix_exports_status", "status"),
        Index("ix_exports_created_at", "created_at"),
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="exports")


class ImportJob(BaseModel):
    __tablename__ = "import_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    import_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000))
    total_records: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    success_records: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    mapping: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    errors: Mapped[list] = mapped_column(JSONB, server_default="[]", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(2000))

    __table_args__ = (
        Index("ix_import_jobs_organization_id", "organization_id"),
        Index("ix_import_jobs_status", "status"),
    )

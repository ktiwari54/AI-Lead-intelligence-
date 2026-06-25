import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Index, Numeric, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class EmailVerification(BaseModel):
    __tablename__ = "email_verifications"

    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    sub_status: Mapped[str | None] = mapped_column(String(50))
    provider: Mapped[str | None] = mapped_column(String(100))
    is_deliverable: Mapped[bool | None] = mapped_column()
    is_role_address: Mapped[bool | None] = mapped_column()
    is_disposable: Mapped[bool | None] = mapped_column()
    is_catch_all: Mapped[bool | None] = mapped_column()
    smtp_provider: Mapped[str | None] = mapped_column(String(200))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_response: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_email_verifications_email", "email"),
        Index("ix_email_verifications_contact_id", "contact_id"),
        Index("ix_email_verifications_organization_id", "organization_id"),
        Index("ix_email_verifications_status", "status"),
    )

    contact: Mapped["Contact | None"] = relationship(
        "Contact", back_populates="email_verifications"
    )

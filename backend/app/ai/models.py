import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Index, Numeric, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class LeadScore(BaseModel):
    __tablename__ = "lead_scores"

    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    overall_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    industry_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    company_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    engagement_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    technology_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    seniority_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    fit_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_breakdown: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    model_version: Mapped[str | None] = mapped_column(String(50))
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_lead_scores_contact_id", "contact_id"),
        Index("ix_lead_scores_company_id", "company_id"),
        Index("ix_lead_scores_organization_id", "organization_id"),
        Index("ix_lead_scores_overall_score", "overall_score"),
    )

    contact: Mapped["Contact | None"] = relationship("Contact", back_populates="lead_scores")
    company: Mapped["Company | None"] = relationship("Company", back_populates="lead_scores")

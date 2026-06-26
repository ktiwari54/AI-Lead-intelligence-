import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Index, Numeric, Text, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class Search(BaseModel):
    __tablename__ = "searches"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    query: Mapped[str | None] = mapped_column(Text)
    filters: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    search_type: Mapped[str] = mapped_column(String(50), server_default="standard", nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False)
    result_count: Mapped[int] = mapped_column(server_default="0", nullable=False)
    execution_time_ms: Mapped[int | None] = mapped_column()
    credits_used: Mapped[int] = mapped_column(server_default="0", nullable=False)

    __table_args__ = (
        Index("ix_searches_organization_id", "organization_id"),
        Index("ix_searches_created_by", "created_by"),
        Index("ix_searches_status", "status"),
        Index("ix_searches_created_at", "created_at"),
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="searches")
    results: Mapped[list["SearchResult"]] = relationship(
        "SearchResult", back_populates="search", cascade="all, delete-orphan"
    )


class SearchResult(BaseModel):
    __tablename__ = "search_results"

    search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("searches.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    rank: Mapped[int | None] = mapped_column()
    source: Mapped[str | None] = mapped_column(String(100))
    result_metadata: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_search_results_search_id", "search_id"),
        Index("ix_search_results_company_id", "company_id"),
        Index("ix_search_results_contact_id", "contact_id"),
    )

    search: Mapped["Search"] = relationship("Search", back_populates="results")


class SavedSearch(BaseModel):
    __tablename__ = "saved_searches"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    query: Mapped[str | None] = mapped_column(Text)
    filters: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    search_type: Mapped[str] = mapped_column(String(50), server_default="standard", nullable=False)
    is_shared: Mapped[bool] = mapped_column(server_default="false", nullable=False)
    run_count: Mapped[int] = mapped_column(server_default="0", nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_saved_searches_organization_id", "organization_id"),
        Index("ix_saved_searches_created_by", "created_by"),
    )

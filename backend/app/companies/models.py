import uuid
from sqlalchemy import String, Integer, ForeignKey, Index, Numeric, Text, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class Company(BaseModel):
    __tablename__ = "companies"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(500), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(255))
    domain: Mapped[str | None] = mapped_column(String(255))
    industry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("industries.id"), nullable=True
    )
    country_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True
    )
    state_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("states.id"), nullable=True
    )
    city_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cities.id"), nullable=True
    )
    address: Mapped[str | None] = mapped_column(String(1000))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    employee_count: Mapped[int | None] = mapped_column(Integer)
    employee_range: Mapped[str | None] = mapped_column(String(50))
    revenue: Mapped[float | None] = mapped_column(Numeric(20, 2))
    revenue_range: Mapped[str | None] = mapped_column(String(50))
    ownership_type: Mapped[str | None] = mapped_column(String(50))
    company_size: Mapped[str | None] = mapped_column(String(50))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    data_sources: Mapped[list] = mapped_column(JSONB, server_default="[]", nullable=False)
    enrichment_status: Mapped[str] = mapped_column(
        String(20), server_default="pending", nullable=False
    )
    last_enriched_at: Mapped[str | None] = mapped_column(String(50))
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_companies_organization_id", "organization_id"),
        Index("ix_companies_domain", "domain"),
        Index("ix_companies_company_name", "company_name"),
        Index("ix_companies_industry_id", "industry_id"),
        Index("ix_companies_country_id", "country_id"),
        Index("ix_companies_city_id", "city_id"),
        Index("ix_companies_org_domain", "organization_id", "domain"),
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="companies"
    )
    industry: Mapped["Industry | None"] = relationship("Industry", back_populates="companies")
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="company")
    social_profiles: Mapped[list["CompanySocialProfile"]] = relationship(
        "CompanySocialProfile", back_populates="company", cascade="all, delete-orphan"
    )
    technologies: Mapped[list["CompanyTechnology"]] = relationship(
        "CompanyTechnology", back_populates="company", cascade="all, delete-orphan"
    )
    tags: Mapped[list["CompanyTag"]] = relationship(
        "CompanyTag", back_populates="company", cascade="all, delete-orphan"
    )
    lead_scores: Mapped[list["LeadScore"]] = relationship("LeadScore", back_populates="company")


class CompanySocialProfile(BaseModel):
    __tablename__ = "company_social_profiles"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_url: Mapped[str] = mapped_column(String(500), nullable=False)
    handle: Mapped[str | None] = mapped_column(String(200))
    followers: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_company_social_profiles_company_id", "company_id"),
        Index("ix_company_social_profiles_platform", "platform"),
    )

    company: Mapped["Company"] = relationship("Company", back_populates="social_profiles")


class CompanyTechnology(BaseModel):
    __tablename__ = "company_technologies"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    technology_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("technologies.id"), nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
    detected_at: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        Index("ix_company_technologies_company_id", "company_id"),
        Index("ix_company_technologies_technology_id", "technology_id"),
        Index("uq_company_technology", "company_id", "technology_id", unique=True),
    )

    company: Mapped["Company"] = relationship("Company", back_populates="technologies")
    technology: Mapped["Technology"] = relationship(
        "Technology", back_populates="company_technologies"
    )

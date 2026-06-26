import uuid
from sqlalchemy import String, ForeignKey, Index, Numeric, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class Contact(BaseModel):
    __tablename__ = "contacts"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(200), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(200))
    designation: Mapped[str | None] = mapped_column(String(300))
    department: Mapped[str | None] = mapped_column(String(200))
    seniority: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    email_status: Mapped[str] = mapped_column(String(20), server_default="unknown", nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    phone_status: Mapped[str] = mapped_column(String(20), server_default="unknown", nullable=False)
    country_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True
    )
    city_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cities.id"), nullable=True
    )
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    enrichment_status: Mapped[str] = mapped_column(
        String(20), server_default="pending", nullable=False
    )
    data_sources: Mapped[list] = mapped_column(JSONB, server_default="[]", nullable=False)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_contacts_organization_id", "organization_id"),
        Index("ix_contacts_company_id", "company_id"),
        Index("ix_contacts_email", "email"),
        Index("ix_contacts_designation", "designation"),
        Index("ix_contacts_country_id", "country_id"),
        Index("ix_contacts_org_email", "organization_id", "email"),
    )

    company: Mapped["Company | None"] = relationship("Company", back_populates="contacts")
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="contacts"
    )
    social_profiles: Mapped[list["ContactSocialProfile"]] = relationship(
        "ContactSocialProfile", back_populates="contact", cascade="all, delete-orphan"
    )
    tags: Mapped[list["ContactTag"]] = relationship(
        "ContactTag", back_populates="contact", cascade="all, delete-orphan"
    )
    email_verifications: Mapped[list["EmailVerification"]] = relationship(
        "EmailVerification", back_populates="contact"
    )
    lead_scores: Mapped[list["LeadScore"]] = relationship("LeadScore", back_populates="contact")
    activities: Mapped[list["Activity"]] = relationship("Activity", back_populates="contact")
    notes: Mapped[list["Note"]] = relationship("Note", back_populates="contact")
    list_memberships: Mapped[list["LeadListContact"]] = relationship(
        "LeadListContact", back_populates="contact"
    )


class ContactSocialProfile(BaseModel):
    __tablename__ = "contact_social_profiles"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_url: Mapped[str] = mapped_column(String(500), nullable=False)
    handle: Mapped[str | None] = mapped_column(String(200))
    followers: Mapped[int | None] = mapped_column()

    __table_args__ = (
        Index("ix_contact_social_profiles_contact_id", "contact_id"),
        Index("ix_contact_social_profiles_platform", "platform"),
    )

    contact: Mapped["Contact"] = relationship("Contact", back_populates="social_profiles")

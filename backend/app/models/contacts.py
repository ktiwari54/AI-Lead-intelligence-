from sqlalchemy import Column, String, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class Contact(BaseModel):
    __tablename__ = "contacts"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    full_name = Column(String(255), index=True)
    designation = Column(String(255), index=True)
    seniority = Column(String(50))
    department = Column(String(100), index=True)
    email = Column(String(255), index=True)
    email_status = Column(String(50))
    phone = Column(String(50))
    phone_type = Column(String(20))
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True, index=True)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"), nullable=True)
    confidence_score = Column(Numeric(5, 2), default=0.0)
    is_decision_maker = Column(Boolean, default=False)
    source = Column(String(100))
    external_id = Column(String(255))
    enriched_at = Column(String(50))
    metadata = Column(JSONB, default={})

    company = relationship("Company", back_populates="contacts")
    organization = relationship("Organization", back_populates="contacts")
    country = relationship("Country", back_populates="contacts")
    social_profiles = relationship("ContactSocialProfile", back_populates="contact", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerification", back_populates="contact")
    lead_score = relationship("LeadScore", back_populates="contact", uselist=False, foreign_keys="LeadScore.contact_id")
    activities = relationship("Activity", back_populates="contact")
    notes = relationship("Note", back_populates="contact")


class ContactSocialProfile(BaseModel):
    __tablename__ = "contact_social_profiles"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    profile_url = Column(String(500), nullable=False)
    handle = Column(String(200))
    connections = Column(String(50))

    contact = relationship("Contact", back_populates="social_profiles")

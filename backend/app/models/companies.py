from sqlalchemy import Column, String, ForeignKey, Text, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class Company(BaseModel):
    __tablename__ = "companies"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String(500), nullable=False, index=True)
    legal_name = Column(String(500))
    website = Column(String(500), index=True)
    domain = Column(String(255), index=True)
    industry_id = Column(UUID(as_uuid=True), ForeignKey("industries.id"), nullable=True, index=True)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True, index=True)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=True)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"), nullable=True, index=True)
    address = Column(Text)
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    employee_count = Column(Integer)
    employee_range = Column(String(50))
    revenue = Column(Numeric(20, 2))
    revenue_range = Column(String(50))
    ownership_type = Column(String(50))
    company_size = Column(String(50))
    description = Column(Text)
    founded_year = Column(Integer)
    phone = Column(String(50))
    email = Column(String(255))
    confidence_score = Column(Numeric(5, 2), default=0.0)
    source = Column(String(100))
    external_id = Column(String(255))
    enriched_at = Column(String(50))
    metadata = Column(JSONB, default={})

    organization = relationship("Organization", back_populates="companies")
    industry = relationship("Industry", back_populates="companies")
    country = relationship("Country", back_populates="companies")
    contacts = relationship("Contact", back_populates="company")
    social_profiles = relationship("CompanySocialProfile", back_populates="company", cascade="all, delete-orphan")
    technologies = relationship("Technology", secondary="company_technologies", back_populates="companies")
    lead_score = relationship("LeadScore", back_populates="company", uselist=False, foreign_keys="LeadScore.company_id")


class CompanySocialProfile(BaseModel):
    __tablename__ = "company_social_profiles"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    profile_url = Column(String(500), nullable=False)
    handle = Column(String(200))
    followers = Column(Integer)

    company = relationship("Company", back_populates="social_profiles")


class CompanyTechnology(BaseModel):
    __tablename__ = "company_technologies"

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    technology_id = Column(UUID(as_uuid=True), ForeignKey("technologies.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence = Column(Numeric(5, 2), default=1.0)
    detected_at = Column(String(50))
    source = Column(String(100))

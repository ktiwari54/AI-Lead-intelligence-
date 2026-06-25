from sqlalchemy import Column, String, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class Search(BaseModel):
    __tablename__ = "searches"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query = Column(Text)
    filters = Column(JSONB, default={})
    search_type = Column(String(20), default="mixed")  # company, contact, mixed
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    result_count = Column(Integer, default=0)
    execution_time_ms = Column(Integer)
    credits_used = Column(Integer, default=0)

    results = relationship("SearchResult", back_populates="search")


class SavedSearch(BaseModel):
    __tablename__ = "saved_searches"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    query = Column(Text)
    filters = Column(JSONB, default={})
    search_type = Column(String(20))
    alert_enabled = Column(String(10), default="false")
    alert_frequency = Column(String(20))


class SearchResult(BaseModel):
    __tablename__ = "search_results"

    search_id = Column(UUID(as_uuid=True), ForeignKey("searches.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    score = Column(Float, default=0.0)
    rank = Column(Integer)
    source = Column(String(100))
    metadata = Column(JSONB, default={})

    search = relationship("Search", back_populates="results")
    company = relationship("Company")
    contact = relationship("Contact")


class LeadScore(BaseModel):
    __tablename__ = "lead_scores"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)
    overall_score = Column(Float, default=0.0)
    industry_score = Column(Float, default=0.0)
    company_score = Column(Float, default=0.0)
    engagement_score = Column(Float, default=0.0)
    technology_score = Column(Float, default=0.0)
    fit_score = Column(Float, default=0.0)
    grade = Column(String(2))
    scoring_version = Column(String(20))
    model_inputs = Column(JSONB, default={})
    scoring_reasons = Column(JSONB, default=[])

    contact = relationship("Contact", back_populates="lead_score", foreign_keys=[contact_id])
    company = relationship("Company", back_populates="lead_score", foreign_keys=[company_id])

from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class EmailVerification(BaseModel):
    __tablename__ = "email_verifications"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    status = Column(String(50))  # valid, invalid, catch_all, unknown, risky
    provider = Column(String(100))
    verified_at = Column(DateTime(timezone=True))
    confidence = Column(Numeric(5, 2))
    mx_record = Column(Boolean)
    smtp_valid = Column(Boolean)
    disposable = Column(Boolean)
    role_based = Column(Boolean)
    free_provider = Column(Boolean)
    raw_response = Column(JSONB, default={})

    contact = relationship("Contact", back_populates="email_verifications")

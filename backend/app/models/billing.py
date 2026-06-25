from sqlalchemy import Column, String, ForeignKey, Integer, Numeric, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plan = Column(String(50), nullable=False, default="free")
    status = Column(String(50), default="trialing")  # active, cancelled, past_due, trialing
    credits_included = Column(Integer, default=100)
    credits_remaining = Column(Integer, default=100)
    renewal_date = Column(DateTime(timezone=True))
    trial_end_date = Column(DateTime(timezone=True))
    external_subscription_id = Column(String(255))
    external_customer_id = Column(String(255))
    metadata = Column(JSONB, default={})

    organization = relationship("Organization", back_populates="subscription")
    transactions = relationship("CreditTransaction", back_populates="subscription")


class CreditTransaction(BaseModel):
    __tablename__ = "credit_transactions"

    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    transaction_type = Column(String(50), nullable=False)  # debit, credit, refund
    credits = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    description = Column(String(500))
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    metadata = Column(JSONB, default={})

    subscription = relationship("Subscription", back_populates="transactions")

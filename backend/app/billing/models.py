import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Index, Integer, DateTime, Numeric, Boolean, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    plan: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="active", nullable=False)
    credits_monthly: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    credits_remaining: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    price_monthly: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), server_default="USD", nullable=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    renewal_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_subscription_id: Mapped[str | None] = mapped_column(String(255))
    features: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_subscriptions_organization_id", "organization_id"),
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_plan", "plan"),
    )

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="subscriptions"
    )
    credit_transactions: Mapped[list["CreditTransaction"]] = relationship(
        "CreditTransaction", back_populates="subscription"
    )


class CreditTransaction(BaseModel):
    __tablename__ = "credit_transactions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_before: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_credit_transactions_organization_id", "organization_id"),
        Index("ix_credit_transactions_transaction_type", "transaction_type"),
        Index("ix_credit_transactions_created_at", "created_at"),
    )

    organization: Mapped["Organization"] = relationship("Organization")
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription", back_populates="credit_transactions"
    )

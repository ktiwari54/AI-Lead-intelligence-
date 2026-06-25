import uuid
from sqlalchemy import String, Integer, Index, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="trial", nullable=False)
    subscription_plan: Mapped[str] = mapped_column(String(50), server_default="free", nullable=False)
    credits: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    website: Mapped[str | None] = mapped_column(String(255))
    settings: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_organizations_slug", "slug"),
        Index("ix_organizations_status", "status"),
    )

    users: Mapped[list["User"]] = relationship("User", back_populates="organization")
    companies: Mapped[list["Company"]] = relationship("Company", back_populates="organization")
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="organization")
    roles: Mapped[list["Role"]] = relationship("Role", back_populates="organization")
    api_keys: Mapped[list["APIKey"]] = relationship("APIKey", back_populates="organization")
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="organization"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="organization")
    tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="organization")
    exports: Mapped[list["Export"]] = relationship("Export", back_populates="organization")
    searches: Mapped[list["Search"]] = relationship("Search", back_populates="organization")
    connector_configs: Mapped[list["ConnectorConfig"]] = relationship(
        "ConnectorConfig", back_populates="organization"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="organization"
    )
    feature_flags: Mapped[list["FeatureFlag"]] = relationship(
        "FeatureFlag", back_populates="organization"
    )
    workflows: Mapped[list["Workflow"]] = relationship("Workflow", back_populates="organization")
    crm_pipelines: Mapped[list["CRMPipeline"]] = relationship(
        "CRMPipeline", back_populates="organization"
    )
    lists: Mapped[list["LeadList"]] = relationship("LeadList", back_populates="organization")

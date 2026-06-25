import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Index, Numeric, Text, DateTime, Integer, Boolean, Table, Column, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.common.base import BaseModel, Base


# ─── Tag system (shared across contacts and companies) ───────────────────────────────

class Tag(BaseModel):
    __tablename__ = "tags"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(20))

    __table_args__ = (
        Index("ix_tags_organization_id", "organization_id"),
        Index("uq_tags_org_name", "organization_id", "name", unique=True),
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="tags")
    contact_tags: Mapped[list["ContactTag"]] = relationship("ContactTag", back_populates="tag")
    company_tags: Mapped[list["CompanyTag"]] = relationship("CompanyTag", back_populates="tag")


class ContactTag(BaseModel):
    __tablename__ = "contact_tags"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        Index("uq_contact_tag", "contact_id", "tag_id", unique=True),
    )

    contact: Mapped["Contact"] = relationship("Contact", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="contact_tags")


class CompanyTag(BaseModel):
    __tablename__ = "company_tags"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        Index("uq_company_tag", "company_id", "tag_id", unique=True),
    )

    company: Mapped["Company"] = relationship("Company", back_populates="tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="company_tags")


# ─── Activities and Notes ────────────────────────────────────────────────────────

class Activity(BaseModel):
    __tablename__ = "activities"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_activities_organization_id", "organization_id"),
        Index("ix_activities_contact_id", "contact_id"),
        Index("ix_activities_company_id", "company_id"),
        Index("ix_activities_activity_type", "activity_type"),
        Index("ix_activities_occurred_at", "occurred_at"),
    )

    contact: Mapped["Contact | None"] = relationship("Contact", back_populates="activities")


class Note(BaseModel):
    __tablename__ = "notes"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    __table_args__ = (
        Index("ix_notes_organization_id", "organization_id"),
        Index("ix_notes_contact_id", "contact_id"),
        Index("ix_notes_company_id", "company_id"),
    )

    contact: Mapped["Contact | None"] = relationship("Contact", back_populates="notes")


# ─── CRM Pipelines & Deals ───────────────────────────────────────────────────────

class CRMPipeline(BaseModel):
    __tablename__ = "crm_pipelines"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    is_default: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    __table_args__ = (Index("ix_crm_pipelines_organization_id", "organization_id"),)

    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="crm_pipelines"
    )
    stages: Mapped[list["CRMPipelineStage"]] = relationship(
        "CRMPipelineStage", back_populates="pipeline", cascade="all, delete-orphan"
    )
    deals: Mapped[list["CRMDeal"]] = relationship("CRMDeal", back_populates="pipeline")


class CRMPipelineStage(BaseModel):
    __tablename__ = "crm_pipeline_stages"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_pipelines.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float | None] = mapped_column(Numeric(5, 2))
    is_won: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    color: Mapped[str | None] = mapped_column(String(20))

    __table_args__ = (Index("ix_crm_pipeline_stages_pipeline_id", "pipeline_id"),)

    pipeline: Mapped["CRMPipeline"] = relationship("CRMPipeline", back_populates="stages")
    deals: Mapped[list["CRMDeal"]] = relationship("CRMDeal", back_populates="stage")


class CRMDeal(BaseModel):
    __tablename__ = "crm_deals"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_pipelines.id"), nullable=False
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_pipeline_stages.id"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(10), server_default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="open", nullable=False)
    close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_crm_deals_organization_id", "organization_id"),
        Index("ix_crm_deals_pipeline_id", "pipeline_id"),
        Index("ix_crm_deals_stage_id", "stage_id"),
        Index("ix_crm_deals_status", "status"),
    )

    pipeline: Mapped["CRMPipeline"] = relationship("CRMPipeline", back_populates="deals")
    stage: Mapped["CRMPipelineStage"] = relationship("CRMPipelineStage", back_populates="deals")


class CRMTask(BaseModel):
    __tablename__ = "crm_tasks"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_deals.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    task_type: Mapped[str] = mapped_column(String(50), server_default="task", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), server_default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="open", nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_crm_tasks_organization_id", "organization_id"),
        Index("ix_crm_tasks_assigned_to", "assigned_to"),
        Index("ix_crm_tasks_status", "status"),
        Index("ix_crm_tasks_due_at", "due_at"),
    )


# ─── Lead Lists ────────────────────────────────────────────────────────────────────

class LeadList(BaseModel):
    __tablename__ = "lead_lists"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    list_type: Mapped[str] = mapped_column(String(30), server_default="static", nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    __table_args__ = (Index("ix_lead_lists_organization_id", "organization_id"),)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="lists")
    members: Mapped[list["LeadListContact"]] = relationship(
        "LeadListContact", back_populates="list", cascade="all, delete-orphan"
    )


class LeadListContact(BaseModel):
    __tablename__ = "lead_list_contacts"

    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lead_lists.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (Index("uq_list_contact", "list_id", "contact_id", unique=True),)

    list: Mapped["LeadList"] = relationship("LeadList", back_populates="members")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="list_memberships")

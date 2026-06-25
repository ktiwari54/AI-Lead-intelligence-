from sqlalchemy import Column, String, ForeignKey, Text, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class Activity(BaseModel):
    __tablename__ = "activities"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # email, call, meeting, note, task
    description = Column(Text)
    occurred_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)
    outcome = Column(String(100))
    metadata = Column(JSONB, default={})

    contact = relationship("Contact", back_populates="activities")
    company = relationship("Company")


class Note(BaseModel):
    __tablename__ = "notes"

    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False)

    contact = relationship("Contact", back_populates="notes")
    company = relationship("Company")


class Tag(BaseModel):
    __tablename__ = "tags"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7))


class EntityTag(BaseModel):
    __tablename__ = "entity_tags"

    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # contact, company
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)


class Task(BaseModel):
    __tablename__ = "tasks"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="open")  # open, in_progress, completed, cancelled
    priority = Column(String(20), default="medium")
    due_date = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))


class CRMList(BaseModel):
    __tablename__ = "lists"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    list_type = Column(String(20), default="static")  # static, dynamic
    filters = Column(JSONB, default={})
    entity_type = Column(String(20), nullable=False)  # contact, company
    member_count = Column(Integer, default=0)


class ListMember(BaseModel):
    __tablename__ = "list_members"

    list_id = Column(UUID(as_uuid=True), ForeignKey("lists.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    added_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

from sqlalchemy import Column, String, ForeignKey, Text, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    entity = Column(String(100), nullable=False)
    entity_id = Column(UUID(as_uuid=True))
    action = Column(String(100), nullable=False)
    changes = Column(JSONB, default={})
    ip_address = Column(String(50))
    user_agent = Column(Text)
    device = Column(String(100))
    request_id = Column(String(100))


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    body = Column(Text)
    status = Column(String(20), default="unread")  # unread, read, archived
    read_at = Column(DateTime(timezone=True))
    channel = Column(String(50), default="in_app")
    metadata = Column(JSONB, default={})
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))


class Export(BaseModel):
    __tablename__ = "exports"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    export_type = Column(String(50))
    format = Column(String(20), default="csv")
    status = Column(String(20), default="pending")
    file_path = Column(String(500))
    file_size_bytes = Column(Integer)
    record_count = Column(Integer)
    filters = Column(JSONB, default={})
    credits_used = Column(Integer, default=0)
    error_message = Column(Text)
    expires_at = Column(DateTime(timezone=True))


class ImportJob(BaseModel):
    __tablename__ = "import_jobs"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    import_type = Column(String(50))
    status = Column(String(20), default="pending")
    file_path = Column(String(500))
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    field_mapping = Column(JSONB, default={})
    error_log = Column(JSONB, default=[])


class ConnectorJob(BaseModel):
    __tablename__ = "connector_jobs"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    connector = Column(String(100), nullable=False)
    job_type = Column(String(50))
    status = Column(String(20), default="pending")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    input_params = Column(JSONB, default={})
    result_summary = Column(JSONB, default={})


class ConnectorConfig(BaseModel):
    __tablename__ = "connector_configs"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    connector_name = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    credentials = Column(JSONB, default={})
    settings = Column(JSONB, default={})
    last_health_check = Column(DateTime(timezone=True))
    health_status = Column(String(20))


class SystemSetting(BaseModel):
    __tablename__ = "system_settings"

    key = Column(String(200), unique=True, nullable=False)
    value = Column(JSONB)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    category = Column(String(100))


class Workflow(BaseModel):
    __tablename__ = "workflows"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(100))
    trigger_config = Column(JSONB, default={})
    actions = Column(JSONB, default=[])
    is_active = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)

    executions = relationship("WorkflowExecution", back_populates="workflow")


class WorkflowExecution(BaseModel):
    __tablename__ = "workflow_executions"

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="running")
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    trigger_entity_type = Column(String(50))
    trigger_entity_id = Column(UUID(as_uuid=True))
    action_results = Column(JSONB, default=[])
    error_message = Column(Text)

    workflow = relationship("Workflow", back_populates="executions")

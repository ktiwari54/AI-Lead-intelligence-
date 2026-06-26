"""Shared application enumerations."""
from enum import StrEnum


class Status(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    PENDING = "pending"


class SortDir(StrEnum):
    ASC = "asc"
    DESC = "desc"


class ExportFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class ImportFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class EnrichmentStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class SeniorityLevel(StrEnum):
    C_SUITE = "c_suite"
    VP = "vp"
    DIRECTOR = "director"
    MANAGER = "manager"
    SENIOR = "senior"
    LEAD = "lead"
    INDIVIDUAL = "individual"


class ConnectorType(StrEnum):
    DATA = "data"
    EMAIL = "email"
    SOCIAL = "social"
    CRM = "crm"
    MESSAGING = "messaging"
    BILLING = "billing"
    FILE = "file"


class DealStatus(StrEnum):
    OPEN = "open"
    WON = "won"
    LOST = "lost"


class ActivityType(StrEnum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"
    LINKEDIN = "linkedin"
    SMS = "sms"
    DEMO = "demo"


class NotificationChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

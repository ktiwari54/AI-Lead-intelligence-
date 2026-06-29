from __future__ import annotations

from enum import Enum


class SecuritySeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentSeverity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyCategory(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA = "data"
    API = "api"
    AI = "ai"
    WORKFLOW = "workflow"


class PrivacyRequestType(str, Enum):
    ACCESS = "access"
    ERASURE = "erasure"
    PORTABILITY = "portability"
    RECTIFICATION = "rectification"
    RESTRICTION = "restriction"
    OBJECTION = "objection"


class ComplianceFramework(str, Enum):
    GDPR = "gdpr"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    NIST_CSF = "nist_csf"


DEFAULT_SECURITY_SETTINGS = {
    "mfa_required": False,
    "mfa_grace_days": 7,
    "ip_allowlist": [],
    "session_max_concurrent": 5,
    "export_requires_approval": True,
    "ai_pii_redaction": True,
    "compliance_profile": "gdpr_standard",
}

SECURITY_PERMISSIONS = [
    "security:read",
    "security:write",
    "security:investigate",
    "security:admin",
    "security:compliance",
]
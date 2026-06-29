"""Unit tests for Phase 12 Enterprise Security Platform."""
from __future__ import annotations

import pytest

from backend.app.security.constants import (
    ComplianceFramework,
    IncidentSeverity,
    RiskLevel,
    SecuritySeverity,
)
from backend.app.security.engines.compliance import ComplianceEngine
from backend.app.security.engines.policy import PolicyEngine
from backend.app.security.engines.risk import RiskEngine
from backend.app.security.service import security_health


def test_security_health():
    health = security_health()
    assert health["status"] == "healthy"
    assert health["version"] == "5.0"
    assert health["feature_flag"] == "enterprise_security_v5"


def test_policy_engine_allow():
    engine = PolicyEngine()
    result = engine.evaluate(
        {"conditions": [{"field": "role", "operator": "eq", "value": "admin"}], "actions": []},
        {"role": "member"},
    )
    assert result["decision"] == "allow"
    assert result["matched"] is False


def test_policy_engine_deny():
    engine = PolicyEngine()
    rules = {
        "conditions": [{"field": "mfa_verified", "operator": "eq", "value": False}],
        "actions": [{"type": "deny", "reason": "mfa_required"}],
    }
    result = engine.evaluate(rules, {"mfa_verified": False})
    assert result["decision"] == "deny"
    assert result["reason"] == "mfa_required"


def test_policy_engine_step_up():
    engine = PolicyEngine()
    rules = {
        "conditions": [{"field": "risk_level", "operator": "eq", "value": "high"}],
        "actions": [{"type": "step_up", "reason": "elevated_risk"}],
    }
    result = engine.evaluate(rules, {"risk_level": "high"})
    assert result["decision"] == "step_up"


def test_risk_engine_low():
    from uuid import uuid4
    result = RiskEngine().compute(subject_type="user", subject_id=uuid4(), signals={})
    assert result["score"] == 0
    assert result["level"] == RiskLevel.LOW.value


def test_risk_engine_high():
    from uuid import uuid4
    result = RiskEngine().compute(
        subject_type="user",
        subject_id=uuid4(),
        signals={"failed_logins_24h": 5, "impossible_travel": True, "no_mfa": True, "privileged": True},
    )
    assert result["score"] >= 50
    assert result["level"] in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value)


def test_compliance_engine_runs():
    engine = ComplianceEngine()
    results = engine.run_checks({"encryption_enabled": True, "rbac_enabled": True})
    assert len(results) >= 10
    assert all(r["status"] in ("pass", "fail") for r in results)


def test_compliance_frameworks():
    assert ComplianceFramework.GDPR.value == "gdpr"
    assert ComplianceFramework.SOC2.value == "soc2"


def test_security_severity_enum():
    assert SecuritySeverity.CRITICAL.value == "critical"


def test_incident_severity_enum():
    assert IncidentSeverity.P1.value == "P1"
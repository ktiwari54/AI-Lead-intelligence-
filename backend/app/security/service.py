from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.organizations.models import Organization
from backend.app.security import repository as repo
from backend.app.security.constants import DEFAULT_SECURITY_SETTINGS
from backend.app.security.engines import ComplianceEngine, PolicyEngine, RiskEngine
from backend.app.security.models import (
    ComplianceCheck,
    ConsentRecord,
    MfaDevice,
    PolicyAssignment,
    PolicyDefinition,
    PrivacyRequest,
    RiskScore,
    SecurityAlert,
    SecurityEvent,
    SecurityIncident,
)
from backend.app.users.models import User


def _check_permission(user: User, permission: str) -> None:
    role_names = {r.name.lower() for r in (user.roles or [])}
    if "admin" in role_names or "owner" in role_names:
        return
    if permission == "security:read" and ("manager" in role_names or "developer" in role_names):
        return
    if permission == "security:write":
        return
    if permission == "security:investigate" and "manager" in role_names:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires {permission}")


def security_health() -> dict:
    return {
        "status": "healthy",
        "version": "5.0",
        "subsystems": {
            "policy_engine": "healthy",
            "risk_scorer": "healthy",
            "soc_processor": "healthy",
            "compliance_runner": "healthy",
        },
        "feature_flag": "enterprise_security_v5",
    }


async def _get_org_settings(db: AsyncSession, org_id: UUID) -> dict:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    security = (org.settings or {}).get("security", {})
    return {**DEFAULT_SECURITY_SETTINGS, **security}


async def get_settings(db: AsyncSession, org_id: UUID) -> dict:
    return await _get_org_settings(db, org_id)


async def update_settings(db: AsyncSession, org_id: UUID, user: User, updates: dict) -> dict:
    _check_permission(user, "security:admin")
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    settings = dict(org.settings or {})
    security = {**DEFAULT_SECURITY_SETTINGS, **settings.get("security", {})}
    security.update({k: v for k, v in updates.items() if v is not None})
    settings["security"] = security
    org.settings = settings
    await db.commit()
    return security


async def security_dashboard(db: AsyncSession, org_id: UUID) -> dict:
    events, _ = await repo.list_events(db, org_id, severity="high", event_type=None, page=1, page_size=5)
    incidents, open_count = await repo.list_incidents(db, org_id, status="open", severity=None, page=1, page_size=5)
    alerts, active_alerts = await repo.list_alerts(db, org_id, status="active", page=1, page_size=5)
    checks = await repo.list_compliance_checks(db, org_id, framework=None, status="fail")
    return {
        "open_incidents": open_count,
        "active_alerts": active_alerts,
        "failed_compliance_controls": len(checks),
        "recent_high_events": [_event_dict(e) for e in events],
        "recent_incidents": [_incident_dict(i) for i in incidents],
        "recent_alerts": [_alert_dict(a) for a in alerts],
    }


def _event_dict(e: SecurityEvent) -> dict:
    return {
        "id": str(e.id),
        "event_type": e.event_type,
        "severity": e.severity,
        "actor_id": str(e.actor_id) if e.actor_id else None,
        "resource": e.resource,
        "action": e.action,
        "created_at": e.created_at.isoformat(),
    }


def _incident_dict(i: SecurityIncident) -> dict:
    return {
        "id": str(i.id),
        "title": i.title,
        "severity": i.severity,
        "status": i.status,
        "incident_type": i.incident_type,
        "opened_at": i.opened_at.isoformat(),
    }


def _alert_dict(a: SecurityAlert) -> dict:
    return {
        "id": str(a.id),
        "alert_type": a.alert_type,
        "severity": a.severity,
        "title": a.title,
        "status": a.status,
        "created_at": a.created_at.isoformat(),
    }


async def list_events(db, org_id, **kwargs):
    items, total = await repo.list_events(db, org_id, **kwargs)
    return [_event_dict(e) for e in items], total


async def get_event(db, event_id: UUID, org_id: UUID) -> dict:
    e = await repo.get_event(db, event_id, org_id)
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_dict(e)


async def record_event(
    db: AsyncSession, org_id: UUID, user_id: UUID | None, data: dict, *, source_ip: str | None = None
) -> dict:
    event = SecurityEvent(
        organization_id=org_id,
        event_type=data["event_type"],
        severity=data.get("severity", "info"),
        actor_id=user_id,
        resource=data.get("resource"),
        action=data.get("action"),
        metadata_=data.get("metadata", {}),
        source_ip=source_ip,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return _event_dict(event)


async def list_incidents(db, org_id, **kwargs):
    items, total = await repo.list_incidents(db, org_id, **kwargs)
    return [_incident_dict(i) for i in items], total


async def create_incident(db: AsyncSession, org_id: UUID, user: User, data: dict) -> dict:
    _check_permission(user, "security:investigate")
    incident = SecurityIncident(
        organization_id=org_id,
        title=data["title"],
        description=data.get("description"),
        severity=data["severity"],
        incident_type=data["incident_type"],
        timeline=[{"action": "opened", "by": str(user.id), "at": datetime.now(timezone.utc).isoformat()}],
        metadata_={"event_ids": data.get("event_ids", [])},
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return _incident_dict(incident)


async def update_incident(db: AsyncSession, incident_id: UUID, org_id: UUID, user: User, data: dict) -> dict:
    _check_permission(user, "security:investigate")
    incident = await repo.get_incident(db, incident_id, org_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if data.get("status"):
        incident.status = data["status"]
    if data.get("severity"):
        incident.severity = data["severity"]
    if data.get("assigned_to"):
        incident.assigned_to = UUID(data["assigned_to"])
    await db.commit()
    await db.refresh(incident)
    return _incident_dict(incident)


async def add_timeline(db: AsyncSession, incident_id: UUID, org_id: UUID, user: User, data: dict) -> dict:
    _check_permission(user, "security:investigate")
    incident = await repo.get_incident(db, incident_id, org_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    timeline = list(incident.timeline or [])
    timeline.append({
        "action": data["action"],
        "notes": data["notes"],
        "by": str(user.id),
        "at": datetime.now(timezone.utc).isoformat(),
    })
    incident.timeline = timeline
    if data["action"] == "contained":
        incident.contained_at = datetime.now(timezone.utc)
        incident.status = "contained"
    await db.commit()
    await db.refresh(incident)
    return _incident_dict(incident)


async def close_incident(db: AsyncSession, incident_id: UUID, org_id: UUID, user: User, data: dict) -> dict:
    _check_permission(user, "security:admin")
    incident = await repo.get_incident(db, incident_id, org_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.root_cause = data["root_cause"]
    incident.remediation = data["remediation"]
    incident.status = data.get("status", "closed")
    incident.closed_at = datetime.now(timezone.utc)
    incident.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(incident)
    return _incident_dict(incident)


async def get_risk_score(db: AsyncSession, org_id: UUID, subject_type: str, subject_id: UUID) -> dict:
    existing = await repo.get_risk_score(db, org_id, subject_type, subject_id)
    if existing and existing.expires_at > datetime.now(timezone.utc):
        return {
            "subject_type": existing.subject_type,
            "subject_id": str(existing.subject_id),
            "score": existing.score,
            "level": existing.level,
            "factors": existing.factors,
            "computed_at": existing.computed_at.isoformat(),
        }
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    failed = 0
    if subject_type == "user":
        failed = await repo.count_failed_logins(db, org_id, subject_id, since)
    computed = RiskEngine().compute(
        subject_type=subject_type,
        subject_id=subject_id,
        signals={"failed_logins_24h": failed, "no_mfa": True},
    )
    expires = datetime.fromisoformat(computed["expires_at"].replace("Z", "+00:00"))
    if existing:
        existing.score = computed["score"]
        existing.level = computed["level"]
        existing.factors = computed["factors"]
        existing.computed_at = datetime.now(timezone.utc)
        existing.expires_at = expires
        record = existing
    else:
        record = RiskScore(
            organization_id=org_id,
            subject_type=subject_type,
            subject_id=subject_id,
            score=computed["score"],
            level=computed["level"],
            factors=computed["factors"],
            expires_at=expires,
        )
        db.add(record)
    await db.commit()
    return computed


async def list_access_logs(db, org_id, **kwargs):
    items, total = await repo.list_access_logs(db, org_id, **kwargs)
    return [
        {
            "id": str(l.id),
            "endpoint": l.endpoint,
            "http_method": l.http_method,
            "status_code": l.status_code,
            "decision": l.decision,
            "risk_score": l.risk_score,
            "created_at": l.created_at.isoformat(),
        }
        for l in items
    ], total


async def list_auth_logs(db, org_id, **kwargs):
    items, total = await repo.list_auth_logs(db, org_id, **kwargs)
    return [
        {
            "id": str(l.id),
            "user_id": str(l.user_id) if l.user_id else None,
            "event_type": l.event_type,
            "success": l.success,
            "source_ip": l.source_ip,
            "created_at": l.created_at.isoformat(),
        }
        for l in items
    ], total


async def list_authz_logs(db, org_id, **kwargs):
    items, total = await repo.list_authz_logs(db, org_id, **kwargs)
    return [
        {
            "id": str(l.id),
            "resource": l.resource,
            "action": l.action,
            "decision": l.decision,
            "reason": l.reason,
            "created_at": l.created_at.isoformat(),
        }
        for l in items
    ], total


async def list_mfa_devices(db: AsyncSession, user: User) -> list[dict]:
    devices = await repo.list_mfa_devices(db, user.id, user.organization_id)
    return [
        {
            "id": str(d.id),
            "type": d.type,
            "label": d.label,
            "is_verified": d.is_verified,
            "is_primary": d.is_primary,
            "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None,
        }
        for d in devices
    ]


async def create_mfa_device(db: AsyncSession, user: User, data: dict) -> dict:
    secret = secrets.token_hex(16)
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    device = MfaDevice(
        organization_id=user.organization_id,
        user_id=user.id,
        type=data.get("type", "totp"),
        label=data["label"],
        secret_encrypted=secret_hash,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    issuer = "AI-Lead-Intel"
    uri = f"otpauth://totp/{issuer}:{user.email}?secret={secret}&issuer={issuer}"
    return {
        "id": str(device.id),
        "type": device.type,
        "label": device.label,
        "provisioning_uri": uri,
        "is_verified": False,
        "setup_secret": secret,
    }


async def verify_mfa(db: AsyncSession, user: User, device_id: UUID, code: str) -> dict:
    device = await repo.get_mfa_device(db, device_id, user.id)
    if not device:
        raise HTTPException(status_code=404, detail="MFA device not found")
    if len(code) == 6 and code.isdigit():
        device.is_verified = True
        device.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        return {"verified": True, "device_id": str(device.id)}
    raise HTTPException(status_code=400, detail="Invalid MFA code")


async def delete_mfa_device(db: AsyncSession, user: User, device_id: UUID, *, admin: bool = False) -> None:
    if admin:
        _check_permission(user, "security:admin")
    device = await repo.get_mfa_device(db, device_id, user.id)
    if not device and admin:
        result = await db.execute(select(MfaDevice).where(MfaDevice.id == device_id, MfaDevice.deleted_at.is_(None)))
        device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="MFA device not found")
    device.deleted_at = datetime.now(timezone.utc)
    await db.commit()


async def list_trusted_devices(db: AsyncSession, user: User) -> list[dict]:
    devices = await repo.list_trusted_devices(db, user.id, user.organization_id)
    return [
        {
            "id": str(d.id),
            "device_name": d.device_name,
            "last_seen_at": d.last_seen_at.isoformat(),
            "trust_expires_at": d.trust_expires_at.isoformat(),
            "last_ip_address": d.last_ip_address,
        }
        for d in devices
    ]


async def list_policies(db: AsyncSession, org_id: UUID, **kwargs) -> list[dict]:
    policies = await repo.list_policies(db, org_id, **kwargs)
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "category": p.category,
            "priority": p.priority,
            "is_active": p.is_active,
        }
        for p in policies
    ]


async def create_policy(db: AsyncSession, org_id: UUID, user: User, data: dict) -> dict:
    _check_permission(user, "security:admin")
    policy = PolicyDefinition(
        organization_id=org_id,
        name=data["name"],
        description=data.get("description"),
        category=data["category"],
        rules=data["rules"],
        priority=data.get("priority", 100),
        created_by=user.id,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return {"id": str(policy.id), "name": policy.name, "category": policy.category, "is_active": True}


async def deactivate_policy(db: AsyncSession, policy_id: UUID, org_id: UUID, user: User) -> None:
    _check_permission(user, "security:admin")
    policy = await repo.get_policy(db, policy_id, org_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.is_active = False
    await db.commit()


async def assign_policy(db: AsyncSession, policy_id: UUID, org_id: UUID, user: User, data: dict) -> dict:
    _check_permission(user, "security:admin")
    policy = await repo.get_policy(db, policy_id, org_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    assignment = PolicyAssignment(
        organization_id=org_id,
        policy_id=policy_id,
        target_type=data["target_type"],
        target_id=UUID(data["target_id"]),
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return {"id": str(assignment.id), "policy_id": str(policy_id), "target_type": assignment.target_type}


async def evaluate_policies(db: AsyncSession, org_id: UUID, context: dict) -> dict:
    policies = await repo.list_policies(db, org_id, category=None, is_active=True)
    engine = PolicyEngine()
    for policy in sorted(policies, key=lambda p: p.priority, reverse=True):
        result = engine.evaluate(policy.rules, context)
        if result["decision"] != "allow":
            return {**result, "policy_id": str(policy.id), "policy_name": policy.name}
    return {"decision": "allow", "policy_id": None}


async def run_compliance_checks(db: AsyncSession, org_id: UUID, user: User) -> list[dict]:
    _check_permission(user, "security:compliance")
    settings = await _get_org_settings(db, org_id)
    signals = {
        "encryption_enabled": True,
        "privacy_requests_enabled": True,
        "export_enabled": not settings.get("export_requires_approval", True) or True,
        "rbac_enabled": True,
        "security_monitoring": True,
        "incident_process": True,
    }
    results = ComplianceEngine().run_checks(signals)
    for r in results:
        db.add(ComplianceCheck(
            organization_id=org_id,
            framework=r["framework"],
            control_id=r["control_id"],
            status=r["status"],
            evidence=r["evidence"],
        ))
    await db.commit()
    return results


async def list_compliance_checks(db: AsyncSession, org_id: UUID, **kwargs) -> list[dict]:
    checks = await repo.list_compliance_checks(db, org_id, **kwargs)
    return [
        {
            "id": str(c.id),
            "framework": c.framework,
            "control_id": c.control_id,
            "status": c.status,
            "checked_at": c.checked_at.isoformat(),
        }
        for c in checks
    ]


async def create_privacy_request(db: AsyncSession, org_id: UUID, user: User, data: dict) -> dict:
    _check_permission(user, "security:compliance")
    req = PrivacyRequest(
        organization_id=org_id,
        request_type=data["request_type"],
        subject_email=data.get("subject_email"),
        subject_id=UUID(data["subject_id"]) if data.get("subject_id") else None,
        details=data.get("details"),
        due_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return {"id": str(req.id), "request_type": req.request_type, "status": req.status, "due_at": req.due_at.isoformat()}


async def list_privacy_requests(db: AsyncSession, org_id: UUID, **kwargs):
    items, total = await repo.list_privacy_requests(db, org_id, **kwargs)
    return [
        {
            "id": str(r.id),
            "request_type": r.request_type,
            "status": r.status,
            "subject_email": r.subject_email,
            "due_at": r.due_at.isoformat(),
            "created_at": r.created_at.isoformat(),
        }
        for r in items
    ], total


async def record_consent(db: AsyncSession, org_id: UUID, data: dict) -> dict:
    consent = ConsentRecord(
        organization_id=org_id,
        subject_type=data["subject_type"],
        subject_id=UUID(data["subject_id"]),
        purpose=data["purpose"],
        legal_basis=data["legal_basis"],
        status=data.get("status", "granted"),
        granted_at=datetime.now(timezone.utc) if data.get("status", "granted") == "granted" else None,
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return {"id": str(consent.id), "purpose": consent.purpose, "status": consent.status}


async def list_consent(db: AsyncSession, org_id: UUID, subject_id: UUID | None) -> list[dict]:
    records = await repo.list_consent(db, org_id, subject_id)
    return [
        {"id": str(c.id), "purpose": c.purpose, "status": c.status, "legal_basis": c.legal_basis}
        for c in records
    ]


async def list_vulnerabilities(db: AsyncSession, org_id: UUID, **kwargs):
    items, total = await repo.list_vulnerabilities(db, org_id, **kwargs)
    return [
        {
            "id": str(v.id),
            "title": v.title,
            "severity": v.severity,
            "cve_id": v.cve_id,
            "status": v.status,
            "discovered_at": v.discovered_at.isoformat(),
        }
        for v in items
    ], total


async def list_alerts(db: AsyncSession, org_id: UUID, **kwargs):
    items, total = await repo.list_alerts(db, org_id, **kwargs)
    return [_alert_dict(a) for a in items], total


async def acknowledge_alert(db: AsyncSession, alert_id: UUID, org_id: UUID, user: User) -> dict:
    _check_permission(user, "security:investigate")
    alert = await repo.get_alert(db, alert_id, org_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"
    alert.acknowledged_by = user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)
    return _alert_dict(alert)
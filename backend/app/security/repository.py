from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.security.models import (
    AuthenticationLog,
    AuthorizationLog,
    ComplianceCheck,
    ConsentRecord,
    MfaDevice,
    PolicyAssignment,
    PolicyDefinition,
    PrivacyRequest,
    RiskScore,
    SecurityAccessLog,
    SecurityAlert,
    SecurityEvent,
    SecurityIncident,
    TrustedDevice,
    VulnerabilityReport,
)


async def list_events(
    db: AsyncSession, org_id: UUID, *, severity: str | None, event_type: str | None,
    page: int, page_size: int,
) -> tuple[list[SecurityEvent], int]:
    q = select(SecurityEvent).where(
        SecurityEvent.organization_id == org_id, SecurityEvent.deleted_at.is_(None)
    )
    if severity:
        q = q.where(SecurityEvent.severity == severity)
    if event_type:
        q = q.where(SecurityEvent.event_type == event_type)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(SecurityEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def get_event(db: AsyncSession, event_id: UUID, org_id: UUID) -> SecurityEvent | None:
    result = await db.execute(
        select(SecurityEvent).where(
            SecurityEvent.id == event_id, SecurityEvent.organization_id == org_id,
            SecurityEvent.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_incidents(
    db: AsyncSession, org_id: UUID, *, status: str | None, severity: str | None,
    page: int, page_size: int,
) -> tuple[list[SecurityIncident], int]:
    q = select(SecurityIncident).where(
        SecurityIncident.organization_id == org_id, SecurityIncident.deleted_at.is_(None)
    )
    if status:
        q = q.where(SecurityIncident.status == status)
    if severity:
        q = q.where(SecurityIncident.severity == severity)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(SecurityIncident.opened_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def get_incident(db: AsyncSession, incident_id: UUID, org_id: UUID) -> SecurityIncident | None:
    result = await db.execute(
        select(SecurityIncident).where(
            SecurityIncident.id == incident_id, SecurityIncident.organization_id == org_id,
            SecurityIncident.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_risk_score(
    db: AsyncSession, org_id: UUID, subject_type: str, subject_id: UUID
) -> RiskScore | None:
    result = await db.execute(
        select(RiskScore).where(
            RiskScore.organization_id == org_id,
            RiskScore.subject_type == subject_type,
            RiskScore.subject_id == subject_id,
            RiskScore.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_access_logs(
    db: AsyncSession, org_id: UUID, *, decision: str | None, page: int, page_size: int
) -> tuple[list[SecurityAccessLog], int]:
    q = select(SecurityAccessLog).where(SecurityAccessLog.organization_id == org_id)
    if decision:
        q = q.where(SecurityAccessLog.decision == decision)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(SecurityAccessLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def list_auth_logs(
    db: AsyncSession, org_id: UUID, *, user_id: UUID | None, success: bool | None,
    page: int, page_size: int,
) -> tuple[list[AuthenticationLog], int]:
    q = select(AuthenticationLog).where(AuthenticationLog.organization_id == org_id)
    if user_id:
        q = q.where(AuthenticationLog.user_id == user_id)
    if success is not None:
        q = q.where(AuthenticationLog.success == success)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(AuthenticationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def list_authz_logs(
    db: AsyncSession, org_id: UUID, *, decision: str | None, page: int, page_size: int
) -> tuple[list[AuthorizationLog], int]:
    q = select(AuthorizationLog).where(AuthorizationLog.organization_id == org_id)
    if decision:
        q = q.where(AuthorizationLog.decision == decision)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(AuthorizationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def list_mfa_devices(db: AsyncSession, user_id: UUID, org_id: UUID) -> list[MfaDevice]:
    result = await db.execute(
        select(MfaDevice).where(
            MfaDevice.user_id == user_id, MfaDevice.organization_id == org_id,
            MfaDevice.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def get_mfa_device(db: AsyncSession, device_id: UUID, user_id: UUID) -> MfaDevice | None:
    result = await db.execute(
        select(MfaDevice).where(MfaDevice.id == device_id, MfaDevice.user_id == user_id, MfaDevice.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def list_trusted_devices(db: AsyncSession, user_id: UUID, org_id: UUID) -> list[TrustedDevice]:
    result = await db.execute(
        select(TrustedDevice).where(
            TrustedDevice.user_id == user_id, TrustedDevice.organization_id == org_id,
            TrustedDevice.is_revoked == False,  # noqa: E712
            TrustedDevice.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def list_policies(
    db: AsyncSession, org_id: UUID, *, category: str | None, is_active: bool | None
) -> list[PolicyDefinition]:
    q = select(PolicyDefinition).where(
        PolicyDefinition.organization_id == org_id, PolicyDefinition.deleted_at.is_(None)
    )
    if category:
        q = q.where(PolicyDefinition.category == category)
    if is_active is not None:
        q = q.where(PolicyDefinition.is_active == is_active)
    result = await db.execute(q.order_by(PolicyDefinition.priority.desc()))
    return list(result.scalars().all())


async def get_policy(db: AsyncSession, policy_id: UUID, org_id: UUID) -> PolicyDefinition | None:
    result = await db.execute(
        select(PolicyDefinition).where(
            PolicyDefinition.id == policy_id, PolicyDefinition.organization_id == org_id,
            PolicyDefinition.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_policy_assignments(db: AsyncSession, policy_id: UUID, org_id: UUID) -> list[PolicyAssignment]:
    result = await db.execute(
        select(PolicyAssignment).where(
            PolicyAssignment.policy_id == policy_id, PolicyAssignment.organization_id == org_id,
            PolicyAssignment.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def list_compliance_checks(
    db: AsyncSession, org_id: UUID, *, framework: str | None, status: str | None
) -> list[ComplianceCheck]:
    q = select(ComplianceCheck).where(
        ComplianceCheck.organization_id == org_id, ComplianceCheck.deleted_at.is_(None)
    )
    if framework:
        q = q.where(ComplianceCheck.framework == framework)
    if status:
        q = q.where(ComplianceCheck.status == status)
    result = await db.execute(q.order_by(ComplianceCheck.checked_at.desc()).limit(100))
    return list(result.scalars().all())


async def list_privacy_requests(
    db: AsyncSession, org_id: UUID, *, status: str | None, page: int, page_size: int
) -> tuple[list[PrivacyRequest], int]:
    q = select(PrivacyRequest).where(
        PrivacyRequest.organization_id == org_id, PrivacyRequest.deleted_at.is_(None)
    )
    if status:
        q = q.where(PrivacyRequest.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(PrivacyRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def list_consent(db: AsyncSession, org_id: UUID, subject_id: UUID | None) -> list[ConsentRecord]:
    q = select(ConsentRecord).where(ConsentRecord.organization_id == org_id, ConsentRecord.deleted_at.is_(None))
    if subject_id:
        q = q.where(ConsentRecord.subject_id == subject_id)
    result = await db.execute(q.order_by(ConsentRecord.created_at.desc()))
    return list(result.scalars().all())


async def list_vulnerabilities(
    db: AsyncSession, org_id: UUID | None, *, status: str | None, page: int, page_size: int
) -> tuple[list[VulnerabilityReport], int]:
    q = select(VulnerabilityReport).where(VulnerabilityReport.deleted_at.is_(None))
    if org_id:
        q = q.where(VulnerabilityReport.organization_id == org_id)
    if status:
        q = q.where(VulnerabilityReport.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(VulnerabilityReport.discovered_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def list_alerts(
    db: AsyncSession, org_id: UUID, *, status: str | None, page: int, page_size: int
) -> tuple[list[SecurityAlert], int]:
    q = select(SecurityAlert).where(
        SecurityAlert.organization_id == org_id, SecurityAlert.deleted_at.is_(None)
    )
    if status:
        q = q.where(SecurityAlert.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    result = await db.execute(q.order_by(SecurityAlert.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def get_alert(db: AsyncSession, alert_id: UUID, org_id: UUID) -> SecurityAlert | None:
    result = await db.execute(
        select(SecurityAlert).where(
            SecurityAlert.id == alert_id, SecurityAlert.organization_id == org_id,
            SecurityAlert.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def count_failed_logins(db: AsyncSession, org_id: UUID, user_id: UUID, since: datetime) -> int:
    result = await db.execute(
        select(func.count()).select_from(AuthenticationLog).where(
            AuthenticationLog.organization_id == org_id,
            AuthenticationLog.user_id == user_id,
            AuthenticationLog.success == False,  # noqa: E712
            AuthenticationLog.created_at >= since,
        )
    )
    return result.scalar_one() or 0
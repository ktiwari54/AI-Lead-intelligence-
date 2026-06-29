from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.deps import get_current_user, get_db
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.security import service
from backend.app.security.schemas import (
    AlertAcknowledgeRequest,
    ConsentCreateRequest,
    IncidentCloseRequest,
    IncidentCreateRequest,
    IncidentTimelineRequest,
    IncidentUpdateRequest,
    MfaDeviceCreateRequest,
    MfaVerifyRequest,
    PolicyAssignRequest,
    PolicyCreateRequest,
    PrivacyRequestCreate,
    SecuritySettingsUpdate,
)
from backend.app.users.models import User

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/health", response_model=APIResponse)
async def security_health():
    return APIResponse(data=service.security_health())


@router.get("/dashboard", response_model=APIResponse)
async def security_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.security_dashboard(db, current_user.organization_id))


@router.get("/settings", response_model=APIResponse)
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.get_settings(db, current_user.organization_id))


@router.patch("/settings", response_model=APIResponse)
async def update_security_settings(
    body: SecuritySettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.update_settings(
        db, current_user.organization_id, current_user, body.model_dump(exclude_unset=True)
    )
    return APIResponse(data=data)


@router.get("/events", response_model=PaginatedResponse)
async def list_security_events(
    severity: str | None = None,
    event_type: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_events(
        db, current_user.organization_id, severity=severity, event_type=event_type,
        page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/events/{event_id}", response_model=APIResponse)
async def get_security_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.get_event(db, event_id, current_user.organization_id))


@router.get("/incidents", response_model=PaginatedResponse)
async def list_incidents(
    status: str | None = None,
    severity: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_incidents(
        db, current_user.organization_id, status=status, severity=severity, page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.post("/incidents", response_model=APIResponse)
async def create_incident(
    body: IncidentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.create_incident(
        db, current_user.organization_id, current_user, body.model_dump()
    ))


@router.patch("/incidents/{incident_id}", response_model=APIResponse)
async def update_incident(
    incident_id: UUID,
    body: IncidentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.update_incident(
        db, incident_id, current_user.organization_id, current_user, body.model_dump(exclude_unset=True)
    ))


@router.post("/incidents/{incident_id}/timeline", response_model=APIResponse)
async def add_incident_timeline(
    incident_id: UUID,
    body: IncidentTimelineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.add_timeline(
        db, incident_id, current_user.organization_id, current_user, body.model_dump()
    ))


@router.post("/incidents/{incident_id}/close", response_model=APIResponse)
async def close_incident(
    incident_id: UUID,
    body: IncidentCloseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.close_incident(
        db, incident_id, current_user.organization_id, current_user, body.model_dump()
    ))


@router.get("/risk-scores/me", response_model=APIResponse)
async def my_risk_score(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await service.get_risk_score(
        db, current_user.organization_id, "user", current_user.id
    )
    return APIResponse(data=data)


@router.get("/risk-scores", response_model=APIResponse)
async def get_risk_score(
    subject_type: str = Query("user"),
    subject_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sid = subject_id or current_user.id
    data = await service.get_risk_score(db, current_user.organization_id, subject_type, sid)
    return APIResponse(data=data)


@router.get("/access-logs", response_model=PaginatedResponse)
async def list_access_logs(
    decision: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_access_logs(
        db, current_user.organization_id, decision=decision, page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/authentication-logs", response_model=PaginatedResponse)
async def list_authentication_logs(
    user_id: UUID | None = None,
    success: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_auth_logs(
        db, current_user.organization_id, user_id=user_id, success=success, page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/authorization-logs", response_model=PaginatedResponse)
async def list_authorization_logs(
    decision: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_authz_logs(
        db, current_user.organization_id, decision=decision, page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/mfa/devices", response_model=APIResponse)
async def list_mfa_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.list_mfa_devices(db, current_user))


@router.post("/mfa/devices", response_model=APIResponse)
async def create_mfa_device(
    body: MfaDeviceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.create_mfa_device(db, current_user, body.model_dump()))


@router.post("/mfa/verify", response_model=APIResponse)
async def verify_mfa(
    body: MfaVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.verify_mfa(db, current_user, UUID(body.device_id), body.code))


@router.delete("/mfa/devices/{device_id}", response_model=APIResponse)
async def delete_mfa_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.delete_mfa_device(db, current_user, device_id)
    return APIResponse(data={"deleted": True})


@router.get("/devices", response_model=APIResponse)
async def list_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.list_trusted_devices(db, current_user))


@router.get("/policies", response_model=APIResponse)
async def list_policies(
    category: str | None = None,
    is_active: bool | None = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.list_policies(
        db, current_user.organization_id, category=category, is_active=is_active
    ))


@router.post("/policies", response_model=APIResponse)
async def create_policy(
    body: PolicyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.create_policy(
        db, current_user.organization_id, current_user, body.model_dump()
    ))


@router.delete("/policies/{policy_id}", response_model=APIResponse)
async def deactivate_policy(
    policy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.deactivate_policy(db, policy_id, current_user.organization_id, current_user)
    return APIResponse(data={"deactivated": True})


@router.post("/policies/{policy_id}/assignments", response_model=APIResponse)
async def assign_policy(
    policy_id: UUID,
    body: PolicyAssignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.assign_policy(
        db, policy_id, current_user.organization_id, current_user, body.model_dump()
    ))


@router.get("/compliance/checks", response_model=APIResponse)
async def list_compliance_checks(
    framework: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.list_compliance_checks(
        db, current_user.organization_id, framework=framework, status=status
    ))


@router.post("/compliance/checks/run", response_model=APIResponse)
async def run_compliance_checks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.run_compliance_checks(db, current_user.organization_id, current_user))


@router.post("/privacy/requests", response_model=APIResponse)
async def create_privacy_request(
    body: PrivacyRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.create_privacy_request(
        db, current_user.organization_id, current_user, body.model_dump()
    ))


@router.get("/privacy/requests", response_model=PaginatedResponse)
async def list_privacy_requests(
    status: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_privacy_requests(
        db, current_user.organization_id, status=status, page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/consent", response_model=APIResponse)
async def list_consent_records(
    subject_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.list_consent(db, current_user.organization_id, subject_id))


@router.post("/consent", response_model=APIResponse)
async def record_consent(
    body: ConsentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.record_consent(
        db, current_user.organization_id, body.model_dump()
    ))


@router.get("/vulnerabilities", response_model=PaginatedResponse)
async def list_vulnerabilities(
    status: str | None = "open",
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_vulnerabilities(
        db, current_user.organization_id, status=status, page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.get("/alerts", response_model=PaginatedResponse)
async def list_security_alerts(
    status: str | None = "active",
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.list_alerts(
        db, current_user.organization_id, status=status, page=page, page_size=per_page,
    )
    pages = (total + per_page - 1) // per_page if total else 0
    return PaginatedResponse(data=items, total=total, page=page, per_page=per_page, pages=pages)


@router.post("/alerts/{alert_id}/acknowledge", response_model=APIResponse)
async def acknowledge_alert(
    alert_id: UUID,
    body: AlertAcknowledgeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return APIResponse(data=await service.acknowledge_alert(
        db, alert_id, current_user.organization_id, current_user
    ))
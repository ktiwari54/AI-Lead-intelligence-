"""Organization endpoints."""
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.common.dependencies import DbDep, UserDep
from app.common.schemas import SuccessResponse
from app.organizations.schemas import (
    InviteUserRequest,
    OrgResponse,
    OrgSettingUpdate,
    OrgUpdate,
    OrgUsageResponse,
)
from app.organizations.service import OrganizationService

router = APIRouter()


@router.get("/me", response_model=OrgResponse)
async def get_my_org(user: UserDep, db: DbDep) -> dict:
    """Get the current user's organization."""
    return await OrganizationService(db).get(user.org_id)


@router.patch("/me", response_model=OrgResponse)
async def update_my_org(req: OrgUpdate, user: UserDep, db: DbDep) -> dict:
    """Update organization details."""
    user.require_permission("settings:update")
    return await OrganizationService(db).update(user.org_id, req)


@router.get("/me/settings")
async def get_settings(user: UserDep, db: DbDep) -> list:
    """List organization settings."""
    return await OrganizationService(db).get_settings(user.org_id)


@router.put("/me/settings", response_model=SuccessResponse)
async def upsert_setting(req: OrgSettingUpdate, user: UserDep, db: DbDep) -> SuccessResponse:
    """Create or update an organization setting."""
    user.require_permission("settings:update")
    await OrganizationService(db).upsert_setting(user.org_id, req.key, req.value)
    return SuccessResponse(message="Setting updated")


@router.get("/me/usage", response_model=OrgUsageResponse | None)
async def get_usage(
    user: UserDep,
    db: DbDep,
    year: int = Query(default=datetime.now().year),
    month: int = Query(default=datetime.now().month),
) -> dict | None:
    """Get monthly usage statistics."""
    return await OrganizationService(db).get_usage(user.org_id, year, month)


@router.post("/me/invite", response_model=SuccessResponse, status_code=201)
async def invite_user(req: InviteUserRequest, user: UserDep, db: DbDep) -> SuccessResponse:
    """Invite a new member to the organization."""
    user.require_permission("users:create")
    await OrganizationService(db).invite_user(user.org_id, user.user_id, req)
    return SuccessResponse(message=f"Invitation sent to {req.email}")

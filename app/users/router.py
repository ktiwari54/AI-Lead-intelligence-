"""User management endpoints."""
from uuid import UUID

from fastapi import APIRouter, Query

from app.common.dependencies import DbDep, UserDep
from app.common.schemas import Page, SuccessResponse
from app.users.schemas import AssignRoleRequest, RoleResponse, UserResponse, UserUpdate
from app.users.service import UserService

router = APIRouter()


@router.get("", response_model=Page[UserResponse])
async def list_users(
    user: UserDep,
    db: DbDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = Query(default=None),
) -> Page:
    """List all users in the organization."""
    user.require_permission("users:read")
    from app.common.schemas import PageParams
    params = PageParams(page=page, page_size=page_size)
    items, total = await UserService(db).list_users(user.org_id, search=search, offset=params.offset, limit=page_size)
    return Page.create(items, total, params)


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(user: UserDep, db: DbDep) -> list:
    """List all available roles."""
    return await UserService(db).list_roles()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, user: UserDep, db: DbDep) -> dict:
    """Get a specific user by ID."""
    user.require_permission("users:read")
    return await UserService(db).get(user_id, user.org_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: UUID, req: UserUpdate, user: UserDep, db: DbDep) -> dict:
    """Update a user. Users can update themselves; admins can update any user."""
    if user_id != user.user_id:
        user.require_permission("users:update")
    return await UserService(db).update(user_id, user.org_id, req)


@router.delete("/{user_id}", response_model=SuccessResponse)
async def deactivate_user(user_id: UUID, user: UserDep, db: DbDep) -> SuccessResponse:
    """Deactivate a user."""
    user.require_permission("users:delete")
    await UserService(db).deactivate(user_id, user.org_id)
    return SuccessResponse(message="User deactivated")


@router.post("/{user_id}/roles", response_model=SuccessResponse)
async def assign_role(user_id: UUID, req: AssignRoleRequest, user: UserDep, db: DbDep) -> SuccessResponse:
    """Assign a role to a user."""
    user.require_permission("users:update")
    await UserService(db).assign_role(user_id, user.org_id, req.role_slug)
    return SuccessResponse(message=f"Role '{req.role_slug}' assigned")

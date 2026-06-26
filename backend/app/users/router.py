import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.users.schemas import UserCreate, UserUpdate, UserResponse
from backend.app.users.service import UserService
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_user_id, get_current_org_id

router = APIRouter()


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).get_by_id(user_id, org_id)
    return APIResponse(data=UserResponse.model_validate(user))


@router.patch("/me", response_model=APIResponse[UserResponse])
async def update_me(
    data: UserUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).update_user(user_id, org_id, data)
    return APIResponse(data=UserResponse.model_validate(user))


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    users, total = await UserService(db).list_users(org_id, pagination)
    return PaginatedResponse.create(
        data=[UserResponse.model_validate(u) for u in users],
        total=total, page=pagination.page, per_page=pagination.per_page,
    )


@router.post("/", response_model=APIResponse[UserResponse], status_code=201)
async def create_user(
    data: UserCreate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).create_user(org_id, data)
    return APIResponse(data=UserResponse.model_validate(user), message="User created")


@router.get("/{user_id}", response_model=APIResponse[UserResponse])
async def get_user(
    user_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).get_by_id(user_id, org_id)
    return APIResponse(data=UserResponse.model_validate(user))


@router.patch("/{user_id}", response_model=APIResponse[UserResponse])
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService(db).update_user(user_id, org_id, data)
    return APIResponse(data=UserResponse.model_validate(user))

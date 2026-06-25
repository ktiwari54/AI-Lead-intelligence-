import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.users.models import User
from backend.app.users.schemas import UserCreate, UserUpdate
from backend.app.common.security import hash_password
from backend.app.common.exceptions import NotFoundError, ConflictError
from backend.app.common.pagination import PaginationParams


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID, org_id: uuid.UUID) -> User:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.organization_id == org_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        return user

    async def list_users(self, org_id: uuid.UUID, pagination: PaginationParams) -> tuple[list[User], int]:
        base = select(User).where(User.organization_id == org_id, User.deleted_at.is_(None))
        count_result = await self.db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar()
        result = await self.db.execute(base.offset(pagination.offset).limit(pagination.per_page))
        return result.scalars().all(), total

    async def create_user(self, org_id: uuid.UUID, data: UserCreate) -> User:
        existing = await self.db.execute(
            select(User).where(User.email == data.email, User.organization_id == org_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Email already in use")
        user = User(
            organization_id=org_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=hash_password(data.password),
            timezone=data.timezone,
            language=data.language,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(self, user_id: uuid.UUID, org_id: uuid.UUID, data: UserUpdate) -> User:
        user = await self.get_by_id(user_id, org_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        return user

    async def deactivate_user(self, user_id: uuid.UUID, org_id: uuid.UUID) -> User:
        user = await self.get_by_id(user_id, org_id)
        user.status = "inactive"
        return user

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.identity import User
from app.core.security import hash_password, verify_password
from app.core.exceptions import UnauthorizedError
from app.users.schemas import UserUpdate, ChangePasswordRequest


async def update_user(user: User, data: UserUpdate) -> User:
    for k, v in data.model_dump(exclude_none=True, exclude_unset=True).items():
        setattr(user, k, v)
    return user


async def change_password(user: User, data: ChangePasswordRequest) -> User:
    if not verify_password(data.current_password, user.password_hash):
        raise UnauthorizedError("Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    return user

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.identity import User, Organization
from app.models.billing import Subscription
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import UnauthorizedError, ConflictError
from app.auth.schemas import LoginRequest, RegisterRequest


async def login(data: LoginRequest, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.email == data.email, User.is_deleted == False))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")
    if user.status != "active":
        raise UnauthorizedError("Account is not active")
    return {
        "access_token": create_access_token(str(user.id), {"org_id": str(user.organization_id)}),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
        "expires_in": 3600,
    }


async def register(data: RegisterRequest, db: AsyncSession) -> dict:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictError("Email already registered")

    org = Organization(
        name=data.organization_name,
        slug=data.organization_name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8],
    )
    db.add(org)
    await db.flush()

    sub = Subscription(organization_id=org.id, plan="trial", credits_included=500, credits_remaining=500)
    db.add(sub)

    user = User(
        organization_id=org.id,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password_hash=hash_password(data.password),
        status="active",
    )
    db.add(user)
    await db.flush()

    return {
        "access_token": create_access_token(str(user.id), {"org_id": str(org.id)}),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
        "expires_in": 3600,
    }

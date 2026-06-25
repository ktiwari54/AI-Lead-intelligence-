import uuid
from sqlalchemy import Column, String, ForeignKey, Integer, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.common.base_model import BaseModel


class Organization(BaseModel):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(20), default="trial", nullable=False)  # active, suspended, trial, cancelled
    subscription_plan = Column(String(50), default="free", nullable=False)
    credits = Column(Integer, default=100, nullable=False)
    settings = Column(JSONB, default={})
    logo_url = Column(String(500))
    website = Column(String(255))

    users = relationship("User", back_populates="organization")
    companies = relationship("Company", back_populates="organization")
    contacts = relationship("Contact", back_populates="organization")
    subscription = relationship("Subscription", back_populates="organization", uselist=False)


class User(BaseModel):
    __tablename__ = "users"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # active, inactive, pending, suspended
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    avatar_url = Column(String(500))
    last_login = Column(DateTime(timezone=True))
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    preferences = Column(JSONB, default={})

    organization = relationship("Organization", back_populates="users")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    api_keys = relationship("APIKey", back_populates="user")


class Role(BaseModel):
    __tablename__ = "roles"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_system = Column(Boolean, default=False)

    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")


class Permission(BaseModel):
    __tablename__ = "permissions"

    module = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(Text)

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")


class RolePermission(BaseModel):
    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)


class UserRole(BaseModel):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)


class APIKey(BaseModel):
    __tablename__ = "api_keys"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(10), nullable=False)
    scopes = Column(JSONB, default=[])
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="api_keys")

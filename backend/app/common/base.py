"""
SQLAlchemy declarative base with UUID v7 primary keys, timestamps, and soft delete.
"""
from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from backend.app.common.uuid7 import uuid7


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    Abstract base for all domain entities.

    Uses UUID v7 as primary key. UUID v7 is time-ordered, so sequential
    inserts produce adjacent B-tree leaf pages — dramatically better than
    UUID v4's random distribution which causes constant page splits.

    The server_default calls uuid_generate_v7() (defined in init_db.sql).
    The Python-side default (uuid7) is used when creating objects in code
    without going through the DB, e.g. in unit tests with SQLite.
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,                          # Python-side: generates UUID v7
        server_default=text("uuid_generate_v7()"),  # DB-side fallback
    )

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"

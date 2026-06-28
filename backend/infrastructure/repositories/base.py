from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.base import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class PageParams:
    page: int = 1
    page_size: int = 25

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class BaseRepository(Generic[T]):
    """Base SQLAlchemy repository with tenant scoping and soft-delete filtering."""

    model: type[T]

    def __init__(self, session: AsyncSession):
        self.session = session

    def _base_query(self, org_id: UUID) -> Select:
        return select(self.model).where(
            self.model.organization_id == org_id,
            self.model.deleted_at.is_(None),
        )

    async def get_by_id(self, entity_id: UUID, org_id: UUID) -> T | None:
        result = await self.session.execute(
            self._base_query(org_id).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def paginate(self, query: Select, page: PageParams) -> tuple[list[T], int]:
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()
        result = await self.session.execute(
            query.offset(page.offset).limit(page.page_size)
        )
        return list(result.scalars().all()), total

    async def soft_delete(self, entity: T) -> None:
        from datetime import datetime, timezone

        entity.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
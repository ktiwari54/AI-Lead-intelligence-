"""Shared Pydantic schemas."""
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime


class PageParams(BaseSchema):
    page: int = Field(default=1, ge=1, le=10000)
    page_size: int = Field(default=25, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseSchema, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        pages = max(1, -(-total // params.page_size))  # ceiling division
        return cls(items=items, total=total, page=params.page, page_size=params.page_size, pages=pages)


class SortParams(BaseSchema):
    sort_by: str = "created_at"
    sort_dir: str = Field(default="desc", pattern="^(asc|desc)$")


class ErrorDetail(BaseSchema):
    code: str
    message: str
    details: Any = None
    request_id: str | None = None


class ErrorResponse(BaseSchema):
    error: ErrorDetail


class SuccessResponse(BaseSchema):
    message: str = "Success"
    data: Any = None


class IDResponse(BaseSchema):
    id: UUID

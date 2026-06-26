from __future__ import annotations
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel


class ExportCreate(BaseModel):
    name: str
    format: Literal["CSV", "EXCEL", "JSON"] = "CSV"
    entity_type: Literal["companies", "contacts", "leads"] = "contacts"
    filters: dict = {}


class ExportResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    name: str
    format: str
    entity_type: str
    status: str
    filters: dict = {}
    file_path: str | None = None
    file_size_bytes: int | None = None
    row_count: int | None = None
    error_message: str | None = None
    expires_at: datetime | None = None
    created_at: datetime


class ImportJobCreate(BaseModel):
    name: str
    entity_type: Literal["companies", "contacts"]
    mapping: dict = {}


class ImportJobResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    name: str
    entity_type: str
    status: str
    total_rows: int | None = None
    processed_rows: int | None = None
    failed_rows: int | None = None
    mapping: dict = {}
    errors: list = []
    created_at: datetime

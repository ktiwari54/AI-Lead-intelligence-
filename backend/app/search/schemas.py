import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str | None = None
    filters: dict = Field(default_factory=dict)
    search_type: str = "standard"


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    query: str | None = None
    filters: dict = Field(default_factory=dict)
    search_type: str = "standard"
    is_shared: bool = False


class SearchResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    query: str | None
    filters: dict
    search_type: str
    status: str
    result_count: int
    execution_time_ms: int | None
    credits_used: int
    created_at: datetime

"""Search schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.common.schemas import BaseSchema, Page


class SearchRequest(BaseSchema):
    query: str | None = None
    search_type: str = Field(default="company", pattern="^(company|contact|all)$")
    filters: dict = Field(default_factory=dict)
    sort_by: str | None = None
    sort_dir: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    use_semantic: bool = False
    use_connectors: bool = False
    connector_ids: list[str] = Field(default_factory=list)


class NLSearchRequest(BaseSchema):
    """Natural-language search — query is free-form text."""
    query: str = Field(min_length=1, max_length=1000)
    search_type: str = Field(default="company", pattern="^(company|contact|all)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)


class ParsedSearchIntent(BaseSchema):
    raw_query: str
    search_type: str
    filters: dict
    keywords: list[str]
    explanation: str
    confidence: float


class SearchResultItem(BaseSchema):
    id: UUID
    entity_type: str
    name: str
    score: float
    highlights: dict = {}
    data: dict = {}


class SearchResponse(BaseSchema):
    items: list[SearchResultItem]
    total: int
    page: int
    page_size: int
    pages: int
    query_id: UUID | None = None
    execution_ms: int = 0
    cache_hit: bool = False
    explanation: str | None = None


class SavedSearchCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=200)
    search_type: str = "company"
    query: str | None = None
    filters: dict = Field(default_factory=dict)
    alert_enabled: bool = False
    alert_frequency: str | None = None
    is_shared: bool = False


class SavedSearchResponse(BaseSchema):
    id: UUID
    name: str
    search_type: str
    query: str | None = None
    filters: dict
    alert_enabled: bool
    is_shared: bool
    use_count: int
    created_at: datetime


class AutocompleteRequest(BaseSchema):
    q: str = Field(min_length=1, max_length=100)
    search_type: str = "company"
    limit: int = Field(default=10, ge=1, le=20)

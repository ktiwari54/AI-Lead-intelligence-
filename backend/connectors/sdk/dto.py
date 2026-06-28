from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import UUID


@dataclass
class FieldProvenance:
    field_name: str
    source: str
    source_type: str
    retrieved_at: datetime
    confidence: float = 1.0


@dataclass
class NormalizedAddressDTO:
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    country_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class NormalizedCompanyDTO:
    external_id: str | None = None
    name: str = ""
    legal_name: str | None = None
    domain: str | None = None
    website: str | None = None
    industry: str | None = None
    sub_industry: str | None = None
    employee_count: int | None = None
    employee_band: str | None = None
    annual_revenue: int | None = None
    revenue_band: str | None = None
    description: str | None = None
    founded_year: int | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    technologies: list[str] = field(default_factory=list)
    addresses: list[NormalizedAddressDTO] = field(default_factory=list)
    source: str = ""
    source_type: str = ""
    provenance: list[FieldProvenance] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedContactDTO:
    external_id: str | None = None
    first_name: str = ""
    last_name: str = ""
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    department: str | None = None
    seniority: str | None = None
    linkedin_url: str | None = None
    company_domain: str | None = None
    company_name: str | None = None
    email_verified: bool | None = None
    phone_verified: bool | None = None
    source: str = ""
    source_type: str = ""
    provenance: list[FieldProvenance] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorSearchRequest:
    query: str | None = None
    entity_type: Literal["company", "contact", "both"] = "both"
    filters: dict[str, Any] = field(default_factory=dict)
    page: int = 1
    page_size: int = 25
    org_id: UUID | None = None


@dataclass
class ConnectorRecordDTO:
    entity_type: Literal["company", "contact"]
    external_id: str | None
    company: NormalizedCompanyDTO | None = None
    contact: NormalizedContactDTO | None = None
    match_confidence: float = 0.0


@dataclass
class ConnectorSearchResult:
    success: bool
    records: list[ConnectorRecordDTO] = field(default_factory=list)
    total: int = 0
    errors: list[str] = field(default_factory=list)
    credits_used: int = 0
    source: str = ""
    latency_ms: int = 0
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitDTO:
    requests_remaining: int
    requests_limit: int
    reset_at: datetime | None = None
    burst_remaining: int | None = None


@dataclass
class ConnectorHealthDTO:
    healthy: bool
    latency_ms: int
    message: str = ""
    last_success_at: datetime | None = None
    error_rate_1h: float = 0.0
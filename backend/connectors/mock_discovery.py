"""Local-dev mock discovery connector — returns sample hits without API keys."""

from __future__ import annotations

import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.app.discovery.capabilities import ConnectorCapability, ConnectorCategory, DataSourceType
from backend.connectors.sdk.base import ConnectorSDKBase, RetryPolicy
from backend.connectors.sdk.dto import (
    ConnectorHealthDTO,
    ConnectorRecordDTO,
    ConnectorSearchRequest,
    ConnectorSearchResult,
    FieldProvenance,
    NormalizedAddressDTO,
    NormalizedCompanyDTO,
    NormalizedContactDTO,
    RateLimitDTO,
)
from backend.connectors.sdk.registry import SDKConnectorRegistry

_SAMPLE_COMPANIES: list[dict[str, Any]] = [
    {
        "name": "Austin SaaS Labs",
        "domain": "austinsaaslabs.com",
        "industry": "Software",
        "employee_count": 85,
        "description": "B2B SaaS platform for revenue operations teams.",
        "technologies": ["React", "PostgreSQL", "AWS"],
        "city": "Austin",
        "state": "TX",
    },
    {
        "name": "CloudForge Analytics",
        "domain": "cloudforge.io",
        "industry": "Software",
        "employee_count": 120,
        "description": "Cloud-native analytics for mid-market SaaS companies.",
        "technologies": ["Python", "Kubernetes", "Snowflake"],
        "city": "Austin",
        "state": "TX",
    },
    {
        "name": "DataPulse AI",
        "domain": "datapulse.ai",
        "industry": "Artificial Intelligence",
        "employee_count": 45,
        "description": "AI-powered lead scoring and enrichment for GTM teams.",
        "technologies": ["FastAPI", "OpenSearch", "Redis"],
        "city": "Austin",
        "state": "TX",
    },
]

_SAMPLE_CONTACTS: list[dict[str, Any]] = [
    {
        "first_name": "Jordan",
        "last_name": "Reeves",
        "email": "jordan.reeves@austinsaaslabs.com",
        "title": "VP Sales",
        "company_name": "Austin SaaS Labs",
        "company_domain": "austinsaaslabs.com",
    },
    {
        "first_name": "Morgan",
        "last_name": "Chen",
        "email": "morgan.chen@cloudforge.io",
        "title": "Head of Growth",
        "company_name": "CloudForge Analytics",
        "company_domain": "cloudforge.io",
    },
]


@SDKConnectorRegistry.register
class MockDiscoveryConnector(ConnectorSDKBase):
    """Returns deterministic sample companies/contacts for local development."""

    name = "mock_discovery"
    display_name = "Mock Discovery (Local Dev)"
    version = "1.0.0"
    category = ConnectorCategory.SEARCH_PROVIDER
    source_type = DataSourceType.PUBLIC_REGISTRY
    capabilities = frozenset({
        ConnectorCapability.SEARCH,
        ConnectorCapability.LOOKUP,
        ConnectorCapability.FETCH_DETAILS,
    })

    def authenticate(self) -> bool:
        self._authenticated = True
        return True

    def health_check(self) -> ConnectorHealthDTO:
        return ConnectorHealthDTO(
            healthy=True,
            latency_ms=1,
            message="mock connector ready",
            last_success_at=datetime.now(timezone.utc),
        )

    def search(self, request: ConnectorSearchRequest) -> ConnectorSearchResult:
        started = time.perf_counter()
        query = (request.query or "").lower()
        records: list[ConnectorRecordDTO] = []

        if request.entity_type in ("company", "both"):
            for item in _filter_companies(query):
                dto = self._company_dto(item)
                records.append(
                    ConnectorRecordDTO(
                        entity_type="company",
                        external_id=dto.external_id or "",
                        company=dto,
                        match_confidence=0.82,
                    )
                )

        if request.entity_type in ("contact", "both"):
            for item in _filter_contacts(query):
                dto = self._contact_dto(item)
                records.append(
                    ConnectorRecordDTO(
                        entity_type="contact",
                        external_id=dto.external_id or "",
                        contact=dto,
                        match_confidence=0.78,
                    )
                )

        return ConnectorSearchResult(
            success=True,
            records=records,
            total=len(records),
            source=self.name,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def lookup(self, identifier: str, identifier_type: str = "domain") -> ConnectorSearchResult:
        if identifier_type in ("email", "contact"):
            for item in _SAMPLE_CONTACTS:
                if item["email"] == identifier:
                    dto = self._contact_dto(item)
                    return ConnectorSearchResult(
                        success=True,
                        records=[ConnectorRecordDTO(entity_type="contact", external_id=dto.external_id or "", contact=dto)],
                        total=1,
                        source=self.name,
                    )
        else:
            for item in _SAMPLE_COMPANIES:
                if item["domain"] == identifier:
                    dto = self._company_dto(item)
                    return ConnectorSearchResult(
                        success=True,
                        records=[ConnectorRecordDTO(entity_type="company", external_id=dto.external_id or "", company=dto)],
                        total=1,
                        source=self.name,
                    )
        return ConnectorSearchResult(success=True, records=[], total=0, source=self.name)

    def fetch_details(self, external_id: str, entity_type: str = "company") -> ConnectorSearchResult:
        return self.lookup(external_id, identifier_type="domain" if entity_type == "company" else "email")

    def normalize(
        self,
        raw: dict[str, Any],
        entity_type: str = "company",
    ) -> NormalizedCompanyDTO | NormalizedContactDTO:
        if entity_type == "contact" or raw.get("email"):
            return self._contact_dto(raw)
        return self._company_dto(raw)

    def validate(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> list[str]:
        return []

    def transform(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> dict[str, Any]:
        if isinstance(dto, NormalizedCompanyDTO):
            return {"name": dto.name, "domain": dto.domain, "industry": dto.industry, "_type": "company"}
        return {"first_name": dto.first_name, "last_name": dto.last_name, "email": dto.email, "_type": "contact"}

    def map_to_domain_model(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> dict[str, Any]:
        base = self.transform(dto)
        base["_source"] = self.name
        base["_source_type"] = self.source_type.value
        return base

    def get_rate_limit(self) -> RateLimitDTO:
        return RateLimitDTO(requests_remaining=1_000_000, requests_limit=1_000_000)

    def retry_policy(self) -> RetryPolicy:
        return RetryPolicy(max_attempts=1)

    def _company_dto(self, raw: dict[str, Any]) -> NormalizedCompanyDTO:
        now = datetime.now(timezone.utc)
        domain = raw.get("domain", "")
        return NormalizedCompanyDTO(
            external_id=raw.get("external_id") or str(uuid.uuid5(uuid.NAMESPACE_DNS, domain)),
            name=raw.get("name", ""),
            domain=domain,
            industry=raw.get("industry"),
            employee_count=raw.get("employee_count"),
            description=raw.get("description"),
            technologies=raw.get("technologies", []),
            addresses=[
                NormalizedAddressDTO(
                    city=raw.get("city"),
                    state=raw.get("state"),
                    country="United States",
                    country_code="US",
                )
            ],
            source=self.name,
            source_type=self.source_type.value,
            provenance=[FieldProvenance("name", self.name, self.source_type.value, now)],
            raw=raw,
        )

    def _contact_dto(self, raw: dict[str, Any]) -> NormalizedContactDTO:
        now = datetime.now(timezone.utc)
        email = raw.get("email", "")
        return NormalizedContactDTO(
            external_id=raw.get("external_id") or str(uuid.uuid5(uuid.NAMESPACE_DNS, email)),
            first_name=raw.get("first_name", ""),
            last_name=raw.get("last_name", ""),
            email=email,
            title=raw.get("title"),
            company_name=raw.get("company_name"),
            company_domain=raw.get("company_domain"),
            source=self.name,
            source_type=self.source_type.value,
            provenance=[FieldProvenance("email", self.name, self.source_type.value, now)],
            raw=raw,
        )


_STOP_WORDS = frozenset({
    "and", "for", "the", "with", "from", "that", "this", "into", "about",
    "company", "companies", "contact", "contacts", "lead", "leads", "in", "at",
})


def _query_tokens(query: str) -> list[str]:
    return [
        t
        for t in re.split(r"\W+", query.lower())
        if len(t) > 2 and t not in _STOP_WORDS
    ]


def _filter_companies(query: str) -> list[dict[str, Any]]:
    if not query:
        return list(_SAMPLE_COMPANIES)
    tokens = _query_tokens(query)
    if not tokens:
        return list(_SAMPLE_COMPANIES)
    matches = []
    for company in _SAMPLE_COMPANIES:
        haystack = " ".join(
            str(company.get(k, "")) for k in ("name", "domain", "industry", "description", "city")
        ).lower()
        if all(token in haystack for token in tokens):
            matches.append(company)
    return matches or list(_SAMPLE_COMPANIES)


def _filter_contacts(query: str) -> list[dict[str, Any]]:
    if not query:
        return list(_SAMPLE_CONTACTS)
    tokens = _query_tokens(query)
    if not tokens:
        return list(_SAMPLE_CONTACTS)
    matches = []
    for contact in _SAMPLE_CONTACTS:
        haystack = " ".join(str(contact.get(k, "")) for k in contact).lower()
        if all(token in haystack for token in tokens):
            matches.append(contact)
    return matches
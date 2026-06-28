"""Apollo.io connector — Phase 5 SDK v2 reference implementation."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.app.discovery.capabilities import ConnectorCapability, ConnectorCategory, DataSourceType
from backend.connectors.sdk.base import ConnectorSDKBase, RetryPolicy
from backend.connectors.sdk.dto import (
    ConnectorHealthDTO,
    ConnectorRecordDTO,
    ConnectorSearchRequest,
    ConnectorSearchResult,
    FieldProvenance,
    NormalizedCompanyDTO,
    NormalizedContactDTO,
    RateLimitDTO,
)
from backend.connectors.sdk.registry import SDKConnectorRegistry


class ApolloRateLimitError(Exception):
    pass


class ApolloCreditsExhaustedError(Exception):
    pass


class ApolloValidationError(Exception):
    pass


@SDKConnectorRegistry.register
class ApolloConnectorV2(ConnectorSDKBase):
    """Apollo.io — licensed B2B search, lookup, and enrichment provider."""

    name = "apollo"
    display_name = "Apollo.io"
    version = "2.0.0"
    category = ConnectorCategory.ENRICHMENT
    source_type = DataSourceType.LICENSED_PROVIDER
    capabilities = frozenset({
        ConnectorCapability.SEARCH,
        ConnectorCapability.LOOKUP,
        ConnectorCapability.FETCH_DETAILS,
        ConnectorCapability.ENRICH,
    })

    BASE_URL = "https://api.apollo.io/v1"
    REQUESTS_PER_MINUTE = 50
    REQUESTS_PER_DAY = 10000

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.api_key: str = config.get("api_key", "")

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.BASE_URL,
            headers={"Content-Type": "application/json", "x-api-key": self.api_key},
            timeout=30.0,
        )

    def _handle_errors(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            raise ApolloRateLimitError("Apollo rate limit exceeded")
        if response.status_code == 402:
            raise ApolloCreditsExhaustedError("Apollo credits exhausted")
        if response.status_code == 422:
            raise ApolloValidationError(f"Apollo validation error: {response.json()}")
        response.raise_for_status()

    @retry(
        retry=retry_if_exception_type(ApolloRateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self._client() as client:
            response = client.post(path, json=payload)
        self._handle_errors(response)
        return response.json()

    def authenticate(self) -> bool:
        try:
            self._post("/auth/health", {"api_key": self.api_key})
            self._authenticated = True
            return True
        except Exception:
            self._authenticated = False
            return False

    def health_check(self) -> ConnectorHealthDTO:
        started = time.monotonic()
        try:
            data = self._post("/auth/health", {"api_key": self.api_key})
            credits = (data.get("credits") or {}).get("remaining")
            return ConnectorHealthDTO(
                healthy=True,
                latency_ms=int((time.monotonic() - started) * 1000),
                message="ok",
                last_success_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            return ConnectorHealthDTO(
                healthy=False,
                latency_ms=int((time.monotonic() - started) * 1000),
                message=str(exc),
            )

    def search(self, request: ConnectorSearchRequest) -> ConnectorSearchResult:
        self._ensure_authenticated()
        started = time.perf_counter()

        if request.entity_type == "company":
            path, key = "/organizations/search", "organizations"
            payload = self._build_org_payload(request)
        else:
            path, key = "/mixed_people/search", "people"
            payload = self._build_people_payload(request)

        try:
            raw = self._post(path, payload)
        except (ApolloCreditsExhaustedError, ApolloValidationError) as exc:
            return ConnectorSearchResult(success=False, errors=[str(exc)], source=self.name)
        except Exception as exc:
            return ConnectorSearchResult(success=False, errors=[str(exc)], source=self.name)

        records = self._records_from_raw(raw.get(key, []), request.entity_type)
        return ConnectorSearchResult(
            success=True,
            records=records,
            total=raw.get("pagination", {}).get("total_entries", len(records)),
            source=self.name,
            latency_ms=int((time.perf_counter() - started) * 1000),
            raw_response=raw,
        )

    def lookup(self, identifier: str, identifier_type: str = "domain") -> ConnectorSearchResult:
        self._ensure_authenticated()
        started = time.perf_counter()

        raw: dict[str, Any] = {}
        try:
            if identifier_type in ("email", "contact"):
                raw = self._post("/people/match", {"email": identifier, "reveal_personal_emails": True})
                person = raw.get("person")
                records = [self._contact_record(person)] if person else []
            else:
                raw = self._post("/organizations/enrich", {"domain": identifier})
                org = raw.get("organization", raw)
                records = [self._company_record(org)] if org else []
        except Exception as exc:
            return ConnectorSearchResult(success=False, errors=[str(exc)], source=self.name)

        return ConnectorSearchResult(
            success=True,
            records=records,
            total=len(records),
            source=self.name,
            latency_ms=int((time.perf_counter() - started) * 1000),
            raw_response=raw,
        )

    def fetch_details(self, external_id: str, entity_type: str = "company") -> ConnectorSearchResult:
        self._ensure_authenticated()
        if entity_type == "company":
            raw = self._post("/organizations/show", {"organization_id": external_id})
            org = raw.get("organization", raw)
            records = [self._company_record(org)] if org else []
        else:
            raw = self._post("/people/show", {"person_id": external_id})
            person = raw.get("person", raw)
            records = [self._contact_record(person)] if person else []

        return ConnectorSearchResult(
            success=True,
            records=records,
            total=len(records),
            source=self.name,
            raw_response=raw,
        )

    def normalize(
        self,
        raw: dict[str, Any],
        entity_type: str = "company",
    ) -> NormalizedCompanyDTO | NormalizedContactDTO:
        record_type = raw.get("type", entity_type)
        now = datetime.now(timezone.utc)
        prov = [FieldProvenance("source", self.name, self.source_type.value, now)]

        if record_type in ("organization", "company"):
            return NormalizedCompanyDTO(
                external_id=str(raw.get("id", "")),
                name=raw.get("name", ""),
                domain=raw.get("primary_domain") or raw.get("domain"),
                industry=raw.get("industry"),
                employee_count=raw.get("estimated_num_employees"),
                annual_revenue=raw.get("annual_revenue"),
                description=raw.get("short_description"),
                linkedin_url=raw.get("linkedin_url"),
                technologies=[
                    t.get("name") for t in (raw.get("technologies") or []) if t.get("name")
                ],
                source=self.name,
                source_type=self.source_type.value,
                provenance=prov,
                raw=raw,
            )

        org = raw.get("organization") or {}
        return NormalizedContactDTO(
            external_id=str(raw.get("id", "")),
            first_name=raw.get("first_name", ""),
            last_name=raw.get("last_name", ""),
            email=raw.get("email"),
            phone=raw.get("sanitized_phone") or raw.get("phone"),
            title=raw.get("title"),
            department=(raw.get("departments") or [None])[0],
            seniority=raw.get("seniority"),
            linkedin_url=raw.get("linkedin_url"),
            company_name=org.get("name") or raw.get("organization_name"),
            company_domain=org.get("primary_domain") or raw.get("organization_primary_domain"),
            source=self.name,
            source_type=self.source_type.value,
            provenance=prov,
            raw=raw,
        )

    def validate(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> list[str]:
        errors: list[str] = []
        if isinstance(dto, NormalizedCompanyDTO):
            if not dto.name:
                errors.append("company.name is required")
        elif isinstance(dto, NormalizedContactDTO):
            if not dto.first_name and not dto.email:
                errors.append("contact requires first_name or email")
        return errors

    def transform(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> dict[str, Any]:
        if isinstance(dto, NormalizedCompanyDTO):
            return {
                "name": dto.name,
                "domain": dto.domain,
                "industry": dto.industry,
                "employee_count": dto.employee_count,
                "technologies": dto.technologies,
                "_type": "company",
            }
        return {
            "first_name": dto.first_name,
            "last_name": dto.last_name,
            "email": dto.email,
            "title": dto.title,
            "company_domain": dto.company_domain,
            "_type": "contact",
        }

    def map_to_domain_model(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> dict[str, Any]:
        base = self.transform(dto)
        base["_source"] = self.name
        base["_source_type"] = self.source_type.value
        if dto.provenance:
            base["_provenance"] = [
                {"field": p.field_name, "source": p.source, "retrieved_at": p.retrieved_at.isoformat()}
                for p in dto.provenance
            ]
        return base

    def get_rate_limit(self) -> RateLimitDTO:
        return RateLimitDTO(
            requests_remaining=self.REQUESTS_PER_DAY,
            requests_limit=self.REQUESTS_PER_DAY,
        )

    def retry_policy(self) -> RetryPolicy:
        return RetryPolicy(max_attempts=4, retryable_status_codes=(429, 500, 502, 503, 504))

    def _build_people_payload(self, request: ConnectorSearchRequest) -> dict[str, Any]:
        payload: dict[str, Any] = dict(request.filters)
        if request.query:
            payload.setdefault("q_keywords", request.query)
        payload.setdefault("page", request.page)
        payload.setdefault("per_page", request.page_size)
        return payload

    def _build_org_payload(self, request: ConnectorSearchRequest) -> dict[str, Any]:
        payload: dict[str, Any] = dict(request.filters)
        if request.query:
            payload.setdefault("q_organization_name", request.query)
        payload.setdefault("page", request.page)
        payload.setdefault("per_page", request.page_size)
        return payload

    def _records_from_raw(
        self,
        items: list[dict[str, Any]],
        entity_type: str,
    ) -> list[ConnectorRecordDTO]:
        records: list[ConnectorRecordDTO] = []
        for item in items:
            if entity_type == "company":
                records.append(self._company_record(item))
            else:
                item = {**item, "type": "person"}
                records.append(self._contact_record(item))
        return records

    def _company_record(self, raw: dict[str, Any]) -> ConnectorRecordDTO:
        raw = {**raw, "type": "organization"}
        dto = self.normalize(raw, entity_type="company")
        assert isinstance(dto, NormalizedCompanyDTO)
        return ConnectorRecordDTO(
            entity_type="company",
            external_id=str(raw.get("id", "")),
            company=dto,
            match_confidence=0.8,
        )

    def _contact_record(self, raw: dict[str, Any]) -> ConnectorRecordDTO:
        raw = {**raw, "type": "person"}
        dto = self.normalize(raw, entity_type="contact")
        assert isinstance(dto, NormalizedContactDTO)
        return ConnectorRecordDTO(
            entity_type="contact",
            external_id=str(raw.get("id", "")),
            contact=dto,
            match_confidence=0.75,
        )
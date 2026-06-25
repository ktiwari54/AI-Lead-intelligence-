"""Apollo.io connector for people and company search/enrichment."""

import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.connectors.base import BaseConnector, ConnectorResult, RateLimitInfo
from backend.connectors.registry import ConnectorRegistry


class ApolloRateLimitError(Exception):
    pass


class ApolloCreditsExhaustedError(Exception):
    pass


class ApolloValidationError(Exception):
    pass


@ConnectorRegistry.register
class ApolloConnector(BaseConnector):
    """Apollo.io connector for people and company search/enrichment."""

    name = "apollo"
    display_name = "Apollo.io"
    version = "1.0.0"
    supports_search = True
    supports_lookup = True
    supports_enrich = True
    supported_operations = ["search_people", "search_companies", "enrich_person", "enrich_company"]

    BASE_URL = "https://api.apollo.io/v1"
    REQUESTS_PER_MINUTE = 50
    REQUESTS_PER_DAY = 10000

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key: str = config.get("api_key", "")
        self._credits_remaining: int | None = None

    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
            },
            timeout=30.0,
        )

    def _handle_response_errors(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            raise ApolloRateLimitError("Apollo rate limit exceeded")
        if response.status_code == 402:
            raise ApolloCreditsExhaustedError("Apollo credits exhausted")
        if response.status_code == 422:
            body = response.json()
            raise ApolloValidationError(f"Apollo validation error: {body}")
        response.raise_for_status()

    @retry(
        retry=retry_if_exception_type(ApolloRateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _post(self, path: str, payload: dict) -> dict:
        with self._get_client() as client:
            response = client.post(path, json=payload)
        self._handle_response_errors(response)
        return response.json()

    @retry(
        retry=retry_if_exception_type(ApolloRateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get(self, path: str, params: dict | None = None) -> dict:
        with self._get_client() as client:
            response = client.get(path, params=params or {})
        self._handle_response_errors(response)
        return response.json()

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """POST /auth/health — returns True if API key is valid."""
        try:
            data = self._post("/auth/health", {"api_key": self.api_key})
            self._authenticated = True
            return True
        except (ApolloCreditsExhaustedError, ApolloValidationError, httpx.HTTPStatusError):
            self._authenticated = False
            return False
        except Exception:
            self._authenticated = False
            return False

    def search(self, query: str | dict, filters: dict | None = None, **kwargs) -> ConnectorResult:
        """Search people via Apollo /mixed_people/search.

        `query` may be a plain search string or a dict with fields:
            person_titles, person_locations,
            organization_industry_tag_ids, page, per_page.
        `filters` (optional dict) is merged into the payload.
        """
        self._ensure_authenticated()

        if isinstance(query, str):
            payload: dict[str, Any] = {"q_keywords": query}
        else:
            payload = dict(query)

        if filters:
            payload.update(filters)

        payload.setdefault("page", 1)
        payload.setdefault("per_page", 25)

        try:
            data = self._post("/mixed_people/search", payload)
        except ApolloCreditsExhaustedError as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)
        except ApolloValidationError as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)
        except Exception as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

        people = data.get("people", [])
        normalized = [self.normalize({"type": "person", **p}) for p in people]
        return ConnectorResult(
            success=True,
            data=normalized,
            raw_response=data,
            source=self.name,
        )

    def lookup(self, identifier: str, identifier_type: str = "email", **kwargs) -> ConnectorResult:
        """POST /people/match — look up a person by email address."""
        self._ensure_authenticated()
        try:
            data = self._post("/people/match", {
                "email": identifier,
                "reveal_personal_emails": True,
            })
        except ApolloCreditsExhaustedError as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)
        except Exception as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

        person = data.get("person")
        if not person:
            return ConnectorResult(success=True, data=[], source=self.name)
        normalized = self.normalize({"type": "person", **person})
        return ConnectorResult(success=True, data=[normalized], raw_response=data, source=self.name)

    def enrich(self, data: dict, **kwargs) -> ConnectorResult:
        """Enrich a person (by email) or organisation (by domain)."""
        self._ensure_authenticated()
        try:
            if "domain" in data:
                raw = self._post("/organizations/enrich", {"domain": data["domain"]})
                org = raw.get("organization", raw)
                normalized = self.normalize({"type": "organization", **org})
                return ConnectorResult(
                    success=True, data=[normalized], raw_response=raw, source=self.name
                )
            if "email" in data:
                raw = self._post("/people/match", {
                    "email": data["email"],
                    "reveal_personal_emails": True,
                })
                person = raw.get("person", {})
                normalized = self.normalize({"type": "person", **person})
                return ConnectorResult(
                    success=True, data=[normalized], raw_response=raw, source=self.name
                )
            return ConnectorResult(
                success=False,
                errors=["enrich() requires 'email' or 'domain' in data"],
                source=self.name,
            )
        except (ApolloCreditsExhaustedError, ApolloValidationError, ApolloRateLimitError) as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)
        except Exception as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

    def normalize(self, raw: dict) -> dict:
        """Map Apollo API response fields to the platform's canonical schema."""
        record_type = raw.get("type", "person")

        if record_type == "organization":
            return {
                "name": raw.get("name"),
                "domain": raw.get("primary_domain") or raw.get("domain"),
                "industry": raw.get("industry"),
                "employee_count": raw.get("estimated_num_employees"),
                "annual_revenue": raw.get("annual_revenue_printed") or raw.get("annual_revenue"),
                "description": raw.get("short_description"),
                "technologies": [
                    t.get("name") for t in (raw.get("technologies") or []) if t.get("name")
                ],
                "linkedin_url": raw.get("linkedin_url"),
                "twitter_url": raw.get("twitter_url"),
                "_source": self.name,
                "_type": "company",
            }

        # Default: person
        org = raw.get("organization") or {}
        return {
            "first_name": raw.get("first_name"),
            "last_name": raw.get("last_name"),
            "email": raw.get("email"),
            "phone": raw.get("sanitized_phone") or raw.get("phone"),
            "designation": raw.get("title"),
            "department": raw.get("departments", [None])[0] if raw.get("departments") else None,
            "seniority": raw.get("seniority"),
            "linkedin_url": raw.get("linkedin_url"),
            "company_name": org.get("name") or raw.get("organization_name"),
            "company_domain": org.get("primary_domain") or raw.get("organization_primary_domain"),
            "_source": self.name,
            "_type": "person",
        }

    def health_check(self) -> dict:
        """Return health and credit status from Apollo."""
        start = time.monotonic()
        try:
            data = self._post("/auth/health", {"api_key": self.api_key})
            latency_ms = int((time.monotonic() - start) * 1000)
            credits_info = data.get("credits") or {}
            return {
                "healthy": True,
                "status": "ok",
                "latency_ms": latency_ms,
                "api_key_valid": True,
                "credits_remaining": credits_info.get("remaining"),
            }
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "healthy": False,
                "status": "error",
                "latency_ms": latency_ms,
                "api_key_valid": False,
                "error": str(exc),
            }

    def get_rate_limit(self) -> RateLimitInfo:
        """Return configured Apollo rate limits (static, no per-request quota endpoint)."""
        return RateLimitInfo(
            requests_remaining=self.REQUESTS_PER_DAY,
            requests_limit=self.REQUESTS_PER_DAY,
            reset_at=None,
        )

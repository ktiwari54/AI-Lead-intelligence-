"""Clearbit connector for company and person enrichment."""

import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
    wait_exponential,
)

from backend.connectors.base import BaseConnector, ConnectorResult, RateLimitInfo
from backend.connectors.registry import ConnectorRegistry


class ClearbitRateLimitError(Exception):
    pass


class ClearbitPendingError(Exception):
    """Raised when Clearbit returns 202 Accepted (async lookup in progress)."""
    pass


@ConnectorRegistry.register
class ClearbitConnector(BaseConnector):
    """Clearbit connector for company and person enrichment."""

    name = "clearbit"
    display_name = "Clearbit"
    version = "1.0.0"
    supports_search = True
    supports_lookup = True
    supports_enrich = True
    supported_operations = ["enrich_person", "enrich_company", "find_company", "reveal_company"]

    COMPANY_BASE_URL = "https://company.clearbit.com/v2"
    PERSON_BASE_URL = "https://person.clearbit.com/v2"
    AUTOCOMPLETE_URL = "https://autocomplete.clearbit.com/v1"
    REQUESTS_PER_MINUTE = 600

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key: str = config.get("api_key", "")

    def _get_company_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.COMPANY_BASE_URL,
            auth=(self.api_key, ""),
            timeout=30.0,
        )

    def _get_person_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.PERSON_BASE_URL,
            auth=(self.api_key, ""),
            timeout=30.0,
        )

    def _handle_response_errors(self, response: httpx.Response) -> None:
        if response.status_code == 202:
            raise ClearbitPendingError("Clearbit lookup is pending (202 Accepted)")
        if response.status_code == 429:
            raise ClearbitRateLimitError("Clearbit rate limit exceeded")
        response.raise_for_status()

    @retry(
        retry=retry_if_exception_type(ClearbitRateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get_company(self, path: str, params: dict | None = None) -> dict:
        with self._get_company_client() as client:
            response = client.get(path, params=params or {})
        self._handle_response_errors(response)
        return response.json()

    @retry(
        retry=retry_if_exception_type(ClearbitRateLimitError),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get_person(self, path: str, params: dict | None = None) -> dict:
        with self._get_person_client() as client:
            response = client.get(path, params=params or {})
        self._handle_response_errors(response)
        return response.json()

    def _get_with_202_poll(
        self,
        client_func,
        path: str,
        params: dict | None = None,
        max_poll: int = 3,
        poll_delay: float = 2.0,
    ) -> dict | None:
        """Call client_func; if 202 is returned, retry up to max_poll times.

        Returns None if still pending after all retries (partial-data scenario).
        """
        for attempt in range(max_poll):
            try:
                return client_func(path, params)
            except ClearbitPendingError:
                if attempt < max_poll - 1:
                    time.sleep(poll_delay)
        return None  # Still pending after retries

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """Test connectivity by fetching Clearbit's own company profile."""
        try:
            self._get_company("/companies/find", {"domain": "clearbit.com"})
            self._authenticated = True
            return True
        except (ClearbitPendingError, ClearbitRateLimitError):
            # 202 still counts as a valid auth response
            self._authenticated = True
            return True
        except Exception:
            self._authenticated = False
            return False

    def search(self, query: str | dict, filters: dict | None = None, **kwargs) -> ConnectorResult:
        """Company autocomplete via Clearbit Autocomplete API.

        `query` is a company name string (or dict with key `query`).
        """
        self._ensure_authenticated()

        search_term = query if isinstance(query, str) else query.get("query", "")

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.get(
                    f"{self.AUTOCOMPLETE_URL}/companies/suggest",
                    params={"query": search_term},
                )
            response.raise_for_status()
            suggestions: list[dict] = response.json()
        except Exception as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

        normalized = [
            {
                "name": s.get("name"),
                "domain": s.get("domain"),
                "logo_url": s.get("logo"),
                "_source": self.name,
                "_type": "company",
            }
            for s in suggestions
        ]
        return ConnectorResult(
            success=True, data=normalized, raw_response={"suggestions": suggestions}, source=self.name
        )

    def lookup(self, identifier: str, identifier_type: str = "domain", **kwargs) -> ConnectorResult:
        """Look up a company by domain."""
        self._ensure_authenticated()

        try:
            raw = self._get_with_202_poll(
                self._get_company,
                "/companies/find",
                {"domain": identifier},
            )
        except Exception as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

        if raw is None:
            # Still pending after polling
            return ConnectorResult(
                success=True,
                data=[],
                errors=["Clearbit lookup pending; try again shortly"],
                source=self.name,
            )

        normalized = self.normalize({"_type": "company", **raw})
        return ConnectorResult(success=True, data=[normalized], raw_response=raw, source=self.name)

    def enrich(self, data: dict, **kwargs) -> ConnectorResult:
        """Enrich a person (by email) or company (by domain).

        For a person email, uses the combined person+company endpoint.
        For a domain, fetches the company profile.

        Note on webhooks: Clearbit also supports a webhook callback pattern for
        async enrichment at scale. To use it, pass `webhook_url` in the config
        and handle the POST callback in your web framework. This connector does
        not implement webhook receiving — it uses the polling fallback instead.
        """
        self._ensure_authenticated()

        if "email" in data:
            try:
                raw = self._get_with_202_poll(
                    self._get_person,
                    "/combined/find",
                    {"email": data["email"]},
                )
            except Exception as exc:
                return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

            if raw is None:
                return ConnectorResult(
                    success=True,
                    data=[],
                    errors=["Clearbit person lookup pending; try again shortly"],
                    source=self.name,
                )

            person_raw = raw.get("person") or {}
            company_raw = raw.get("company") or {}
            result = {
                **self.normalize({"_type": "person", **person_raw}),
                "company": self.normalize({"_type": "company", **company_raw}),
            }
            return ConnectorResult(success=True, data=[result], raw_response=raw, source=self.name)

        if "domain" in data:
            return self.lookup(data["domain"], identifier_type="domain")

        return ConnectorResult(
            success=False,
            errors=["enrich() requires 'email' or 'domain' in data"],
            source=self.name,
        )

    def normalize(self, raw: dict) -> dict:
        """Map Clearbit API response fields to the platform's canonical schema."""
        record_type = raw.get("_type", "company")

        if record_type == "person":
            employment = raw.get("employment") or {}
            return {
                "first_name": raw.get("name", {}).get("givenName") if raw.get("name") else None,
                "last_name": raw.get("name", {}).get("familyName") if raw.get("name") else None,
                "email": raw.get("email"),
                "designation": employment.get("title"),
                "seniority": employment.get("seniority"),
                "department": employment.get("subRole") or employment.get("role"),
                "linkedin_url": (raw.get("linkedin") or {}).get("handle"),
                "twitter_url": (raw.get("twitter") or {}).get("handle"),
                "avatar_url": raw.get("avatar"),
                "bio": raw.get("bio"),
                "location": raw.get("location"),
                "_source": self.name,
                "_type": "person",
            }

        # Default: company
        category = raw.get("category") or {}
        geo = raw.get("geo") or {}
        metrics = raw.get("metrics") or {}
        tech = raw.get("tech") or []
        tags = raw.get("tags") or []

        return {
            "name": raw.get("name"),
            "domain": raw.get("domain"),
            "description": raw.get("description"),
            "founded_year": raw.get("foundedYear"),
            "employee_count": metrics.get("employees") or raw.get("metrics", {}).get("employeesRange"),
            "annual_revenue": metrics.get("annualRevenue"),
            "industry": category.get("industry"),
            "country": geo.get("country"),
            "city": geo.get("city"),
            "logo_url": raw.get("logo"),
            "linkedin_url": (raw.get("linkedin") or {}).get("handle"),
            "twitter_url": (raw.get("twitter") or {}).get("handle"),
            "crunchbase_url": (raw.get("crunchbase") or {}).get("handle"),
            "technologies": tech if isinstance(tech, list) else [],
            "tags": tags if isinstance(tags, list) else [],
            "_source": self.name,
            "_type": "company",
        }

    def health_check(self) -> dict:
        """Test API connectivity and return latency + auth status."""
        start = time.monotonic()
        try:
            self._get_company("/companies/find", {"domain": "clearbit.com"})
            latency_ms = int((time.monotonic() - start) * 1000)
            return {"healthy": True, "status": "ok", "latency_ms": latency_ms, "authenticated": True}
        except ClearbitPendingError:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {"healthy": True, "status": "ok", "latency_ms": latency_ms, "authenticated": True}
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "healthy": False,
                "status": "error",
                "latency_ms": latency_ms,
                "authenticated": False,
                "error": str(exc),
            }

    def get_rate_limit(self) -> RateLimitInfo:
        """Return Clearbit rate limits (static; no quota endpoint available)."""
        return RateLimitInfo(
            requests_remaining=self.REQUESTS_PER_MINUTE,
            requests_limit=self.REQUESTS_PER_MINUTE,
            reset_at=None,
        )

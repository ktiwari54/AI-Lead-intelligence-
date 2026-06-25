"""Hunter.io connector for email finding and verification."""

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


class HunterRateLimitError(Exception):
    pass


class HunterAccountLimitError(Exception):
    pass


class HunterDomainNotFoundError(Exception):
    pass


# Hunter error code mapping
_HUNTER_ERRORS: dict[int, type[Exception]] = {
    104: HunterDomainNotFoundError,
    105: HunterAccountLimitError,
}


@ConnectorRegistry.register
class HunterConnector(BaseConnector):
    """Hunter.io connector for email finding and verification."""

    name = "hunter"
    display_name = "Hunter.io"
    version = "1.0.0"
    supports_search = True
    supports_lookup = True
    supports_enrich = True
    supported_operations = ["find_email", "verify_email", "domain_search"]

    BASE_URL = "https://api.hunter.io/v2"
    REQUESTS_PER_SECOND = 10
    SEARCHES_PER_MONTH_FREE = 500

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key: str = config.get("api_key", "")
        self._account_info: dict = {}

    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.BASE_URL,
            timeout=30.0,
        )

    def _base_params(self) -> dict[str, str]:
        return {"api_key": self.api_key}

    def _handle_response_errors(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            raise HunterRateLimitError("Hunter.io rate limit exceeded")
        if response.status_code >= 400:
            try:
                body = response.json()
                errors = body.get("errors", [])
                if errors:
                    code = errors[0].get("code", 0)
                    details = errors[0].get("details", response.text)
                    exc_class = _HUNTER_ERRORS.get(code)
                    if exc_class:
                        raise exc_class(details)
            except (ValueError, KeyError):
                pass
            response.raise_for_status()

    @retry(
        retry=retry_if_exception_type(HunterRateLimitError),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get(self, path: str, params: dict | None = None) -> dict:
        merged = {**self._base_params(), **(params or {})}
        with self._get_client() as client:
            response = client.get(path, params=merged)
        self._handle_response_errors(response)
        return response.json()

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """GET /account — verify key is active and cache account info."""
        try:
            data = self._get("/account")
            account = data.get("data", {})
            if account.get("email"):
                self._account_info = account
                self._authenticated = True
                return True
            self._authenticated = False
            return False
        except Exception:
            self._authenticated = False
            return False

    def search(self, query: str | dict, filters: dict | None = None, **kwargs) -> ConnectorResult:
        """Domain search — returns email addresses found for a domain.

        `query` may be a domain string or a dict with keys:
            domain, company, limit, offset, type, seniority, department.
        """
        self._ensure_authenticated()

        if isinstance(query, str):
            params: dict[str, Any] = {"domain": query}
        else:
            params = dict(query)

        if filters:
            params.update(filters)

        params.setdefault("limit", 25)
        params.setdefault("offset", 0)

        try:
            data = self._get("/domain-search", params)
        except HunterDomainNotFoundError as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)
        except HunterAccountLimitError as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)
        except Exception as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

        payload = data.get("data", {})
        emails = payload.get("emails", [])
        domain = payload.get("domain", "")
        organization = payload.get("organization", "")

        normalized = [
            self.normalize({**e, "_domain": domain, "_organization": organization})
            for e in emails
        ]
        return ConnectorResult(
            success=True,
            data=normalized,
            raw_response=data,
            source=self.name,
        )

    def lookup(
        self,
        identifier: str,
        identifier_type: str = "email",
        **kwargs,
    ) -> ConnectorResult:
        """Find an email address using domain + name, or look up by email.

        For email-finder pass `domain`, `first_name`, `last_name` in kwargs.
        For direct email lookup pass identifier as the email.
        """
        self._ensure_authenticated()

        try:
            if identifier_type == "email" and "domain" not in kwargs:
                # Treat identifier as email to find; use email-verifier for basic lookup
                data = self._get("/email-finder", {"email": identifier})
            else:
                params: dict[str, Any] = {
                    "domain": kwargs.get("domain", ""),
                    "first_name": kwargs.get("first_name", ""),
                    "last_name": kwargs.get("last_name", ""),
                }
                data = self._get("/email-finder", params)
        except (HunterDomainNotFoundError, HunterAccountLimitError) as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)
        except Exception as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

        contact = data.get("data", {})
        if not contact or not contact.get("email"):
            return ConnectorResult(success=True, data=[], source=self.name)
        return ConnectorResult(
            success=True,
            data=[self.normalize(contact)],
            raw_response=data,
            source=self.name,
        )

    def enrich(self, data: dict, **kwargs) -> ConnectorResult:
        """Verify an email address and return deliverability metadata."""
        self._ensure_authenticated()

        email = data.get("email")
        if not email:
            return ConnectorResult(
                success=False,
                errors=["enrich() requires 'email' in data"],
                source=self.name,
            )

        try:
            raw = self._get("/email-verifier", {"email": email})
        except Exception as exc:
            return ConnectorResult(success=False, errors=[str(exc)], source=self.name)

        payload = raw.get("data", {})
        result = {
            "email": payload.get("email", email),
            "is_valid": payload.get("result") == "deliverable",
            "is_disposable": payload.get("disposable", False),
            "is_role_address": payload.get("webmail", False),
            "is_catch_all": payload.get("accept_all", False),
            "smtp_check": payload.get("smtp_server", False),
            "score": payload.get("score"),
            "_source": self.name,
        }
        return ConnectorResult(success=True, data=[result], raw_response=raw, source=self.name)

    def normalize(self, raw: dict) -> dict:
        """Map Hunter API response fields to the platform's canonical schema."""
        return {
            "email": raw.get("value") or raw.get("email"),
            "first_name": raw.get("first_name"),
            "last_name": raw.get("last_name"),
            "designation": raw.get("position"),
            "department": raw.get("department"),
            "seniority": raw.get("seniority"),
            "linkedin_url": raw.get("linkedin"),
            "twitter_url": raw.get("twitter"),
            "phone": raw.get("phone_number"),
            "confidence": raw.get("confidence"),
            "company_name": raw.get("_organization"),
            "company_domain": raw.get("_domain") or raw.get("domain"),
            "_source": self.name,
            "_type": "person",
        }

    def health_check(self) -> dict:
        """Return account / quota status from Hunter."""
        start = time.monotonic()
        try:
            data = self._get("/account")
            latency_ms = int((time.monotonic() - start) * 1000)
            account = data.get("data", {})
            requests_info = account.get("requests", {})
            searches = requests_info.get("searches", {})
            verifications = requests_info.get("verifications", {})
            return {
                "healthy": True,
                "status": "ok",
                "latency_ms": latency_ms,
                "plan": account.get("plan_name"),
                "searches_used": searches.get("used"),
                "searches_available": searches.get("available"),
                "verifications_used": verifications.get("used"),
                "verifications_available": verifications.get("available"),
            }
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "healthy": False,
                "status": "error",
                "latency_ms": latency_ms,
                "error": str(exc),
            }

    def get_rate_limit(self) -> RateLimitInfo:
        """Return Hunter rate limit info derived from cached account data."""
        searches = (
            self._account_info
            .get("requests", {})
            .get("searches", {})
        )
        available = searches.get("available", self.SEARCHES_PER_MONTH_FREE)
        limit = searches.get("available", self.SEARCHES_PER_MONTH_FREE) + searches.get("used", 0)
        return RateLimitInfo(
            requests_remaining=available,
            requests_limit=limit,
            reset_at=None,
        )

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorResult:
    success: bool
    data: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    raw_response: dict = field(default_factory=dict)
    credits_used: int = 0
    source: str = ""


@dataclass
class RateLimitInfo:
    requests_remaining: int
    requests_limit: int
    reset_at: str | None = None


class BaseConnector(ABC):
    """
    Every data source connector must implement this interface.
    """

    name: str = ""
    display_name: str = ""
    version: str = "1.0"
    supports_search: bool = True
    supports_lookup: bool = True
    supports_enrich: bool = True

    def __init__(self, config: dict):
        self.config = config
        self._authenticated = False

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the data source. Returns True on success."""
        ...

    @abstractmethod
    def search(self, query: str, filters: dict) -> ConnectorResult:
        """Search for companies or contacts matching the query and filters."""
        ...

    @abstractmethod
    def lookup(self, identifier: str, identifier_type: str = "email") -> ConnectorResult:
        """Look up a specific entity by a unique identifier."""
        ...

    @abstractmethod
    def enrich(self, data: dict) -> ConnectorResult:
        """Enrich existing data with additional fields from this source."""
        ...

    @abstractmethod
    def normalize(self, raw: dict) -> dict:
        """Normalize raw API response into the platform's canonical schema."""
        ...

    @abstractmethod
    def health_check(self) -> dict:
        """Return health status: {healthy: bool, latency_ms: int, ...}"""
        ...

    @abstractmethod
    def get_rate_limit(self) -> RateLimitInfo:
        """Return current rate limit status."""
        ...

    def parse_response(self, response: Any) -> dict:
        """Parse a raw HTTP response into a dictionary."""
        if hasattr(response, "json"):
            return response.json()
        if isinstance(response, str):
            import json
            return json.loads(response)
        return response

    def retry(self, func, *args, max_attempts: int = 3, backoff_base: float = 2.0, **kwargs):
        """Execute func with exponential backoff on failure."""
        import time
        last_exc = None
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exc = e
                if attempt < max_attempts - 1:
                    sleep_time = backoff_base ** attempt
                    time.sleep(sleep_time)
        raise last_exc

    def _ensure_authenticated(self):
        if not self._authenticated:
            self._authenticated = self.authenticate()
        if not self._authenticated:
            raise RuntimeError(f"Connector '{self.name}' failed to authenticate")

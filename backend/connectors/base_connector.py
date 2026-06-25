from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectorResult:
    def __init__(self, success: bool, data: Any = None, error: str = None, credits_used: int = 0):
        self.success = success
        self.data = data
        self.error = error
        self.credits_used = credits_used

    def __repr__(self):
        return f"ConnectorResult(success={self.success}, credits_used={self.credits_used})"


class BaseConnector(ABC):
    name: str = "base"
    version: str = "1.0.0"
    credits_per_call: int = 1

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._authenticated = False

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the provider and store session state."""

    @abstractmethod
    async def search(self, params: Dict) -> ConnectorResult:
        """Search for companies or contacts."""

    @abstractmethod
    async def lookup(self, identifier: str) -> ConnectorResult:
        """Look up a specific entity by domain, email, or ID."""

    @abstractmethod
    async def enrich(self, entity: Dict) -> ConnectorResult:
        """Enrich an existing entity with additional data."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify the connector is operational."""

    @abstractmethod
    def get_rate_limit(self) -> Dict:
        """Return rate limit metadata for this connector."""

    def normalize(self, raw_data: Dict) -> Dict:
        """Transform provider-specific response to platform schema."""
        return raw_data

    def parse_response(self, response: Any) -> Dict:
        return response

    async def retry(self, func, *args, max_retries: int = 3, backoff: float = 2.0, **kwargs) -> Any:
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                if attempt == max_retries - 1:
                    raise
                wait = backoff ** attempt
                logger.warning("%s retry %d/%d in %.1fs: %s", self.name, attempt + 1, max_retries, wait, exc)
                await asyncio.sleep(wait)

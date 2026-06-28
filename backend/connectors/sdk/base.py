from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from backend.app.discovery.capabilities import ConnectorCapability, ConnectorCategory, DataSourceType
from backend.connectors.sdk.dto import (
    ConnectorHealthDTO,
    ConnectorSearchRequest,
    ConnectorSearchResult,
    NormalizedCompanyDTO,
    NormalizedContactDTO,
    RateLimitDTO,
)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_base: float = 2.0
    max_backoff_seconds: float = 60.0
    retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504)


class ConnectorSDKBase(ABC):
    """
    Phase 5 Connector SDK — every provider implements this contract.
    Business logic never depends on provider-specific response shapes.
    """

    name: str = ""
    display_name: str = ""
    version: str = "2.0"
    category: ConnectorCategory = ConnectorCategory.ENRICHMENT
    source_type: DataSourceType = DataSourceType.LICENSED_PROVIDER
    capabilities: frozenset[ConnectorCapability] = frozenset()

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._authenticated = False

    @abstractmethod
    def authenticate(self) -> bool: ...

    @abstractmethod
    def health_check(self) -> ConnectorHealthDTO: ...

    @abstractmethod
    def search(self, request: ConnectorSearchRequest) -> ConnectorSearchResult: ...

    @abstractmethod
    def lookup(self, identifier: str, identifier_type: str = "domain") -> ConnectorSearchResult: ...

    @abstractmethod
    def fetch_details(self, external_id: str, entity_type: str = "company") -> ConnectorSearchResult: ...

    @abstractmethod
    def normalize(self, raw: dict[str, Any], entity_type: str = "company") -> NormalizedCompanyDTO | NormalizedContactDTO: ...

    @abstractmethod
    def validate(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> list[str]: ...

    @abstractmethod
    def transform(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> dict[str, Any]: ...

    @abstractmethod
    def map_to_domain_model(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> dict[str, Any]: ...

    @abstractmethod
    def get_rate_limit(self) -> RateLimitDTO: ...

    def retry_policy(self) -> RetryPolicy:
        return RetryPolicy()

    def disconnect(self) -> None:
        self._authenticated = False

    def supports(self, capability: ConnectorCapability) -> bool:
        return capability in self.capabilities

    def _ensure_authenticated(self) -> None:
        if not self._authenticated:
            self._authenticated = self.authenticate()
        if not self._authenticated:
            raise RuntimeError(f"Connector '{self.name}' failed to authenticate")
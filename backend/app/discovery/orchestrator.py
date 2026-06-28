from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from backend.app.discovery.pipelines.confidence import ConfidenceEngine
from backend.app.discovery.pipelines.enrichment import EnrichmentPipeline
from backend.app.discovery.pipelines.entity_resolution import EntityResolutionEngine
from backend.app.discovery.pipelines.normalization import NormalizationPipeline
from backend.app.discovery.schemas import DiscoveryRequest, DiscoveryResultHit, DiscoveryResultResponse
from backend.connectors.connector_config import connector_config_for, should_use_mock_connectors
from backend.connectors.registry import ConnectorRegistry
from backend.connectors.sdk.dto import (
    ConnectorRecordDTO,
    ConnectorSearchRequest,
    ConnectorSearchResult,
    NormalizedCompanyDTO,
    NormalizedContactDTO,
)
from backend.connectors.sdk.registry import SDKConnectorRegistry

StageCallback = Callable[[str, str], Awaitable[None] | None]


@dataclass
class ConnectorExecutionResult:
    connector_name: str
    success: bool
    result: ConnectorSearchResult | None = None
    error: str | None = None
    latency_ms: int = 0
    credits_used: int = 0


@dataclass
class OrchestratorContext:
    job_id: uuid.UUID
    org_id: uuid.UUID
    request: DiscoveryRequest
    connector_results: list[ConnectorExecutionResult] = field(default_factory=list)
    merged_hits: list[DiscoveryResultHit] = field(default_factory=list)
    stages: dict[str, str] = field(default_factory=dict)
    credits_used: int = 0


class DiscoveryOrchestrator:
    """
    Phase 5 Discovery Orchestrator — coordinates provider-agnostic discovery pipeline.
    """

    def __init__(
        self,
        registry: type[ConnectorRegistry] = ConnectorRegistry,
        normalization: NormalizationPipeline | None = None,
        entity_resolution: EntityResolutionEngine | None = None,
        confidence: ConfidenceEngine | None = None,
        enrichment: EnrichmentPipeline | None = None,
    ):
        self._registry = registry
        self._normalization = normalization or NormalizationPipeline()
        self._entity_resolution = entity_resolution or EntityResolutionEngine()
        self._confidence = confidence or ConfidenceEngine()
        self._enrichment = enrichment or EnrichmentPipeline(registry)

    async def execute(
        self,
        org_id: uuid.UUID,
        request: DiscoveryRequest,
        *,
        job_id: uuid.UUID | None = None,
        on_stage: StageCallback | None = None,
    ) -> DiscoveryResultResponse:
        job_id = job_id or uuid.uuid4()
        ctx = OrchestratorContext(job_id=job_id, org_id=org_id, request=request)
        started = time.perf_counter()

        await self._set_stage(ctx, on_stage, "connector_execution", "in_progress")
        connector_names = request.connectors or self._select_connectors(request)
        ctx.connector_results = await self._execute_parallel(org_id, request, connector_names)
        ctx.credits_used = sum(r.credits_used for r in ctx.connector_results)
        await self._set_stage(ctx, on_stage, "connector_execution", "completed")

        ctx.merged_hits, ctx.stages, extra_credits = await self._run_pipeline(ctx, on_stage)
        ctx.credits_used += extra_credits

        took_ms = int((time.perf_counter() - started) * 1000)
        return DiscoveryResultResponse(
            job_id=job_id,
            total=len(ctx.merged_hits),
            hits=ctx.merged_hits,
            took_ms=took_ms,
            connectors=[
                {
                    "name": r.connector_name,
                    "success": r.success,
                    "latency_ms": r.latency_ms,
                    "credits_used": r.credits_used,
                    "error": r.error,
                }
                for r in ctx.connector_results
            ],
        )

    async def _set_stage(
        self,
        ctx: OrchestratorContext,
        on_stage: StageCallback | None,
        stage: str,
        status: str,
    ) -> None:
        ctx.stages[stage] = status
        if on_stage:
            result = on_stage(stage, status)
            if asyncio.iscoroutine(result):
                await result

    def _select_connectors(self, request: DiscoveryRequest) -> list[str]:
        if should_use_mock_connectors():
            return ["mock_discovery"]

        sdk_names = [
            c["name"]
            for c in SDKConnectorRegistry.list_available()
            if "search" in c.get("capabilities", []) and c["name"] != "mock_discovery"
        ]
        configured = [name for name in sdk_names if connector_config_for(name)]
        if configured:
            return configured[:3]

        available = self._registry.list_available()
        names = [c["name"] for c in available if c.get("supports_search")]
        return names[:3] if names else ["mock_discovery"]

    async def _execute_parallel(
        self,
        org_id: uuid.UUID,
        request: DiscoveryRequest,
        connector_names: list[str],
    ) -> list[ConnectorExecutionResult]:
        if not connector_names:
            return []
        tasks = [self._execute_connector(name, org_id, request) for name in connector_names]
        return list(await asyncio.gather(*tasks))

    async def _execute_connector(
        self,
        name: str,
        org_id: uuid.UUID,
        request: DiscoveryRequest,
    ) -> ConnectorExecutionResult:
        started = time.perf_counter()
        search_req = ConnectorSearchRequest(
            query=request.query,
            entity_type=request.entity_type,  # type: ignore[arg-type]
            filters=request.filters,
            org_id=org_id,
        )

        config = connector_config_for(name)
        sdk = SDKConnectorRegistry.get(name, config)
        connector = sdk or self._registry.get(name, config)
        if not connector:
            return ConnectorExecutionResult(
                connector_name=name,
                success=False,
                error=f"Connector '{name}' not registered",
            )

        try:
            if sdk:
                result = await asyncio.to_thread(connector.search, search_req)
            else:
                result = await asyncio.to_thread(connector.search, search_req.query or "", search_req.filters)
            latency = int((time.perf_counter() - started) * 1000)
            adapted = self._adapt_legacy_result(result, name)
            return ConnectorExecutionResult(
                connector_name=name,
                success=adapted.success,
                result=adapted,
                latency_ms=latency,
                credits_used=getattr(result, "credits_used", 0) or adapted.credits_used,
            )
        except Exception as e:
            return ConnectorExecutionResult(
                connector_name=name,
                success=False,
                error=str(e),
                latency_ms=int((time.perf_counter() - started) * 1000),
            )

    def _adapt_legacy_result(self, result: Any, source: str) -> ConnectorSearchResult:
        if isinstance(result, ConnectorSearchResult):
            return result
        records = []
        for item in getattr(result, "data", []) or []:
            entity_type = item.get("_type", "company")
            if entity_type in ("person", "contact"):
                contact = NormalizedContactDTO(
                    external_id=str(item.get("id", "")),
                    first_name=item.get("first_name", ""),
                    last_name=item.get("last_name", ""),
                    email=item.get("email"),
                    phone=item.get("phone"),
                    title=item.get("designation") or item.get("title"),
                    department=item.get("department"),
                    seniority=item.get("seniority"),
                    linkedin_url=item.get("linkedin_url"),
                    company_name=item.get("company_name"),
                    company_domain=item.get("company_domain"),
                    source=source,
                    source_type="licensed_provider",
                )
                records.append(
                    ConnectorRecordDTO(
                        entity_type="contact",
                        external_id=contact.external_id,
                        contact=contact,
                        match_confidence=item.get("confidence", 0.5),
                    )
                )
            else:
                company = NormalizedCompanyDTO(
                    external_id=str(item.get("id", "")),
                    name=item.get("name", ""),
                    domain=item.get("domain"),
                    industry=item.get("industry"),
                    employee_count=item.get("employee_count"),
                    description=item.get("description"),
                    linkedin_url=item.get("linkedin_url"),
                    technologies=item.get("technologies", []),
                    source=source,
                    source_type="licensed_provider",
                )
                records.append(
                    ConnectorRecordDTO(
                        entity_type="company",
                        external_id=company.external_id,
                        company=company,
                        match_confidence=item.get("confidence", 0.5),
                    )
                )
        return ConnectorSearchResult(
            success=getattr(result, "success", True),
            records=records,
            total=len(records),
            source=source,
            credits_used=getattr(result, "credits_used", 0),
        )

    def _collect_records(self, results: list[ConnectorExecutionResult]) -> list[ConnectorRecordDTO]:
        records: list[ConnectorRecordDTO] = []
        for exec_result in results:
            if not exec_result.success or not exec_result.result:
                continue
            for record in exec_result.result.records:
                if record.company or record.contact:
                    records.append(record)
        return records

    async def _run_pipeline(
        self,
        ctx: OrchestratorContext,
        on_stage: StageCallback | None,
    ) -> tuple[list[DiscoveryResultHit], dict[str, str], int]:
        credits_used = 0
        raw_records = self._collect_records(ctx.connector_results)

        await self._set_stage(ctx, on_stage, "normalization", "in_progress")
        normalized, _ = self._normalization.process(raw_records)
        await self._set_stage(ctx, on_stage, "normalization", "completed")

        await self._set_stage(ctx, on_stage, "entity_resolution", "in_progress")
        resolved, _ = self._entity_resolution.resolve(normalized)
        await self._set_stage(ctx, on_stage, "entity_resolution", "completed")

        verification_map: dict[str, float] = {}
        if ctx.request.enrich:
            await self._set_stage(ctx, on_stage, "enrichment", "in_progress")
            resolved, enrich_stats = await self._enrichment.enrich(
                resolved,
                verify_contacts=ctx.request.verify_contacts,
                org_id=ctx.org_id,
            )
            credits_used += enrich_stats.credits_used
            for entity in resolved:
                if entity.record.contact and entity.record.contact.email_verified:
                    verification_map[str(entity.id)] = 0.95
            await self._set_stage(ctx, on_stage, "enrichment", "completed")
        else:
            await self._set_stage(ctx, on_stage, "enrichment", "skipped")

        await self._set_stage(ctx, on_stage, "confidence", "in_progress")
        hits = self._confidence.score_entities(resolved, verification_map=verification_map)
        await self._set_stage(ctx, on_stage, "confidence", "completed")

        return hits, ctx.stages, credits_used
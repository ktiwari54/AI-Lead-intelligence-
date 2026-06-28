from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from backend.app.discovery.pipelines.entity_resolution import ResolvedRecord
from backend.connectors.registry import ConnectorRegistry
from backend.connectors.sdk.dto import NormalizedCompanyDTO, NormalizedContactDTO


@dataclass
class EnrichmentStats:
    entities_in: int = 0
    fields_enriched: int = 0
    credits_used: int = 0
    providers_called: list[str] = field(default_factory=list)


ENRICHMENT_PLAN: dict[str, list[tuple[str, list[str]]]] = {
    "company": [
        ("industry", ["clearbit", "apollo"]),
        ("employee_count", ["clearbit", "apollo"]),
        ("description", ["clearbit"]),
        ("technologies", ["clearbit", "apollo"]),
    ],
    "contact": [
        ("email_verified", ["hunter"]),
        ("title", ["apollo"]),
    ],
}


class EnrichmentPipeline:
    """Augment resolved entities using enrichment-capable connectors."""

    def __init__(self, registry: type[ConnectorRegistry] = ConnectorRegistry):
        self._registry = registry

    async def enrich(
        self,
        entities: list[ResolvedRecord],
        *,
        verify_contacts: bool = False,
        org_id: Any = None,
    ) -> tuple[list[ResolvedRecord], EnrichmentStats]:
        stats = EnrichmentStats(entities_in=len(entities))
        enriched: list[ResolvedRecord] = []

        for entity in entities:
            record = entity.record
            if entity.entity_type == "company" and record.company:
                updated, fields, credits, providers = await self._enrich_company(record.company)
                record.company = updated
                stats.fields_enriched += fields
                stats.credits_used += credits
                stats.providers_called.extend(providers)
            elif entity.entity_type == "contact" and record.contact:
                updated, fields, credits, providers = await self._enrich_contact(
                    record.contact, verify=verify_contacts
                )
                record.contact = updated
                stats.fields_enriched += fields
                stats.credits_used += credits
                stats.providers_called.extend(providers)
            enriched.append(entity)

        stats.providers_called = list(dict.fromkeys(stats.providers_called))
        return enriched, stats

    async def _enrich_company(self, company: NormalizedCompanyDTO) -> tuple[NormalizedCompanyDTO, int, int, list[str]]:
        if not company.domain:
            return company, 0, 0, []

        fields_enriched = 0
        credits = 0
        providers: list[str] = []

        for provider_name in ("clearbit", "apollo"):
            connector = self._registry.get(provider_name, {})
            if not connector or not getattr(connector, "supports_enrich", False):
                continue
            try:
                result = await asyncio.to_thread(connector.enrich, {"domain": company.domain})
                if not result.success or not result.data:
                    continue
                providers.append(provider_name)
                credits += getattr(result, "credits_used", 1)
                patch = result.data[0]
                for key in ("industry", "employee_count", "description", "technologies", "name", "linkedin_url"):
                    if not getattr(company, key, None) and patch.get(key):
                        setattr(company, key, patch.get(key))
                        fields_enriched += 1
            except Exception:
                continue
            if fields_enriched >= 3:
                break

        return company, fields_enriched, credits, providers

    async def _enrich_contact(
        self,
        contact: NormalizedContactDTO,
        *,
        verify: bool,
    ) -> tuple[NormalizedContactDTO, int, int, list[str]]:
        fields_enriched = 0
        credits = 0
        providers: list[str] = []

        if verify and contact.email:
            hunter = self._registry.get("hunter", {})
            if hunter:
                try:
                    result = await asyncio.to_thread(hunter.enrich, {"email": contact.email})
                    if result.success and result.data:
                        providers.append("hunter")
                        credits += getattr(result, "credits_used", 1)
                        patch = result.data[0]
                        if patch.get("is_valid") or patch.get("result") == "deliverable":
                            contact.email_verified = True
                            fields_enriched += 1
                        elif "score" in patch:
                            contact.email_verified = (patch.get("score", 0) or 0) >= 70
                            fields_enriched += 1
                except Exception:
                    pass

        if contact.email and not contact.title:
            apollo = self._registry.get("apollo", {})
            if apollo:
                try:
                    result = await asyncio.to_thread(apollo.enrich, {"email": contact.email})
                    if result.success and result.data:
                        providers.append("apollo")
                        credits += getattr(result, "credits_used", 1)
                        patch = result.data[0]
                        if patch.get("designation") or patch.get("title"):
                            contact.title = patch.get("designation") or patch.get("title")
                            fields_enriched += 1
                except Exception:
                    pass

        return contact, fields_enriched, credits, providers
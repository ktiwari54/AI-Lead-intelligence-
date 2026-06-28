from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from backend.app.discovery.matchers import ExactMatcher, FuzzyMatcher
from backend.app.discovery.normalizers import DomainNormalizer, EmailNormalizer
from backend.connectors.sdk.dto import ConnectorRecordDTO, NormalizedCompanyDTO, NormalizedContactDTO


@dataclass
class ResolvedRecord:
    id: uuid.UUID
    entity_type: str
    record: ConnectorRecordDTO
    merged_from: list[str] = field(default_factory=list)
    resolution_confidence: float = 1.0
    merge_explanation: dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityResolutionStats:
    candidates_in: int = 0
    entities_out: int = 0
    merges: int = 0
    review_queued: int = 0


class EntityResolutionEngine:
    """Merge duplicate discovery records using exact and fuzzy matching."""

    COMPANY_FUZZY_THRESHOLD = 0.85
    CONTACT_EMAIL_THRESHOLD = 0.98

    def resolve(self, records: list[ConnectorRecordDTO]) -> tuple[list[ResolvedRecord], EntityResolutionStats]:
        stats = EntityResolutionStats(candidates_in=len(records))
        companies = [r for r in records if r.entity_type == "company"]
        contacts = [r for r in records if r.entity_type == "contact"]

        resolved: list[ResolvedRecord] = []
        resolved.extend(self._resolve_companies(companies, stats))
        resolved.extend(self._resolve_contacts(contacts, stats))
        stats.entities_out = len(resolved)
        return resolved, stats

    def _resolve_companies(
        self,
        records: list[ConnectorRecordDTO],
        stats: EntityResolutionStats,
    ) -> list[ResolvedRecord]:
        groups: list[list[ConnectorRecordDTO]] = []
        for record in records:
            placed = False
            for group in groups:
                if self._company_match(group[0], record) >= self.COMPANY_FUZZY_THRESHOLD:
                    group.append(record)
                    placed = True
                    break
            if not placed:
                groups.append([record])

        results: list[ResolvedRecord] = []
        for group in groups:
            golden = self._merge_company_group(group)
            if len(group) > 1:
                stats.merges += len(group) - 1
            results.append(
                ResolvedRecord(
                    id=uuid.uuid4(),
                    entity_type="company",
                    record=golden,
                    merged_from=[r.company.external_id or "" for r in group if r.company and r.company.external_id],
                    resolution_confidence=self._company_match(group[0], golden),
                    merge_explanation={
                        "strategy": "domain_exact_or_name_fuzzy",
                        "sources_merged": len(group),
                    },
                )
            )
        return results

    def _resolve_contacts(
        self,
        records: list[ConnectorRecordDTO],
        stats: EntityResolutionStats,
    ) -> list[ResolvedRecord]:
        groups: list[list[ConnectorRecordDTO]] = []
        for record in records:
            placed = False
            for group in groups:
                if self._contact_match(group[0], record) >= self.CONTACT_EMAIL_THRESHOLD:
                    group.append(record)
                    placed = True
                    break
            if not placed:
                groups.append([record])

        results: list[ResolvedRecord] = []
        for group in groups:
            golden = self._merge_contact_group(group)
            if len(group) > 1:
                stats.merges += len(group) - 1
            results.append(
                ResolvedRecord(
                    id=uuid.uuid4(),
                    entity_type="contact",
                    record=golden,
                    merged_from=[r.contact.external_id or "" for r in group if r.contact and r.contact.external_id],
                    resolution_confidence=0.95 if len(group) > 1 else 0.8,
                    merge_explanation={
                        "strategy": "email_exact_or_name_company_fuzzy",
                        "sources_merged": len(group),
                    },
                )
            )
        return results

    def _company_match(self, a: ConnectorRecordDTO, b: ConnectorRecordDTO) -> float:
        if not a.company or not b.company:
            return 0.0
        domain_score = ExactMatcher.score(
            DomainNormalizer.normalize(a.company.domain),
            DomainNormalizer.normalize(b.company.domain),
        )
        if domain_score == 1.0:
            return 1.0
        return FuzzyMatcher.score(a.company.name, b.company.name)

    def _contact_match(self, a: ConnectorRecordDTO, b: ConnectorRecordDTO) -> float:
        if not a.contact or not b.contact:
            return 0.0
        email_score = ExactMatcher.score(
            EmailNormalizer.normalize(a.contact.email),
            EmailNormalizer.normalize(b.contact.email),
        )
        if email_score >= self.CONTACT_EMAIL_THRESHOLD:
            return email_score
        name_a = f"{a.contact.first_name} {a.contact.last_name}".strip()
        name_b = f"{b.contact.first_name} {b.contact.last_name}".strip()
        name_score = FuzzyMatcher.score(name_a, name_b)
        domain_score = ExactMatcher.score(a.contact.company_domain, b.contact.company_domain)
        if name_score >= 0.9 and domain_score == 1.0:
            return 0.9
        return max(email_score, name_score * 0.5)

    def _merge_company_group(self, group: list[ConnectorRecordDTO]) -> ConnectorRecordDTO:
        base = group[0]
        if not base.company:
            return base
        merged = NormalizedCompanyDTO(**{k: v for k, v in base.company.__dict__.items()})
        for other in group[1:]:
            if not other.company:
                continue
            for field_name in (
                "legal_name", "domain", "website", "industry", "employee_count",
                "annual_revenue", "description", "phone", "linkedin_url",
            ):
                if not getattr(merged, field_name) and getattr(other.company, field_name):
                    setattr(merged, field_name, getattr(other.company, field_name))
            merged.technologies = list({*merged.technologies, *other.company.technologies})
            merged.provenance = [*merged.provenance, *other.company.provenance]
        best = max(group, key=lambda r: r.match_confidence)
        return ConnectorRecordDTO(
            entity_type="company",
            external_id=merged.external_id,
            company=merged,
            match_confidence=best.match_confidence,
        )

    def _merge_contact_group(self, group: list[ConnectorRecordDTO]) -> ConnectorRecordDTO:
        base = group[0]
        if not base.contact:
            return base
        merged = NormalizedContactDTO(**{k: v for k, v in base.contact.__dict__.items()})
        for other in group[1:]:
            if not other.contact:
                continue
            for field_name in (
                "email", "phone", "title", "department", "seniority",
                "linkedin_url", "company_name", "company_domain",
            ):
                if not getattr(merged, field_name) and getattr(other.contact, field_name):
                    setattr(merged, field_name, getattr(other.contact, field_name))
            merged.provenance = [*merged.provenance, *other.contact.provenance]
        best = max(group, key=lambda r: r.match_confidence)
        return ConnectorRecordDTO(
            entity_type="contact",
            external_id=merged.external_id,
            contact=merged,
            match_confidence=best.match_confidence,
        )
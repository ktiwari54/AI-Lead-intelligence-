from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from typing import Any

from backend.app.discovery.pipelines.entity_resolution import ResolvedRecord
from backend.app.discovery.schemas import ConfidenceExplanation, DiscoveryResultHit
from backend.app.discovery.capabilities import DataSourceType


SOURCE_TRUST_BASE: dict[str, float] = {
    DataSourceType.OFFICIAL_API.value: 0.95,
    DataSourceType.PUBLIC_REGISTRY.value: 0.95,
    DataSourceType.GOVERNMENT_OPEN_DATA.value: 0.95,
    DataSourceType.LICENSED_PROVIDER.value: 0.85,
    DataSourceType.USER_AUTHORIZED.value: 0.80,
    DataSourceType.USER_IMPORT.value: 0.60,
    DataSourceType.SEARCH_INDEX.value: 0.60,
}

WEIGHTS = {
    "source_trust": 0.25,
    "field_completeness": 0.15,
    "cross_source_validation": 0.20,
    "recency": 0.10,
    "verification_status": 0.15,
    "normalization_quality": 0.05,
    "duplicate_resolution": 0.10,
}


@dataclass
class ConfidenceInput:
    entity: ResolvedRecord
    field_completeness: float
    sources: list[str] = field(default_factory=list)
    verification_status: float = 0.5
    normalization_quality: float = 0.85


class ConfidenceEngine:
    """Compute explainable confidence scores for discovery hits."""

    def score_entities(
        self,
        entities: list[ResolvedRecord],
        *,
        field_completeness_map: dict[str, float] | None = None,
        verification_map: dict[str, float] | None = None,
    ) -> list[DiscoveryResultHit]:
        hits: list[DiscoveryResultHit] = []
        for entity in entities:
            record = entity.record
            data = self._record_to_data(record)
            key = str(entity.id)
            completeness = (field_completeness_map or {}).get(key, self._field_completeness(data))
            verification = (verification_map or {}).get(key, 0.5)

            source_type = ""
            if record.company:
                source_type = record.company.source_type or record.company.source
            elif record.contact:
                source_type = record.contact.source_type or record.contact.source

            explanation = self._build_explanation(
                ConfidenceInput(
                    entity=entity,
                    field_completeness=completeness,
                    sources=entity.merged_from or ([record.company.source if record.company else record.contact.source if record.contact else ""]),
                    verification_status=verification,
                ),
                source_type,
            )
            hits.append(
                DiscoveryResultHit(
                    id=entity.id,
                    entity_type=entity.entity_type,  # type: ignore[arg-type]
                    confidence=explanation.overall,
                    source_trust=explanation.source_trust,
                    field_completeness=explanation.field_completeness,
                    verification_status="verified" if verification >= 0.9 else ("unverified" if verification < 0.5 else "unknown"),
                    data=data,
                    provenance=self._extract_provenance(record),
                    explanation=explanation.model_dump(),
                )
            )
        return hits

    def _build_explanation(self, inp: ConfidenceInput, source_type: str) -> ConfidenceExplanation:
        source_trust = SOURCE_TRUST_BASE.get(source_type, 0.75)
        cross_source = 1.0 if len(inp.sources) > 1 and any(inp.sources) else 0.5
        recency = 0.85
        normalization_quality = inp.normalization_quality
        duplicate_resolution = inp.entity.resolution_confidence

        overall = (
            WEIGHTS["source_trust"] * source_trust
            + WEIGHTS["field_completeness"] * inp.field_completeness
            + WEIGHTS["cross_source_validation"] * cross_source
            + WEIGHTS["recency"] * recency
            + WEIGHTS["verification_status"] * inp.verification_status
            + WEIGHTS["normalization_quality"] * normalization_quality
            + WEIGHTS["duplicate_resolution"] * duplicate_resolution
        )

        factors: list[dict[str, Any]] = []
        if cross_source >= 0.9:
            factors.append({"field": "cross_source", "score": cross_source, "reason": "Multiple sources agree"})
        if inp.field_completeness >= 0.7:
            factors.append({"field": "completeness", "score": inp.field_completeness, "reason": "Strong field coverage"})
        if inp.verification_status >= 0.9:
            factors.append({"field": "verification", "score": inp.verification_status, "reason": "Contact data verified"})

        return ConfidenceExplanation(
            overall=round(min(0.99, overall), 4),
            source_trust=round(source_trust, 4),
            field_completeness=round(inp.field_completeness, 4),
            cross_source_validation=round(cross_source, 4),
            recency=round(recency, 4),
            verification_status=round(inp.verification_status, 4),
            normalization_quality=round(normalization_quality, 4),
            duplicate_resolution=round(duplicate_resolution, 4),
            factors=factors,
        )

    def _record_to_data(self, record: Any) -> dict[str, Any]:
        if record.company:
            return _to_jsonable({k: v for k, v in record.company.__dict__.items() if not k.startswith("_")})
        if record.contact:
            return _to_jsonable({k: v for k, v in record.contact.__dict__.items() if not k.startswith("_")})
        return {}

    def _field_completeness(self, data: dict[str, Any]) -> float:
        if not data:
            return 0.0
        populated = [k for k, v in data.items() if v not in (None, "", [], {}) and not k.startswith("_")]
        return min(1.0, len(populated) / 8)

    def _extract_provenance(self, record: Any) -> list[dict[str, Any]]:
        prov = []
        dto = record.company or record.contact
        if dto and getattr(dto, "provenance", None):
            for p in dto.provenance:
                prov.append({
                    "field": p.field_name,
                    "source": p.source,
                    "source_type": p.source_type,
                    "retrieved_at": p.retrieved_at.isoformat() if p.retrieved_at else None,
                })
        return prov


def _to_jsonable(value: Any) -> Any:
    """Recursively convert dataclasses and datetimes for JSONB persistence."""
    if is_dataclass(value):
        return {k: _to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    return value
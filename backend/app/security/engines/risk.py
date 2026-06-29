from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID


class RiskEngine:
    """Computes zero-trust risk scores from contextual signals."""

    def compute(
        self,
        *,
        subject_type: str,
        subject_id: UUID,
        signals: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        signals = signals or {}
        score = 0
        factors: list[dict[str, Any]] = []

        if signals.get("failed_logins_24h", 0) >= 3:
            score += 25
            factors.append({"factor": "failed_logins", "weight": 25, "value": signals["failed_logins_24h"]})

        if signals.get("new_device"):
            score += 15
            factors.append({"factor": "new_device", "weight": 15})

        if signals.get("impossible_travel"):
            score += 30
            factors.append({"factor": "impossible_travel", "weight": 30})

        if signals.get("no_mfa") and signals.get("privileged"):
            score += 20
            factors.append({"factor": "no_mfa_privileged", "weight": 20})

        if signals.get("api_abuse_score", 0) > 50:
            score += 20
            factors.append({"factor": "api_abuse", "weight": 20, "value": signals["api_abuse_score"]})

        score = min(score, 100)
        level = self._level(score)
        now = datetime.now(timezone.utc)

        return {
            "subject_type": subject_type,
            "subject_id": str(subject_id),
            "score": score,
            "level": level,
            "factors": factors,
            "computed_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }

    def _level(self, score: int) -> str:
        if score >= 75:
            return "critical"
        if score >= 50:
            return "high"
        if score >= 25:
            return "medium"
        return "low"
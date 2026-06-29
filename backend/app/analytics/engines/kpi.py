from __future__ import annotations

from typing import Any


class KPIEngine:
    """Evaluates KPIs with targets, thresholds, and period comparison."""

    def evaluate(
        self,
        metric_key: str,
        current_value: float,
        *,
        previous_value: float | None = None,
        target: float | None = None,
        warning_threshold: float | None = None,
        critical_threshold: float | None = None,
    ) -> dict[str, Any]:
        growth = None
        if previous_value is not None and previous_value != 0:
            growth = round((current_value - previous_value) / previous_value * 100, 2)

        status = "healthy"
        if critical_threshold is not None and current_value <= critical_threshold:
            status = "critical"
        elif warning_threshold is not None and current_value <= warning_threshold:
            status = "warning"
        elif target is not None and current_value < target * 0.8:
            status = "warning"

        progress = round(current_value / target * 100, 2) if target else None

        return {
            "metric_key": metric_key,
            "current_value": current_value,
            "previous_value": previous_value,
            "growth_rate": growth,
            "target": target,
            "progress_pct": progress,
            "status": status,
        }

    def build_executive_kpis(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        definitions = [
            ("total_companies", "Total Companies", None),
            ("total_contacts", "Total Contacts", None),
            ("verified_contacts", "Verified Contacts", None),
            ("pipeline_value", "Pipeline Value", None),
            ("active_users", "Active Users", None),
            ("discovery_jobs", "Discovery Jobs", None),
            ("avg_lead_score", "Avg Lead Score", 70.0),
            ("verification_rate", "Verification Rate %", 60.0),
        ]
        kpis = []
        for key, label, target in definitions:
            val = snapshot.get(key)
            if val is None:
                continue
            kpis.append({
                **self.evaluate(key, float(val), target=target),
                "label": label,
            })
        return kpis
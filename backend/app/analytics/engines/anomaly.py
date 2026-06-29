from __future__ import annotations

from statistics import mean, stdev
from typing import Any


class AnomalyEngine:
    """Statistical anomaly detection using z-score on time series."""

    def detect(
        self,
        series: list[dict[str, Any]],
        *,
        z_threshold: float = 2.5,
    ) -> list[dict[str, Any]]:
        if len(series) < 5:
            return []

        values = [float(p["value"]) for p in series]
        avg = mean(values)
        std = stdev(values) or 1.0
        anomalies = []

        for point in series:
            val = float(point["value"])
            z = abs(val - avg) / std
            if z >= z_threshold:
                anomalies.append({
                    "date": point["date"],
                    "value": val,
                    "z_score": round(z, 2),
                    "expected_range": [round(avg - z_threshold * std, 2), round(avg + z_threshold * std, 2)],
                    "severity": "critical" if z >= 3.5 else "warning",
                    "type": "spike" if val > avg else "drop",
                })
        return anomalies

    def scan_metrics(self, metrics: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        results = []
        for key, series in metrics.items():
            for anomaly in self.detect(series):
                results.append({"metric_key": key, **anomaly})
        return results
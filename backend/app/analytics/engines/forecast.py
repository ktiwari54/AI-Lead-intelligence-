from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


class ForecastEngine:
    """Simple linear forecasting for metrics (production: replace with ML models)."""

    def linear_forecast(
        self,
        series: list[dict[str, Any]],
        *,
        periods: int = 30,
    ) -> list[dict[str, Any]]:
        if len(series) < 2:
            return []

        values = [float(p["value"]) for p in series]
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        num = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        den = sum((i - x_mean) ** 2 for i in range(n)) or 1
        slope = num / den
        intercept = y_mean - slope * x_mean

        last_date = datetime.fromisoformat(series[-1]["date"]).replace(tzinfo=timezone.utc)
        forecasts = []
        for i in range(1, periods + 1):
            pred = intercept + slope * (n - 1 + i)
            fd = last_date + timedelta(days=i)
            forecasts.append({
                "date": fd.date().isoformat(),
                "predicted_value": round(max(0, pred), 2),
                "lower_bound": round(max(0, pred * 0.85), 2),
                "upper_bound": round(pred * 1.15, 2),
                "confidence": 0.75,
            })
        return forecasts

    def forecast_metric(
        self,
        metric_key: str,
        series: list[dict[str, Any]],
        *,
        periods: int = 30,
    ) -> dict[str, Any]:
        return {
            "metric_key": metric_key,
            "model_type": "linear",
            "historical_points": len(series),
            "forecasts": self.linear_forecast(series, periods=periods),
        }
"""Unit tests for Phase 9 Analytics BI Platform."""
from __future__ import annotations

import pytest

from backend.app.analytics.engines.anomaly import AnomalyEngine
from backend.app.analytics.engines.forecast import ForecastEngine
from backend.app.analytics.engines.insights import AIInsightEngine
from backend.app.analytics.engines.kpi import KPIEngine
from backend.app.analytics.constants import DashboardType, WidgetType, AlertSeverity


@pytest.fixture
def kpi_engine():
    return KPIEngine()


@pytest.fixture
def anomaly_engine():
    return AnomalyEngine()


@pytest.fixture
def forecast_engine():
    return ForecastEngine()


@pytest.fixture
def insight_engine():
    return AIInsightEngine()


SAMPLE_SERIES = [
    {"date": "2026-01-01", "value": 10},
    {"date": "2026-01-02", "value": 12},
    {"date": "2026-01-03", "value": 11},
    {"date": "2026-01-04", "value": 13},
    {"date": "2026-01-05", "value": 12},
    {"date": "2026-01-06", "value": 50},
]


def test_kpi_evaluate_growth(kpi_engine):
    result = kpi_engine.evaluate("contacts_created", 120, previous_value=100, target=150)
    assert result["growth_rate"] == 20.0
    assert result["status"] == "healthy"
    assert result["progress_pct"] == 80.0


def test_kpi_critical_threshold(kpi_engine):
    result = kpi_engine.evaluate(
        "verified_contacts", 30,
        warning_threshold=50, critical_threshold=20,
    )
    assert result["status"] == "warning"


def test_kpi_executive_kpis(kpi_engine):
    snapshot = {
        "total_companies": 100,
        "total_contacts": 500,
        "verified_contacts": 300,
        "pipeline_value": 50000,
        "active_users": 10,
        "discovery_jobs": 25,
    }
    kpis = kpi_engine.build_executive_kpis(snapshot)
    assert len(kpis) >= 5
    assert all("metric_key" in k for k in kpis)


def test_anomaly_detection(anomaly_engine):
    anomalies = anomaly_engine.detect(SAMPLE_SERIES, z_threshold=2.0)
    assert len(anomalies) >= 1
    assert anomalies[0]["type"] == "spike"


def test_anomaly_scan_metrics(anomaly_engine):
    stable = [{"date": f"2026-01-{i:02d}", "value": 10} for i in range(1, 10)]
    assert anomaly_engine.scan_metrics({"stable": stable}) == []

    spike_series = [{"date": f"2026-01-{i:02d}", "value": v} for i, v in enumerate([10] * 9 + [1000], 1)]
    results = anomaly_engine.scan_metrics({"revenue": spike_series})
    assert len(results) >= 1
    assert all(r["metric_key"] == "revenue" for r in results)


def test_forecast_linear(forecast_engine):
    series = [{"date": f"2026-01-{i:02d}", "value": 10 + i} for i in range(1, 15)]
    result = forecast_engine.forecast_metric("companies_created", series, periods=7)
    assert "forecasts" in result
    assert len(result["forecasts"]) == 7
    assert result["model_type"] == "linear"


def test_insight_summarize(insight_engine):
    snapshot = {
        "total_companies": 50,
        "total_contacts": 200,
        "pipeline_value": 100000,
        "avg_lead_score": 72,
        "verification_rate": 40,
    }
    kpis = [{"metric_key": "contacts", "label": "Contacts", "current_value": 200, "growth_rate": 15}]
    result = insight_engine.summarize_dashboard(snapshot, kpis)
    assert "summary" in result
    assert "recommendations" in result
    assert len(result["recommendations"]) >= 1


def test_insight_answer_question(insight_engine):
    snapshot = {"total_companies": 100, "total_contacts": 500, "pipeline_value": 250000}
    result = insight_engine.answer_question("How is my pipeline?", {"snapshot": snapshot})
    assert "answer" in result
    assert "pipeline" in result["answer"].lower() or "companies" in result["answer"].lower()


def test_dashboard_type_enum():
    assert DashboardType.EXECUTIVE.value == "executive"
    assert DashboardType.CUSTOM.value == "custom"


def test_widget_type_enum():
    assert WidgetType.KPI_CARD.value == "kpi_card"
    assert WidgetType.FUNNEL.value == "funnel"


def test_alert_severity_enum():
    assert AlertSeverity.CRITICAL.value == "critical"
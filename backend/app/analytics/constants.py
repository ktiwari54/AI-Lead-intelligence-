from __future__ import annotations

from enum import Enum


class DashboardType(str, Enum):
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    SALES = "sales"
    DISCOVERY = "discovery"
    AI = "ai"
    WORKFLOW = "workflow"
    PLATFORM = "platform"
    CUSTOM = "custom"


class WidgetType(str, Enum):
    KPI_CARD = "kpi_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    AREA_CHART = "area_chart"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    TABLE = "table"
    HEATMAP = "heatmap"
    GEO_MAP = "geo_map"
    SANKEY = "sankey"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class MetricGranularity(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


EXECUTIVE_KPIS = [
    "total_organizations",
    "active_users",
    "total_companies",
    "total_contacts",
    "verified_contacts",
    "discovery_jobs",
    "pipeline_value",
    "mrr",
    "arr",
    "monthly_growth",
    "churn_rate",
    "ai_usage",
    "platform_health",
]
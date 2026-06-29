from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.common.base import BaseModel


class Dashboard(BaseModel):
    __tablename__ = "dashboards"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    dashboard_type: Mapped[str] = mapped_column(String(30), server_default="custom", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    layout: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    version: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)

    __table_args__ = (
        Index("ix_dashboards_org_id", "organization_id"),
        Index("ix_dashboards_type", "dashboard_type"),
        UniqueConstraint("organization_id", "slug", name="uq_dashboard_org_slug"),
    )


class DashboardWidget(BaseModel):
    __tablename__ = "dashboard_widgets"

    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False
    )
    widget_key: Mapped[str] = mapped_column(String(100), nullable=False)
    widget_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    position: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    metric_key: Mapped[str | None] = mapped_column(String(100))
    query: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        Index("ix_dashboard_widgets_dashboard_id", "dashboard_id"),
        UniqueConstraint("dashboard_id", "widget_key", name="uq_dashboard_widget_key"),
    )


class Report(BaseModel):
    __tablename__ = "reports"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    definition: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    template_slug: Mapped[str | None] = mapped_column(String(100))
    is_scheduled: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    version: Mapped[int] = mapped_column(Integer, server_default="1", nullable=False)

    __table_args__ = (
        Index("ix_reports_org_id", "organization_id"),
        UniqueConstraint("organization_id", "slug", name="uq_report_org_slug"),
    )


class ReportSchedule(BaseModel):
    __tablename__ = "report_schedules"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), server_default="UTC", nullable=False)
    recipients: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    format: Mapped[str] = mapped_column(String(20), server_default="pdf", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_report_schedules_report_id", "report_id"),)


class MetricDefinition(BaseModel):
    __tablename__ = "metrics"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE")
    )
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), server_default="general", nullable=False)
    unit: Mapped[str | None] = mapped_column(String(30))
    formula: Mapped[dict | None] = mapped_column(JSONB)
    is_system: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    __table_args__ = (
        Index("ix_metrics_key", "metric_key"),
        Index("ix_metrics_category", "category"),
    )


class MetricAggregation(BaseModel):
    __tablename__ = "aggregations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    granularity: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    dimensions: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    __table_args__ = (
        Index("ix_aggregations_org_metric_period", "organization_id", "metric_key", "period_start"),
        UniqueConstraint("organization_id", "metric_key", "granularity", "period_start", name="uq_agg_period"),
    )


class KPIDefinition(BaseModel):
    __tablename__ = "kpis"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE")
    )
    kpi_key: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    target_value: Mapped[float | None] = mapped_column(Numeric(18, 4))
    warning_threshold: Mapped[float | None] = mapped_column(Numeric(18, 4))
    critical_threshold: Mapped[float | None] = mapped_column(Numeric(18, 4))
    comparison: Mapped[str] = mapped_column(String(20), server_default="previous_period", nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (Index("ix_kpis_key", "kpi_key"),)


class AnalyticsEvent(BaseModel):
    __tablename__ = "analytics_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payload: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    value: Mapped[float | None] = mapped_column(Numeric(18, 4))
    correlation_id: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        Index("ix_analytics_events_org_type", "organization_id", "event_type"),
        Index("ix_analytics_events_created_at", "created_at"),
    )


class ForecastModel(BaseModel):
    __tablename__ = "forecast_models"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(30), server_default="linear", nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    __table_args__ = (Index("ix_forecast_models_org_id", "organization_id"),)


class ForecastResult(BaseModel):
    __tablename__ = "forecast_results"

    model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forecast_models.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    forecast_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    lower_bound: Mapped[float | None] = mapped_column(Numeric(18, 4))
    upper_bound: Mapped[float | None] = mapped_column(Numeric(18, 4))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))

    __table_args__ = (Index("ix_forecast_results_model_date", "model_id", "forecast_date"),)


class AlertRule(BaseModel):
    __tablename__ = "alert_rules"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), server_default="warning", nullable=False)
    channels: Mapped[list] = mapped_column(JSONB, server_default=text("'[\"in_app\"]'::jsonb"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, server_default="60", nullable=False)

    __table_args__ = (Index("ix_alert_rules_org_id", "organization_id"),)


class Alert(BaseModel):
    __tablename__ = "alerts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    metric_key: Mapped[str | None] = mapped_column(String(100))
    current_value: Mapped[float | None] = mapped_column(Numeric(18, 4))
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    __table_args__ = (
        Index("ix_alerts_org_id", "organization_id"),
        Index("ix_alerts_severity", "severity"),
    )


class CohortDefinition(BaseModel):
    __tablename__ = "cohorts"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    definition: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    results: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (Index("ix_cohorts_org_id", "organization_id"),)


class FunnelDefinition(BaseModel):
    __tablename__ = "funnels"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    funnel_type: Mapped[str] = mapped_column(String(30), server_default="conversion", nullable=False)
    steps: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    results: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (Index("ix_funnels_org_id", "organization_id"),)


class WidgetLibraryItem(BaseModel):
    __tablename__ = "widget_library"

    widget_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), server_default="general", nullable=False)
    default_config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    __table_args__ = (Index("ix_widget_library_type", "widget_type"),)
# 12 — API Specification

**Version 4.0** | Phase 9 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication & Permissions](#2-authentication--permissions)
3. [Existing v3 Endpoints](#3-existing-v3-endpoints)
4. [v4 Dashboard Endpoints](#4-v4-dashboard-endpoints)
5. [Metrics Endpoints](#5-metrics-endpoints)
6. [Forecast Endpoints](#6-forecast-endpoints)
7. [Insights & NL Query](#7-insights--nl-query)
8. [Alert Endpoints](#8-alert-endpoints)
9. [Report Endpoints](#9-report-endpoints)
10. [Warehouse & Admin](#10-warehouse--admin)
11. [Error Codes](#11-error-codes)
12. [OpenAPI Tags](#12-openapi-tags)

---

## 1. Overview

All analytics endpoints are served under `/api/v1/analytics` via `backend/app/analytics/router.py`. v3 endpoints remain backward-compatible; v4 endpoints are gated by feature flag `analytics_platform_v4`.

**Base URL:** `http://localhost:8000/api/v1/analytics`  
**Content-Type:** `application/json`  
**Response envelope:** `APIResponse[T]` from `backend/app/common/response.py`

---

## 2. Authentication & Permissions

| Permission | Scope | Roles |
|------------|-------|-------|
| `analytics:read` | View dashboards, metrics, insights, alerts | member, manager, admin |
| `analytics:write` | Create reports, custom dashboards | manager, admin |
| `analytics:admin` | Alert rules, custom metrics, warehouse refresh, thresholds | admin |

All endpoints require `Authorization: Bearer <token>` and enforce `organization_id` from `get_current_user`.

---

## 3. Existing v3 Endpoints

Preserved from `backend/app/analytics/router.py` — no breaking changes.

### GET /dashboard

```http
GET /api/v1/analytics/dashboard
Authorization: Bearer {token}
```

**Response:** `APIResponse[DashboardStats]`

```json
{
  "data": {
    "total_companies": 423,
    "total_contacts": 1247,
    "total_searches": 3891,
    "ai_scores_generated": 982,
    "credits_remaining": 5800,
    "credits_monthly": 10000,
    "active_deals": 87,
    "new_companies_this_month": 56,
    "new_contacts_this_month": 142,
    "avg_lead_score": 58.2
  }
}
```

**Cache:** Redis, TTL 300s, key `analytics:{org_id}:dashboard`

### GET /lead-velocity

```http
GET /api/v1/analytics/lead-velocity?days=30
```

| Param | Type | Default | Range |
|-------|------|---------|-------|
| `days` | int | 30 | 7–365 |

**Response:** `APIResponse[LeadVelocityData]`

### GET /score-distribution

**Response:** `APIResponse[ScoreDistribution]`

### GET /industry

**Response:** `APIResponse[IndustryBreakdown]`

### GET /geography

**Response:** `APIResponse[GeographyBreakdown]`

### GET /seniority

**Response:** `APIResponse[SeniorityBreakdown]`

### GET /search-activity

```http
GET /api/v1/analytics/search-activity?days=30
```

**Response:** `APIResponse[SearchActivityData]`

### GET /crm-funnel

**Response:** `APIResponse[CRMFunnelData]`

### GET /credits

```http
GET /api/v1/analytics/credits?days=30
```

**Response:** `APIResponse[CreditUsageData]`

### GET /full

Aggregated bundle of all v3 endpoints.

**Response:** `APIResponse[FullAnalyticsResponse]`

**Cache:** Redis, TTL 300s

---

## 4. v4 Dashboard Endpoints

### GET /dashboards/executive

```http
GET /api/v1/analytics/dashboards/executive?period=quarter&compare=previous_period
```

| Param | Type | Values |
|-------|------|--------|
| `period` | string | `day`, `week`, `month`, `quarter`, `year` |
| `compare` | string | `previous_period`, `previous_year`, `none` |

**Response:**

```json
{
  "data": {
    "kpis": [
      {
        "key": "revenue.pipeline_value",
        "name": "Pipeline Value",
        "value": 2400000,
        "format": "currency",
        "comparison": { "change_percent": 12.0, "trend": "up" },
        "sparkline": [{"date": "2026-06-01", "value": 2100000}]
      }
    ],
    "scorecard": { "overall_health": "green", "kpis": [] },
    "panels": [
      {
        "panel_id": "pipeline_trend",
        "viz_type": "area_chart",
        "data": { "series": [] }
      }
    ],
    "insights": [],
    "generated_at": "2026-06-29T10:00:00Z"
  }
}
```

### GET /dashboards/operational

Same structure as executive, operational KPI set.

### GET /dashboards/workflows

Workflow analytics dashboard (Phase 8 integration).

```http
GET /api/v1/analytics/dashboards/workflows?from=2026-06-01&to=2026-06-29
```

### GET /dashboards/revenue

Revenue and pipeline dashboard with forecast overlay.

### GET /dashboards/{dashboard_id}

Custom dashboard by ID from `analytics.dashboard_configs`.

---

## 5. Metrics Endpoints

### GET /metrics

```http
GET /api/v1/analytics/metrics?keys=lead_velocity.contacts,score.avg&from=2026-06-01&to=2026-06-29&granularity=day
```

| Param | Type | Required |
|-------|------|----------|
| `keys` | string (comma-separated) | Yes |
| `from` | date (ISO 8601) | Yes |
| `to` | date | Yes |
| `granularity` | string | No (default: `day`) |
| `dimensions` | string (comma-separated) | No |
| `compare` | string | No |

**Response:**

```json
{
  "data": {
    "metrics": {
      "lead_velocity.contacts": {
        "key": "lead_velocity.contacts",
        "name": "Daily Contact Creation Rate",
        "series": [
          {"date": "2026-06-01", "value": 42},
          {"date": "2026-06-02", "value": 38}
        ],
        "metadata": {
          "source": "warehouse",
          "granularity": "day",
          "query_duration_ms": 45.2
        }
      }
    }
  }
}
```

### GET /metrics/{key}

Single metric with optional comparison.

### POST /metrics/custom

**Permission:** `analytics:admin`

```json
{
  "key": "custom.deals_per_rep",
  "name": "Deals per Sales Rep",
  "formula_yaml": "formula:\n  type: ratio\n  numerator: ...\n  denominator: ..."
}
```

### POST /metrics/custom/{key}/validate

Validates SQL without saving.

---

## 6. Forecast Endpoints

### GET /forecasts

```http
GET /api/v1/analytics/forecasts
```

Lists available forecasts for the tenant.

### GET /forecasts/{metric_key}

```http
GET /api/v1/analytics/forecasts/forecast.pipeline_value?horizon=30
```

### GET /forecasts/{metric_key}/series

Full series with confidence intervals.

### POST /forecasts/{metric_key}/refresh

**Permission:** `analytics:admin`  
Triggers on-demand forecast generation. Returns `202 Accepted`.

### POST /forecasts/scenarios

```json
{
  "metric_key": "forecast.revenue",
  "scenarios": [
    {"name": "conservative", "win_rate_adjustment": -0.05},
    {"name": "optimistic", "win_rate_adjustment": 0.05}
  ]
}
```

### GET /forecasts/{metric_key}/accuracy

Backtest accuracy metrics (MAPE, RMSE, coverage).

---

## 7. Insights & NL Query

### GET /insights

```http
GET /api/v1/analytics/insights?priority=high&limit=10
```

| Param | Type | Default |
|-------|------|---------|
| `priority` | string | all |
| `type` | string | all |
| `limit` | int | 20 |
| `include_dismissed` | bool | false |

### POST /insights/generate

Triggers on-demand insight generation. Costs 1 AI credit.

### POST /insights/{id}/dismiss

```json
{ "reason": "Already addressed" }
```

### POST /nl-query

```json
{
  "query": "Which industries had the most contacts last month?"
}
```

**Response:**

```json
{
  "data": {
    "parsed_query": {
      "metric_key": "lead_velocity.contacts",
      "dimensions": ["industry"],
      "time_range": {"from": "2026-05-01", "to": "2026-05-31"}
    },
    "results": {
      "breakdown": [
        {"label": "Technology", "value": 142, "percentage": 32.1},
        {"label": "Finance", "value": 89, "percentage": 20.1}
      ]
    },
    "summary": "Technology leads contact creation with 142 contacts (32.1%), followed by Finance with 89.",
    "visualization": "horizontal_bar",
    "credits_used": 1
  }
}
```

---

## 8. Alert Endpoints

### CRUD /alerts/rules

```
GET    /api/v1/analytics/alerts/rules
POST   /api/v1/analytics/alerts/rules
GET    /api/v1/analytics/alerts/rules/{id}
PUT    /api/v1/analytics/alerts/rules/{id}
DELETE /api/v1/analytics/alerts/rules/{id}
POST   /api/v1/analytics/alerts/rules/{id}/pause
POST   /api/v1/analytics/alerts/rules/{id}/resume
```

**Create example:**

```json
{
  "name": "Low Lead Score Alert",
  "type": "threshold",
  "metric_key": "score.avg",
  "condition": {
    "operator": "lt",
    "value": 40,
    "window": "1d",
    "consecutive": 3
  },
  "severity": "high",
  "channels": ["in_app", "email"],
  "recipients": ["user-uuid-1", "user-uuid-2"],
  "throttle_minutes": 60
}
```

### GET /alerts/events

```http
GET /api/v1/analytics/alerts/events?from=2026-06-01&severity=high
```

### POST /alerts/events/{id}/acknowledge

### GET /alerts/templates

### POST /alerts/templates/{id}/instantiate

---

## 9. Report Endpoints

```
GET    /api/v1/analytics/reports
POST   /api/v1/analytics/reports
GET    /api/v1/analytics/reports/{id}
PUT    /api/v1/analytics/reports/{id}
DELETE /api/v1/analytics/reports/{id}
POST   /api/v1/analytics/reports/{id}/run
GET    /api/v1/analytics/reports/{id}/executions
GET    /api/v1/analytics/reports/executions/{exec_id}
GET    /api/v1/analytics/reports/executions/{exec_id}/download
POST   /api/v1/analytics/reports/{id}/schedule
GET    /api/v1/analytics/reports/templates
POST   /api/v1/analytics/reports/templates/{id}/instantiate
```

### POST /reports/{id}/run

```json
{
  "format": "pdf",
  "filters_override": { "period": "last_7_days" }
}
```

**Response:** `202 Accepted`

```json
{
  "data": {
    "execution_id": "uuid",
    "status": "pending",
    "estimated_seconds": 15
  }
}
```

---

## 10. Warehouse & Admin

### POST /warehouse/refresh

**Permission:** `analytics:admin`

```json
{
  "scope": "incremental",
  "org_id": null
}
```

| Scope | Description |
|-------|-------------|
| `incremental` | Process changes since last watermark |
| `full` | Rebuild all facts for org (or all orgs) |
| `dimensions` | Refresh dimension tables only |
| `materialized_views` | Refresh MVs only |

### GET /warehouse/status

```json
{
  "data": {
    "pipelines": [
      {
        "name": "fact_lead_activity",
        "status": "idle",
        "last_success_at": "2026-06-29T09:45:00Z",
        "lag_seconds": 900,
        "rows_processed": 1523
      }
    ],
    "materialized_views": [
      {"name": "mv_kpi_daily", "last_refreshed": "2026-06-29T09:30:00Z"}
    ]
  }
}
```

### PUT /kpi-thresholds/{metric_key}

**Permission:** `analytics:admin`

### GET /kpi-thresholds

### POST /export/{format}

```http
POST /api/v1/analytics/export/csv
```

```json
{
  "dashboard_id": "executive",
  "period": "last_30_days",
  "panels": ["pipeline_trend", "lead_velocity"]
}
```

---

## 11. Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 400 | `INVALID_TIME_RANGE` | Date range exceeds 365 days or from > to |
| 400 | `INVALID_METRIC_KEY` | Unknown metric key |
| 400 | `INVALID_FORMULA` | Custom metric SQL validation failed |
| 403 | `ANALYTICS_PERMISSION_DENIED` | Missing required permission |
| 403 | `FEATURE_NOT_ENABLED` | `analytics_platform_v4` flag disabled |
| 404 | `DASHBOARD_NOT_FOUND` | Dashboard ID not found |
| 404 | `REPORT_NOT_FOUND` | Report ID not found |
| 409 | `REPORT_LIMIT_EXCEEDED` | Max saved reports for plan tier |
| 422 | `NL_QUERY_PARSE_FAILED` | Could not translate NL query |
| 429 | `RATE_LIMIT_EXCEEDED` | NL query or export rate limit |
| 503 | `WAREHOUSE_UNAVAILABLE` | ETL lag > 2 hours, stale data warning |

---

## 12. OpenAPI Tags

```python
# backend/app/analytics/router.py

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Sub-routers (v4)
dashboards_router = APIRouter(prefix="/dashboards", tags=["Analytics Dashboards"])
metrics_router = APIRouter(prefix="/metrics", tags=["Analytics Metrics"])
forecasts_router = APIRouter(prefix="/forecasts", tags=["Analytics Forecasts"])
insights_router = APIRouter(prefix="/insights", tags=["Analytics Insights"])
alerts_router = APIRouter(prefix="/alerts", tags=["Analytics Alerts"])
reports_router = APIRouter(prefix="/reports", tags=["Analytics Reports"])
warehouse_router = APIRouter(prefix="/warehouse", tags=["Analytics Warehouse"])
```

### Rate Limits

| Endpoint Group | Limit | Window |
|-------------|-------|--------|
| v3 dashboard endpoints | 60 req | 1 min |
| Metrics batch | 30 req | 1 min |
| NL query | 20 req | 1 hour |
| Report generation | 10 req | 1 hour |
| Warehouse refresh | 5 req | 1 hour |
| Export | 20 req | 1 hour |
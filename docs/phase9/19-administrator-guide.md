# 19 — Administrator Guide

**Version 4.0** | Phase 9 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Initial Setup](#2-initial-setup)
3. [Feature Flag Configuration](#3-feature-flag-configuration)
4. [Warehouse Management](#4-warehouse-management)
5. [KPI Threshold Management](#5-kpi-threshold-management)
6. [Alert Administration](#6-alert-administration)
7. [Custom Metrics](#7-custom-metrics)
8. [User & Permission Management](#8-user--permission-management)
9. [Monitoring & Health Checks](#9-monitoring--health-checks)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

This guide is for **Platform Administrators** and **Tenant Admins** who configure, manage, and maintain the analytics platform.

**Required permission:** `analytics:admin`  
**Related docs:** Phase 8 Administrator Guide (`docs/phase8/18-administrator-guide.md`)

---

## 2. Initial Setup

### 2.1 Enable Analytics Platform v4

```powershell
# 1. Run database migration
cd C:\path\to\AI-Lead-intelligence-
alembic upgrade head  # Applies 015_phase9_analytics_platform

# 2. Enable feature flag (global or per-org)
curl -X POST http://localhost:8000/api/v1/admin/feature-flags `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{ "key": "analytics_platform_v4", "is_enabled": true }'

# 3. Seed dimension tables (date dimension)
python -m scripts.seed.analytics_dimensions

# 4. Run initial ETL
curl -X POST http://localhost:8000/api/v1/analytics/warehouse/refresh `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  -d '{ "scope": "full" }'

# 5. Seed executive dashboard templates
python -m scripts.seed.executive_dashboards

# 6. Instantiate default alert templates
curl -X POST http://localhost:8000/api/v1/analytics/alerts/templates/seed-all `
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 2.2 Verify Setup

| Check | Command | Expected |
|-------|---------|----------|
| Schema exists | `\dn analytics` in psql | `analytics` schema listed |
| Date dimension populated | `SELECT COUNT(*) FROM analytics.dim_date` | ~5,800 rows |
| ETL watermarks set | `GET /analytics/warehouse/status` | All pipelines `idle` |
| Dashboard loads | `GET /analytics/dashboards/executive` | 200 with KPI data |
| Cache working | Check Redis keys `analytics:*` | Keys present after dashboard load |

---

## 3. Feature Flag Configuration

### 3.1 Available Flags

| Flag Key | Scope | Description |
|----------|-------|-------------|
| `analytics_platform_v4` | Global/Org | Enable v4 features (dashboards, reports, forecasts) |
| `analytics_nl_query` | Org | Enable natural language queries |
| `analytics_forecasting` | Org | Enable forecasting engine |
| `analytics_ai_insights` | Org | Enable AI insight generation |
| `analytics_benchmarks` | Org | Opt-in to cross-tenant benchmarks |
| `analytics_custom_metrics` | Org | Allow custom metric definitions |

### 3.2 Per-Organization Enable

```json
POST /api/v1/admin/feature-flags
{
  "key": "analytics_platform_v4",
  "is_enabled": true,
  "organization_id": "org-uuid"
}
```

### 3.3 Plan Tier Defaults

| Flag | Starter | Professional | Enterprise |
|------|---------|-------------|------------|
| `analytics_platform_v4` | ✅ | ✅ | ✅ |
| `analytics_nl_query` | ✅ (5/day) | ✅ (20/day) | ✅ (100/day) |
| `analytics_forecasting` | ❌ | ✅ | ✅ |
| `analytics_ai_insights` | ✅ (1/day) | ✅ (2/day) | ✅ (unlimited) |
| `analytics_benchmarks` | ❌ | ❌ | ✅ |
| `analytics_custom_metrics` | ❌ | ❌ | ✅ |

---

## 4. Warehouse Management

### 4.1 ETL Pipeline Status

```
GET /api/v1/analytics/warehouse/status
```

| Pipeline | Expected Frequency | Max Lag |
|----------|-------------------|---------|
| `fact_lead_activity` | 15 min | 30 min |
| `fact_deal_pipeline` | 15 min | 30 min |
| `fact_workflow_executions` | 15 min | 30 min |
| `fact_score_distribution` | 15 min | 30 min |
| `fact_credit_usage` | 15 min | 30 min |
| Dimension refresh | Daily 02:00 UTC | 26 hours |
| Materialized views | 30 min | 1 hour |

### 4.2 Manual Refresh

```powershell
# Incremental (recommended for routine)
curl -X POST http://localhost:8000/api/v1/analytics/warehouse/refresh `
  -d '{ "scope": "incremental" }'

# Full rebuild (after data issues)
curl -X POST http://localhost:8000/api/v1/analytics/warehouse/refresh `
  -d '{ "scope": "full", "org_id": "uuid" }'

# Dimensions only
curl -X POST http://localhost:8000/api/v1/analytics/warehouse/refresh `
  -d '{ "scope": "dimensions" }'

# Materialized views only
curl -X POST http://localhost:8000/api/v1/analytics/warehouse/refresh `
  -d '{ "scope": "materialized_views" }'
```

### 4.3 Celery Beat Schedule

```python
# backend/workers/celery_config.py
CELERYBEAT_SCHEDULE = {
    "analytics-etl-incremental": {
        "task": "analytics.etl_incremental",
        "schedule": crontab(minute="*/15"),
    },
    "analytics-refresh-mvs": {
        "task": "analytics.refresh_mvs",
        "schedule": crontab(minute="*/30"),
    },
    "analytics-refresh-dimensions": {
        "task": "analytics.refresh_dimensions",
        "schedule": crontab(hour=2, minute=0),
    },
    "analytics-generate-forecasts": {
        "task": "analytics.generate_forecasts",
        "schedule": crontab(hour=4, minute=0),
    },
    "analytics-generate-insights": {
        "task": "analytics.generate_insights",
        "schedule": crontab(hour=6, minute=0),
    },
    "analytics-evaluate-alerts": {
        "task": "analytics.evaluate_alerts",
        "schedule": crontab(minute="*/5"),
    },
}
```

### 4.4 Data Quality Monitoring

```sql
-- Check latest data quality results
SELECT check_name, status, expected_value, actual_value, run_at
FROM analytics.data_quality_checks
WHERE run_at > NOW() - INTERVAL '24 hours'
ORDER BY run_at DESC;
```

---

## 5. KPI Threshold Management

### 5.1 Setting Targets

```
PUT /api/v1/analytics/kpi-thresholds/{metric_key}
{
  "target_value": 55,
  "warning_below": 45,
  "critical_below": 35,
  "warning_above": null,
  "critical_above": null
}
```

### 5.2 Default Thresholds

Applied on org creation from plan tier templates (see doc 04):

```python
# scripts/seed/kpi_thresholds.py
PLAN_THRESHOLDS = {
    "professional": {
        "score.avg": {"target": 55, "warning_below": 45, "critical_below": 35},
        "workflow.success_rate": {"target": 95, "warning_below": 90, "critical_below": 85},
        "billing.burn_rate": {"target": 80, "warning_above": 90, "critical_above": 95},
    }
}
```

### 5.3 KPI Change Management

All KPI definition changes are logged in `analytics.kpi_change_log`. To modify a platform KPI:

1. Submit change request with business justification
2. Test in staging with 7-day parallel run
3. Update metric definition YAML
4. Deploy and invalidate all caches
5. Notify affected tenants via changelog

---

## 6. Alert Administration

### 6.1 Managing Alert Rules

```
# List all rules
GET /api/v1/analytics/alerts/rules

# Create from template
POST /api/v1/analytics/alerts/templates/low-lead-score/instantiate

# Pause during maintenance
POST /api/v1/analytics/alerts/rules/{id}/pause

# View recent events
GET /api/v1/analytics/alerts/events?from=2026-06-01&severity=high
```

### 6.2 Alert Tuning Guidelines

| Issue | Adjustment |
|-------|-----------|
| Too many alerts | Increase `throttle_minutes`, increase `consecutive` |
| Missing real issues | Decrease thresholds, decrease `consecutive` |
| Alert fatigue | Consolidate related rules into composite alerts |
| Wrong severity | Adjust severity mapping |

### 6.3 Notification Channel Setup

| Channel | Configuration |
|---------|--------------|
| In-app | Automatic (no config needed) |
| Email | Uses platform email service (SendGrid) |
| Webhook | `POST /api/v1/admin/integrations/webhooks` |
| Slack | `POST /api/v1/admin/integrations/slack` |

---

## 7. Custom Metrics

### 7.1 Creating Custom Metrics (Enterprise)

```
POST /api/v1/analytics/metrics/custom
{
  "key": "custom.deals_per_rep",
  "name": "Deals per Sales Rep",
  "description": "Average deals created per active sales rep per month",
  "formula_yaml": "formula:\n  type: ratio\n  numerator: |\n    SELECT COUNT(*) FROM crm.crm_deals\n    WHERE organization_id = :org_id AND created_at BETWEEN :from AND :to\n  denominator: |\n    SELECT COUNT(DISTINCT owner_id) FROM crm.crm_deals\n    WHERE organization_id = :org_id AND created_at BETWEEN :from AND :to"
}
```

### 7.2 Validation

Always validate before saving:

```
POST /api/v1/analytics/metrics/custom/custom.deals_per_rep/validate
```

### 7.3 Custom Metric Limits

| Constraint | Value |
|------------|-------|
| Max custom metrics per org | 20 (Enterprise) |
| Query timeout | 30s |
| Max rows | 100,000 |
| Allowed schemas | analytics, core, crm, ai, search, billing, audit |
| SELECT only | Enforced by sandbox |

---

## 8. User & Permission Management

### 8.1 Analytics Permission Assignment

| Role | Permissions | Use Case |
|------|------------|----------|
| Viewer | `analytics:read` | View dashboards only |
| Analyst | `analytics:read`, `analytics:write` | Create reports, custom dashboards |
| Admin | `analytics:read`, `analytics:write`, `analytics:admin` | Full analytics administration |

### 8.2 Assigning Permissions

```powershell
# Via admin API
curl -X PUT http://localhost:8000/api/v1/admin/users/{user_id}/role `
  -d '{ "role": "manager" }'  # manager includes analytics:read + analytics:write
```

### 8.3 Audit Review

```sql
-- Recent analytics admin actions
SELECT event_type, user_id, metadata, timestamp
FROM audit.audit_logs
WHERE event_type LIKE 'analytics.%'
  AND organization_id = :org_id
ORDER BY timestamp DESC
LIMIT 50;
```

---

## 9. Monitoring & Health Checks

### 9.1 Health Check Endpoints

| Endpoint | Check |
|----------|-------|
| `GET /api/v1/health` | API alive |
| `GET /analytics/warehouse/status` | ETL pipeline health |
| Grafana `/d/analytics` | Platform metrics |

### 9.2 Key Metrics to Monitor

| Metric | Alert Threshold | Grafana Panel |
|--------|----------------|---------------|
| `analytics_etl_lag_seconds` | > 3600 | ETL Lag |
| `analytics_query_duration_seconds` p95 | > 2s | Query Latency |
| Cache hit rate | < 70% | Cache Performance |
| `analytics` queue depth | > 100 | Worker Queue |
| Report generation failures | > 5/hour | Report Health |

### 9.3 Daily Admin Checklist

- [ ] Check ETL pipeline status (all `idle`, lag < 30 min)
- [ ] Review data quality checks (no failures)
- [ ] Check alert events (no unacknowledged critical)
- [ ] Verify cache hit rate > 80%
- [ ] Review slow query log
- [ ] Check Celery worker health
- [ ] Verify forecast generation completed

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue | Diagnosis | Resolution |
|-------|-----------|------------|
| Dashboard empty | ETL not run | `POST /warehouse/refresh { "scope": "full" }` |
| Stale data indicator | ETL lag > 1 hour | Check Celery worker, restart if needed |
| Forecast not available | Insufficient history | Need 30+ days of data |
| NL query fails | AI credits exhausted | Top up credits |
| Report generation timeout | Query too broad | Add filters, reduce date range |
| Custom metric error | SQL sandbox violation | Fix SQL, validate first |
| Alert not firing | Rule paused or throttled | Check rule status, clear throttle |
| High query latency | Cache miss + OLTP fallback | Refresh MVs, warm cache |

### 10.2 Log Locations

| Component | Log Path |
|-----------|----------|
| API server | `logs/api.log` |
| Analytics worker | `logs/celery-analytics.log` |
| ETL pipeline | Search for `analytics.etl` in worker logs |
| Slow queries | Search for `Slow analytics query` in API logs |
| Alert evaluation | Search for `analytics.evaluate_alerts` in worker logs |

### 10.3 Support Escalation

| Level | Criteria | Contact |
|-------|----------|---------|
| L1 | Dashboard not loading, stale data | Tenant admin (this guide) |
| L2 | ETL failure, data quality issues | Platform ops team |
| L3 | Schema migration, performance degradation | Engineering team |
| L4 | Data corruption, security incident | Engineering + Security team |
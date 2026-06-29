# 16 — Sample Executive Dashboards

**Version 4.0** | Phase 9 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [CRO Revenue Dashboard](#2-cro-revenue-dashboard)
3. [VP Sales Pipeline Dashboard](#3-vp-sales-pipeline-dashboard)
4. [CEO Platform Health Dashboard](#4-ceo-platform-health-dashboard)
5. [RevOps Efficiency Dashboard](#5-revops-efficiency-dashboard)
6. [JSON Configurations](#6-json-configurations)
7. [Sample API Responses](#7-sample-api-responses)

---

## 1. Overview

This document provides **ready-to-deploy executive dashboard configurations** with sample data, panel layouts, and API response payloads. Use these as seed templates in `analytics.dashboard_configs` and frontend development references.

---

## 2. CRO Revenue Dashboard

### 2.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Revenue Overview — Q2 2026          [Compare: Q1 2026 ▼]          │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────┤
│ Pipeline │ Weighted │ Win Rate │ Avg Deal │ Revenue  │ Forecast     │
│ $4.2M ↑  │ $2.8M ↑  │ 24% →    │ $18.2K ↑ │ $1.1M ↑  │ $1.4M (90d)  │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────────┤
│  Pipeline by Stage (funnel)                                          │
├──────────────────────────────┬──────────────────────────────────────┤
│  Revenue Trend (area, 12mo)  │  Win/Loss Ratio (donut)              │
├──────────────────────────────┼──────────────────────────────────────┤
│  Top Deals (table, top 10)   │  Forecast vs Actual (combo chart)    │
├──────────────────────────────┴──────────────────────────────────────┤
│  AI Insight: "Pipeline grew 12% QoQ driven by Technology sector..."  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 KPI Values (Sample)

| KPI | Q2 2026 | Q1 2026 | Change |
|-----|---------|---------|--------|
| Pipeline Value | $4,200,000 | $3,750,000 | +12.0% |
| Weighted Pipeline | $2,800,000 | $2,450,000 | +14.3% |
| Win Rate | 24.0% | 23.5% | +0.5pp |
| Avg Deal Size | $18,200 | $16,800 | +8.3% |
| Revenue (Won) | $1,100,000 | $980,000 | +12.2% |
| 90-Day Forecast | $1,400,000 | — | — |

### 2.3 Pipeline Funnel Data

| Stage | Deals | Value | % of Total |
|-------|-------|-------|------------|
| Prospecting | 62 | $1,100,000 | 26.2% |
| Qualification | 45 | $890,000 | 21.2% |
| Proposal | 28 | $720,000 | 17.1% |
| Negotiation | 18 | $540,000 | 12.9% |
| Closed Won | 37 | $950,000 | 22.6% |

---

## 3. VP Sales Pipeline Dashboard

### 3.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Pipeline Intelligence               [Last 30 Days ▼]                │
├──────────┬──────────┬──────────┬──────────┬──────────────────────────┤
│ Active   │ New Deals│ Velocity │ Stale    │ Conversion               │
│ Deals 87 │ +23 ↑    │ 12.4 days│ 8 deals  │ 3.1%                     │
├──────────┴──────────┴──────────┴──────────┴──────────────────────────┤
│  Deal Creation Trend (bar, daily)                                    │
├──────────────────────────────┬──────────────────────────────────────┤
│  Stage Aging Heatmap         │  Deal Value Distribution (histogram) │
├──────────────────────────────┼──────────────────────────────────────┤
│  Lead Score vs Deal Value    │  Industry Pipeline Breakdown (treemap)│
│  (scatter plot)              │                                      │
├──────────────────────────────┴──────────────────────────────────────┤
│  Stale Deals Alert: 8 deals in Negotiation > 30 days ($320K)        │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Key Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Active Deals | 87 | 80+ | 🟢 |
| New Deals (30d) | 23 | 20+ | 🟢 |
| Pipeline Velocity | 12.4 days/stage | < 14 | 🟢 |
| Stale Deals (>30d) | 8 | < 5 | 🟡 |
| Lead-to-Deal Conversion | 3.1% | 2.5% | 🟢 |
| Avg Lead Score (won) | 72.4 | 65+ | 🟢 |

---

## 4. CEO Platform Health Dashboard

### 4.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Platform Health — June 2026                                       │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────┤
│ Platform │ Lead     │ AI Score │ Automation│ Credit   │ User         │
│ ROI 340% │ Vel 142/w│ Avg 58.2 │ ROI 5.2x │ 72% used │ Growth +8%  │
├──────────┴──────────┴──────────┴──────────┴──────────┴──────────────┤
│  KPI Scorecard (6 green, 1 yellow, 0 red)                           │
├──────────────────────────────┬──────────────────────────────────────┤
│  Monthly Trends (multi-line) │  Platform ROI Breakdown (waterfall)  │
├──────────────────────────────┼──────────────────────────────────────┤
│  AI Insights Summary         │  Workflow Health Summary             │
├──────────────────────────────┴──────────────────────────────────────┤
│  Key Risks & Opportunities (AI-generated)                           │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Scorecard

| KPI | Value | Target | Status |
|-----|-------|--------|--------|
| Platform ROI | 340% | 300% | 🟢 |
| Lead Velocity | 142/week | 120/week | 🟢 |
| Avg Lead Score | 58.2 | 55.0 | 🟢 |
| Automation ROI | 5.2x | 3.0x | 🟢 |
| Credit Utilization | 72% | < 80% | 🟢 |
| Win Rate | 22% | 25% | 🟡 |
| User Growth | +8% MoM | +5% | 🟢 |

### 4.3 AI Insights (Sample)

1. **Pipeline grew 12% QoQ** — Driven by Technology sector (+28% contacts) and improved lead scoring (avg score up 3.2 points). *Recommended: Increase Technology-focused search campaigns.*

2. **Credit efficiency improving** — Credits per deal dropped from 85 to 62 (-27%) after auto-score workflow deployment. *Recommended: Expand workflow coverage to remaining manual processes.*

3. **Win rate plateau** — Win rate flat at 22% for 3 months despite higher lead scores. *Recommended: Review qualification criteria and stage progression rules.*

---

## 5. RevOps Efficiency Dashboard

### 5.1 Layout

Focus on operational efficiency metrics combining lead generation, AI usage, and workflow automation.

| Panel | Type | Data |
|-------|------|------|
| Credits per Deal trend | Line | 90-day trailing |
| Searches per Contact | KPI card | Current month |
| Workflow Success Rate | Gauge | Target: 95% |
| Lead-to-Score Coverage | Bullet chart | Target: 80% |
| Automation ROI by Workflow | Horizontal bar | Top 10 workflows |
| Credit Usage by Type | Stacked bar | Monthly |
| ETL Freshness | Status indicator | Last refresh time |

---

## 6. JSON Configurations

### 6.1 CRO Dashboard Config

```json
{
  "id": "cro-revenue",
  "name": "CRO Revenue Dashboard",
  "dashboard_type": "executive",
  "layout": [
    {"panel_id": "kpi_pipeline", "metric_key": "revenue.pipeline_value", "viz_type": "kpi_card", "x": 0, "y": 0, "w": 2, "h": 1},
    {"panel_id": "kpi_weighted", "metric_key": "revenue.weighted_pipeline", "viz_type": "kpi_card", "x": 2, "y": 0, "w": 2, "h": 1},
    {"panel_id": "kpi_win_rate", "metric_key": "crm.win_rate", "viz_type": "kpi_card", "x": 4, "y": 0, "w": 2, "h": 1},
    {"panel_id": "kpi_avg_deal", "metric_key": "revenue.avg_deal_size", "viz_type": "kpi_card", "x": 6, "y": 0, "w": 2, "h": 1},
    {"panel_id": "kpi_revenue", "metric_key": "revenue.won_value", "viz_type": "kpi_card", "x": 8, "y": 0, "w": 2, "h": 1},
    {"panel_id": "kpi_forecast", "metric_key": "forecast.revenue", "viz_type": "kpi_card", "x": 10, "y": 0, "w": 2, "h": 1},
    {"panel_id": "pipeline_funnel", "metric_key": "crm.funnel", "viz_type": "funnel_chart", "x": 0, "y": 1, "w": 12, "h": 2},
    {"panel_id": "revenue_trend", "metric_key": "revenue.pipeline_value", "viz_type": "area_chart", "x": 0, "y": 3, "w": 6, "h": 2},
    {"panel_id": "win_loss", "metric_key": "crm.win_loss_ratio", "viz_type": "donut_chart", "x": 6, "y": 3, "w": 6, "h": 2},
    {"panel_id": "top_deals", "metric_key": "crm.top_deals", "viz_type": "data_table", "x": 0, "y": 5, "w": 6, "h": 2},
    {"panel_id": "forecast_actual", "metric_key": "forecast.revenue", "viz_type": "combo_chart", "x": 6, "y": 5, "w": 6, "h": 2},
    {"panel_id": "ai_insights", "metric_key": "insights.latest", "viz_type": "insight_panel", "x": 0, "y": 7, "w": 12, "h": 1}
  ],
  "globalFilters": [
    {"type": "period", "default": "quarter"},
    {"type": "compare", "default": "previous_period"}
  ],
  "refreshInterval": 300
}
```

### 6.2 Seed Script

```python
# scripts/seed/executive_dashboards.py

EXECUTIVE_DASHBOARDS = [
    {"id": "cro-revenue", "name": "CRO Revenue Dashboard", "type": "executive", "config": CRO_CONFIG},
    {"id": "vp-pipeline", "name": "VP Sales Pipeline", "type": "executive", "config": VP_CONFIG},
    {"id": "ceo-health", "name": "CEO Platform Health", "type": "executive", "config": CEO_CONFIG},
    {"id": "revops-efficiency", "name": "RevOps Efficiency", "type": "operational", "config": REVOPS_CONFIG},
]

async def seed_dashboards(db, org_id):
    for dash in EXECUTIVE_DASHBOARDS:
        await upsert_dashboard_config(db, org_id, dash)
```

---

## 7. Sample API Responses

### 7.1 Executive Dashboard Response

```json
{
  "data": {
    "kpis": [
      {
        "key": "revenue.pipeline_value",
        "name": "Pipeline Value",
        "value": 4200000,
        "format": "currency",
        "comparison": {"change_percent": 12.0, "trend": "up", "previous_value": 3750000},
        "sparkline": [
          {"date": "2026-04-01", "value": 3500000},
          {"date": "2026-05-01", "value": 3750000},
          {"date": "2026-06-01", "value": 4200000}
        ]
      }
    ],
    "scorecard": {
      "overall_health": "green",
      "green_count": 6,
      "yellow_count": 1,
      "red_count": 0,
      "kpis": []
    },
    "panels": [
      {
        "panel_id": "pipeline_funnel",
        "viz_type": "funnel_chart",
        "data": {
          "breakdown": [
            {"label": "Prospecting", "value": 62, "percentage": 26.2},
            {"label": "Qualification", "value": 45, "percentage": 21.2},
            {"label": "Proposal", "value": 28, "percentage": 17.1},
            {"label": "Negotiation", "value": 18, "percentage": 12.9},
            {"label": "Closed Won", "value": 37, "percentage": 22.6}
          ]
        }
      }
    ],
    "insights": [
      {
        "type": "trend",
        "priority": "medium",
        "title": "Pipeline grew 12% QoQ",
        "summary": "Driven by Technology sector (+28% contacts) and improved lead scoring.",
        "recommended_actions": ["Increase Technology-focused search campaigns"]
      }
    ],
    "generated_at": "2026-06-29T10:00:00Z"
  }
}
```

### 7.2 Scorecard Response

```json
{
  "data": {
    "period": "2026-Q2",
    "overall_health": "green",
    "kpis": [
      {"key": "revenue.pipeline_value", "current": 4200000, "target": 3500000, "status": "green", "trend": "up", "change_percent": 12.0},
      {"key": "crm.win_rate", "current": 24.0, "target": 25.0, "status": "yellow", "trend": "flat", "change_percent": 0.5},
      {"key": "efficiency.platform_roi", "current": 340, "target": 300, "status": "green", "trend": "up", "change_percent": 15.0}
    ]
  }
}
```
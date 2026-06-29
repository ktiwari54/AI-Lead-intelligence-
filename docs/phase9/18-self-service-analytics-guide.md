# 18 — Self-Service Analytics Guide

**Version 4.0** | Phase 9 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Getting Started](#2-getting-started)
3. [Report Builder Walkthrough](#3-report-builder-walkthrough)
4. [Natural Language Queries](#4-natural-language-queries)
5. [Custom Dashboards](#5-custom-dashboards)
6. [Scheduling & Sharing](#6-scheduling--sharing)
7. [Best Practices](#7-best-practices)
8. [Limitations](#8-limitations)

---

## 1. Overview

This guide is for **Business Analysts and Power Users** who build custom reports, explore data, and create dashboards without engineering support.

**Required permissions:**
- `analytics:read` — View data, run NL queries
- `analytics:write` — Create reports, custom dashboards

**Primary routes:**
- Report Builder: `/analytics/reports`
- Custom Dashboards: `/analytics/custom`
- NL Query: `/analytics/explore`

---

## 2. Getting Started

### 2.1 Accessing Self-Service Analytics

1. Navigate to **Analytics** in the main navigation
2. Click **Reports** tab for report builder
3. Click **Explore** tab for natural language queries
4. Click **Custom Dashboards** to create personalized views

### 2.2 Available Data Domains

| Domain | Dimensions | Metrics | Source |
|--------|-----------|---------|--------|
| **Leads** | industry, geography, seniority, company_size, date | contacts, companies, avg_score | core, ai |
| **Pipeline** | stage, status, owner, date | deal_count, value, win_rate | crm |
| **Search** | date, query_type | search_count, avg_results | search |
| **Workflows** | workflow_name, trigger_type, node_type, date | executions, success_rate, duration | audit |
| **Billing** | transaction_type, date | credits_used, remaining | billing |

---

## 3. Report Builder Walkthrough

### 3.1 Creating a Report from Template

1. Go to `/analytics/reports`
2. Click **New Report** → **From Template**
3. Select a template (e.g., "Weekly Lead Summary")
4. Customize name and filters
5. Click **Preview** to see results
6. Click **Save** to persist

### 3.2 Building a Custom Report

**Example: "Contacts by Industry and Seniority, Last 30 Days"**

| Step | Action |
|------|--------|
| 1 | Click **New Report** → **Blank** |
| 2 | Drag **Contacts** metric to canvas |
| 3 | Drag **Industry** dimension to canvas (grouping) |
| 4 | Drag **Seniority** dimension to canvas (sub-grouping) |
| 5 | Add filter: Date Range = Last 30 days |
| 6 | Add filter: Score ≥ 40 (optional) |
| 7 | Click **Preview** — table appears |
| 8 | Switch viz type to **Horizontal Bar** (optional) |
| 9 | Click **Save** → name it → **Save** |

### 3.3 Visualization Switching

The same underlying query can be displayed as:

| Viz Type | Best For |
|----------|----------|
| Table | Detailed data, exact values |
| Bar Chart | Category comparison |
| Line Chart | Trends over time |
| Pie/Donut | Part-of-whole (≤ 12 categories) |
| Horizontal Bar | Ranked categories |

### 3.4 Running and Exporting

| Action | Steps |
|--------|-------|
| **Preview** | Click Preview (100-row limit, instant) |
| **Run full** | Click Run → select format (CSV/PDF/XLSX) |
| **Download** | Wait for completion → click Download |
| **Schedule** | Click Schedule → set cron, recipients, format |

---

## 4. Natural Language Queries

### 4.1 How It Works

1. Navigate to `/analytics/explore`
2. Type a question in plain English
3. The AI translates it to a structured query
4. Results appear with an auto-selected visualization
5. Optionally ask follow-up questions

### 4.2 Example Queries

| Question | What You Get |
|----------|-------------|
| "How many contacts did we add last week?" | Single KPI value + daily trend |
| "Which industries have the highest average score?" | Horizontal bar chart |
| "Show me workflow failures this month" | Table with failure details |
| "Compare pipeline value to last quarter" | KPI card with comparison badge |
| "What's our credit burn rate?" | Gauge chart vs monthly budget |
| "Top 5 countries by contact count" | Horizontal bar, top 5 |
| "How has lead velocity changed over 90 days?" | Line chart with trend line |

### 4.3 Tips for Better Results

| Tip | Example |
|-----|---------|
| Be specific about time | "last 30 days" not "recently" |
| Name the metric | "contacts" not "leads" (unless you mean both) |
| Specify dimensions | "by industry" for breakdowns |
| Use comparison words | "compared to last month" |
| Limit scope | "top 10" for ranked results |

### 4.4 Cost

Each NL query costs **1 AI credit**. Check your remaining credits on the dashboard before heavy exploration.

---

## 5. Custom Dashboards

### 5.1 Creating a Custom Dashboard

1. Go to `/analytics/custom`
2. Click **New Dashboard**
3. Name your dashboard
4. Add panels by selecting metrics and visualization types
5. Arrange panels via drag-and-drop on the 12-column grid
6. Set global filters (date range, comparison period)
7. Save and optionally set as default

### 5.2 Panel Configuration

| Setting | Options |
|---------|---------|
| Metric | Any metric from the catalog |
| Visualization | 25 chart types (see doc 07) |
| Size | Drag to resize on grid |
| Filters | Panel-specific filter overrides |
| Refresh | Inherit global or set custom interval |

### 5.3 Sharing

| Method | Steps |
|--------|-------|
| **Share link** | Click Share → copy link → send to team member |
| **Export image** | Click Export → PNG → download |
| **Schedule email** | Create a report from dashboard → Schedule |

---

## 6. Scheduling & Sharing

### 6.1 Scheduled Reports

```
Report → Schedule → Configure:
  - Frequency: Daily / Weekly / Monthly / Custom cron
  - Format: PDF / CSV / XLSX
  - Recipients: Team members (same org)
  - Filters: Override date range per schedule
```

### 6.2 Schedule Examples

| Report | Schedule | Recipients | Format |
|--------|----------|------------|--------|
| Weekly Lead Summary | Mon 8 AM | Sales team | PDF |
| Monthly Pipeline | 1st of month | VP Sales | XLSX |
| Daily Workflow Health | Daily 7 AM | Automation admin | PDF |
| Credit Usage | Fri 5 PM | Admin | CSV |

### 6.3 Plan Limits

| Feature | Starter | Professional | Enterprise |
|---------|---------|-------------|------------|
| Saved reports | 10 | 50 | Unlimited |
| Scheduled reports | 3 | 20 | Unlimited |
| Custom dashboards | 2 | 10 | Unlimited |
| NL queries/day | 5 | 20 | 100 |
| Export formats | CSV | CSV, PDF | CSV, PDF, XLSX |

---

## 7. Best Practices

### 7.1 Report Design

| Practice | Rationale |
|----------|-----------|
| Start with a template | Faster, proven query patterns |
| Use filters to limit scope | Faster queries, relevant results |
| Prefer warehouse metrics | Faster than OLTP fallback |
| Name reports descriptively | Team discoverability |
| Add descriptions | Context for future users |
| Test with Preview first | Avoid expensive full runs |

### 7.2 Dashboard Design

| Practice | Rationale |
|----------|-----------|
| Max 8 panels per dashboard | Cognitive load, performance |
| Lead with KPI cards | Immediate status assessment |
| Use consistent date ranges | Comparable panels |
| Group related panels | Logical flow top-to-bottom |
| Set appropriate refresh intervals | Balance freshness vs load |

### 7.3 Data Exploration

| Practice | Rationale |
|----------|-----------|
| Start broad, then filter | Avoid empty results |
| Use NL queries for discovery | Find available metrics |
| Switch to report builder for precision | Exact control over dimensions |
| Export for offline analysis | Complex calculations in Excel |
| Check data freshness indicator | Stale data may mislead |

---

## 8. Limitations

| Limitation | Detail | Workaround |
|------------|--------|------------|
| Max 100K rows per report | Performance constraint | Add filters to reduce scope |
| Max 365-day date range | API constraint | Run multiple reports |
| No cross-tenant data | Security | Request admin benchmark report |
| No raw SQL access | Security sandbox | Use custom metrics (admin only) |
| No real-time data | ETL lag 15 min | Use v3 OLTP endpoints for live counts |
| No custom viz types | Library is fixed | Request via feature request |
| NL queries cost credits | AI credit consumption | Use report builder for repeated queries |
| PII not available | Privacy protection | Contact data via CRM module |
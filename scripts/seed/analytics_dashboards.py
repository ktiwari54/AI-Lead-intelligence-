#!/usr/bin/env python3
"""Seed system analytics dashboards and widget library for Phase 9."""
from __future__ import annotations

import asyncio

WIDGET_LIBRARY = [
    {"widget_type": "kpi_card", "name": "KPI Card", "category": "general", "default_config": {"format": "number"}},
    {"widget_type": "line_chart", "name": "Line Chart", "category": "charts", "default_config": {"show_legend": True}},
    {"widget_type": "bar_chart", "name": "Bar Chart", "category": "charts", "default_config": {"stacked": False}},
    {"widget_type": "funnel", "name": "Conversion Funnel", "category": "sales", "default_config": {"show_rates": True}},
    {"widget_type": "gauge", "name": "Gauge", "category": "kpis", "default_config": {"min": 0, "max": 100}},
    {"widget_type": "table", "name": "Data Table", "category": "general", "default_config": {"page_size": 10}},
]

SYSTEM_DASHBOARDS = [
    {
        "slug": "executive-overview",
        "name": "Executive Overview",
        "dashboard_type": "executive",
        "description": "C-suite KPIs, growth trends, and AI-generated insights",
        "widgets": [
            {"widget_key": "total_companies", "widget_type": "kpi_card", "title": "Total Companies", "metric_key": "total_companies", "position": {"x": 0, "y": 0, "w": 3, "h": 2}},
            {"widget_key": "total_contacts", "widget_type": "kpi_card", "title": "Total Contacts", "metric_key": "total_contacts", "position": {"x": 3, "y": 0, "w": 3, "h": 2}},
            {"widget_key": "pipeline_value", "widget_type": "kpi_card", "title": "Pipeline Value", "metric_key": "pipeline_value", "position": {"x": 6, "y": 0, "w": 3, "h": 2}},
            {"widget_key": "company_growth", "widget_type": "line_chart", "title": "Company Growth", "metric_key": "companies_created", "position": {"x": 0, "y": 2, "w": 6, "h": 4}},
            {"widget_key": "contact_growth", "widget_type": "line_chart", "title": "Contact Growth", "metric_key": "contacts_created", "position": {"x": 6, "y": 2, "w": 6, "h": 4}},
        ],
    },
    {
        "slug": "sales-performance",
        "name": "Sales Performance",
        "dashboard_type": "sales",
        "description": "Pipeline funnel, deal velocity, and conversion metrics",
        "widgets": [
            {"widget_key": "lead_funnel", "widget_type": "funnel", "title": "Lead Funnel", "metric_key": "lead_funnel", "position": {"x": 0, "y": 0, "w": 6, "h": 4}},
            {"widget_key": "pipeline_value", "widget_type": "kpi_card", "title": "Pipeline Value", "metric_key": "pipeline_value", "position": {"x": 6, "y": 0, "w": 3, "h": 2}},
            {"widget_key": "avg_deal_size", "widget_type": "kpi_card", "title": "Avg Deal Size", "metric_key": "avg_deal_value", "position": {"x": 9, "y": 0, "w": 3, "h": 2}},
        ],
    },
    {
        "slug": "discovery-analytics",
        "name": "Discovery Analytics",
        "dashboard_type": "discovery",
        "description": "Search activity, connector performance, and enrichment metrics",
        "widgets": [
            {"widget_key": "discovery_jobs", "widget_type": "kpi_card", "title": "Discovery Jobs", "metric_key": "discovery_jobs", "position": {"x": 0, "y": 0, "w": 4, "h": 2}},
            {"widget_key": "search_volume", "widget_type": "line_chart", "title": "Search Volume", "metric_key": "searches", "position": {"x": 0, "y": 2, "w": 8, "h": 4}},
            {"widget_key": "success_rate", "widget_type": "gauge", "title": "Success Rate", "metric_key": "discovery_success_rate", "position": {"x": 8, "y": 0, "w": 4, "h": 4}},
        ],
    },
]


async def seed():
    import backend.app.orm_registry  # noqa: F401
    from sqlalchemy import select
    from backend.database import AsyncSessionLocal
    from backend.app.analytics.models import Dashboard, DashboardWidget, WidgetLibraryItem
    from backend.app.organizations.models import Organization

    async with AsyncSessionLocal() as db:
        for widget in WIDGET_LIBRARY:
            existing = await db.execute(
                select(WidgetLibraryItem).where(
                    WidgetLibraryItem.widget_type == widget["widget_type"],
                    WidgetLibraryItem.is_system == True,  # noqa: E712
                )
            )
            if existing.scalar_one_or_none():
                print(f"Skip existing widget: {widget['widget_type']}")
                continue
            db.add(WidgetLibraryItem(
                widget_type=widget["widget_type"],
                name=widget["name"],
                category=widget["category"],
                default_config=widget["default_config"],
                is_system=True,
            ))
            print(f"Seeded widget: {widget['widget_type']}")

        orgs = (await db.execute(select(Organization.id).limit(10))).scalars().all()
        if not orgs:
            print("No organizations found — skipping dashboard seed")
            await db.commit()
            return

        for org_id in orgs:
            for dash_def in SYSTEM_DASHBOARDS:
                existing = await db.execute(
                    select(Dashboard).where(
                        Dashboard.organization_id == org_id,
                        Dashboard.slug == dash_def["slug"],
                    )
                )
                if existing.scalar_one_or_none():
                    print(f"Skip existing dashboard: {dash_def['slug']} for org {org_id}")
                    continue

                dashboard = Dashboard(
                    organization_id=org_id,
                    name=dash_def["name"],
                    slug=dash_def["slug"],
                    dashboard_type=dash_def["dashboard_type"],
                    description=dash_def["description"],
                    is_system=True,
                    layout={"columns": 12, "row_height": 60},
                )
                db.add(dashboard)
                await db.flush()

                for w in dash_def["widgets"]:
                    db.add(DashboardWidget(
                        dashboard_id=dashboard.id,
                        widget_key=w["widget_key"],
                        widget_type=w["widget_type"],
                        title=w["title"],
                        metric_key=w.get("metric_key"),
                        position=w["position"],
                        config={},
                    ))
                print(f"Seeded dashboard: {dash_def['slug']} for org {org_id}")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
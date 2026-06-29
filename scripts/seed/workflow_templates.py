#!/usr/bin/env python3
"""Seed system workflow templates for Phase 8."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

TEMPLATES = [
    {
        "slug": "lead-qualification",
        "name": "Lead Qualification",
        "description": "Score and qualify new contacts automatically",
        "category": "sales",
        "trigger_type": "contact.created",
        "canvas": {
            "nodes": [
                {"key": "trigger", "type": "trigger", "config": {"event": "contact.created"}},
                {"key": "score", "type": "ai", "config": {"ai_action": "score_lead"}},
                {"key": "check", "type": "condition", "config": {"condition": {"field": "results.score.lead_score", "operator": "gte", "value": 70}}},
                {"key": "notify", "type": "action", "config": {"action_type": "send_notification", "template": "high_value_contact"}},
                {"key": "end", "type": "end", "config": {}},
            ],
            "edges": [
                {"source": "trigger", "target": "score"},
                {"source": "score", "target": "check"},
                {"source": "check", "target": "notify", "label": "true"},
                {"source": "notify", "target": "end"},
                {"source": "check", "target": "end", "label": "false"},
            ],
        },
    },
    {
        "slug": "lead-assignment",
        "name": "Lead Assignment",
        "description": "Route leads to owners based on territory",
        "category": "sales",
        "trigger_type": "lead.created",
        "canvas": {
            "nodes": [
                {"key": "trigger", "type": "trigger", "config": {}},
                {"key": "assign", "type": "action", "config": {"action_type": "assign_owner", "strategy": "round_robin"}},
                {"key": "task", "type": "action", "config": {"action_type": "create_task", "title": "Follow up new lead"}},
                {"key": "end", "type": "end", "config": {}},
            ],
            "edges": [
                {"source": "trigger", "target": "assign"},
                {"source": "assign", "target": "task"},
                {"source": "task", "target": "end"},
            ],
        },
    },
    {
        "slug": "sales-follow-up",
        "name": "Sales Follow-up",
        "description": "Automated follow-up sequence after activity",
        "category": "sales",
        "trigger_type": "activity.completed",
        "canvas": {
            "nodes": [
                {"key": "trigger", "type": "trigger", "config": {}},
                {"key": "delay", "type": "delay", "config": {"seconds": 86400}},
                {"key": "email", "type": "ai", "config": {"ai_action": "generate_followup"}},
                {"key": "send", "type": "action", "config": {"action_type": "send_email"}},
                {"key": "end", "type": "end", "config": {}},
            ],
            "edges": [
                {"source": "trigger", "target": "delay"},
                {"source": "delay", "target": "email"},
                {"source": "email", "target": "send"},
                {"source": "send", "target": "end"},
            ],
        },
    },
    {
        "slug": "company-research",
        "name": "Company Research",
        "description": "AI research and summary for new companies",
        "category": "enrichment",
        "trigger_type": "company.created",
        "canvas": {
            "nodes": [
                {"key": "trigger", "type": "trigger", "config": {}},
                {"key": "research", "type": "ai", "config": {"ai_action": "research_company"}},
                {"key": "summarize", "type": "ai", "config": {"ai_action": "summarize_company"}},
                {"key": "note", "type": "action", "config": {"action_type": "create_note"}},
                {"key": "end", "type": "end", "config": {}},
            ],
            "edges": [
                {"source": "trigger", "target": "research"},
                {"source": "research", "target": "summarize"},
                {"source": "summarize", "target": "note"},
                {"source": "note", "target": "end"},
            ],
        },
    },
    {
        "slug": "daily-report",
        "name": "Daily Report",
        "description": "Export and email daily pipeline report",
        "category": "reporting",
        "trigger_type": "cron",
        "canvas": {
            "nodes": [
                {"key": "trigger", "type": "trigger", "config": {"cron": "0 8 * * 1-5"}},
                {"key": "export", "type": "action", "config": {"action_type": "export_csv", "entity_type": "deal"}},
                {"key": "email", "type": "action", "config": {"action_type": "send_email", "template": "daily_report"}},
                {"key": "end", "type": "end", "config": {}},
            ],
            "edges": [
                {"source": "trigger", "target": "export"},
                {"source": "export", "target": "email"},
                {"source": "email", "target": "end"},
            ],
        },
    },
]


async def seed():
    from sqlalchemy import select
    from backend.database import AsyncSessionLocal
    from backend.app.workflows.models import WorkflowTemplate

    async with AsyncSessionLocal() as db:
        for tmpl in TEMPLATES:
            existing = await db.execute(
                select(WorkflowTemplate).where(WorkflowTemplate.slug == tmpl["slug"])
            )
            if existing.scalar_one_or_none():
                print(f"Skip existing template: {tmpl['slug']}")
                continue
            db.add(WorkflowTemplate(
                organization_id=None,
                slug=tmpl["slug"],
                name=tmpl["name"],
                description=tmpl["description"],
                category=tmpl["category"],
                trigger_type=tmpl["trigger_type"],
                canvas=tmpl["canvas"],
                is_system=True,
            ))
            print(f"Seeded template: {tmpl['slug']}")
        await db.commit()


def export_samples():
    out = Path(__file__).parent / "fixtures" / "workflow_templates.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(TEMPLATES, indent=2))
    print(f"Exported samples to {out}")


if __name__ == "__main__":
    export_samples()
    asyncio.run(seed())
# 16 — Sample Workflow Definitions

**Version 1.0** | Phase 8 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Auto-Score New Contacts (JSON)](#2-auto-score-new-contacts-json)
3. [Approval-Gated CRM Sync (JSON)](#3-approval-gated-crm-sync-json)
4. [Scheduled Weekly Export (YAML)](#4-scheduled-weekly-export-yaml)
5. [AI Classify and Route (JSON)](#5-ai-classify-and-route-json)
6. [Legacy v1 Format (JSON)](#6-legacy-v1-format-json)
7. [Webhook-Triggered Workflow (JSON)](#7-webhook-triggered-workflow-json)
8. [Complex Branching (JSON)](#8-complex-branching-json)

---

## 1. Overview

This document provides **implementation-ready** workflow definitions in JSON and YAML formats. These examples can be imported via API (`POST /workflows`) or instantiated from templates.

**Schema version:** `2.0`

---

## 2. Auto-Score New Contacts (JSON)

```json
{
  "name": "Auto-Score New Contacts",
  "description": "Score VP+ contacts on creation and notify on high scores",
  "category": "lead_scoring",
  "definition": {
    "schema_version": "2.0",
    "nodes": [
      {
        "id": "trigger-1",
        "type": "event_trigger",
        "position": { "x": 100, "y": 200 },
        "data": {
          "label": "Contact Created",
          "config": {
            "event": "contact.created",
            "filter": "{{ trigger.payload.seniority in ['vp', 'c_level', 'director'] }}"
          }
        }
      },
      {
        "id": "score-1",
        "type": "ai_score",
        "position": { "x": 400, "y": 200 },
        "data": {
          "label": "AI Score Contact",
          "config": {
            "entity_type": "contact",
            "entity_id": "{{ trigger.payload.id }}",
            "model": "default",
            "include_explanation": true
          }
        }
      },
      {
        "id": "cond-1",
        "type": "condition",
        "position": { "x": 700, "y": 200 },
        "data": {
          "label": "High Score?",
          "config": {
            "expression": "{{ steps.score-1.output.score >= 70 }}"
          }
        }
      },
      {
        "id": "notify-1",
        "type": "send_notification",
        "position": { "x": 1000, "y": 100 },
        "data": {
          "label": "Notify Sales Team",
          "config": {
            "template": "high_value_contact",
            "recipients": { "type": "role", "value": "manager" },
            "data": {
              "contact_id": "{{ trigger.payload.id }}",
              "score": "{{ steps.score-1.output.score }}",
              "explanation": "{{ steps.score-1.output.explanation }}"
            }
          }
        }
      },
      {
        "id": "tag-1",
        "type": "add_tag",
        "position": { "x": 1000, "y": 300 },
        "data": {
          "label": "Tag as Low Priority",
          "config": {
            "entity_type": "contact",
            "entity_id": "{{ trigger.payload.id }}",
            "tag": "low_priority_score"
          }
        }
      }
    ],
    "edges": [
      { "id": "e1", "source": "trigger-1", "target": "score-1", "type": "default" },
      { "id": "e2", "source": "score-1", "target": "cond-1", "type": "default" },
      { "id": "e3", "source": "cond-1", "target": "notify-1", "type": "conditional_true" },
      { "id": "e4", "source": "cond-1", "target": "tag-1", "type": "conditional_false" }
    ],
    "settings": {
      "timeout_seconds": 300,
      "max_retries": 3
    }
  }
}
```

---

## 3. Approval-Gated CRM Sync (JSON)

```json
{
  "name": "Approve High-Value CRM Sync",
  "description": "Require manager approval before syncing deals over $100K",
  "category": "crm_automation",
  "definition": {
    "schema_version": "2.0",
    "nodes": [
      {
        "id": "trigger-1",
        "type": "event_trigger",
        "data": {
          "label": "Deal Stage Changed",
          "config": {
            "event": "deal.stage_changed",
            "filter": "{{ trigger.payload.deal.value >= 100000 }}"
          }
        }
      },
      {
        "id": "score-1",
        "type": "ai_score",
        "data": {
          "label": "Score Associated Contact",
          "config": {
            "entity_type": "contact",
            "entity_id": "{{ trigger.payload.deal.primary_contact_id }}",
            "model": "default"
          }
        }
      },
      {
        "id": "approval-1",
        "type": "approval_sequential",
        "data": {
          "label": "Manager Approval",
          "config": {
            "title": "Approve CRM sync for ${{ trigger.payload.deal.value }} deal",
            "message": "Deal '{{ trigger.payload.deal.name }}' requires approval before CRM sync.",
            "approvers": [
              { "type": "role", "value": "manager", "order": 1 }
            ],
            "timeout_hours": 48,
            "timeout_action": "escalate",
            "escalation": { "type": "role", "value": "admin" },
            "context_fields": [
              "trigger.payload.deal.value",
              "trigger.payload.deal.name",
              "steps.score-1.output.score"
            ]
          }
        }
      },
      {
        "id": "crm-1",
        "type": "crm_sync",
        "data": {
          "label": "Sync to CRM",
          "config": {
            "entity_type": "deal",
            "entity_id": "{{ trigger.payload.deal.id }}",
            "direction": "push",
            "connector": "default"
          }
        }
      },
      {
        "id": "notify-1",
        "type": "send_notification",
        "data": {
          "label": "Sync Complete",
          "config": {
            "template": "crm_sync_complete",
            "recipients": { "type": "user", "value": "{{ trigger.payload.deal.owner_id }}" }
          }
        }
      }
    ],
    "edges": [
      { "id": "e1", "source": "trigger-1", "target": "score-1" },
      { "id": "e2", "source": "score-1", "target": "approval-1" },
      { "id": "e3", "source": "approval-1", "target": "crm-1" },
      { "id": "e4", "source": "crm-1", "target": "notify-1" }
    ],
    "settings": {
      "timeout_seconds": 600
    }
  }
}
```

---

## 4. Scheduled Weekly Export (YAML)

```yaml
name: Weekly Contact Export
description: Export high-scoring contacts every Monday at 8 AM EST
category: data_operations

definition:
  schema_version: "2.0"
  nodes:
    - id: trigger-1
      type: schedule_trigger
      data:
        label: Weekly Schedule
        config:
          cron_expression: "0 8 * * 1"
          timezone: America/New_York
          holiday_calendar_id: us_federal

    - id: export-1
      type: export_data
      data:
        label: Export High-Score Contacts
        config:
          entity_type: contact
          format: csv
          filters:
            lead_score_min: 70
            updated_within_days: 7
          columns:
            - first_name
            - last_name
            - email
            - company_name
            - lead_score

    - id: notify-1
      type: send_notification
      data:
        label: Export Ready
        config:
          template: export_complete
          recipients:
            type: role
            value: manager
          data:
            export_id: "{{ steps.export-1.output.export_id }}"
            row_count: "{{ steps.export-1.output.row_count }}"

  edges:
    - id: e1
      source: trigger-1
      target: export-1
    - id: e2
      source: export-1
      target: notify-1

  settings:
    timeout_seconds: 600
```

---

## 5. AI Classify and Route (JSON)

```json
{
  "name": "Classify and Route Inbound Leads",
  "definition": {
    "schema_version": "2.0",
    "nodes": [
      {
        "id": "trigger-1",
        "type": "event_trigger",
        "data": {
          "config": { "event": "contact.created", "filter": "{{ trigger.payload.source == 'inbound_form' }}" }
        }
      },
      {
        "id": "classify-1",
        "type": "ai_classify",
        "data": {
          "config": {
            "text": "{{ trigger.payload.notes }}",
            "categories": ["hot_lead", "warm_lead", "support_request", "spam"],
            "model": "fast"
          }
        }
      },
      {
        "id": "switch-1",
        "type": "switch",
        "data": {
          "config": {
            "expression": "{{ steps.classify-1.output.classification }}",
            "cases": [
              { "value": "hot_lead", "target": "task-hot" },
              { "value": "warm_lead", "target": "task-warm" },
              { "value": "support_request", "target": "notify-support" }
            ],
            "default_target": "tag-spam"
          }
        }
      },
      {
        "id": "task-hot",
        "type": "create_task",
        "data": {
          "config": {
            "title": "URGENT: Hot inbound lead - {{ trigger.payload.first_name }}",
            "assignee": { "type": "role", "value": "manager" },
            "due_in_hours": 4,
            "priority": "high"
          }
        }
      },
      {
        "id": "task-warm",
        "type": "create_task",
        "data": {
          "config": {
            "title": "Follow up: Warm lead - {{ trigger.payload.first_name }}",
            "assignee": { "type": "role", "value": "member" },
            "due_in_hours": 24,
            "priority": "medium"
          }
        }
      },
      {
        "id": "notify-support",
        "type": "send_notification",
        "data": {
          "config": {
            "template": "support_request",
            "recipients": { "type": "team", "value": "support" }
          }
        }
      },
      {
        "id": "tag-spam",
        "type": "add_tag",
        "data": {
          "config": {
            "entity_type": "contact",
            "entity_id": "{{ trigger.payload.id }}",
            "tag": "spam_suspect"
          }
        }
      }
    ],
    "edges": [
      { "id": "e1", "source": "trigger-1", "target": "classify-1" },
      { "id": "e2", "source": "classify-1", "target": "switch-1" },
      { "id": "e3", "source": "switch-1", "target": "task-hot" },
      { "id": "e4", "source": "switch-1", "target": "task-warm" },
      { "id": "e5", "source": "switch-1", "target": "notify-support" },
      { "id": "e6", "source": "switch-1", "target": "tag-spam" }
    ]
  }
}
```

---

## 6. Legacy v1 Format (JSON)

Phase 3 format — auto-converted to v2 on ingest:

```json
{
  "name": "Auto-score new contacts (v1)",
  "trigger": { "event": "contact.created" },
  "conditions": [
    { "field": "contact.seniority", "operator": "in", "value": ["vp", "c_level"] }
  ],
  "actions": [
    { "type": "score_entity", "params": { "entity_type": "contact" } },
    { "type": "send_notification", "params": { "template": "high_value_contact" } }
  ],
  "is_active": true
}
```

Equivalent v2 graph auto-generated by `v1_adapter.py`.

---

## 7. Webhook-Triggered Workflow (JSON)

```json
{
  "name": "External System Integration",
  "definition": {
    "schema_version": "2.0",
    "nodes": [
      {
        "id": "trigger-1",
        "type": "webhook_trigger",
        "data": {
          "config": {
            "webhook_id": "auto-generated-on-activate",
            "allowed_ips": [],
            "require_signature": true
          }
        }
      },
      {
        "id": "extract-1",
        "type": "ai_extract",
        "data": {
          "config": {
            "text": "{{ trigger.payload.body.message }}",
            "schema": {
              "email": { "type": "string" },
              "company": { "type": "string" },
              "intent": { "type": "string" }
            }
          }
        }
      },
      {
        "id": "create-1",
        "type": "create_contact",
        "data": {
          "config": {
            "email": "{{ steps.extract-1.output.extracted.email }}",
            "company_name": "{{ steps.extract-1.output.extracted.company }}",
            "source": "webhook",
            "notes": "{{ trigger.payload.body.message }}"
          }
        }
      }
    ],
    "edges": [
      { "id": "e1", "source": "trigger-1", "target": "extract-1" },
      { "id": "e2", "source": "extract-1", "target": "create-1" }
    ]
  }
}
```

---

## 8. Complex Branching (JSON)

Demonstrates `loop`, `merge`, `delay`, and `set_variable` nodes:

```json
{
  "name": "Batch Score and Enrich Contacts",
  "definition": {
    "schema_version": "2.0",
    "nodes": [
      {
        "id": "trigger-1",
        "type": "schedule_trigger",
        "data": {
          "config": { "cron_expression": "0 2 * * *", "timezone": "UTC" }
        }
      },
      {
        "id": "search-1",
        "type": "ai_nl_search",
        "data": {
          "config": {
            "query": "contacts not scored in last 30 days with valid email",
            "entity_type": "contact",
            "limit": 100
          }
        }
      },
      {
        "id": "loop-1",
        "type": "loop",
        "data": {
          "config": {
            "items": "{{ steps.search-1.output.results }}",
            "item_variable": "current_contact",
            "max_iterations": 100
          }
        }
      },
      {
        "id": "score-1",
        "type": "ai_score",
        "data": {
          "config": {
            "entity_type": "contact",
            "entity_id": "{{ vars.current_contact.id }}"
          }
        }
      },
      {
        "id": "delay-1",
        "type": "delay",
        "data": {
          "config": { "seconds": 2 }
        }
      },
      {
        "id": "merge-1",
        "type": "merge",
        "data": {
          "config": { "mode": "collect", "output_variable": "scored_contacts" }
        }
      },
      {
        "id": "summary-1",
        "type": "set_variable",
        "data": {
          "config": {
            "name": "batch_summary",
            "value": {
              "total_scored": "{{ len(vars.scored_contacts) }}",
              "avg_score": "{{ avg(vars.scored_contacts, 'score') }}"
            }
          }
        }
      },
      {
        "id": "notify-1",
        "type": "send_notification",
        "data": {
          "config": {
            "template": "batch_score_complete",
            "recipients": { "type": "role", "value": "admin" },
            "data": "{{ vars.batch_summary }}"
          }
        }
      }
    ],
    "edges": [
      { "id": "e1", "source": "trigger-1", "target": "search-1" },
      { "id": "e2", "source": "search-1", "target": "loop-1" },
      { "id": "e3", "source": "loop-1", "target": "score-1" },
      { "id": "e4", "source": "score-1", "target": "delay-1" },
      { "id": "e5", "source": "delay-1", "target": "loop-1" },
      { "id": "e6", "source": "loop-1", "target": "merge-1" },
      { "id": "e7", "source": "merge-1", "target": "summary-1" },
      { "id": "e8", "source": "summary-1", "target": "notify-1" }
    ],
    "settings": {
      "timeout_seconds": 1800,
      "max_retries": 1
    }
  }
}
```

---

## Related Documents

- [02-visual-workflow-builder-spec.md](./02-visual-workflow-builder-spec.md) — Canvas representation
- [11-workflow-templates.md](./11-workflow-templates.md) — Template catalog
- [07-api-specification.md](./07-api-specification.md) — Import via API
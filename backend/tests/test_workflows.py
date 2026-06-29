"""Unit tests for Phase 8 Workflow Engine."""
from __future__ import annotations

import pytest

from backend.app.workflows.engine.compiler import WorkflowCompiler
from backend.app.workflows.engine.conditions import evaluate_condition, evaluate_conditions
from backend.app.workflows.engine.validator import WorkflowValidator
from backend.app.workflows.engine.approval import ApprovalEngine
from backend.app.workflows.constants import OrchestrationMode
from backend.app.workflows.orchestration import infer_orchestration_mode, validate_mode_constraints


@pytest.fixture
def compiler():
    return WorkflowCompiler()


@pytest.fixture
def validator():
    return WorkflowValidator()


SAMPLE_CANVAS = {
    "nodes": [
        {"key": "trigger", "type": "trigger", "label": "Contact Created", "config": {"event": "contact.created"}},
        {"key": "check_score", "type": "condition", "label": "Score Check", "config": {"condition": {"field": "trigger.score", "operator": "gte", "value": 70}}},
        {"key": "notify", "type": "action", "label": "Notify", "config": {"action_type": "send_notification"}},
        {"key": "end", "type": "end", "label": "End", "config": {}},
    ],
    "edges": [
        {"source": "trigger", "target": "check_score"},
        {"source": "check_score", "target": "notify", "label": "true"},
        {"source": "notify", "target": "end"},
    ],
}


def test_compiler_canvas(compiler):
    plan = compiler.compile(
        trigger_type="contact.created",
        trigger_config={"event": "contact.created"},
        canvas=SAMPLE_CANVAS,
    )
    assert plan["entry_node"] == "trigger"
    assert len(plan["nodes"]) >= 3
    assert plan["graph"] is True


def test_compiler_linear_steps(compiler):
    steps = [
        {"id": "score", "type": "action", "config": {"action_type": "score_entity"}},
        {"id": "email", "type": "action", "config": {"action_type": "send_email"}},
    ]
    plan = compiler.compile(
        trigger_type="manual",
        trigger_config={},
        steps=steps,
    )
    assert plan["entry_node"] == "trigger"
    assert any(n["key"] == "score" for n in plan["nodes"])
    assert plan["graph"] is False


def test_validator_valid_canvas(validator):
    result = validator.validate(canvas=SAMPLE_CANVAS, steps=None, trigger_type="contact.created")
    assert result["valid"] is True
    assert result["errors"] == []


def test_validator_missing_trigger(validator):
    canvas = {"nodes": [{"key": "action1", "type": "action"}], "edges": []}
    result = validator.validate(canvas=canvas, steps=None, trigger_type="manual")
    assert result["valid"] is False
    assert any("trigger" in e.lower() for e in result["errors"])


def test_condition_evaluation():
    ctx = {"trigger": {"score": 85, "name": "Acme"}}
    assert evaluate_condition({"field": "trigger.score", "operator": "gte", "value": 70}, ctx)
    assert not evaluate_condition({"field": "trigger.score", "operator": "lt", "value": 70}, ctx)
    assert evaluate_conditions([], ctx)


def test_condition_boolean_logic():
    ctx = {"trigger": {"score": 85, "verified": True}}
    cond = {
        "and": [
            {"field": "trigger.score", "operator": "gte", "value": 80},
            {"field": "trigger.verified", "operator": "eq", "value": True},
        ]
    }
    assert evaluate_condition(cond, ctx)


def test_approval_sequential():
    engine = ApprovalEngine()
    approvals = [
        {"id": "1", "status": "approved"},
        {"id": "2", "status": "pending"},
    ]
    assert engine.evaluate_policy(approval_type="sequential", approvals=approvals) == "pending"


def test_approval_majority():
    engine = ApprovalEngine()
    approvals = [
        {"id": "1", "status": "approved"},
        {"id": "2", "status": "approved"},
        {"id": "3", "status": "pending"},
    ]
    assert engine.evaluate_policy(approval_type="majority", approvals=approvals) == "approved"


def test_infer_event_driven_mode():
    mode = infer_orchestration_mode(trigger_type="lead.created", canvas=SAMPLE_CANVAS)
    assert mode == OrchestrationMode.EVENT_DRIVEN


def test_infer_scheduled_mode():
    mode = infer_orchestration_mode(trigger_type="cron", canvas=None)
    assert mode == OrchestrationMode.SCHEDULED


def test_infer_hitl_mode():
    canvas = {
        "nodes": [
            {"key": "t", "type": "trigger"},
            {"key": "a", "type": "approval", "config": {}},
            {"key": "e", "type": "end"},
        ],
        "edges": [],
    }
    mode = infer_orchestration_mode(trigger_type="lead.updated", canvas=canvas)
    assert mode == OrchestrationMode.HUMAN_IN_THE_LOOP


def test_hitl_requires_approval_node():
    errors = validate_mode_constraints(
        OrchestrationMode.HUMAN_IN_THE_LOOP,
        trigger_type="lead.updated",
        canvas=SAMPLE_CANVAS,
    )
    assert any("approval" in e.lower() for e in errors)


def test_scheduled_requires_schedule_or_cron():
    errors = validate_mode_constraints(
        OrchestrationMode.SCHEDULED,
        trigger_type="lead.created",
        canvas=SAMPLE_CANVAS,
    )
    assert len(errors) > 0


@pytest.mark.asyncio
async def test_executor_runs_simple_plan():
    from uuid import uuid4
    from backend.app.workflows.engine.executor import WorkflowExecutor

    executor = WorkflowExecutor()
    plan = {
        "entry_node": "trigger",
        "nodes": [
            {"key": "trigger", "type": "trigger", "config": {}},
            {"key": "action1", "type": "action", "config": {"action_type": "send_notification"}},
            {"key": "end", "type": "end", "config": {}},
        ],
        "edges": [
            {"source": "trigger", "target": "action1"},
            {"source": "action1", "target": "end"},
        ],
        "variables": {},
    }
    result = await executor.execute(plan, org_id=uuid4(), user_id=None, trigger_data={"test": True})
    assert result["status"] in ("completed", "waiting")
    assert len(result["step_results"]) >= 2
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from backend.app.workflows.constants import ExecutionStatus, NodeType
from backend.app.workflows.engine.actions import action_registry
from backend.app.workflows.engine.approval import ApprovalEngine
from backend.app.workflows.engine.conditions import evaluate_condition

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes compiled workflow plans with retry-safe idempotent steps."""

    def __init__(self) -> None:
        self._approval = ApprovalEngine()

    async def execute(
        self,
        plan: dict[str, Any],
        *,
        org_id: UUID,
        user_id: UUID | None,
        trigger_data: dict[str, Any],
        execution_id: UUID | None = None,
        checkpoint: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context: dict[str, Any] = {
            "trigger": trigger_data,
            "variables": plan.get("variables", {}),
            "org_id": str(org_id),
            "execution_id": str(execution_id) if execution_id else None,
        }
        if checkpoint:
            context.update(checkpoint.get("context", {}))

        nodes = plan.get("nodes", [])
        edges = plan.get("edges", [])
        adjacency = self._build_adjacency(edges)
        node_map = {n["key"]: n for n in nodes}

        entry = plan.get("entry_node")
        if not entry and nodes:
            entry = nodes[0]["key"]

        step_results: list[dict[str, Any]] = []
        status = ExecutionStatus.COMPLETED.value
        error_message: str | None = None
        current = entry
        visited_guard = 0

        while current and visited_guard < 500:
            visited_guard += 1
            node = node_map.get(current)
            if not node:
                break

            ntype = node.get("type")
            if ntype == NodeType.END.value:
                step_results.append({"node": current, "status": "completed", "type": ntype})
                break

            if ntype == NodeType.TRIGGER.value:
                step_results.append({"node": current, "status": "completed", "type": ntype})
                current = self._next_node(adjacency, current, context)
                continue

            if ntype in (NodeType.CONDITION.value, NodeType.DECISION.value):
                cond = node.get("config", {}).get("condition", {})
                passed = evaluate_condition(cond, context)
                step_results.append({"node": current, "status": "completed", "type": ntype, "passed": passed})
                current = self._next_node(adjacency, current, context, branch="true" if passed else "false")
                continue

            if ntype == NodeType.DELAY.value:
                delay_secs = node.get("config", {}).get("seconds", 0)
                step_results.append({"node": current, "status": "waiting", "type": ntype, "delay_seconds": delay_secs})
                status = ExecutionStatus.WAITING.value
                break

            if ntype == NodeType.APPROVAL.value:
                step_results.append({"node": current, "status": "waiting_approval", "type": ntype})
                status = ExecutionStatus.WAITING.value
                break

            if ntype == NodeType.PARALLEL.value:
                branches = adjacency.get(current, [])
                parallel_results = []
                for edge in branches:
                    branch_key = edge.get("target")
                    branch_node = node_map.get(branch_key)
                    if branch_node:
                        parallel_results.append({"node": branch_key, "status": "queued"})
                step_results.append({"node": current, "status": "completed", "type": ntype, "branches": parallel_results})
                merge_targets = [e.get("target") for e in adjacency.get(current, [])]
                current = merge_targets[0] if merge_targets else None
                continue

            start = time.monotonic()
            try:
                result = await self._execute_node(node, org_id=org_id, user_id=user_id, context=context)
                duration_ms = int((time.monotonic() - start) * 1000)
                step_results.append({
                    "node": current,
                    "status": "completed",
                    "type": ntype,
                    "result": result,
                    "duration_ms": duration_ms,
                })
                context.setdefault("results", {})[current] = result
            except Exception as exc:
                logger.exception("Workflow node %s failed", current)
                step_results.append({"node": current, "status": "failed", "type": ntype, "error": str(exc)})
                status = ExecutionStatus.FAILED.value
                error_message = str(exc)
                break

            current = self._next_node(adjacency, current, context)

        return {
            "status": status,
            "step_results": step_results,
            "error_message": error_message,
            "context": context,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _execute_node(
        self,
        node: dict[str, Any],
        *,
        org_id: UUID,
        user_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        ntype = node.get("type")
        config = node.get("config", {})

        if ntype == NodeType.AI.value:
            action_type = config.get("ai_action", "trigger_ai_agent")
        elif ntype == NodeType.WEBHOOK.value:
            action_type = "trigger_webhook"
        elif ntype == NodeType.ACTION.value:
            action_type = config.get("action_type", config.get("type", "end_workflow"))
        else:
            action_type = config.get("action_type", ntype or "end_workflow")

        params = {**config, "_action_type": action_type}
        return await action_registry.execute(
            action_type,
            params,
            org_id=org_id,
            user_id=user_id,
            context=context,
        )

    def _build_adjacency(self, edges: list[dict]) -> dict[str, list[dict]]:
        adj: dict[str, list[dict]] = {}
        for edge in edges:
            adj.setdefault(edge.get("source"), []).append(edge)
        return adj

    def _next_node(
        self,
        adjacency: dict[str, list[dict]],
        current: str,
        context: dict[str, Any],
        branch: str | None = None,
    ) -> str | None:
        edges = adjacency.get(current, [])
        if not edges:
            return None
        if branch:
            for edge in edges:
                label = (edge.get("label") or edge.get("condition", {}).get("branch", "")).lower()
                if label == branch:
                    return edge.get("target")
        for edge in edges:
            cond = edge.get("condition")
            if cond and not evaluate_condition(cond, context):
                continue
            return edge.get("target")
        return edges[0].get("target") if edges else None
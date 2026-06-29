from __future__ import annotations

from typing import Any

from backend.app.workflows.constants import NodeType


class WorkflowCompiler:
    """Compiles visual canvas or linear steps into an execution plan."""

    def compile(
        self,
        *,
        trigger_type: str,
        trigger_config: dict[str, Any],
        canvas: dict[str, Any] | None = None,
        steps: list[dict] | None = None,
    ) -> dict[str, Any]:
        if canvas and canvas.get("nodes"):
            return self._compile_canvas(trigger_type, trigger_config, canvas)
        return self._compile_steps(trigger_type, trigger_config, steps or [])

    def _compile_canvas(
        self,
        trigger_type: str,
        trigger_config: dict[str, Any],
        canvas: dict[str, Any],
    ) -> dict[str, Any]:
        nodes = {n.get("key") or n.get("id"): n for n in canvas.get("nodes", [])}
        edges = canvas.get("edges", [])
        adjacency: dict[str, list[dict]] = {}
        for edge in edges:
            src = edge.get("source")
            adjacency.setdefault(src, []).append(edge)

        trigger_node = next(
            (n for n in canvas.get("nodes", []) if n.get("type") == NodeType.TRIGGER.value),
            None,
        )
        entry_key = (trigger_node.get("key") or trigger_node.get("id")) if trigger_node else None

        execution_nodes: list[dict[str, Any]] = []
        visited: set[str] = set()

        def walk(key: str | None) -> None:
            if not key or key in visited:
                return
            visited.add(key)
            node = nodes.get(key)
            if not node:
                return
            execution_nodes.append({
                "key": key,
                "type": node.get("type"),
                "label": node.get("label"),
                "config": node.get("config", {}),
            })
            for edge in adjacency.get(key, []):
                walk(edge.get("target"))

        walk(entry_key)

        return {
            "version": 1,
            "trigger": {"type": trigger_type, "config": trigger_config},
            "entry_node": entry_key,
            "nodes": execution_nodes,
            "edges": edges,
            "variables": canvas.get("variables", {}),
            "graph": True,
        }

    def _compile_steps(
        self,
        trigger_type: str,
        trigger_config: dict[str, Any],
        steps: list[dict],
    ) -> dict[str, Any]:
        nodes = []
        edges = []
        prev_key = "trigger"

        nodes.append({
            "key": "trigger",
            "type": NodeType.TRIGGER.value,
            "label": trigger_type,
            "config": trigger_config,
        })

        for i, step in enumerate(steps):
            key = step.get("id") or f"step_{i}"
            nodes.append({
                "key": key,
                "type": step.get("type", NodeType.ACTION.value),
                "label": step.get("label"),
                "config": step.get("config") or step.get("params") or {},
            })
            edges.append({"source": prev_key, "target": key})
            prev_key = key

        nodes.append({"key": "end", "type": NodeType.END.value, "label": "End", "config": {}})
        edges.append({"source": prev_key, "target": "end"})

        return {
            "version": 1,
            "trigger": {"type": trigger_type, "config": trigger_config},
            "entry_node": "trigger",
            "nodes": nodes,
            "edges": edges,
            "variables": {},
            "graph": False,
        }
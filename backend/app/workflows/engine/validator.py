from __future__ import annotations

from typing import Any

from backend.app.workflows.constants import NodeType


class WorkflowValidator:
    """Validates workflow canvas and linear step definitions."""

    VALID_NODE_TYPES = {t.value for t in NodeType}

    def validate(self, *, canvas: dict[str, Any] | None, steps: list[dict] | None, trigger_type: str) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []

        if not trigger_type:
            errors.append("trigger_type is required")

        if canvas and canvas.get("nodes"):
            canvas_errors, canvas_warnings = self._validate_canvas(canvas)
            errors.extend(canvas_errors)
            warnings.extend(canvas_warnings)
        elif steps:
            errors.extend(self._validate_steps(steps))
        else:
            warnings.append("No canvas or steps defined; workflow will only support manual trigger")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_canvas(self, canvas: dict[str, Any]) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        nodes = canvas.get("nodes", [])
        edges = canvas.get("edges", [])

        if not nodes:
            errors.append("Canvas must contain at least one node")
            return errors, warnings

        node_keys = set()
        trigger_count = 0
        end_count = 0

        for node in nodes:
            key = node.get("key") or node.get("id")
            if not key:
                errors.append("Node missing key/id")
                continue
            if key in node_keys:
                errors.append(f"Duplicate node key: {key}")
            node_keys.add(key)

            ntype = node.get("type", "")
            if ntype not in self.VALID_NODE_TYPES:
                errors.append(f"Invalid node type '{ntype}' on node '{key}'")
            if ntype == NodeType.TRIGGER.value:
                trigger_count += 1
            if ntype == NodeType.END.value:
                end_count += 1

        if trigger_count == 0:
            errors.append("Workflow must have exactly one trigger node")
        elif trigger_count > 1:
            warnings.append(f"Multiple trigger nodes ({trigger_count}); first will be used")

        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src not in node_keys:
                errors.append(f"Edge source '{src}' not found")
            if tgt not in node_keys:
                errors.append(f"Edge target '{tgt}' not found")

        reachable = self._reachable_nodes(nodes, edges)
        orphan = node_keys - reachable
        if orphan:
            errors.append(f"Orphan nodes not connected to trigger: {', '.join(sorted(orphan))}")

        if end_count == 0:
            errors.append("Workflow should have at least one end node")

        return errors, warnings

    def _validate_steps(self, steps: list[dict]) -> list[str]:
        errors: list[str] = []
        if not steps:
            errors.append("Steps array is empty")
        for i, step in enumerate(steps):
            if not step.get("type"):
                errors.append(f"Step {i} missing type")
        return errors

    def _reachable_nodes(self, nodes: list[dict], edges: list[dict]) -> set[str]:
        keys = {n.get("key") or n.get("id") for n in nodes}
        adj: dict[str, list[str]] = {k: [] for k in keys if k}
        for edge in edges:
            src, tgt = edge.get("source"), edge.get("target")
            if src in adj and tgt:
                adj[src].append(tgt)

        trigger_keys = [
            n.get("key") or n.get("id")
            for n in nodes
            if n.get("type") == NodeType.TRIGGER.value
        ]
        if not trigger_keys:
            return set()

        visited: set[str] = set()
        stack = [trigger_keys[0]]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            stack.extend(adj.get(cur, []))
        return visited
"""Lightweight Python SDK for Workflow API."""
from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx


class WorkflowClient:
    def __init__(self, base_url: str, api_key: str | None = None, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self._headers: dict[str, str] = {}
        if api_key:
            self._headers["X-API-Key"] = api_key
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, headers=self._headers, timeout=30)

    def list_workflows(self, *, page: int = 1, is_active: bool | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page}
        if is_active is not None:
            params["is_active"] = is_active
        with self._client() as c:
            r = c.get("/workflows", params=params)
            r.raise_for_status()
            return r.json()

    def create_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._client() as c:
            r = c.post("/workflows", json=payload)
            r.raise_for_status()
            return r.json()

    def execute(
        self,
        workflow_id: UUID | str,
        *,
        entity_type: str | None = None,
        entity_id: UUID | str | None = None,
        payload: dict[str, Any] | None = None,
        async_mode: bool = True,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"async_mode": async_mode, "payload": payload or {}}
        if entity_type:
            body["entity_type"] = entity_type
        if entity_id:
            body["entity_id"] = str(entity_id)
        with self._client() as c:
            r = c.post(f"/workflows/{workflow_id}/execute", json=body)
            r.raise_for_status()
            return r.json()

    def get_execution(self, execution_id: UUID | str) -> dict[str, Any]:
        with self._client() as c:
            r = c.get(f"/workflows/executions/{execution_id}")
            r.raise_for_status()
            return r.json()

    def list_templates(self, category: str | None = None) -> dict[str, Any]:
        params = {"category": category} if category else {}
        with self._client() as c:
            r = c.get("/workflows/templates", params=params)
            r.raise_for_status()
            return r.json()
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable
from uuid import UUID

logger = logging.getLogger(__name__)

ActionHandler = Callable[..., Awaitable[dict[str, Any]]]


class ActionRegistry:
    """Registry of workflow action executors."""

    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}
        self._register_defaults()

    def register(self, action_type: str, handler: ActionHandler) -> None:
        self._handlers[action_type] = handler

    def get(self, action_type: str) -> ActionHandler | None:
        return self._handlers.get(action_type)

    async def execute(
        self,
        action_type: str,
        params: dict[str, Any],
        *,
        org_id: UUID,
        user_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        handler = self.get(action_type)
        if not handler:
            return {"status": "skipped", "reason": f"unknown_action:{action_type}"}
        return await handler(params=params, org_id=org_id, user_id=user_id, context=context)

    def _register_defaults(self) -> None:
        for action in (
            "create_lead", "update_lead", "delete_lead",
            "create_company", "update_company", "assign_owner",
            "create_task", "create_activity", "create_note",
            "create_deal", "update_deal",
            "send_email", "send_sms", "send_whatsapp", "send_notification",
            "trigger_ai_agent", "verify_email", "verify_phone",
            "run_discovery", "enrich_company", "enrich_contact",
            "generate_summary", "generate_sales_email",
            "export_csv", "import_csv", "push_to_crm",
            "call_rest_api", "call_graphql", "execute_sql",
            "generate_pdf", "upload_file", "store_document",
            "run_sub_workflow", "trigger_webhook",
            "delay", "wait_for_approval", "wait_for_event", "end_workflow",
            "score_entity", "send_notification",
            "research_company", "research_contact", "summarize_company",
            "summarize_contact", "generate_outreach_email", "generate_followup",
            "generate_meeting_brief", "recommend_next_action", "score_lead",
            "rank_prospects", "classify_industry", "extract_structured_data",
            "translate_content", "summarize_documents", "categorize_records",
            "duplicate_detection", "intent_classification",
        ):
            self.register(action, self._noop_action)

    async def _noop_action(
        self,
        *,
        params: dict[str, Any],
        org_id: UUID,
        user_id: UUID | None,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        action = params.get("_action_type", "unknown")
        logger.info("Workflow action stub: %s org=%s", action, org_id)
        return {"status": "completed", "action": action, "params": params, "stub": True}


action_registry = ActionRegistry()
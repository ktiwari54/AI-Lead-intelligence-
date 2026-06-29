from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from backend.app.workflows.constants import OrchestrationMode
from backend.app.workflows.orchestration import MODE_PROFILES, get_dispatcher_for_mode

logger = logging.getLogger(__name__)


class HybridOrchestrator:
    """
    Routes workflow executions through mode-specific dispatch paths.

    | Mode              | Dispatcher       | When it runs                          |
    |-------------------|------------------|---------------------------------------|
    | event_driven      | event_bus        | Domain events (lead.created, etc.)    |
    | scheduled         | celery_beat      | Cron / schedule table                 |
    | human_in_the_loop | approval_engine  | Event + pause at approval gates       |
    """

    async def dispatch(
        self,
        mode: OrchestrationMode,
        *,
        workflow_id: UUID,
        org_id: UUID,
        execution_id: UUID,
        trigger_data: dict[str, Any],
        async_mode: bool = True,
    ) -> dict[str, Any]:
        profile = MODE_PROFILES[mode]
        dispatcher = get_dispatcher_for_mode(mode)

        logger.info(
            "Dispatching %s orchestration workflow=%s execution=%s via %s",
            mode.value,
            workflow_id,
            execution_id,
            dispatcher,
        )

        if async_mode:
            from backend.workers.tasks.workflows import run_workflow_execution

            run_workflow_execution.delay(
                str(execution_id),
                str(org_id),
                mode.value,
            )
            return {
                "execution_id": str(execution_id),
                "status": "pending",
                "orchestration_mode": mode.value,
                "dispatcher": dispatcher,
                "supports_resume": profile.supports_resume,
            }

        return {
            "execution_id": str(execution_id),
            "status": "running",
            "orchestration_mode": mode.value,
            "dispatcher": dispatcher,
            "supports_resume": profile.supports_resume,
        }

    def should_process_event(self, mode: OrchestrationMode) -> bool:
        return mode in (OrchestrationMode.EVENT_DRIVEN, OrchestrationMode.HUMAN_IN_THE_LOOP)

    def should_process_schedule(self, mode: OrchestrationMode) -> bool:
        return mode == OrchestrationMode.SCHEDULED

    def execution_status_on_approval_wait(self, mode: OrchestrationMode) -> str:
        if mode == OrchestrationMode.HUMAN_IN_THE_LOOP:
            return "waiting_approval"
        return "waiting"


hybrid_orchestrator = HybridOrchestrator()
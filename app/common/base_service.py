"""Base service class providing credit and event helpers."""
from uuid import UUID

from app.core.events import DomainEvent, event_bus
from app.core.logging import get_logger


class BaseService:
    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    async def publish(self, event: DomainEvent) -> None:
        await event_bus.publish(event)

    async def deduct_credits(
        self,
        session,
        org_id: UUID,
        amount: int,
        description: str,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
    ) -> None:
        from sqlalchemy import text
        # Get current balance from organizations table
        result = await session.execute(
            text("SELECT credits_balance FROM auth.organizations WHERE id = :id"),
            {"id": str(org_id)},
        )
        row = result.fetchone()
        if row is None:
            raise ValueError("Organization not found")
        balance_before = row[0]
        if balance_before < amount:
            from app.core.exceptions import InsufficientCreditsError
            raise InsufficientCreditsError(f"Need {amount} credits, have {balance_before}")
        balance_after = balance_before - amount
        await session.execute(
            text("UPDATE auth.organizations SET credits_balance = :bal WHERE id = :id"),
            {"bal": balance_after, "id": str(org_id)},
        )
        from app.core.events import CreditDeducted
        await self.publish(
            CreditDeducted(
                org_id=org_id,
                payload={
                    "amount": amount,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                    "description": description,
                },
            )
        )

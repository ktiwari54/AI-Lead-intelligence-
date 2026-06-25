from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.enrichment import EmailVerification
from app.models.contacts import Contact
from app.core.exceptions import NotFoundError
from app.enrichment.schemas import EmailVerifyRequest, EmailVerifyResponse


async def verify_email(data: EmailVerifyRequest, db: AsyncSession) -> EmailVerifyResponse:
    contact = await db.get(Contact, data.contact_id)
    if not contact:
        raise NotFoundError("Contact not found")

    # Dispatch to enrichment_worker for async processing; return immediate stub
    verification = EmailVerification(
        contact_id=data.contact_id,
        email=data.email,
        status="pending",
        provider="queue",
    )
    db.add(verification)
    await db.flush()

    # Enqueue async task
    try:
        from workers.enrichment_worker import verify_email_task
        verify_email_task.delay(str(data.contact_id), data.email)
    except Exception:
        pass  # graceful if worker not running

    return EmailVerifyResponse(email=data.email, status="pending")

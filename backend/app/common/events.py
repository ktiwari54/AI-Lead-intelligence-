from enum import StrEnum


class DomainEvent(StrEnum):
    # Company events
    COMPANY_CREATED = "company.created"
    COMPANY_UPDATED = "company.updated"
    COMPANY_DELETED = "company.deleted"
    COMPANY_ENRICHED = "company.enriched"

    # Contact events
    CONTACT_CREATED = "contact.created"
    CONTACT_UPDATED = "contact.updated"
    CONTACT_DELETED = "contact.deleted"
    CONTACT_ENRICHED = "contact.enriched"

    # Lead / AI events
    LEAD_SCORED = "lead.scored"
    LEAD_CREATED = "lead.created"

    # Search events
    SEARCH_COMPLETED = "search.completed"
    SEARCH_SAVED = "search.saved"

    # Export / Import events
    EXPORT_GENERATED = "export.generated"
    IMPORT_COMPLETED = "import.completed"

    # Notification events
    NOTIFICATION_SENT = "notification.sent"

    # Connector events
    CONNECTOR_STARTED = "connector.started"
    CONNECTOR_FINISHED = "connector.finished"
    CONNECTOR_FAILED = "connector.failed"

    # Enrichment events
    EMAIL_VERIFIED = "email.verified"
    PHONE_VALIDATED = "phone.validated"

    # Workflow events
    WORKFLOW_EXECUTED = "workflow.executed"
    WORKFLOW_FAILED = "workflow.failed"

    # Auth / user events
    USER_REGISTERED = "user.registered"
    USER_LOGGED_IN = "user.logged_in"

    # Billing events
    SUBSCRIPTION_UPDATED = "subscription.updated"
    CREDITS_CONSUMED = "credits.consumed"
    CREDITS_ADDED = "credits.added"

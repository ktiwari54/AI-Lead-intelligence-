"""
Domain event definitions for the AI Lead Intelligence Platform.

Events are the immutable record of what happened in the system.
They differ from audit logs in that:
- Events represent business-meaningful state transitions
- Events can be replayed to rebuild derived state
- Events are the source of truth; DB tables are projections
- Consumers can subscribe to events for async side-effects

Event naming convention: {AggregateType}.{PastTenseVerb}
e.g., Contact.Created, Deal.StageChanged, Subscription.Upgraded
"""
from __future__ import annotations
from enum import StrEnum


class DomainEvent(StrEnum):
    # Organization events
    ORGANIZATION_CREATED = "Organization.Created"
    ORGANIZATION_UPDATED = "Organization.Updated"
    ORGANIZATION_SUSPENDED = "Organization.Suspended"

    # User events
    USER_REGISTERED = "User.Registered"
    USER_LOGGED_IN = "User.LoggedIn"
    USER_LOGGED_OUT = "User.LoggedOut"
    USER_PASSWORD_CHANGED = "User.PasswordChanged"
    USER_DEACTIVATED = "User.Deactivated"
    USER_ROLE_ASSIGNED = "User.RoleAssigned"
    API_KEY_CREATED = "ApiKey.Created"
    API_KEY_REVOKED = "ApiKey.Revoked"

    # Company events
    COMPANY_CREATED = "Company.Created"
    COMPANY_UPDATED = "Company.Updated"
    COMPANY_DELETED = "Company.Deleted"
    COMPANY_ENRICHED = "Company.Enriched"
    COMPANY_MERGED = "Company.Merged"
    COMPANY_LOCATION_SET = "Company.LocationSet"

    # Contact events
    CONTACT_CREATED = "Contact.Created"
    CONTACT_UPDATED = "Contact.Updated"
    CONTACT_DELETED = "Contact.Deleted"
    CONTACT_EMAIL_VERIFIED = "Contact.EmailVerified"
    CONTACT_ENRICHED = "Contact.Enriched"
    CONTACT_ADDED_TO_LIST = "Contact.AddedToList"
    CONTACT_REMOVED_FROM_LIST = "Contact.RemovedFromList"

    # Lead scoring events
    LEAD_SCORED = "Lead.Scored"
    LEAD_SCORE_THRESHOLD_CROSSED = "Lead.ScoreThresholdCrossed"
    EMBEDDING_GENERATED = "Lead.EmbeddingGenerated"

    # Search events
    SEARCH_EXECUTED = "Search.Executed"
    SEARCH_SAVED = "Search.Saved"

    # CRM events
    DEAL_CREATED = "Deal.Created"
    DEAL_STAGE_CHANGED = "Deal.StageChanged"
    DEAL_VALUE_CHANGED = "Deal.ValueChanged"
    DEAL_WON = "Deal.Won"
    DEAL_LOST = "Deal.Lost"
    DEAL_DELETED = "Deal.Deleted"
    TASK_CREATED = "Task.Created"
    TASK_COMPLETED = "Task.Completed"
    TASK_OVERDUE = "Task.Overdue"
    NOTE_CREATED = "Note.Created"
    ACTIVITY_LOGGED = "Activity.Logged"

    # Billing events
    SUBSCRIPTION_CREATED = "Subscription.Created"
    SUBSCRIPTION_UPGRADED = "Subscription.Upgraded"
    SUBSCRIPTION_DOWNGRADED = "Subscription.Downgraded"
    SUBSCRIPTION_CANCELED = "Subscription.Canceled"
    SUBSCRIPTION_RENEWED = "Subscription.Renewed"
    CREDITS_DEDUCTED = "Credits.Deducted"
    CREDITS_ADDED = "Credits.Added"
    CREDITS_EXHAUSTED = "Credits.Exhausted"
    PAYMENT_SUCCEEDED = "Payment.Succeeded"
    PAYMENT_FAILED = "Payment.Failed"

    # Export/Import events
    EXPORT_REQUESTED = "Export.Requested"
    EXPORT_COMPLETED = "Export.Completed"
    EXPORT_FAILED = "Export.Failed"
    IMPORT_STARTED = "Import.Started"
    IMPORT_COMPLETED = "Import.Completed"

    # Integration events
    CONNECTOR_CONNECTED = "Connector.Connected"
    CONNECTOR_DISCONNECTED = "Connector.Disconnected"
    CONNECTOR_HEALTH_CHANGED = "Connector.HealthChanged"

    # System events
    FEATURE_FLAG_CHANGED = "FeatureFlag.Changed"
    SYSTEM_SETTING_CHANGED = "SystemSetting.Changed"

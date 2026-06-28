# Phase 3 — Module Specifications

**Version 3.0** | Per-module use cases, DTOs, dependencies, and acceptance criteria.

---

## Module Specification Template

Each module below includes:
- **Responsibility** — bounded context scope
- **Aggregates** — DDD aggregate roots
- **Use Cases** — application service methods
- **Key DTOs** — Pydantic request/response schemas
- **Dependencies** — upstream/downstream modules
- **Events Published** — domain events emitted
- **Events Consumed** — events this module reacts to
- **Acceptance Criteria** — definition of done

---

## 1. Auth Module

**Path:** `app/auth/`

### Responsibility
Identity verification, session management, OAuth flows, 2FA, password lifecycle.

### Aggregates
- `UserSession`, `RefreshToken`, `MagicLinkToken`, `PasswordResetToken`

### Use Cases

| Method | Input | Output | Side Effects |
|--------|-------|--------|--------------|
| `register` | `RegisterRequest` | `TokenResponse` | Create user + org, publish `user.registered` |
| `login` | `LoginRequest` | `TokenResponse` | Create session, audit log |
| `refresh` | `RefreshRequest` | `TokenResponse` | Rotate refresh token |
| `logout` | `RefreshRequest` | void | Revoke refresh token |
| `oauth_callback` | `OAuthCallbackRequest` | `TokenResponse` | Link/create user |
| `setup_2fa` | `user_id` | `TwoFactorSetupResponse` | Store TOTP secret (encrypted) |
| `verify_2fa` | `TwoFactorVerifyRequest` | void | Enable 2FA flag |
| `forgot_password` | `ForgotPasswordRequest` | void | Send reset email |
| `reset_password` | `ResetPasswordRequest` | void | Revoke all sessions |
| `list_sessions` | `user_id` | `list[SessionResponse]` | — |
| `revoke_session` | `session_id` | void | — |

### Key DTOs

```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=100)
    organization_name: str = Field(min_length=2, max_length=100)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

### Dependencies
- **Downstream:** Users (create user), Organizations (create org)
- **Infrastructure:** Redis (lockout, magic links), SMTP (emails)

### Events Published
`user.registered`, `user.logged_in`, `user.password_reset`

### Acceptance Criteria
- [ ] JWT access token expires in 60 min
- [ ] Refresh token rotation on every refresh
- [ ] Account lockout after 5 failed attempts
- [ ] OAuth Google + Microsoft flows complete
- [ ] 2FA TOTP setup and verification
- [ ] All tokens stored as hashes in DB

---

## 2. Organizations Module

**Path:** `app/organizations/`

### Responsibility
Multi-tenant organization management, plan limits, tenant settings.

### Aggregates
- `Organization`

### Use Cases

| Method | Input | Output |
|--------|-------|--------|
| `get_current` | `org_id` | `OrganizationResponse` |
| `update` | `UpdateOrgRequest` | `OrganizationResponse` |
| `get_usage` | `org_id` | `UsageResponse` |
| `check_credit_balance` | `org_id`, `amount` | `bool` |
| `consume_credits` | `org_id`, `amount`, `reason` | `CreditTransaction` |

### Key DTOs

```python
class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: Literal["free", "starter", "pro", "enterprise"]
    monthly_credits: int
    credits_used: int
    credits_remaining: int
    settings: OrganizationSettings
    created_at: datetime

class OrganizationSettings(BaseModel):
    icp_industries: list[str] = []
    default_country: str | None = None
    timezone: str = "UTC"
```

### Dependencies
- **Upstream:** Auth (tenant context)
- **Downstream:** Billing (plan info)

### Events Published
`organization.updated`, `organization.credits_consumed`

### Acceptance Criteria
- [ ] Slug auto-generated from name, unique globally
- [ ] Credit consumption atomic (DB transaction)
- [ ] Plan limits enforced via `BillingPort`

---

## 3. Users Module

**Path:** `app/users/`

### Responsibility
User lifecycle, RBAC, API key management.

### Aggregates
- `User`, `Role`, `Permission`, `APIKey`

### Use Cases

| Method | Permission Required |
|--------|---------------------|
| `get_me` | Authenticated |
| `update_me` | Authenticated |
| `list_users` | `users:read` |
| `create_user` | `users:write` |
| `update_user` | `users:write` |
| `delete_user` | `users:delete` |
| `list_roles` | `users:read` |
| `create_role` | `users:admin` |
| `create_api_key` | `api_keys:write` |
| `revoke_api_key` | `api_keys:write` |
| `resolve_permissions` | Internal |

### Key DTOs

```python
class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    organization_id: UUID
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime

class APIKeyCreateRequest(BaseModel):
    name: str = Field(max_length=100)
    scopes: list[str]
    expires_at: datetime | None = None

class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
```

### Dependencies
- **Upstream:** Auth, Organizations
- **Infrastructure:** Redis (permission cache)

### Events Published
`user.created`, `user.updated`, `user.deleted`, `api_key.created`, `api_key.revoked`

### Events Consumed
`user.registered` → finalize user setup

### Acceptance Criteria
- [ ] Permission cache invalidated on role change
- [ ] API key shown only once on creation
- [ ] API key scopes enforced on developer API routes

---

## 4. Companies Module

**Path:** `app/companies/`

### Responsibility
Company CRUD, intelligence, merge, technology detection, import/export.

### Aggregates
- `Company`, `CompanyTechnology`, `CompanySocialProfile`

### Use Cases

| Method | Credits | Events |
|--------|---------|--------|
| `create` | 0 | `company.created` |
| `update` | 0 | `company.updated` |
| `delete` | 0 | `company.deleted` |
| `merge` | 0 | `company.merged` |
| `search` | 0 | — |
| `get_intelligence` | 0 | — |
| `detect_technology` | 2 | triggers worker |
| `get_summary` | 1 | AI summary |
| `get_timeline` | 0 | — |
| `import_companies` | 1/row | `import.started` |
| `export_companies` | 0 | `export.requested` |
| `find_duplicates` | 0 | — |

### Key DTOs

```python
class CreateCompanyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    domain: DomainStr | None = None
    industry: str | None = None
    country: CountryCode | None = None
    city: str | None = None
    employee_count: int | None = Field(None, ge=0)
    annual_revenue: int | None = Field(None, ge=0)
    description: str | None = None
    technologies: list[str] = []
    social_links: dict[str, str] = {}

class CompanyResponse(BaseModel):
    id: UUID
    name: str
    domain: str | None
    industry: str | None
    country: str | None
    city: str | None
    employee_count: int | None
    annual_revenue: int | None
    lead_score: float | None
    technologies: list[str]
    social_links: dict[str, str]
    created_at: datetime
    updated_at: datetime

class MergeCompaniesRequest(BaseModel):
    survivor_id: UUID
    duplicate_ids: list[UUID] = Field(min_length=1)
    strategy: Literal["keep_highest_score", "keep_most_complete"] = "keep_highest_score"
```

### Dependencies
- **Upstream:** Auth, Organizations, Billing
- **Downstream:** Contacts, AI, Enrichment, Search, CRM
- **Infrastructure:** CompanyRepository, OpenSearch, S3

### Events Published
`company.created`, `company.updated`, `company.merged`, `company.deleted`

### Events Consumed
`lead.scored` → update company lead_score
`connector.finished` → merge enrichment data

### Acceptance Criteria
- [ ] Duplicate domain rejected within org (409)
- [ ] Merge reassigns all contacts to survivor
- [ ] Soft delete cascades to search index removal
- [ ] Spatial search via PostGIS

---

## 5. Contacts Module

**Path:** `app/contacts/`

### Responsibility
Contact CRUD, verification, merge, intelligence, CRM sync, notes/tags.

### Aggregates
- `Contact`, `ContactSocialProfile`, `ContactTag`

### Use Cases

| Method | Credits |
|--------|---------|
| `create` | 0 |
| `update` | 0 |
| `delete` | 0 |
| `merge` | 0 |
| `verify_email` | 1 |
| `verify_phone` | 1 |
| `get_intelligence` | 0 |
| `get_timeline` | 0 |
| `add_note` | 0 |
| `assign_tags` | 0 |
| `crm_sync` | 0 |

### Key DTOs

```python
class CreateContactRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: PhoneNumber | None = None
    company_id: UUID | None = None
    designation: str | None = None
    department: str | None = None
    seniority: Seniority | None = None
    linkedin_url: HttpUrl | None = None

class ContactResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    company_id: UUID | None
    company_name: str | None
    designation: str | None
    seniority: str | None
    lead_score: float | None
    email_verified: bool
    created_at: datetime
```

### Dependencies
- Companies, Enrichment, AI, CRM, Notifications

### Events Published
`contact.created`, `contact.updated`, `contact.merged`, `contact.deleted`

### Events Consumed
`email.verified` → update contact verification status
`lead.scored` → update contact lead_score

### Acceptance Criteria
- [ ] Email uniqueness within org
- [ ] Phone normalized to E.164
- [ ] Merge prefers verified email
- [ ] Company_id validated against org tenant

---

## 6. Search Module

**Path:** `app/search/`

### Responsibility
Structured search, AI search orchestration, history, saved searches, suggestions.

### Aggregates
- `Search`, `SearchResult`, `SavedSearch`

### Use Cases

| Method | Credits | Async |
|--------|---------|-------|
| `execute_search` | 5 | No |
| `execute_ai_search` | 10 | Yes |
| `get_search_status` | 0 | — |
| `get_history` | 0 | — |
| `create_saved_search` | 0 | — |
| `delete_saved_search` | 0 | — |
| `suggest` | 0 | — |
| `get_filter_options` | 0 | — |

### Key DTOs

```python
class SearchRequest(BaseModel):
    query: str | None = None
    filters: SearchFilters
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)

class SearchFilters(BaseModel):
    entity_type: Literal["company", "contact"]
    industry: list[str] | None = None
    country: list[str] | None = None
    state: list[str] | None = None
    employee_min: int | None = None
    employee_max: int | None = None
    technologies: list[str] | None = None
    seniority: list[str] | None = None
    lead_score_min: float | None = None

class AISearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    entity_type: Literal["company", "contact"] = "company"
    page: int = 1
    page_size: int = 25

class SearchResultItem(BaseModel):
    entity_type: str
    entity_id: UUID
    score: float
    data: dict
    source: str | None = None
    explanation: str | None = None
```

### Dependencies
- AI (NL parsing), Connectors (data sources), Billing, OpenSearch, Redis

### Events Published
`search.completed`, `search.started`

### Events Consumed
`connector.finished` → merge results into search

### Acceptance Criteria
- [ ] AI search returns 202 with search_id for async polling
- [ ] Results cached in Redis (5 min TTL)
- [ ] Saved search triggers notification on new matches (optional)
- [ ] Credit deducted before search execution

---

## 7. AI Module

**Path:** `app/ai/`

### Responsibility
Lead scoring, semantic search, recommendations, NL parsing, summaries.

### Aggregates
- `LeadScore`, `Recommendation`

### Use Cases

| Method | Credits |
|--------|---------|
| `score_contact` | 1 |
| `score_company` | 1 |
| `score_bulk` | 1/entity |
| `get_scores` | 0 |
| `semantic_search_companies` | 0 |
| `semantic_search_contacts` | 0 |
| `find_similar` | 0 |
| `get_recommendations` | 0 |
| `generate_summary` | 1 |
| `parse_natural_language` | 0 (internal) |

### Key DTOs

```python
class LeadScoreResponse(BaseModel):
    entity_type: Literal["company", "contact"]
    entity_id: UUID
    score: float = Field(ge=0, le=100)
    signals: dict[str, float]
    recommendation: Literal["pursue", "nurture", "deprioritize"]
    explanation: str | None
    scored_at: datetime
    model_version: str

class BulkScoreRequest(BaseModel):
    entity_type: Literal["company", "contact"]
    entity_ids: list[UUID] = Field(min_length=1, max_length=100)
    icp_config: ICPConfig | None = None

class ICPConfig(BaseModel):
    industries: list[str] = []
    min_employees: int | None = None
    max_employees: int | None = None
    countries: list[str] = []
    technologies: list[str] = []
    seniorities: list[str] = []

class RecommendationResponse(BaseModel):
    type: str
    action: str
    reason: str
    confidence: float
    entity_id: UUID | None = None
```

### Dependencies
- Companies, Contacts, Organizations (ICP settings), OpenAI/Anthropic, pgvector

### Events Published
`lead.scored`

### Acceptance Criteria
- [ ] Rule-based scoring works without API keys
- [ ] LLM scoring degrades gracefully on API failure
- [ ] Embeddings generated on entity create/update
- [ ] Score history retained (latest + previous)

---

## 8. Connectors Module

**Path:** `app/connectors/` (migrated from `integrations/`)

### Responsibility
Connector registry, per-org config, job orchestration, health monitoring.

### Aggregates
- `ConnectorConfig`, `ConnectorJob`

### Use Cases

| Method | Description |
|--------|-------------|
| `list_available` | Registry metadata + health status |
| `list_configs` | Org connector configurations |
| `create_config` | Store encrypted credentials |
| `update_config` | Update credentials/settings |
| `delete_config` | Remove config |
| `test_config` | Health check with stored credentials |
| `create_job` | Queue connector execution |
| `get_job` | Job status + results |
| `list_jobs` | Paginated job history |

### Key DTOs

```python
class ConnectorInfo(BaseModel):
    name: str
    display_name: str
    connector_type: str
    capabilities: list[str]
    status: Literal["healthy", "degraded", "down"]

class ConnectorConfigRequest(BaseModel):
    connector_name: str
    credentials: dict[str, str]
    settings: dict = {}
    is_active: bool = True

class ConnectorJobResponse(BaseModel):
    id: UUID
    connector_name: str
    status: Literal["queued", "running", "completed", "failed"]
    query: str | None
    result_count: int
    credits_used: int
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
```

### Dependencies
- `connectors/` implementations, Celery, Billing

### Events Published
`connector.finished`, `connector.failed`

### Acceptance Criteria
- [ ] Credentials encrypted at rest (AES-256-GCM)
- [ ] Jobs track status lifecycle
- [ ] Health check runs every 6 hours via beat
- [ ] Rate limits respected per connector

---

## 9. Enrichment Module

**Path:** `app/enrichment/`

### Responsibility
Email verification, phone validation, entity enrichment, technology detection.

### Use Cases

| Method | Credits | Async |
|--------|---------|-------|
| `verify_email` | 1 | Yes |
| `bulk_verify_emails` | 1/email | Yes |
| `verify_phone` | 1 | Yes |
| `enrich_contact` | 3 | Yes |
| `enrich_company` | 3 | Yes |
| `detect_technology` | 2 | Yes |
| `get_verification_status` | 0 | — |

### Key DTOs

```python
class EmailVerificationResponse(BaseModel):
    email: str
    status: Literal["valid", "invalid", "risky", "unknown"]
    deliverable: bool
    disposable: bool
    verified_at: datetime
    source: str

class EnrichContactRequest(BaseModel):
    contact_id: UUID
    connectors: list[str] = ["apollo", "clearbit"]
```

### Events Published
`email.verified`, `phone.verified`, `enrichment.completed`

### Events Consumed
`contact.created` → optional auto-verify

### Acceptance Criteria
- [ ] Verification results cached 24h
- [ ] Bulk verify processes in batches of 50
- [ ] Enrichment merges data into entity without overwriting verified fields

---

## 10. CRM Module

**Path:** `app/crm/`

### Responsibility
Pipeline management, deals, tasks, tags, lists, activities, external CRM sync.

### Aggregates
- `Pipeline`, `PipelineStage`, `Deal`, `Task`, `Tag`, `LeadList`, `Activity`, `Note`

### Use Cases

| Method | Permission |
|--------|------------|
| Pipeline CRUD | `crm:write` / `crm:read` |
| Deal CRUD + stage transition | `crm:write` |
| Task CRUD + complete | `crm:write` |
| Tag CRUD + assign | `crm:write` |
| List CRUD + add/remove contacts | `crm:write` |
| Activity log | `crm:write` |
| `sync_push` | `crm:sync` |
| `sync_pull` | `crm:sync` |

### Key DTOs

```python
class CreateDealRequest(BaseModel):
    title: str
    company_id: UUID | None = None
    contact_id: UUID | None = None
    pipeline_id: UUID
    stage_id: UUID
    value: Decimal | None = None
    currency: CurrencyCode = "USD"
    expected_close_date: date | None = None

class DealResponse(BaseModel):
    id: UUID
    title: str
    company_id: UUID | None
    contact_id: UUID | None
    pipeline_id: UUID
    stage_id: UUID
    stage_name: str
    value: Decimal | None
    currency: str
    status: Literal["open", "won", "lost"]
    expected_close_date: date | None
    created_at: datetime
```

### Events Published
`deal.created`, `deal.stage_changed`, `deal.won`, `deal.lost`, `task.completed`

### Events Consumed
`lead.scored` → auto-create task for high-score leads (via workflow)

### Acceptance Criteria
- [ ] Stage transitions validated against pipeline definition
- [ ] Deal value supports multi-currency
- [ ] CRM sync is bidirectional with conflict resolution (latest wins)

---

## 11. Workflows Module

**Path:** `app/workflows/` (extracted from admin)

### Responsibility
Rule-based automation: trigger → conditions → actions.

### Aggregates
- `Workflow`, `WorkflowExecution`

### Use Cases

| Method | Description |
|--------|-------------|
| `create` | Define trigger + conditions + actions |
| `update` | Modify workflow definition |
| `delete` | Soft delete workflow |
| `list` | Paginated workflow list |
| `execute_manual` | Trigger workflow on specific entity |
| `process_event` | Internal: match event to workflows |

### Key DTOs

```python
class WorkflowTrigger(BaseModel):
    event: str  # e.g. "contact.created"

class WorkflowCondition(BaseModel):
    field: str
    operator: Literal["eq", "ne", "gt", "lt", "in", "contains"]
    value: Any

class WorkflowAction(BaseModel):
    type: Literal["score_entity", "send_notification", "create_task", "add_tag", "crm_sync"]
    params: dict = {}

class CreateWorkflowRequest(BaseModel):
    name: str
    trigger: WorkflowTrigger
    conditions: list[WorkflowCondition] = []
    actions: list[WorkflowAction] = Field(min_length=1, max_length=10)
    is_active: bool = True
```

### Events Published
`workflow.executed`, `workflow.failed`

### Events Consumed
All domain events (subscriber)

### Acceptance Criteria
- [ ] Max 10 actions per workflow
- [ ] Conditions evaluated with AND logic
- [ ] Execution log retained for 90 days
- [ ] Failed actions retried once

---

## 12. Exports Module

**Path:** `app/exports/`

### Responsibility
Data export (CSV/Excel/PDF) and import (CSV/Excel/JSON) engine.

### Use Cases

| Method | Async | Credits |
|--------|-------|---------|
| `create_export` | Yes | 0 |
| `get_export` | — | 0 |
| `download_export` | — | 0 |
| `delete_export` | — | 0 |
| `create_import` | Yes | 1/row |
| `get_import_status` | — | 0 |
| `confirm_upload` | — | 0 |

### Key DTOs

```python
class CreateExportRequest(BaseModel):
    entity_type: Literal["company", "contact"]
    format: Literal["csv", "xlsx", "pdf"]
    filters: dict = {}
    columns: list[str] | None = None

class ExportResponse(BaseModel):
    id: UUID
    status: Literal["queued", "processing", "completed", "failed", "expired"]
    format: str
    row_count: int | None
    file_size_bytes: int | None
    download_url: str | None
    expires_at: datetime | None
    created_at: datetime

class CreateImportRequest(BaseModel):
    entity_type: Literal["company", "contact"]
    format: Literal["csv", "xlsx", "json"]
    file_id: UUID
    mapping: dict[str, str]
    options: ImportOptions = ImportOptions()

class ImportOptions(BaseModel):
    skip_duplicates: bool = True
    update_existing: bool = False
    batch_size: int = Field(100, ge=10, le=500)
```

### Events Published
`export.completed`, `import.completed`, `import.failed`

### Acceptance Criteria
- [ ] Export files expire after 7 days
- [ ] Import validates each row against Pydantic schema
- [ ] Error report generated for failed rows
- [ ] Max concurrent exports: 3 per org

---

## 13. Analytics Module

**Path:** `app/analytics/`

### Responsibility
Read-only dashboard metrics, funnel analysis, usage reporting.

### Use Cases
All read-only, no mutations. Data sourced from materialized views + Redis cache.

| Endpoint | Data Source |
|----------|-------------|
| `dashboard` | Materialized views |
| `lead_velocity` | `searches` + `contacts` time series |
| `score_distribution` | `lead_scores` histogram |
| `crm_funnel` | `crm_deals` by stage |
| `credits` | `credit_transactions` aggregation |

### Acceptance Criteria
- [ ] Dashboard cached 10 min in Redis
- [ ] Materialized views refreshed daily at 04:00 UTC
- [ ] All queries scoped to `organization_id`

---

## 14. Notifications Module

**Path:** `app/notifications/`

### Responsibility
In-app, email, webhook, WebSocket real-time notifications.

### Use Cases

| Method | Channel |
|--------|---------|
| `create` | Internal |
| `list` | In-app |
| `mark_read` | In-app |
| `send_email` | Email (worker) |
| `send_webhook` | Webhook (worker) |
| `broadcast_ws` | WebSocket |
| `update_preferences` | Settings |

### Events Consumed
`lead.scored`, `export.completed`, `search.completed`, `workflow.executed`

### Acceptance Criteria
- [ ] WebSocket authenticated via JWT query param
- [ ] Unread count endpoint < 50ms (cached)
- [ ] Email notifications respect user preferences

---

## 15. Billing Module

**Path:** `app/billing/`

### Responsibility
Subscription management, credit tracking, Stripe integration.

### Use Cases

| Method | Description |
|--------|-------------|
| `get_subscription` | Current plan + status |
| `create_subscription` | Stripe checkout |
| `change_plan` | Upgrade/downgrade |
| `cancel_subscription` | Cancel at period end |
| `get_credits` | Balance + usage |
| `add_credits` | Admin credit grant |
| `consume_credits` | Internal, called by other services |
| `handle_stripe_webhook` | Process Stripe events |

### Key DTOs

```python
class SubscriptionResponse(BaseModel):
    plan: str
    status: Literal["active", "past_due", "canceled", "trialing"]
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool

class CreditBalanceResponse(BaseModel):
    monthly_credits: int
    credits_used: int
    credits_remaining: int
    bonus_credits: int
```

### Events Published
`subscription.updated`, `subscription.canceled`, `credits.consumed`

### Acceptance Criteria
- [ ] Credit consumption is atomic and idempotent
- [ ] Stripe webhooks verified via signature
- [ ] Plan limits enforced before operations

---

## 16. Admin Module

**Path:** `app/admin/`

### Responsibility
Platform administration, audit logs, system settings, feature flags.

### Use Cases

| Method | Permission |
|--------|------------|
| `get_stats` | `admin:read` (superadmin) |
| `list_audit_logs` | `admin:audit` |
| `get/update_settings` | `admin:settings` |
| `get/update_feature_flags` | `admin:settings` |

### Acceptance Criteria
- [ ] Audit logs captured automatically by middleware
- [ ] Feature flags support percentage rollout
- [ ] Settings changes require admin permission

---

## Cross-Module Dependency Matrix

| Module | Depends On |
|--------|------------|
| Auth | Users, Organizations |
| Users | Organizations |
| Companies | Organizations, Billing |
| Contacts | Companies, Organizations, Billing |
| Search | Companies, Contacts, AI, Connectors, Billing |
| AI | Companies, Contacts, Organizations |
| Connectors | Billing |
| Enrichment | Contacts, Companies, Connectors, Billing |
| CRM | Companies, Contacts, Connectors |
| Workflows | All event publishers |
| Exports | Companies, Contacts, Billing |
| Analytics | All (read-only) |
| Notifications | Users |
| Billing | Organizations |
| Admin | All (read-only) |

---

*End of Phase 3 Module Specifications*
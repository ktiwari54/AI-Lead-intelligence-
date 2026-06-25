-- =============================================================================
-- Index Definitions
-- =============================================================================

BEGIN;

-- organizations
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(status);
CREATE INDEX IF NOT EXISTS idx_organizations_created_at ON organizations(created_at DESC);

-- users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_org_status ON users(organization_id, status);

-- companies
CREATE INDEX IF NOT EXISTS idx_companies_organization_id ON companies(organization_id);
CREATE INDEX IF NOT EXISTS idx_companies_domain ON companies(domain);
CREATE INDEX IF NOT EXISTS idx_companies_website ON companies(website);
CREATE INDEX IF NOT EXISTS idx_companies_industry_id ON companies(industry_id);
CREATE INDEX IF NOT EXISTS idx_companies_country_id ON companies(country_id);
CREATE INDEX IF NOT EXISTS idx_companies_city_id ON companies(city_id);
CREATE INDEX IF NOT EXISTS idx_companies_created_at ON companies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_companies_name_trgm ON companies USING gin(company_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_companies_org_deleted ON companies(organization_id) WHERE is_deleted = FALSE;

-- contacts
CREATE INDEX IF NOT EXISTS idx_contacts_organization_id ON contacts(organization_id);
CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_country_id ON contacts(country_id);
CREATE INDEX IF NOT EXISTS idx_contacts_full_name_trgm ON contacts USING gin(full_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_contacts_designation_trgm ON contacts USING gin(designation gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_contacts_department ON contacts(department);
CREATE INDEX IF NOT EXISTS idx_contacts_email_status ON contacts(email_status);
CREATE INDEX IF NOT EXISTS idx_contacts_is_decision_maker ON contacts(is_decision_maker) WHERE is_decision_maker = TRUE;
CREATE INDEX IF NOT EXISTS idx_contacts_org_deleted ON contacts(organization_id) WHERE is_deleted = FALSE;

-- searches
CREATE INDEX IF NOT EXISTS idx_searches_organization_id ON searches(organization_id);
CREATE INDEX IF NOT EXISTS idx_searches_created_by ON searches(created_by);
CREATE INDEX IF NOT EXISTS idx_searches_status ON searches(status);
CREATE INDEX IF NOT EXISTS idx_searches_created_at ON searches(created_at DESC);

-- search_results
CREATE INDEX IF NOT EXISTS idx_search_results_search_id ON search_results(search_id);
CREATE INDEX IF NOT EXISTS idx_search_results_company_id ON search_results(company_id);
CREATE INDEX IF NOT EXISTS idx_search_results_contact_id ON search_results(contact_id);

-- lead_scores
CREATE INDEX IF NOT EXISTS idx_lead_scores_contact_id ON lead_scores(contact_id);
CREATE INDEX IF NOT EXISTS idx_lead_scores_company_id ON lead_scores(company_id);
CREATE INDEX IF NOT EXISTS idx_lead_scores_overall_score ON lead_scores(overall_score DESC);

-- email_verifications
CREATE INDEX IF NOT EXISTS idx_email_verifications_contact_id ON email_verifications(contact_id);
CREATE INDEX IF NOT EXISTS idx_email_verifications_email ON email_verifications(email);

-- activities
CREATE INDEX IF NOT EXISTS idx_activities_contact_id ON activities(contact_id);
CREATE INDEX IF NOT EXISTS idx_activities_company_id ON activities(company_id);
CREATE INDEX IF NOT EXISTS idx_activities_organization_id ON activities(organization_id);
CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities(created_at DESC);

-- notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id) WHERE status = 'unread';

-- audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- credit_transactions
CREATE INDEX IF NOT EXISTS idx_credit_transactions_organization_id ON credit_transactions(organization_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_subscription_id ON credit_transactions(subscription_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at DESC);

COMMIT;

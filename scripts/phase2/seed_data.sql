-- =============================================================
-- Phase 2 Seed Data
-- =============================================================

-- -------------------------------------------------------
-- Subscription Plans
-- -------------------------------------------------------
INSERT INTO billing.subscription_plans (id, name, slug, description, price_monthly, price_annual, credits_per_month, max_users, max_searches_per_day, max_exports_per_month, features, is_active, is_public, sort_order)
VALUES
    (uuid_generate_v7(), 'Starter',      'starter',      'For individuals and small teams',       49,   470,   500,   3,    100,  10,  '{"api_access": false, "crm": false, "ai_scoring": false, "bulk_export": false}', TRUE, TRUE, 1),
    (uuid_generate_v7(), 'Professional', 'professional', 'For growing sales teams',               149,  1430,  2000,  10,   500,  50,  '{"api_access": true, "crm": true, "ai_scoring": true, "bulk_export": false}',  TRUE, TRUE, 2),
    (uuid_generate_v7(), 'Business',     'business',     'For scaling revenue organizations',     399,  3830,  8000,  50,   2000, 200, '{"api_access": true, "crm": true, "ai_scoring": true, "bulk_export": true}',   TRUE, TRUE, 3),
    (uuid_generate_v7(), 'Enterprise',   'enterprise',   'Unlimited for large enterprises',       999,  9590,  50000, 999,  10000,1000,'{"api_access": true, "crm": true, "ai_scoring": true, "bulk_export": true, "sso": true, "dedicated_support": true}', TRUE, FALSE, 4)
ON CONFLICT (slug) DO NOTHING;

-- -------------------------------------------------------
-- System Roles
-- -------------------------------------------------------
INSERT INTO auth.roles (id, organization_id, name, slug, description, level, is_system, is_active)
VALUES
    (uuid_generate_v7(), NULL, 'Super Admin',    'super_admin', 'Full platform access',           100, TRUE, TRUE),
    (uuid_generate_v7(), NULL, 'Org Owner',      'org_owner',   'Organization owner',             90,  TRUE, TRUE),
    (uuid_generate_v7(), NULL, 'Admin',          'admin',       'Organization administrator',     80,  TRUE, TRUE),
    (uuid_generate_v7(), NULL, 'Manager',        'manager',     'Team manager',                   60,  TRUE, TRUE),
    (uuid_generate_v7(), NULL, 'Member',         'member',      'Standard member',                40,  TRUE, TRUE),
    (uuid_generate_v7(), NULL, 'Viewer',         'viewer',      'Read-only access',               20,  TRUE, TRUE),
    (uuid_generate_v7(), NULL, 'API User',       'api_user',    'API-only programmatic access',   30,  TRUE, TRUE)
ON CONFLICT (slug) DO NOTHING;

-- -------------------------------------------------------
-- Permissions
-- -------------------------------------------------------
INSERT INTO auth.permissions (id, resource, action, scope, description)
VALUES
    -- Companies
    (uuid_generate_v7(), 'companies',   'read',   'org',  'View companies'),
    (uuid_generate_v7(), 'companies',   'create', 'org',  'Create companies'),
    (uuid_generate_v7(), 'companies',   'update', 'org',  'Update companies'),
    (uuid_generate_v7(), 'companies',   'delete', 'org',  'Delete companies'),
    (uuid_generate_v7(), 'companies',   'export', 'org',  'Export companies'),
    -- Contacts
    (uuid_generate_v7(), 'contacts',    'read',   'org',  'View contacts'),
    (uuid_generate_v7(), 'contacts',    'create', 'org',  'Create contacts'),
    (uuid_generate_v7(), 'contacts',    'update', 'org',  'Update contacts'),
    (uuid_generate_v7(), 'contacts',    'delete', 'org',  'Delete contacts'),
    (uuid_generate_v7(), 'contacts',    'export', 'org',  'Export contacts'),
    -- Search
    (uuid_generate_v7(), 'searches',    'read',   'org',  'Perform searches'),
    (uuid_generate_v7(), 'searches',    'create', 'org',  'Save searches'),
    (uuid_generate_v7(), 'searches',    'delete', 'org',  'Delete saved searches'),
    -- CRM
    (uuid_generate_v7(), 'deals',       'read',   'org',  'View deals'),
    (uuid_generate_v7(), 'deals',       'create', 'org',  'Create deals'),
    (uuid_generate_v7(), 'deals',       'update', 'org',  'Update deals'),
    (uuid_generate_v7(), 'deals',       'delete', 'org',  'Delete deals'),
    -- AI
    (uuid_generate_v7(), 'ai_scores',   'read',   'org',  'View AI lead scores'),
    (uuid_generate_v7(), 'ai_scores',   'create', 'org',  'Trigger AI scoring'),
    -- Reports
    (uuid_generate_v7(), 'reports',     'read',   'org',  'View analytics reports'),
    (uuid_generate_v7(), 'reports',     'export', 'org',  'Export reports'),
    -- Users
    (uuid_generate_v7(), 'users',       'read',   'org',  'View users'),
    (uuid_generate_v7(), 'users',       'create', 'org',  'Invite users'),
    (uuid_generate_v7(), 'users',       'update', 'org',  'Update users'),
    (uuid_generate_v7(), 'users',       'delete', 'org',  'Remove users'),
    -- Settings
    (uuid_generate_v7(), 'settings',    'read',   'org',  'View settings'),
    (uuid_generate_v7(), 'settings',    'update', 'org',  'Update settings'),
    -- API Keys
    (uuid_generate_v7(), 'api_keys',    'read',   'org',  'View API keys'),
    (uuid_generate_v7(), 'api_keys',    'create', 'org',  'Create API keys'),
    (uuid_generate_v7(), 'api_keys',    'delete', 'org',  'Delete API keys'),
    -- Connectors
    (uuid_generate_v7(), 'connectors',  'read',   'org',  'View connector configs'),
    (uuid_generate_v7(), 'connectors',  'create', 'org',  'Configure connectors'),
    (uuid_generate_v7(), 'connectors',  'delete', 'org',  'Remove connectors'),
    -- Billing
    (uuid_generate_v7(), 'billing',     'read',   'org',  'View billing info'),
    (uuid_generate_v7(), 'billing',     'update', 'org',  'Manage billing'),
    -- System
    (uuid_generate_v7(), 'system',      'read',   'global','View system settings'),
    (uuid_generate_v7(), 'system',      'update', 'global','Update system settings'),
    (uuid_generate_v7(), 'organizations','read',  'global','View all organizations'),
    (uuid_generate_v7(), 'organizations','update','global','Update any organization'),
    (uuid_generate_v7(), 'organizations','delete','global','Delete organizations')
ON CONFLICT DO NOTHING;

-- -------------------------------------------------------
-- Industries
-- -------------------------------------------------------
INSERT INTO core.industries (id, name, slug, naics_code)
VALUES
    (uuid_generate_v7(), 'Technology',                    'technology',                    '541500'),
    (uuid_generate_v7(), 'Software & SaaS',               'software-saas',                 '511210'),
    (uuid_generate_v7(), 'Financial Services',            'financial-services',            '522000'),
    (uuid_generate_v7(), 'Banking',                       'banking',                       '522100'),
    (uuid_generate_v7(), 'Insurance',                     'insurance',                     '524000'),
    (uuid_generate_v7(), 'Healthcare',                    'healthcare',                    '621000'),
    (uuid_generate_v7(), 'Pharmaceuticals',               'pharmaceuticals',               '325400'),
    (uuid_generate_v7(), 'Biotechnology',                 'biotechnology',                 '541711'),
    (uuid_generate_v7(), 'Retail',                        'retail',                        '441000'),
    (uuid_generate_v7(), 'E-Commerce',                    'ecommerce',                     '454110'),
    (uuid_generate_v7(), 'Manufacturing',                 'manufacturing',                 '310000'),
    (uuid_generate_v7(), 'Automotive',                    'automotive',                    '336000'),
    (uuid_generate_v7(), 'Aerospace & Defense',           'aerospace-defense',             '336400'),
    (uuid_generate_v7(), 'Energy',                        'energy',                        '211000'),
    (uuid_generate_v7(), 'Renewable Energy',              'renewable-energy',              '221100'),
    (uuid_generate_v7(), 'Real Estate',                   'real-estate',                   '531000'),
    (uuid_generate_v7(), 'Construction',                  'construction',                  '230000'),
    (uuid_generate_v7(), 'Telecommunications',            'telecommunications',            '517000'),
    (uuid_generate_v7(), 'Media & Entertainment',         'media-entertainment',           '512000'),
    (uuid_generate_v7(), 'Education',                     'education',                     '611000'),
    (uuid_generate_v7(), 'Government',                    'government',                    '921000'),
    (uuid_generate_v7(), 'Non-Profit',                    'non-profit',                    '813000'),
    (uuid_generate_v7(), 'Consulting',                    'consulting',                    '541610'),
    (uuid_generate_v7(), 'Legal Services',                'legal-services',                '541100'),
    (uuid_generate_v7(), 'Accounting & Audit',            'accounting-audit',              '541200'),
    (uuid_generate_v7(), 'Marketing & Advertising',       'marketing-advertising',         '541800'),
    (uuid_generate_v7(), 'Human Resources',               'human-resources',               '561300'),
    (uuid_generate_v7(), 'Logistics & Supply Chain',      'logistics-supply-chain',        '484000'),
    (uuid_generate_v7(), 'Food & Beverage',               'food-beverage',                 '311000'),
    (uuid_generate_v7(), 'Agriculture',                   'agriculture',                   '110000'),
    (uuid_generate_v7(), 'Mining',                        'mining',                        '210000'),
    (uuid_generate_v7(), 'Chemicals',                     'chemicals',                     '325000'),
    (uuid_generate_v7(), 'Textiles & Apparel',            'textiles-apparel',              '313000'),
    (uuid_generate_v7(), 'Hospitality & Tourism',         'hospitality-tourism',           '721000'),
    (uuid_generate_v7(), 'Sports & Recreation',           'sports-recreation',             '713000'),
    (uuid_generate_v7(), 'Art & Design',                  'art-design',                    '711500'),
    (uuid_generate_v7(), 'Research & Development',        'research-development',          '541700'),
    (uuid_generate_v7(), 'Information Technology Services','it-services',                  '541510'),
    (uuid_generate_v7(), 'Cybersecurity',                 'cybersecurity',                 '541512'),
    (uuid_generate_v7(), 'Cloud Computing',               'cloud-computing',               '518210'),
    (uuid_generate_v7(), 'Artificial Intelligence',       'artificial-intelligence',       '541519'),
    (uuid_generate_v7(), 'Data Analytics',                'data-analytics',                '541511'),
    (uuid_generate_v7(), 'Blockchain',                    'blockchain',                    '523130'),
    (uuid_generate_v7(), 'Internet of Things',            'iot',                           '334419'),
    (uuid_generate_v7(), 'Robotics & Automation',         'robotics-automation',           '333200'),
    (uuid_generate_v7(), 'Space Technology',              'space-technology',              '336415'),
    (uuid_generate_v7(), 'Clean Technology',              'clean-technology',              '221300'),
    (uuid_generate_v7(), 'Social Media',                  'social-media',                  '519130'),
    (uuid_generate_v7(), 'Gaming',                        'gaming',                        '713210'),
    (uuid_generate_v7(), 'Mobile Applications',           'mobile-applications',           '511210')
ON CONFLICT (slug) DO NOTHING;

-- -------------------------------------------------------
-- Technology Categories
-- -------------------------------------------------------
INSERT INTO core.technology_categories (id, name, slug)
VALUES
    (uuid_generate_v7(), 'CRM',                    'crm'),
    (uuid_generate_v7(), 'ERP',                    'erp'),
    (uuid_generate_v7(), 'Marketing Automation',   'marketing-automation'),
    (uuid_generate_v7(), 'Cloud Infrastructure',   'cloud-infrastructure'),
    (uuid_generate_v7(), 'Analytics & BI',         'analytics-bi'),
    (uuid_generate_v7(), 'Communication & Collaboration', 'communication-collaboration'),
    (uuid_generate_v7(), 'Security',               'security'),
    (uuid_generate_v7(), 'DevOps & CI/CD',         'devops-cicd'),
    (uuid_generate_v7(), 'Database',               'database'),
    (uuid_generate_v7(), 'E-Commerce Platform',    'ecommerce-platform'),
    (uuid_generate_v7(), 'Content Management',     'content-management'),
    (uuid_generate_v7(), 'HR & Payroll',           'hr-payroll'),
    (uuid_generate_v7(), 'Customer Support',       'customer-support'),
    (uuid_generate_v7(), 'Finance & Accounting',   'finance-accounting'),
    (uuid_generate_v7(), 'Data Integration',       'data-integration'),
    (uuid_generate_v7(), 'AI & Machine Learning',  'ai-ml'),
    (uuid_generate_v7(), 'Web Framework',          'web-framework'),
    (uuid_generate_v7(), 'Mobile Development',     'mobile-development'),
    (uuid_generate_v7(), 'Monitoring & Observability', 'monitoring-observability'),
    (uuid_generate_v7(), 'Identity & Access',      'identity-access'),
    (uuid_generate_v7(), 'CDN & Edge',             'cdn-edge'),
    (uuid_generate_v7(), 'Email Marketing',        'email-marketing'),
    (uuid_generate_v7(), 'Project Management',     'project-management'),
    (uuid_generate_v7(), 'Sales Enablement',       'sales-enablement'),
    (uuid_generate_v7(), 'Supply Chain',           'supply-chain')
ON CONFLICT (slug) DO NOTHING;

-- -------------------------------------------------------
-- Designations
-- -------------------------------------------------------
INSERT INTO core.designations (id, title, slug, level, department_hint)
VALUES
    -- C-Suite
    (uuid_generate_v7(), 'Chief Executive Officer',         'ceo',             'c_suite', NULL),
    (uuid_generate_v7(), 'Chief Operating Officer',         'coo',             'c_suite', 'Operations'),
    (uuid_generate_v7(), 'Chief Financial Officer',         'cfo',             'c_suite', 'Finance'),
    (uuid_generate_v7(), 'Chief Technology Officer',        'cto',             'c_suite', 'Engineering'),
    (uuid_generate_v7(), 'Chief Marketing Officer',         'cmo',             'c_suite', 'Marketing'),
    (uuid_generate_v7(), 'Chief Revenue Officer',           'cro',             'c_suite', 'Sales'),
    (uuid_generate_v7(), 'Chief Product Officer',           'cpo',             'c_suite', 'Product'),
    (uuid_generate_v7(), 'Chief Information Officer',       'cio',             'c_suite', 'IT'),
    (uuid_generate_v7(), 'Chief People Officer',            'chro',            'c_suite', 'HR'),
    -- VP
    (uuid_generate_v7(), 'VP of Sales',                     'vp-sales',        'vp',      'Sales'),
    (uuid_generate_v7(), 'VP of Marketing',                 'vp-marketing',    'vp',      'Marketing'),
    (uuid_generate_v7(), 'VP of Engineering',               'vp-engineering',  'vp',      'Engineering'),
    (uuid_generate_v7(), 'VP of Product',                   'vp-product',      'vp',      'Product'),
    (uuid_generate_v7(), 'VP of Finance',                   'vp-finance',      'vp',      'Finance'),
    (uuid_generate_v7(), 'VP of Operations',                'vp-operations',   'vp',      'Operations'),
    -- Director
    (uuid_generate_v7(), 'Director of Sales',               'dir-sales',       'director','Sales'),
    (uuid_generate_v7(), 'Director of Marketing',           'dir-marketing',   'director','Marketing'),
    (uuid_generate_v7(), 'Director of Engineering',         'dir-engineering', 'director','Engineering'),
    (uuid_generate_v7(), 'Director of Product',             'dir-product',     'director','Product'),
    (uuid_generate_v7(), 'Director of Finance',             'dir-finance',     'director','Finance'),
    -- Manager
    (uuid_generate_v7(), 'Sales Manager',                   'sales-manager',   'manager', 'Sales'),
    (uuid_generate_v7(), 'Marketing Manager',               'mkt-manager',     'manager', 'Marketing'),
    (uuid_generate_v7(), 'Engineering Manager',             'eng-manager',     'manager', 'Engineering'),
    (uuid_generate_v7(), 'Product Manager',                 'product-manager', 'manager', 'Product'),
    (uuid_generate_v7(), 'Account Manager',                 'account-manager', 'manager', 'Sales'),
    -- Individual
    (uuid_generate_v7(), 'Software Engineer',               'software-engineer','individual','Engineering'),
    (uuid_generate_v7(), 'Data Scientist',                  'data-scientist',  'individual','Data'),
    (uuid_generate_v7(), 'Sales Representative',            'sales-rep',       'individual','Sales'),
    (uuid_generate_v7(), 'Marketing Specialist',            'mkt-specialist',  'individual','Marketing'),
    (uuid_generate_v7(), 'Business Analyst',                'biz-analyst',     'individual','Strategy'),
    -- Senior
    (uuid_generate_v7(), 'Senior Software Engineer',        'sr-software-eng', 'senior',  'Engineering'),
    (uuid_generate_v7(), 'Senior Data Scientist',           'sr-data-scientist','senior', 'Data'),
    (uuid_generate_v7(), 'Senior Product Manager',          'sr-product-mgr',  'senior',  'Product'),
    (uuid_generate_v7(), 'Senior Sales Executive',          'sr-sales-exec',   'senior',  'Sales'),
    (uuid_generate_v7(), 'Senior Marketing Manager',        'sr-mkt-manager',  'senior',  'Marketing'),
    -- Lead
    (uuid_generate_v7(), 'Tech Lead',                       'tech-lead',       'lead',    'Engineering'),
    (uuid_generate_v7(), 'Lead Data Engineer',              'lead-data-eng',   'lead',    'Data'),
    (uuid_generate_v7(), 'Lead Product Designer',           'lead-designer',   'lead',    'Design'),
    (uuid_generate_v7(), 'Team Lead - Sales',               'sales-team-lead', 'lead',    'Sales'),
    (uuid_generate_v7(), 'Lead Business Analyst',           'lead-biz-analyst','lead',    'Strategy')
ON CONFLICT (slug) DO NOTHING;

-- -------------------------------------------------------
-- Feature Flags
-- -------------------------------------------------------
INSERT INTO system.feature_flags (id, key, description, is_enabled, rollout_percent)
VALUES
    (uuid_generate_v7(), 'ai_lead_scoring',         'AI-powered lead scoring',                TRUE,  100),
    (uuid_generate_v7(), 'semantic_search',          'Vector semantic search',                 TRUE,  100),
    (uuid_generate_v7(), 'geo_search',               'Geographic radius search',               TRUE,  100),
    (uuid_generate_v7(), 'bulk_enrich',              'Bulk enrichment via connectors',         TRUE,  80),
    (uuid_generate_v7(), 'intent_signals',           'Buyer intent signal detection',          TRUE,  50),
    (uuid_generate_v7(), 'duplicate_detection',      'AI duplicate company/contact detection', TRUE,  100),
    (uuid_generate_v7(), 'crm_sync',                 'CRM two-way sync (Salesforce/HubSpot)',  TRUE,  100),
    (uuid_generate_v7(), 'workflow_automation',      'Sales workflow automation',              TRUE,  100),
    (uuid_generate_v7(), 'advanced_analytics',       'Advanced analytics dashboards',          TRUE,  100),
    (uuid_generate_v7(), 'sso_saml',                 'SSO via SAML 2.0',                       TRUE,  100),
    (uuid_generate_v7(), 'api_v2',                   'REST API v2',                            TRUE,  100),
    (uuid_generate_v7(), 'export_parquet',           'Parquet format exports',                 FALSE, 0),
    (uuid_generate_v7(), 'real_time_alerts',         'Real-time search alerts',                TRUE,  70),
    (uuid_generate_v7(), 'contact_graph',            'Contact relationship graph',             FALSE, 10),
    (uuid_generate_v7(), 'predictive_analytics',     'Predictive churn / upsell analytics',   FALSE, 20)
ON CONFLICT (key) DO NOTHING;

-- -------------------------------------------------------
-- System Settings
-- -------------------------------------------------------
INSERT INTO system.system_settings (id, category, key, value, data_type, description)
VALUES
    (uuid_generate_v7(), 'ai',        'default_embedding_model',  '"text-embedding-3-small"', 'string',  'Default embedding model'),
    (uuid_generate_v7(), 'ai',        'default_scoring_model',    '"claude-haiku-4-5-20251001"', 'string', 'Default AI scoring model'),
    (uuid_generate_v7(), 'ai',        'embedding_dimensions',     '1536',                    'integer', 'Embedding vector dimensions'),
    (uuid_generate_v7(), 'ai',        'score_cache_ttl_hours',    '24',                      'integer', 'Lead score cache TTL in hours'),
    (uuid_generate_v7(), 'search',    'default_page_size',        '25',                      'integer', 'Default search page size'),
    (uuid_generate_v7(), 'search',    'max_page_size',            '100',                     'integer', 'Maximum search page size'),
    (uuid_generate_v7(), 'search',    'cache_ttl_minutes',        '30',                      'integer', 'Search cache TTL in minutes'),
    (uuid_generate_v7(), 'search',    'max_saved_searches',       '50',                      'integer', 'Max saved searches per org'),
    (uuid_generate_v7(), 'export',    'max_rows_per_export',      '50000',                   'integer', 'Max rows per export'),
    (uuid_generate_v7(), 'export',    'export_url_ttl_hours',     '24',                      'integer', 'Export download URL TTL'),
    (uuid_generate_v7(), 'export',    'allowed_formats',          '["csv","xlsx","json"]',   'array',   'Allowed export formats'),
    (uuid_generate_v7(), 'rate_limit','api_requests_per_minute',  '120',                     'integer', 'API rate limit per minute'),
    (uuid_generate_v7(), 'rate_limit','search_requests_per_minute','60',                     'integer', 'Search rate limit per minute'),
    (uuid_generate_v7(), 'billing',   'credit_expiry_months',     '12',                      'integer', 'Credits expire after N months'),
    (uuid_generate_v7(), 'billing',   'min_credit_purchase',      '100',                     'integer', 'Minimum credit purchase amount')
ON CONFLICT (category, key) DO NOTHING;

-- -------------------------------------------------------
-- AI Models
-- -------------------------------------------------------
INSERT INTO ai.ai_models (id, provider, model_id, model_type, display_name, input_dims, output_dims, cost_per_token, is_default, is_active)
VALUES
    (uuid_generate_v7(), 'openai',    'text-embedding-3-small',       'embedding',    'OpenAI Embedding Small',   1536, 1536, 0.00000002, TRUE,  TRUE),
    (uuid_generate_v7(), 'openai',    'text-embedding-3-large',       'embedding',    'OpenAI Embedding Large',   3072, 3072, 0.00000013, FALSE, TRUE),
    (uuid_generate_v7(), 'openai',    'gpt-4o-mini',                  'completion',   'GPT-4o Mini',              NULL, NULL, 0.00000015, FALSE, TRUE),
    (uuid_generate_v7(), 'anthropic', 'claude-haiku-4-5-20251001',    'scoring',      'Claude Haiku 4.5',         NULL, NULL, 0.00000025, TRUE,  TRUE),
    (uuid_generate_v7(), 'anthropic', 'claude-sonnet-4-6',            'completion',   'Claude Sonnet 4.6',        NULL, NULL, 0.000003,   FALSE, TRUE)
ON CONFLICT (model_id) DO NOTHING;

-- -------------------------------------------------------
-- Notification Types
-- -------------------------------------------------------
INSERT INTO notification.notification_types (id, key, display_name, channels)
VALUES
    (uuid_generate_v7(), 'welcome',               'Welcome',                    '{in_app, email}'),
    (uuid_generate_v7(), 'invite_accepted',        'Invite Accepted',            '{in_app, email}'),
    (uuid_generate_v7(), 'credit_low',             'Credits Running Low',        '{in_app, email}'),
    (uuid_generate_v7(), 'credit_exhausted',       'Credits Exhausted',          '{in_app, email}'),
    (uuid_generate_v7(), 'export_ready',           'Export Ready',               '{in_app, email}'),
    (uuid_generate_v7(), 'import_complete',        'Import Complete',            '{in_app, email}'),
    (uuid_generate_v7(), 'import_failed',          'Import Failed',              '{in_app, email}'),
    (uuid_generate_v7(), 'search_alert',           'Saved Search Alert',         '{in_app, email}'),
    (uuid_generate_v7(), 'deal_assigned',          'Deal Assigned to You',       '{in_app}'),
    (uuid_generate_v7(), 'task_due',               'Task Due Soon',              '{in_app, email}'),
    (uuid_generate_v7(), 'task_overdue',           'Task Overdue',               '{in_app, email}'),
    (uuid_generate_v7(), 'enrichment_complete',    'Enrichment Complete',        '{in_app}'),
    (uuid_generate_v7(), 'duplicate_found',        'Duplicate Detected',         '{in_app}'),
    (uuid_generate_v7(), 'score_updated',          'Lead Score Updated',         '{in_app}'),
    (uuid_generate_v7(), 'plan_upgraded',          'Plan Upgraded',              '{in_app, email}'),
    (uuid_generate_v7(), 'plan_downgraded',        'Plan Downgraded',            '{in_app, email}'),
    (uuid_generate_v7(), 'invoice_paid',           'Invoice Paid',               '{email}'),
    (uuid_generate_v7(), 'invoice_failed',         'Invoice Payment Failed',     '{in_app, email}'),
    (uuid_generate_v7(), 'security_alert',         'Security Alert',             '{in_app, email}')
ON CONFLICT (key) DO NOTHING;

-- -------------------------------------------------------
-- Countries (G20 + Major Markets)
-- -------------------------------------------------------
INSERT INTO core.countries (id, iso2, iso3, name, phone_code, currency, continent)
VALUES
    (uuid_generate_v7(), 'US', 'USA', 'United States',           '+1',    'USD', 'North America'),
    (uuid_generate_v7(), 'GB', 'GBR', 'United Kingdom',          '+44',   'GBP', 'Europe'),
    (uuid_generate_v7(), 'DE', 'DEU', 'Germany',                 '+49',   'EUR', 'Europe'),
    (uuid_generate_v7(), 'FR', 'FRA', 'France',                  '+33',   'EUR', 'Europe'),
    (uuid_generate_v7(), 'CA', 'CAN', 'Canada',                  '+1',    'CAD', 'North America'),
    (uuid_generate_v7(), 'AU', 'AUS', 'Australia',               '+61',   'AUD', 'Oceania'),
    (uuid_generate_v7(), 'JP', 'JPN', 'Japan',                   '+81',   'JPY', 'Asia'),
    (uuid_generate_v7(), 'CN', 'CHN', 'China',                   '+86',   'CNY', 'Asia'),
    (uuid_generate_v7(), 'IN', 'IND', 'India',                   '+91',   'INR', 'Asia'),
    (uuid_generate_v7(), 'BR', 'BRA', 'Brazil',                  '+55',   'BRL', 'South America'),
    (uuid_generate_v7(), 'MX', 'MEX', 'Mexico',                  '+52',   'MXN', 'North America'),
    (uuid_generate_v7(), 'KR', 'KOR', 'South Korea',             '+82',   'KRW', 'Asia'),
    (uuid_generate_v7(), 'IT', 'ITA', 'Italy',                   '+39',   'EUR', 'Europe'),
    (uuid_generate_v7(), 'ES', 'ESP', 'Spain',                   '+34',   'EUR', 'Europe'),
    (uuid_generate_v7(), 'NL', 'NLD', 'Netherlands',             '+31',   'EUR', 'Europe'),
    (uuid_generate_v7(), 'SE', 'SWE', 'Sweden',                  '+46',   'SEK', 'Europe'),
    (uuid_generate_v7(), 'NO', 'NOR', 'Norway',                  '+47',   'NOK', 'Europe'),
    (uuid_generate_v7(), 'CH', 'CHE', 'Switzerland',             '+41',   'CHF', 'Europe'),
    (uuid_generate_v7(), 'SG', 'SGP', 'Singapore',               '+65',   'SGD', 'Asia'),
    (uuid_generate_v7(), 'HK', 'HKG', 'Hong Kong',               '+852',  'HKD', 'Asia'),
    (uuid_generate_v7(), 'AE', 'ARE', 'United Arab Emirates',    '+971',  'AED', 'Middle East'),
    (uuid_generate_v7(), 'SA', 'SAU', 'Saudi Arabia',            '+966',  'SAR', 'Middle East'),
    (uuid_generate_v7(), 'IL', 'ISR', 'Israel',                  '+972',  'ILS', 'Middle East'),
    (uuid_generate_v7(), 'ZA', 'ZAF', 'South Africa',            '+27',   'ZAR', 'Africa'),
    (uuid_generate_v7(), 'NG', 'NGA', 'Nigeria',                 '+234',  'NGN', 'Africa'),
    (uuid_generate_v7(), 'EG', 'EGY', 'Egypt',                   '+20',   'EGP', 'Africa'),
    (uuid_generate_v7(), 'AR', 'ARG', 'Argentina',               '+54',   'ARS', 'South America'),
    (uuid_generate_v7(), 'CO', 'COL', 'Colombia',                '+57',   'COP', 'South America'),
    (uuid_generate_v7(), 'CL', 'CHL', 'Chile',                   '+56',   'CLP', 'South America'),
    (uuid_generate_v7(), 'ID', 'IDN', 'Indonesia',               '+62',   'IDR', 'Asia'),
    (uuid_generate_v7(), 'MY', 'MYS', 'Malaysia',                '+60',   'MYR', 'Asia'),
    (uuid_generate_v7(), 'TH', 'THA', 'Thailand',                '+66',   'THB', 'Asia'),
    (uuid_generate_v7(), 'PH', 'PHL', 'Philippines',             '+63',   'PHP', 'Asia'),
    (uuid_generate_v7(), 'VN', 'VNM', 'Vietnam',                 '+84',   'VND', 'Asia'),
    (uuid_generate_v7(), 'PK', 'PAK', 'Pakistan',                '+92',   'PKR', 'Asia'),
    (uuid_generate_v7(), 'TR', 'TUR', 'Turkey',                  '+90',   'TRY', 'Europe'),
    (uuid_generate_v7(), 'PL', 'POL', 'Poland',                  '+48',   'PLN', 'Europe'),
    (uuid_generate_v7(), 'RO', 'ROU', 'Romania',                 '+40',   'RON', 'Europe'),
    (uuid_generate_v7(), 'UA', 'UKR', 'Ukraine',                 '+380',  'UAH', 'Europe'),
    (uuid_generate_v7(), 'NZ', 'NZL', 'New Zealand',             '+64',   'NZD', 'Oceania'),
    (uuid_generate_v7(), 'IE', 'IRL', 'Ireland',                 '+353',  'EUR', 'Europe'),
    (uuid_generate_v7(), 'DK', 'DNK', 'Denmark',                 '+45',   'DKK', 'Europe'),
    (uuid_generate_v7(), 'FI', 'FIN', 'Finland',                 '+358',  'EUR', 'Europe'),
    (uuid_generate_v7(), 'PT', 'PRT', 'Portugal',                '+351',  'EUR', 'Europe'),
    (uuid_generate_v7(), 'BE', 'BEL', 'Belgium',                 '+32',   'EUR', 'Europe')
ON CONFLICT (iso2) DO NOTHING;

-- -------------------------------------------------------
-- Connectors
-- -------------------------------------------------------
INSERT INTO connector.connectors (id, name, display_name, description, connector_type, supports_search, supports_enrich, supports_sync, rate_limit_rpm, credit_cost, is_active, is_system)
VALUES
    (uuid_generate_v7(), 'apollo',      'Apollo.io',      'Sales intelligence platform',         'data',     TRUE,  TRUE,  FALSE, 60,  1, TRUE, TRUE),
    (uuid_generate_v7(), 'hunter',      'Hunter.io',      'Email finder and verifier',           'email',    TRUE,  TRUE,  FALSE, 30,  1, TRUE, TRUE),
    (uuid_generate_v7(), 'clearbit',    'Clearbit',       'Company and contact enrichment',      'data',     TRUE,  TRUE,  FALSE, 60,  2, TRUE, TRUE),
    (uuid_generate_v7(), 'zoominfo',    'ZoomInfo',       'B2B intelligence database',           'data',     TRUE,  TRUE,  FALSE, 60,  3, TRUE, TRUE),
    (uuid_generate_v7(), 'linkedin',    'LinkedIn',       'Professional network data',           'social',   FALSE, TRUE,  FALSE, 20,  5, TRUE, TRUE),
    (uuid_generate_v7(), 'salesforce',  'Salesforce CRM', 'CRM two-way sync',                   'crm',      FALSE, FALSE, TRUE,  120, 0, TRUE, TRUE),
    (uuid_generate_v7(), 'hubspot',     'HubSpot CRM',    'CRM two-way sync',                   'crm',      FALSE, FALSE, TRUE,  120, 0, TRUE, TRUE),
    (uuid_generate_v7(), 'slack',       'Slack',          'Team notifications and alerts',       'messaging',FALSE, FALSE, FALSE, 60,  0, TRUE, TRUE),
    (uuid_generate_v7(), 'sendgrid',    'SendGrid',       'Transactional email delivery',        'email',    FALSE, FALSE, FALSE, 600, 0, TRUE, TRUE),
    (uuid_generate_v7(), 'stripe',      'Stripe',         'Payment processing',                  'billing',  FALSE, FALSE, FALSE, 100, 0, TRUE, TRUE)
ON CONFLICT (name) DO NOTHING;

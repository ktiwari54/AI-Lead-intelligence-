-- =============================================================================
-- Seed Data: Reference tables (industries, countries)
-- =============================================================================

BEGIN;

-- Industries
INSERT INTO industries (id, industry_name, description) VALUES
    (uuid_generate_v4(), 'Technology', 'Software, hardware, and IT services'),
    (uuid_generate_v4(), 'SaaS', 'Software as a Service'),
    (uuid_generate_v4(), 'Financial Services', 'Banking, insurance, and fintech'),
    (uuid_generate_v4(), 'Healthcare', 'Medical devices, pharma, and health services'),
    (uuid_generate_v4(), 'E-Commerce', 'Online retail and marketplaces'),
    (uuid_generate_v4(), 'Manufacturing', 'Industrial and consumer goods'),
    (uuid_generate_v4(), 'Real Estate', 'Commercial and residential property'),
    (uuid_generate_v4(), 'Education', 'EdTech and academic institutions'),
    (uuid_generate_v4(), 'Media & Entertainment', 'Publishing, streaming, and gaming'),
    (uuid_generate_v4(), 'Logistics & Supply Chain', 'Freight, warehousing, and last-mile'),
    (uuid_generate_v4(), 'Consulting', 'Management and IT consulting'),
    (uuid_generate_v4(), 'Retail', 'Brick-and-mortar and omnichannel retail')
ON CONFLICT (industry_name) DO NOTHING;

-- Technologies
INSERT INTO technologies (id, technology_name, category, vendor) VALUES
    (uuid_generate_v4(), 'Salesforce', 'CRM', 'Salesforce'),
    (uuid_generate_v4(), 'HubSpot', 'CRM', 'HubSpot'),
    (uuid_generate_v4(), 'AWS', 'Cloud', 'Amazon'),
    (uuid_generate_v4(), 'Google Cloud', 'Cloud', 'Google'),
    (uuid_generate_v4(), 'Azure', 'Cloud', 'Microsoft'),
    (uuid_generate_v4(), 'React', 'Frontend Framework', 'Meta'),
    (uuid_generate_v4(), 'Node.js', 'Backend Runtime', 'OpenJS Foundation'),
    (uuid_generate_v4(), 'Python', 'Programming Language', 'PSF'),
    (uuid_generate_v4(), 'PostgreSQL', 'Database', 'PostgreSQL Global Development Group'),
    (uuid_generate_v4(), 'Redis', 'Cache / Queue', 'Redis Ltd'),
    (uuid_generate_v4(), 'Stripe', 'Payments', 'Stripe'),
    (uuid_generate_v4(), 'Segment', 'Analytics', 'Twilio'),
    (uuid_generate_v4(), 'Intercom', 'Customer Support', 'Intercom'),
    (uuid_generate_v4(), 'Zendesk', 'Customer Support', 'Zendesk'),
    (uuid_generate_v4(), 'Slack', 'Collaboration', 'Salesforce')
ON CONFLICT (technology_name) DO NOTHING;

-- Countries (partial list)
INSERT INTO countries (id, name, iso2, iso3, phone_code, currency, continent) VALUES
    (uuid_generate_v4(), 'United States', 'US', 'USA', '+1', 'USD', 'North America'),
    (uuid_generate_v4(), 'United Kingdom', 'GB', 'GBR', '+44', 'GBP', 'Europe'),
    (uuid_generate_v4(), 'Canada', 'CA', 'CAN', '+1', 'CAD', 'North America'),
    (uuid_generate_v4(), 'Australia', 'AU', 'AUS', '+61', 'AUD', 'Oceania'),
    (uuid_generate_v4(), 'Germany', 'DE', 'DEU', '+49', 'EUR', 'Europe'),
    (uuid_generate_v4(), 'France', 'FR', 'FRA', '+33', 'EUR', 'Europe'),
    (uuid_generate_v4(), 'India', 'IN', 'IND', '+91', 'INR', 'Asia'),
    (uuid_generate_v4(), 'Singapore', 'SG', 'SGP', '+65', 'SGD', 'Asia'),
    (uuid_generate_v4(), 'Netherlands', 'NL', 'NLD', '+31', 'EUR', 'Europe'),
    (uuid_generate_v4(), 'Brazil', 'BR', 'BRA', '+55', 'BRL', 'South America')
ON CONFLICT (iso2) DO NOTHING;

-- System Roles
INSERT INTO roles (id, name, description, is_system) VALUES
    (uuid_generate_v4(), 'admin', 'Full platform access', TRUE),
    (uuid_generate_v4(), 'member', 'Standard user access', TRUE),
    (uuid_generate_v4(), 'viewer', 'Read-only access', TRUE)
ON CONFLICT DO NOTHING;

-- System Settings
INSERT INTO system_settings (key, value, description, is_public, category) VALUES
    ('platform.name', '"AI Lead Intelligence"', 'Platform display name', TRUE, 'general'),
    ('platform.version', '"1.0.0"', 'Current platform version', TRUE, 'general'),
    ('credits.search_cost', '1', 'Credits deducted per search', FALSE, 'billing'),
    ('credits.enrichment_cost', '5', 'Credits deducted per enrichment', FALSE, 'billing'),
    ('credits.export_cost', '1', 'Credits deducted per export record', FALSE, 'billing'),
    ('scoring.model_version', '"1.0.0"', 'Active lead scoring model version', FALSE, 'ai'),
    ('email.verification_enabled', 'true', 'Enable email verification feature', FALSE, 'features')
ON CONFLICT (key) DO NOTHING;

COMMIT;

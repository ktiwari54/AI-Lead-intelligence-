#!/usr/bin/env python3
"""Seed script for AI Lead Intelligence Platform.

Usage:
    python scripts/seed/seed_data.py

Requires:
    DATABASE_URL environment variable pointing to a running PostgreSQL instance.
    All models must be importable (run from repo root or ensure PYTHONPATH is set).
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — allow running from repo root without installing the package
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# Third-party
# ---------------------------------------------------------------------------
try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

try:
    from passlib.hash import bcrypt
except ImportError:
    # Fallback — deterministic hash for dev seeds only
    import hashlib

    class bcrypt:  # type: ignore
        @staticmethod
        def hash(password: str) -> str:
            return "$2b$12$" + hashlib.sha256(password.encode()).hexdigest()[:53]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def uid() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


def days_ago(n: int) -> datetime:
    return now() - timedelta(days=n)


def days_from_now(n: int) -> datetime:
    return now() + timedelta(days=n)


def load_fixture(name: str) -> list:
    path = FIXTURES_DIR / name
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def print_step(msg: str) -> None:
    print(f"  --> {msg}")


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
async def get_connection() -> asyncpg.Connection:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set.\n"
            "Example: postgresql://postgres:password@localhost:5432/ai_lead_intelligence"
        )
    conn = await asyncpg.connect(database_url)
    return conn


# ---------------------------------------------------------------------------
# Seed: Organizations
# ---------------------------------------------------------------------------
async def seed_organizations(conn: asyncpg.Connection) -> list[dict]:
    print_section("Organizations")
    orgs = [
        {
            "id": uid(),
            "name": "Acme Corp",
            "slug": "acme-corp",
            "plan": "enterprise",
            "monthly_credits": 10000,
            "credits_used": 2340,
            "is_active": True,
            "created_at": days_ago(180),
            "updated_at": days_ago(1),
        },
        {
            "id": uid(),
            "name": "TechStartup Inc",
            "slug": "techstartup-inc",
            "plan": "growth",
            "monthly_credits": 2000,
            "credits_used": 870,
            "is_active": True,
            "created_at": days_ago(60),
            "updated_at": days_ago(2),
        },
    ]

    await conn.executemany(
        """
        INSERT INTO organizations (id, name, slug, plan, monthly_credits, credits_used, is_active, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (slug) DO NOTHING
        """,
        [
            (
                o["id"], o["name"], o["slug"], o["plan"],
                o["monthly_credits"], o["credits_used"], o["is_active"],
                o["created_at"], o["updated_at"]
            )
            for o in orgs
        ],
    )
    print_step(f"Inserted {len(orgs)} organizations")
    return orgs


# ---------------------------------------------------------------------------
# Seed: Users
# ---------------------------------------------------------------------------
async def seed_users(conn: asyncpg.Connection, orgs: list[dict]) -> list[dict]:
    print_section("Users")
    hashed_pw = bcrypt.hash("Seed@Password123")

    users = []
    templates = [
        ("admin",   "admin",   "{slug}.admin@example.com",   "{name} Admin"),
        ("manager", "manager", "{slug}.manager@example.com", "{name} Manager"),
        ("viewer",  "viewer",  "{slug}.viewer@example.com",  "{name} Viewer"),
    ]

    for org in orgs:
        for role, _label, email_tpl, name_tpl in templates:
            users.append(
                {
                    "id": uid(),
                    "organization_id": org["id"],
                    "email": email_tpl.format(slug=org["slug"]),
                    "full_name": name_tpl.format(name=org["name"]),
                    "role": role,
                    "hashed_password": hashed_pw,
                    "is_active": True,
                    "is_verified": True,
                    "last_login_at": days_ago(1),
                    "created_at": org["created_at"],
                    "updated_at": org["updated_at"],
                }
            )

    await conn.executemany(
        """
        INSERT INTO users
            (id, organization_id, email, full_name, role, hashed_password,
             is_active, is_verified, last_login_at, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
        ON CONFLICT (email) DO NOTHING
        """,
        [
            (
                u["id"], u["organization_id"], u["email"], u["full_name"],
                u["role"], u["hashed_password"], u["is_active"], u["is_verified"],
                u["last_login_at"], u["created_at"], u["updated_at"]
            )
            for u in users
        ],
    )
    print_step(f"Inserted {len(users)} users (3 per organization)")
    return users


# ---------------------------------------------------------------------------
# Seed: Subscriptions
# ---------------------------------------------------------------------------
async def seed_subscriptions(conn: asyncpg.Connection, orgs: list[dict]) -> None:
    print_section("Subscriptions")
    subscriptions = [
        {
            "id": uid(),
            "organization_id": orgs[0]["id"],
            "plan": "enterprise",
            "status": "active",
            "stripe_subscription_id": "sub_enterprise_acme_001",
            "stripe_customer_id": "cus_acme_001",
            "current_period_start": days_ago(30),
            "current_period_end": days_from_now(0),
            "created_at": days_ago(180),
            "updated_at": days_ago(30),
        },
        {
            "id": uid(),
            "organization_id": orgs[1]["id"],
            "plan": "growth",
            "status": "active",
            "stripe_subscription_id": "sub_growth_techstartup_001",
            "stripe_customer_id": "cus_techstartup_001",
            "current_period_start": days_ago(15),
            "current_period_end": days_from_now(15),
            "created_at": days_ago(60),
            "updated_at": days_ago(15),
        },
    ]

    await conn.executemany(
        """
        INSERT INTO subscriptions
            (id, organization_id, plan, status, stripe_subscription_id, stripe_customer_id,
             current_period_start, current_period_end, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        ON CONFLICT DO NOTHING
        """,
        [
            (
                s["id"], s["organization_id"], s["plan"], s["status"],
                s["stripe_subscription_id"], s["stripe_customer_id"],
                s["current_period_start"], s["current_period_end"],
                s["created_at"], s["updated_at"]
            )
            for s in subscriptions
        ],
    )
    print_step(f"Inserted {len(subscriptions)} subscriptions")


# ---------------------------------------------------------------------------
# Seed: Credit Transactions
# ---------------------------------------------------------------------------
async def seed_credit_transactions(
    conn: asyncpg.Connection, orgs: list[dict], users: list[dict]
) -> None:
    print_section("Credit Transactions")

    def org_admin(org_id: str) -> str:
        return next(u["id"] for u in users if u["organization_id"] == org_id and u["role"] == "admin")

    transactions = []
    for org in orgs:
        admin_id = org_admin(org["id"])
        # Initial credit purchase
        transactions.append(
            (uid(), org["id"], admin_id, org["monthly_credits"], "purchase",
             "Monthly plan credit allocation", None, days_ago(30))
        )
        # Simulated usage events
        for i, (amount, desc) in enumerate(
            [(-50, "Search: SaaS companies in US"),
             (-30, "Contact export batch"),
             (-120, "AI scoring: 100 companies"),
             (-200, "Bulk contact enrichment"),
             (-10, "CRM sync: HubSpot")]
        ):
            transactions.append(
                (uid(), org["id"], admin_id, amount, "usage", desc, None, days_ago(25 - i * 4))
            )

    await conn.executemany(
        """
        INSERT INTO credit_transactions
            (id, organization_id, user_id, amount, type, description, reference_id, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        ON CONFLICT DO NOTHING
        """,
        transactions,
    )
    print_step(f"Inserted {len(transactions)} credit transactions")


# ---------------------------------------------------------------------------
# Seed: Companies
# ---------------------------------------------------------------------------
async def seed_companies(
    conn: asyncpg.Connection, orgs: list[dict]
) -> list[dict]:
    print_section("Companies")
    raw = load_fixture("companies.json")

    companies = []
    for i, c in enumerate(raw):
        org = orgs[i % len(orgs)]
        companies.append(
            {
                "id": uid(),
                "organization_id": org["id"],
                "name": c["name"],
                "domain": c["domain"],
                "industry": c["industry"],
                "country": c["country"],
                "city": c["city"],
                "employee_count": c["employee_count"],
                "annual_revenue": c.get("annual_revenue"),
                "description": c.get("description"),
                "technologies": json.dumps(c.get("technologies", [])),
                "lead_score": round(40 + (i * 3.1 % 60), 1),
                "created_at": days_ago(120 - i * 3),
                "updated_at": days_ago(5),
            }
        )

    await conn.executemany(
        """
        INSERT INTO companies
            (id, organization_id, name, domain, industry, country, city,
             employee_count, annual_revenue, description, technologies, lead_score,
             created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12,$13,$14)
        ON CONFLICT DO NOTHING
        """,
        [
            (
                c["id"], c["organization_id"], c["name"], c["domain"],
                c["industry"], c["country"], c["city"], c["employee_count"],
                c["annual_revenue"], c["description"], c["technologies"],
                c["lead_score"], c["created_at"], c["updated_at"]
            )
            for c in companies
        ],
    )
    print_step(f"Inserted {len(companies)} companies")
    return companies


# ---------------------------------------------------------------------------
# Seed: Contacts
# ---------------------------------------------------------------------------
async def seed_contacts(
    conn: asyncpg.Connection, orgs: list[dict], companies: list[dict]
) -> list[dict]:
    print_section("Contacts")
    raw = load_fixture("contacts.json")

    contacts = []
    for i, ct in enumerate(raw):
        company = companies[i % len(companies)]
        contacts.append(
            {
                "id": uid(),
                "organization_id": company["organization_id"],
                "company_id": company["id"],
                "first_name": ct["first_name"],
                "last_name": ct["last_name"],
                "email": ct["email"],
                "phone": ct.get("phone"),
                "designation": ct["designation"],
                "department": ct["department"],
                "seniority": ct["seniority"],
                "linkedin_url": ct.get("linkedin_url"),
                "lead_score": round(35 + (i * 2.7 % 65), 1),
                "created_at": days_ago(90 - i),
                "updated_at": days_ago(3),
            }
        )

    await conn.executemany(
        """
        INSERT INTO contacts
            (id, organization_id, company_id, first_name, last_name, email,
             phone, designation, department, seniority, linkedin_url,
             lead_score, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
        ON CONFLICT DO NOTHING
        """,
        [
            (
                c["id"], c["organization_id"], c["company_id"],
                c["first_name"], c["last_name"], c["email"], c["phone"],
                c["designation"], c["department"], c["seniority"],
                c["linkedin_url"], c["lead_score"], c["created_at"], c["updated_at"]
            )
            for c in contacts
        ],
    )
    print_step(f"Inserted {len(contacts)} contacts")
    return contacts


# ---------------------------------------------------------------------------
# Seed: CRM Pipelines & Stages
# ---------------------------------------------------------------------------
async def seed_crm_pipelines(
    conn: asyncpg.Connection, orgs: list[dict]
) -> tuple[list[dict], list[dict]]:
    print_section("CRM Pipelines & Stages")

    pipeline_templates = [
        ("Default Sales Pipeline", True),
        ("Enterprise Pipeline", False),
        ("Inbound Pipeline", False),
        ("Partner Pipeline", False),
        ("Renewal Pipeline", False),
    ]

    stage_templates = [
        ("Prospecting",      1, "#94A3B8", False, False),
        ("Qualification",    2, "#60A5FA", False, False),
        ("Proposal Sent",    3, "#F59E0B", False, False),
        ("Closed Won",       4, "#10B981", True,  False),
        # Closed Lost is a 5th stage only appended to provide full pipeline coverage
        # but only for the first pipeline template to keep it to 4 stages per pipeline
    ]

    pipelines = []
    stages = []

    for org in orgs:
        for p_idx, (p_name, is_default) in enumerate(pipeline_templates):
            pipeline_id = uid()
            pipelines.append(
                {
                    "id": pipeline_id,
                    "organization_id": org["id"],
                    "name": p_name,
                    "is_default": is_default,
                    "display_order": p_idx + 1,
                    "created_at": days_ago(100),
                    "updated_at": days_ago(5),
                }
            )
            for s_idx, (s_name, s_order, s_color, is_won, is_lost) in enumerate(stage_templates):
                stages.append(
                    {
                        "id": uid(),
                        "pipeline_id": pipeline_id,
                        "name": s_name,
                        "display_order": s_order,
                        "color": s_color,
                        "is_closed_won": is_won,
                        "is_closed_lost": is_lost,
                        "created_at": days_ago(100),
                    }
                )

    await conn.executemany(
        """
        INSERT INTO crm_pipelines
            (id, organization_id, name, is_default, display_order, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7)
        ON CONFLICT DO NOTHING
        """,
        [
            (p["id"], p["organization_id"], p["name"], p["is_default"],
             p["display_order"], p["created_at"], p["updated_at"])
            for p in pipelines
        ],
    )

    await conn.executemany(
        """
        INSERT INTO crm_stages
            (id, pipeline_id, name, display_order, color, is_closed_won, is_closed_lost, created_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        ON CONFLICT DO NOTHING
        """,
        [
            (s["id"], s["pipeline_id"], s["name"], s["display_order"],
             s["color"], s["is_closed_won"], s["is_closed_lost"], s["created_at"])
            for s in stages
        ],
    )

    print_step(f"Inserted {len(pipelines)} pipelines and {len(stages)} stages")
    return pipelines, stages


# ---------------------------------------------------------------------------
# Seed: CRM Deals
# ---------------------------------------------------------------------------
async def seed_crm_deals(
    conn: asyncpg.Connection,
    orgs: list[dict],
    users: list[dict],
    companies: list[dict],
    contacts: list[dict],
    pipelines: list[dict],
    stages: list[dict],
) -> None:
    print_section("CRM Deals")

    deal_data = [
        ("Acme Corp — Enterprise Expansion",    95000_00,  0.75, 30),
        ("CloudFlow Annual License",             48000_00,  0.50, 45),
        ("DataSync Integration Deal",            12500_00,  0.30, 60),
        ("NexaHealth Platform Rollout",         120000_00,  0.85, 15),
        ("RetailBoost SaaS Subscription",        22000_00,  0.60, 20),
        ("FinSecure Compliance Module",          75000_00,  0.40, 90),
        ("GlobalTech Consulting Contract",       30000_00,  0.65, 25),
        ("StartupBoost Growth Package",          8500_00,   0.90, 10),
        ("MedTech Data Pipeline",               55000_00,  0.45, 50),
        ("EduLearn AI Features Upsell",         15000_00,  0.70, 35),
    ]

    deals = []
    for i, (title, amount, prob, days_close) in enumerate(deal_data):
        org = orgs[i % len(orgs)]
        org_pipelines = [p for p in pipelines if p["organization_id"] == org["id"]]
        pipeline = org_pipelines[i % len(org_pipelines)]
        pipeline_stages = [s for s in stages if s["pipeline_id"] == pipeline["id"]]
        stage = pipeline_stages[i % len(pipeline_stages)]
        owner = next(u for u in users if u["organization_id"] == org["id"] and u["role"] == "manager")
        company = companies[i % len(companies)]
        contact = contacts[i % len(contacts)]

        deals.append(
            (
                uid(), org["id"], pipeline["id"], stage["id"],
                contact["id"], company["id"], owner["id"],
                title, amount, "USD", prob,
                days_from_now(days_close), "open",
                days_ago(30 - i), days_ago(1),
            )
        )

    await conn.executemany(
        """
        INSERT INTO crm_deals
            (id, organization_id, pipeline_id, stage_id, contact_id, company_id,
             owner_id, title, amount, currency, probability,
             expected_close_date, status, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
        ON CONFLICT DO NOTHING
        """,
        deals,
    )
    print_step(f"Inserted {len(deals)} deals")


# ---------------------------------------------------------------------------
# Seed: System Settings
# ---------------------------------------------------------------------------
async def seed_system_settings(conn: asyncpg.Connection) -> None:
    print_section("System Settings")

    settings = [
        (uid(), "PLATFORM_NAME",          "AI Lead Intelligence",  "string",  "Display name of the platform"),
        (uid(), "MAX_SEARCH_RESULTS",      "500",                   "integer", "Maximum results per search query"),
        (uid(), "MAX_EXPORT_ROWS",         "10000",                 "integer", "Maximum rows per export file"),
        (uid(), "AI_SCORING_MODEL",        "lead-score-v2",         "string",  "Active AI scoring model version"),
        (uid(), "CREDIT_COST_SEARCH",      "10",                    "integer", "Credits consumed per search execution"),
        (uid(), "CREDIT_COST_ENRICHMENT",  "5",                     "integer", "Credits consumed per contact enrichment"),
        (uid(), "CREDIT_COST_EXPORT",      "1",                     "integer", "Credits consumed per exported row"),
        (uid(), "SUPPORT_EMAIL",           "support@ailead.example","string",  "Platform support email address"),
        (uid(), "SESSION_TIMEOUT_MINUTES", "480",                   "integer", "User session timeout in minutes"),
        (uid(), "RATE_LIMIT_REQUESTS",     "200",                   "integer", "API rate limit per minute per org"),
    ]

    await conn.executemany(
        """
        INSERT INTO system_settings (id, key, value, value_type, description, updated_at)
        VALUES ($1, $2, $3, $4, $5, NOW())
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """,
        settings,
    )
    print_step(f"Inserted/updated {len(settings)} system settings")


# ---------------------------------------------------------------------------
# Seed: Feature Flags
# ---------------------------------------------------------------------------
async def seed_feature_flags(conn: asyncpg.Connection) -> None:
    print_section("Feature Flags")

    flags = [
        (uid(), "ai_scoring",            True,  json.dumps({}),
         "Enable AI-powered lead scoring"),
        (uid(), "bulk_export",           True,  json.dumps({"max_rows": 10000}),
         "Enable bulk CSV/XLSX export"),
        (uid(), "advanced_analytics",    False, json.dumps({"rollout_pct": 0}),
         "Advanced analytics dashboard — beta"),
        (uid(), "crm_sync",              True,  json.dumps({"providers": ["hubspot", "salesforce"]}),
         "Enable CRM bi-directional sync"),
        (uid(), "linkedin_enrichment",   True,  json.dumps({}),
         "Enrich contacts with LinkedIn data"),
        (uid(), "predictive_icp",        False, json.dumps({"rollout_pct": 10}),
         "Predictive ICP model — limited beta"),
        (uid(), "multi_pipeline_crm",    True,  json.dumps({}),
         "Support multiple CRM pipelines per org"),
        (uid(), "email_sequences",       False, json.dumps({}),
         "Automated email sequence feature — coming soon"),
    ]

    await conn.executemany(
        """
        INSERT INTO feature_flags (id, name, is_enabled, conditions, description, created_at, updated_at)
        VALUES ($1, $2, $3, $4::jsonb, $5, NOW(), NOW())
        ON CONFLICT (name) DO UPDATE
            SET is_enabled = EXCLUDED.is_enabled,
                conditions = EXCLUDED.conditions,
                updated_at = NOW()
        """,
        flags,
    )
    print_step(f"Inserted/updated {len(flags)} feature flags")


# ---------------------------------------------------------------------------
# Seed: Sample Searches
# ---------------------------------------------------------------------------
async def seed_searches(
    conn: asyncpg.Connection, orgs: list[dict], users: list[dict]
) -> None:
    print_section("Sample Searches")

    searches = []
    search_templates = [
        (
            "US SaaS Companies 100-500 employees",
            {"industry": "SaaS", "country": "US", "employee_min": 100, "employee_max": 500},
            42, 10,
        ),
        (
            "UK Fintech Decision Makers",
            {"industry": "Fintech", "country": "UK", "seniority": ["C_LEVEL", "VP"]},
            18, 8,
        ),
        (
            "High-Score Healthcare Leads",
            {"industry": "Healthcare", "lead_score_min": 75},
            31, 15,
        ),
        (
            "German Engineering Firms",
            {"country": "DE", "industry": "Manufacturing"},
            7, 5,
        ),
        (
            "Series B+ Startups with AI Tech",
            {"technologies": ["machine learning", "python"], "funding_stage": "Series B+"},
            55, 20,
        ),
    ]

    for org in orgs:
        manager = next(u for u in users if u["organization_id"] == org["id"] and u["role"] == "manager")
        for i, (name, filters, result_count, credits) in enumerate(search_templates):
            searches.append(
                (
                    uid(), org["id"], manager["id"], name,
                    json.dumps(filters), result_count, credits,
                    "completed", days_ago(20 - i * 3), days_ago(25 - i * 3),
                )
            )

    await conn.executemany(
        """
        INSERT INTO searches
            (id, organization_id, user_id, name, filters, result_count,
             credits_used, status, executed_at, created_at)
        VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10)
        ON CONFLICT DO NOTHING
        """,
        searches,
    )
    print_step(f"Inserted {len(searches)} sample searches")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
async def main() -> None:
    print("\nAI Lead Intelligence Platform — Database Seed Script")
    print("=" * 60)
    print(f"Started at: {now().isoformat()}")

    conn = await get_connection()
    print_step("Connected to database")

    try:
        # Core identity
        orgs = await seed_organizations(conn)
        users = await seed_users(conn, orgs)
        await seed_subscriptions(conn, orgs)
        await seed_credit_transactions(conn, orgs, users)

        # Lead intelligence
        companies = await seed_companies(conn, orgs)
        contacts = await seed_contacts(conn, orgs, companies)
        await seed_searches(conn, orgs, users)

        # CRM
        pipelines, stages = await seed_crm_pipelines(conn, orgs)
        await seed_crm_deals(conn, orgs, users, companies, contacts, pipelines, stages)

        # Platform configuration
        await seed_system_settings(conn)
        await seed_feature_flags(conn)

    finally:
        await conn.close()
        print_step("Database connection closed")

    print(f"\n{'='*60}")
    print("  Seed completed successfully!")
    print(f"  Finished at: {now().isoformat()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import all models to register them with the metadata
from backend.app.common.base import Base  # noqa: F401
from backend.app.organizations.models import Organization  # noqa: F401
from backend.app.users.models import User, Role, Permission, APIKey, RefreshToken  # noqa: F401
from backend.app.common.reference import Industry, Country, State, City, Technology  # noqa: F401
from backend.app.companies.models import Company, CompanySocialProfile, CompanyTechnology  # noqa: F401
from backend.app.contacts.models import Contact, ContactSocialProfile  # noqa: F401
from backend.app.search.models import Search, SearchResult, SavedSearch  # noqa: F401
from backend.app.ai.models import LeadScore  # noqa: F401
from backend.app.enrichment.models import EmailVerification  # noqa: F401
from backend.app.crm.models import (  # noqa: F401
    Tag, ContactTag, CompanyTag, Activity, Note,
    CRMPipeline, CRMPipelineStage, CRMDeal, CRMTask,
    LeadList, LeadListContact,
)
from backend.app.notifications.models import Notification  # noqa: F401
from backend.app.exports.models import Export, ImportJob  # noqa: F401
from backend.app.integrations.models import ConnectorConfig, ConnectorJob  # noqa: F401
from backend.app.billing.models import Subscription, CreditTransaction  # noqa: F401
from backend.app.admin.models import AuditLog, SystemSetting, FeatureFlag, Workflow, WorkflowExecution  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url():
    from backend.config import settings
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

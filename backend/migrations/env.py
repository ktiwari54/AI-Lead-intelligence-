"""Alembic migration environment - async with multi-schema support."""
from __future__ import annotations
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

from backend.app.common.base import Base
from backend.config import get_settings

# Import all models so their metadata is registered
from backend.app.organizations.models import *  # noqa: F401, F403
from backend.app.users.models import *  # noqa: F401, F403
from backend.app.companies.models import *  # noqa: F401, F403
from backend.app.contacts.models import *  # noqa: F401, F403
from backend.app.search.models import *  # noqa: F401, F403
from backend.app.ai.models import *  # noqa: F401, F403
from backend.app.crm.models import *  # noqa: F401, F403
from backend.app.enrichment.models import *  # noqa: F401, F403
from backend.app.billing.models import *  # noqa: F401, F403
from backend.app.notifications.models import *  # noqa: F401, F403
from backend.app.exports.models import *  # noqa: F401, F403
from backend.app.integrations.models import *  # noqa: F401, F403
from backend.app.admin.models import *  # noqa: F401, F403
from backend.app.discovery.models import *  # noqa: F401, F403

config = context.config
settings = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# All schemas Alembic should track
SCHEMAS = [
    "public", "auth", "core", "crm", "search", "ai", "analytics",
    "connector", "audit", "billing", "notification", "system",
    "enrichment", "export",
]


def include_object(object, name, type_, reflected, compare_to):
    """Include all objects from all tracked schemas."""
    if type_ == "table":
        return True
    return True


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema="public",
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    config_section = config.get_section(config.config_ini_section, {})
    config_section["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        search_path = ", ".join(SCHEMAS)
        await connection.execute(text(f"SET search_path TO {search_path}"))
        await connection.commit()

        def run_migrations(connection):
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_schemas=True,
                version_table_schema="public",
                include_object=include_object,
                compare_type=True,
                compare_server_default=True,
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

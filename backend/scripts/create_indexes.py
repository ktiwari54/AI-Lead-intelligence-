"""Apply index DDL to the database."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def apply_indexes():
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    sql = (Path(__file__).parent.parent / "migrations" / "ddl" / "002_indexes.sql").read_text()

    async with engine.begin() as conn:
        await conn.exec_driver_sql(sql)

    await engine.dispose()
    print("Indexes applied.")


if __name__ == "__main__":
    asyncio.run(apply_indexes())

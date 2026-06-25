"""Run seed SQL files against the configured database."""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def run_seed():
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    seed_dir = Path(__file__).parent.parent / "migrations" / "seed"

    async with engine.begin() as conn:
        for sql_file in sorted(seed_dir.glob("*.sql")):
            print(f"Running seed: {sql_file.name}")
            sql = sql_file.read_text()
            await conn.exec_driver_sql(sql)
            print(f"  Done: {sql_file.name}")

    await engine.dispose()
    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(run_seed())

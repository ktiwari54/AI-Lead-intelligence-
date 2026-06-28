"""Run async coroutines safely inside Celery fork workers."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import TypeVar

T = TypeVar("T")


def run_async_task(coro: Coroutine[None, None, T]) -> T:
    """Execute a coroutine in a dedicated event loop with a clean DB pool."""
    from backend.database import engine

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            loop.run_until_complete(engine.dispose())
        except Exception:
            pass
        loop.close()
        asyncio.set_event_loop(None)
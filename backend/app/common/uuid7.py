"""
UUID v7 implementation for Python.

UUID v7 is time-ordered (vs random UUID v4), meaning rows inserted close
together in time will have adjacent primary keys. This dramatically improves
B-tree index locality in PostgreSQL, reducing page splits and improving
sequential scan performance at scale.

Format: [48-bit unix_ms][4-bit version=7][12-bit rand_a][2-bit variant][62-bit rand_b]
"""
from __future__ import annotations
import os
import time
import uuid
from typing import Any

# Try the uuid_extensions package first, fall back to our own implementation
try:
    from uuid_extensions import uuid7 as _uuid7_ext  # pip install uuid-extensions

    def uuid7() -> uuid.UUID:
        return _uuid7_ext()

except ImportError:
    import struct
    import random

    _last_ms: int = 0
    _seq: int = 0

    def uuid7() -> uuid.UUID:
        """
        Generate a UUID v7.
        Monotonically increasing within the same millisecond using a sequence counter.
        """
        global _last_ms, _seq

        now_ms = int(time.time() * 1000)

        if now_ms == _last_ms:
            _seq = (_seq + 1) & 0xFFF  # 12-bit sequence
        else:
            _last_ms = now_ms
            _seq = random.getrandbits(12)

        rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF

        # Assemble: 48-bit ms | 4-bit ver (7) | 12-bit seq | 2-bit var (10) | 62-bit rand
        high = (now_ms << 16) | (0x7000) | _seq
        low = (0x8000000000000000) | rand_b

        int_val = (high << 64) | low
        return uuid.UUID(int=int_val)


def uuid7_str() -> str:
    """Return UUID v7 as a lowercase string."""
    return str(uuid7())


def is_uuid7(u: uuid.UUID) -> bool:
    """Check if a UUID is version 7."""
    return u.version == 7


def uuid7_timestamp_ms(u: uuid.UUID) -> int:
    """Extract the embedded Unix timestamp (milliseconds) from a UUID v7."""
    return u.int >> 80


def uuid7_datetime(u: uuid.UUID):
    """Extract the embedded datetime from a UUID v7."""
    from datetime import datetime, timezone
    ms = uuid7_timestamp_ms(u)
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


# SQLAlchemy TypeDecorator for UUID v7
from sqlalchemy import types as sa_types


class UUID7(sa_types.TypeDecorator):
    """
    SQLAlchemy type that stores UUID v7 as a native PostgreSQL UUID column
    but generates UUID v7 values by default on the Python side.
    """
    impl = sa_types.Uuid
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return uuid.UUID(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

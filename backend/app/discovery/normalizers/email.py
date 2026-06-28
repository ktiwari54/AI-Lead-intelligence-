from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailNormalizer:
    @staticmethod
    def normalize(value: str | None) -> str | None:
        if not value:
            return None
        email = value.strip().lower()
        return email if _EMAIL_RE.match(email) else None
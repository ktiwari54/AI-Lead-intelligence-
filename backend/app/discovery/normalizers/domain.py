from __future__ import annotations

import re
from urllib.parse import urlparse


class DomainNormalizer:
    @staticmethod
    def normalize(value: str | None) -> str | None:
        if not value:
            return None
        text = value.strip().lower()
        if "://" not in text:
            text = f"https://{text}"
        parsed = urlparse(text)
        host = parsed.netloc or parsed.path.split("/")[0]
        host = host.removeprefix("www.")
        if not host or "." not in host:
            return None
        return host
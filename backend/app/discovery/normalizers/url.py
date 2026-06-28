from __future__ import annotations

from urllib.parse import urlparse, urlunparse


class UrlNormalizer:
    @staticmethod
    def normalize(value: str | None) -> str | None:
        if not value:
            return None
        text = value.strip()
        if not text.startswith(("http://", "https://")):
            text = f"https://{text}"
        parsed = urlparse(text)
        if not parsed.netloc:
            return None
        return urlunparse(("https", parsed.netloc.lower(), parsed.path.rstrip("/") or "", "", "", ""))
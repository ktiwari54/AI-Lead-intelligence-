from __future__ import annotations

import re
import unicodedata

_SUFFIXES = re.compile(
    r"\b(inc\.?|llc\.?|l\.?l\.?c\.?|ltd\.?|corp\.?|corporation|co\.?|gmbh|plc|sa|ag)\b\.?",
    re.IGNORECASE,
)


class CompanyNameNormalizer:
    @staticmethod
    def normalize(value: str | None) -> str:
        if not value:
            return ""
        text = unicodedata.normalize("NFKC", value.strip())
        text = _SUFFIXES.sub("", text)
        text = re.sub(r"\s+", " ", text).strip(" ,.")
        return text.title() if text.isupper() or text.islower() else text
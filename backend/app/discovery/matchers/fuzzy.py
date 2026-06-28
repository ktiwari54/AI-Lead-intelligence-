from __future__ import annotations

import difflib


class FuzzyMatcher:
    @staticmethod
    def score(a: str | None, b: str | None) -> float:
        if not a or not b:
            return 0.0
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
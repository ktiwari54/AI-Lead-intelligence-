from __future__ import annotations


class ExactMatcher:
    @staticmethod
    def score(a: str | None, b: str | None) -> float:
        if not a or not b:
            return 0.0
        return 1.0 if a.strip().lower() == b.strip().lower() else 0.0
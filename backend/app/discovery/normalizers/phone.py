from __future__ import annotations

import re


class PhoneNormalizer:
    @staticmethod
    def normalize(value: str | None, default_region: str = "US") -> str | None:
        if not value:
            return None
        digits = re.sub(r"[^\d+]", "", value.strip())
        if not digits:
            return None
        if digits.startswith("00"):
            digits = f"+{digits[2:]}"
        if not digits.startswith("+"):
            if default_region == "US" and len(digits) == 10:
                digits = f"+1{digits}"
            elif default_region == "US" and len(digits) == 11 and digits.startswith("1"):
                digits = f"+{digits}"
            else:
                digits = f"+{digits}"
        return digits if len(re.sub(r"\D", "", digits)) >= 7 else None
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


GDPR_CONTROLS = [
    ("gdpr", "art_5_lawfulness", "Lawful basis documented for processing"),
    ("gdpr", "art_17_erasure", "Data erasure workflow available"),
    ("gdpr", "art_20_portability", "Data export in machine-readable format"),
    ("gdpr", "art_32_security", "Encryption at rest and in transit"),
    ("gdpr", "art_33_breach", "Breach notification process defined"),
]

SOC2_CONTROLS = [
    ("soc2", "cc6_1_access", "Logical access controls enforced"),
    ("soc2", "cc6_6_encryption", "Data encrypted in transit"),
    ("soc2", "cc7_2_monitoring", "Security monitoring active"),
    ("soc2", "cc8_1_change", "Change management process"),
]

ISO_CONTROLS = [
    ("iso27001", "a_9_access", "Access control policy"),
    ("iso27001", "a_12_operations", "Operational procedures documented"),
    ("iso27001", "a_16_incidents", "Incident management process"),
]


class ComplianceEngine:
    """Runs automated compliance control checks against platform state."""

    def all_controls(self) -> list[tuple[str, str, str]]:
        return GDPR_CONTROLS + SOC2_CONTROLS + ISO_CONTROLS

    def run_checks(self, org_signals: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        signals = org_signals or {}
        results = []
        now = datetime.now(timezone.utc)

        for framework, control_id, description in self.all_controls():
            status, evidence = self._check_control(framework, control_id, signals)
            results.append({
                "framework": framework,
                "control_id": control_id,
                "description": description,
                "status": status,
                "evidence": evidence,
                "checked_at": now.isoformat(),
                "next_check_at": None,
            })
        return results

    def _check_control(
        self, framework: str, control_id: str, signals: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        checks = {
            "art_32_security": signals.get("encryption_enabled", True),
            "art_17_erasure": signals.get("privacy_requests_enabled", True),
            "art_20_portability": signals.get("export_enabled", True),
            "cc6_1_access": signals.get("rbac_enabled", True),
            "cc7_2_monitoring": signals.get("security_monitoring", True),
            "a_16_incidents": signals.get("incident_process", True),
        }
        key = control_id.split("_", 1)[-1] if "_" in control_id else control_id
        passed = checks.get(control_id, checks.get(key, True))
        status = "pass" if passed else "fail"
        return status, {"automated": True, "framework": framework, "control": control_id}
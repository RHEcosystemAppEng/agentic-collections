from __future__ import annotations

from pathlib import Path

from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import read_text


def run(root: Path, registration_status: str) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    status_by_pack: dict[str, dict[str, str]] = {"rh-support-engineer": {}}
    readme = read_text(root / "README.md")
    has_policy_note = "rh-support-engineer policy" in readme.lower() or "intentionally excluded" in readme.lower()

    if registration_status == "registered":
        status_by_pack["rh-support-engineer"]["registration_status"] = "registered"
        return findings, status_by_pack

    if has_policy_note:
        status_by_pack["rh-support-engineer"]["registration_status"] = "excluded-by-policy"
        return findings, status_by_pack

    severity = Severity.BLOCKING
    findings.append(
        Finding(
            finding_id="SCP-001-RH-SUPPORT-ENGINEER",
            rule_id="SCP-001",
            severity=severity,
            artifact_path="README.md",
            message="rh-support-engineer is unregistered without explicit policy note",
            expected="Either marketplace registration or explicit exclusion policy note",
            actual="Unregistered and no policy note",
            ci_enforcement=default_enforcement_for_severity(severity),
            pack_name="rh-support-engineer",
        )
    )
    status_by_pack["rh-support-engineer"]["registration_status"] = "missing"
    return findings, status_by_pack


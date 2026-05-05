from __future__ import annotations

from .models import CiEnforcement, Severity


def default_enforcement_for_severity(severity: Severity) -> CiEnforcement:
    if severity == Severity.BLOCKING:
        return CiEnforcement.FAIL
    if severity in (Severity.HIGH, Severity.MEDIUM):
        return CiEnforcement.WARN
    return CiEnforcement.REPORT


def ci_status_from_findings(findings: list[dict]) -> str:
    for finding in findings:
        if finding.get("ci_enforcement") == CiEnforcement.FAIL.value:
            return "fail"
    return "pass"


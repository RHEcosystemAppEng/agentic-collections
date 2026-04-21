from __future__ import annotations

from .models import Severity


def summarize_findings(findings: list[dict], packs_total: int) -> dict:
    counts = {
        Severity.BLOCKING.value: 0,
        Severity.HIGH.value: 0,
        Severity.MEDIUM.value: 0,
        Severity.INFORMATIONAL.value: 0,
    }
    for finding in findings:
        severity = finding.get("severity")
        if severity in counts:
            counts[severity] += 1
    return {
        "packs_total": packs_total,
        "findings_total": len(findings),
        "by_severity": counts,
    }


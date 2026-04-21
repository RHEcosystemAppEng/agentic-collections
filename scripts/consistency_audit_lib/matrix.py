from __future__ import annotations

from .discovery import PACKS
from .models import MatrixRow, Severity


def _worst_severity(severities: list[Severity]) -> str:
    order = [Severity.BLOCKING, Severity.HIGH, Severity.MEDIUM, Severity.INFORMATIONAL]
    for severity in order:
        if severity in severities:
            return severity.value
    return "none"


def build_matrix(
    findings_by_pack: dict[str, list[dict]],
    status_by_pack: dict[str, dict[str, str]],
) -> list[dict]:
    rows: list[dict] = []
    for pack in PACKS:
        statuses = status_by_pack.get(pack, {})
        pack_findings = findings_by_pack.get(pack, [])
        severities = [
            Severity(item["severity"])
            for item in pack_findings
            if item.get("severity") in {s.value for s in Severity}
        ]
        row = MatrixRow(
            pack_name=pack,
            registration_status=statuses.get("registration_status", "missing"),
            version_consistency_status=statuses.get("version", "pass"),
            model_metadata_status=statuses.get("model", "pass"),
            claim_reality_status=statuses.get("claims", "pass"),
            style_icon_status=statuses.get("style", "pass"),
            overall_severity=_worst_severity(severities),
        )
        rows.append(row.to_dict())
    return rows


from __future__ import annotations

from pathlib import Path

from ..discovery import PACKS
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import load_json


REQUIRED_TOP_LEVEL_KEYS = ("repository", "packs", "mcp_servers", "generated_at")


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    statuses: dict[str, dict[str, str]] = {pack: {"style": "pass"} for pack in PACKS}
    data_path = root / "docs" / "data.json"

    if not data_path.exists():
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-003-MISSING-DATA-JSON",
                rule_id="VIS-003",
                severity=severity,
                artifact_path="docs/data.json",
                message="Documentation site data file is missing or has not yet been generated",
                expected="docs/data.json exists (generate via `make generate`)",
                actual="file missing",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"
        return findings, statuses

    try:
        data = load_json(data_path)
    except Exception as exc:
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-003-INVALID-DATA-JSON",
                rule_id="VIS-003",
                severity=severity,
                artifact_path="docs/data.json",
                message="Documentation site data file is not valid JSON",
                expected="Valid JSON object with required top-level keys",
                actual=f"JSON decode/load failed: {exc}",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"
        return findings, statuses

    missing_keys = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in data]
    if missing_keys:
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-003-MISSING-REQUIRED-KEYS",
                rule_id="VIS-003",
                severity=severity,
                artifact_path="docs/data.json",
                message="Documentation site data file is missing required top-level keys",
                expected=f"Keys present: {', '.join(REQUIRED_TOP_LEVEL_KEYS)}",
                actual=f"Missing keys: {', '.join(missing_keys)}",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"
        return findings, statuses

    if not isinstance(data.get("packs"), list) or not isinstance(data.get("mcp_servers"), list):
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-003-INVALID-TOP-LEVEL-TYPES",
                rule_id="VIS-003",
                severity=severity,
                artifact_path="docs/data.json",
                message="Documentation site data file has invalid top-level types",
                expected="`packs` and `mcp_servers` are arrays",
                actual=(
                    f"packs={type(data.get('packs')).__name__}, "
                    f"mcp_servers={type(data.get('mcp_servers')).__name__}"
                ),
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"

    return findings, statuses

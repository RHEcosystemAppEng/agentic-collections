from __future__ import annotations

from pathlib import Path

from ..discovery import PACKS
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import load_json


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    statuses: dict[str, dict[str, str]] = {pack: {"style": "pass"} for pack in PACKS}
    icons = load_json(root / "docs" / "icons.json")
    plugins = load_json(root / "docs" / "plugins.json")
    pack_icons = icons.get("packs", {})

    for pack in PACKS:
        if pack not in pack_icons:
            severity = Severity.HIGH
            findings.append(
                Finding(
                    finding_id=f"VIS-002-MISSING-ICON-{pack}",
                    rule_id="VIS-002",
                    severity=severity,
                    artifact_path="docs/icons.json",
                    message=f"Missing icon mapping for pack '{pack}'",
                    expected="Pack icon exists in docs/icons.json",
                    actual="No icon mapping",
                    ci_enforcement=default_enforcement_for_severity(severity),
                    pack_name=pack,
                )
            )
            statuses[pack]["style"] = "warn"
        if pack not in plugins:
            severity = Severity.HIGH
            findings.append(
                Finding(
                    finding_id=f"VIS-002-MISSING-PLUGIN-TITLE-{pack}",
                    rule_id="VIS-002",
                    severity=severity,
                    artifact_path="docs/plugins.json",
                    message=f"Missing plugin display metadata for pack '{pack}'",
                    expected="Pack title exists in docs/plugins.json",
                    actual="No plugin metadata",
                    ci_enforcement=default_enforcement_for_severity(severity),
                    pack_name=pack,
                )
            )
            statuses[pack]["style"] = "warn"
    return findings, statuses


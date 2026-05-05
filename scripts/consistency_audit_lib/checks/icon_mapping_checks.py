from __future__ import annotations

from pathlib import Path

from ..discovery import PACKS
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import load_json


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    statuses: dict[str, dict[str, str]] = {pack: {"style": "pass"} for pack in PACKS}
    icons_path = root / "docs" / "icons.json"
    plugins_path = root / "docs" / "plugins.json"

    icons_available = icons_path.exists()
    plugins_available = plugins_path.exists()

    if not icons_available:
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-002-MISSING-ICONS-FILE",
                rule_id="VIS-002",
                severity=severity,
                artifact_path="docs/icons.json",
                message="Icon mapping file is missing",
                expected="docs/icons.json exists",
                actual="file missing",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"

    if not plugins_available:
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-002-MISSING-PLUGINS-FILE",
                rule_id="VIS-002",
                severity=severity,
                artifact_path="docs/plugins.json",
                message="Plugin title mapping file is missing",
                expected="docs/plugins.json exists",
                actual="file missing",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"

    icons = load_json(icons_path) if icons_available else {}
    plugins = load_json(plugins_path) if plugins_available else {}
    pack_icons = icons.get("packs", {}) if icons_available else {}

    for pack in PACKS:
        if icons_available and pack not in pack_icons:
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
        if plugins_available and pack not in plugins:
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


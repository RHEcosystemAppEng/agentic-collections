from __future__ import annotations

import re
from pathlib import Path

from ..discovery import PACKS
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import load_json, read_text


TOKEN_RE = re.compile(r"--[a-z0-9-]+\s*:")
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    statuses: dict[str, dict[str, str]] = {pack: {"style": "pass"} for pack in PACKS}
    css_path = root / "docs" / "styles.css"
    js_path = root / "docs" / "app.js"

    css = ""
    js = ""
    if css_path.exists():
        css = read_text(css_path)
    else:
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-001-MISSING-STYLES-CSS",
                rule_id="VIS-001",
                severity=severity,
                artifact_path="docs/styles.css",
                message="Canonical docs stylesheet is missing",
                expected="docs/styles.css exists",
                actual="file missing",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"

    if js_path.exists():
        js = read_text(js_path)
    else:
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-001-MISSING-APP-JS",
                rule_id="VIS-001",
                severity=severity,
                artifact_path="docs/app.js",
                message="Docs site app script is missing",
                expected="docs/app.js exists",
                actual="file missing",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"

    token_path = root / "docs" / "style-tokens.json"
    token_data = load_json(token_path) if token_path.exists() else {}
    tokens = TOKEN_RE.findall(css) if css else []
    if css and not tokens:
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="VIS-001-NO-TOKENS",
                rule_id="VIS-001",
                severity=severity,
                artifact_path="docs/styles.css",
                message="No canonical CSS tokens found",
                expected="At least one --token variable",
                actual="No token declarations",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )

    # Hardcoded hex in JS can indicate drift from centralized token usage.
    js_hex_count = len(HEX_RE.findall(js)) if js else 0
    if js_hex_count > 0:
        severity = Severity.MEDIUM
        findings.append(
            Finding(
                finding_id="VIS-001-JS-HARDCODED-COLOR",
                rule_id="VIS-001",
                severity=severity,
                artifact_path="docs/app.js",
                message="Hardcoded color values detected in docs/app.js",
                expected="Prefer tokenized styles from docs/styles.css",
                actual=f"{js_hex_count} hardcoded hex values",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"
    if not token_data:
        severity = Severity.MEDIUM
        findings.append(
            Finding(
                finding_id="VIS-001-MISSING-STYLE-TOKEN-FILE",
                rule_id="VIS-001",
                severity=severity,
                artifact_path="docs/style-tokens.json",
                message="style token metadata file is missing",
                expected="docs/style-tokens.json exists with color and size token definitions",
                actual="file missing or empty",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            statuses[pack]["style"] = "warn"
    else:
        if "colors" not in token_data or "sizes" not in token_data:
            severity = Severity.MEDIUM
            findings.append(
                Finding(
                    finding_id="VIS-001-INCOMPLETE-STYLE-TOKEN-FILE",
                    rule_id="VIS-001",
                    severity=severity,
                    artifact_path="docs/style-tokens.json",
                    message="style token metadata missing required sections",
                    expected="colors and sizes sections present",
                    actual="colors/sizes keys incomplete",
                    ci_enforcement=default_enforcement_for_severity(severity),
                )
            )
            for pack in PACKS:
                statuses[pack]["style"] = "warn"
    return findings, statuses


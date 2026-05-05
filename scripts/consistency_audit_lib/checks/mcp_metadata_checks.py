from __future__ import annotations

from pathlib import Path

from ..discovery import PACKS
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import load_json


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    statuses: dict[str, dict[str, str]] = {pack: {"style": "pass"} for pack in PACKS}
    mcp = load_json(root / "docs" / "mcp.json")

    for server_name, server in mcp.items():
        if not isinstance(server, dict):
            continue
        if "title" not in server:
            severity = Severity.MEDIUM
            findings.append(
                Finding(
                    finding_id=f"VIS-002-MCP-MISSING-TITLE-{server_name}",
                    rule_id="VIS-002",
                    severity=severity,
                    artifact_path="docs/mcp.json",
                    message=f"MCP metadata missing title for '{server_name}'",
                    expected="title field present",
                    actual="title missing",
                    ci_enforcement=default_enforcement_for_severity(severity),
                )
            )
            for pack in PACKS:
                statuses[pack]["style"] = "warn"
    return findings, statuses


from __future__ import annotations

from pathlib import Path

from ..discovery import PACKS
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import load_yaml


def marketplace_versions(root: Path) -> dict[str, str]:
    marketplace = load_yaml(root / "marketplace" / "rh-agentic-collection.yml")
    modules = marketplace.get("modules", [])
    versions: dict[str, str] = {}
    for module in modules:
        if isinstance(module, dict) and module.get("name"):
            versions[module["name"]] = str(module.get("version", ""))
    return versions


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]], dict[str, str]]:
    findings: list[Finding] = []
    status_by_pack: dict[str, dict[str, str]] = {}
    versions = marketplace_versions(root)
    for pack in PACKS:
        status_by_pack.setdefault(pack, {})
        if pack in versions:
            status_by_pack[pack]["registration_status"] = "registered"
            status_by_pack[pack]["version"] = "pass"
        else:
            status_by_pack[pack]["registration_status"] = "missing"
            status_by_pack[pack]["version"] = "fail"
            severity = Severity.BLOCKING if pack != "rh-support-engineer" else Severity.INFORMATIONAL
            findings.append(
                Finding(
                    finding_id=f"VER-001-{pack}",
                    rule_id="VER-001",
                    severity=severity,
                    artifact_path="marketplace/rh-agentic-collection.yml",
                    message=f"Pack '{pack}' is not listed in marketplace modules",
                    expected="Pack is listed or explicitly excluded by policy",
                    actual="Not listed",
                    ci_enforcement=default_enforcement_for_severity(severity),
                    pack_name=pack,
                )
            )
    return findings, status_by_pack, versions


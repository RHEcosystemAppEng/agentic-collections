from __future__ import annotations

from pathlib import Path

from ..discovery import PACKS, pack_readmes
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import extract_first_semver, read_text


def run(root: Path, marketplace_versions: dict[str, str]) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    status_by_pack: dict[str, dict[str, str]] = {}
    root_readme = read_text(root / "README.md")
    root_version = extract_first_semver(root_readme)

    for pack, readme_path in pack_readmes(root).items():
        status_by_pack.setdefault(pack, {})
        if not readme_path.exists():
            severity = Severity.HIGH
            findings.append(
                Finding(
                    finding_id=f"VER-002-MISSING-{pack}",
                    rule_id="VER-002",
                    severity=severity,
                    artifact_path=str(readme_path.relative_to(root)),
                    message=f"Pack README missing for '{pack}'",
                    expected="README exists with version reference",
                    actual="README missing",
                    ci_enforcement=default_enforcement_for_severity(severity),
                    pack_name=pack,
                )
            )
            status_by_pack[pack]["version"] = "warn"
            continue

        pack_version = extract_first_semver(read_text(readme_path))
        canonical = marketplace_versions.get(pack)
        if canonical and pack_version and canonical != pack_version:
            severity = Severity.HIGH
            findings.append(
                Finding(
                    finding_id=f"VER-002-PACK-{pack}",
                    rule_id="VER-002",
                    severity=severity,
                    artifact_path=str(readme_path.relative_to(root)),
                    message=f"Pack README version mismatch for '{pack}'",
                    expected=canonical,
                    actual=pack_version,
                    ci_enforcement=default_enforcement_for_severity(severity),
                    pack_name=pack,
                )
            )
            status_by_pack[pack]["version"] = "warn"
        elif canonical and root_version and canonical != root_version:
            status_by_pack[pack]["version"] = "warn"
        else:
            status_by_pack[pack]["version"] = status_by_pack[pack].get("version", "pass")

    return findings, status_by_pack


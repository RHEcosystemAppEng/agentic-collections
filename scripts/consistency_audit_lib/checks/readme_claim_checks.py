from __future__ import annotations

import re
from pathlib import Path

from ..discovery import PACKS, skill_files_for_pack
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import read_text


ROOT_SKILL_TOTAL_RE = re.compile(r"\*\*Total:\*\*\s+(\d+)\s+skills", re.IGNORECASE)


def _actual_total_skills(root: Path) -> int:
    total = 0
    for pack in PACKS:
        total += len(skill_files_for_pack(root, pack))
    return total


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    status_by_pack: dict[str, dict[str, str]] = {pack: {} for pack in PACKS}
    readme_path = root / "README.md"
    content = read_text(readme_path)

    match = ROOT_SKILL_TOTAL_RE.search(content)
    if match:
        claimed = int(match.group(1))
        actual = _actual_total_skills(root)
        if claimed != actual:
            severity = Severity.HIGH
            findings.append(
                Finding(
                    finding_id="CLM-001-ROOT-SKILL-TOTAL",
                    rule_id="CLM-001",
                    severity=severity,
                    artifact_path="README.md",
                    message="Root README total skill count is out of sync with repository reality",
                    expected=str(actual),
                    actual=str(claimed),
                    ci_enforcement=default_enforcement_for_severity(severity),
                )
            )
            for pack in PACKS:
                status_by_pack[pack]["claims"] = "warn"

    wording_required = "orchestration"
    if wording_required not in content.lower():
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="CLM-001-ROOT-WORDING",
                rule_id="CLM-001",
                severity=severity,
                artifact_path="README.md",
                message="Root README should explicitly distinguish agents and orchestration wording",
                expected="Wording includes explicit orchestration terminology",
                actual="No explicit orchestration wording found",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )
        for pack in PACKS:
            status_by_pack[pack]["claims"] = "warn"

    for pack in PACKS:
        status_by_pack[pack].setdefault("claims", "pass")
    return findings, status_by_pack


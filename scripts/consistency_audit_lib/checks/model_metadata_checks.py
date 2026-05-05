from __future__ import annotations

from pathlib import Path

from ..discovery import PACKS, skill_files_for_pack
from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import extract_frontmatter


VALID_MODELS = {"inherit", "sonnet", "haiku"}
VALID_COLORS = {"cyan", "green", "blue", "yellow", "red", "magenta"}


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    statuses: dict[str, dict[str, str]] = {pack: {} for pack in PACKS}
    for pack in PACKS:
        pack_findings = 0
        for skill in skill_files_for_pack(root, pack):
            frontmatter = extract_frontmatter(skill)
            model = str(frontmatter.get("model", "")).strip()
            color = str(frontmatter.get("color", "")).strip().lower()
            if not model:
                pack_findings += 1
                severity = Severity.BLOCKING
                findings.append(
                    Finding(
                        finding_id=f"MOD-001-MISSING-MODEL-{pack}-{skill.parent.name}",
                        rule_id="MOD-001",
                        severity=severity,
                        artifact_path=str(skill.relative_to(root)),
                        message="Skill frontmatter missing required model",
                        expected="model: inherit|sonnet|haiku",
                        actual="model field missing",
                        ci_enforcement=default_enforcement_for_severity(severity),
                        pack_name=pack,
                    )
                )
            elif model not in VALID_MODELS:
                pack_findings += 1
                severity = Severity.BLOCKING
                findings.append(
                    Finding(
                        finding_id=f"MOD-001-INVALID-MODEL-{pack}-{skill.parent.name}",
                        rule_id="MOD-001",
                        severity=severity,
                        artifact_path=str(skill.relative_to(root)),
                        message="Skill frontmatter has invalid model",
                        expected="inherit|sonnet|haiku",
                        actual=model,
                        ci_enforcement=default_enforcement_for_severity(severity),
                        pack_name=pack,
                    )
                )
            if color and color not in VALID_COLORS:
                pack_findings += 1
                severity = Severity.HIGH
                findings.append(
                    Finding(
                        finding_id=f"MOD-002-INVALID-COLOR-{pack}-{skill.parent.name}",
                        rule_id="MOD-002",
                        severity=severity,
                        artifact_path=str(skill.relative_to(root)),
                        message="Skill frontmatter has non-standard color value",
                        expected="cyan|green|blue|yellow|red|magenta",
                        actual=color,
                        ci_enforcement=default_enforcement_for_severity(severity),
                        pack_name=pack,
                    )
                )
        statuses[pack]["model"] = "warn" if pack_findings else "pass"
    return findings, statuses


from __future__ import annotations

from pathlib import Path

from ..enforcement import default_enforcement_for_severity
from ..models import Finding, Severity
from ..sources import read_text


def run(root: Path) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    statuses: dict[str, dict[str, str]] = {}

    python_validator = read_text(root / "scripts" / "validate_skill_design.py")
    shell_validator = read_text(root / "scripts" / "validate-skills.sh")

    python_mentions_optional = "Model is optional" in python_validator
    shell_requires_model = "Missing 'model' field in frontmatter (MANDATORY)" in shell_validator

    if python_mentions_optional and shell_requires_model:
        severity = Severity.HIGH
        findings.append(
            Finding(
                finding_id="MOD-002-VALIDATOR-DRIFT",
                rule_id="MOD-002",
                severity=severity,
                artifact_path="scripts/validate_skill_design.py",
                message="Python and shell validators disagree on model-frontmatter requiredness",
                expected="Validators share required model policy",
                actual="Python validator treats model as optional while shell validator requires it",
                ci_enforcement=default_enforcement_for_severity(severity),
            )
        )

    return findings, statuses


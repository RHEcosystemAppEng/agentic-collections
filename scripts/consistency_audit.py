#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Callable

from consistency_audit_lib import matrix as matrix_builder
from consistency_audit_lib.checks import (
    docs_data_checks,
    icon_mapping_checks,
    mcp_metadata_checks,
    model_metadata_checks,
    readme_claim_checks,
    readme_version_checks,
    style_checks,
    validator_alignment_checks,
    version_checks,
)
from consistency_audit_lib.contracts import validate_audit_report, validate_ci_violations
from consistency_audit_lib.discovery import PACKS, repo_root
from consistency_audit_lib.enforcement import ci_status_from_findings
from consistency_audit_lib.models import Finding, utc_now_iso
from consistency_audit_lib.reporting import write_json, write_markdown
from consistency_audit_lib.summary import summarize_findings


def _run_check(
    checker: Callable,
    root: Path,
    findings: list[dict],
    status_by_pack: dict[str, dict[str, str]],
    *args,
):
    check_findings, check_statuses = checker(root, *args) if args else checker(root)
    for finding in check_findings:
        findings.append(finding.to_dict() if isinstance(finding, Finding) else finding)
    for pack, status in check_statuses.items():
        status_by_pack.setdefault(pack, {}).update(status)


def _current_branch(root: Path) -> str:
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root, text=True
        ).strip()
        return output
    except Exception:
        return "unknown"


def build_report(root: Path) -> tuple[dict, dict]:
    findings: list[dict] = []
    status_by_pack: dict[str, dict[str, str]] = {pack: {} for pack in PACKS}

    version_findings, version_statuses, marketplace_versions = version_checks.run(root)
    for finding in version_findings:
        findings.append(finding.to_dict())
    for pack, statuses in version_statuses.items():
        status_by_pack.setdefault(pack, {}).update(statuses)

    _run_check(readme_version_checks.run, root, findings, status_by_pack, marketplace_versions)
    _run_check(readme_claim_checks.run, root, findings, status_by_pack)
    _run_check(model_metadata_checks.run, root, findings, status_by_pack)
    _run_check(validator_alignment_checks.run, root, findings, status_by_pack)
    _run_check(style_checks.run, root, findings, status_by_pack)
    _run_check(icon_mapping_checks.run, root, findings, status_by_pack)
    _run_check(mcp_metadata_checks.run, root, findings, status_by_pack)
    _run_check(docs_data_checks.run, root, findings, status_by_pack)

    matrix = matrix_builder.build_matrix(
        findings_by_pack={
            pack: [f for f in findings if f.get("pack_name") == pack]
            for pack in PACKS
        },
        status_by_pack=status_by_pack,
    )

    summary = summarize_findings(findings, len(PACKS))
    report = {
        "schema_version": "1.0.0",
        "generated_at": utc_now_iso(),
        "branch": _current_branch(root),
        "summary": summary,
        "matrix": matrix,
        "findings": findings,
        "policy_decisions": [],
        "remediation_plan": [],
    }

    ci_violations = {
        "status": ci_status_from_findings(findings),
        "failure_threshold": "blocking>0",
        "blocking_count": summary["by_severity"]["blocking"],
        "high_count": summary["by_severity"]["high"],
        "medium_count": summary["by_severity"]["medium"],
        "informational_count": summary["by_severity"]["informational"],
        "violations": [
            f
            for f in findings
            if f.get("ci_enforcement") == "fail"
        ],
    }
    return report, ci_violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Collection consistency audit")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", default="")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--changed-only", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    report, ci_violations = build_report(root)

    report_schema = root / "specs" / "001-collection-consistency-audit" / "contracts" / "audit-report.schema.json"
    ci_schema = root / "specs" / "001-collection-consistency-audit" / "contracts" / "ci-violations.schema.json"
    validate_audit_report(report, report_schema)
    validate_ci_violations(ci_violations, ci_schema)

    output_path = Path(args.output) if args.output else (
        root / "reports" / ("consistency-audit.json" if args.format == "json" else "consistency-audit.md")
    )
    if not output_path.is_absolute():
        output_path = root / output_path

    if args.format == "json":
        write_json(output_path, report)
        print(f"Wrote audit JSON report to {output_path}")
    else:
        write_markdown(output_path, report)
        print(f"Wrote audit markdown report to {output_path}")

    ci_output = output_path.with_name("ci-violations.json")
    write_json(ci_output, ci_violations)

    if args.ci and ci_violations["status"] == "fail":
        print("Consistency audit CI gate failed")
        return 1

    if args.changed_only:
        print("Note: --changed-only currently runs full scan (future optimization)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


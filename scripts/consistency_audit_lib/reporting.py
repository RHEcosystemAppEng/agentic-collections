from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    summary = payload.get("summary", {})
    findings = payload.get("findings", [])
    matrix = payload.get("matrix", [])

    lines = [
        "# Consistency Audit Report",
        "",
        f"- Generated: `{payload.get('generated_at', '')}`",
        f"- Branch: `{payload.get('branch', '')}`",
        f"- Total packs: `{summary.get('packs_total', 0)}`",
        f"- Total findings: `{summary.get('findings_total', 0)}`",
        "",
        "## Severity Summary",
        "",
        f"- blocking: `{summary.get('by_severity', {}).get('blocking', 0)}`",
        f"- high: `{summary.get('by_severity', {}).get('high', 0)}`",
        f"- medium: `{summary.get('by_severity', {}).get('medium', 0)}`",
        f"- informational: `{summary.get('by_severity', {}).get('informational', 0)}`",
        "",
        "## Matrix",
        "",
        "| Pack | Registration | Version | Model | Claims | Style | Overall |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in matrix:
        lines.append(
            f"| {row.get('pack_name')} | {row.get('registration_status')} | "
            f"{row.get('version_consistency_status')} | {row.get('model_metadata_status')} | "
            f"{row.get('claim_reality_status')} | {row.get('style_icon_status')} | "
            f"{row.get('overall_severity')} |"
        )

    lines.extend(["", "### Matrix Status Explanations", ""])
    lines.extend(
        [
            "| Pack | Domain | Status | Triggering Findings |",
            "|---|---|---|---|",
        ]
    )

    matrix_domains = [
        ("Version", "version_consistency_status", "VER"),
        ("Model", "model_metadata_status", "MOD"),
        ("Claims", "claim_reality_status", "CLM"),
        ("Style", "style_icon_status", "VIS"),
    ]
    has_non_pass_matrix = False
    for row in matrix:
        pack_name = str(row.get("pack_name", ""))
        for domain_name, status_key, rule_prefix in matrix_domains:
            status = str(row.get(status_key, "pass"))
            if status == "pass":
                continue
            has_non_pass_matrix = True
            triggers: list[str] = []
            for finding in findings:
                rule_id = str(finding.get("rule_id", ""))
                if not rule_id.startswith(rule_prefix):
                    continue
                finding_pack = finding.get("pack_name")
                if finding_pack in (None, "", pack_name):
                    finding_id = finding.get("finding_id", "unknown-finding")
                    triggers.append(f"`{finding_id}` (`{rule_id}`)")

            trigger_text = "; ".join(triggers) if triggers else "_no mapped finding ID_"
            lines.append(f"| {pack_name} | {domain_name} | {status} | {trigger_text} |")

    if not has_non_pass_matrix:
        lines.append("| _none_ | _n/a_ | pass | _all matrix cells are pass_ |")

    lines.extend(["", "## Findings", ""])
    if not findings:
        lines.append("- No findings")
    else:
        for finding in findings:
            finding_id = finding.get("finding_id", "unknown-finding")
            pack_scope = finding.get("pack_name") or "all-packs/global"
            lines.append(
                f"- [{finding.get('severity')}] `{finding.get('rule_id')}` `{finding_id}` "
                f"[scope: {pack_scope}] {finding.get('message')} ({finding.get('artifact_path')})"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


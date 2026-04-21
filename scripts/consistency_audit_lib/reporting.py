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

    lines.extend(["", "## Findings", ""])
    if not findings:
        lines.append("- No findings")
    else:
        for finding in findings:
            lines.append(
                f"- [{finding.get('severity')}] `{finding.get('rule_id')}` {finding.get('message')} "
                f"({finding.get('artifact_path')})"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


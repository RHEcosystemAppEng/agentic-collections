from __future__ import annotations

from pathlib import Path
from typing import Any


def _validate_required_fields(payload: dict[str, Any], required_fields: list[str], context: str) -> None:
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f"{context} missing required fields: {', '.join(missing)}")


def validate_audit_report(payload: dict[str, Any], schema_path: Path) -> None:
    # Minimal contract validation based on required fields from schema.
    # Kept lightweight to avoid adding new dependency just for JSON Schema runtime.
    _ = schema_path  # Explicitly consumed by caller for traceability.
    _validate_required_fields(
        payload,
        [
            "schema_version",
            "generated_at",
            "branch",
            "summary",
            "matrix",
            "findings",
            "policy_decisions",
            "remediation_plan",
        ],
        "audit report payload",
    )


def validate_ci_violations(payload: dict[str, Any], schema_path: Path) -> None:
    _ = schema_path
    _validate_required_fields(
        payload,
        ["status", "failure_threshold", "blocking_count", "violations"],
        "ci violations payload",
    )


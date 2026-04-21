from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Severity(str, Enum):
    BLOCKING = "blocking"
    HIGH = "high"
    MEDIUM = "medium"
    INFORMATIONAL = "informational"


class CiEnforcement(str, Enum):
    FAIL = "fail"
    WARN = "warn"
    REPORT = "report"


@dataclass
class Finding:
    finding_id: str
    rule_id: str
    severity: Severity
    artifact_path: str
    message: str
    ci_enforcement: CiEnforcement
    pack_name: str | None = None
    expected: str = ""
    actual: str = ""
    autofixable: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["severity"] = self.severity.value
        payload["ci_enforcement"] = self.ci_enforcement.value
        return payload


@dataclass
class MatrixRow:
    pack_name: str
    registration_status: str
    version_consistency_status: str
    model_metadata_status: str
    claim_reality_status: str
    style_icon_status: str
    overall_severity: str
    observed_versions: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Data Model: Collection Consistency Audit

## 1) Core Entities

### ConsistencyRule

Defines one auditable policy rule.

| Field | Type | Description |
|---|---|---|
| `rule_id` | string | Stable identifier (example: `VER-001`) |
| `scope` | enum | `pack` \| `skill` \| `docs-site` \| `marketplace` |
| `severity` | enum | `blocking` \| `high` \| `medium` \| `informational` |
| `check_method` | enum | `script` \| `schema` \| `regex` \| `computed` |
| `autofixable` | boolean | Whether automated remediation can be safely applied |
| `source_of_truth_files` | string[] | Authoritative file path list used for validation |
| `description` | string | Rule intent and pass criteria |
| `ci_enforcement` | enum | `fail` \| `warn` \| `report` |

### PackAuditRow

Represents one row in the per-pack consistency matrix.

| Field | Type | Description |
|---|---|---|
| `pack_name` | string | Pack identifier (example: `rh-sre`) |
| `registration_status` | enum | `registered` \| `missing` |
| `canonical_version` | string or null | Canonical version from source-of-truth (if applicable) |
| `observed_versions` | object | Versions found in root README, pack README, and `.catalog` metadata files |
| `model_metadata_summary` | object | Skill count, compliant count, missing model count, invalid values |
| `claim_reality_summary` | object | Claimed counts vs discovered counts (skills, agents, docs/orchestration claims) |
| `style_icon_summary` | object | Icon mapping existence and style token/hardcode findings |
| `status` | enum | `pass` \| `warn` \| `fail` |

### ConsistencyFinding

One concrete mismatch or policy violation.

| Field | Type | Description |
|---|---|---|
| `finding_id` | string | Deterministic ID for tracking |
| `rule_id` | string | Linked `ConsistencyRule` |
| `severity` | enum | `blocking` \| `high` \| `medium` \| `informational` |
| `pack_name` | string or null | Pack scope if applicable |
| `artifact_path` | string | File where finding originates |
| `expected` | string | Expected value/state |
| `actual` | string | Observed value/state |
| `message` | string | Human-readable explanation |
| `autofixable` | boolean | Mirrors rule/item capability |

### PolicyDecision

Documents resolved policy choices and branch decisions.

| Field | Type | Description |
|---|---|---|
| `decision_id` | string | Stable decision key |
| `topic` | enum | `versioning` \| `model-metadata` \| `visual-style` \| `scope-policy` |
| `decision` | string | Chosen policy statement |
| `applies_to` | string[] | Packs/artifacts affected |
| `effective_phase` | enum | `phase-a` \| `phase-b` \| `phase-c` |
| `notes` | string | Migration or exception details |

### RemediationItem

Prioritized action derived from one or more findings.

| Field | Type | Description |
|---|---|---|
| `item_id` | string | Remediation identifier |
| `priority` | enum | `p0` \| `p1` \| `p2` \| `p3` |
| `finding_ids` | string[] | Linked findings |
| `owner_area` | string | Responsible maintainer area |
| `target_artifacts` | string[] | Files to update |
| `guardrail_rule_ids` | string[] | CI checks preventing recurrence |

## 2) Consistency Rule Catalog (Initial)

| rule_id | scope | severity | check_method | autofixable | source_of_truth_files |
|---|---|---|---|---|---|
| `VER-001` | marketplace | blocking | computed | false | `marketplace/rh-agentic-collection.yml` |
| `VER-002` | pack | high | computed | true | `README.md`, `<pack>/README.md` |
| `VER-003` | pack | medium | schema | true | `<pack>/.catalog/collection.yaml`, `<pack>/.catalog/collection.json` |
| `MOD-001` | skill | blocking | script | false | `skills/*/SKILL.md`, `SKILL_DESIGN_PRINCIPLES.md` |
| `MOD-002` | skill | high | script | false | `scripts/validate_skill_design.py`, `scripts/validate-skills.sh` |
| `VIS-001` | docs-site | medium | regex | true | `docs/styles.css` |
| `VIS-002` | docs-site | high | regex | true | `docs/app.js`, `docs/icons.json`, `docs/plugins.json`, `docs/mcp.json` |
| `CLM-001` | pack | high | computed | false | `README.md`, `<pack>/README.md`, filesystem counts |

## 3) Per-Pack Matrix Projection

Each `PackAuditRow` is rendered to matrix columns:

1. `pack_name`
2. `registration_status`
3. `version_consistency_status`
4. `model_metadata_status`
5. `claim_reality_status`
6. `style_icon_status`
7. `overall_severity`

## 4) Severity to CI Mapping

| Severity | CI Behavior (Phase A) | CI Behavior (Phase B+) |
|---|---|---|
| `blocking` | fail | fail |
| `high` | warn | fail on changed scope |
| `medium` | warn | warn (optionally fail on changed scope later) |
| `informational` | report | report |

## 5) Registration Status Semantics

`PackAuditRow.registration_status` uses:

- `registered`: pack exists in source-of-truth registration and receives full parity checks.
- `missing`: pack is absent from registration and is flagged by applicable registration/version rules.

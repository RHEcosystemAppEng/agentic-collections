---
name: collection-compliance
description: |
  Diagnose and fix `.catalog/` validation failures (schema, roster, banners, sample workflows, JSON mirror). Use when:
  - `make validate` or CI reports collection compliance errors
  - A PR adds skills but catalog was not updated
  - `collection.json` is out of sync with `collection.yaml`

  Remediation is via the create-collection workflow and `catalog_yaml_to_json.py`—not by weakening checks.
model: inherit
color: yellow
allowed-tools: Read Glob Grep Bash
---

# Collection compliance

**Audience:** Contributors fixing `.catalog/` CI failures.

**Goal:** Clear reported violations from `scripts/validate_collection_compliance.py` and `scripts/validate_collection_schema.py`.

## Prerequisites

- Run from repository root.
- Read [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md).

## When to Use

- After `make validate-collection-compliance` fails locally or in GitHub Actions.

## Workflow

1. **Re-run** `uv run python scripts/validate_collection_compliance.py` and capture errors (pack path + message).

2. **Classify**
   - **Missing file** — create `.catalog/collection.yaml` via create-collection skill (or `uv run python scripts/bootstrap_catalog.py --pack <pack>` for bootstrap baseline).
   - **Schema** — align YAML with [catalog/collection.schema.json](../../catalog/collection.schema.json).
   - **Roster** — every `skills/<n>/SKILL.md` must appear once under `contents.skills` or `contents.orchestration_skills` with `name == <n>`.
   - **Banner** — `collection.yaml` must mention `create-collection` and `Golden sources` in the opening `#` block.
   - **`collection.json` drift** — run `uv run python scripts/catalog_yaml_to_json.py --pack <pack>` or `make catalog-mirror-json`.

3. **Re-validate** — `make validate-collection-compliance`.

## Dependencies

- create-collection skill (sibling under `.cursor/skills/`)

## Common Issues

- **`skills_decision_guide` with no skills** — guide must be `[]` if the pack has no `skills/` tree.
- **Orchestration miscount** — move skills that delegate end-to-end flows to `orchestration_skills` per COLLECTION_SPEC judgment rules.

## Example usage

```bash
make validate-collection-compliance
uv run python scripts/catalog_yaml_to_json.py --pack rh-developer
make validate-collection-compliance
```

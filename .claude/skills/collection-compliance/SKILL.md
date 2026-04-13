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
   - **Schema** — align YAML with [catalog/schema.yaml](../../catalog/schema.yaml).
   - **Roster** — every `skills/<n>/SKILL.md` must appear once under `contents.skills` or `contents.orchestration_skills` with `name == <n>`.
   - **Banner** — `collection.yaml` must mention `create-collection` and `Golden sources` in the opening `#` block.
   - **`collection.json` drift** — run `uv run python scripts/catalog_yaml_to_json.py --pack <pack>` or `make catalog-mirror-json`.
   - **Fragment refs / length** — `*_file` and `deploy_and_use` file refs must start with `#` and name a sibling `.md` under `.catalog/` (e.g. `#install.md`). Inline monitored fields over **500** code points must move to a fragment (see COLLECTION_SPEC).
   - **Fragment provenance (`.catalog/*.md`)** — each referenced fragment must start with a leading HTML **`<!-- … -->`** block with the **same intent** as the `collection.yaml` banner: **create-collection** workflow and **Golden sources** (SKILL, README, CLAUDE, marketplace). See [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md) **Provenance banners** (CI does not yet assert this text; fix when reviewing fragments).
   - **Thin `deploy_and_use` (manual review)** — if the pack has **`mcps.json`** MCP servers, **`deploy_and_use`** (inline or **`#deploy_and_use.md`**) should meet [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md) **install + env + MCP** (prerequisites, **`export`** for each **`${VAR}`** name, Lola **`path:`**, MCP notes, optional Claude/Cursor install). CI may not fail; fix via **create-collection** when reviewing PRs.

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

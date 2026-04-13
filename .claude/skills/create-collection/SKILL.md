---
name: create-collection
description: |
  Author or refresh `<pack>/.catalog/collection.yaml` and related `.catalog/` artifacts from golden sources (SKILL.md, README, CLAUDE.md, Lola marketplace). Use when:
  - Adding a new pack or refreshing the collection catalog for GitHub Pages / tooling
  - Aligning catalog narrative, sample workflows, and decision guide with skills on disk
  - Preparing a PR after changing skills or marketplace metadata

  Outputs only under `<pack>/.catalog/` (never overwrite README, SKILL, CLAUDE, or marketplace YAML).
model: inherit
color: blue
allowed-tools: Read Glob Grep Bash
---

# Create collection catalog

**Audience:** Maintainers and assistants updating per-pack `.catalog/` data.

**Goal:** Produce a coherent `collection.yaml` that passes `make validate-collection-compliance`, using human judgment for synthesis—not a blind dump of frontmatter.

## Prerequisites

- Repository root as cwd.
- Read [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md) and [catalog/collection.schema.json](../../catalog/collection.schema.json).
- Optional: run `uv run python scripts/scaffold_catalog.py <pack>` for a stdout draft roster.

## When to Use

- New marketplace module or new pack directory needs `.catalog/`.
- Skills were added/removed/renamed and roster parity must match disk.
- Marketplace `description` / `version` changed and catalog should reflect it (still edit marketplace in git separately).

## Workflow

1. **Resolve pack** — directory name must appear in `union(marketplace/modules[].path, docs/plugins.json keys)` and exist on disk.

2. **Read sources in order** (precedence):
   - `skills/*/SKILL.md` (frontmatter + body for summaries and orchestration hints)
   - `<pack>/README.md`
   - `<pack>/CLAUDE.md` (intent routing → `skills_decision_guide` ideas)
   - Matching row in `marketplace/rh-agentic-collection.yml` (`path` == pack)

3. **Classify skills** — place each skill in `contents.skills` or `contents.orchestration_skills` using maintainer judgment. Optional hint: `metadata.collection.role: orchestration` in `SKILL.md` frontmatter. Names in YAML **must** match the `skills/<name>/` directory name.

4. **Write `<pack>/.catalog/collection.yaml`** — start with the standard **# banner** (see COLLECTION_SPEC). Inline short fields; move prose longer than ~50 lines into `.catalog/*.md` and reference with `*_file` keys as needed.

5. **Mirror JSON** — from repo root: `uv run python scripts/catalog_yaml_to_json.py --pack <pack>` (or `make catalog-mirror-json`).

6. **Self-review checklist**
   - Every on-disk `skills/<n>/SKILL.md` appears exactly once in `skills` ∪ `orchestration_skills`.
   - No `TODO:` / `TBD` in `sample_workflows.workflow`; each workflow includes `User:` and `-` bullets.
   - `skills_decision_guide` empty if the pack has **no** skills; otherwise each `skill_to_use` matches a skill dir.
   - `resources[].url` set; `embedded_doc` only if that path exists under the pack.

7. **Validate** — `make validate-collection-compliance` before commit.

## Dependencies

- `make validate-collection-compliance`
- `uv run python scripts/scaffold_catalog.py <pack>` (optional)

## Common Issues

- **CI: `collection.json` drift** — regenerate with `make catalog-mirror-json`.
- **Roster errors** — YAML `name` must equal the skill folder name, not a display alias.
- **Empty support pack** — if there are no `skills/`, use empty `skills`, `orchestration_skills`, and `skills_decision_guide: []`.

## Example usage

```bash
uv run python scripts/scaffold_catalog.py rh-sre
uv run python scripts/catalog_yaml_to_json.py --pack rh-sre
make validate-collection-compliance
```

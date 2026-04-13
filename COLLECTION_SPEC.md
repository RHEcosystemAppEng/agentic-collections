# Collection catalog specification

This repository uses a **pack-local collection catalog**: curated metadata and summaries live under **`<pack>/.catalog/`** (YAML as the source of record, JSON as a deterministic mirror for consumers that prefer it). **Golden sources** are pack `SKILL.md` files, `README.md`, `CLAUDE.md`, and [`marketplace/rh-agentic-collection.yml`](marketplace/rh-agentic-collection.yml). Catalog files **describe** the collection for tooling and documentation; they are **authored** primarily via the [**create-collection**](.claude/skills/create-collection/SKILL.md) skill (assistant + maintainer + PR review) and must not overwrite READMEs or marketplace YAML.

**Machine validation:** [`collection.schema.json`](catalog/collection.schema.json) (JSON Schema) and [`scripts/validate_collection_compliance.py`](scripts/validate_collection_compliance.py). **Pack list:** union of Lola marketplace `modules[].path` and keys of [`docs/plugins.json`](docs/plugins.json), limited to directories that exist on disk — see [`scripts/pack_registry.py`](scripts/pack_registry.py).

## Layout

| Path | Purpose |
|------|---------|
| `<pack>/.catalog/collection.yaml` | Canonical catalog document (YAML) |
| `<pack>/.catalog/collection.json` | Deterministic JSON mirror of YAML (regenerate with `make catalog-mirror-json`; CI fails on drift) |
| `<pack>/.catalog/*.md` | Optional long prose fragments referenced via `*_file` keys when inline YAML is too large (threshold: **~50 lines** — align with maintainability; shorter content stays inline) |

**Plugin / install IDs:** default `id` equals the pack directory name. Overrides: **`rh-virt`** → `openshift-virtualization`; **`ocp-admin`** → `openshift-administration`.

## Source precedence (pack-local)

When multiple sources could supply the same logical field:

1. **`skills/*/SKILL.md`** (per-skill `name`, `description`, body for `summary_markdown` hints)
2. **`<pack>/README.md`**
3. **`<pack>/CLAUDE.md`** (intent routing for decision-guide hints, personas)

**Lola marketplace:** the module whose `path` equals `<pack>` supplies `version`, module `name`, module `description`, and `tags` for listing-oriented fields. **Never** write back to marketplace YAML from automation or the create-collection workflow.

## Provenance banners

| Artifact | Banner |
|----------|--------|
| `collection.yaml` | Leading `#` comment block: must mention **create-collection** workflow and **golden sources** (SKILL, README, CLAUDE, marketplace). |
| `.catalog/*.md` fragments | Leading HTML `<!-- ... -->` with the same intent. |
| `collection.json` | **No** embedded banner; **CI** regenerates from YAML and fails if the committed file differs. |

## Orchestration vs regular skills

**Primary:** maintainer / assistant judgment while following **create-collection**. **Optional:** `metadata.collection.role: orchestration` in `SKILL.md` frontmatter for clearer compliance checks — not required on every skill.

## Completeness and CI

All **required** schema fields must be present on merge to `main` (no empty placeholders, no `TODO:` / `TBD` in `sample_workflows.workflow`). CI runs **`make validate`** (includes structure + **collection compliance**).

## Related

- [`SKILL_DESIGN_PRINCIPLES.md`](SKILL_DESIGN_PRINCIPLES.md) — skill content (Tier 2)
- [`.claude/skills/collection-compliance/SKILL.md`](.claude/skills/collection-compliance/SKILL.md) — validation workflow

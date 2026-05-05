# Implementation Plan: Collection Consistency Audit

**Branch**: `001-collection-consistency-audit` | **Date**: 2026-04-14 | **Spec**: `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/specs/001-collection-consistency-audit/spec.md`
**Input**: Feature specification from `/specs/001-collection-consistency-audit/spec.md`

## Summary

Introduce a repository-native consistency audit workflow that builds a per-pack matrix and produces machine-readable plus markdown outputs covering version metadata, skill model metadata, docs visual/style tokens, and README claim-to-reality checks. Enforcement is incremental: blocking findings fail CI, high/medium findings are warning-only at first, and informational findings are reported for transparency.

## Technical Context

**Language/Version**: Python 3.11 (existing scripts), Bash (existing CI wrappers), Markdown/JSON/YAML for policy and report artifacts  
**Primary Dependencies**: Existing `uv` workflow, existing validation scripts in `scripts/`, existing GitHub Actions workflows in `.github/workflows/`  
**Storage**: Repository files only (no external database)  
**Testing**: Existing `make validate`, `make validate-skill-design`, and CI workflows; add audit checks as repository scripts and CI steps  
**Target Platform**: Linux CI runners (`ubuntu-latest`) and local contributor environments using `uv`  
**Project Type**: Monorepo policy and validation enhancement  
**Performance Goals**: Full audit completes within normal validation window and is suitable for PR-time execution on changed scope and full-main execution  
**Constraints**: Repository-native only; minimal disruption; incremental adoption with clear fail/warn/info boundaries; no secret exposure  
**Scale/Scope**: 6 packs (`rh-sre`, `rh-developer`, `ocp-admin`, `rh-virt`, `rh-ai-engineer`, `rh-automation`) plus docs-site metadata files and marketplace/readme sources

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Current constitution file is a template placeholder with no enforceable project-specific gates. No constitutional blockers identified; governance constraints are derived from existing repository standards and CI behaviors:

- Use existing script and CI patterns (`scripts/*.py`, `scripts/*.sh`, `make` targets, `.github/workflows/*`)
- Keep checks additive and incremental before tightening CI failure policy
- Preserve optional/placeholder pack handling through explicit policy instead of implicit exclusion

**Post-design re-check**: Passed. Generated artifacts keep all checks repository-native, avoid external infrastructure, and define incremental enforcement.

## Project Structure

### Documentation (this feature)

```text
specs/001-collection-consistency-audit/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── audit-report.schema.json
│   └── ci-violations.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
marketplace/
└── rh-agentic-collection.yml                 # Canonical version source for listed packs

README.md                                     # Root version/claims that must reconcile with audit matrix

rh-sre/README.md
rh-developer/README.md
ocp-admin/README.md
rh-virt/README.md
rh-ai-engineer/README.md
rh-automation/README.md                       # Pack-level version and claims

docs/
├── styles.css
├── app.js
├── icons.json
├── plugins.json
└── mcp.json                                  # Visual/style token and icon metadata sources

scripts/
├── validate_structure.py
├── validate_skill_design.py
├── validate-skills.sh
├── run-skill-linter.sh
└── ci-validate-changed-skills.sh             # Existing enforcement baseline to extend

.github/workflows/
├── compliance-check.yml
└── skill-spec-report.yml                     # CI insertion points for audit guardrails
```

**Structure Decision**: Extend existing `scripts/` and GitHub Actions workflows with audit logic and contract-driven outputs, rather than introducing a new framework or external service.

## Enforcement Boundary Strategy

### CI Failure Levels

- **Blocking (fail CI now)**:
  - Missing required model frontmatter in any in-scope skill
  - Invalid model values (must be `inherit|sonnet|haiku`)
  - Inconsistent canonical version between marketplace module entry and policy-authoritative pack metadata
- **High/Medium (warning-only initially, promotable later)**:
  - README claim mismatch (skill/agent/orchestration counts) where metadata can be corrected without runtime breakage
  - Style token drift and hardcoded visual values outside canonical token set
  - Non-canonical duplicate version declarations that do not conflict with canonical value
- **Informational**:
  - Optional metadata enhancements, non-blocking style normalization opportunities, and docs clarity improvements

### Incremental Adoption

1. **Phase A**: Generate report + warnings, block only severe metadata violations.
2. **Phase B**: Require zero high findings on changed scope.
3. **Phase C**: Enable strict mode for full repository on main.

## Complexity Tracking

No constitution violations requiring justification at planning time.

# Research: Collection Consistency Audit

## Decision 1: Canonical Version Source-of-Truth

**Decision**: Use `marketplace/rh-agentic-collection.yml` module `version` as canonical for all marketplace-listed packs. Treat root and pack README versions as derived presentation values that must reconcile to marketplace values.

**Rationale**:
- Marketplace file is the install source used by Lola and already defines module-level versions.
- Root and pack READMEs currently contain version claims that can drift from marketplace values.
- Centralizing on one canonical source reduces ambiguity and simplifies CI checks.

**Alternatives considered**:
- Root `README.md` as canonical: rejected because it is descriptive and currently drift-prone.
- Pack-local README as canonical: rejected due to duplication and poor cross-pack consistency.
- Optional plugin metadata as canonical: rejected because plugin metadata is optional and currently absent.

## Decision 2: Model Metadata Policy Reconciliation

**Decision**: Enforce model frontmatter presence and valid values (`inherit|sonnet|haiku`) for every in-scope `skills/*/SKILL.md`, and align all validators/documentation to that policy.

**Rationale**:
- `SKILL_DESIGN_PRINCIPLES.md` defines model as mandatory with explicit allowed values.
- `scripts/validate-skills.sh` already enforces mandatory model and allowed values.
- `scripts/validate_skill_design.py` currently treats model as optional, creating policy drift between validators.
- Aligning enforcement removes confusion and prevents contradictory CI outcomes.

**Alternatives considered**:
- Keep model optional in Tier 2 validator: rejected because it conflicts with repository principles and shell validator behavior.
- Expand model vocabulary now: rejected to minimize disruption and avoid policy churn.

## Decision 3: Current Enforcement Map (Reality Baseline)

**Decision**: Build audit logic from current enforcement behaviors and explicitly document gaps:
- `scripts/validate_structure.py`: pack structure checks (`mcps.json`, optional plugin metadata, `CLAUDE.md` routing completeness).
- `scripts/validate_skill_design.py`: Tier 2 principles (currently with model optionality gap).
- `scripts/validate-skills.sh` and `scripts/run-skill-linter.sh`: skill frontmatter and structure enforcement.
- `.github/workflows/compliance-check.yml`: runs `make validate` + changed-skill design validation.
- `.github/workflows/skill-spec-report.yml`: skill specification linter with fail-on-errors.

**Rationale**:
- The new audit must integrate existing CI signals instead of replacing them.
- Existing checks already cover many prerequisites needed by consistency reporting.

**Alternatives considered**:
- Replace existing validators with one monolith: rejected due to migration risk and disruption.
- Run audit only offline: rejected because drift prevention requires CI integration.

## Decision 4: Per-Pack Consistency Matrix Shape

**Decision**: Define one normalized row per pack with these sections:
- registration/version: marketplace registration status, canonical version, non-canonical version observations
- model metadata: skill counts, missing/invalid model declarations, policy compliance
- claim-to-reality: README claim values vs discovered filesystem counts
- style/icon mapping: plugin title/icon mappings, token usage references, hardcoded style evidence

**Rationale**:
- Matrix rows provide a deterministic, comparable baseline across all in-scope packs.
- Supports severity classification and CI policy decisions from one unified model.

**Alternatives considered**:
- Separate reports per domain only: rejected because cross-domain triage is harder.
- Per-file findings only: rejected because pack-level ownership and prioritization are unclear.

## Decision 5: Visual/Style Token Governance

**Decision**: Introduce canonical style token policy anchored to `docs/styles.css` CSS variables and validate dependent files (`docs/app.js`, `docs/icons.json`, `docs/plugins.json`, `docs/mcp.json`) against those tokens and size conventions.

**Rationale**:
- Current docs files include both tokenized styles and hardcoded inline style values.
- Token-first rules are lower-risk and enable gradual reduction of hardcoded values.
- Required files are already centralized and can be validated with repository scripts.

**Alternatives considered**:
- Full immediate refactor of all inline styles: rejected as high disruption.
- No style enforcement in CI: rejected because drift would continue.

## Decision 6: CI Enforcement Boundaries

**Decision**:
- `blocking` findings fail CI immediately (critical metadata integrity issues).
- `high` and `medium` are warning-only initially, with promotion path to fail-on-changed-scope.
- `informational` always non-blocking.

**Rationale**:
- Matches "minimal disruption + incremental adoption" constraint.
- Preserves merge velocity while creating clear tightening path.

**Alternatives considered**:
- Fail on all severities now: rejected due to likely broad initial breakage.
- Report-only forever: rejected because no drift prevention.

## Decision 7: Active-Scope Normalization

**Decision**: Limit consistency-audit scope to active marketplace/repository packs and remove `rh-support-engineer` from audit coverage.

**Rationale**:
- Prevents recurring false-positive findings against a removed pack.
- Keeps matrix and CI outputs focused on currently maintained collections.

**Alternatives considered**:
- Keep policy-based exclusion branch: rejected because it adds maintenance overhead for an out-of-scope pack.

# Tasks: Collection Consistency Audit

**Input**: Design documents from `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/specs/001-collection-consistency-audit/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: No new standalone test-suite tasks are required by spec; each user story includes executable validation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`) for story-phase tasks only
- Every task includes an exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the audit implementation scaffold and policy/config entry points.

- [X] T001 Create audit script package directory at `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/`
- [X] T002 Create CLI entrypoint scaffold in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit.py`
- [X] T003 [P] Create rule catalog file in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_rules.yml`
- [X] T004 [P] Add consistency audit Make target definitions in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/Makefile`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared loading, schema validation, severity policy, and reusable report plumbing.

**CRITICAL**: User story work starts only after this phase.

- [X] T005 Implement repository file discovery utilities in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/discovery.py`
- [X] T006 [P] Implement canonical source loaders for marketplace/readme/docs assets in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/sources.py`
- [X] T007 [P] Implement findings and severity model objects from data model in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/models.py`
- [X] T008 Implement audit-report and CI-violations schema validators in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/contracts.py`
- [X] T009 Implement severity-to-CI enforcement mapper (`fail|warn|report`) in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/enforcement.py`
- [X] T010 Implement JSON/Markdown report writers using schema contracts in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/reporting.py`
- [X] T011 Wire CLI flags (`--format`, `--output`, `--ci`, `--changed-only`) to foundational modules in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit.py`

**Checkpoint**: Foundation complete; user-story audits can now be implemented independently.

---

## Phase 3: User Story 1 - Produce a Cross-Collection Consistency Baseline (Priority: P1) 🎯 MVP

**Goal**: Deliver a per-pack metadata consistency baseline with canonical version alignment and claim-to-reality findings.

**Independent Test**: Run the audit CLI and confirm output includes all seven packs, matrix rows, version/registration status, claim findings, and severity classifications.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement pack-scope matrix row generation in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/matrix.py`
- [X] T013 [US1] Implement marketplace registration and canonical version checks against `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/marketplace/rh-agentic-collection.yml` in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/version_checks.py`
- [X] T014 [US1] Implement root and pack README version reconciliation checks for `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/README.md`, `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/rh-sre/README.md`, `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/rh-developer/README.md`, `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/ocp-admin/README.md`, `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/rh-support-engineer/README.md`, `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/rh-virt/README.md`, `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/rh-ai-engineer/README.md`, and `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/rh-automation/README.md` in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/readme_version_checks.py`
- [X] T015 [US1] Implement dedicated root README claim drift check (skill count totals and “agents vs orchestration skills” wording) in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/readme_claim_checks.py`
- [X] T016 [US1] Implement dedicated rh-support-engineer policy branch check (registered vs explicit exclusion note) in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/scope_policy_checks.py`
- [X] T017 [US1] Add explicit `rh-support-engineer` policy documentation section in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/README.md`
- [X] T018 [US1] Implement baseline severity summary aggregation (blocking/high/medium/informational) in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/summary.py`
- [X] T019 [US1] Validate that README and marketplace references are internally consistent by running and documenting output examples in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/specs/001-collection-consistency-audit/quickstart.md`

**Checkpoint**: Baseline matrix and authoritative source alignment are functional and independently verifiable.

---

## Phase 4: User Story 2 - Establish Explicit Consistency Policies (Priority: P2)

**Goal**: Enforce and align model/frontmatter policy across documentation and validators.

**Independent Test**: Introduce a temporary invalid or missing model declaration and confirm audit + validator outputs flag it with enforceable severity and aligned messaging.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement skill frontmatter model/color scanner for `skills/*/SKILL.md` in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/model_metadata_checks.py`
- [X] T021 [US2] Update `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/validate_skill_design.py` to require `model` presence and enforce valid model values aligned with repository policy
- [X] T022 [US2] Update `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/SKILL_DESIGN_PRINCIPLES.md` where necessary to keep model/color policy and enforcement statements consistent with validators
- [X] T023 [US2] Add model/color policy consistency checks between shell and Python validators in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/validator_alignment_checks.py`
- [X] T024 [US2] Update local validation guidance for model policy enforcement in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/README.md`
- [X] T025 [US2] Verify skill model/color policy checks are enforceable via script by running documented commands and recording expected pass/fail behavior in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/specs/001-collection-consistency-audit/quickstart.md`

**Checkpoint**: Model/frontmatter policy is explicit, validator-aligned, and script-enforceable.

---

## Phase 5: User Story 3 - Plan and Enforce Drift Prevention (Priority: P3)

**Goal**: Normalize docs visual/style metadata and add CI guardrails to prevent future drift.

**Independent Test**: Introduce a temporary hardcoded style or icon mapping gap and confirm the audit reports it with expected severity and CI behavior.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement style token extraction and hardcoded style detection for `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/docs/styles.css` and `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/docs/app.js` in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/style_checks.py`
- [X] T027 [P] [US3] Implement icon and title mapping completeness checks for `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/docs/icons.json` and `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/docs/plugins.json` in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/icon_mapping_checks.py`
- [X] T028 [US3] Implement MCP presentation metadata consistency checks for `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/docs/mcp.json` in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/scripts/consistency_audit_lib/checks/mcp_metadata_checks.py`
- [X] T029 [US3] Refactor conflicting hardcoded style values to canonical token usage in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/docs/app.js`
- [X] T030 [US3] Add optional centralized style token metadata file at `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/docs/style-tokens.json` and align docs checks to it where practical
- [X] T031 [US3] Add CI drift-check step for consistency audit in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/.github/workflows/compliance-check.yml`
- [X] T032 [US3] Add changed-scope consistency audit invocation for PRs in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/.github/workflows/skill-spec-report.yml`
- [X] T033 [US3] Verify docs-site style tokens and icon mappings are complete and single-sourced where possible, and document verification procedure in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/specs/001-collection-consistency-audit/quickstart.md`

**Checkpoint**: Visual/style consistency and CI drift prevention are operational.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation, contributor guidance, and rollout hardening.

- [X] T034 [P] Update consistency-audit contributor guide and command reference in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/docs/README.md`
- [X] T035 [P] Add remediation and severity interpretation guidance for contributors in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/README.md`
- [X] T036 Add rollout notes for fail/warn/report policy phases in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/specs/001-collection-consistency-audit/quickstart.md`
- [X] T037 Run end-to-end local validation commands and capture final expected workflow in `/wip/src/github.com/RHEcosystemAppEng/agentic-collections/specs/001-collection-consistency-audit/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: starts immediately.
- **Phase 2 (Foundational)**: depends on Phase 1; blocks all user stories.
- **Phase 3 (US1)**: depends on Phase 2; delivers MVP baseline.
- **Phase 4 (US2)**: depends on Phase 2 and can run after US1 baseline scaffolding is stable.
- **Phase 5 (US3)**: depends on Phase 2; CI integration should follow completion of US1/US2 checks.
- **Phase 6 (Polish)**: depends on completion of desired story phases.

### User Story Dependencies

- **US1 (P1)**: no dependency on other stories; required for initial baseline and policy branch resolution.
- **US2 (P2)**: uses shared foundation; references US1 severity/report structures but remains independently verifiable.
- **US3 (P3)**: uses shared foundation; CI drift gates should include outputs from US1 and US2 checks.

### Within Each User Story

- Implement check modules before wiring them into CLI summaries.
- Update docs/policies after checks produce expected findings.
- Perform story-specific validation task before moving to next priority.

### Parallel Opportunities

- Setup: T003 and T004 in parallel after T001/T002.
- Foundational: T006 and T007 parallel; T008 and T009 parallel once models exist.
- US1: T012 can run while T013/T014 are implemented; T016 can proceed after registration parser exists.
- US2: T020 and T023 parallel; doc updates T022 and T024 parallel.
- US3: T026 and T027 parallel; workflow edits T031 and T032 parallel.
- Polish: T034 and T035 parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel check implementation for baseline matrix:
Task: "T013 [US1] Implement marketplace registration and canonical version checks in scripts/consistency_audit_lib/checks/version_checks.py"
Task: "T015 [US1] Implement root README claim drift check in scripts/consistency_audit_lib/checks/readme_claim_checks.py"

# Parallel documentation/policy alignment once checks exist:
Task: "T017 [US1] Add rh-support-engineer policy section in README.md"
Task: "T019 [US1] Document README/marketplace consistency verification in specs/001-collection-consistency-audit/quickstart.md"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1) to deliver baseline matrix + source-of-truth alignment.
3. Validate US1 independently via CLI report outputs and README/marketplace consistency checks.
4. Demo baseline report and severity taxonomy before policy expansion.

### Incremental Delivery

1. Deliver US1 baseline and policy branch resolution (`rh-support-engineer` decision).
2. Add US2 validator and model policy alignment.
3. Add US3 style normalization and CI drift checks.
4. Finish with polish and contributor guidance updates.

### Team Parallel Strategy

1. One developer completes Setup/Foundational.
2. After foundation:
   - Developer A: US1 baseline and claim/version checks.
   - Developer B: US2 model validator alignment.
   - Developer C: US3 style/icon checks and CI wiring.
3. Integrate and complete Phase 6 polish.

---

## Notes

- `[P]` tasks are designed to avoid same-file merge conflicts when possible.
- Story labels map each task to spec priorities (`P1` -> `US1`, `P2` -> `US2`, `P3` -> `US3`).
- Dedicated required tasks are included for:
  - root README skill-count + wording drift (`T015`)
  - `rh-support-engineer` inclusion/exclusion policy (`T016`, `T017`)
  - CI automated drift checks (`T031`, `T032`)

# PR #63 Feedback Action Items (Pre-Rebase, Decision-Locked)

This list captures the PR #63 follow-up work after Phase 0 decisions were finalized.
It is intentionally scoped to pre-rebase planning and execution ordering.

## Finalized Decisions (Phase 0)

- **D0.1**: Remove `rh-support-engineer` from consistency-audit scope.
- **D0.2**: Keep skill `model` policy as `inherit | sonnet | haiku`.
- **D0.3**: Change `rh-sre/skills/playbook-generator/SKILL.md` color to `yellow`.
- **D0.4**: Do not adopt `spec-kit` workflow in this repository; remove/de-emphasize references.

## Phase 1 - Decision-Driven Remediation

- [X] **F001 (D0.1)** Update pack scope in `scripts/consistency_audit_lib/discovery.py` to remove `rh-support-engineer`.
- [X] **F002 (D0.1)** Remove `rh-support-engineer` policy branch logic from runtime audit code (`scripts/consistency_audit_lib/checks/scope_policy_checks.py` and wiring in `scripts/consistency_audit.py`).
- [X] **F003 (D0.1)** Remove `SCP-001` from `scripts/consistency_rules.yml` and align rule catalog references in docs/spec artifacts.
- [X] **F004 (D0.1)** Update scope-dependent checks and docs to six-pack scope (`README.md`, `specs/001-collection-consistency-audit/spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`).
- [X] **F005 (D0.3)** Set `color: yellow` in `rh-sre/skills/playbook-generator/SKILL.md`.
- [X] **F006 (D0.2)** Keep model-policy enforcement unchanged (`inherit|sonnet|haiku`) and verify docs/validators remain aligned (no inherit-only migration work).
- [X] **F007 (D0.4)** Remove/de-emphasize `spec-kit` workflow references from contributor-facing docs and ensure spec-kit artifacts are not treated as required project workflow.

## Phase 2 - Remaining Reviewer Feedback (Still Applicable)

- [X] **F008** Stop tracking generated report artifacts in git (`reports/`) and add ignore rule in `.gitignore`.
- [X] **F009** Add graceful missing-file handling (`Path.exists`) in:
  - `scripts/consistency_audit_lib/checks/style_checks.py`
  - `scripts/consistency_audit_lib/checks/icon_mapping_checks.py`
- [X] **F010** Revisit `docs/data.json` auditing in `scripts/consistency_audit_lib/checks/docs_data_checks.py` so generated/ignored docs data does not create noisy false-positive findings.
- [X] **F011** Improve report clarity in markdown output (`scripts/consistency_audit_lib/reporting.py`) so matrix `warn/fail` statuses are explicitly traceable to findings/rules.
- [X] **F012** Remove outdated `.claude-plugin/plugin.json` assumptions from `specs/001-collection-consistency-audit/data-model.md` and align with current Lola/.catalog compliance model.
- [X] **F013** Confirm consistency checks are integrated into existing validation flow (Make + CI) with low-friction defaults.

## Post-Rebase Validity Check (2026-05-04)

- Rebase onto `origin/main` completed successfully.
- `F001`-`F007` remain valid and completed on the rebased branch.
- `F008`-`F012` were executed and completed after the rebase pass.
- `F013` is now validated as complete (Make target + CI workflow integration confirmed).

# Quickstart: Collection Consistency Audit

## Purpose

Run metadata and style consistency checks locally, then enforce drift prevention in CI with minimal disruption.

## 1) Run Existing Baseline Checks

From repository root:

```bash
make validate
make validate-skill-design
```

For local incremental work:

```bash
make validate-skill-design-changed
```

## 2) Run Consistency Audit

Repository-native commands:

```bash
# Full matrix + findings for all packs
uv run python scripts/consistency_audit.py --format json --output reports/consistency-audit.json

# Human-readable markdown summary
uv run python scripts/consistency_audit.py --format markdown --output reports/consistency-audit.md

# CI gate mode (fails by policy threshold)
uv run python scripts/consistency_audit.py --ci
```

Expected outputs follow contracts in:

- `specs/001-collection-consistency-audit/contracts/audit-report.schema.json`
- `specs/001-collection-consistency-audit/contracts/ci-violations.schema.json`

## 3) Validate README and Marketplace Consistency

Run the audit and verify that the matrix and findings reflect internal consistency for:

- `marketplace/rh-agentic-collection.yml`
- root `README.md`
- pack `README.md` files

Recommended check:

```bash
uv run python scripts/consistency_audit.py --format markdown --output reports/consistency-audit.md
```

Then confirm in report output:

- all in-scope packs appear in matrix rows
- registration/version findings are severity-classified
- claim findings include root README skill count and wording checks

## 4) Verify Model/Color Policy Enforceability

Run all model-policy validators:

```bash
make validate-skill-design
./scripts/validate-skills.sh
uv run python scripts/consistency_audit.py --format json --output reports/consistency-audit-model.json
```

Expected behavior:

- missing/invalid `model` values are flagged as blocking
- non-standard `color` values are detected and reported
- validator drift between shell/Python checks is reported

## 5) Verify Style/Icon Single-Source Consistency

Validate style token and icon mapping consistency:

```bash
uv run python scripts/consistency_audit.py --format json --output reports/consistency-audit-style.json
```

Confirm that:

- token metadata exists in `docs/style-tokens.json`
- icon mappings in `docs/icons.json` cover all packs
- titles in `docs/plugins.json` cover all packs
- `docs/app.js` avoids hardcoded hex/rgba values where practical

## 6) Severity and CI Behavior

- `blocking`: fail CI immediately
- `high`: warning-only in initial rollout; promotable to fail on changed scope
- `medium`: warning-only
- `informational`: report-only

CI policy should be explicit and versioned in repository scripts/workflows.

## 7) Safe Metadata Updates

When updating versions or metadata:

1. Update canonical version in `marketplace/rh-agentic-collection.yml`
2. Reconcile root `README.md` and affected pack `README.md`
3. If optional plugin metadata exists, reconcile plugin version too
4. Re-run local validation and consistency audit before opening PR

## 8) Safe Style/Icon Updates

When updating docs presentation:

1. Prefer tokens in `docs/styles.css` over hardcoded color/size values
2. Keep icon mappings in `docs/icons.json` and pack titles in `docs/plugins.json` synchronized
3. Validate MCP presentation metadata in `docs/mcp.json`
4. Regenerate site data (`make generate`) and verify rendering (`make test`)

## 9) Rollout Phases (Fail/Warn/Report)

1. **Phase A**: fail on blocking findings, warn on high/medium, report informational.
2. **Phase B**: fail on blocking + high findings for changed scope.
3. **Phase C**: strict mode on main for full repository scans.

## 10) Recommended PR Checklist

- Run: `make validate`
- Run: `make validate-skill-design-changed` (or full)
- Run consistency audit in markdown and JSON modes
- Attach/report severity summary and remediation deltas
- Ensure no new blocking findings before merge

## 11) End-to-End Validation Flow

```bash
make validate
make validate-skill-design
make validate-consistency-audit
make validate-consistency-audit-ci
```

Expected result:

- structure and skill checks pass
- consistency reports are generated in `reports/`
- CI gate command exits successfully when no blocking findings remain

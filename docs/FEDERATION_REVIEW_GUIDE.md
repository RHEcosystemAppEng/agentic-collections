# Federation Review Guide

Step-by-step guide for maintainers evaluating a [Federation Request](https://github.com/RHEcosystemAppEng/agentic-collections/issues/new?template=federation-request.yml).

Federation means referencing an **external agentic pack** in our catalog. The code stays in the external repo — we don't copy or modify it. Users install federated packs directly from the external repo via Lola.

## Two ways to review

| Method | When to use |
|--------|------------|
| **`/federation-review` skill** | Interactive review from Claude Code. Reads the issue, runs validation, guides you through manual checks, and creates the registration PR if approved. |
| **Manual (this guide)** | Step-by-step commands when you prefer to review without Claude Code. |

CI also runs automated validation on any PR with the `federation` label (see [CI automation](#ci-automation) below).

---

## Automated validation (recommended)

Steps 1–6 can be run with a single command from the agentic-collections repo root:

```bash
# Full pack at repo root
uv run python scripts/validate_federation.py <repo-url> <ref>

# Pack in a subdirectory
uv run python scripts/validate_federation.py <repo-url> <ref> --pack-path <path>

# Only specific skills
uv run python scripts/validate_federation.py <repo-url> <ref> --skills <skill1> <skill2>

# JSON output (for CI)
uv run python scripts/validate_federation.py <repo-url> <ref> --json
```

The script checks: clone access, Lola structure, Tier 1, Tier 2, MCP version pinning, and gitleaks. If all pass, the pack is ready for manual review (steps 7–8).

---

## Manual steps

### Step 1: Verify access and basic info

- [ ] Repository URL is reachable and public
- [ ] The ref (SHA or tag) exists: `git ls-remote <repo-url> <ref>`
- [ ] Owner/contact information is provided
- [ ] License file exists in the repo and is compatible with Apache 2.0 (e.g., Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause)

```bash
git clone --no-checkout <repo-url> /tmp/federation-review
cd /tmp/federation-review
git checkout <ref>
```

### Step 2: Verify Lola pack structure

The pack must have the minimum structure for Lola installation:

```
<pack>/
├── CLAUDE.md        # Required: persona, intent routing, rules
├── README.md        # Required: description, prerequisites, installation
├── mcps.json        # Required: MCP server configs (can be empty: {"mcpServers": {}})
└── skills/          # Required: at least one skill
    └── <skill>/
        └── SKILL.md # Required: YAML frontmatter + implementation
```

```bash
ls CLAUDE.md README.md mcps.json skills/*/SKILL.md
```

If the request is for a **subset of skills** (not the full pack), verify only the listed skill paths exist.

### Step 3: Validate skills — Tier 1 (agentskills.io spec)

Tier 1 is **mandatory**. Run the linter on each skill:

```bash
# From the agentic-collections repo root:
for skill_dir in /tmp/federation-review/skills/*/; do
  ./scripts/run-skill-linter.sh "$skill_dir"
done
```

**Result:** All skills must pass (exit code 0). Warnings are acceptable; errors block federation.

### Step 4: Validate skills — Tier 2 (design principles)

Tier 2 is **mandatory**. Run the design principles validator:

```bash
uv run python scripts/validate_skill_design.py /tmp/federation-review
```

See [SKILL_DESIGN_PRINCIPLES.md](../SKILL_DESIGN_PRINCIPLES.md) for the full list of design principles.

### Step 5: Validate MCP configuration

If the pack uses MCP servers (`mcps.json` is not empty):

- [ ] **No `:latest` tags** — All container images must use pinned versions or SHAs
- [ ] **No hardcoded credentials** — All secrets use `${ENV_VAR}` format

```bash
grep -r ":latest" mcps.json && echo "FAIL: found :latest" || echo "PASS: no :latest"
```

### Step 6: Security review

- [ ] No credentials or secrets in any file
- [ ] Destructive operations have human-in-the-loop confirmation

```bash
gitleaks detect --source /tmp/federation-review --verbose
```

LLM-based security scan is triggered **on-demand** by a maintainer due to cost.

### Step 7: AI agent compatibility

Verify the declared AI agent compatibility from the issue:

- [ ] If **Claude Code** is declared: CLAUDE.md exists with proper intent routing
- [ ] If **Cursor** is declared: check for Cursor-compatible configuration
- [ ] If **ChatGPT** is declared: check for ChatGPT-compatible configuration

### Step 8: Decision

| Result | Action |
|--------|--------|
| All checks pass | Approve — create registration PR with label `federation` |
| Minor issues | Comment on issue with specific fixes, label `federation/changes-requested` |
| Major issues | Reject with explanation, label `federation/rejected`, close issue |

When approving, add the pack to `marketplace/rh-agentic-collection.yml` under `federated_modules` (include the `license` field from the issue) and link back to the issue.

---

## CI automation

PRs with the `federation` label automatically trigger the **Federation Validation** workflow (`.github/workflows/federation-validation.yml`). It:

1. Reads `federated_modules` from `marketplace/rh-agentic-collection.yml`
2. Runs `scripts/validate_federation.py` on each entry
3. Posts a summary comment on the PR with pass/fail results

The label-based trigger ensures validation only runs on federation PRs, not on every marketplace YAML change.

---

## Cleanup

```bash
rm -rf /tmp/federation-review
```

## Quick reference

| Check | Required | Automated | Tool/Command |
|-------|----------|-----------|--------------|
| Public access | Yes | Yes | `git ls-remote` |
| License compatibility | Yes | No | Manual review |
| Lola pack structure | Yes | Yes | `scripts/validate_federation.py` |
| Tier 1 (agentskills.io) | Yes | Yes | `scripts/validate_federation.py` |
| Tier 2 (design principles) | Yes | Yes | `scripts/validate_federation.py` |
| MCP version pinning | Yes | Yes | `scripts/validate_federation.py` |
| Credential scan | Yes | Yes | `gitleaks` via script |
| AI agent compatibility | Yes | No | Manual review |
| Security scan (LLM) | On-demand | No | Maintainer-triggered |

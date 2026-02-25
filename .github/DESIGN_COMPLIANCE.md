# Design Compliance Check

Automated merge-blocking PR check that evaluates skill and agent definitions
in this repository against the design principles defined in
[CLAUDE.md](../CLAUDE.md).

---

## How it works

```
PR opened / updated
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Collect diff  (changed *.md / *.yml / *.json files)          │
│ 2. Deterministic pre-checks (no LLM, fast):                     │
│      • YAML frontmatter present and contains required fields    │
│      • Required ## sections present (Prerequisites, Workflow…)  │
│      • Agent files do NOT reference MCP tools directly          │
│      • Document Consultation sections include "Read tool" step  │
│ 3. GitHub Models LLM analysis (gpt-4o-mini by default):         │
│      • Sends policy text + filtered diff                        │
│      • Requires strictly structured JSON response               │
│      • Checks deeper design principle compliance                │
│ 4. Produce JSON report → upload as workflow artifact            │
│ 5. Write Markdown summary → GitHub job summary page             │
│ 6. Exit 0 (pass) or 1 (fail)                                    │
└─────────────────────────────────────────────────────────────────┘
```

The workflow is intentionally **safe for fork PRs**: it uses the
`pull_request` event (not `pull_request_target`), so it runs with
read-only `GITHUB_TOKEN` permissions and no access to repository secrets.

---

## Enabling branch protection (required status check)

1. Go to **Settings → Branches** in the GitHub repository.
2. Click **Add branch protection rule** (or edit the existing `main` rule).
3. Enable **Require status checks to pass before merging**.
4. Search for and add: **`design-compliance`**
   (this is the exact job name in
   `.github/workflows/design-compliance.yml`).
5. Optionally enable **Require branches to be up to date before merging**.
6. Save the rule.

Once the rule is active, every PR that touches skill or agent files will
require a green `design-compliance` check before it can be merged.

---

## Tuning the policy file

Policy lives in [`policy/design-compliance.yml`](../policy/design-compliance.yml).

| Key | Purpose |
|-----|---------|
| `model.name` | GitHub Models model to use (e.g. `gpt-4o-mini`, `gpt-4o`) |
| `model.max_tokens` | Maximum tokens in the LLM response |
| `model.temperature` | Sampling temperature (lower = more deterministic) |
| `diff_limits.max_bytes` | Max bytes of diff sent to the LLM per run |
| `deterministic_checks.mcp_tool_denylist` | MCP tool name patterns that must not appear in agent files |
| `deterministic_checks.skill_required_frontmatter` | YAML frontmatter fields every skill must have |
| `deterministic_checks.agent_required_frontmatter` | YAML frontmatter fields every agent must have |
| `deterministic_checks.skill_required_sections` | `##` headings every skill must contain |
| `deterministic_checks.agent_required_sections` | `##` headings every agent must contain |

### Adding new MCP tool patterns

When a new MCP server is added to the repository, add its tool name prefix
to `mcp_tool_denylist` so the deterministic check catches any accidental
direct usage inside agent files:

```yaml
deterministic_checks:
  mcp_tool_denylist:
    - "my_new_server__"   # ← add this line
```

---

## Reading the JSON report

The artifact `design-compliance-report` (downloadable from the Actions run)
contains a JSON file with the following structure:

```jsonc
{
  "compliant": false,                  // overall pass/fail
  "deterministic_violations": [        // caught by pre-checks (no LLM)
    {
      "file": "rh-sre/agents/foo.md",
      "principle": "Core Architecture - Agents orchestrate skills…",
      "description": "Agent file references MCP tool pattern 'vulnerability__' directly.",
      "line": "42"
    }
  ],
  "llm_violations": [                  // caught by GitHub Models LLM
    {
      "file": "rh-virt/skills/bar/SKILL.md",
      "principle": "1 - Document Consultation Transparency",
      "description": "Document Consultation section lacks 'Read tool' action step.",
      "line": "N/A"
    }
  ],
  "warnings": [],                      // non-blocking observations
  "summary": "Found 2 violations…",   // 1-3 sentence summary
  "files_checked": ["rh-sre/agents/foo.md", "rh-virt/skills/bar/SKILL.md"],
  "llm_model": "gpt-4o-mini",
  "llm_used": true,
  "llm_error": null                    // set if LLM call failed
}
```

### Triaging violations

| Field | What to do |
|-------|-----------|
| `deterministic_violations` | Fix before the LLM even runs. These are clear, mechanical rule breaches. |
| `llm_violations` | Review carefully – the LLM may occasionally over-flag. If a finding is a false positive, note it in the PR and the reviewer can dismiss. |
| `warnings` | Non-blocking. Address in a follow-up if appropriate. |
| `llm_error` | The API call failed. Deterministic checks still ran. Rerun the workflow or check GitHub Models status. |

---

## Running locally

```bash
# Install dependencies (if not already done via make install)
pip install requests pyyaml

# Generate a local diff against main
git diff origin/main...HEAD -- '*.md' '*.yml' '*.yaml' '*.json' > /tmp/pr.diff

# Run the check (set GITHUB_TOKEN to a PAT with GitHub Models access)
export GITHUB_TOKEN="ghp_…"
python scripts/design_compliance.py \
  --diff-file    /tmp/pr.diff \
  --policy-file  policy/design-compliance.yml \
  --output-file  /tmp/compliance-report.json \
  --summary-file /tmp/compliance-summary.md

# To run deterministic checks only (no API call):
python scripts/design_compliance.py \
  --diff-file    /tmp/pr.diff \
  --policy-file  policy/design-compliance.yml \
  --output-file  /tmp/compliance-report.json \
  --skip-llm
```

---

## Authentication & security notes

* The workflow uses `permissions: contents: read` and `pull-requests: read`
  (least privilege).
* `GITHUB_TOKEN` is passed only via the environment variable `GITHUB_TOKEN`,
  never on the command line (it would appear in logs).
* The `pull_request` event is used instead of `pull_request_target`, so fork
  PRs cannot access repository secrets.
* GitHub Models authenticates using the workflow's built-in `GITHUB_TOKEN`.
  No additional secrets are needed.

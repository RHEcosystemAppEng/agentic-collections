---
name: federation-review
description: |
  Review a Federation Request issue and validate the external pack for inclusion in the catalog.

  Use when:
  - "Review federation request"
  - "Validate external pack"
  - User mentions "federation", "federate", or "external pack"

  NOT for direct contributions (use /agentic-contribution-skill instead).
model: inherit
color: yellow
license: Apache-2.0
metadata:
  author: Red Hat Ecosystem Engineering
  version: 1.0.0
  category: internal-tooling
---

# Federation Review

Evaluate a Federation Request issue and validate the external agentic pack for inclusion in the Red Hat Agentic Collections catalog.

## Prerequisites

- Access to the agentic-collections repository
- The federation request issue number or URL
- `uv` installed for running validation scripts
- Optional: `gitleaks` installed for credential scanning

## When to Use This Skill

Use this when a Federation Request issue has been opened and you need to evaluate whether the external pack meets quality standards for inclusion in the catalog.

## Workflow

### Phase 1: Read the Federation Request

1. **Action:** Ask the user for the Federation Request issue number or URL
2. **Action:** Read the issue using `gh issue view <number>`
3. **Extract** from the issue:
   - Repository URL
   - Ref (SHA or tag)
   - Pack name
   - License
   - AI agent compatibility
   - Skills subset (if specified, empty means full pack)
   - Owner/contact info
4. **Output to user:** Summary of the request with all extracted fields

### Phase 2: Run Automated Validation

1. **Action:** Run the validation script:

```bash
# Full pack validation
uv run python scripts/validate_federation.py <repo-url> <ref>

# If the pack is in a subdirectory
uv run python scripts/validate_federation.py <repo-url> <ref> --pack-path <path>

# If only specific skills were requested
uv run python scripts/validate_federation.py <repo-url> <ref> --skills <skill1> <skill2>
```

2. **Output to user:** The full validation report with pass/fail for each check:
   - Clone and access
   - Lola pack structure
   - Tier 1 (agentskills.io spec)
   - Tier 2 (design principles)
   - MCP version pinning
   - Credential scan (gitleaks)

### Phase 3: Manual Review

These checks require human judgment. Present each to the user for confirmation:

1. **License compatibility:** Is the declared license compatible with Apache 2.0?
   - Compatible: Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause
   - Incompatible: GPL, AGPL, SSPL, proprietary
   - Ask user to confirm

2. **AI agent compatibility:** Do the declared agents match what the pack actually supports?
   - Claude Code: CLAUDE.md with intent routing exists?
   - Cursor: cursor-compatible config exists?
   - ChatGPT: chatgpt-compatible config exists?

3. **Pack quality:** Based on the README and CLAUDE.md:
   - Is the pack description clear and accurate?
   - Is the target persona well-defined?
   - Are prerequisites documented?

4. **Output to user:** Summary of manual review findings

### Phase 4: Decision

Present the combined results and ask the user for a decision:

| Decision | Action |
|----------|--------|
| **Approve** | Comment on the issue confirming approval. Create a PR to add the pack to `marketplace/rh-agentic-collection.yml` under `federated_modules`. Add label `federation` to the PR. |
| **Request changes** | Comment on the issue listing specific fixes needed. Add label `federation/changes-requested` to the issue. |
| **Reject** | Comment on the issue with explanation. Add label `federation/rejected` to the issue. Close the issue. |

### Phase 5: Registration (only if approved)

If the user approves, create the registration PR:

1. **Action:** Add the federated module entry to `marketplace/rh-agentic-collection.yml`:

```yaml
federated_modules:
  - name: "<pack-name>"
    description: "<from issue>"
    version: "<from repo>"
    license: "<from issue>"
    repository: "<repo-url>"
    ref: "<ref>"
    pack_path: "."
    tags: []
```

2. **Action:** Create a branch, commit, and push
3. **Action:** Create a PR with label `federation` linking to the original issue
4. **Output to user:** PR URL

## Dependencies

### Required MCP Servers

None — this skill uses CLI tools (`gh`, `git`, `uv`) and repository scripts only.

### Required MCP Tools

None — no MCP tools are invoked.

### Related Skills

- `/agentic-contribution-skill` — for direct contributions (create or import skills into this repo)

### Reference Documentation

**Internal:**
- [Federation Review Guide](../../../docs/FEDERATION_REVIEW_GUIDE.md) — full evaluation criteria
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) — contribution paths overview
- [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md) — Tier 2 design principles

**Scripts:**
- `scripts/validate_federation.py` — automated validation checks

## Human-in-the-Loop

This skill requires human confirmation at two points:
1. **Manual review** (Phase 3): License, AI agent compatibility, and quality are judgment calls
2. **Decision** (Phase 4): The approve/reject decision is always made by the maintainer

## Example Usage

```
User: /federation-review
Skill: What is the Federation Request issue number?
User: 42
Skill: Reading issue #42...
       Repository: https://github.com/partner/network-pack
       Ref: v2.1.0
       License: Apache-2.0
       Skills: entire pack (no subset specified)
       Running validation...
       [shows validation report]
       Manual review needed:
       - License Apache-2.0: compatible? [Y/n]
       - Claude Code support declared, CLAUDE.md found: confirmed
       Decision: Approve, Request changes, or Reject?
User: Approve
Skill: Creating registration PR...
       PR #87 created: https://github.com/RHEcosystemAppEng/agentic-collections/pull/87
```

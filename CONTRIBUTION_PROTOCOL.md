# Contribution Protocol

> **Draft** — This document defines the end-to-end protocol for contributing to Red Hat Agentic Collections. Covers both direct contributions and federation of external repositories. Subject to change as the process matures.

## Two Contribution Paths

| | Direct Contribution | Federation |
|---|---|---|
| **Your code lives in** | This repository | Your repository |
| **Compliance level** | Strict (Tier 1 + Tier 2 mandatory) | Tier 1 mandatory, Tier 2 recommended |
| **Entry point** | `/agentic-contribution-skill` in Claude Code | PR adding module to marketplace YAML |
| **Review process** | PR with automated CI + maintainer review | PR with `federation` label → automated CI + maintainer review |
| **PR auto-assigned to** | Pack owner via CODEOWNERS | Maintainers |
| **You control** | Nothing after merge (maintainers own it) | Your repo, your pace, your releases |
| **Catalog appearance** | Immediate after merge | After registration PR merges + next build |

Choose **direct contribution** when you want your skill to be part of the official collection with full maintainer support. Choose **federation** when you want to keep ownership of your code and release independently.

---

## Path 1: Direct Contribution

For adding skills or packs directly to this repository.

### Process

```
Fork & clone → /agentic-contribution-skill → PR → CI validation → CODEOWNERS review → Merge
```

### Step 1: Setup

1. Fork the repository on GitHub
2. Clone your fork locally
3. Open the project in Claude Code

### Step 2: Create or Import

Run `/agentic-contribution-skill` and choose a mode:

- **Create**: Answer discovery questions → skill is generated, validated, and placed in the right pack
- **Import**: Point to an existing SKILL.md → the skill is analyzed, adapted to repo standards, and placed in the right pack

The skill handles:
- Pack selection based on content analysis
- Structure and section generation following [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md)
- CLAUDE.md intent routing update
- Tier 1 + Tier 2 validation
- Git workflow (branch, commit, push)

### Step 3: Submit PR

The skill can create the PR for you, or you can do it manually. The PR template includes:
- Contribution method (skill or manual)
- Pack-persona alignment justification
- Compliance checklist

### Step 4: CI Validation

Automated checks run on every PR:

| Check | What it validates | Blocks merge? |
|-------|-------------------|---------------|
| `compliance-check` | Pack structure + collection compliance | Yes |
| `skill-spec-report` | Tier 1: agentskills.io spec (frontmatter, naming, line limits) | Yes (on errors) |
| `/skill-code-review` | AI review against CLAUDE.md + design principles | No (maintainer-triggered) |
| `/skill-security-scan` | Security scan (injection, exfiltration, supply chain) | No (maintainer-triggered) |

### Step 5: Review & Merge

1. GitHub auto-assigns the pack owner as reviewer (via [CODEOWNERS](CODEOWNERS))
2. Pack owner reviews the PR
3. Feedback addressed if needed
4. Approval and merge
5. Skill available in the catalog after next build

### Validation Commands

The skill runs these automatically, but you can run them manually:

```bash
# Tier 1: agentskills.io spec
./scripts/run-skill-linter.sh <pack>/skills/<skill-name>/

# Tier 2: design principles
make validate-skill-design-changed

# Full repo validation
make validate
```

### Pre-commit Hooks

If you have pre-commit installed, these hooks run locally before each commit:

| Hook | What it validates |
|------|-------------------|
| `gitleaks` | No secrets in committed files |
| `make-validate` | Pack structure + collection compliance |
| `validate-skill-design-changed` | Tier 2: design principles |
| `skill-spec-linter` | Tier 1: agentskills.io spec |

### Requirements

- All skills must pass Tier 1 + Tier 2 validation
- Skills must fit a pack's persona (the skill suggests the right pack)
- No hardcoded credentials (`${ENV_VAR}` format only)
- Human-in-the-loop confirmation for destructive operations
- CLAUDE.md intent routing must be updated

---

## Path 2: Federation

For referencing skills from external repositories in the Agentic Collections catalog.

### Process

```
Contributor opens PR → Federation CI validates → Maintainer reviews (+ /federation-review) → Merge
```

### Step 1: Open a Federation PR

Open a PR that adds a new module entry to `marketplace/rh-agentic-collection.yml` with your external repository URL. Add the `federation` label to the PR. Fill in the "Federation request" section of the PR template.

### Step 2: Automated CI

The Federation Validation workflow runs automatically on PRs with the `federation` label. It validates only new or changed federated modules against: Lola module schema, Tier 1, Tier 2, MCP pinning, and credential scan.

### Step 3: Maintainer Review

Maintainers review the PR and may use `/federation-review` in Claude Code to check license compatibility and verify the module loads in Lola.

### Step 4: Ongoing Maintenance

- **Version updates**: Open a PR updating the SHA/tag in marketplace YAML
- **Re-validation**: Federated skills are validated on each catalog build
- **Removal**: If the external repo becomes unavailable or skills stop passing validation, the federation entry may be removed after notification

### Requirements

**Mandatory:**
- Skills follow SKILL.md format with valid YAML frontmatter (`name`, `description`, `license`)
- Skills pass Tier 1 validation (agentskills.io spec)
- Repository is public and accessible
- Stable ref provided (commit SHA or release tag) or default branch
- Compatible license (Apache-2.0 recommended)

**Recommended:**
- Skills pass Tier 2 validation (design principles)
- Repository includes `mcps.json` if skills depend on MCP servers
- Skills include Common Issues and Example Usage sections
- Repository has its own CI for skill validation

### Responsibilities

**Federated repo owner:**
- Maintain skill quality and validation compliance
- Provide stable refs (don't force-push tagged commits)
- Update skills when notified of standard changes

**Agentic Collections maintainers:**
- Validate federated skills on registration and catalog builds
- Notify owners of validation failures
- Remove stale entries after reasonable notice

### What Federation Does NOT Include

- Federated skills are not modified by this repository
- Federation does not grant write access to this repository
- Federation does not imply endorsement — it means skills meet minimum quality standards

---

## Review Assignment

PR reviews are auto-assigned via [CODEOWNERS](CODEOWNERS):

| Files touched | Reviewer |
|---|---|
| `rh-sre/` | Pack owner (see CODEOWNERS) |
| `rh-virt/` | Pack owner (see CODEOWNERS) |
| `ocp-admin/` | Pack owner (see CODEOWNERS) |
| *(other packs)* | Pack owner (see CODEOWNERS) |
| `.github/`, `scripts/`, `marketplace/` | Maintainers |
| Federation PRs (`marketplace/` only) | Maintainers |

To make CODEOWNERS review mandatory, enable "Require review from Code Owners" in branch protection settings for the `main` branch.

---

## Pack-Persona Reference

Skills must fit into an existing pack or justify a new one:

| Pack | Persona | Scope |
|------|---------|-------|
| `rh-sre` | Site Reliability Engineers | CVE, compliance, RHEL automation |
| `rh-developer` | Application Developers | Deployment, builds, Helm |
| `rh-virt` | Virtualization Admins | VM lifecycle, snapshots, migrations |
| `ocp-admin` | OpenShift Administrators | Cluster management, monitoring |
| `rh-ai-engineer` | AI/ML Engineers | Model serving, inference |
| `rh-automation` | Automation Leads | Ansible AAP governance |
| `rh-basic` | General Red Hat Users | Diagnostics, lifecycle |
| `rh-support-engineer` | Support Engineers | Troubleshooting |

For direct contributions, `/agentic-contribution-skill` suggests the right pack automatically. For federation, explain pack fit in the issue.

---

## Questions?

- [GitHub Issues](https://github.com/RHEcosystemAppEng/agentic-plugins/issues)

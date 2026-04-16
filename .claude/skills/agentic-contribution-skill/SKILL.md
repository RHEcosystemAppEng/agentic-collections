---
name: agentic-contribution-skill
description: |
  Interactive skill and agentic pack creation with automated validation and marketplace compliance.

  Use when:
  - "Create a new skill"
  - "Create a new agentic pack"
  - "Add skill to <pack>"
  - "Build skill for <rh-product>"
  - User mentions "skill builder", "contribute", "new skill", or "new pack"

  Guides through discovery, definition, generation, and validation. Enforces SKILL_DESIGN_PRINCIPLES.md and agentskills.io spec.
model: inherit
color: green
metadata:
  author: "Red Hat Ecosystem Engineering"
  version: "1.0.0"
---

# /agentic-contribution-skill Skill

Interactive AI assistant for creating production-ready skills and agentic packs for **Red Hat products and platforms** with automated quality validation.

All skills created follow **Red Hat product guidelines, official documentation standards** (docs.redhat.com, access.redhat.com), and **best practices** for Red Hat Enterprise Linux, OpenShift Container Platform, Ansible Automation Platform, Red Hat Lightspeed, and other Red Hat ecosystem products.

**Creates**: Complete skill structure with YAML frontmatter, all mandatory sections, pack integration, and new agentic packs (Lola-compatible)
**Validates**: Tier 1 (agentskills.io) + Tier 2 (repository design principles)
**Applies**: Red Hat documentation compliance (uses official Red Hat documentation to adapt skill content to manufacturer guidelines - not automated validation)
**Marketplace**: Registers packs in `marketplace/rh-agentic-collection.yml` for Lola package manager installation

## Prerequisites

**Required Tools**:
- `git` - Version control
- `uv` - Python environment manager
- `bash` - Shell for validation scripts

**Verification**:
```bash
test -d .git && echo "✓ Git repo" || echo "✗ Not a git repo"
which uv >/dev/null && echo "✓ uv installed" || echo "✗ Install uv"
test -f SKILL_DESIGN_PRINCIPLES.md && echo "✓ Valid repo" || echo "✗ Wrong directory"
```

**Human Notification Protocol**:

If prerequisites fail:
```
❌ Cannot execute: <issue>
📋 Setup: <specific_steps>
🔗 Doc: CONTRIBUTING.md
```

**Security**: Never display git credentials or secrets.

## When to Use This Skill

**Use when**:
- Creating new skill for any pack
- Creating new agentic pack collection
- Developing or editing skills for this agentic collection
- User explicitly invokes `/agentic-contribution-skill`

**Do NOT use when**:
- Asking about standards (direct to SKILL_DESIGN_PRINCIPLES.md)
- General contributing questions (direct to CONTRIBUTING.md)

## Workflow

### Phase 1: Discovery (5 questions max)

Ask concisely, validate before proceeding. Make additional questions if needed to gather complete context.

1. **Purpose & Red Hat Product**: "What does the skill do? (1 sentence) For which Red Hat product(s) is this skill targeted?"
2. **Persona**: "What role uses it?" (detect existing pack or suggest new)
3. **Pack**: "Use <existing-pack>? (yes/no/create-new)"
4. **MCP Tools**: "What MCP tools does it need?" (verify in pack's mcps.json)
5. **Operation Type**: "Read-only, additive, or destructive?" (determines color)

**Validation**:
- Purpose: specific, under 100 chars
- Red Hat product: identified (OpenShift, RHEL, Ansible, etc.)
- Persona: matches known or justifies new pack
- MCP tools: exist or explain what to add
- Operation type → Color mapping: cyan/green/blue/yellow/red

### Phase 2: Definition (6 questions max)

1. **Name**: Ask "Skill name? (kebab-case, unique)" → Validate if name is representative of purpose and Red Hat product. If NOT representative, propose 2-3 better alternatives and ask user to choose → Check: `test -d <pack>/skills/<name>/` for uniqueness
2. **Use Cases**: "3-5 user phrases for 'Use when'" (concrete, not generic)
3. **Anti-Patterns**: "NOT for? (with alternative)"
4. **Workflow**: "Steps with MCP tools?" (e.g., "1. Validate VM - resources_get")
5. **Common Issues**: "3+ issues: problem: cause: solution"
6. **Prerequisites**: "Special requirements? (env vars, permissions)"

**Token Check**: Estimate description tokens (~use_cases + anti_patterns). Warn if > 400 words (~520 tokens).

### Phase 3: Pre-Generation Summary

Show complete spec:

```markdown
## Review Before Generation

**Pack**: <pack> | **Skill**: <name> | **Color**: <color>

**Purpose**: <purpose>
**Red Hat Product**: <rh-product>

**Use When**: <3-5 examples>
**NOT for**: <anti-pattern>

**Workflow**: <N> steps
**Common Issues**: <N> documented
**MCP Tools**: <tool_count> tools
**Human-in-the-Loop**: <Yes/No>

Proceed? (yes/no)
```

### Phase 4: Generation

**Create structure**:
```bash
mkdir -p <pack>/skills/<skill-name>/
```

**Generate files**:
1. **SKILL.md**: YAML frontmatter + 10 mandatory sections (follow SKILL_DESIGN_PRINCIPLES.md template)
2. **Update <pack>/CLAUDE.md**: Add intent routing entry
3. **Create <pack>/mcps.json**: If new MCP server needed (use `${ENV_VAR}` format)
4. **Update marketplace/rh-agentic-collection.yml**: If new pack (register pack for Lola installation)
5. **Create pack structure**: If new pack (README.md, CLAUDE.md, skills/ directory)
6. **Optional - plugin.json**: Only if publishing via Claude Code plugin mechanism (`.claude-plugin/plugin.json`)

**Mandatory SKILL.md sections** (in order):
1. Frontmatter (name, description, model, color)
2. `# /<skill-name> Skill` + overview
3. `## Prerequisites` (verification + Human Notification Protocol)
4. `## When to Use This Skill`
5. `## Workflow` (with precise parameters)
6. `## Common Issues` (min 3)
7. `## Dependencies` (MCP servers, tools, related skills)
8. `## Critical: Human-in-the-Loop Requirements` (if applicable)
9. `## Security Considerations` (if applicable)
10. `## Example Usage` (min 1)

### Phase 5: Validation

**Tier 1 - agentskills.io**:
```bash
./scripts/run-skill-linter.sh <pack>/skills/<skill-name>/
```

**Tier 2 - Design Principles**:
```bash
make validate-skill-design-changed
```

**Report clearly**:
- ✅ PASSED → Proceed
- ⚠️ WARNINGS → Ask user to continue
- ❌ ERRORS → Block, show fixes

**Document Consultation** (REQUIRED):
Read [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md) before validation.
Output: "I consulted SKILL_DESIGN_PRINCIPLES.md for validation criteria."

### Phase 6: Post-Validation Summary

```markdown
## ✅ Skill Created

**Files**:
✅ <pack>/skills/<name>/SKILL.md
✅ <pack>/CLAUDE.md (intent routing updated)
[If new pack]:
✅ <pack>/README.md
✅ <pack>/CLAUDE.md
✅ <pack>/mcps.json (if MCP servers needed)
✅ marketplace/rh-agentic-collection.yml (pack registered)

**Validation**:
✅ Tier 1: agentskills.io compliant
✅ Tier 2: Design principles satisfied

**Quality**:
- Sections: <N>
- Tokens: <N>/500
- Workflow steps: <N>
- Common issues: <N>

**Lola Installation**:
After merge: `lola install -f <pack-name>`

**Opinion**: <Your assessment - strengths, fit, readiness>

Ready to commit? (yes/no)
```

### Phase 7: Git Workflow (User Confirmation Required)

**Each step requires confirmation**:

1. **Branch**: "Create `feat/<skill-name>`? (yes/no)"
2. **Stage**: Show files, ask confirmation
3. **Commit**: Show message, ask confirmation
   ```
   feat: add <skill-name> skill to <pack>

   <skill-purpose>

   Tier 1+2 validated

   ```
4. **Push**: "Push changes? (yes/no)"
5. **PR**: Use `gh` and/or `git` if available, else provide manual instructions

### Phase 8: Final Summary

```markdown
## 🎉 Complete!

**Created**: <pack>/skills/<name>/SKILL.md
**Quality**: Production-ready
**PR**: <url_or_manual_instructions>

**CI checks will run automatically**

Thank you for contributing! 🚀
```

## Common Issues

### Issue 1: "Description exceeds 500 tokens"

**Fix**: Shorten frontmatter - move details to body sections.

### Issue 2: "Skill name exists"

**Fix**: Choose more specific name. Check: `ls <pack>/skills/`

### Issue 3: "MCP server not configured"

**Fix**: Add to `<pack>/mcps.json` using `${ENV_VAR}` format.

### Issue 4: "Git push authentication failed"

**Fix**: Configure credentials:
```bash
# HTTPS
git config --global credential.helper store

# SSH
ssh-add ~/.ssh/id_ed25519
```

### Issue 5: "uv not found"

**Fix**: Install:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Issue 6: "New pack not installable via Lola"

**Cause**: Pack not registered in `marketplace/rh-agentic-collection.yml`

**Fix**: Add pack entry to marketplace file:
```yaml
- name: <pack-name>
  version: 0.1.0
  description: <pack-description>
  path: <pack-name>
```

## Dependencies

### Required MCP Servers

None - This skill operates on repository files and git operations only. No MCP servers required.

### Required MCP Tools

None - Uses Claude Code built-in tools (Read, Write, Edit, Bash, Skill) for file operations and validation.

### Related Skills

None - agentic-contribution-skill is self-contained and doesn't invoke other skills.

### Repository Files

- `SKILL_DESIGN_PRINCIPLES.md` - Design principles (DP1-11)
- `scripts/run-skill-linter.sh` - Tier 1 validation
- `scripts/validate_skill_design.py` - Tier 2 validation
- `Makefile` - Validation targets
- `marketplace/rh-agentic-collection.yml` - Lola marketplace registry

### System Requirements

See [Prerequisites](#prerequisites) section for required system tools (git, uv, bash).

### Reference Documentation

**Internal**:
- [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md) - Complete design principles
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) - Contribution workflow guide
- [rh-virt/SKILL_TEMPLATE.md](../../../rh-virt/SKILL_TEMPLATE.md) - Enhanced template example

**External**:
- [agentskills.io Specification](https://agentskills.io/specification) - Base skill standard
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format
- [Lola Package Manager](https://github.com/RedHatProductSecurity/lola) - AI skills package manager

## Critical: Human-in-the-Loop Requirements

**MUST confirm before**:

1. **File Generation**: Show pre-generation summary, wait for "yes"
2. **Git Branch**: Ask before creating branch
3. **Git Commit**: Show commit message, wait for approval
4. **Git Push**: Confirm before pushing to remote
5. **Quality Enforcement**: Block on validation errors, warn on warnings

**NEVER**:
- Create commits without confirmation
- Push without explicit approval
- Skip validation steps
- Proceed if Tier 1 or Tier 2 validation fails with errors

**Why**: User controls their repository. Quality standards ensure CI success.

## Security Considerations

- **Git Credentials**: Never display tokens, SSH keys, or passwords
- **Environment Variables**: Report presence only, never values
- **User Repository**: Only operate in user's workspace
- **File Overwrite**: Warn before overwriting, require confirmation
- **MCP Credentials**: Only `${ENV_VAR}` format, never hardcoded
- **Script Execution**: User's repo context only

## Example Usage

```
User: "Create skill for rh-virt to backup VMs"

Agentic-Contribution-Skill:
What does it do? For which Red Hat product(s) is this skill targeted?
> "Create VM backups using snapshots for OpenShift Virtualization"

What role uses it?
> "Virt admins"

✅ Detected pack: rh-virt. Use it? (yes/no)
> yes

MCP tools needed?
> "vm-snapshot-create from openshift-virtualization"

Operation type? (read-only/additive/destructive)
> "additive"

✅ Color: green

Skill name? (kebab-case)
> "vm-backup-create"

✅ Name is representative of purpose (VM backup using snapshots for OpenShift Virtualization)
✅ Unique in rh-virt

3-5 user phrases for 'Use when':
> - "Backup VM database-01"
> - "Create snapshot before upgrade"
> - "Save VM state for recovery"

NOT for?
> "NOT for restoring (use vm-snapshot-restore)"

Workflow steps with MCP tools:
> 1. Validate VM exists - resources_get
> 2. Check storage supports snapshots - storageclasses_list
> 3. Create snapshot - virtualmachinesnapshot_create
> 4. Monitor until ready - virtualmachinesnapshot_get

3+ common issues:
> "Snapshot fails: Storage doesn't support: Use snapshot-capable storage"
> "VM not found: Wrong namespace: Verify with oc project"
> "Stuck pending: CSI driver issue: Check openshift-storage pods"

## Review Before Generation
[shows complete summary]

Proceed? (yes/no)
> yes

✅ Generated: rh-virt/skills/vm-backup-create/SKILL.md
✅ Updated: rh-virt/CLAUDE.md (intent routing)

Running validation...
I consulted SKILL_DESIGN_PRINCIPLES.md for validation criteria.

✅ Tier 1: PASSED
✅ Tier 2: PASSED (8/8 design principles)

## ✅ Skill Created
Production-ready quality

Ready to commit? (yes/no)
> yes

[Git workflow with confirmations]

🎉 Complete! PR created at: github.com/...

Thank you for contributing!
```

---

### Example 2: Non-representative name triggers AI suggestions

```
Skill name? (kebab-case)
> "check-stuff"

⚠️ Not representative of purpose (monitor cluster health for OpenShift).

Suggestions:
1. cluster-health-monitor
2. ocp-health-check  
3. cluster-metrics-monitor

Choose (1-3) or provide your own:
> 1

✅ Using "cluster-health-monitor"
```

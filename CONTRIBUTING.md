# Contributing to Agentic Collections

Thank you for your interest in contributing to the Red Hat Agentic Collections marketplace! This guide will help you create high-quality skills that meet our standards and integrate seamlessly into the ecosystem.

## Quick Start

The **fastest and recommended way** to contribute is using the `/agentic-contribution-skill` tool:

```bash
# Run the interactive skill builder
/agentic-contribution-skill

# Follow the interactive prompts
# The tool will guide you through everything: discovery, definition, generation, validation, and git workflow
```

The agentic-contribution-skill ensures your contribution meets all quality standards automatically.

## What is agentic-contribution-skill?

`agentic-contribution-skill` is an interactive AI assistant available in this repository's `.claude/skills/` directory that:
- ✅ Guides you through skill creation with targeted questions
- ✅ Generates complete skill structure following best practices
- ✅ Validates against agentskills.io specification (Tier 1)
- ✅ Validates against repository design principles (Tier 2)
- ✅ Automates git workflow (branch, commit, PR)
- ✅ Ensures your skill passes CI checks before submission

**Why use it?** It eliminates guesswork, prevents common mistakes, and saves hours of manual work.

**How it works**: The skill uses a human-in-the-loop approach - you maintain full control. It will ask for confirmation before:
- Generating files
- Creating git branches
- Making commits
- Pushing to remote

## Prerequisites

### Required Tools

1. **Git** - Version control
   ```bash
   git --version  # Verify installation
   ```

2. **uv** - Python environment manager (for validation scripts)
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or on macOS
   brew install uv
   ```

3. **Claude Code** - Latest version
   - Desktop app: [claude.ai/code](https://claude.ai/code)
   - VS Code/JetBrains extension
   - CLI tool

### Repository Setup

1. **Fork the repository** to your GitHub account
   - Visit: https://github.com/RHEcosystemAppEng/agentic-collections
   - Click "Fork" button (top right)

2. **Clone your fork** locally
   ```bash
   git clone https://github.com/YOUR_USERNAME/agentic-collections
   cd agentic-collections
   ```

3. **Add upstream remote** (optional but recommended)
   ```bash
   git remote add upstream https://github.com/RHEcosystemAppEng/agentic-collections
   ```

4. **Open the repository in Claude Code**
   - The `/agentic-contribution-skill` will be automatically available
   - Claude Code loads skills from `.claude/skills/` directory on startup
   - Verify it's available by typing `/agentic-contribution-skill` in the prompt

### Knowledge Requirements

- **Basic understanding** of AI skills and agents
- **Familiarity** with YAML frontmatter syntax
- **Knowledge** of the technology/platform your skill targets
- **Understanding** of Git workflow (fork, branch, commit, PR)

## Contribution Workflow

### Using agentic-contribution-skill (Recommended)

The agentic-contribution-skill guides you through 5 phases:

#### Phase 1: Discovery
Answer questions about your skill:
- What does it do?
- Who uses it?
- Which pack should it belong to?
- What MCP tools does it need?

#### Phase 2: Definition
Provide detailed specifications:
- Skill name (unique, kebab-case)
- Use case examples (concrete user phrases)
- Workflow steps with MCP tools
- Common issues users might face

#### Phase 3: Generation
agentic-contribution-skill creates:
- Complete `SKILL.md` with all mandatory sections
- Updated `CLAUDE.md` intent routing
- MCP configuration (if needed)
- New pack structure (if creating new pack)

#### Phase 4: Validation
Automated quality checks:
- **Tier 1**: agentskills.io specification compliance
- **Tier 2**: Repository design principles (DP1-11)
- Detailed feedback on any issues

#### Phase 5: Git Workflow
With your confirmation at each step:
- Create branch (`feat/skill-name`)
- Stage files
- Create commit with co-authorship
- Push to your fork
- Guide PR creation

### Manual Contribution (Advanced)

If you prefer manual creation:

1. **Read the standards**
   - [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) - Complete requirements
   - [agentskills.io specification](https://agentskills.io/specification) - Base standard

2. **Create skill structure**
   ```bash
   mkdir -p <pack>/skills/<skill-name>/
   # Create SKILL.md following SKILL_DESIGN_PRINCIPLES.md template
   ```

3. **Update pack CLAUDE.md**
   - Add entry to intent routing table

4. **Validate locally**
   ```bash
   # Tier 1 validation (agentskills.io)
   ./scripts/run-skill-linter.sh <pack>/skills/<skill-name>/
   
   # Tier 2 validation (design principles)
   make validate-skill-design-changed
   
   # Both must pass before committing
   ```

5. **Create pull request**
   ```bash
   git checkout -b feat/<skill-name>
   git add <pack>/skills/<skill-name>/ <pack>/CLAUDE.md
   git commit -m "feat: add <skill-name> skill to <pack>"
   git push origin feat/<skill-name>
   # Create PR on GitHub from your fork to upstream
   ```

## Quality Standards

All skills must comply with **two tiers** of standards:

### Tier 1: agentskills.io Specification (Automated)

Base standard for skill structure and format:
- Valid YAML frontmatter with required fields
- Proper naming conventions (kebab-case)
- Section structure and ordering
- Parameter documentation

**Validation**: `./scripts/run-skill-linter.sh`

### Tier 2: Repository Design Principles (Automated)

Enhanced requirements specific to this repository:

| Principle | Requirement | Validated By |
|-----------|-------------|--------------|
| **DP1** | Document Consultation Transparency | Script checks for Read tool + declaration |
| **DP2** | Precise Parameter Specification | Validates parameter examples exist |
| **DP3** | Description Conciseness | Counts tokens, must be <500 |
| **DP4** | Dependencies Declaration | Checks Dependencies section presence |
| **DP5** | Human-in-the-Loop Requirements | Validates confirmation steps for critical ops |
| **DP6** | Mandatory Sections | Verifies all required sections present in order |
| **DP7** | MCP Server Verification | Checks for credential exposure |
| **DP11** | Pack-Level CLAUDE.md | Validates intent routing updated |

**Validation**: `make validate-skill-design-changed`

See [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) for complete details and rationale.

## What Makes a Good Skill?

### Clear Purpose
- **Do one thing well** - Single responsibility
- **Specific use case** - Not too broad
- **Real user need** - Solves actual problem

### Quality Documentation
- **Concrete examples** - Real user phrases, not generic descriptions
- **Precise parameters** - Exact formats with examples
- **Common issues** - At least 3 documented with solutions
- **Complete workflow** - All steps with error handling

### Production Ready
- **Error handling** - Covers failure scenarios
- **Security** - No credential exposure
- **Human-in-the-loop** - Confirmations for critical operations
- **Validated** - Passes Tier 1 + Tier 2 checks

## Pack Selection Guide

Choose the right pack for your skill:

| Pack | Persona | When to Use |
|------|---------|-------------|
| **rh-sre** | Site Reliability Engineers | CVE remediation, system compliance, RHEL automation |
| **rh-developer** | Application Developers | App deployment, S2I builds, Helm charts |
| **openshift-virtualization** | Virtualization Admins | VM lifecycle, snapshots, migrations |
| **ocp-admin** | OpenShift Administrators | Cluster management, health reports, monitoring |
| **rh-ai-engineer** | AI/ML Engineers | Model serving, vLLM, KServe, NVIDIA NIM |
| **rh-automation** | Automation Leads | Ansible AAP governance, safety checks |
| **rh-support-engineer** | Support Engineers | Technical support, troubleshooting |

**Creating a new pack?** Use agentic-contribution-skill - it will create the complete pack structure for you.

## Testing Your Skill Locally

Before submitting a PR, test your skill locally:

1. **Invoke the skill** in Claude Code:
   ```
   /your-skill-name
   ```

2. **Try different scenarios**:
   - Normal use case (happy path)
   - Edge cases
   - Error conditions

3. **Verify the output**:
   - Check that MCP tools are called correctly
   - Ensure error messages are helpful
   - Confirm human-in-the-loop prompts appear for critical operations

4. **Test with real data** (if applicable):
   - Use actual VMs, clusters, or systems (in a safe environment)
   - Don't test destructive operations on production systems

## Pull Request Process

### Before Submitting

- [ ] Skill created with agentic-contribution-skill or manually validated
- [ ] Tier 1 validation passed: `./scripts/run-skill-linter.sh`
- [ ] Tier 2 validation passed: `make validate-skill-design-changed`
- [ ] Tested skill locally by invoking it in Claude Code
- [ ] Reviewed generated skill for accuracy
- [ ] No credentials exposed in skill documentation

### PR Template

When creating your PR, include:

```markdown
## Description
[What does the skill do and why is it valuable?]

## Skill Details
- **Pack**: <pack-name>
- **Operation Type**: <read-only|additive|reversible|destructive>
- **MCP Servers**: <server-list>
- **Validation**: Tier 1 + Tier 2 passed

## Use Cases
- [List 3-5 concrete examples]

## Testing
- [x] Generated with agentic-contribution-skill / manually validated
- [x] Tier 1 validation passed
- [x] Tier 2 validation passed
- [ ] Manually tested skill invocation

## Checklist
- [x] Follows SKILL_DESIGN_PRINCIPLES.md
- [x] CLAUDE.md intent routing updated
- [x] No credentials exposed
- [x] Human-in-the-loop for critical operations
```

### CI Checks

Your PR will automatically run:
1. **Compliance check** - Validates marketplace structure
2. **Skill spec linter** - Tier 1 validation (agentskills.io)
3. **Design validator** - Tier 2 validation (design principles)

All checks must pass before merge.

### Review Process

1. **Automated validation** - CI checks run
2. **Maintainer review** - Quality and fit assessment
3. **Feedback** - Requested changes (if needed)
4. **Iteration** - Address feedback, re-validate
5. **Approval** - Maintainer approves
6. **Merge** - Skill added to marketplace

## Common Issues and Solutions

### Validation Failures

**Issue**: "Description exceeds 500 tokens"
- **Fix**: Shorten frontmatter description, move details to body sections
- **Tool**: `head -n 20 SKILL.md | wc -w` (rough estimate: ~1.3 words per token)

**Issue**: "Skill name already exists"
- **Fix**: Choose more specific name, check: `ls <pack>/skills/`

**Issue**: "MCP server not configured"
- **Fix**: Add to `<pack>/mcps.json` using `${ENV_VAR}` format for credentials

### Git Issues

**Issue**: "Push authentication failed"
- **Fix**: Configure git credentials or SSH key
- **HTTPS**: `git config --global credential.helper store`
- **SSH**: Add SSH key to GitHub settings

**Issue**: "Merge conflicts"
- **Fix**: Sync with upstream, resolve conflicts
  ```bash
  git fetch upstream
  git merge upstream/main
  # Resolve conflicts
  git commit
  ```

### Skill Quality

**Issue**: "Workflow steps too vague"
- **Fix**: Add precise parameter names and examples
- **Example**: Instead of "Create VM", use "Create VM with `name: <vm-name>`, `namespace: <namespace>`"

**Issue**: "Missing common issues"
- **Fix**: Document at least 3 real issues users might face with causes and solutions

## Getting Help

### Resources

- **Design Principles**: [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md)
- **agentskills.io Spec**: https://agentskills.io/specification
- **Documentation Site**: https://rhecosystemappeng.github.io/agentic-collections

### Support Channels

- **Issues**: [GitHub Issues](https://github.com/RHEcosystemAppEng/agentic-collections/issues)
- **Discussions**: [GitHub Discussions](https://github.com/RHEcosystemAppEng/agentic-collections/discussions)
- **PR Comments**: Ask questions directly in your pull request

### Reporting Bugs

Found a bug in agentic-contribution-skill or existing skills?

1. Check [existing issues](https://github.com/RHEcosystemAppEng/agentic-collections/issues)
2. Create new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (Claude Code version, OS)

## Advanced Topics

### Creating a New Pack

Use agentic-contribution-skill - it automates the process:
1. Detects when a new pack is needed
2. Creates complete pack structure:
   - `README.md`
   - `CLAUDE.md` with intent routing
   - `skills/` directory
   - `mcps.json` (if MCP servers needed)
   - Optional: `.claude-plugin/plugin.json` (if publishing via Claude Code plugin format)
3. Updates `marketplace/rh-agentic-collection.yml`

Manual creation is possible but not recommended - see [CLAUDE.md](CLAUDE.md) for structure.

### Adding MCP Servers

agentic-contribution-skill guides you through:
1. MCP server selection based on use case
2. `mcps.json` configuration with environment variables
3. Security validation (no hardcoded credentials)

Manual addition: Add to `<pack>/mcps.json` following existing patterns.

### Skill Templates

Reference templates:
- **General**: [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) - Standard template
- **rh-virt Enhanced**: [rh-virt/SKILL_TEMPLATE.md](rh-virt/SKILL_TEMPLATE.md) - With additional quality checks

agentic-contribution-skill uses these templates automatically.

## Code of Conduct

We are committed to providing a welcoming and inclusive experience for all contributors.

**Expected Behavior**:
- Be respectful and professional
- Accept constructive feedback gracefully
- Focus on what's best for the community
- Show empathy towards others

**Unacceptable Behavior**:
- Harassment or discriminatory language
- Personal attacks or trolling
- Spam or off-topic content

Report issues to: eco-engineering@redhat.com

## License

By contributing to this repository, you agree that your contributions will be licensed under the Apache License 2.0.

See [LICENSE](LICENSE) for details.

---

## Thank You!

Your contributions make this marketplace valuable for the entire Red Hat ecosystem. Whether you're fixing a typo or adding a complex skill, every contribution matters.

**Ready to contribute?** Start with `/agentic-contribution-skill` and let the tool guide you!

Questions? Open an [issue](https://github.com/RHEcosystemAppEng/agentic-collections/issues) or discussion.

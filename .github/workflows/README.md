# GitHub Actions Workflows

This directory contains CI/CD workflows for the agentic collections repository.

## Available Workflows

### 1. `validate-skills.yml` - Universal Skill Validation

**Purpose**: Validates all skills against SKILL_CHECKLIST.md requirements (agentskills.io specification + repository design principles).

**Triggers**:
- **Every pull request** (opened, synchronized, reopened, or marked ready for review)
- Pushes to `main` branch
- **Excludes**: Draft pull requests (validation runs only when PR is ready for review)

**What it validates**:

**Tier 1 - agentskills.io specification (MANDATORY):**
- ✅ Directory structure (skill-name/SKILL.md)
- ✅ Name format (1-64 chars, lowercase, no consecutive hyphens)
- ✅ Description length (1-1024 chars, under 500 tokens)
- ✅ YAML frontmatter completeness (name, description)

**Tier 2 - Repository design principles (MANDATORY):**
- ✅ Model field (must be: inherit, sonnet, or haiku)
- ✅ Color field (must be: cyan, green, blue, yellow, or red)
- ✅ SKILL.md header format (# /<skill-name> Skill or # [Skill Name])
- ✅ Required sections presence and order
- ✅ Prerequisites with verification steps
- ✅ When to Use This Skill with anti-patterns
- ✅ Workflow with MCP tools and parameters
- ✅ Document consultation transparency
- ✅ Dependencies declaration
- ✅ Human-in-the-Loop requirements
- ✅ Security (no credential exposure)
- ✅ Content quality (links, file size)

**How to run locally**:
```bash
# Validate all skills in all collections
./scripts/validate-skills.sh

# Validate specific collection
./scripts/validate-skills.sh rh-virt/

# Validate single skill
./scripts/validate-skills.sh rh-virt/skills/vm-create/

# Strict mode (exit on first error)
./scripts/validate-skills.sh --strict rh-virt/

# Verbose output
./scripts/validate-skills.sh --verbose
```

**Expected output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Universal Skill Validator
Validates skills against CLAUDE.md and agentskills.io specification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 9 skill(s) to validate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validating: vm-create
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Skill 'vm-create' passed validation

...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validation Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Skills:    9
Passed:          9
Failed:          0
Total Errors:    0

✓ All skills passed validation
```

**Validation Levels**:

The script validates all requirements from SKILL_CHECKLIST.md:
- **Level 1:** agentskills.io specification (Sections 0-9) - MANDATORY
- **Level 2:** Repository design principles (Sections 10-37) - MANDATORY

All skills must pass both levels to be committed.

**When validation fails**:

The workflow will fail and provide:
1. Specific errors for each skill
2. Common issues and fixes
3. Local validation command
4. Reference to SKILL_CHECKLIST.md for detailed requirements

**Common validation errors**:
- Missing or invalid `model` field (must be: inherit, sonnet, or haiku)
- Missing or invalid `color` field (must be: cyan, green, blue, yellow, or red)
- Invalid SKILL.md header format (must be: # /<skill-name> Skill)
- Missing required sections (Prerequisites, When to Use, Workflow, Dependencies)
- Missing "NOT for" anti-patterns in description

**Related files**:
- `scripts/validate-skills.sh` - Main validation script
- `SKILL_CHECKLIST.md` - Universal skill requirements checklist (single source of truth)
- `CLAUDE.md` - Repository architecture and patterns

## Adding New Workflows

When adding new workflows:

1. **Name the file descriptively**: `action-description.yml`
2. **Add documentation** in this README
3. **Define clear triggers** (PR, push, manual, schedule)
4. **Use semantic job names** that describe what they validate/test
5. **Provide clear error messages** when workflows fail
6. **Keep workflows focused** - one responsibility per workflow

## Best Practices

### Workflow Design
- ✅ Use specific path filters to avoid unnecessary runs
- ✅ Checkout with full history (`fetch-depth: 0`) when needed for diffs
- ✅ Use established GitHub Actions from trusted sources
- ✅ Provide summary outputs for quick review

### Error Reporting
- ✅ Clear failure messages with actionable steps
- ✅ Reference documentation for resolution
- ✅ Group related errors together

### Performance
- ✅ Run only on relevant file changes
- ✅ Use caching when applicable
- ✅ Parallelize independent validation steps

## Troubleshooting

### Workflow not triggering

Check:
1. File paths match the `paths:` filter
2. Branch protection rules aren't blocking the workflow
3. GitHub Actions are enabled in repository settings

### Validation script fails locally but passes in CI (or vice versa)

This can happen due to:
1. Different file line endings (CRLF vs LF)
2. Different bash versions
3. Missing script permissions (`chmod +x`)

**Fix**:
```bash
# Ensure script is executable
chmod +x scripts/validate-skills.sh

# Check line endings
file scripts/validate-skills.sh

# Convert to LF if needed
dos2unix scripts/validate-skills.sh
```

### False positives in validation

If the validator reports errors for valid skills:
1. Review the validation logic in `scripts/validate-skills.sh`
2. Check if your skill follows CLAUDE.md design principles exactly
3. Review SKILL_CHECKLIST.md for specific formatting requirements
4. Open an issue if the validator has a bug

## Maintenance

This README should be updated when:
- New workflows are added
- Validation logic changes
- New validation levels are introduced
- Troubleshooting patterns emerge

**Last Updated**: 2026-02-26
**Workflows Count**: 1 (validate-skills.yml)

# GitHub Actions Workflows

This directory contains CI/CD workflows for the agentic collections repository.

## Available Workflows

### 1. `skill-spec-report.yml` - Skill Specification Linter Report

**Purpose**: Validates skills against agentskills.io specification using the skill-linter and generates a comprehensive compliance report.

**Triggers**:
- **Pull requests** → Validates ALL skills in affected packs (ensures pack consistency)
- **Pushes to main** → Validates ALL skills across all packs (ensures repo health)
- **Manual dispatch** → Choose between all skills or pack-wide validation
- **Excludes**: Draft pull requests

**Validation Strategy** (Pack-Wide Validation):
- ⚡ **PRs**: Validates ALL skills in affected packs (pack-wide consistency)
  - Example: Change `rh-virt/skills/vm-create/SKILL.md` → validates ALL `rh-virt/skills/*`
- 🔍 **Push to main**: Full validation of all 37 skills across all packs
- 🎛️ **Manual**: Choose validation scope via workflow dispatch

**What it validates**:

**agentskills.io Specification Compliance:**
- ✅ Directory structure (skill-name/SKILL.md)
- ✅ YAML frontmatter delimiters and completeness
- ✅ Name field (1-64 chars, lowercase, pattern matching, directory alignment)
- ✅ Description field (1-1024 chars, routing keywords, no marketing copy)
- ✅ Optional fields (compatibility, allowed-tools format)
- ✅ Line count (max 500 lines in SKILL.md)
- ✅ Subdirectory validation (only scripts/, references/, assets/)
- ✅ Content quality (no ASCII art, no persona statements)

**Behavior**:
- **Errors detected** → ❌ Workflow fails, blocks PR merge
- **Warnings only** → ⚠️ Workflow passes, allows merge with warnings
- **All pass** → ✅ Workflow passes

**Report Format**:
- Real-time progress (✅/⚠️/❌) for each skill
- **Detailed error output** shown ONLY for failed skills
- **Summary table** at the end with counts (Total/Passed/Warnings/Failed)

**How to run locally**:
```bash
# Validate ALL skills
./scripts/run-skill-linter.sh

# Validate only changed skills (detects git changes)
CHANGED=$(./scripts/detect-changed-skills.sh)
if [ -n "$CHANGED" ]; then
  ./scripts/run-skill-linter.sh $CHANGED
fi

# Validate specific skills
./scripts/run-skill-linter.sh rh-virt/skills/vm-create rh-virt/skills/vm-delete

# Validate single skill (detailed output)
./.claude/skills/skill-linter/scripts/validate-skill.sh rh-virt/skills/vm-create/
```

**Manual workflow dispatch**:
1. Go to Actions → Skill Specification Report
2. Click "Run workflow"
3. Choose:
   - **Validate all skills: true** → Full scan (37 skills)
   - **Validate all skills: false** → Changed skills only

**Expected output**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            Skill Specification Linter Report
         agentskills.io Specification Compliance
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 37 skill(s) to validate

✅ rh-sre/cve-impact
✅ rh-sre/fleet-inventory
⚠️  rh-developer/helm-deploy - PASSED WITH WARNINGS
❌ rh-virt/vm-create - FAILED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DETAILED ERROR REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAILED: rh-virt/vm-create
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[FAIL] Missing frontmatter opening delimiter (---)
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VALIDATION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metric                                   Count
────────────────────────────────────────────────────────────────
Total Skills:                            37
✅ Passed:                               30
⚠️  Passed with Warnings:                6
❌ Failed:                               1

❌ VALIDATION FAILED - ERRORS DETECTED
Skills with errors must be fixed before merge
```

**When validation fails**:

The workflow will:
1. Show detailed error output for each failed skill
2. Display summary table with failure counts
3. Block PR merge (exit code 1)
4. Provide guidance on fixing errors locally

**When validation passes with warnings**:

The workflow will:
1. Show which skills have warnings
2. Display summary table
3. Allow PR merge (exit code 0)
4. Warn that warnings should be reviewed

**Common validation errors**:
- Missing frontmatter delimiters (---)
- Name doesn't match directory name
- Description exceeds 1024 characters or lacks routing keywords
- Line count exceeds 500 lines
- Invalid `allowed-tools` format (must be space-delimited)
- ASCII art or persona statements in content
- Marketing buzzwords in description

**Related files**:
- `scripts/run-skill-linter.sh` - Comprehensive linter reporter script (accepts optional skill dirs)
- `scripts/detect-changed-skills.sh` - Detects changed skills in PRs and commits
- `.claude/skills/skill-linter/scripts/validate-skill.sh` - Core validation script
- `.claude/skills/skill-linter/SKILL.md` - Linter documentation

**Performance**:
- **PR validation (single pack)**: ~10-40 seconds (e.g., all 9 rh-virt skills)
- **PR validation (multiple packs)**: ~20-60 seconds (varies by pack count)
- **Full validation (all packs)**: ~60-90 seconds (all 37 skills)
- **Pack-wide**: 30-60% faster than full validation (depends on pack size)

**Scope**: This workflow validates **ONLY** agentskills.io specification compliance. Repository-specific design principles (model, color, sections, etc.) are validated by other workflows.

### 2. `compliance-check.yml` - Agentic Collections Structure Validation

**Purpose**: Validates the entire agentic collections repository structure and runs skill design compliance checks on changed skills only.

**Triggers**:
- **Every pull request**
- Pushes to `main` branch

**What it validates**:

**Repository structure validation (`make validate`):**
- ✅ Collection directory structure and naming conventions
- ✅ Required files presence (README.md, mcps.json, etc.)
- ✅ Plugin metadata completeness
- ✅ MCP server configurations

**Changed skills validation (`./scripts/ci-validate-changed-skills.sh`):**
- ✅ Detects which skills were modified in the PR/push
- ✅ Validates only changed skills against SKILL_DESIGN_PRINCIPLES.md
- ✅ Runs design compliance checks specific to modified skills

**How to run locally**:
```bash
# Validate entire repository structure
make validate

# Validate changed skills (simulates CI environment)
./scripts/ci-validate-changed-skills.sh

# Or validate all skills
make validate-skill-design
```

**Expected output**:
```
Validating repository structure...
✓ Collection structure valid
✓ Plugin metadata valid
✓ MCP configurations valid

Validating changed skills...
Found 2 changed skill(s): vm-create, vm-delete
✓ vm-create passed design compliance
✓ vm-delete passed design compliance
```

**When validation fails**:

The workflow will fail and provide:
1. Specific structural errors in the repository
2. Design compliance violations for changed skills
3. Reference to SKILL_DESIGN_PRINCIPLES.md

**Common validation errors**:
- Missing required collection files (README.md, mcps.json)
- Invalid MCP server configuration syntax
- Skills not following design principles (see SKILL_DESIGN_PRINCIPLES.md)
- Missing documentation in collections

**Related files**:
- `Makefile` - Build and validation targets
- `scripts/ci-validate-changed-skills.sh` - Changed skills detector and validator
- `scripts/validate_skill_design.py` - Design compliance validation script
- `SKILL_DESIGN_PRINCIPLES.md` - Design principles checklist

### 3. `deploy-pages.yml` - GitHub Pages Documentation Deployment

**Purpose**: Generates and deploys HTML documentation for all agentic collections to GitHub Pages.

**Triggers**:
- **Manual dispatch** (workflow_dispatch)
- Pushes to `main` branch affecting documentation paths:
  - `rh-sre/**`
  - `rh-developer/**`
  - `ocp-admin/**`
  - `rh-virt/**`
  - `scripts/**`
  - `docs/**`
  - `.github/workflows/deploy-pages.yml`

**What it does**:

**Documentation generation (`make generate`):**
- ✅ Generates HTML documentation from Markdown files
- ✅ Creates collection indexes and navigation
- ✅ Builds skill reference pages
- ✅ Generates searchable documentation site

**Deployment:**
- ✅ Configures GitHub Pages environment
- ✅ Uploads documentation artifacts
- ✅ Deploys to GitHub Pages with proper permissions

**How to run locally**:
```bash
# Generate documentation locally
make generate

# Preview generated docs
cd docs && python3 -m http.server 8000
# Open http://localhost:8000 in your browser
```

**Expected output**:
```
Generating documentation...
✓ Processing rh-sre collection
✓ Processing rh-developer collection
✓ Processing rh-virt collection
✓ Building site navigation
✓ Documentation generated in docs/

Deploying to GitHub Pages...
✓ Artifact uploaded
✓ Deployed successfully
```

**When deployment fails**:

The workflow will fail if:
1. Documentation generation fails (invalid Markdown, missing files)
2. GitHub Pages permissions not configured
3. Artifact upload fails
4. Deployment step fails

**Common deployment errors**:
- Missing Python dependencies (resolved by `make install`)
- Invalid frontmatter in Markdown files
- GitHub Pages not enabled in repository settings
- Insufficient workflow permissions

**Related files**:
- `Makefile` - Documentation generation targets
- `scripts/generate-docs.py` - Documentation generator (if exists)
- `docs/` - Generated documentation output directory

**Concurrency settings**:
- Only one deployment runs at a time (group: "pages")
- New deployments cancel in-progress ones

### 4. `security-scan.yml` - Skill Security Scan

**Purpose**: Scans skills for security vulnerabilities using [cisco-ai-skill-scanner](https://github.com/cisco-ai-defense/skill-scanner) with LLM-powered analysis. Detects prompt injection, data exfiltration, social engineering, and other AI agent security risks.

**Triggers**:
- **Pull requests** → Scans changed packs only (when `**/skills/**` or `**/mcps.json` change)
- **Manual dispatch** → Scan specific PR or all packs
- **Excludes**: Draft pull requests

**Cost optimization**:
- **Path filters**: Only triggers when skill files or MCP configs change
- **Concurrency**: Cancels in-progress scans when new commits are pushed
- **Prerequisite gate**: Waits for `compliance-check` and `skill-linter` to pass before running — if either fails, the scan is skipped to save LLM tokens

**What it checks**:
- YAML/manifest injection risks
- Command injection via untrusted inputs
- Supply chain risks (unpinned dependencies)
- Data exfiltration patterns
- Social engineering triggers
- Cross-skill overlap and coordinated behavior
- Missing metadata (license, provenance)

**Behavior**:
- **MEDIUM or higher findings** → ❌ Workflow fails, blocks PR merge
- **LOW/INFO only** → ✅ Workflow passes
- Posts scan summary as PR comment with collapsible report per pack
- Uploads detailed reports as workflow artifacts (30-day retention)

**How to run locally**:
```bash
# Install scanner
uv pip install --system 'cisco-ai-skill-scanner[google]'

# Set credentials
export SKILL_SCANNER_LLM_API_KEY=<your-api-key>
export SKILL_SCANNER_LLM_MODEL=gemini/gemini-2.5-pro  # or openai/gpt-5

# Scan a single pack
skill-scanner scan-all rh-virt/skills \
  --recursive --use-behavioral --use-llm \
  --check-overlap --enable-meta \
  --fail-on-severity medium \
  --format markdown --detailed \
  --output security-report.md
```

**Manual workflow dispatch**:
1. Go to Actions → Skill Security Scan
2. Click "Run workflow"
3. Provide:
   - **PR number** (required) — PR to post results to
   - **Scan all packs** — `true` for full scan, `false` for changed packs only

**Secrets required**:
- `SKILL_SCANNER_LLM_API_KEY` — API key for LLM provider
- `SKILL_SCANNER_LLM_MODEL` — Model identifier (e.g., `gemini/gemini-2.5-pro`)

**Performance**:
- ~10-15 minutes per pack (depends on number of skills and LLM response time)
- Uses `uv` instead of `pip` for faster dependency installation with caching

**Related files**:
- `scripts/detect-changed-packs.sh` - Detects packs with changed files in PRs
- Security reports uploaded as workflow artifacts

### 5. `gemini-code-review.yml` - Gemini Code Review

**Purpose**: Automated code review using Google Gemini, validating PRs against project rules (CLAUDE.md, SKILL_DESIGN_PRINCIPLES.md).

**Triggers**:
- **Pull requests** (opened, synchronize, reopened)
- **Manual dispatch** with PR number

**What it does**:
- Fetches PR diff and project rules
- Sends to Gemini for review
- Posts review as PR comment (updates existing comment on re-runs)

**Secrets required**:
- `GEMINI_API_KEY` — Google Gemini API key

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
2. Check if your skill follows SKILL_DESIGN_PRINCIPLES.md requirements exactly
3. Verify agentskills.io specification compliance
4. Open an issue if the validator has a bug

## Maintenance

This README should be updated when:
- New workflows are added
- Validation logic changes
- New validation levels are introduced
- Troubleshooting patterns emerge

**Last Updated**: 2026-05-05
**Workflows Count**: 5 (skill-spec-report.yml, compliance-check.yml, deploy-pages.yml, security-scan.yml, gemini-code-review.yml)

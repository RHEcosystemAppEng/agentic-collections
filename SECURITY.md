# Security Guidelines

This document provides security guidelines for the agentic-collections repository, focusing on credential management and preventing sensitive data from being committed.

## Table of Contents

- [Credential Management](#credential-management)
- [Gitleaks Protection](#gitleaks-protection)
- [Environment Setup](#environment-setup)
- [Incident Response](#incident-response)

---

## Credential Management

### Never Hardcode Secrets

**Rule**: Never commit API keys, passwords, tokens, or any sensitive credentials directly in code or configuration files.

**Why**: Hardcoded secrets in version control:
- Can be accessed by anyone with repository access
- Remain in git history even after deletion
- Can be exposed in public forks or clones
- Violate compliance requirements (PCI-DSS, SOC 2, etc.)

### Use Environment Variables

**Best Practice**: Store credentials in environment variables and reference them in code.

❌ **INCORRECT** (hardcoded):
```python
API_KEY = "sk-proj-abc123def456ghi789"
```

✅ **CORRECT** (environment variable):
```python
import os
API_KEY = os.environ.get("OPENAI_API_KEY")
```

❌ **INCORRECT** (hardcoded):
```javascript
const apiKey = "ghp_1234567890abcdefghij";
```

✅ **CORRECT** (environment variable):
```javascript
const apiKey = process.env.GITHUB_TOKEN;
```

### mcps.json Requirements

**MCP Configuration Rule** (per [CLAUDE.md line 125](CLAUDE.md#L125)):

> Never hardcode credentials. Always use `${ENV_VAR}` references.

❌ **INCORRECT** (hardcoded credentials):
```json
{
  "mcpServers": {
    "lightspeed-mcp": {
      "env": {
        "LIGHTSPEED_CLIENT_ID": "12345-abcde",
        "LIGHTSPEED_CLIENT_SECRET": "sk-proj-abc123..."
      }
    }
  }
}
```

✅ **CORRECT** (environment variable references):
```json
{
  "mcpServers": {
    "lightspeed-mcp": {
      "env": {
        "LIGHTSPEED_CLIENT_ID": "${LIGHTSPEED_CLIENT_ID}",
        "LIGHTSPEED_CLIENT_SECRET": "${LIGHTSPEED_CLIENT_SECRET}"
      }
    }
  }
}
```

---

## Gitleaks Protection

This repository uses [gitleaks](https://github.com/gitleaks/gitleaks) to automatically scan for secrets before commits.

### Installation

```bash
# Install gitleaks and pre-commit hook (one-time setup)
scripts/install-hooks.sh
```

This script:
1. Installs gitleaks (via Homebrew on macOS, binary download on Linux)
2. Sets up a pre-commit hook to scan staged changes
3. Uses `.gitleaks.toml` for project-specific rules

### What's Detected

Gitleaks scans for:

- **API Keys**: OpenAI (sk-*, sk-proj-*), GitHub (ghp_*, ghu_*, ghs_*), AWS (AKIA*), Google (AIza*)
- **Private Keys**: SSH, SSL/TLS (PEM format)
- **Database URLs**: Connection strings with embedded passwords
- **JWT Tokens**: eyJ... format tokens
- **Generic Secrets**: password, api_key, secret, token assignments
- **MCP Hardcoded Values**: `mcps.json` files without ${VAR} pattern

### Manual Scanning

```bash
# Scan entire repository history
gitleaks detect --source . --verbose

# Generate JSON report
gitleaks detect --source . --report-path gitleaks-report.json

# Scan specific branch
gitleaks detect --source . --log-opts="origin/main"

# Scan only staged changes (pre-commit does this automatically)
gitleaks protect --staged
```

### Configuration

The `.gitleaks.toml` file contains:
- **Default rules**: Gitleaks' built-in secret detection patterns
- **Custom rules**: MCP-specific validation, database URLs
- **Allowlist**: Patterns to exclude (environment variables, examples, test fixtures)
- **Stopwords**: Keywords that indicate false positives ("example", "sample", "test")

### When Gitleaks Blocks a Commit

```
=========================================
🚨 COMMIT BLOCKED - Secrets Detected
=========================================

Gitleaks found potential secrets in your staged changes.

To fix:
  1. Remove hardcoded secrets
  2. Use environment variables: ${ENV_VAR}
  3. Review .gitleaks.toml for allowed patterns

To bypass (DANGEROUS - only for test fixtures):
  git commit --no-verify
```

**To Fix**:
1. Remove the hardcoded secret from your code
2. Replace with environment variable reference
3. Add the actual secret to your local environment (see [Environment Setup](#environment-setup))
4. Verify fix: `git diff --cached`
5. Commit again

### Bypassing Gitleaks

**Warning**: Only use for test fixtures or documentation examples.

```bash
git commit --no-verify -m "Add test fixture"
```

### False Positives

If gitleaks incorrectly flags a pattern, you can:

1. **Add to allowlist** in `.gitleaks.toml`:
```toml
[allowlist]
regexes = [
    '''your-false-positive-pattern''',
]
```

2. **Use stopwords** in `.gitleaks.toml`:
```toml
stopwords = [
    "example",
    "your-specific-keyword",
]
```

3. **Inline comment** (not recommended):
```python
API_KEY = "sk-example-123"  # gitleaks:allow
```

---

## Environment Setup

### Local Development (.env files)

Use `.env` files for local development (already in `.gitignore`):

```bash
# .env (NOT committed)
OPENAI_API_KEY=sk-proj-...
GITHUB_TOKEN=ghp_...
AWS_ACCESS_KEY_ID=AKIA...
LIGHTSPEED_CLIENT_ID=...
LIGHTSPEED_CLIENT_SECRET=...
```

**Loading .env files**:

Python (with python-dotenv):
```python
from dotenv import load_dotenv
load_dotenv()

import os
api_key = os.environ["OPENAI_API_KEY"]
```

Node.js (with dotenv):
```javascript
require('dotenv').config();

const apiKey = process.env.OPENAI_API_KEY;
```

### Shell Profile

Add to `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`:

```bash
# API Keys
export OPENAI_API_KEY="your-key"
export GITHUB_TOKEN="your-token"

# Red Hat Lightspeed
export LIGHTSPEED_CLIENT_ID="your-client-id"
export LIGHTSPEED_CLIENT_SECRET="your-client-secret"

# AWS
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Security Note**: Ensure your shell profile has restrictive permissions:
```bash
chmod 600 ~/.bashrc ~/.zshrc
```

### Secret Management Tools

For production, consider using:

- **AWS Secrets Manager**: For AWS-hosted applications
- **HashiCorp Vault**: For multi-cloud secret management
- **1Password CLI**: For team secret sharing
- **GitHub Secrets**: For CI/CD pipelines

---

## Incident Response

### If You Accidentally Committed a Secret

**Act Immediately** - Assume the secret is compromised.

#### Step 1: Revoke the Credential

**Priority**: Revoke the exposed credential first.

- **OpenAI**: Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys) → Revoke
- **GitHub**: Go to [github.com/settings/tokens](https://github.com/settings/tokens) → Delete
- **AWS**: Go to IAM Console → Access Keys → Deactivate/Delete
- **Red Hat Lightspeed**: Contact administrator or regenerate via console

#### Step 2: Remove from Git History

**Warning**: Rewriting history requires force push.

```bash
# Install git-filter-repo (if not installed)
# macOS: brew install git-filter-repo
# Linux: pip install git-filter-repo

# Remove file from all history
git filter-repo --path path/to/secret/file --invert-paths

# Or remove specific pattern from all files
git filter-repo --replace-text <(echo "sk-proj-actual-key==>REDACTED")

# Force push (WARNING: coordinate with team)
git push --force --all
git push --force --tags
```

#### Step 3: Notify Team

- **Inform team members**: They need to re-clone or reset their local repos
- **Update CI/CD**: Rotate secrets in CI/CD pipelines
- **Audit access**: Check if the secret was used maliciously

#### Step 4: Verify Removal

```bash
# Search git history for secret
git log -S "sk-proj-abc123" --all

# Should return no results after cleanup
```

### Prevention Checklist

After an incident:

- [ ] Secret revoked and rotated
- [ ] Git history cleaned
- [ ] Force push completed
- [ ] Team notified
- [ ] CI/CD secrets updated
- [ ] Access logs audited
- [ ] Gitleaks hook installed/verified
- [ ] Root cause analysis completed
- [ ] Process updated to prevent recurrence

---

## Additional Resources

### Documentation References

- **Repository Guidelines**: [CLAUDE.md](CLAUDE.md) - Line 125 documents MCP credential requirements
- **.gitignore**: Pre-configured to exclude common secret files (.env, *.key, *.pem)
- **MCP Example**: [rh-sre/mcps.json](rh-sre/mcps.json) - Reference implementation with ${VAR} pattern
- **Gitleaks Configuration**: [.gitleaks.toml](.gitleaks.toml) - Project-specific rules

### External Resources

- **Gitleaks**: https://github.com/gitleaks/gitleaks
- **OWASP Secrets Management**: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- **GitHub Secret Scanning**: https://docs.github.com/en/code-security/secret-scanning
- **AWS Secrets Manager**: https://aws.amazon.com/secrets-manager/
- **git-filter-repo**: https://github.com/newren/git-filter-repo

---

## Support

For questions about this security policy:

1. Review this SECURITY.md document
2. Check [CLAUDE.md](CLAUDE.md) for repository-specific guidelines
3. Test with: `gitleaks protect --staged`
4. Open a GitHub issue for policy clarifications

**Important**: Never include actual secrets in issue reports or pull request descriptions.

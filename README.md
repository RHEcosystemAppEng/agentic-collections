Agentic collections to automate interaction with Red Hat platforms and products for various marketplaces.


| Agentic Pack | Persona/Role | Marketplaces |
|--------------|--------------|--------------|
| [Red Hat SRE](rh-sre/README.md) | SRE | Claude code, Cursor |
| [Red Hat Developer](rh-developer/README.md) | Developer | Claude code, Cursor |
| [OpenShift Administration](ocp-admin/README.md) | OpenShift Administration | Claude code, Cursor |
| [Red Hat Support Engineer](rh-support-engineer/README.md) | Support Engineer | Claude code, Cursor, ChatGPT |
| [Red Hat Virtualization](rh-virt/README.md) | Virt Admin | Claude code, Cursor |

## Documentation Site

View the interactive documentation at: **https://rhecosystemappeng.github.io/agentic-collections**

The site provides:
- **Agentic Collections**: Browse all available collections, skills, and agents with detailed descriptions
- **MCP Servers**: Explore MCP server configurations and integration details
- **Search**: Find collection, skills, agents, and servers by keyword across all content

### Prerequisites

The documentation tools use [uv](https://github.com/astral-sh/uv) for fast, isolated Python environment management:

```bash
# Install uv (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS with Homebrew
brew install uv
```

### Local Development

Generate and view documentation locally:

```bash
# Install dependencies (first time only)
make install

# Validate pack structure (plugin.json, .mcp.json, frontmatter)
make validate

# Validate skills against Design Principles (SKILL_DESIGN_PRINCIPLES.md)
# Validate only changed skills (staged + unstaged) - recommended for local dev:
make validate-skill-design-changed
# Or validate all skills / a specific pack:
make validate-skill-design
make validate-skill-design PACK=rh-sre

# Generate docs/data.json
make generate

# Start local server at http://localhost:8000
make serve

# Or run full test suite with auto-open
make test-full
```

Updates are automatically deployed to GitHub Pages when changes are pushed to main.

For more details, see [docs/README.md](docs/README.md).

### Skill Design Validation

Use the `validate-skill-design` and `validate-skill-design-changed` targets to check skills against the [Design Principles](SKILL_DESIGN_PRINCIPLES.md) referenced from CLAUDE.md. **CI runs this validation automatically** on pull requests and pushes to main, but only for changed skills. For local development, run `validate-skill-design-changed` to validate only your modified skills (staged + unstaged). To perform full validation or validate a specific pack, run `validate-skill-design`. Ensure compliance with:

- Document consultation transparency (DP1)
- Parameter specification and ordering (DP2)
- Description conciseness (DP3)
- Dependencies declaration (DP4)
- Human-in-the-loop requirements for critical operations (DP5)
- Mandatory sections (Prerequisites, When to Use, Workflow) (DP6)
- Credential security (no `echo $VAR` exposure) (DP7)

```bash
# Validate only changed skills (staged + unstaged) - recommended for local dev
make validate-skill-design-changed

# Validate all packs
make validate-skill-design

# Validate a specific pack only
make validate-skill-design PACK=rh-sre

# Treat warnings as errors
uv run python scripts/validate_skill_design.py --warnings-as-errors

```

## Security

This repository uses [gitleaks](https://github.com/gitleaks/gitleaks) to prevent accidental commits of sensitive data.

### Quick Start

```bash
# Install gitleaks and pre-commit hook (one-time setup)
scripts/install-hooks.sh
```

### What's Protected

- **API keys**: OpenAI, GitHub, AWS, Google Cloud
- **Private keys**: SSH, SSL/TLS certificates
- **Hardcoded credentials** in `.mcp.json` files
- **Database connection strings** with passwords
- **JWT tokens** and authentication secrets

### MCP Configuration Rules

✅ **CORRECT** - Use environment variable references:
```json
{
  "env": {
    "LIGHTSPEED_CLIENT_ID": "${LIGHTSPEED_CLIENT_ID}",
    "LIGHTSPEED_CLIENT_SECRET": "${LIGHTSPEED_CLIENT_SECRET}"
  }
}
```

❌ **BLOCKED** - Hardcoded values:
```json
{
  "env": {
    "LIGHTSPEED_CLIENT_SECRET": "sk-proj-abc123..."
  }
}
```

### Manual Scanning

```bash
# Scan entire repository history
gitleaks detect --source . --verbose

# Scan only staged changes
gitleaks protect --staged
```

See [SECURITY.md](SECURITY.md) for details.

## Adding a New MCP Server

To add a new MCP server to an agentic pack and display it on the documentation site:

### Step 1: Add MCP Configuration to Pack

Add the server configuration to `<pack>/.mcp.json`:

```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "podman|docker|npx",
      "args": ["run", "--rm", "-i", "..."],
      "env": {
        "VAR_NAME": "${VAR_NAME}"  // Always use env var references
      },
      "description": "Brief description of the MCP server",
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only|none"
      }
    }
  }
}
```

**Security Requirements:**
- ✅ Always use `${ENV_VAR}` references for credentials
- ❌ Never hardcode API keys, tokens, or secrets
- ✅ Set appropriate security isolation level

### Step 2: Add Custom Metadata (Optional)

To display repository links and tool descriptions on the documentation site, add an entry to `docs/mcp.json`:

```json
{
  "your-server-name": {
    "repository": "https://github.com/org/repo",
    "tools": [
      {
        "name": "tool_name",
        "description": "What this tool does and when to use it"
      }
    ]
  }
}
```

**Fields:**
- `repository`: GitHub repository URL (appears as README badge on server card)
- `tools`: Array of tool objects with name and description (displayed in server details modal)

### Step 3: Generate Documentation

Regenerate the documentation site data:

```bash
make generate
```

This will:
1. Parse the `.mcp.json` file from your pack
2. Merge it with custom data from `docs/mcp.json`
3. Update `docs/data.json` with the new server

### Step 4: Verify Locally

Test the changes locally:

```bash
make serve
```

Visit http://localhost:8000 and verify:
- Server appears in MCP Servers section
- Server card shows correct information
- README badge appears (if repository URL provided)
- Tools count displays (if tools provided)
- Details modal shows all configuration

### Step 5: Commit and Deploy

```bash
git add <pack>/.mcp.json docs/mcp.json docs/data.json
git commit -m "feat: add <server-name> MCP server to <pack>"
git push
```

The documentation site will automatically update via GitHub Actions.

### Example: Adding Red Hat Lightspeed MCP Server

**File: `rh-sre/.mcp.json`**
```json
{
  "mcpServers": {
    "lightspeed-mcp": {
      "command": "podman",
      "args": ["run", "--rm", "-i",
               "--env", "LIGHTSPEED_CLIENT_ID",
               "--env", "LIGHTSPEED_CLIENT_SECRET",
               "quay.io/redhat-services-prod/insights-mcp:latest"],
      "env": {
        "LIGHTSPEED_CLIENT_ID": "${LIGHTSPEED_CLIENT_ID}",
        "LIGHTSPEED_CLIENT_SECRET": "${LIGHTSPEED_CLIENT_SECRET}"
      },
      "description": "Red Hat Lightspeed MCP server for CVE data and remediation",
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only"
      }
    }
  }
}
```

**File: `docs/mcp.json`**
```json
{
  "lightspeed-mcp": {
    "repository": "https://github.com/RedHatInsights/insights-mcp",
    "tools": [
      {
        "name": "vulnerability__get_cves",
        "description": "Get list of CVEs affecting the account"
      },
      {
        "name": "vulnerability__get_cve",
        "description": "Get details about specific CVE"
      }
    ]
  }
}
```

### Troubleshooting

**Server not appearing:**
- Run `make validate` to check for JSON syntax errors
- Verify `.mcp.json` file is in the pack directory
- Check that pack directory is listed in `scripts/generate_pack_data.py` PACK_DIRS

**Tools not showing:**
- Ensure `docs/mcp.json` has entry for your server
- Verify tool objects have both `name` and `description` fields
- Regenerate with `make generate`

**Security errors:**
- Check for hardcoded credentials with `gitleaks protect --staged`
- Ensure all env values use `${VAR}` format
- Review security isolation settings


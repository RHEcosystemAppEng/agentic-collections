# Red Hat Agentic Collections

**Production-ready AI skills and automation for Red Hat platforms** - Install specialized plugins for SREs, developers, platform administrators, and AI engineers working with RHEL, OpenShift, and Red Hat automation platforms.

[![Validate Agentic Collections](https://github.com/RHEcosystemAppEng/agentic-collections/actions/workflows/compliance-check.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-collections/actions/workflows/compliance-check.yml)
[![Skill Specification Linter](https://github.com/RHEcosystemAppEng/agentic-collections/actions/workflows/skill-spec-report.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-collections/actions/workflows/skill-spec-report.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/Claude%20Code-Marketplace-purple)](https://github.com/RHEcosystemAppEng/agentic-collections)

---

## 🚀 Quick Start

### 1. Add the Marketplace

```bash
/plugin marketplace add RHEcosystemAppEng/agentic-collections
```

### 2. Install a Plugin

```bash
# For Site Reliability Engineers
/plugin install rh-sre@redhat-agentic-collections

# For Developers
/plugin install rh-developer@redhat-agentic-collections

# For OpenShift Administrators
/plugin install ocp-admin@redhat-agentic-collections

# For Virtualization Administrators
/plugin install openshift-virtualization@redhat-agentic-collections

# For AI/ML Engineers
/plugin install rh-ai-engineer@redhat-agentic-collections

# For Ansible Automation Platform Engineers
/plugin install rh-automation@redhat-agentic-collections
```

See each plugin's README for available skills and usage examples.

### 3. Update

```bash
# Update the marketplace to get latest plugin versions
/plugin marketplace update redhat-agentic-collections

# Update a specific plugin to the latest version
/plugin update rh-sre@redhat-agentic-collections
```

**Note:** Claude Code automatically checks for marketplace updates at startup. Manual updates are useful when you want the latest skills immediately.

### 4. Uninstall

```bash
# Uninstall a specific plugin
/plugin uninstall rh-sre@redhat-agentic-collections

# Remove the marketplace (this will uninstall all plugins from this marketplace)
/plugin marketplace remove redhat-agentic-collections
```

---

## 📦 Available Plugins

7 persona-focused plugins with **100+ production-ready skills**:

| Plugin | Version | Skills | Description | Personas |
|--------|---------|--------|-------------|----------|
| **[rh-sre](rh-sre/README.md)** | 1.0.0 | 38 | CVE remediation, system compliance, RHEL automation | Site Reliability Engineers |
| **[rh-developer](rh-developer/README.md)** | 1.0.0 | 14 | Application deployment, S2I builds, Helm charts | Application Developers |
| **[openshift-virtualization](rh-virt/README.md)** | 1.0.0 | 16 | VM lifecycle, snapshots, migrations, cloning | Virtualization Admins |
| **[ocp-admin](ocp-admin/README.md)** | 1.0.0 | 1 | Multi-cluster management, health reports, monitoring | OpenShift Administrators |
| **[rh-ai-engineer](rh-ai-engineer/README.md)** | 1.0.0 | 18 | Model serving, vLLM, KServe, NVIDIA NIM | AI/ML Engineers |
| **[rh-automation](rh-automation/README.md)** | 1.0.0 | 13 | Ansible Automation Platform governance, safety checks | Automation Leads |
| **[rh-support-engineer](rh-support-engineer/README.md)** | 1.0.0 | 0* | Technical support and troubleshooting | Support Engineers |

**Total:** 100 skills across 7 plugins | **License:** Apache 2.0 | **Status:** Production Ready

<sub>* Coming soon</sub>

---

## 📋 Prerequisites

### General Requirements

1. **Claude Code** (latest version recommended)
   - Desktop app ([claude.ai/code](https://claude.ai/code))
   - VS Code extension, JetBrains extension, or Web app
   - CLI tool

2. **Container Runtime** (Podman or Docker)
   - Required for MCP servers used by most plugins
   - Podman (recommended for Linux): `sudo dnf install podman`
   - Docker Desktop (macOS/Windows): [docker.com](https://docker.com)

3. **Network Access**
   - Internet connectivity for marketplace installation
   - Access to container registries (quay.io, registry.redhat.io)
   - Access to Red Hat platforms (depending on plugins used)

### Plugin-Specific Requirements

Each plugin has additional requirements:
- **Credentials**: Red Hat API keys, cluster kubeconfigs, service tokens
- **Platform Access**: OpenShift clusters, RHEL systems, Ansible Automation Platform
- **Permissions**: Cluster admin, namespace edit, or view roles

**See each plugin's README for detailed requirements and setup instructions.**

---

### Key Features

- **🎯 Role-Specific**: Each plugin is designed for specific personas and workflows
- **🔒 Security First**: Credential handling, human-in-the-loop for destructive operations
- **🔧 Production Ready**: 100+ skills validated against [design principles](SKILL_DESIGN_PRINCIPLES.md)
- **📚 Documentation**: AI-optimized docs with semantic indexing (rh-sre reference)
- **🔌 MCP Integration**: Red Hat Lightspeed, Ansible Automation Platform servers
- **✅ Quality Assured**: Automated compliance checks and specification linting

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

**Platform Notes (Linux vs macOS):**

On **Linux**, you may want to add `--userns=keep-id:uid=65532,gid=65532` to the Podman `args` for proper UID/GID mapping inside the container. This ensures the container process runs with the correct non-root user identity.

On **macOS**, this flag is **not supported** because Podman runs inside a Linux VM where user namespace mapping behaves differently. Omit it on macOS or the container will fail to start.

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

---

## 🧪 Local Testing

Test the marketplace locally before publishing:

### Add Local Marketplace

```bash
cd /path/to/agentic-collections
/plugin marketplace add .
```

### Install Plugin Locally

```bash
/plugin install rh-sre@redhat-agentic-collections
```

### Validate Marketplace

```bash
# Validate marketplace.json and all plugins
claude plugin validate .

# Or from within Claude Code
/plugin validate .
```

This will check:
- ✅ Marketplace.json schema compliance
- ✅ All plugin.json files syntax
- ✅ YAML frontmatter in skills
- ✅ Duplicate names
- ✅ Invalid paths

---

## 🤝 Contributing

We welcome contributions! Here's how to add or improve skills:

### Adding a New Skill

1. Follow the [Skill Design Principles](SKILL_DESIGN_PRINCIPLES.md)
2. Use the appropriate template:
   - General: See SKILL_DESIGN_PRINCIPLES.md
   - rh-virt collection: Use `rh-virt/SKILL_TEMPLATE.md`
3. Create `skills/<skill-name>/SKILL.md` with proper YAML frontmatter
4. Validate with the linter:
   ```bash
   make validate-skill-design-changed
   ```
5. Update the pack's `CLAUDE.md` intent routing table

### Adding a New Plugin

1. Create plugin directory: `<pack-name>/`
2. Add `.claude-plugin/plugin.json` with metadata
3. Add `skills/` directory
4. Add `CLAUDE.md` with persona and skill routing (see [rh-ai-engineer/CLAUDE.md](rh-ai-engineer/CLAUDE.md))
5. Add `README.md` with plugin description
6. Update marketplace.json:
   ```json
   {
     "name": "your-plugin",
     "description": "Plugin description",
     "version": "1.0.0",
     "author": {...},
     "source": "./your-plugin",
     "category": "your-category",
     "skills": "./skills"
   }
   ```
7. Validate: `make validate && claude plugin validate .`

### Pull Request Guidelines

- Run `make validate-skill-design-changed` before committing
- Ensure CI checks pass (compliance + linter)
- Follow conventional commits format
- Update relevant documentation

---

## 📚 Additional Resources

- **[Documentation Site](https://rhecosystemappeng.github.io/agentic-collections)**: Browse all collections, skills, and MCP servers
- **[CLAUDE.md](CLAUDE.md)**: Repository structure and development workflow
- **[Skill Design Principles](SKILL_DESIGN_PRINCIPLES.md)**: Quality guidelines for skills
- **[VALIDATION_REPORT.md](VALIDATION_REPORT.md)**: Marketplace compliance verification
- **[Security Policy](SECURITY.md)**: Credential handling and vulnerability reporting

---

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

**Maintained by:** [Red Hat Ecosystem Engineering](https://github.com/RHEcosystemAppEng)

**Questions?** Open an [issue](https://github.com/RHEcosystemAppEng/agentic-collections/issues) or check the [documentation site](https://rhecosystemappeng.github.io/agentic-collections).

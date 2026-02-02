Agentic packs to automate interaction with Red Hat platforms and products for various marketplaces.


| Agentic Pack | Persona/Role | Marketplaces |
|--------------|--------------|--------------|
| [Red Hat SRE](rh-sre/README.md) | SRE | Claude code, Cursor |
| [Red Hat Developer](rh-developer/README.md) | Developer | Claude code, Cursor |
| [OpenShift Administration](ocp-admin/README.md) | OpenShift Administration | Claude code, Cursor |
| [Red Hat Support Engineer](rh-support-engineer/README.md) | Support Engineer | Claude code, Cursor, ChatGPT |
| [Red Hat Virtualization](rh-virt/README.md) | Virt Admin | Claude code, Cursor |

## Documentation Site

View the interactive documentation at: **https://dmartinol.github.io/ai5-marketplaces/**

The site provides:
- **Agentic Packs**: Browse all available packs, skills, and agents with detailed descriptions
- **MCP Servers**: Explore MCP server configurations and integration details
- **Search**: Find packs, skills, agents, and servers by keyword across all content

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

# Validate pack structure
make validate

# Generate docs/data.json
make generate

# Start local server at http://localhost:8000
make serve

# Or run full test suite with auto-open
make test-full
```

Updates are automatically deployed to GitHub Pages when changes are pushed to main.

For more details, see [docs/README.md](docs/README.md).

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


<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, CLAUDE.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- Claude Code CLI or IDE extension (if using Claude Code)
- Podman or Docker installed (for container-based MCP servers)
- Red Hat Lightspeed service account ([console](https://console.redhat.com/))

### Environment setup

Configure Red Hat Lightspeed credentials (names must match **`mcps.json`**):

```bash
export LIGHTSPEED_CLIENT_ID="your-service-account-client-id"
export LIGHTSPEED_CLIENT_SECRET="your-service-account-client-secret"
```

For Ansible Automation Platform MCP (optional, for playbook execution flows):

```bash
export AAP_MCP_SERVER="your-aap-controller-hostname"
export AAP_API_TOKEN="your-api-token"
```

### Installation (Lola)

From a checkout of this repository, install the pack with [Lola](https://github.com/RedHatProductSecurity/lola) using the registry file at the repo root:

```bash
lola install -f rh-sre
```

The module is declared in **`marketplace/rh-agentic-collection.yml`** (`path: rh-sre`). See the root [README.md](../../README.md) for marketplace setup.

### Installation (Claude Code)

Install the collection as a Claude Code plugin:

```bash
claude plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-collections
claude plugin install rh-sre
```

Or for local development:

```bash
claude plugin marketplace add /path/to/agentic-collections
claude plugin install rh-sre
```

### Installation (Cursor)

Cursor does not support direct marketplace install via CLI. Clone the repository and copy the pack:

```bash
git clone https://github.com/RHEcosystemAppEng/agentic-collections.git
cp -r agentic-collections/rh-sre ~/.cursor/plugins/rh-sre
```

Or download and extract:

```bash
wget -qO- https://github.com/RHEcosystemAppEng/agentic-collections/archive/refs/heads/main.tar.gz | tar xz
cp -r agentic-collections-main/rh-sre ~/.cursor/plugins/rh-sre
```

### MCP configuration

Server definitions live in **`mcps.json`** at the pack root. Use **`${VAR}`** placeholders only; never commit secrets.

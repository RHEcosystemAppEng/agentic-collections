<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, CLAUDE.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- Claude Code CLI or IDE extension (if using Claude Code)
- Podman installed (for the container-based Lightspeed MCP server)
- Red Hat service account ([console.redhat.com](https://console.redhat.com/iam/service-accounts))

Skills fall back to WebFetch on public Red Hat documentation if the MCP server is not configured — Podman and a service account are optional.

### Environment setup

Configure Red Hat Lightspeed credentials (names must match **`mcps.json`**):

```bash
export LIGHTSPEED_CLIENT_ID="your-service-account-client-id"
export LIGHTSPEED_CLIENT_SECRET="your-service-account-client-secret"
```

Secrets must never be committed to the repository and must not be echoed in assistant output.

### Installation (Lola)

From a checkout of this repository, install the pack with [Lola](https://github.com/RedHatProductSecurity/lola):

```bash
lola install -f rh-basic
```

The module is declared in **`marketplace/rh-agentic-collection.yml`** (`path: rh-basic`). See the root [README.md](../../README.md) for marketplace setup.

### Installation (Claude Code)

```bash
lola install -f rh-basic -a claude-code
```

### Installation (Cursor)

```bash
lola install -f rh-basic -a cursor
```

### MCP configuration

Server definitions live in **`mcps.json`** at the pack root. The Lightspeed MCP server runs as a Podman container using `${LIGHTSPEED_CLIENT_ID}` and `${LIGHTSPEED_CLIENT_SECRET}` placeholders only; never commit secret values.

Configure the environment variables above, then run `lola install -f rh-basic` to install the pack.

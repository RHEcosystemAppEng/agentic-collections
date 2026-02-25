# Copilot Instructions for agentic-collections

## Repository Overview

This repository contains **agentic collections** — persona-specific plugin packs that automate interactions with Red Hat platforms. Each pack ships skills, agents, and MCP server configurations for AI marketplaces (Claude Code, Cursor, ChatGPT).

## Repository Structure

```
agentic-collections/
├── rh-sre/              # Site Reliability Engineering (reference implementation)
├── rh-developer/        # Developer tools
├── ocp-admin/           # OpenShift administration
├── rh-support-engineer/ # Technical support
├── rh-virt/             # Virtualization management
├── docs/                # Generated documentation site (do not edit data.json manually)
├── scripts/             # Python build/validate/generate scripts
└── Makefile             # Main developer commands
```

### Inside each pack

```
<pack>/
├── README.md
├── .claude-plugin/plugin.json   # Optional: name, version, description, author, license
├── .mcp.json                    # MCP server configs — credentials via env vars ONLY
├── agents/<agent>.md            # Workflow orchestrators (YAML frontmatter required)
└── skills/<skill-name>/SKILL.md # Task executors (YAML frontmatter required)
```

## Build, Validate, and Test

All tooling uses [uv](https://github.com/astral-sh/uv). Install it once:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

| Command | Purpose |
|---|---|
| `make install` | Install Python deps |
| `make validate` | Validate pack/skill/agent structure (runs in CI) |
| `make generate` | Rebuild `docs/data.json` |
| `make test` | validate + generate + verify checks |
| `make serve` | Local site at http://localhost:8000 |

**CI runs `make install && make validate` on every PR.** Always run `make validate` after editing skills, agents, or `.mcp.json` files to catch errors before pushing.

Packs known to the validator are listed in `scripts/validate_structure.py` (`PACK_DIRS`). Add new packs there when creating them.

## Key File Formats

### Skills — `skills/<name>/SKILL.md`

Must start with valid YAML frontmatter containing at minimum `name` and `description`:

```yaml
---
name: skill-name
description: |
  Concise when-to-use description with 3-5 examples.
  Keep under 500 tokens.
model: inherit
color: blue
---
```

### Agents — `agents/<name>.md`

Same YAML frontmatter requirement (`name` + `description`). Agents orchestrate skills; they do not call MCP tools directly.

### `.mcp.json`

```json
{
  "mcpServers": {
    "server-name": {
      "command": "podman",
      "args": ["run", "--rm", "-i", "..."],
      "env": { "SECRET": "${SECRET}" },
      "description": "...",
      "security": { "isolation": "container", "network": "local", "credentials": "env-only" }
    }
  }
}
```

**NEVER hardcode credentials.** Always use `${ENV_VAR}` references. Gitleaks runs as a pre-commit hook and in CI.

## Design Principles (from CLAUDE.md)

1. **Skills encapsulate tools** — never call MCP tools directly; always go through a skill.
2. **Agents orchestrate skills** — complex workflows delegate to specialized skills.
3. **Document consultation is an action** — actually read reference docs with the Read tool before claiming to have consulted them.
4. **Precise parameters** — specify exact tool parameters (names, formats, examples) so first-attempt tool calls succeed.
5. **Human-in-the-loop for critical ops** — require explicit confirmation before playbook execution or destructive actions.
6. **Never print credential values** — only report whether env vars are set/unset, never their contents.
7. **Dependencies section in every skill** — list required MCP servers, tools, related skills, and reference docs.

## Adding a New Pack

1. Create `<pack-name>/` directory with `README.md`.
2. Add `skills/` and optionally `agents/`, `.mcp.json`, `.claude-plugin/plugin.json`.
3. Add the new pack name to `PACK_DIRS` in `scripts/validate_structure.py`.
4. Run `make validate && make generate` to regenerate docs locally for testing; do **not** commit `docs/data.json` (it is generated during deployment).

## Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md` with valid YAML frontmatter.
2. Follow the mandatory section order: Prerequisites → When to Use → Workflow → Dependencies → (Human-in-the-Loop if needed) → Example Usage.
3. Run `make validate` to confirm no errors.

See `rh-virt/SKILL_TEMPLATE.md` for the canonical skill template and `rh-sre` as the full reference implementation.

## Security

- Gitleaks protects against accidental secret commits.
- Install pre-commit hook: `scripts/install-hooks.sh`
- Manual scan: `gitleaks detect --source . --verbose`
- See `SECURITY.md` and `.gitleaks.toml` for details.

## Common Errors and Workarounds

| Error | Cause | Fix |
|---|---|---|
| `Missing YAML frontmatter` | SKILL.md or agent .md missing `---` block | Add frontmatter with `name` and `description` |
| `Invalid JSON in .mcp.json` | Syntax error or comments in JSON | JSON does not support comments; remove them |
| `Pack directory does not exist` | New pack not listed in validator | Add to `PACK_DIRS` in `scripts/validate_structure.py` |
| `uv: command not found` | uv not installed | `curl -LsSf https://astral.sh/uv/install.sh | sh` |
| Gitleaks blocks commit | Credential-like value in file | Use `${ENV_VAR}` references instead of literal values |

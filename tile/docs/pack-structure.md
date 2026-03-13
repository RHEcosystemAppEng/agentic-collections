# Pack & Skill Structure

Conventions for creating new agentic packs, skills, and agents in agentic-collections.

## Pack Directory Structure

```
<pack-name>/
├── README.md                    # Pack description, persona, target marketplaces
├── .claude-plugin/              # Claude Code plugin metadata (optional)
│   └── plugin.json
├── .mcp.json                    # MCP server configurations
├── skills/                      # Skill definitions
│   └── <skill-name>/            # kebab-case, matches SKILL.md 'name' field
│       └── SKILL.md             # Skill definition
├── agents/                      # Agent definitions (optional)
│   └── <agent-name>.md
└── docs/                        # AI-optimized knowledge base (optional)
    ├── INDEX.md
    ├── SOURCES.md
    └── .ai-index/
        ├── semantic-index.json
        ├── task-to-docs-mapping.json
        └── cross-reference-graph.json
```

All five packs are listed in `scripts/validate_structure.py`:
```python
PACK_DIRS = ['rh-sre', 'rh-developer', 'ocp-admin', 'rh-support-engineer', 'rh-virt']
```

## plugin.json Schema

```json { .api }
{
  "name": "string",           // REQUIRED — pack name (kebab-case)
  "version": "string",        // REQUIRED — semantic version
  "description": "string",    // REQUIRED — pack description
  "author": {
    "name": "string",         // OPTIONAL
    "email": "string"         // OPTIONAL
  },
  "homepage": "string",       // OPTIONAL — URL
  "repository": "string",     // OPTIONAL — URL
  "license": "string",        // OPTIONAL — e.g. "Apache-2.0"
  "keywords": ["string"]      // OPTIONAL — search keywords
}
```

If `plugin.json` is missing, defaults are used: `version='0.0.0'`, `author={'name': 'Red Hat'}`, `license='Apache-2.0'`.

## .mcp.json Schema

```json { .api }
{
  "mcpServers": {
    "<server-name>": {
      // --- Command-based server (default) ---
      "command": "podman|docker|npx|bash",
      "args": ["string"],
      "env": {
        "VAR_NAME": "${VAR_NAME}"   // ALWAYS use ${VAR} references — NEVER hardcode
      },

      // --- HTTP-based remote server ---
      "type": "http",
      "url": "https://${HOST}/path/mcp",
      "headers": {
        "Authorization": "Bearer ${TOKEN}"
      },
      "env": {},     // optional for HTTP servers

      // --- Common fields ---
      "description": "string",
      "security": {
        "isolation": "container|process",
        "network": "local",
        "credentials": "env-only|none"
      }
    }
  }
}
```

**Security rules:**
- ALWAYS use `${ENV_VAR}` references for credentials
- NEVER hardcode API keys, tokens, or secrets
- Set appropriate `security.isolation` level

**Platform notes (Linux vs macOS):**
- Linux: add `--userns=keep-id:uid=65532,gid=65532` to Podman args for proper UID/GID mapping
- macOS: omit `--userns` (unsupported inside Podman VM)

## SKILL.md Frontmatter Schema

```yaml { .api }
---
name: skill-name               # REQUIRED — kebab-case; matches directory name exactly
                               # Format: 1-64 chars, a-z0-9-, no --, no leading/trailing -
description: |                 # REQUIRED — < 500 tokens (~2000 chars)
  [Description — what the skill does]

  Use when:
  - "Example user query 1"
  - "Example user query 2"
  - User mentions "keyword"

  NOT for [use case] (use [/other-skill] instead).
model: inherit|sonnet|haiku    # REQUIRED
  # inherit: use parent context (recommended)
  # sonnet: complex reasoning tasks
  # haiku: simple, fast operations
color: cyan|green|blue|yellow|red|magenta  # REQUIRED
  # cyan:    read-only (list, view, get)
  # green:   additive (create, clone, build)
  # blue:    reversible (start, stop, restart)
  # yellow:  destructive but recoverable
  # red:     irreversible (delete, restore)
  # magenta: creative (generation)
metadata:                      # OPTIONAL — custom key-value pairs
  author: "team-name"
  version: "1.0"
  user_invocable: "true"       # marks as user-invokable via slash command
---
```

## Mandatory Skill Sections (in order)

```markdown { .api }
# /skill-name Skill
[1-2 sentence overview]

## Critical: Human-in-the-Loop Requirements
[Include when skill creates/deletes/modifies/executes — omit for read-only skills]

## Prerequisites
**Required MCP Servers:** `server-name` ([setup guide](link))
**Required MCP Tools:** `tool_name` (from server) — Description
**Environment Variables:** `VAR` — What it controls
**Verification Steps:** [check MCP available, check env vars — never expose values]
**Human Notification Protocol:** [what to do when prerequisites fail]
**Security:** Never display credential values.

## When to Use This Skill
Use when:
- [Scenario 1]
- [Scenario 2]

Do NOT use when:
- [Anti-pattern] → Use `/other-skill` instead

## Workflow
### Step 1: [Action Name]
**Document Consultation** (if applicable):
1. **Action**: Read [doc.md](path) using Read tool to understand [topic]
2. **Output to user**: "I consulted [doc.md](path) to understand [topic]."

**MCP Tool**: `tool_name` (from server-name)
**Parameters**:
- `param`: "value" (type, format, constraints)
**Expected Output**: [Description]
**Error Handling**:
- If [condition]: [resolution]

## Dependencies
### Required MCP Servers
- `server-name` — Description ([setup](link))

### Required MCP Tools
- `tool_name` (from server) — What it does
  - Parameters: param1, param2

### Related Skills
- `skill-name` — When to use instead

### Reference Documentation
**Internal:** [doc.md](path) — Purpose
**Official:** [Title](https://docs.redhat.com/...)

## Example Usage
[User query → skill response example]
```

## Skill-to-Skill Invocation

When one skill invokes another, use the slash format consistently:

```markdown { .api }
# CORRECT — slash format
Execute the `/mcp-lightspeed-validator` skill
Invoke the `/playbook-executor` skill

# WRONG — inconsistent
Use the Skill tool:
  skill: "mcp-lightspeed-validator"
```

## Skill Design Principles Summary

| # | Principle | Key Requirement |
|---|-----------|-----------------|
| 1 | Document Consultation Transparency | Use Read tool first, then declare "I consulted [doc]" |
| 2 | Precise Parameter Specification | Exact parameter names, types, formats |
| 3 | Skill Precedence & Conciseness | Invoke skills not raw MCP tools; description < 500 tokens |
| 4 | Skill-to-Skill Invocation | Use `/skill-name` slash format |
| 5 | Dependencies Declaration | `## Dependencies` with all 4 subsections |
| 6 | Human-in-the-Loop | Confirmations for create/delete/modify/execute |
| 7 | Mandatory Sections | Prerequisites, When to Use, Workflow (in order) |
| 8 | MCP Verification | Check availability; NEVER echo $VAR values |
| 9 | Single Responsibility | One purpose per skill |
| 10 | Naming Conventions | kebab-case; folder = `name` field; file = SKILL.md |
| 11 | Content Quality | No hardcoded values (`<namespace>` not `production`), no broken links |

## Agent Template

```yaml { .api }
---
name: agent-name
description: |
  Multi-step workflow orchestrating skills.

  Use when:
  - [Complex multi-step workflow]

  NOT for single ops (use skills).
model: inherit
color: red
metadata:
  tools: ["All"]
---

# [Agent Name]

[Overview]

## Prerequisites
[MCP servers and skills — see Skill Design Principles]

## When to Use This Agent
[Multi-step workflows vs individual skills]

## Workflow

### Step 1: [Action]

**Invoke skill:**
Execute the `/skill-name` skill

**Human Confirmation** (if critical):
Ask: "Proceed?" Wait for confirmation.

## Dependencies
### Required MCP Servers
### Required MCP Tools
### Related Skills
### Reference Documentation

## Critical: Human-in-the-Loop Requirements
[If applicable]
```

## AI Documentation System (rh-sre pattern)

```yaml { .api }
# YAML frontmatter for docs in rh-sre/docs/
---
title: Document Title
category: rhel|ansible|openshift|insights|references
sources:
  - title: Official Red Hat Doc Title
    url: https://docs.redhat.com/...
    date_accessed: YYYY-MM-DD
tags: [keyword1, keyword2]
semantic_keywords: [phrases for AI discovery]
use_cases: [task_ids]
related_docs: [cross-references]
last_updated: YYYY-MM-DD
---
```

**Source attribution**: All content must derive from official Red Hat documentation. Document sources in `docs/SOURCES.md`.

**Doc structure**: Overview → When to Use → Main Content → Related Docs

**Performance targets**: 29% token reduction, 85% navigation overhead reduction via semantic indexing.

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Pack folder | lowercase-dash | `rh-sre`, `ocp-admin` |
| Skill folder | kebab-case, matches `name` field | `skills/cve-impact/` |
| Skill file | uppercase SKILL.md | `SKILL.md` |
| Agent file | lowercase-dash.md | `agents/full-remediation.md` |
| Skill `name` field | 1-64 chars, `a-z0-9-`, no `--`, no leading/trailing `-` | `cve-impact` |

## Adding a New Pack

```bash
# 1. Create pack directory
mkdir <pack-name>

# 2. Create README.md with description, persona, marketplaces

# 3. Create skills directory
mkdir -p <pack-name>/skills

# 4. (Optional) Add plugin.json
mkdir -p <pack-name>/.claude-plugin
# Create .claude-plugin/plugin.json

# 5. (Optional) Add MCP server config
# Create .mcp.json

# 6. Add to validate_structure.py PACK_DIRS and generate_pack_data.py PACK_DIRS

# 7. Add title to docs/plugins.json

# 8. Validate
make validate
```

## Adding a New Skill

```bash
# 1. Create skill directory (name must match SKILL.md 'name' field)
mkdir -p <pack-name>/skills/<skill-name>

# 2. Create SKILL.md with mandatory frontmatter and sections
# See SKILL.md Frontmatter Schema and Mandatory Sections above

# 3. Run Tier 1 linter (agentskills.io spec)
./scripts/run-skill-linter.sh <pack-name>/skills/<skill-name>/

# 4. Run Tier 2 validator (design principles)
uv run python scripts/validate_skill_design.py <pack-name>

# 5. Validate structure
make validate
```

## Adding an MCP Server to a Pack

```bash
# 1. Add server config to <pack>/.mcp.json (use ${ENV_VAR} references)

# 2. (Optional) Add custom metadata to docs/mcp.json

# 3. Regenerate documentation
make generate

# 4. Validate
make validate
```

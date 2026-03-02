# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains **agentic collections** - plugin collections that automate interactions with Red Hat platforms and products across multiple AI marketplaces (Claude Code, Cursor, ChatGPT). Each pack is persona-specific and includes skills, agents, and supporting documentation.

## Repository Structure

```
agentic-collections/
├── rh-sre/              # Site Reliability Engineering pack (reference implementation)
├── rh-developer/        # Developer tools pack
├── ocp-admin/           # OpenShift administration pack
├── rh-support-engineer/ # Technical support pack
└── rh-virt/             # Virtualization management pack
```

### Agentic Pack Architecture

Each pack follows this structure:
```
<pack-name>/
├── README.md            # Pack description, persona, target marketplaces
├── .claude-plugin/      # Claude Code plugin metadata
│   └── plugin.json      # Name, version, description, author, license
├── .mcp.json           # MCP server configurations (uses env vars for credentials)
├── agents/             # Multi-step workflow orchestrators
│   └── <agent>.md      # Agent definition with YAML frontmatter
├── skills/             # Specialized task executors
│   └── <skill>/
│       └── SKILL.md    # Skill definition with YAML frontmatter
└── docs/               # AI-optimized knowledge base (rh-sre only currently)
    ├── INDEX.md        # Documentation map and AI discovery guide
    ├── SOURCES.md      # Official Red Hat source attributions
    └── .ai-index/      # Semantic indexing for token optimization
```

## Working with Agentic Collections

### Skills vs Agents

**Skills** (`skills/<skill-name>/SKILL.md`):
- Single-purpose task executors
- Encapsulate specific tool access and domain knowledge
- Invoked via the `Skill` tool
- Structure: YAML frontmatter + implementation guide
- Example: `cve-impact` (CVE risk assessment), `playbook-generator` (Ansible generation)

**Agents** (`agents/<agent>.md`):
- Multi-step workflow orchestrators
- Delegate to multiple skills in sequence
- Invoked via the `Task` tool with `subagent_type`
- Structure: YAML frontmatter + workflow definition
- Example: `remediator` (orchestrates 5 skills for end-to-end CVE remediation)

**Key Pattern**: Agents orchestrate skills; skills encapsulate tools. Never call MCP tools directly - always go through skills.

## Skill and Agent Requirements

**CRITICAL:** EVERY SKILL and AGENT must comply with:
- **Tier 1:** agentskills.io specification (AUTOMATED via linter)
- **Tier 2:** Repository design principles (MANUAL review)

**Before committing any skill:**

1. **Run automated validation (Tier 1):**
   ```bash
   ./scripts/run-skill-linter.sh skills/skill-name/
   ```

2. **Manual review (Tier 2):**
   - Review [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) for complete requirements
   - Use appropriate template (general or collection-specific)
   - Verify all design principles are followed

**Documentation:**
- [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) - Complete design principles, templates, and rationale

### MCP Server Integration

MCP servers are configured in `<pack>/.mcp.json`:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "podman|docker|npx",
      "args": ["..."],
      "env": {
        "VAR_NAME": "${VAR_NAME}"  // Environment variable references
      },
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only"
      }
    }
  }
}
```

**Critical**: Never hardcode credentials. Always use `${ENV_VAR}` references.

## AI-Optimized Documentation (rh-sre Reference)

The `rh-sre` pack demonstrates advanced documentation patterns for token optimization:

### Semantic Indexing System

Located in `docs/.ai-index/`:
- `semantic-index.json` - Document metadata with semantic keywords
- `task-to-docs-mapping.json` - Pre-computed doc sets for common workflows
- `cross-reference-graph.json` - Document relationship graph

**Usage Pattern** (for AI agents reading rh-sre docs):
1. Read `semantic-index.json` first (~200 tokens)
2. Match task keywords to relevant docs
3. Load only required docs using progressive disclosure
4. Follow cross-references for related content

**Performance**: 29% token reduction on average, 85% reduction in navigation overhead

### Documentation Standards

All docs include YAML frontmatter:
```yaml
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

**Source Attribution**: All content derived from official Red Hat documentation (see `docs/SOURCES.md`)

## Naming Conventions

### Folders
- Lowercase with dash separators: `rh-sre`, `ocp-admin`
- Red Hat prefix: `rh-`
- Acronyms for brevity: `ocp` (OpenShift Container Platform), `virt` (Virtualization)

### Files
- Skills: `skills/<skill-name>/SKILL.md` (uppercase SKILL.md)
- Agents: `agents/<agent-name>.md` (lowercase, no folder)
- Docs: Lowercase with dashes, categorized by directory

## Development Workflow

### Creating a New Agentic Pack

1. Create pack folder: `<pack-name>/`
2. Add `README.md` with description, persona, marketplaces
3. Create `skills/` directory
4. Optional: Add `.claude-plugin/plugin.json` for Claude Code
5. Optional: Add `.mcp.json` for MCP server integrations
6. Optional: Add `agents/` for multi-step workflows
7. Update main `README.md` table with link

### Adding a Skill

1. Create `skills/<skill-name>/SKILL.md`
2. Define YAML frontmatter with mandatory fields:
   - `name`, `description` (agentskills.io spec)
   - `model` (inherit|sonnet|haiku), `color` (cyan|green|blue|yellow|red) - Repository requirement
   - Optional: `metadata` for custom fields (author, priority, version)
3. Follow [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) for:
   - Section structure and ordering
   - Prerequisites with verification
   - Workflow with precise parameters
   - Dependencies declaration
4. Include concrete examples and complete error handling
5. Test with `Skill` tool invocation
6. Validate with `./scripts/run-skill-linter.sh skills/<skill-name>/`

**Collection-Specific Standards:**
- **rh-virt**: Follow `rh-virt/SKILL_TEMPLATE.md` for enhanced quality standards including mandatory Common Issues and Example Usage sections

### Adding an Agent

1. Create `agents/<agent-name>.md`
2. Follow skill requirements in [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) (agents use same structure)
3. Define YAML frontmatter (name, description, model, tools)
4. Document workflow that orchestrates multiple skills
5. Provide clear examples of when to use agent vs individual skills
6. Test with `Task` tool invocation

### Adding Documentation (rh-sre pattern)

1. Create doc in appropriate category: `docs/{rhel,ansible,openshift,insights,references}/`
2. Add complete YAML frontmatter with official sources
3. Follow content structure: Overview → When to Use → Main Content → Related Docs
4. Lead with code examples (production-ready, not toy examples)
5. Update `docs/INDEX.md` navigation structure
6. Update `docs/SOURCES.md` with source URLs
7. Regenerate indexes: `python docs/.ai-index/generate-index.py` (when available)

## Integration with Red Hat Platforms

### Red Hat Lightspeed MCP Server
- CVE vulnerability data and risk assessment
- System inventory and compliance
- Remediation playbook generation
- Requires: `LIGHTSPEED_CLIENT_ID`, `LIGHTSPEED_CLIENT_SECRET` env vars

### Ansible MCP Server
- Playbook execution and job tracking
- Status monitoring
- Container-isolated execution

## Reference Implementation

The `rh-sre` pack is the most complete implementation, demonstrating:
- Full skill orchestration (10 skills)
- Agent-based workflows (remediator agent)
- AI-optimized documentation system
- MCP server integration
- Red Hat Lightspeed platform integration

When creating new collection, use `rh-sre` as the architectural reference.

### rh-virt (Quality-Controlled Pattern)

The `rh-virt` pack demonstrates skill quality standardization:
- Comprehensive skill templates (`SKILL_TEMPLATE.md`)
- Risk-based color coding (cyan/green/blue/yellow/red)
- Mandatory Common Issues and Example Usage sections
- Consistent section ordering and formatting

Use `rh-virt` as reference for collections requiring high consistency and maintainability.

When creating new collections, follow the pattern that best matches your needs:
- **Tool-focused domains** (infrastructure, operations) → Follow rh-virt pattern

## Key Principles

### Core Architecture
1. **Skills encapsulate tools** - Never call MCP tools directly; always invoke skills
2. **Agents orchestrate skills** - Complex workflows delegate to specialized skills
3. **agentskills.io compliance** - All skills follow the official specification
4. **Progressive disclosure** - Load docs incrementally based on task needs

### Security & Configuration
5. **Environment variables for secrets** - Never hardcode credentials
6. **Never expose credential values** - Check env vars are set, but NEVER print their values in output
7. **MCP server integration** - Use `.mcp.json` with environment variable references

### Documentation & Quality
8. **Official sources only** - Document all sources in SOURCES.md
9. **Production-ready examples** - No toy code, include error handling
10. **Persona-focused design** - Each collection serves specific user roles

**Validation:**
- Design principles and requirements: [SKILL_DESIGN_PRINCIPLES.md](./SKILL_DESIGN_PRINCIPLES.md)
- Automated linter (Tier 1): `./scripts/run-skill-linter.sh`

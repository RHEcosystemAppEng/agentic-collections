---
title: Skill Conventions
category: references
tags: [conventions, prerequisites, human-in-the-loop, security]
semantic_keywords: [prerequisite verification, human confirmation, credential security, skill shared patterns]
use_cases: [nim-setup, model-deploy, serving-runtime-config, debug-inference]
last_updated: 2026-03-01
---

# rh-ai-engineer Skill Conventions

Shared conventions for all skills in the rh-ai-engineer agentic collection.

## Prerequisite Verification Protocol

Before executing any skill, verify MCP server availability:

1. **Check MCP Server Configuration** - Verify required servers exist in `.mcp.json`
2. **Check Environment Variables** - Verify required env vars are set (check presence only, NEVER expose values)
3. **Check Optional MCP Servers** - Note availability; skip optional features if unavailable (non-blocking)

**When prerequisites fail:**

1. Stop execution immediately
2. Report the specific missing prerequisite:
   ```
   Cannot execute [skill-name]: [specific prerequisite] is not available

   Setup Instructions:
   1. [Server-specific setup steps]
   2. Set required environment variables
   3. Restart Claude Code to reload MCP servers

   Documentation: [link to server docs]
   ```
3. Offer options: "setup" (help configure now) / "skip" (skip this skill) / "abort" (stop workflow)
4. WAIT for user decision -- never proceed automatically

**Common prerequisite: OpenShift MCP Server**

All rh-ai-engineer skills require the `openshift` MCP server:
- Source: https://github.com/openshift/openshift-mcp-server
- Required env var: `KUBECONFIG`
- Setup: Add to `.mcp.json`, set KUBECONFIG, restart Claude Code

## Human-in-the-Loop Requirements

All rh-ai-engineer skills that create or modify Kubernetes resources MUST:

1. **Display the resource manifest** (with credentials REDACTED) before creation
2. **Ask for explicit confirmation** -- "yes/no" or "yes/no/modify"
3. **WAIT for user response** -- never auto-execute
4. **On failure, present diagnostic options** -- never auto-delete or auto-retry

**Never:**
- Create resources without user reviewing the manifest
- Display actual credential values (API keys, passwords, tokens)
- Skip confirmation for any resource creation
- Assume approval -- always wait for explicit user confirmation

**Why This Matters:**
- GPU resources are expensive and may have associated costs
- Deployments may affect other workloads competing for cluster resources
- Credentials grant access to external services (NGC, model registries)

## Security Conventions

- **Credentials**: Never display actual values; only report presence/absence
- **Secrets**: Use proper Kubernetes Secret types (`dockerconfigjson`, `Opaque`)
- **KUBECONFIG**: Path and contents never exposed in output
- **Namespace isolation**: All resources created in user-specified namespace only
- **RBAC**: Check for sufficient permissions before attempting resource creation
- **Credential lifecycle**: Advise users to rotate API keys periodically

---
title: Skill Conventions
category: references
tags: [conventions, prerequisites, human-in-the-loop, security, resilience, fallback]
semantic_keywords: [prerequisite verification, human confirmation, credential security, skill shared patterns, MCP resilience, OpenShift fallback, RBAC degradation]
use_cases: [nim-setup, model-deploy, serving-runtime-config, debug-inference, ai-observability, model-monitor, guardrails-config, ds-project-setup, workbench-manage, pipeline-manage, model-registry]
last_updated: 2026-03-23
---

# rh-ai-engineer Skill Conventions

Shared conventions for all skills in the rh-ai-engineer agentic collection.

## MCP Server Requirement Tiers

All rh-ai-engineer skills classify MCP servers into three tiers:

**Required** — The skill cannot function without this server. Fail immediately if unavailable.
- `openshift` — The only universally required server. Provides reliable Kubernetes resource CRUD via `resources_get`, `resources_list`, `resources_create_or_update`, `resources_delete`, `pods_list`, `pods_log`, `events_list`.

**Preferred** — Try this server's tools first for convenience and higher-level abstraction. On failure (auth error, API error, connection error), automatically fall back to the Required server's equivalent operation.
- `rhoai` — Provides RHOAI-specific convenience tools (`deploy_model`, `create_workbench`, etc.). All operations have OpenShift equivalents documented in [openshift-fallback-templates.md](openshift-fallback-templates.md).

**Optional** — Used when available; features gracefully skipped when unavailable.
- `ai-observability` — GPU metrics, vLLM analysis, distributed tracing. Non-blocking.

Skills MUST use this structure in their Prerequisites section:
```markdown
**Required MCP Server**: `openshift` (hard requirement, no fallback)
**Preferred MCP Server**: `rhoai` (used when available, OpenShift fallback on failure)
**Optional MCP Server**: `ai-observability` (skipped when unavailable)
```

## MCP Server Resilience Protocol

When an RHOAI MCP tool fails (Unauthorized, Unsupported Media Type, Unprocessable Entity, connection error, or any non-success response):

1. **Do NOT prompt the user** about the failure — immediately attempt the OpenShift fallback
2. **Use the equivalent operation** from [openshift-fallback-templates.md](openshift-fallback-templates.md)
3. **Report the fallback transparently** in the output: "Note: Used OpenShift direct API (RHOAI tool returned [brief error description])."
4. **Never fail a skill workflow** solely because an RHOAI tool is unavailable — always have an OpenShift alternative
5. **If the OpenShift fallback also fails**, then report the error and offer user options

**RHOAI tools that are permanently replaced** (do NOT attempt these — always use OpenShift):
- `list_notebook_images` — returns incorrect hardcoded image names. Use ImageStream lookup via OpenShift instead (see [openshift-fallback-templates.md](openshift-fallback-templates.md#notebook-image-discovery-imagestream-lookup)).
- `list_catalog_sources` — wrong API type detection. Use `resources_list` for catalog CRs instead.
- `create_pipeline_server` — constructs invalid DSPA manifest. Use `resources_create_or_update` with correct DSPA YAML template instead (see [openshift-fallback-templates.md](openshift-fallback-templates.md#datasciencepipelinesapplication-dspa)).

## RBAC Graceful Degradation

When any MCP tool returns a 403 Forbidden or "insufficient permissions" error:

1. **Try namespace-scoped alternative** — if a cluster-scoped operation fails (e.g., list Nodes), try the namespace-scoped equivalent (e.g., list pods with GPU resource requests)
2. **Report actionable information** — identify the specific API group, resource, and verb that was denied
3. **Never display raw HTTP errors** — translate to user-friendly messages:
   ```
   Permission denied: Cannot [verb] [resource] in [namespace/cluster].
   Required RBAC: [specific role or permission needed]
   Contact your cluster administrator to grant access.
   ```
4. **Suggest minimum required roles** — e.g., "edit role in namespace X" or "cluster-monitoring-view for Prometheus access"

## Prerequisite Verification Protocol

Before executing any skill, verify MCP server availability:

1. **Check Required MCP Servers** - Verify `openshift` server is configured and responding. Fail if unavailable.
2. **Check Preferred MCP Servers** - Note if `rhoai` is available. If unavailable, inform user that OpenShift direct API will be used for all operations (non-blocking).
3. **Check Optional MCP Servers** - Note availability of `ai-observability`; skip optional features if unavailable (non-blocking).
4. **Check Environment Variables** - Verify required env vars are set (check presence only, NEVER expose values)

**When Required prerequisites fail:**

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

**OpenShift MCP Server** (universally required):
- Source: https://github.com/openshift/openshift-mcp-server
- Required env var: `KUBECONFIG`
- Setup: Add to `.mcp.json`, set `KUBECONFIG`, restart Claude Code

## Common Prerequisites

All rh-ai-engineer skills share these baseline prerequisites. Individual skills reference this section instead of repeating them.

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster with Red Hat OpenShift AI operator installed
- For model serving skills (`/model-deploy`, `/serving-runtime-config`, `/debug-inference`): KServe model serving platform configured, model serving enabled on the target namespace (label: `opendatahub.io/dashboard: "true"`)
- For NIM runtime: NVIDIA GPU Operator and Node Feature Discovery (NFD) Operator installed

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

# Red Hat SRE Collection (rh-sre)

Site Reliability Engineering skills for CVE analysis, Ansible-based remediation, system inventory, and execution reporting. Integrates with Red Hat Lightspeed and Ansible Automation Platform (AAP) MCP servers.

- **Persona**: SRE
- **Marketplaces**: Claude Code, Cursor
- **Plugin version**: 1.0.0

## Prerequisites

### MCP Servers

Configure in `rh-sre/.mcp.json`. All servers use container isolation via Podman.

```json { .api }
{
  "mcpServers": {
    "lightspeed-mcp": {
      "command": "podman",
      "args": [
        "run", "--rm", "-i",
        "--env", "LIGHTSPEED_CLIENT_ID",
        "--env", "LIGHTSPEED_CLIENT_SECRET",
        "quay.io/redhat-services-prod/insights-management-tenant/insights-mcp/red-hat-lightspeed-mcp:latest"
      ],
      "env": {
        "LIGHTSPEED_CLIENT_ID": "${LIGHTSPEED_CLIENT_ID}",
        "LIGHTSPEED_CLIENT_SECRET": "${LIGHTSPEED_CLIENT_SECRET}"
      },
      "description": "Red Hat Lightspeed MCP for CVE data and remediation",
      "security": { "isolation": "container", "network": "local", "credentials": "env-only" }
    },
    "aap-mcp-job-management": {
      "type": "http",
      "url": "https://${AAP_MCP_SERVER}/job_management/mcp",
      "headers": { "Authorization": "Bearer ${AAP_API_TOKEN}" },
      "description": "AAP job management MCP server"
    },
    "aap-mcp-inventory-management": {
      "type": "http",
      "url": "https://${AAP_MCP_SERVER}/inventory_management/mcp",
      "headers": { "Authorization": "Bearer ${AAP_API_TOKEN}" },
      "description": "AAP inventory management MCP server"
    }
  }
}
```

### Environment Variables

| Variable | Required By | Description |
|----------|-------------|-------------|
| `LIGHTSPEED_CLIENT_ID` | lightspeed-mcp | Red Hat Lightspeed service account client ID |
| `LIGHTSPEED_CLIENT_SECRET` | lightspeed-mcp | Red Hat Lightspeed service account secret |
| `AAP_MCP_SERVER` | aap-mcp-* | AAP server hostname/IP |
| `AAP_API_TOKEN` | aap-mcp-* | AAP API authentication token |

## Capabilities

### /remediation — Full CVE Remediation Orchestration

The primary orchestrating skill for complete end-to-end CVE remediation. Invokes 7 sub-skills in sequence. Use this for all multi-step remediation workflows.

```markdown { .api }
Skill: remediation
Invocation: /remediation
Model: inherit
Color: (unset — critical/security)

Orchestration chain:
  1. /cve-impact          — Impact analysis
  2. /system-context      — System inventory
  3. /cve-validation      — CVE validation
  4. /playbook-generator  — Ansible playbook generation
  5. /job-template-creator (if needed) — AAP job template setup
  6. /playbook-executor   — Playbook execution via AAP
  7. /remediation-verifier — Verify remediation success

Use when:
- "Remediate CVE-YYYY-NNNNN"
- "Create and execute a playbook for CVE-X"
- "Patch CVE-X across all systems"
- Multi-step remediation workflows

NOT for: simple CVE listing (use /cve-impact instead)
```

**Example:**
```
User: "Remediate CVE-2024-1234 on my production systems"
Agent: Executes /remediation → runs full 7-step workflow with user confirmations
```

---

### /cve-impact — CVE Discovery and Risk Assessment

Primary skill for all CVE queries. DO NOT use raw Lightspeed MCP tools directly.

```markdown { .api }
Skill: cve-impact
Invocation: /cve-impact
Model: inherit
Color: (unset)

Workflow:
  Step -1: HITL pagination prompt (system-level queries ONLY — MUST be first reply)
  Step 0: Validate /mcp-lightspeed-validator
  Step 1: Choose flow:
    - Account-level (all devices): flows/01-account-cves.md
    - System-level all CVEs:       flows/02-system-all-cves.md
    - System-level remediatable:   flows/03-system-remediatable-cves.md
  Step 2: CVE Information Retrieval (specific CVE)
  Step 3: Affected Systems Identification
  Step 4: System Classification
  Step 5: Risk Assessment
  Step 6: Impact Analysis
  Step 7: Remediation Readiness Check

CRITICAL — system-level HITL: First reply MUST be pagination prompt, before
any MCP tool call. User chooses: first-page-only / all-pages / N-pages.

MCP tools used:
  - vulnerability__get_cves        — list CVEs by severity/filter
  - vulnerability__get_cve         — get specific CVE details
  - vulnerability__get_cve_systems — systems affected by CVE
  - vulnerability__get_system_cves — CVEs affecting a system (system_uuid ONLY)
  - inventory__find_host_by_name   — resolve hostname → system_uuid
  - inventory__get_host_details    — detailed system info

Use when: CVE discovery, listing, risk assessment, system-level CVE queries
NOT for: remediation actions (use /remediation)
```

**get_system_cves parameter note:**
- Use `system_uuid` parameter (NOT `system_id`)
- Does NOT support `impact`, `limit`, or severity filters — filter client-side
- Parse responses using `skills/cve-impact/references/01-cve-response-parser.py`

**Parser usage:**
```bash
# Single page
python3 rh-sre/skills/cve-impact/references/01-cve-response-parser.py response.json

# Multiple pages (merged, deduplicated)
python3 rh-sre/skills/cve-impact/references/01-cve-response-parser.py page1.json page2.json page3.json

# Environment filters
FILTER_REMEDIATABLE=1 python3 ... response.json
FILTER_IMPACT=Critical,Important python3 ... response.json
OUTPUT=report SYSTEM_NAME=hostname python3 ... page1.json page2.json
```

---

### /cve-validation — CVE ID Validation

Validates CVE identifiers and checks remediation availability before remediation planning.

```markdown { .api }
Skill: cve-validation
Invocation: /cve-validation
Model: inherit
Color: (unset)

Use when:
- Verify CVE exists and is valid
- Check severity before analysis
- Confirm automated remediation is available

NOT for: full remediation (use /remediation), simple listing (use /cve-impact)
```

---

### /playbook-generator — Ansible Playbook Generation

Generates production-ready Ansible remediation playbooks via Red Hat Lightspeed. Returns playbook AS-IS — do NOT modify without explicit user validation.

```markdown { .api }
Skill: playbook-generator
Invocation: /playbook-generator
Model: inherit
Color: (unset)

MCP tool: remediations__create_vuln_playbook (from lightspeed-mcp)

CRITICAL:
- This skill ONLY GENERATES playbooks. NOT executes.
- For execution: use /playbook-executor
- ALWAYS use this instead of calling create_vulnerability_playbook directly
- NEVER execute with ansible-playbook CLI
- NEVER modify generated playbook without explicit user validation
```

---

### /playbook-executor — Ansible Playbook Execution via AAP

Executes remediation playbooks via Ansible Automation Platform with job management, dry-run support, and reporting.

```markdown { .api }
Skill: playbook-executor
Invocation: /playbook-executor
Model: inherit
Color: (unset — critical)

Git Flow: If template playbook path ≠ generated playbook path,
  perform Git Flow (commit, push, sync) BEFORE launching the job.

Human-in-the-Loop: Required before any job execution.

MCP tools (aap-mcp-job-management):
  - job_templates_list           — list job templates
  - job_templates_retrieve       — get template details (fields: id, name, inventory, project, playbook, credentials)
  - job_templates_launch_retrieve — launch job (job_type: "check" for dry-run, "run" for execution)
  - jobs_retrieve                — get job status (poll every 2s)
  - jobs_stdout_retrieve         — get console output (format: "txt")
  - jobs_job_events_list         — get task events for live progress
  - jobs_job_host_summaries_list — get per-host statistics
  - jobs_relaunch_retrieve       — relaunch failed jobs (hosts: "failed")
  - projects_list                — list AAP projects

MCP tools (aap-mcp-inventory-management):
  - inventories_list             — list inventories
  - hosts_list                   — list inventory hosts

Prerequisite: /mcp-aap-validator, /job-template-remediation-validator
```

---

### /fleet-inventory — System Inventory

Queries and displays managed system inventory from Red Hat Lightspeed.

```markdown { .api }
Skill: fleet-inventory
Invocation: /fleet-inventory
Model: inherit
Color: (unset)

Use when:
- "Show the managed fleet"
- "List all systems registered in Lightspeed"
- "What systems are affected by CVE-X?"
- "How many RHEL 8 systems do we have?"

NOT for: remediation actions (use /remediation)
```

---

### /system-context — System Deployment Context

Gathers comprehensive system inventory and deployment context for CVE-affected systems.

```markdown { .api }
Skill: system-context
Invocation: /system-context
Model: inherit
Color: (unset)

Orchestrates: get_cve_systems + get_host_details MCP tools
Provides: RHEL version detection, environment classification (prod/staging/dev),
  deployment analysis, remediation strategy determination

ALWAYS use instead of calling get_cve_systems or get_host_details directly.
```

---

### /remediation-verifier — Post-Remediation Verification

Verifies CVE remediation success after playbook execution.

```markdown { .api }
Skill: remediation-verifier
Invocation: /remediation-verifier
Model: inherit
Color: (unset)

Orchestrates: get_cve + get_cve_systems + get_host_details MCP tools
Checks: CVE status, package version validation, service health

ALWAYS use instead of calling verification MCP tools directly.
```

---

### /mcp-lightspeed-validator — Lightspeed MCP Validator

Validates connectivity to Red Hat Lightspeed MCP server with a lightweight test call.

```markdown { .api }
Skill: mcp-lightspeed-validator
Invocation: /mcp-lightspeed-validator
Model: haiku
Color: yellow

Validation results:
  PASSED   — continue with operations
  PARTIAL  — warn user, ask to proceed
  FAILED   — stop, provide setup instructions

Validation freshness: Skip if already validated in current session.
```

---

### /mcp-aap-validator — AAP MCP Validator

Validates connectivity to AAP MCP servers.

```markdown { .api }
Skill: mcp-aap-validator
Invocation: /mcp-aap-validator
Model: haiku
Color: yellow

Tests both aap-mcp-job-management and aap-mcp-inventory-management connectivity.
```

---

### /job-template-creator — AAP Job Template Creation

Guides creating AAP job templates for playbook execution via AAP Web UI.

```markdown { .api }
Skill: job-template-creator
Invocation: /job-template-creator
Model: inherit
Color: blue

Use when: creating new job templates, adding playbooks to Git projects,
  configuring AAP for CVE remediation execution
```

---

### /job-template-remediation-validator — Job Template Validation

Verifies an AAP job template meets requirements for CVE remediation playbooks.

```markdown { .api }
Skill: job-template-remediation-validator
Invocation: /job-template-remediation-validator
Model: inherit
Color: (unset)

Use before /playbook-executor when selecting a job template.
NOT for: AAP connectivity (use /mcp-aap-validator), creating templates (use /job-template-creator)
```

---

### /execution-summary — Execution Report

Generates a report of agents, skills, tools, and documentation accessed during a workflow.

```markdown { .api }
Skill: execution-summary
Invocation: /execution-summary
Model: haiku
Color: blue

Use when: "generate execution summary", "summarize what was used",
  "show execution summary", "what agents/skills/tools were used"
```

## Lightspeed MCP Tool Reference

```python { .api }
# Vulnerability toolset (lightspeed-mcp)
vulnerability__get_cves(
    severity: list[str],   # e.g. ["Critical", "Important"]
    sort_by: str,          # e.g. "-cvss_score"
    limit: int             # 1-100
) -> list[dict]            # CVEs with CVSS, severity, affected systems count

vulnerability__get_cve(
    cve_id: str,           # format: "CVE-YYYY-NNNNN"
    include_details: bool  # True for complete metadata
) -> dict                  # CVSS vector, affected packages, references

vulnerability__get_cve_systems(
    cve_id: str,           # format: "CVE-YYYY-NNNNN"
    include_patched: bool  # False to exclude patched systems
) -> list[dict]            # Systems with UUID, hostname, package version

vulnerability__get_system_cves(
    system_uuid: str       # REQUIRED — NOT system_id
    # Does NOT support: impact, limit, severity filters — filter client-side
) -> list[dict]            # CVEs affecting the system

# Inventory toolset (lightspeed-mcp)
inventory__find_host_by_name(
    name: str              # hostname to resolve
) -> dict                  # system_uuid, hostname, IP, metadata

inventory__get_host_details(
    system_uuid: str
) -> dict                  # detailed system info, RHEL version, environment

# Remediation toolset (lightspeed-mcp)
remediations__create_vuln_playbook(
    cve_id: str            # CVE to remediate
    # Returns Ansible YAML playbook AS-IS
) -> str                   # Ansible playbook content
```

## AAP MCP Tool Reference

```python { .api }
# aap-mcp-job-management (HTTP MCP server)

job_templates_list(
    page_size: int  # e.g. 10
) -> dict           # paginated list of job templates

job_templates_retrieve(
    id: int         # template ID
) -> dict           # template fields: id, name, inventory, project, playbook,
                    # become_enabled, ask_variables_on_launch, ask_limit_on_launch,
                    # ask_inventory_on_launch, summary_fields, credentials

job_templates_launch_retrieve(
    id: int,
    requestBody: dict  # {
                       #   "job_type": "check",  # dry-run (check mode)
                       #               "run",    # actual execution
                       #   "extra_vars": dict,
                       #   "limit": str          # host limit pattern
                       # }
) -> dict              # launched job: id, status, job_type

jobs_retrieve(
    id: int         # job ID
) -> dict           # job status: id, status (pending/running/successful/failed)

jobs_stdout_retrieve(
    id: int,
    format: str     # "txt" for plain text output
) -> str            # full console output

jobs_job_events_list(
    id: int         # job ID
) -> list[dict]     # task events for live progress

jobs_job_host_summaries_list(
    id: int         # job ID
) -> list[dict]     # per-host statistics (ok, failed, skipped, unreachable counts)

jobs_relaunch_retrieve(
    id: int,
    requestBody: dict  # {"hosts": "failed", "job_type": "run"}
) -> dict              # new job

projects_list() -> dict  # paginated list of AAP projects

# aap-mcp-inventory-management (HTTP MCP server)

inventories_list() -> dict   # paginated list of inventories
hosts_list() -> dict         # paginated list of inventory hosts
```

## AI-Optimized Documentation (rh-sre)

The rh-sre pack includes a semantic indexing system for token-efficient document discovery:

```python { .api }
# docs/.ai-index/ structure:
# semantic-index.json       — document metadata with semantic keywords (~200 tokens to read)
# task-to-docs-mapping.json — pre-computed doc sets for common workflows
# cross-reference-graph.json — document relationship graph

# Recommended usage for AI agents reading rh-sre docs:
# 1. Read semantic-index.json first (~200 tokens)
# 2. Match task keywords to relevant docs
# 3. Load only required docs (progressive disclosure)
# 4. Follow cross-references for related content
# Performance: 29% token reduction, 85% reduction in navigation overhead

# Available documents in rh-sre/docs/:
#
# docs/ansible/
#   aap-job-execution.md          — AAP job execution reference: job templates, launch,
#                                    polling, stdout retrieval, dry-run (check mode)
#   cve-remediation-templates.md  — CVE remediation playbook templates and patterns
#   playbook-integration-aap.md   — Integration patterns for Ansible playbooks with AAP
#
# docs/insights/
#   vulnerability-logic.md        — Lightspeed CVE scoring logic, severity definitions,
#                                    CVSS interpretation for risk assessment
#
# docs/references/
#   cvss-scoring.md               — CVSS scoring reference: base/temporal/environmental metrics
#   lightspeed-mcp-parameters.md  — Complete parameter reference for all Lightspeed MCP tools
#   lightspeed-mcp-tool-failures.md — Common Lightspeed MCP tool failures and resolutions
#   skill-invocation.md           — Skill invocation patterns and orchestration reference
#
# docs/rhel/
#   package-management.md         — RHEL package management reference (dnf, rpm, subscription)
#
# docs/testing/
#   aap-integration-test-guide.md — AAP integration test guide for validating skill workflows
#
# docs/INDEX.md    — Navigation map and AI discovery guide for all rh-sre docs
# docs/SOURCES.md  — Official Red Hat documentation source attributions
```

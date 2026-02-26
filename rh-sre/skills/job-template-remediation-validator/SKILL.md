---
name: job-template-remediation-validator
description: |
  Verify an AAP job template meets requirements for executing CVE remediation playbooks.

  Use when:
  - "Does this job template support remediation playbooks?"
  - "Validate job template X for CVE remediation"
  - "Check if template is ready for playbook-executor"
  - Before playbook-executor selects a template

  NOT for: AAP MCP connectivity (use mcp-aap-validator), creating templates (use job-template-creator).
model: inherit
color: blue
---

# AAP Job Template Remediation Validator

This skill verifies that an AAP (Ansible Automation Platform) job template meets the requirements for executing CVE remediation playbooks as defined by the remediator agent and playbook-executor workflow.

## Prerequisites

**Required MCP Servers**: `aap-mcp-job-management`, `aap-mcp-inventory-management` ([setup guide](https://docs.redhat.com/))

**Required MCP Tools**:
- `job_templates_list` (from aap-mcp-job-management) - List job templates
- `job_templates_retrieve` (from aap-mcp-job-management) - Get template details
- `projects_list` (from aap-mcp-job-management) - Verify project exists and status
- `inventories_list` (from aap-mcp-inventory-management) - Verify inventory exists

**Required Environment Variables**:
- `AAP_MCP_SERVER` - Base URL for the MCP endpoint of the AAP server (must point to the AAP MCP gateway)
- `AAP_API_TOKEN` - AAP API authentication token

### Prerequisite Validation

**CRITICAL**: Before executing, invoke the [mcp-aap-validator](../mcp-aap-validator/SKILL.md) skill to verify AAP MCP server availability.

**Validation freshness**: Can skip if already validated in this session. See [Validation Freshness Policy](../mcp-aap-validator/SKILL.md#validation-freshness-policy).

**How to invoke**:
```
Use the Skill tool:
  skill: "mcp-aap-validator"
```

**Handle validation result**:
- **If validation PASSED**: Continue with template validation
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, provide setup instructions from validator

**Human Notification on Failure**:
If prerequisites are not met:
- ❌ "Cannot proceed: AAP MCP servers are not available"
- 📋 "Setup required: Configure AAP_MCP_SERVER and AAP_API_TOKEN environment variables"
- ❓ "How would you like to proceed? (setup now / skip / abort)"
- ⏸️ Wait for user decision

## When to Use This Skill

**Use this skill when**:
- Verifying a job template before playbook execution
- Checking if a template meets remediation requirements
- Auditing existing templates for remediation readiness
- Troubleshooting "template not compatible" in playbook-executor

**Do NOT use when**:
- Validating AAP MCP connectivity → Use `mcp-aap-validator` skill
- Creating new job templates → Use `job-template-creator` skill
- Executing playbooks → Use `playbook-executor` skill

## Remediation Template Requirements

This skill validates against the requirements documented in [playbook-executor](../playbook-executor/SKILL.md) and [job-template-creator](../job-template-creator/SKILL.md).

### Required (Must Pass)

| Requirement | Description | Validation |
|-------------|-------------|------------|
| **Inventory** | Template has inventory configured | `inventory` field present and non-null |
| **Project** | Template has project configured | `project` field present and non-null |
| **Playbook** | Template has playbook path | `playbook` field present, non-empty |
| **Credentials** | Machine credential (SSH) configured | `summary_fields.credentials` or `credentials` has at least one credential |
| **Privilege Escalation** | Required for package updates | `become_enabled` is true |

### Recommended (Warnings if Missing)

| Requirement | Description | Validation |
|-------------|-------------|------------|
| **Ask Variables on Launch** | Enables dynamic CVE targeting | `ask_variables_on_launch` is true |
| **Ask Limit on Launch** | Enables host targeting at launch | `ask_limit_on_launch` is true |

### Optional Context Checks

| Check | Description |
|-------|-------------|
| **Project Status** | Project exists and is synced (status "successful") |
| **Inventory Exists** | Inventory exists in AAP |
| **Playbook Path** | Path suggests remediation playbook (e.g., contains "remediation") |
| **Playbook Path Matching** | When used by playbook-executor (Scenario 3), the template's playbook path is trusted to match the playbook just created via job-template-creator |

## Workflow

### Phase 0: Validate AAP MCP Prerequisites

**Action**: Invoke the [mcp-aap-validator](../mcp-aap-validator/SKILL.md) skill

**Note**: Can skip if validation was performed earlier in this session and succeeded.

**Handle validation result**:
- **If validation PASSED**: Continue to Phase 1
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution

### Phase 1: Obtain Job Template

**Goal**: Get the job template to validate. User may provide template ID or name.

#### Option A: User Provides Template ID

If user specifies a template ID (e.g., "42" or "template 42"):

**MCP Tool**: `job_templates_retrieve` (from aap-mcp-job-management)

**Parameters**:
- `id`: Template ID as string (e.g., `"42"`)

**Expected Output**: Full job template object with fields: `id`, `name`, `inventory`, `project`, `playbook`, `become_enabled`, `ask_variables_on_launch`, `ask_limit_on_launch`, `summary_fields` (may include `credentials`), `credentials` (array of credential IDs)

**Error Handling**:
- If 404 or template not found: Report "Template ID X not found. Verify the ID exists in AAP."
- If connection error: Report per mcp-aap-validator troubleshooting

#### Option B: User Provides Template Name or No ID

If user says "validate my remediation template" or provides a name:

**MCP Tool**: `job_templates_list` (from aap-mcp-job-management)

**Parameters**:
- `page_size`: 50
- `search`: User-provided name or "remediation" (optional)

**Action**: List templates, let user select by number or ID. If exactly one match, use it. If multiple, present list and ask user to choose.

### Phase 2: Validate Required Fields

**Goal**: Check each required field against the template response.

**Input**: Template object from `job_templates_retrieve`

**Validation Logic**:

```
required_checks = []
required_checks.append(("Inventory", template.get("inventory") is not None and template.get("inventory") != ""))
required_checks.append(("Project", template.get("project") is not None and template.get("project") != ""))
required_checks.append(("Playbook", template.get("playbook") is not None and len(str(template.get("playbook", "")).strip()) > 0))
required_checks.append(("Privilege Escalation", template.get("become_enabled") == True))

# Credentials: AAP API may return credentials in summary_fields.credentials or credentials array
creds = template.get("summary_fields", {}).get("credentials") or template.get("credentials") or []
has_creds = (isinstance(creds, list) and len(creds) > 0) or (isinstance(creds, dict) and creds)
required_checks.append(("Credentials", has_creds))
```

**Note**: If the AAP MCP response structure differs, adapt the field paths. Common AAP API response structures:
- `inventory`: number (ID)
- `project`: number (ID)
- `playbook`: string (path)
- `become_enabled`: boolean
- `credentials`: array of credential IDs, or `summary_fields.credentials` array of objects with `id`, `name`

### Phase 3: Validate Recommended Fields

**Validation Logic**:

```
recommended_checks = []
recommended_checks.append(("Ask Variables on Launch", template.get("ask_variables_on_launch") == True))
recommended_checks.append(("Ask Limit on Launch", template.get("ask_limit_on_launch") == True))
```

### Phase 4: Optional Context Verification

**Goal**: Verify referenced project and inventory exist and are usable.

**Step 4.1: Verify Project Exists and Status**

**MCP Tool**: `projects_list` (from aap-mcp-job-management)

**Parameters**:
- `page_size`: 100
- `search`: Optional - filter by project ID if API supports it

**Action**: Search results for `id == template["project"]`. If found, check `status`:
- `"successful"`: ✓ Project synced, playbooks available
- `"failed"` or `"error"`: ⚠ Project sync failed - playbooks may be stale
- `"pending"` or `"running"`: ⚠ Project syncing - wait before use

**Step 4.2: Verify Inventory Exists**

**MCP Tool**: `inventories_list` (from aap-mcp-inventory-management)

**Parameters**:
- `page_size`: 100

**Action**: Search results for `id == template["inventory"]`. If found: ✓ Inventory exists. If not found: ⚠ Inventory ID not found (may be permission issue).

### Phase 5: Generate Validation Report

**Output Format**:

```markdown
# Job Template Remediation Validation Report

**Template**: {name} (ID: {id})
**Validated**: {timestamp}

## Required Checks
| Requirement | Status | Details |
|-------------|--------|---------|
| Inventory | ✓/✗ | {inventory_id} - {inventory_name or "configured"} |
| Project | ✓/✗ | {project_id} - {project_name or "configured"} |
| Playbook | ✓/✗ | {playbook_path} |
| Credentials | ✓/✗ | {count} credential(s) configured |
| Privilege Escalation | ✓/✗ | become_enabled: {value} |

## Recommended Checks
| Requirement | Status | Details |
|-------------|--------|---------|
| Ask Variables on Launch | ✓/⚠ | {value} |
| Ask Limit on Launch | ✓/⚠ | {value} |

## Context Verification
| Check | Status | Details |
|-------|--------|---------|
| Project Exists | ✓/⚠/✗ | {status} |
| Inventory Exists | ✓/⚠/✗ | {details} |

## Overall Result
{✓ PASSED / ⚠ PASSED WITH WARNINGS / ✗ FAILED}

{If PASSED}: Template is ready for remediation playbook execution.
{If WARNINGS}: Template works but consider enabling ask_variables_on_launch and ask_limit_on_launch for flexibility.
{If FAILED}: Fix required checks before using with playbook-executor. See job-template-creator for setup guidance.
```

### Pass/Fail Determination

- **PASSED**: All 5 required checks pass
- **PASSED WITH WARNINGS**: All required pass, one or more recommended fail
- **FAILED**: One or more required checks fail

## Dependencies

### Required MCP Servers
- `aap-mcp-job-management` - AAP job template and execution management
- `aap-mcp-inventory-management` - AAP inventory management

### Required MCP Tools
- `job_templates_list` (from aap-mcp-job-management) - List templates
- `job_templates_retrieve` (from aap-mcp-job-management) - Get template details
- `projects_list` (from aap-mcp-job-management) - Verify project
- `inventories_list` (from aap-mcp-inventory-management) - Verify inventory

### Related Skills
- `mcp-aap-validator` - **PREREQUISITE** - Validates AAP MCP before this skill
- `playbook-executor` - **PRIMARY USER** - Uses compatible templates for execution
- `job-template-creator` - Creates templates that this skill validates

### Reference Documentation
- [playbook-executor/SKILL.md](../playbook-executor/SKILL.md) - Template compatibility requirements (Phase 1 Step 1.2, Scenario 3 validation)
- [job-template-creator/SKILL.md](../job-template-creator/SKILL.md) - Template configuration for remediation
- [AAP Job Templates](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-job-templates)

## Example Usage

### Example 1: Validate Template by ID

**User Request**: "Validate job template 42 for remediation"

**Skill Response**:

1. Invoke mcp-aap-validator → PASSED
2. Call `job_templates_retrieve(id="42")` → Get template
3. Run validation checks
4. Call `projects_list`, `inventories_list` for context
5. Output report:

```
# Job Template Remediation Validation Report

**Template**: CVE Remediation Template (ID: 42)
**Validated**: 2025-02-25

## Required Checks
| Requirement | Status | Details |
|-------------|--------|---------|
| Inventory | ✓ | 1 - Production Inventory |
| Project | ✓ | 6 - Remediation Playbooks |
| Playbook | ✓ | playbooks/remediation/remediation-template.yml |
| Credentials | ✓ | 1 credential(s) configured |
| Privilege Escalation | ✓ | become_enabled: true |

## Recommended Checks
| Requirement | Status | Details |
|-------------|--------|---------|
| Ask Variables on Launch | ✓ | true |
| Ask Limit on Launch | ✓ | true |

## Overall Result
✓ PASSED

Template is ready for remediation playbook execution.
```

### Example 2: Template Fails - Missing Privilege Escalation

**User Request**: "Check if template 15 works for remediation"

**Skill Response**:

```
# Job Template Remediation Validation Report

**Template**: General Playbook Runner (ID: 15)
**Validated**: 2025-02-25

## Required Checks
| Requirement | Status | Details |
|-------------|--------|---------|
| Inventory | ✓ | 1 - Production Inventory |
| Project | ✓ | 6 - Remediation Playbooks |
| Playbook | ✓ | playbooks/example.yml |
| Credentials | ✓ | 1 credential(s) configured |
| Privilege Escalation | ✗ | become_enabled: false |

## Overall Result
✗ FAILED

Fix required: Enable privilege escalation (become) on this template.
Remediation playbooks require sudo/root for package updates and system changes.

To fix: AAP Web UI → Templates → [Template] → Edit → Options → ✓ Enable Privilege Escalation
```

### Example 3: Invoked by Playbook-Executor

**Context**: playbook-executor filters templates and may invoke this skill to validate user-selected template before execution.

**Workflow**:
```
[playbook-executor] → User selects template ID 10
[playbook-executor] → Invoke job-template-remediation-validator with template 10
[job-template-remediation-validator] → Returns PASSED
[playbook-executor] → Proceeds with execution
```

## Critical: Human-in-the-Loop Requirements

This skill performs **read-only validation** only. It does not modify AAP resources or execute playbooks.

**When user input is needed**:
- **Template selection**: If multiple templates match a search, present the list and ask user to select by number or ID before proceeding
- **Template not found**: If template ID invalid, report error and ask user for correct ID or "list" to see available templates

**No confirmation required** for validation execution - the skill only reads and reports.

## Best Practices

1. **Validate before execution** - Run this skill before playbook-executor when using a new or unfamiliar template
2. **Enable recommended options** - ask_variables_on_launch and ask_limit_on_launch improve flexibility
3. **Project sync** - Ensure project status is "successful" before execution
4. **Credential types** - Template should have Machine (SSH) credential; Vault optional for encrypted playbooks
5. **Naming convention** - Use descriptive names like "Remediate CVE-YYYY-NNNNN" for auditability

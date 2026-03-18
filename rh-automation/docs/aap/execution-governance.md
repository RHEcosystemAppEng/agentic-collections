---
title: Execution Governance
category: aap
sources:
  - title: "Red Hat AAP 2.5 - Job Templates"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-job-templates
    sections: "Ch. 9: Job template configuration, job_type (run/check), diff_mode, limit, extra_vars, job slicing"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Security Best Practices"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-security-best-practices
    sections: "Ch. 15: Sec. 15.1.4 Remove user access to credentials, Sec. 15.1.5 Enforce separation of duties"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Workflows"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-workflows
    sections: "Ch. 9: Workflow RBAC, approval nodes, failure handling"
    date_accessed: 2026-02-20
  - title: "Red Hat Ansible Best Practices - Check Mode"
    url: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_checkmode.html
    sections: "Check mode, diff mode, limitations with shell/command modules"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP Controller Best Practices"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-best-practices
    sections: "Inventory management, environment separation"
    date_accessed: 2026-02-20
tags: [execution, governance, check-mode, risk-classification, rollback, phased-rollout, extra-vars, secret-scanning]
applies_to: [aap2.5, aap2.6]
semantic_keywords:
  - "execute on production"
  - "check mode dry run"
  - "inventory risk classification"
  - "secret scanning extra_vars"
  - "rollback failed job"
  - "phased rollout"
  - "job template launch"
  - "diff mode"
  - "execution safety"
  - "production governance"
use_cases:
  - "governed_execution"
  - "risk_analysis"
  - "check_mode_execution"
  - "rollback"
related_docs:
  - "aap/governance-readiness.md"
  - "aap/job-troubleshooting.md"
  - "references/error-classification.md"
last_updated: 2026-02-26
---

# Execution Governance

This document teaches the agent how to execute governed jobs on Ansible Automation Platform. It covers inventory risk classification, pre-launch safety checks, check mode execution and interpretation, rollback patterns, and phased rollout strategies. Every governance control is rooted in Red Hat's official documentation.

## Overview

A governed execution follows a principle: **the higher the risk, the more governance controls apply**. Risk is determined by the target inventory, the scope of change, and the content of extra_vars. Governance controls range from simple confirmation (low risk) to mandatory check mode, approval gates, and phased rollout (critical risk).

## When to Use This Document

**Use when**:
- User asks to execute, launch, or run a job template
- User asks to push to production
- User asks about check mode or dry runs
- User asks about rollback after a failed execution

**Do NOT use when**:
- User asks to assess platform governance readiness (use [governance-readiness.md](governance-readiness.md))
- User asks to troubleshoot a failed job (use [job-troubleshooting.md](job-troubleshooting.md))

---

## Inventory Risk Classification

### Red Hat Source

> "It is best practice to use separate inventories for production and development environments."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Controller Best Practices*

### Classification Approach

Based on Red Hat's recommendation to separate production and development environments, this agent detects the environment from inventory metadata and applies proportional governance. This is the agent's contribution: translating Red Hat's principle into automated risk detection.

**Risk signals** (checked in order):

1. **Inventory name** (primary signal): Word-boundary matching against environment keywords
2. **Host count** (secondary signal): Large inventories carry higher blast radius
3. **Recent job history** (tertiary signal): Inventories with recent failures may need extra caution

### MCP Pattern: Inventory Lookup

```json
MCP Server: aap-mcp-inventory-management
Tool: inventories_list
Parameters: { "page_size": 100 }
```

To check host count for a specific inventory:

```json
MCP Server: aap-mcp-inventory-management
Tool: hosts_list
Parameters: { "page_size": 1, "search": "<inventory_name>" }
```

### Risk Decision Table

| Inventory Name Pattern | Host Count | Risk Level | Governance Required |
|---|---|---|---|
| Contains `prod`, `production`, `live` | Any | **CRITICAL** | Check mode + approval + phased rollout recommended |
| Contains `stage`, `staging`, `uat`, `preprod` | Any | **HIGH** | Check mode + approval |
| Contains `test`, `qa` | Any | **MEDIUM** | Confirmation only |
| Contains `dev`, `development`, `sandbox`, `lab` | Any | **LOW** | Direct execution permitted |
| No matching pattern | > 50 hosts | **HIGH** | Check mode + approval (large blast radius) |
| No matching pattern | <= 50 hosts | **MEDIUM** | Confirmation only |

**Transparency note**: The name-based risk patterns above are this agent's implementation of Red Hat's principle to "use separate inventories for production and development." The host count thresholds are the agent's contribution for unclassifiable inventories.

---

## Extra Vars Safety Scanning

### Red Hat Source

> "Remove user access to credentials. Credentials can be configured at the organization, team, or user level."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Ch. 15, Sec. 15.1.4*

### What This Means for Extra Vars

Red Hat's credential management system stores secrets securely within AAP. When users pass secrets directly in `extra_vars` (as plain-text strings), they bypass this protection -- the secret appears in job logs, activity stream, and API responses. The agent detects this anti-pattern.

### Detection Patterns

The agent scans `extra_vars` key names and values for indicators of plain-text secrets:

**Key name patterns** (case-insensitive): `password`, `secret`, `token`, `api_key`, `apikey`, `private_key`, `ssh_key`, `access_key`, `auth`

**Value patterns**: Strings that look like tokens (long alphanumeric strings, base64-encoded content, strings starting with common prefixes like `sk-`, `ghp_`, `Bearer`)

### MCP Pattern: Job Template Launch Parameters

Before launching, inspect the launch configuration:

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_launch_retrieve
Parameters: { "id": "<template_id>" }
```

This returns the template's expected extra_vars, defaults, and required fields.

### Decision Table

| Finding | Severity | Action |
|---|---|---|
| Secret-like key name with literal value in extra_vars | **BLOCK** | Refuse to launch. Recommend using AAP credentials instead. |
| Secret-like key name with variable reference (`{{ }}`) | **PASS** | Variable references are acceptable (resolved at runtime) |
| No secret indicators | **PASS** | Proceed with launch |

**Transparency note**: The secret detection patterns above are this agent's implementation of Red Hat's recommendation to "Remove user access to credentials" (Ch. 15, Sec. 15.1.4). The regex patterns are the agent's contribution; the principle is Red Hat's.

---

## Pre-Execution Context Analysis

Beyond static risk classification (inventory name, extra_vars), the agent SHOULD examine the job template's operational context -- its history, configuration, and governance bindings. These signals adapt the risk assessment to the specific scenario rather than relying solely on inventory name patterns.

### Red Hat Sources

> "You can set notifications on job start and job end, including job failure, for the following resources: job templates, workflow templates, organizations, and projects."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 25: Notifications*

> "Workflows enable you to configure a sequence of disparate job templates and link them together in order to execute them as a single unit."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 9: Workflows*

### Signal 1: Job History

Check whether this job template has recent failures:

```json
MCP Server: aap-mcp-job-management
Tool: jobs_list
Parameters: { "page_size": 5, "job_template": "<template_id>", "order_by": "-finished" }
```

| Recent Jobs | Last Runs Status | Signal | Agent Action |
|---|---|---|---|
| > 0 | All successful | **CLEAR** | Proceed normally |
| > 0 | Most recent failed | **WARN** | "This template's last run failed. Investigate before re-executing." |
| > 0 | 2+ consecutive failures | **ELEVATED** | "This template has failed [N] consecutive times. Strongly recommend investigating root cause before retrying." |
| 0 | N/A (never run) | **INFO** | "This template has never been executed. First run -- extra caution recommended." |

**Transparency note**: Job history analysis is the agent's proactive contribution. Red Hat does not prescribe checking history before launches, but the agent uses available MCP data to provide situational awareness that a vanilla agent would not.

### Signal 2: Template Launch Configuration

Check whether the template allows governance overrides at launch time:

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_launch_retrieve
Parameters: { "id": "<template_id>" }
```

Examine the `ask_*_on_launch` fields:

| Field | Value | Implication |
|---|---|---|
| `ask_job_type_on_launch` | `true` | Check mode override available -- governance can enforce dry-run |
| `ask_job_type_on_launch` | `false` | **Check mode not overridable at launch.** Agent cannot enforce dry-run without template modification. |
| `ask_limit_on_launch` | `true` | Phased rollout possible via `limit` parameter |
| `ask_limit_on_launch` | `false` | **Phased rollout not possible.** Agent cannot restrict hosts at launch. |
| `ask_variables_on_launch` | `true` | Extra vars can be overridden -- check for secret injection risk |
| `ask_diff_mode_on_launch` | `true` | Diff mode overridable -- governance can enable detailed change reporting |

**Agent Action**:
- If `ask_job_type_on_launch` is `false` AND risk is CRITICAL/HIGH: Warn user that check mode cannot be enforced. Recommend modifying the template to enable "Prompt on launch" for job_type.
- If `ask_limit_on_launch` is `false` AND risk is CRITICAL: Warn that phased rollout is not possible with this template configuration.

### Signal 3: Notification Bindings

Check whether the template has failure notifications:

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_retrieve
Parameters: { "id": "<template_id>" }
```

If the template shows no notification associations for error events:

**Agent Action**: "Per Red Hat's Notifications documentation (Ch. 25), this job template has no failure notification configured. If this execution fails, no one will be automatically alerted. Consider adding failure notifications before production use."

### Signal 4: Workflow Coverage

Check whether this template is wrapped in a governed workflow:

```json
MCP Server: aap-mcp-job-management
Tool: workflow_job_templates_list
Parameters: { "page_size": 100 }
```

If no workflows exist, or none reference this job template:

**Agent Action**: "Per Red Hat's Workflow documentation (Ch. 9), this job template runs standalone -- not wrapped in a workflow. Workflows provide approval nodes, failure paths, and conditional logic. For production executions, consider wrapping this template in a workflow."

### Signal 5: Previous Run Module Analysis

If job history exists, examine events from the most recent run to identify playbook characteristics that affect check mode coverage:

```json
MCP Server: aap-mcp-job-management
Tool: jobs_job_events_list
Parameters: { "id": "<most_recent_job_id>", "page_size": 50 }
```

Scan event task names and module types. If events show `ansible.builtin.shell` or `ansible.builtin.command` usage:

**Agent Action**: Elevate the check mode warning from generic to specific: "This playbook uses shell/command modules (found in previous run events). Check mode will SKIP these tasks -- they represent [X] of [Y] total tasks and will NOT be validated in the dry run."

### Adaptive Risk Enhancement

After collecting all signals, the agent adjusts the base risk assessment:

| Base Risk | Signals Found | Adjusted Risk | Rationale |
|---|---|---|---|
| CRITICAL | Recent failures + no notifications | CRITICAL (confirmed) | Maximum governance -- investigate failures first |
| HIGH | Never run + check mode not overridable | **CRITICAL** (elevated) | First run on template that can't enforce dry-run |
| MEDIUM | All clear + good history | MEDIUM (confirmed) | Standard governance appropriate |
| LOW | Recent failures | **MEDIUM** (elevated) | Dev environment but template is failing -- extra caution |
| Any | No notifications + production target | Risk + **advisory** | Flag missing notifications as a governance gap |

**Transparency note**: Risk elevation based on operational signals is the agent's proactive contribution. Red Hat's documentation establishes the governance principles; the agent applies them dynamically based on what it discovers about the specific execution scenario.

---

## Check Mode Execution

### Red Hat Source

> "Check mode is a way to run Ansible without making any changes on remote systems. Check mode can be useful for testing playbooks."
>
> -- *Ansible Playbook Guide: Check Mode*

> "The `job_type` field on a job template supports `run` and `check` modes."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 9: Job Templates*

### MCP Pattern: Launch in Check Mode

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_launch_create
Parameters: {
  "id": "<template_id>",
  "requestBody": {
    "job_type": "check",
    "diff_mode": true
  }
}
```

**Key parameters**:
- `job_type`: `"check"` -- runs playbook in check mode (no changes applied)
- `diff_mode`: `true` -- shows what would change (file diffs, package lists)

### Check Mode Limitations

Per Ansible documentation, check mode has important limitations the agent must be aware of:

| Module Category | Check Mode Behavior | Agent Guidance |
|---|---|---|
| `ansible.builtin.dnf` / `ansible.builtin.yum` | **Contacts repos, resolves dependencies, reports what would change** | Reliable for package operations |
| `ansible.builtin.service` / `ansible.builtin.systemd` | Reports what state changes would occur | Reliable |
| `ansible.builtin.copy` / `ansible.builtin.template` | Reports file changes with diff | Reliable |
| `ansible.builtin.shell` / `ansible.builtin.command` | **Skipped entirely** -- check mode cannot predict command output | Warn the user: "Tasks using shell/command modules were skipped in check mode and were NOT validated" |
| `ansible.builtin.raw` | Skipped in check mode | Same warning as shell/command |

### Interpreting Check Mode Results

After the check mode job completes, retrieve its events:

```json
MCP Server: aap-mcp-job-management
Tool: jobs_job_events_list
Parameters: { "id": "<check_mode_job_id>", "page_size": 100 }
```

And the host summary:

```json
MCP Server: aap-mcp-job-management
Tool: jobs_job_host_summaries_list
Parameters: { "id": "<check_mode_job_id>" }
```

**Interpretation guide**:

| Host Summary Field | Meaning | Action |
|---|---|---|
| `failures` > 0 | Tasks would fail if executed | **STOP** -- do not proceed to full run. Report failures. |
| `dark` > 0 | Hosts unreachable | **STOP** -- connectivity issue. Investigate before proceeding. |
| `changed` > 0, `failures` = 0 | Changes would be applied successfully | Safe to proceed with approval |
| `ok` > 0, `changed` = 0 | No changes needed (idempotent) | Report: "Playbook is already in desired state" |
| `skipped` > 0 | Tasks were skipped (conditions not met or check mode limitation) | Warn about check mode limitations for skipped tasks |

### Pitfalls

- **Don't trust check mode blindly**: Shell/command tasks are skipped. If the playbook relies heavily on shell commands, check mode provides incomplete coverage. Warn the user.
- **Don't skip check mode for CRITICAL risk**: Even if the user says "urgent," CRITICAL-risk executions should always get a check mode pass per governance policy.
- **Don't forget diff_mode**: Always set `diff_mode: true` when running check mode. Without it, you see pass/fail but not *what* would change.

---

## Full Execution

### MCP Pattern: Launch with Full Run

After check mode passes and user approves:

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_launch_create
Parameters: {
  "id": "<template_id>",
  "requestBody": {
    "job_type": "run",
    "extra_vars": { ... },
    "limit": "<optional_host_limit>"
  }
}
```

### Monitoring Job Progress

Poll job status until completion:

```json
MCP Server: aap-mcp-job-management
Tool: jobs_retrieve
Parameters: { "id": "<job_id>" }
```

**Status values**: `pending`, `waiting`, `running`, `successful`, `failed`, `error`, `canceled`

### Post-Execution Summary

After completion, retrieve the changed-only summary:

```json
MCP Server: aap-mcp-job-management
Tool: jobs_job_host_summaries_list
Parameters: { "id": "<job_id>" }
```

Report only hosts with `changed > 0` or `failures > 0` to keep the summary actionable.

---

## Rollback Patterns

### Red Hat Source

> "You can relaunch a job with the same parameters, or relaunch on only failed hosts."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 9: Job Templates (Relaunch)*

### MCP Pattern: Relaunch on Failed Hosts

```json
MCP Server: aap-mcp-job-management
Tool: jobs_relaunch_create
Parameters: {
  "id": "<failed_job_id>",
  "requestBody": {
    "hosts": "failed",
    "credential_passwords": {}
  }
}
```

### Rollback Strategies

| Strategy | When to Use | MCP Pattern |
|---|---|---|
| **Relaunch on failed hosts** | Partial failure; retry the same playbook on hosts that failed | `jobs_relaunch_create` with `hosts: "failed"` |
| **Rollback playbook** | Full rollback needed; separate playbook that undoes changes | Launch a different job template (the rollback template) |
| **Revert to previous job** | Re-run the last successful job with same parameters | `jobs_relaunch_create` on the previous successful job ID |

### Pitfalls

- **Don't relaunch blindly**: If check mode caught a failure, relaunching the same playbook on failed hosts will produce the same failure. Fix the root cause first.
- **Don't assume idempotent rollback**: Not all playbooks have rollback versions. If no rollback template exists, manual intervention may be required.

---

## Phased Rollout

### Red Hat Source

> "The `limit` field can be used to restrict the hosts that the job template runs against."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 9: Job Templates*

> "Job slicing enables you to distribute work across multiple Ansible controller nodes."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 9: Job Templates (Job Slicing)*

### Phased Rollout Pattern

For CRITICAL-risk executions targeting many hosts, roll out in phases:

**Phase 1**: Canary -- single host or small group

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_launch_create
Parameters: {
  "id": "<template_id>",
  "requestBody": {
    "job_type": "run",
    "limit": "<canary_host>"
  }
}
```

**Phase 2**: Verify canary success, then expand to 25%

```json
Parameters: {
  "id": "<template_id>",
  "requestBody": {
    "job_type": "run",
    "limit": "<group_name>[0:25%]"
  }
}
```

**Phase 3**: Full rollout after canary + 25% pass

```json
Parameters: {
  "id": "<template_id>",
  "requestBody": {
    "job_type": "run"
  }
}
```

### Health Gate Between Phases

Between each phase, check the job result:

```json
MCP Server: aap-mcp-job-management
Tool: jobs_job_host_summaries_list
Parameters: { "id": "<phase_job_id>" }
```

If `failures > 0` on any host, **STOP the rollout** and report. Do not proceed to the next phase.

### Pitfalls

- **Don't skip the canary**: Even if the user says "execute on all," CRITICAL-risk executions should validate on a canary first.
- **Don't use limit patterns without verifying**: The Ansible `limit` syntax supports patterns (`host1,host2`, `group[0:5]`, `~regex`). Verify the pattern resolves to expected hosts before launching.

---

## Governance Workflow Summary

The complete governed execution workflow:

```
1. IDENTIFY the job template and target inventory
2. CLASSIFY inventory risk (CRITICAL / HIGH / MEDIUM / LOW)
3. SCAN extra_vars for plain-text secrets
4. IF CRITICAL/HIGH risk:
   a. LAUNCH in check mode with diff_mode=true
   b. INTERPRET check mode results
   c. WARN about shell/command limitations
   d. PRESENT findings and ASK for approval
5. IF approved:
   a. IF CRITICAL risk: Execute phased rollout (canary → 25% → full)
   b. IF HIGH risk: Execute full run
   c. Between phases: Verify host summaries (health gate)
6. REPORT changed-only summary
7. IF failure: Offer rollback options
```

---

## Cross-References

- **[governance-readiness.md](governance-readiness.md)** -- Assess platform readiness before first production execution
- **[job-troubleshooting.md](job-troubleshooting.md)** -- If execution fails, use forensic troubleshooting to determine root cause
- **[error-classification.md](../references/error-classification.md)** -- Classify execution errors and determine resolution paths

---

## Official Red Hat Sources

1. Red Hat AAP 2.5, Automation Controller User Guide -- Job Templates (Ch. 9). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-job-templates. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

2. Red Hat AAP 2.5, Configuring Automation Execution -- Security Best Practices (Ch. 15). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-security-best-practices. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

3. Red Hat AAP 2.5, Automation Controller User Guide -- Workflows (Ch. 9). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-workflows. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

4. Red Hat AAP 2.5, Configuring Automation Execution -- Controller Best Practices. https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-best-practices. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

5. Ansible Playbook Guide -- Check Mode. https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_checkmode.html. Accessed 2026-02-20.

---

## Quick Reference

| Governance Control | When Applied | MCP Tool | Key Parameter |
|---|---|---|---|
| Risk Classification | All executions | `inventories_list` | Inventory name + host count |
| Secret Scanning | All executions | `job_templates_launch_retrieve` | extra_vars inspection |
| Check Mode | CRITICAL + HIGH risk | `job_templates_launch_create` | `job_type: "check"`, `diff_mode: true` |
| Approval Gate | CRITICAL + HIGH risk | N/A (human-in-the-loop) | User confirmation |
| Phased Rollout | CRITICAL risk | `job_templates_launch_create` | `limit` parameter per phase |
| Health Gate | Between phases | `jobs_job_host_summaries_list` | `failures` = 0 to proceed |
| Rollback | On failure | `jobs_relaunch_create` | `hosts: "failed"` |
| Changed-Only Summary | Post-execution | `jobs_job_host_summaries_list` | Filter `changed > 0` |

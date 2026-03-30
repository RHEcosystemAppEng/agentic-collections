---
title: Job Troubleshooting
category: aap
sources:
  - title: "Red Hat AAP 2.6 - Troubleshooting Guide (Jobs)"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/troubleshooting_ansible_automation_platform/troubleshoot-jobs
    sections: "Job failure analysis, common job errors, event interpretation"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Job Events"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-job-templates
    sections: "Job events, host summaries, job stdout"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Configuring Automation Execution"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution
    sections: "Instance capacity, job scheduling, execution environment troubleshooting"
    date_accessed: 2026-02-20
tags: [troubleshooting, job-failure, events, host-facts, correlation, forensic-analysis, error-patterns]
applies_to: [aap2.5, aap2.6]
semantic_keywords:
  - "job failed"
  - "why did the job fail"
  - "analyze failure"
  - "job events"
  - "host unreachable"
  - "module failure"
  - "error analysis"
  - "root cause"
  - "failure correlation"
use_cases:
  - "job_failure_analysis"
  - "forensic_troubleshooting"
  - "host_correlation"
related_docs:
  - "aap/execution-governance.md"
  - "aap/governance-readiness.md"
  - "references/error-classification.md"
last_updated: 2026-02-26
---

# Job Troubleshooting

This document teaches the agent how to perform forensic analysis of failed AAP jobs. It covers event extraction and parsing, failure pattern recognition, host fact correlation, and root cause determination. Every analysis technique maps to MCP tools with exact parameters and is backed by Red Hat's official troubleshooting guidance.

## Overview

When an AAP job fails, the raw information exists in three places: **job events** (what happened, step by step), **host summaries** (which hosts failed), and **host facts** (system state of failed hosts). The agent's value is correlating these three data sources to determine root cause and classify the failure type.

## When to Use This Document

**Use when**:
- User reports a failed job: "Job #X failed"
- User asks why an execution failed
- User asks to analyze job errors
- As part of the forensic-troubleshooter agent workflow

**Do NOT use when**:
- User wants to execute a job (use [execution-governance.md](execution-governance.md))
- User wants to assess platform readiness (use [governance-readiness.md](governance-readiness.md))
- User needs error classification taxonomy (use [error-classification.md](../references/error-classification.md) as companion reference)

---

## Step 1: Job Status Retrieval

### Red Hat Source

> "The job detail page shows the status, timing, and results of a job execution."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 9*

### MCP Pattern

```json
MCP Server: aap-mcp-job-management
Tool: jobs_retrieve
Parameters: { "id": "<job_id>" }
```

**Key fields to extract**:
- `status`: `"failed"`, `"error"`, `"canceled"` -- determines analysis path
- `failed`: boolean -- confirms failure
- `job_type`: `"run"` or `"check"` -- check mode failures need different interpretation
- `elapsed`: execution time in seconds
- `launch_type`: `"manual"`, `"schedule"`, `"workflow"` -- context for how the job was triggered

### Status Interpretation

| Status | Meaning | Analysis Path |
|---|---|---|
| `failed` | Playbook execution completed but one or more tasks failed | Analyze job events for `runner_on_failed` events |
| `error` | Platform error prevented job execution | Check instance capacity, EE availability, credential validity |
| `canceled` | Job was canceled by user or timeout | Check if timeout was configured; may indicate hung task |

---

## Step 2: Failure Event Extraction

### Red Hat Source

> "Troubleshooting a failed job in automation controller involves examining the job's event stream to identify which task failed and on which host."
>
> -- *Red Hat AAP 2.6, Troubleshooting Ansible Automation Platform, Troubleshoot Jobs*

### MCP Pattern

```json
MCP Server: aap-mcp-job-management
Tool: jobs_job_events_list
Parameters: {
  "id": "<job_id>",
  "page_size": 100
}
```

### Event Filtering Strategy

Job events contain the full execution trace. For failure analysis, focus on these event types:

| Event Field (`event`) | Meaning | Priority |
|---|---|---|
| `runner_on_failed` | A task failed on a host | **PRIMARY** -- the actual failure |
| `runner_on_unreachable` | A host was unreachable | **PRIMARY** -- connectivity failure |
| `runner_on_skipped` | A task was skipped | SECONDARY -- may indicate conditional logic bypass |
| `playbook_on_stats` | Final play recap | SUMMARY -- aggregate success/failure counts |
| `runner_on_ok` | A task succeeded | CONTEXT -- useful for timeline reconstruction |

### Extracting Failure Details

From each `runner_on_failed` or `runner_on_unreachable` event, extract:

- `host`: Which host failed
- `task`: Which task failed
- `event_data.res.msg`: The error message
- `event_data.res.module_name` or `event_data.task_action`: Which Ansible module was involved
- `event_data.res.rc`: Return code (for command/shell modules)
- `counter`: Event sequence number (for timeline)

### Failure Timeline Reconstruction

Sort events by `counter` to reconstruct the failure sequence:

1. Identify the FIRST failure event (lowest counter among `runner_on_failed`/`runner_on_unreachable`)
2. Check if subsequent tasks were affected (cascade failures)
3. Note the task name and module of the first failure -- this is usually the root cause

---

## Step 3: Host Summary Analysis

### MCP Pattern

```json
MCP Server: aap-mcp-job-management
Tool: jobs_job_host_summaries_list
Parameters: { "id": "<job_id>" }
```

### Interpreting Host Summaries

| Field | Meaning | Forensic Value |
|---|---|---|
| `ok` | Tasks that succeeded | Baseline -- how far the playbook got before failure |
| `changed` | Tasks that made changes | Shows what was already modified before failure (important for rollback) |
| `failures` | Tasks that failed | Core failure count |
| `dark` | Host unreachable events | Indicates connectivity/platform issue, not code issue |
| `skipped` | Tasks skipped | May indicate handler or conditional logic issues |
| `processed` | Total tasks processed | Indicates whether failure was early or late in execution |

### Correlation Pattern

| dark > 0 | failures > 0 | Classification |
|---|---|---|
| Yes | No | **Platform issue**: Host connectivity problem |
| No | Yes | **Code/Config issue**: Playbook task failure |
| Yes | Yes | **Mixed**: Some hosts unreachable, others had task failures |
| No | No | Investigate: job may have `error` status (platform-level failure) |

---

## Step 4: Host Fact Correlation

### Red Hat Source

> "Host facts gathered by Ansible (via setup/gather_facts) can provide system state information useful for troubleshooting failures."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide*

### MCP Pattern

First, retrieve host details to get the host ID:

```json
MCP Server: aap-mcp-inventory-management
Tool: hosts_list
Parameters: { "search": "<hostname_from_failure_event>" }
```

Then retrieve host variables (which may include cached facts):

```json
MCP Server: aap-mcp-inventory-management
Tool: hosts_variable_data_retrieve
Parameters: { "id": "<host_id>", "format": "json" }
```

### Host Fact Correlation Table

When a failure is identified, correlate the error with host facts to determine if the host's system state contributed:

| Error Pattern | Host Fact to Check | Likely Cause |
|---|---|---|
| "No space left on device" | `ansible_mounts[].size_available` | Disk full on target host |
| "Unable to start service" | `ansible_service_mgr` | Service manager mismatch (systemd vs sysvinit) |
| Package not found / install failure | `ansible_distribution`, `ansible_distribution_version` | Wrong OS version; package not in repos |
| "Permission denied" | `ansible_user_id`, `ansible_become` | Privilege escalation not configured |
| "Connection timed out" | `ansible_default_ipv4` | Network configuration issue |
| "No matching host" / "Name resolution failure" | `ansible_fqdn`, `ansible_hostname` | DNS resolution problem |
| "Module not found" | Host's Python version (`ansible_python_version`) | Missing Python dependency on host |
| Out of memory / OOM killed | `ansible_memtotal_mb`, `ansible_memfree_mb` | Insufficient memory |

### Pitfalls

- **Don't assume host facts are current**: Cached facts may be stale. If facts were gathered during a previous job run, they reflect the state at that time, not necessarily now.
- **Don't skip host correlation for "obvious" errors**: Even a simple "package not found" may have a root cause in the host's OS version or repo configuration.

---

## Step 5: Job Stdout (Supplementary)

For detailed output when event data is insufficient:

### MCP Pattern

```json
MCP Server: aap-mcp-job-management
Tool: jobs_stdout_retrieve
Parameters: { "id": "<job_id>", "format": "txt" }
```

**When to use**: When event data doesn't contain enough detail (e.g., `runner_on_failed` without a clear `msg`). The stdout contains the full Ansible output including verbose error messages.

**Supported formats**: `ansi` (colored), `txt` (plain text), `json` (structured), `html` (rendered)

---

## Failure Patterns Reference

### Pattern 1: Host Unreachable

**Red Hat Source**: *AAP 2.6 Troubleshooting Guide* -- "If the job shows hosts as 'dark' (unreachable), verify network connectivity and SSH configuration."

**Event signature**: `event: "runner_on_unreachable"`

**Common causes**:
- SSH port blocked by firewall
- Host is down or rebooting
- DNS resolution failure
- SSH key mismatch (credential issue)

**Correlation**: Check `ansible_default_ipv4` from host facts to verify network configuration.

### Pattern 2: Module Failure (Package Operations)

**Event signature**: `event: "runner_on_failed"`, `task_action: "ansible.builtin.dnf"` or `ansible.builtin.yum"`

**Common causes**:
- Package not available in configured repos
- Repository connectivity issue
- Dependency conflict
- Disk space insufficient for package

**Correlation**: Check `ansible_distribution` and `ansible_distribution_version` to verify OS compatibility.

### Pattern 3: Privilege Escalation Timeout

**Red Hat Source**: *AAP 2.6 Troubleshooting Guide* -- "Privilege escalation timeouts can occur when sudo requires a password or when the become method is misconfigured."

**Event signature**: `event: "runner_on_failed"`, `msg` contains "Timeout" and "privilege escalation"

**Common causes**:
- `become: true` without passwordless sudo configured
- sudo requiring TTY (`requiretty` in sudoers)
- Become method mismatch (sudo vs su vs pbrun)

**Correlation**: Check `ansible_become` and `ansible_user_id` from host facts.

### Pattern 4: Service Start Failure

**Event signature**: `event: "runner_on_failed"`, `task_action: "ansible.builtin.service"` or `"ansible.builtin.systemd"`

**Common causes**:
- Service configuration error (bad config file)
- Port already in use
- Dependency service not running
- SELinux context preventing service start

**Correlation**: Check `ansible_service_mgr` to verify service manager compatibility.

### Pattern 5: Template Rendering Error

**Event signature**: `event: "runner_on_failed"`, `msg` contains "AnsibleUndefinedVariable" or "template error"

**Common causes**:
- Variable not defined in inventory or extra_vars
- Jinja2 syntax error in template
- Variable scope issue (host vs group vs play)

**Correlation**: Check `hosts_variable_data_retrieve` for the host to see what variables are defined.

### Pattern 6: Execution Environment Issue

**Event signature**: Job `status: "error"` (not `"failed"` -- platform-level), error mentions EE or container

**Common causes**:
- EE image not accessible (registry auth failure)
- EE missing required collection
- EE Python version incompatible with playbook

**Correlation**: Check `execution_environments_list` from configuration MCP server.

---

## Root Cause Classification Output Template

The agent MUST produce a structured root cause analysis:

```
## Job Failure Analysis: Job #[job_id]

**Job Status**: [status]
**Elapsed Time**: [elapsed]s
**Launch Type**: [launch_type]

### Failure Timeline

1. [timestamp/counter] - Task "[task_name]" on host "[hostname]": [event_type]
   Error: "[error_message]"
2. [subsequent events if cascade]

### Host Summary

| Host | OK | Changed | Failed | Unreachable |
|---|---|---|---|---|
| [host1] | [ok] | [changed] | [failures] | [dark] |

### Root Cause Classification

**Classification**: [Platform / Code / Configuration] Issue
**Evidence**: Per Red Hat's Troubleshooting Guide: "[relevant guidance]"

**Error Pattern**: [Pattern name from Failure Patterns Reference]
**Root Cause**: [Specific determination]

### Host Fact Correlation

Consulted host facts for [hostname]:
- [relevant fact]: [value] → [correlation finding]

### Recommended Resolution

Per [Red Hat source]: [resolution recommendation]

See [error-classification.md](../references/error-classification.md) for detailed resolution paths.
```

---

## Cross-References

- **[execution-governance.md](execution-governance.md)** -- For rollback options after determining root cause
- **[governance-readiness.md](governance-readiness.md)** -- Platform configuration issues may indicate governance gaps
- **[error-classification.md](../references/error-classification.md)** -- Detailed error taxonomy and resolution path mapping

---

## Official Red Hat Sources

1. Red Hat AAP 2.6, Troubleshooting Ansible Automation Platform -- Troubleshoot Jobs. https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/troubleshooting_ansible_automation_platform/troubleshoot-jobs. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

2. Red Hat AAP 2.5, Automation Controller User Guide -- Job Templates (Ch. 9). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/automation_controller_user_guide/controller-job-templates. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

3. Red Hat AAP 2.5, Configuring Automation Execution. https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

---

## Quick Reference

| Analysis Step | MCP Server | Tool | Key Parameters |
|---|---|---|---|
| Job status | job-management | `jobs_retrieve` | `id` |
| Failure events | job-management | `jobs_job_events_list` | `id`, `page_size: 100` |
| Host summaries | job-management | `jobs_job_host_summaries_list` | `id` |
| Full stdout | job-management | `jobs_stdout_retrieve` | `id`, `format: "txt"` |
| Host lookup | inventory-management | `hosts_list` | `search: "<hostname>"` |
| Host facts | inventory-management | `hosts_variable_data_retrieve` | `id`, `format: "json"` |
| EE check | configuration | `execution_environments_list` | `page_size: 100` |

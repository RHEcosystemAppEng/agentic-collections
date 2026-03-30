---
title: Error Classification Taxonomy
category: references
sources:
  - title: "Red Hat AAP 2.6 - Troubleshooting Guide"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/troubleshooting_ansible_automation_platform/troubleshoot-jobs
    sections: "Job failure types, common error patterns, resolution approaches"
    date_accessed: 2026-02-20
  - title: "Ansible Module Documentation"
    url: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html
    sections: "Module return values, error conditions, check mode behavior"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Configuring Automation Execution"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution
    sections: "Platform errors, capacity issues, execution environment troubleshooting"
    date_accessed: 2026-02-20
tags: [error-classification, taxonomy, platform-errors, code-errors, configuration-errors, resolution-paths]
applies_to: [aap2.5, aap2.6]
semantic_keywords:
  - "error classification"
  - "platform vs code error"
  - "resolution path"
  - "error taxonomy"
  - "failure type determination"
  - "troubleshooting decision tree"
use_cases:
  - "error_classification"
  - "resolution_path_determination"
related_docs:
  - "aap/job-troubleshooting.md"
  - "aap/execution-governance.md"
last_updated: 2026-02-26
---

# Error Classification Taxonomy

This document teaches the agent a systematic framework for classifying AAP job errors into three categories -- **Platform**, **Code**, and **Configuration** -- and mapping each to a resolution path. The classification determines who needs to act (platform admin, playbook developer, or ops engineer) and what Red Hat documentation to reference.

## Overview

Not all job failures are the same. A host connectivity issue requires platform investigation. A bad Jinja2 variable requires playbook code fixes. A privilege escalation timeout requires configuration changes. Classifying the error correctly is the first step to efficient resolution.

## When to Use This Document

**Use when**:
- After analyzing job events (companion to [job-troubleshooting.md](../aap/job-troubleshooting.md))
- When the resolution-advisor skill needs to determine resolution paths
- When classifying errors for the execution summary report

**Do NOT use when**:
- For initial event extraction (use [job-troubleshooting.md](../aap/job-troubleshooting.md) first)
- For execution decisions (use [execution-governance.md](../aap/execution-governance.md))

---

## Classification Decision Tree

```
Job Status?
├── "error" → PLATFORM ERROR (job never executed)
│   ├── EE not found → EE Configuration Issue
│   ├── Capacity exceeded → Instance Capacity Issue
│   └── Credential invalid → Credential Configuration Issue
│
├── "failed" → Examine event types
│   ├── runner_on_unreachable → PLATFORM ERROR
│   │   ├── SSH timeout → Network/Firewall Issue
│   │   ├── DNS failure → DNS Configuration Issue
│   │   └── Auth rejected → SSH Key/Credential Issue
│   │
│   ├── runner_on_failed → Examine module and message
│   │   ├── Module: dnf/yum/apt
│   │   │   ├── "No package matching" → CODE ERROR (wrong package name)
│   │   │   └── "Failed to download" → PLATFORM ERROR (repo access)
│   │   │
│   │   ├── Module: service/systemd
│   │   │   ├── "Could not find" → CODE ERROR (wrong service name)
│   │   │   └── "Failed to start" → CONFIGURATION ERROR (service config)
│   │   │
│   │   ├── Module: copy/template
│   │   │   ├── "AnsibleUndefinedVariable" → CODE ERROR (missing variable)
│   │   │   └── "Permission denied" → CONFIGURATION ERROR (file perms)
│   │   │
│   │   ├── Module: shell/command
│   │   │   ├── rc != 0 → CODE ERROR (script failure)
│   │   │   └── "Timeout" → CONFIGURATION ERROR (command timeout)
│   │   │
│   │   └── Message contains "privilege escalation"
│   │       └── CONFIGURATION ERROR (sudo/become)
│   │
│   └── runner_on_skipped (all tasks) → CODE ERROR (conditional logic)
│
└── "canceled" → Check timeout settings
    ├── Timeout configured and hit → CONFIGURATION ERROR
    └── Manual cancellation → Not an error
```

---

## Category 1: Platform Errors

### Definition

Errors caused by infrastructure, network, or AAP platform state -- not by the playbook code itself. Resolution requires platform admin action.

### Red Hat Source

> "If a job fails immediately or shows all hosts as unreachable, check the automation controller's capacity and the network connectivity to managed hosts."
>
> -- *Red Hat AAP 2.6, Troubleshooting Ansible Automation Platform*

### Error Patterns

#### 1a. Host Unreachable (SSH)

| Field | Pattern |
|---|---|
| Event | `runner_on_unreachable` |
| Message | Contains "Connection timed out", "Connection refused", "No route to host" |
| Host Summary | `dark > 0` |

**Resolution path**: Network/infrastructure team. Check firewall rules, SSH daemon status, host availability.

**Red Hat reference**: AAP 2.6 Troubleshooting Guide -- "Verify network connectivity and SSH configuration."

#### 1b. DNS Resolution Failure

| Field | Pattern |
|---|---|
| Event | `runner_on_unreachable` |
| Message | Contains "Name or service not known", "Could not resolve hostname" |

**Resolution path**: DNS/infrastructure team. Verify DNS records and resolution from controller nodes.

#### 1c. Execution Environment Unavailable

| Field | Pattern |
|---|---|
| Job Status | `error` (not `failed`) |
| Message | Contains "EE", "execution environment", "image pull", "container" |

**Resolution path**: Platform admin. Verify EE image accessibility, registry authentication, and EE configuration in AAP.

**Red Hat reference**: AAP 2.6, Creating and Consuming Execution Environments -- verify image registry access.

#### 1d. Instance Capacity Exhaustion

| Field | Pattern |
|---|---|
| Job Status | `error` or long `pending`/`waiting` |
| Message | Contains "capacity", "no available instances" |

**Resolution path**: Platform admin. Scale instance groups or reduce concurrent job load.

**Red Hat reference**: AAP 2.5, Instance Groups (Ch. 17) -- "Configure instance groups with appropriate capacity."

---

## Category 2: Code Errors

### Definition

Errors caused by playbook logic, module usage, or variable definitions. Resolution requires playbook developer action.

### Red Hat Source

> "Module failures typically indicate an issue with the playbook task definition, such as an incorrect module parameter, missing variable, or logic error."
>
> -- *Red Hat AAP 2.6, Troubleshooting Ansible Automation Platform*

### Error Patterns

#### 2a. Undefined Variable

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Message | Contains "AnsibleUndefinedVariable", "'{{ variable }}' is undefined" |
| Module | `ansible.builtin.template`, `ansible.builtin.debug`, or any task using variables |

**Resolution path**: Playbook developer. Define the variable in inventory vars, group vars, extra_vars, or role defaults.

#### 2b. Wrong Package Name

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Module | `ansible.builtin.dnf`, `ansible.builtin.yum` |
| Message | Contains "No package matching", "No match for argument" |

**Resolution path**: Playbook developer. Verify package name for the target OS distribution and version.

**Host fact correlation**: Check `ansible_distribution` and `ansible_distribution_version` -- package names differ between RHEL 8 and RHEL 9.

#### 2c. Syntax / Logic Error

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Message | Contains "Syntax Error", "template error", "unexpected token" |

**Resolution path**: Playbook developer. Fix Jinja2 syntax, YAML formatting, or task logic.

#### 2d. Script Failure (shell/command)

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Module | `ansible.builtin.shell`, `ansible.builtin.command` |
| `rc` | Non-zero return code |

**Resolution path**: Playbook developer. Debug the shell script/command. Check `stdout` and `stderr` in the event data.

#### 2e. Wrong Service Name

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Module | `ansible.builtin.service`, `ansible.builtin.systemd` |
| Message | Contains "Could not find the requested service" |

**Resolution path**: Playbook developer. Verify service name is correct for the target OS.

---

## Category 3: Configuration Errors

### Definition

Errors caused by mismatches between the playbook's expectations and the target system's configuration. The playbook logic may be correct, but the environment isn't set up to support it. Resolution requires ops/config team action.

### Error Patterns

#### 3a. Privilege Escalation Failure

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Message | Contains "Missing sudo password", "privilege escalation", "Timeout" with "become" |

**Resolution path**: Ops team. Configure passwordless sudo for the Ansible service account, or provide become credentials in AAP.

**Red Hat reference**: AAP 2.6 Troubleshooting Guide -- "Privilege escalation timeouts can occur when sudo requires a password or when the become method is misconfigured."

#### 3b. Credential Mismatch

| Field | Pattern |
|---|---|
| Event | `runner_on_unreachable` or `runner_on_failed` |
| Message | Contains "Authentication failed", "Permission denied (publickey)" |

**Resolution path**: Ops team. Update the AAP credential with the correct SSH key or password. Verify the credential is attached to the correct job template.

**Red Hat reference**: AAP 2.5 Security Best Practices (Ch. 15, Sec. 15.1.4) -- "Credentials should be defined at the organization or team level."

#### 3c. File Permission Denied

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Module | `ansible.builtin.copy`, `ansible.builtin.file`, `ansible.builtin.template` |
| Message | Contains "Permission denied" (NOT SSH-related) |

**Resolution path**: Ops team. Fix file/directory permissions on the target host.

#### 3d. Service Configuration Error

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Module | `ansible.builtin.service`, `ansible.builtin.systemd` |
| Message | Contains "Failed to start", "failed with result 'exit-code'" |

**Resolution path**: Ops team. Check the service's configuration files, port conflicts, and dependency services on the target host.

#### 3e. Missing Collection in EE

| Field | Pattern |
|---|---|
| Event | `runner_on_failed` |
| Message | Contains "couldn't resolve module/action", "No module named" |

**Resolution path**: Platform admin. Update the Execution Environment to include the required Ansible collection.

**Red Hat reference**: AAP 2.6 Creating and Consuming Execution Environments -- "Custom EEs allow pinning specific Ansible collections."

---

## Resolution Path Summary

| Classification | Who Acts | Typical Fix | Red Hat Doc Reference |
|---|---|---|---|
| **Platform** - Host Unreachable | Network/Infra | Firewall, SSH, DNS | AAP 2.6 Troubleshooting Guide |
| **Platform** - EE Unavailable | Platform Admin | Registry access, EE config | AAP 2.6 EE Guide |
| **Platform** - Capacity | Platform Admin | Scale instances | AAP 2.5 Instance Groups (Ch. 17) |
| **Code** - Undefined Variable | Playbook Dev | Define variable | Ansible Variable Precedence docs |
| **Code** - Wrong Package | Playbook Dev | Fix package name | RHEL Package Management docs |
| **Code** - Syntax Error | Playbook Dev | Fix Jinja2/YAML | Ansible Playbook Guide |
| **Code** - Script Failure | Playbook Dev | Debug script | N/A (custom script) |
| **Config** - Privilege Escalation | Ops Team | Sudoers config | AAP 2.6 Troubleshooting Guide |
| **Config** - Credential Mismatch | Ops Team | Update credential | AAP 2.5 Security Best Practices |
| **Config** - Permissions | Ops Team | File permissions | RHEL System Administration |
| **Config** - Service Failure | Ops Team | Service config | systemd documentation |
| **Config** - Missing Collection | Platform Admin | Update EE | AAP 2.6 EE Guide |

---

## Cross-References

- **[job-troubleshooting.md](../aap/job-troubleshooting.md)** -- Use first for event extraction and host correlation before classifying errors
- **[execution-governance.md](../aap/execution-governance.md)** -- For rollback options after classification determines the error requires immediate remediation
- **[governance-readiness.md](../aap/governance-readiness.md)** -- Platform errors may indicate governance gaps (e.g., single instance group causing capacity issues)

---

## Official Red Hat Sources

1. Red Hat AAP 2.6, Troubleshooting Ansible Automation Platform -- Troubleshoot Jobs. https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/troubleshooting_ansible_automation_platform/troubleshoot-jobs. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

2. Ansible Built-in Module Documentation. https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html. Accessed 2026-02-20.

3. Red Hat AAP 2.5, Configuring Automation Execution. https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

---

## Quick Reference

| Error Indicator | Classification | Resolution Owner |
|---|---|---|
| `runner_on_unreachable` | Platform | Network/Infra |
| Job status `error` | Platform | Platform Admin |
| `AnsibleUndefinedVariable` | Code | Playbook Dev |
| `No package matching` | Code | Playbook Dev |
| `rc != 0` (shell/command) | Code | Playbook Dev |
| `privilege escalation` / `Timeout` | Configuration | Ops Team |
| `Permission denied` (file) | Configuration | Ops Team |
| `Failed to start` (service) | Configuration | Ops Team |
| `couldn't resolve module` | Configuration | Platform Admin (EE) |

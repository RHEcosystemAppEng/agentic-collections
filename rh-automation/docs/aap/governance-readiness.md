---
title: AAP Governance Readiness Assessment
category: aap
sources:
  - title: "Red Hat AAP 2.5 - Security Best Practices"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-security-best-practices
    sections: "Ch. 15: Sec. 15.1.2 Minimize administrative accounts, Sec. 15.1.4 Remove user access to credentials, Sec. 15.1.5 Enforce separation of duties, Sec. 15.2.1 Use teams for role-based access, Sec. 15.2.2 External authentication"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Workflows"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/using_automation_execution/controller-workflows
    sections: "Ch. 9: Workflow job templates, Sec. 9.4 Workflow RBAC, approval nodes"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Notifications"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/using_automation_execution/controller-notifications
    sections: "Ch. 25: Notification templates, inheritance hierarchy, notification types"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Instance Groups"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-instance-groups
    sections: "Ch. 17: Instance groups, policies, max_forks, resource isolation"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - Activity Stream"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/assembly-controller-activity-stream
    sections: "Activity stream audit logging, event filtering"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.6 - Execution Environments"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/creating_and_consuming_execution_environments
    sections: "Custom EE creation, dependency pinning, ansible-builder"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.6 - Hardening Guide"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/hardening_and_compliance/index
    sections: "Platform hardening, credential rotation, audit requirements"
    date_accessed: 2026-02-20
  - title: "Red Hat AAP 2.5 - RBAC"
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/access_management_and_authentication/gw-managing-access
    sections: "Ch. 4: Role-based access controls, role definitions, team assignments"
    date_accessed: 2026-02-20
tags: [governance, readiness, assessment, rbac, credentials, workflows, notifications, execution-environments, instance-groups, audit, compliance]
applies_to: [aap2.5, aap2.6]
semantic_keywords:
  - "platform readiness assessment"
  - "governance audit"
  - "AAP best practices check"
  - "RBAC compliance"
  - "credential hygiene"
  - "workflow governance"
  - "notification coverage"
  - "execution environment review"
  - "workload isolation"
  - "audit trail verification"
  - "production readiness"
use_cases:
  - "governance_readiness_assessment"
  - "platform_audit"
  - "pre_execution_check"
related_docs:
  - "aap/execution-governance.md"
  - "aap/job-troubleshooting.md"
  - "references/error-classification.md"
last_updated: 2026-02-26
---

# AAP Governance Readiness Assessment

This document teaches the agent how to audit an Ansible Automation Platform environment against Red Hat's official best practices across 7 governance domains, using MCP tools from all 6 AAP MCP servers. For each domain, the agent learns what "good" looks like according to Red Hat, how to check it programmatically, and how to report findings with full source attribution.

## Overview

A governance readiness assessment answers the question: **"Is this AAP instance configured according to Red Hat's published best practices for production use?"**

The assessment covers 7 domains. Each domain maps to specific Red Hat documentation with direct quotes where available, or feature descriptions where Red Hat documents capability without explicit recommendation. The agent's role is to check the current AAP configuration against these standards and report findings transparently.

## When to Use This Document

**Use when**:
- User asks to assess AAP governance readiness
- User asks "Is my AAP ready for production?"
- User asks to audit platform configuration
- Before a first production execution (part of governance-executor workflow)
- User asks "What should I fix before executing jobs?"

**Do NOT use when**:
- User wants to execute a specific job template (use [execution-governance.md](execution-governance.md))
- User wants to troubleshoot a failed job (use [job-troubleshooting.md](job-troubleshooting.md))
- User only wants to validate MCP connectivity (use aap-mcp-validator skill directly)

---

## Domain 1: Workflow Governance

### Red Hat Source

> "Workflows enable you to configure a sequence of disparate job templates (or workflow templates) and link them together in order to execute them as a single unit."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 9: Workflows*

> "You must have execute access to a job template to add it to a workflow job template."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 9, Sec. 9.4: Workflow RBAC*

### What This Means in Practice

Workflows are Red Hat's prescribed mechanism for multi-step automation with error handling. A workflow can include approval nodes (human gates), failure paths (rollback), and conditional logic. Running standalone job templates for production changes -- without wrapping them in workflows -- bypasses these governance controls.

### MCP Assessment Pattern

**Step 1**: Query workflow job templates.

```json
MCP Server: aap-mcp-job-management
Tool: workflow_job_templates_list
Parameters: { "page_size": 100 }
```

**Step 2**: Query standalone job templates.

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_list
Parameters: { "page_size": 100 }
```

**Step 3**: Compare counts. Calculate the workflow coverage ratio: `workflow_count / (workflow_count + standalone_template_count)`.

### Decision Table

| Workflow Count | Standalone Count | Ratio | Status | Recommendation |
|---|---|---|---|---|
| > 0 | Any | > 50% | **PASS** | Workflows are in active use |
| > 0 | Many | < 50% | **WARN** | Most templates run outside workflow governance |
| 0 | Any | 0% | **GAP** | No workflows configured; production changes lack approval gates and failure paths |

### Gap Remediation

Workflows cannot be created via the current MCP tools (no `workflow_job_templates_create` endpoint). Report this as a manual action item:

**Recommendation**: "Per Red Hat's Workflow documentation (Ch. 9), create workflow job templates that wrap your production job templates. Include approval nodes before critical steps and failure-path nodes for rollback."

### Pitfalls

- **Don't count workflow existence as governance**: A workflow with a single node and no approval gates provides no additional governance over a standalone template.
- **Don't ignore workflow RBAC**: Per Red Hat (Ch. 9, Sec. 9.4), users need execute access to add templates to workflows. Check that workflow execute permissions are restricted appropriately.

---

## Domain 2: Notification Coverage

### Red Hat Source

> "You can set notifications on job start and job end, including job failure, for the following resources: job templates, workflow templates, organizations, and projects."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 25: Notifications*

> "Notification templates can be inherited from an organization or project level, so you do not need to configure them on every job template individually."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide, Ch. 25, Sec. 25.1: Notification Hierarchy*

### What This Means in Practice

Notifications ensure that job outcomes -- especially failures -- are communicated to stakeholders. Without notification templates, a failed production job could go unnoticed until its impact is discovered manually. Red Hat supports Email, Slack, Webhook, PagerDuty, IRC, Grafana, Twilio, and custom webhook notification types.

### MCP Assessment Pattern

**Step 1**: Query notification templates.

```json
MCP Server: aap-mcp-configuration
Tool: notification_templates_list
Parameters: { "page_size": 100 }
```

**Step 2**: Examine results. Check for:
- At least one notification template exists
- Templates cover failure events (look for `notification_type` and associated job template/workflow bindings in the response)

### Decision Table

| Templates Found | Types | Status | Recommendation |
|---|---|---|---|
| > 0 | Includes failure notifications | **PASS** | Notification coverage is configured |
| > 0 | Only success notifications | **WARN** | No failure notifications; failed jobs may go unnoticed |
| 0 | N/A | **GAP** | No notification templates configured |

### Gap Remediation

Notification templates CAN be created via MCP:

```json
MCP Server: aap-mcp-configuration
Tool: notification_templates_create
Parameters: {
  "name": "Production Job Failures",
  "notification_type": "email",
  "organization": 1,
  "notification_configuration": {
    "recipients": ["ops-team@example.com"],
    "sender": "aap-notifications@example.com",
    "host": "smtp.example.com",
    "port": 587,
    "use_tls": true
  }
}
```

**Recommendation**: "Per Red Hat's Notification documentation (Ch. 25), configure notification templates at the organization level for inheritance. At minimum, set up failure notifications for all production job templates."

### Pitfalls

- **Don't assume inheritance is configured**: A notification template existing doesn't mean it's attached to job templates. The template must be bound to specific resources or inherited via organization/project.
- **Don't skip failure notifications**: Per Red Hat (Ch. 25), notifications can be set on both start and end events. Production governance requires at minimum failure notifications.

---

## Domain 3: Access Control (RBAC)

### Red Hat Source

> "Use teams inside of organizations to assign permissions to groups of users rather than to users individually."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Ch. 15, Sec. 15.2.1*

> "Delegate the minimum level of privileges required to run automation."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Ch. 15, Sec. 15.2.1*

> "Minimize administrative accounts...restrict to the minimum set of users."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Ch. 15, Sec. 15.1.2*

### What This Means in Practice

Red Hat's RBAC guidance has three pillars: (1) team-based assignment over individual assignment, (2) least privilege, and (3) minimal admin accounts. Violations include: users with direct individual role assignments instead of team-based ones, excessive superuser accounts, and overly broad role definitions.

### MCP Assessment Pattern

**Step 1**: Query all users.

```json
MCP Server: aap-mcp-user-management
Tool: users_list
Parameters: { "page_size": 100 }
```

**Step 2**: Count superuser accounts. From results, count users where `is_superuser` is `true`.

**Step 3**: Query all teams.

```json
MCP Server: aap-mcp-user-management
Tool: teams_list
Parameters: { "page_size": 100 }
```

**Step 4**: Query individual user role assignments.

```json
MCP Server: aap-mcp-user-management
Tool: role_user_assignments_list
Parameters: { "page_size": 100 }
```

**Step 5**: Query team-based role assignments.

```json
MCP Server: aap-mcp-user-management
Tool: role_team_assignments_list
Parameters: { "page_size": 100 }
```

**Step 6**: Compare individual vs team assignments. Calculate team assignment ratio: `team_assignments / (team_assignments + user_assignments)`.

### Decision Table

| Superusers | Teams | Assignment Ratio | Status | Finding |
|---|---|---|---|---|
| 1 | > 0 | Team-heavy (> 50%) | **PASS** | RBAC follows Red Hat best practices |
| 1 | > 0 | User-heavy (< 50%) | **WARN** | Teams exist but most permissions are assigned individually |
| 1 | 0 | 0% (all individual) | **GAP** | No teams configured; violates "Use teams...to assign permissions to groups" |
| > 1 | Any | Any | **WARN** | Multiple superuser accounts; violates "Minimize administrative accounts" |
| > 3 | Any | Any | **GAP** | Excessive superuser accounts; critical violation of least privilege |

### Gap Remediation

Teams CAN be created via MCP, and role assignments can be managed:

```json
MCP Server: aap-mcp-user-management
Tool: teams_create
Parameters: {
  "name": "automation-operators",
  "organization": 1,
  "description": "Operators who execute production job templates"
}
```

Role assignments can be created to grant team-level permissions:

```json
MCP Server: aap-mcp-user-management
Tool: role_user_assignments_create
Parameters: {
  "user": 3,
  "role_definition": 14,
  "object_id": "1"
}
```

**Recommendation**: "Per Red Hat's Security Best Practices (Ch. 15, Sec. 15.2.1), migrate individual user role assignments to team-based assignments. Create teams that map to operational roles (e.g., automation-operators, automation-admins, automation-auditors) and assign permissions to teams."

### Pitfalls

- **Don't count the admin account as a violation**: Every AAP instance has at least one superuser. The concern is *additional* superuser accounts beyond the minimum required.
- **Don't ignore service accounts**: Users created for CI/CD or API access may legitimately need individual assignments, but they should still follow least privilege.

---

## Domain 4: Credential Security

### Red Hat Source

> "Remove user access to credentials. Credentials can be configured at the organization, team, or user level. Red Hat recommends that credentials be defined at the organization or team level."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Ch. 15, Sec. 15.1.4*

> "Enforce separation of duties. Different credentials (SSH keys, cloud tokens) should be used for different pieces of automation. Do not share one credential across all job templates."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Ch. 15, Sec. 15.1.5*

### What This Means in Practice

Red Hat's credential guidance requires: (1) credentials managed at org/team level, not individual user level, (2) separate credentials per automation context (not one "master key" for everything), and (3) credential types that enforce structure. A single "Machine" credential used across all job templates violates separation of duties.

### MCP Assessment Pattern

**Step 1**: Query all credentials.

```json
MCP Server: aap-mcp-security-compliance
Tool: credentials_list
Parameters: { "page_size": 100 }
```

**Step 2**: Query credential types.

```json
MCP Server: aap-mcp-security-compliance
Tool: credential_types_list
Parameters: { "page_size": 100 }
```

**Step 3**: Analyze credential diversity. From the credentials list, check:
- How many unique credential types are in use
- Whether multiple credentials of the same type exist (separation of duties)
- Whether credentials have descriptive names suggesting scoped usage (e.g., "prod-ssh-key" vs "my-key")

### Decision Table

| Credential Count | Unique Types | Separation | Status | Finding |
|---|---|---|---|---|
| > 1 | > 1 | Scoped names | **PASS** | Credentials follow separation of duties |
| > 1 | 1 | All same type | **WARN** | Single credential type; limited separation of duties |
| 1 | 1 | Single cred | **GAP** | One credential for all automation; violates "Enforce separation of duties" |
| 0 | 0 | None | **GAP** | No credentials configured |

### Gap Remediation

Credentials CAN be created via MCP:

```json
MCP Server: aap-mcp-security-compliance
Tool: credentials_create
Parameters: {
  "name": "prod-machine-credential",
  "credential_type": 1,
  "organization": 1,
  "inputs": {
    "username": "ansible-svc",
    "ssh_key_data": "{{ lookup('file', '/path/to/key') }}"
  }
}
```

**Recommendation**: "Per Red Hat's Security Best Practices (Ch. 15, Sec. 15.1.5), create separate credentials for each environment (dev, staging, production) and each automation context (machine access, cloud provider, source control). Use credential types to enforce input structure."

### Pitfalls

- **Don't expose credential values**: The MCP `credentials_list` tool returns credential metadata, not secrets. Never attempt to retrieve or display actual credential values.
- **Don't confuse credential count with security**: Having 10 credentials doesn't mean they're properly scoped. Check names and types for evidence of separation.

---

## Domain 5: Execution Environments

### Red Hat Source

Red Hat provides Execution Environments (EEs) as containerized runtime environments for automation jobs. EEs replace the legacy `virtualenv` approach.

> "Execution environments are container images that serve as Ansible control nodes. They provide a defined, consistent, and portable environment for executing automation."
>
> -- *Red Hat AAP 2.6, Creating and Consuming Execution Environments*

Red Hat ships a default `Minimal execution environment` and an `Ansible Automation Platform execution environment`. Custom EEs allow pinning specific Ansible collections, Python packages, and system packages.

### What This Means in Practice

Using only the default EE for all jobs means every playbook runs in the same environment, with no dependency isolation. Per Red Hat's EE documentation, custom EEs let teams pin specific collection versions and Python dependencies, preventing "works on my machine" failures and ensuring reproducible automation.

**Framing**: Red Hat provides custom EE capability for dependency isolation and reproducibility. Assessment: Are you utilizing it?

### MCP Assessment Pattern

**Step 1**: Query execution environments.

```json
MCP Server: aap-mcp-configuration
Tool: execution_environments_list
Parameters: { "page_size": 100 }
```

**Step 2**: Analyze results. Check:
- Total count of EEs
- Whether any custom EEs exist (beyond the default Red Hat-provided ones)
- Image names: `quay.io/ansible/` or `registry.redhat.io/` prefixes indicate vendor-provided; custom registries indicate custom EEs

### Decision Table

| Total EEs | Custom EEs | Status | Finding |
|---|---|---|---|
| > default count | > 0 | **PASS** | Custom execution environments in use |
| Default only | 0 | **WARN** | Only default EEs; all jobs share the same runtime environment |

### Gap Remediation

Custom EEs CAN be registered via MCP:

```json
MCP Server: aap-mcp-configuration
Tool: execution_environments_create
Parameters: {
  "name": "production-ee",
  "image": "registry.example.com/aap/production-ee:1.0",
  "organization": 1,
  "description": "Production EE with pinned collection versions"
}
```

**Recommendation**: "Per Red Hat's EE documentation (AAP 2.6), create custom execution environments using `ansible-builder` to pin specific Ansible collections and Python dependencies. This ensures reproducible, isolated automation runs."

### Pitfalls

- **Don't flag default EEs as a failure**: Default EEs are legitimate for development and simple automation. Custom EEs are a maturity indicator, not a hard requirement.
- **Don't overlook image tags**: An EE referencing `latest` tag loses the reproducibility benefit of custom EEs.

---

## Domain 6: Workload Isolation

### Red Hat Source

Red Hat provides Instance Groups for workload isolation and resource management.

> "Instance groups can be used to assign jobs to run on specific sets of instances, providing workload isolation and resource management."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Ch. 17: Instance Groups*

Instance groups support `max_forks` settings to limit concurrent automation load, and policy settings to control instance membership.

### What This Means in Practice

Without instance groups (beyond the default), all jobs compete for the same execution capacity. Production and development workloads share resources, meaning a runaway dev job can starve production automation. Instance groups enable isolation: "production jobs run on production instances, dev jobs run on dev instances."

**Framing**: Red Hat provides instance groups for workload isolation. Assessment: Are you utilizing them to separate production and non-production workloads?

### MCP Assessment Pattern

**Step 1**: Query instance groups.

```json
MCP Server: aap-mcp-system-monitoring
Tool: instance_groups_list
Parameters: { "page_size": 100 }
```

**Step 2**: Analyze results. Check:
- Total count of instance groups
- Whether groups beyond the default exist
- Group names suggesting environment separation (e.g., "production", "development")

### Decision Table

| Instance Groups | Beyond Default | Status | Finding |
|---|---|---|---|
| > 1 | Yes | **PASS** | Workload isolation configured |
| 1 (default only) | No | **WARN** | Single instance group; all workloads share resources |

### Gap Remediation

Instance groups CAN be created via MCP:

```json
MCP Server: aap-mcp-system-monitoring
Tool: instance_groups_create
Parameters: {
  "name": "production",
  "max_forks": 50
}
```

**Recommendation**: "Per Red Hat's Instance Groups documentation (Ch. 17), create separate instance groups for production and non-production workloads. Configure `max_forks` to prevent resource contention."

### Pitfalls

- **Don't over-isolate**: Creating too many instance groups with too few instances each can lead to resource underutilization.
- **Don't forget the controlplane group**: The `controlplane` instance group is system-managed and should not be modified.

---

## Domain 7: Audit Trail

### Red Hat Source

Red Hat provides the Activity Stream as the platform's built-in audit trail.

> "The Activity Stream shows all changes and events in the automation controller, including who made changes and when."
>
> -- *Red Hat AAP 2.5, Automation Controller User Guide: Activity Stream*

The Activity Stream captures user logins, resource creation/modification/deletion, job launches, and configuration changes.

**Framing**: Red Hat provides the Activity Stream for audit and compliance. Assessment: Is it accessible and generating entries?

### MCP Assessment Pattern

**Step 1**: Query the activity stream.

```json
MCP Server: aap-mcp-system-monitoring
Tool: activity_stream_list
Parameters: { "page_size": 10 }
```

**Step 2**: Analyze results. Check:
- Whether entries are being generated (non-empty response)
- Recency of entries (is the platform actively logging?)
- Diversity of event types (logins, job launches, configuration changes)

### Decision Table

| Entries | Recency | Status | Finding |
|---|---|---|---|
| > 0 | Recent (within 24h) | **PASS** | Audit trail is active |
| > 0 | Stale (> 7 days) | **WARN** | Audit entries exist but platform appears inactive |
| 0 | N/A | **GAP** | No audit trail entries found |

### Gap Remediation

The Activity Stream is automatic and cannot be configured via MCP. If no entries are found, the platform may be newly installed or there may be a system issue.

**Recommendation**: "Per Red Hat's Activity Stream documentation, verify that the platform is generating audit entries. For compliance, consider integrating the Activity Stream with external SIEM systems via webhooks or API polling."

### Pitfalls

- **Don't assume completeness**: The Activity Stream captures controller-level events, not playbook-level actions on managed hosts.
- **Don't ignore retention**: Activity Stream entries may have retention limits. For long-term audit, export to external systems.

---

## Bonus Domain: External Authentication

### Red Hat Source

> "You can simplify login for your automation controller users by connecting to external account sources by LDAP, SAML 2.0, and certain OAuth providers."
>
> -- *Red Hat AAP 2.5, Configuring Automation Execution, Ch. 15, Sec. 15.2.2*

### What This Means in Practice

Local-only authentication means user lifecycle management is manual and disconnected from enterprise identity. External authentication (LDAP, SAML, OAuth) integrates AAP with the organization's identity provider, enabling centralized user management, MFA enforcement, and automatic deprovisioning.

### MCP Assessment Pattern

**Step 1**: Query authenticators.

```json
MCP Server: aap-mcp-user-management
Tool: authenticators_list
Parameters: { "page_size": 100 }
```

**Step 2**: Analyze results. Check:
- Whether any external authenticators are configured (LDAP, SAML, OIDC)
- Whether configured authenticators are enabled

### Decision Table

| Authenticators | Enabled | Status | Finding |
|---|---|---|---|
| > 0 (external type) | Yes | **PASS** | External authentication configured |
| > 0 (external type) | No | **WARN** | External authenticator exists but is disabled |
| 0 (or local only) | N/A | **WARN** | Local authentication only; no enterprise identity integration |

### Pitfalls

- **Don't flag local auth as a hard failure**: Small environments or labs may legitimately use local authentication. This is a maturity indicator.
- **Don't expose authenticator configuration details**: The response may contain sensitive LDAP/SAML configuration. Report presence/absence only.

---

## Output Template: Governance Readiness Report

The agent MUST produce output in this format so the audience can see Red Hat documentation citations for every finding:

```
## AAP Governance Readiness Report

**Assessment Date**: [date]
**AAP Instance**: [server URL]
**Domains Assessed**: 7 + 1 bonus

---

### Domain 1: Workflow Governance — [PASS/GAP/WARN]

Per Red Hat's *Automation Controller User Guide* (Ch. 9: Workflows):
> "Workflows enable you to configure a sequence of disparate job templates and link them together."

**Finding**: Found [X] workflow job templates and [Y] standalone job templates. Workflow coverage ratio: [Z]%.
**Recommendation**: [action with source citation]

---

### Domain 2: Notification Coverage — [PASS/GAP/WARN]

Per Red Hat's *Automation Controller User Guide* (Ch. 25: Notifications):
> "You can set notifications on job start and job end, including job failure."

**Finding**: Found [X] notification templates. [Types configured].
**Recommendation**: [action with source citation]

---

### Domain 3: Access Control (RBAC) — [PASS/GAP/WARN]

Per Red Hat's *Security Best Practices* (Ch. 15, Sec. 15.2.1):
> "Use teams inside of organizations to assign permissions to groups of users rather than to users individually."

Per Red Hat's *Security Best Practices* (Ch. 15, Sec. 15.1.2):
> "Minimize administrative accounts...restrict to the minimum set of users."

**Finding**: [X] users ([Y] superusers), [Z] teams, [A] individual assignments, [B] team assignments.
**Recommendation**: [action with source citation]

---

### Domain 4: Credential Security — [PASS/GAP/WARN]

Per Red Hat's *Security Best Practices* (Ch. 15, Sec. 15.1.4):
> "Remove user access to credentials...credentials should be defined at the organization or team level."

Per Red Hat's *Security Best Practices* (Ch. 15, Sec. 15.1.5):
> "Enforce separation of duties...different credentials for each piece of automation."

**Finding**: [X] credentials, [Y] credential types, [separation assessment].
**Recommendation**: [action with source citation]

---

### Domain 5: Execution Environments — [PASS/GAP/WARN]

Per Red Hat's *Creating and Consuming Execution Environments* (AAP 2.6):
> "Execution environments are container images that serve as Ansible control nodes."

**Finding**: [X] execution environments ([Y] custom, [Z] default).
**Recommendation**: [action with source citation]

---

### Domain 6: Workload Isolation — [PASS/GAP/WARN]

Per Red Hat's *Configuring Automation Execution* (Ch. 17: Instance Groups):
> "Instance groups can be used to assign jobs to run on specific sets of instances."

**Finding**: [X] instance groups. [Beyond default assessment].
**Recommendation**: [action with source citation]

---

### Domain 7: Audit Trail — [PASS/GAP/WARN]

Per Red Hat's *Activity Stream* documentation:
> "The Activity Stream shows all changes and events in the automation controller."

**Finding**: [X] activity stream entries. Most recent: [date].
**Recommendation**: [action with source citation]

---

### Bonus: External Authentication — [PASS/WARN]

Per Red Hat's *Security Best Practices* (Ch. 15, Sec. 15.2.2):
> "Connecting to external account sources by LDAP, SAML 2.0, and certain OAuth providers."

**Finding**: [X] external authenticators configured. [Enabled status].
**Recommendation**: [action with source citation]

---

### Summary

| Domain | Status | Key Finding |
|---|---|---|
| Workflow Governance | [status] | [one-line finding] |
| Notification Coverage | [status] | [one-line finding] |
| Access Control (RBAC) | [status] | [one-line finding] |
| Credential Security | [status] | [one-line finding] |
| Execution Environments | [status] | [one-line finding] |
| Workload Isolation | [status] | [one-line finding] |
| Audit Trail | [status] | [one-line finding] |
| External Authentication | [status] | [one-line finding] |

**Overall**: [X] PASS, [Y] WARN, [Z] GAP out of 8 domains assessed.
```

---

## Cross-Domain Correlation

Individual domain assessments reveal single-dimension findings. Cross-domain correlation reveals **compound risks** where gaps in one domain amplify weaknesses in another. The agent MUST perform this analysis after completing all domain assessments.

### Why Correlation Matters

Red Hat's Security Best Practices (Ch. 15) are interconnected: RBAC enables team-based credential management, workflows enable approval gates, notifications ensure visibility. When multiple domains have gaps, the compound effect is worse than the sum of individual gaps.

### Correlation Patterns

After assessing all domains, check for these compound findings:

#### Pattern 1: RBAC Gap + Credential Risk

**Trigger**: Domain 3 (RBAC) is GAP or WARN *and* Domain 4 (Credentials) has any credentials.

**Compound Finding**: Per Red Hat's Ch. 15, Sec. 15.1.4: "Credentials can be configured at the organization, team, or user level." Without teams (Domain 3), credentials are necessarily user-scoped, directly violating this guidance.

**Elevated Recommendation**: "Fix RBAC first -- creating teams unlocks team-scoped credential management, which addresses both domains simultaneously."

#### Pattern 2: No Workflows + No Notifications

**Trigger**: Domain 1 (Workflows) is GAP *and* Domain 2 (Notifications) is GAP.

**Compound Finding**: Jobs run as standalone templates (no approval gates, no failure paths) with no failure alerting. Per Ch. 9 and Ch. 25, this means a failed production job has no governance controls AND no visibility.

**Elevated Recommendation**: "This is the highest-risk combination. Production failures will go unnoticed until manually discovered. Address both domains urgently."

#### Pattern 3: Single Instance Group + Production/Dev Inventories

**Trigger**: Domain 6 (Workload Isolation) is WARN *and* inventory data shows both production-pattern and dev-pattern inventories exist.

**Additional MCP Query** (adaptive -- only when triggered):

```json
MCP Server: aap-mcp-inventory-management
Tool: inventories_list
Parameters: { "page_size": 100 }
```

If inventories matching both `prod`/`production` and `dev`/`development` patterns exist:

**Compound Finding**: Per Ch. 17, instance groups provide workload isolation. With a single group, a runaway development job can starve production automation capacity.

**Elevated Recommendation**: "Create separate instance groups for production and non-production workloads to prevent resource contention."

#### Pattern 4: Multiple Superusers + No External Auth

**Trigger**: Domain 3 (RBAC) shows > 1 superuser *and* Bonus Domain (External Auth) is WARN (local only).

**Compound Finding**: Per Ch. 15, Sec. 15.1.2 and Sec. 15.2.2, superuser accounts with local-only authentication lack MFA and centralized lifecycle management. Password compromise has maximum blast radius.

**Elevated Recommendation**: "Configure external authentication (LDAP/SAML/OIDC) to enforce MFA on superuser accounts. This addresses both RBAC and authentication gaps."

### Correlation Output Template

After the domain-by-domain report, include compound findings:

```
### Compound Risk Analysis

[Only include this section if correlation patterns matched]

⚠️ **[Pattern Name]**:
- Domains involved: [Domain X] ([status]) + [Domain Y] ([status])
- Per Red Hat's [source]: "[relevant quote]"
- Combined impact: [what the compound risk means]
- Priority action: [what to fix first and why]
```

---

## Adaptive Depth Queries

When a domain assessment reveals specific conditions, the agent SHOULD perform follow-up queries to deepen the finding rather than stopping at the surface-level check. This is how the assessment adapts to what it discovers.

### Notification Depth: Check Actual Bindings

**Trigger**: Domain 2 reports PASS (notification templates exist).

**Rationale**: Templates existing doesn't mean they're attached to anything.

**Follow-up Query**:

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_list
Parameters: { "page_size": 100 }
```

Examine each job template's response for notification association fields (`related.notification_templates_started`, `related.notification_templates_success`, `related.notification_templates_error`). If ALL job templates show empty notification bindings:

**Revised Finding**: Downgrade Domain 2 to **WARN**: "Notification templates exist but are not bound to any job templates. Per Ch. 25: 'You can set notifications on job start and job end, including job failure' -- but only if templates are attached to resources."

### Credential Depth: Check Separation of Duties

**Trigger**: Domain 4 has multiple credentials (potential PASS).

**Rationale**: Multiple credentials don't guarantee they're properly scoped.

**Follow-up Query**:

```json
MCP Server: aap-mcp-job-management
Tool: job_templates_list
Parameters: { "page_size": 100 }
```

Compare each job template's `credential` or `credentials` field. If one credential ID appears across templates targeting different inventories (e.g., both dev and prod):

**Revised Finding**: Downgrade Domain 4 to **WARN**: "Credential '[name]' (ID: [id]) is shared across both development and production job templates. Per Ch. 15, Sec. 15.1.5: 'Enforce separation of duties...different credentials for different pieces of automation.'"

### RBAC Depth: Check Role Breadth

**Trigger**: Domain 3 reports PASS (teams exist, team-based assignments).

**Rationale**: Team-based assignments don't guarantee least privilege.

**Follow-up Query**:

```json
MCP Server: aap-mcp-user-management
Tool: role_team_assignments_list
Parameters: { "page_size": 100 }
```

Cross-reference with role definitions. If any team has Admin-level access on organization-wide scope:

**Revised Finding**: Downgrade Domain 3 to **WARN**: "Teams exist, but team '[name]' has Admin-level access across the organization. Per Ch. 15, Sec. 15.2.1: 'Delegate the minimum level of privileges required to run automation.'"

### Scale Calibration

**Trigger**: Always (after all domain assessments).

**Rationale**: A 2-host lab and a 200-host enterprise have different severity thresholds.

**Follow-up Queries**:

```json
MCP Server: aap-mcp-inventory-management
Tool: inventories_list
Parameters: { "page_size": 100 }
```

```json
MCP Server: aap-mcp-inventory-management
Tool: hosts_list
Parameters: { "page_size": 1 }
```

Use total host count and inventory naming patterns to calibrate severity framing:

| Scale Signal | Calibration |
|---|---|
| < 5 hosts, dev/lab inventory only | "Small lab/development environment. Governance gaps noted but severity calibrated to environment scale." |
| 5-50 hosts, mixed inventories | Standard severity |
| > 50 hosts or production-pattern inventories | "Enterprise environment with production workloads. Governance gaps carry elevated risk." |

---

## Prioritized Remediation Ordering

Instead of listing all gaps equally, order remediation by dependency chain. Some fixes unlock others:

| Priority | Domain | Rationale |
|---|---|---|
| 1 | RBAC (Domain 3) | Prerequisite for team-scoped credentials and role-based access |
| 2 | Credential Security (Domain 4) | Depends on teams existing for proper scoping |
| 3 | Workflow Governance (Domain 1) | Enables approval gates and failure paths |
| 4 | Notification Coverage (Domain 2) | Most effective when attached to workflows/templates |
| 5 | Execution Environments (Domain 5) | Independent -- can fix in parallel |
| 6 | Workload Isolation (Domain 6) | Independent -- can fix in parallel |
| 7 | External Authentication (Bonus) | Independent but high-impact for security posture |
| 8 | Audit Trail (Domain 7) | Automatic -- no action unless missing |

**Output Template**:

After the domain-by-domain report, include:

```
### Recommended Fix Order

Based on dependency analysis, address gaps in this order:

1. **[First unfixed domain]** — [why this must be fixed first]
   → Unlocks: [what fixing this enables]
2. **[Second unfixed domain]** — [why this comes next]
   → Depends on: [prerequisite from step 1]
3. ...

Domains that can be addressed in parallel: [list independent domains]
```

---

## Cross-References

- **[execution-governance.md](execution-governance.md)** -- After assessing readiness, use this document for governed execution with risk classification and check mode
- **[job-troubleshooting.md](job-troubleshooting.md)** -- If jobs fail during execution, use this document for forensic troubleshooting with event parsing and host correlation
- **[error-classification.md](../references/error-classification.md)** -- Reference for systematic error classification and resolution path determination

---

## Official Red Hat Sources

1. Red Hat AAP 2.5, Configuring Automation Execution -- Security Best Practices (Ch. 15). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-security-best-practices. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

2. Red Hat AAP 2.5, Automation Controller User Guide -- Workflows (Ch. 9). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/using_automation_execution/controller-workflows. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

3. Red Hat AAP 2.5, Automation Controller User Guide -- Notifications (Ch. 25). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/using_automation_execution/controller-notifications. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

4. Red Hat AAP 2.5, Automation Controller User Guide -- RBAC (Ch. 4). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/access_management_and_authentication/gw-managing-access. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

5. Red Hat AAP 2.5, Configuring Automation Execution -- Instance Groups (Ch. 17). https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-instance-groups. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

6. Red Hat AAP 2.5, Automation Controller User Guide -- Activity Stream. https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/assembly-controller-activity-stream. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

7. Red Hat AAP 2.6, Creating and Consuming Execution Environments. https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/creating_and_consuming_execution_environments. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

8. Red Hat AAP 2.6, Hardening Guide. https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/hardening_and_compliance/index. Accessed 2026-02-20. Content used under CC BY-SA 4.0.

---

## Quick Reference

| Domain | Red Hat Source | MCP Server | Key Tool | Status Thresholds |
|---|---|---|---|---|
| Workflow Governance | Ch. 9 Workflows | job-management | `workflow_job_templates_list` | PASS: >50% coverage, GAP: 0 workflows |
| Notification Coverage | Ch. 25 Notifications | configuration | `notification_templates_list` | PASS: failure notifs exist, GAP: 0 templates |
| Access Control (RBAC) | Ch. 15 Sec. 15.2.1 | user-management | `users_list`, `teams_list`, `role_user_assignments_list`, `role_team_assignments_list` | PASS: teams + <2 superusers, GAP: 0 teams |
| Credential Security | Ch. 15 Sec. 15.1.4-5 | security-compliance | `credentials_list`, `credential_types_list` | PASS: multiple scoped creds, GAP: 1 cred |
| Execution Environments | AAP 2.6 EE Guide | configuration | `execution_environments_list` | PASS: custom EEs, WARN: default only |
| Workload Isolation | Ch. 17 Instance Groups | system-monitoring | `instance_groups_list` | PASS: >1 group, WARN: default only |
| Audit Trail | Activity Stream docs | system-monitoring | `activity_stream_list` | PASS: recent entries, GAP: 0 entries |
| External Auth (bonus) | Ch. 15 Sec. 15.2.2 | user-management | `authenticators_list` | PASS: external enabled, WARN: local only |

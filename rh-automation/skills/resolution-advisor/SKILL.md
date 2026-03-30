---
name: resolution-advisor
description: |
  Provide Red Hat documentation-backed resolution recommendations for classified job errors.

  Use when:
  - After failure analysis and host fact inspection: "How do I fix this?"
  - "What does Red Hat recommend for this error?"
  - "What's the fix for privilege escalation timeout?"
  - "Is this a known AAP issue?"

  NOT for: analyzing events (use job-failure-analyzer first) or checking host facts (use host-fact-inspector first).
model: inherit
color: green
---

# Resolution Advisor

## Prerequisites

**Required MCP Servers**: None required (this skill provides advisory based on documentation)

## When to Use This Skill

Use this skill when:
- After `job-failure-analyzer` has classified the error type
- After `host-fact-inspector` has correlated host facts (when applicable)
- As the final step in the forensic-troubleshooter workflow
- User asks for resolution recommendations

Do NOT use when:
- Job events haven't been analyzed yet (run `job-failure-analyzer` first)
- Host facts haven't been checked (run `host-fact-inspector` first if hosts are involved)
- User wants to execute a job (use governance-executor skill)

## Workflow

### Step 1: Consult Error Classification and Troubleshooting Documentation

**CRITICAL**: Document consultation MUST happen BEFORE providing recommendations.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [error-classification.md](../../docs/references/error-classification.md) using the Read tool to understand the error taxonomy, classification decision tree, and resolution path mapping
2. **Action**: Read [job-troubleshooting.md](../../docs/aap/job-troubleshooting.md) using the Read tool to understand failure pattern details and Red Hat source citations
3. **Output to user**: "I consulted [error-classification.md](docs/references/error-classification.md) and [job-troubleshooting.md](docs/aap/job-troubleshooting.md) to determine the resolution path based on Red Hat's troubleshooting guidance."

### Step 2: Determine Resolution Path

Using the error classification from `job-failure-analyzer` and the correlation from `host-fact-inspector`, map to the resolution path from error-classification.md:

| Classification | Resolution Owner | Red Hat Doc Reference |
|---|---|---|
| Platform - Host Unreachable | Network/Infra team | AAP 2.6 Troubleshooting Guide |
| Platform - EE Unavailable | Platform Admin | AAP 2.6 EE Guide |
| Platform - Capacity | Platform Admin | AAP 2.5 Instance Groups (Ch. 17) |
| Code - Undefined Variable | Playbook Developer | Ansible Variable Precedence docs |
| Code - Wrong Package | Playbook Developer | RHEL Package Management docs |
| Code - Syntax Error | Playbook Developer | Ansible Playbook Guide |
| Config - Privilege Escalation | Ops Team | AAP 2.6 Troubleshooting Guide |
| Config - Credential Mismatch | Ops Team | AAP 2.5 Security Best Practices |
| Config - Service Failure | Ops Team | systemd documentation |
| Config - Missing Collection | Platform Admin | AAP 2.6 EE Guide |

### Step 3: Generate Resolution Advisory

**Output format**:

```
## Resolution Advisory

### Error Summary
**Classification**: [Platform / Code / Configuration] Error
**Pattern**: [Specific pattern from error-classification.md]
**Affected**: [hosts/tasks from failure analysis]

### Red Hat Guidance

Per Red Hat's *[Source Document]*:
> "[Direct quote or guidance from the cited Red Hat documentation]"

### Resolution Steps

**Resolution Owner**: [Network/Infra / Platform Admin / Playbook Developer / Ops Team]

1. [Specific step with Red Hat doc reference]
2. [Specific step with Red Hat doc reference]
3. [Verification step]

### Prevention

Per Red Hat's *[Source Document]* ([Section]):
> "[Guidance on preventing this type of error]"

**Recommended governance control**: [e.g., "Add check mode to catch this in dry runs", "Configure notifications for this failure type"]

### Related Governance Gaps

[If the error points to a governance gap from governance-readiness.md domains, note it]
- Example: "Privilege escalation failures may indicate missing credential separation (Domain 4: Credential Security)"
- Example: "Capacity exhaustion may indicate insufficient workload isolation (Domain 6: Workload Isolation)"
```

### Step 4: Suggest Governance Improvements

If the failure correlates with a governance readiness domain, recommend the user run a governance assessment:

- Platform errors (capacity, EE) → Domains 5 (EE) and 6 (Workload Isolation)
- Configuration errors (credentials, privilege escalation) → Domains 3 (RBAC) and 4 (Credential Security)
- Repeated failures without notification → Domain 2 (Notification Coverage)

## Dependencies

### Required MCP Servers
- None (advisory-only skill based on documentation)

### Required MCP Tools
- None (advisory-only skill based on documentation)

### Related Skills
- `job-failure-analyzer` - Provides error classification input
- `host-fact-inspector` - Provides host correlation input
- `governance-readiness-assessor` - For governance gap follow-up
- `execution-summary` - Audit trail

### Reference Documentation
- [error-classification.md](../../docs/references/error-classification.md) - Error taxonomy and resolution paths
- [job-troubleshooting.md](../../docs/aap/job-troubleshooting.md) - Failure patterns and Red Hat citations

## Example Usage

**User**: "How do I fix the package not found error from Job #4451?"

**Agent**:
1. Reads error-classification.md and job-troubleshooting.md
2. Reports: "I consulted error-classification.md and job-troubleshooting.md to determine the resolution path."
3. Classification: Code Error - Wrong Package Name (Pattern 2b from error-classification.md)
4. Provides resolution:

```
## Resolution Advisory

### Error Summary
**Classification**: Code Error
**Pattern**: Wrong Package Name (2b)
**Affected**: Host web-prod-01, Task "Install security package"

### Red Hat Guidance

Per Red Hat's *AAP 2.6 Troubleshooting Guide*:
> "Module failures typically indicate an issue with the playbook task definition."

### Resolution Steps

**Resolution Owner**: Playbook Developer

1. Verify the package name exists in the target OS repositories
2. Check `ansible_distribution` and `ansible_distribution_version` for the host
3. Update the playbook with the correct package name
4. Re-run with check mode to validate before full execution

### Prevention

Per Red Hat's *Controller Best Practices*:
> "Use separate inventories for production and development environments."

Test playbook changes in a development inventory first.
```

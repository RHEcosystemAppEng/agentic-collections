# Red Hat Automation Agentic Collection

Automation governance for Ansible Automation Platform. 11 skills and 4 reference docs that audit AAP configuration against Red Hat best practices, run governed execution with check mode and rollback, and perform forensic failure analysis with error classification.

**Persona**: Red Hat Automation Governance Architect
**Marketplaces**: Claude Code, Cursor

## What This Adds Over Raw MCP Tools

Raw MCP access lets an agent list templates, launch jobs, and read events. This collection adds:

1. **Knowledge** -- 4 docs distilling 8+ official Red Hat sources, read and cited at runtime
2. **Judgment** -- 8 skills that interpret MCP data through Red Hat best practices (risk classification, error taxonomy, governance assessment)
3. **Workflow** -- 3 orchestration skills that chain other skills with human-in-the-loop controls

All recommendations cite specific Red Hat documentation (chapter and section).

## Three Use Cases

### Use Case 1: Governance Assessment

> "Assess my AAP platform's governance readiness for production use."

The agent audits 7 governance domains across all 6 AAP MCP servers, producing a PASS/GAP/WARN report with Red Hat citations per finding. Domains: Workflow Governance, Notification Coverage, RBAC, Credential Security, Execution Environments, Workload Isolation, Audit Trail.

**Entry point**: `governance-assessor` | **Key skill**: `governance-readiness-assessor` | **Doc**: `governance-readiness.md`

### Use Case 2: Governed Execution

> "Execute the security patch on production urgently."

The agent classifies inventory risk, scans extra_vars for secrets, runs check mode before execution, and requires approval for production targets. Catches failures in dry run before they cause outages.

**Entry point**: `governance-executor` | **Key skills**: `execution-risk-analyzer`, `governed-job-launcher` | **Doc**: `execution-governance.md`

### Use Case 3: Forensic Troubleshooting

> "Job #4451 failed. What happened?"

The agent extracts failure events, classifies errors (Platform/Code/Configuration), correlates with host system facts, and provides Red Hat documentation-backed resolution recommendations.

**Entry point**: `forensic-troubleshooter` | **Key skills**: `job-failure-analyzer`, `host-fact-inspector`, `resolution-advisor` | **Docs**: `job-troubleshooting.md`, `error-classification.md`

## Quick Start

### Prerequisites

- Red Hat Ansible Automation Platform 2.5+
- Cursor IDE (or Claude Code)
- AAP API token

### Environment Setup

```bash
export AAP_MCP_SERVER="your-aap-mcp-server.example.com"
export AAP_API_TOKEN="your-personal-access-token"
```

## Skills (11)

| Skill | Purpose | MCP Servers |
|-------|---------|-------------|
| `governance-assessor` | Orchestrates platform governance audit | All 6 |
| `governance-executor` | Orchestrates governed execution | job-management, inventory-management |
| `forensic-troubleshooter` | Orchestrates failure root cause analysis | job-management, inventory-management |
| `aap-mcp-validator` | Validate AAP MCP server connectivity | All 6 |
| `governance-readiness-assessor` | 7-domain platform governance audit | All 6 |
| `execution-risk-analyzer` | Inventory risk classification + secret scanning | job-management, inventory-management |
| `governed-job-launcher` | Check mode + approval + phased rollout + rollback | job-management |
| `job-failure-analyzer` | Event extraction + error classification | job-management |
| `host-fact-inspector` | Host fact correlation with failures | inventory-management |
| `resolution-advisor` | Red Hat doc-backed resolution recommendations | None (advisory) |
| `execution-summary` | Audit trail with doc consultation tracking | None (reporting) |

## MCP Server Integrations (6)

| Server | Purpose |
|--------|---------|
| `aap-mcp-job-management` | Job templates, launches, events, workflows |
| `aap-mcp-inventory-management` | Inventories, hosts, groups, host facts |
| `aap-mcp-configuration` | Notifications, execution environments, settings |
| `aap-mcp-security-compliance` | Credentials, credential types |
| `aap-mcp-system-monitoring` | Instance groups, activity stream, status |
| `aap-mcp-user-management` | Users, teams, roles, authenticators |

## Documentation

4 AI-optimized documents backed by 8+ official Red Hat sources:

| Document | Content | Red Hat Sources |
|----------|---------|----------------|
| `governance-readiness.md` | 7-domain assessment framework | Security Best Practices, Workflows, Notifications, RBAC, EE, Instance Groups, Activity Stream, Hardening Guide |
| `execution-governance.md` | Risk classification, check mode, rollback, phased rollout | Job Templates, Security Best Practices, Controller Best Practices, Check Mode |
| `job-troubleshooting.md` | Event parsing, host correlation, failure patterns | AAP 2.6 Troubleshooting Guide, Job Events |
| `error-classification.md` | Error taxonomy, classification trees, resolution paths | AAP 2.6 Troubleshooting Guide, Ansible Module docs |

See [docs/INDEX.md](docs/INDEX.md) for the complete documentation map and [docs/SOURCES.md](docs/SOURCES.md) for all source attributions.

## Architecture

```
rh-automation/
├── .mcp.json                        # 6 AAP MCP servers
├── skills/
│   ├── governance-assessor/         # UC1: Orchestrates governance audit
│   ├── governance-executor/         # UC2: Orchestrates governed execution
│   ├── forensic-troubleshooter/     # UC3: Orchestrates failure analysis
│   ├── aap-mcp-validator/           # Shared: MCP connectivity
│   ├── governance-readiness-assessor/ # UC1: 7-domain assessment
│   ├── execution-risk-analyzer/    # UC2: Risk + secret scanning
│   ├── governed-job-launcher/       # UC2: Check mode + launch
│   ├── job-failure-analyzer/        # UC3: Event extraction
│   ├── host-fact-inspector/         # UC3: Host correlation
│   ├── resolution-advisor/          # UC3: Resolution guidance
│   └── execution-summary/          # Shared: Audit trail
└── docs/
    ├── aap/
    │   ├── governance-readiness.md  # 7-domain assessment reference
    │   ├── execution-governance.md # Execution governance reference
    │   └── job-troubleshooting.md   # Failure analysis reference
    └── references/
        └── error-classification.md  # Error taxonomy reference
```

## References

- [Red Hat Ansible Automation Platform](https://www.redhat.com/en/technologies/management/ansible)
- [AAP 2.5 Security Best Practices](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/configuring_automation_execution/controller-security-best-practices)
- [AAP 2.6 Troubleshooting Guide](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/troubleshooting_ansible_automation_platform/troubleshoot-jobs)
- [AAP 2.6 Execution Environments](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html-single/creating_and_using_execution_environments/index)

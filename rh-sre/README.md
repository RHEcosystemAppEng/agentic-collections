# Red Hat SRE Agentic Collection

Site Reliability Engineering tools and automation for managing Red Hat platforms and infrastructure. This pack provides comprehensive capabilities for SRE tasks including vulnerability management, fleet inventory, system monitoring, and operational excellence.

**Persona**: Site Reliability Engineer
**Marketplaces**: Claude Code, Cursor

## Overview

The rh-sre collection is a reference implementation demonstrating the full agentic architecture with:
- **10 specialized skills** for discrete SRE tasks
- **1 orchestration agent** for complex workflows
- **AI-optimized documentation** with semantic indexing
- **2 MCP server integrations** for Red Hat platform access

## Why Use This Agentic Collection Instead of Raw MCP Tools?

While you could use the underlying MCP servers (`lightspeed-mcp`, `ansible-mcp-server`) directly, the agentic collection provides critical advantages that significantly improve reliability, safety, and user experience:

### 🎯 **Reliability & Error Prevention**

**Precise Parameter Specification**
- Skills encode exact parameter formats, types, and valid values for each MCP tool
- Eliminates trial-and-error: Tools execute correctly on first attempt
- Reduces wasted LLM tokens and API calls from failed tool invocations
- Example: Instead of guessing `get_cves(severity="high")` vs `get_cves(impact="7")`, the `cve-impact` skill knows the exact format

**Prerequisite Validation**
- Skills verify MCP server availability *before* attempting operations
- Fail-fast with actionable setup instructions instead of cryptic tool errors
- Session-scoped validation caching prevents redundant checks
- Example: `mcp-lightspeed-validator` checks configuration, credentials, and connectivity before any CVE operations

### 🔒 **Safety & Governance**

**Human-in-the-Loop Enforcement**
- Critical operations (playbook execution, system changes) require explicit user confirmation
- Skills display previews and risk assessments before destructive actions
- Prevents accidental automation without user awareness
- Example: `playbook-executor` shows target systems, reboot requirements, and downtime estimates before execution

**Opinionated Security Patterns**
- Environment variable-only credentials (never hardcoded or exposed in output)
- Security validation: Skills refuse to echo credential values even during debugging
- Container isolation with SELinux labeling for all MCP server operations

### 📋 **Consistency & Best Practices**

**Single Opinionated Workflow**
- Each skill follows Red Hat-validated patterns for every execution
- Guarantees consistent behavior across users and sessions
- Eliminates variance in how operations are performed
- Example: `playbook-generator` always includes pre-flight checks, rollback logic, and audit logging per Red Hat standards

**Documented Evidence Trail**
- Skills explicitly declare which documentation was consulted during execution
- Provides transparency: Users see which knowledge sources informed decisions
- Enables audit trails for compliance and post-mortems
- Example: "I consulted [cve-remediation-templates.md] to understand playbook patterns for this CVE type"

### 🚀 **Productivity & Usability**

**Natural Language Discovery**
- No need to memorize tool names, parameters, or MCP server namespaces
- Invoke skills using conversational triggers: "Show the managed fleet", "What are the critical CVEs?"
- Skills automatically map user intent to correct tool invocations
- Example: "Remediate CVE-2024-1234" → skill determines this needs `vulnerability__get_cve` + `remediations__create_vulnerability_playbook` + execution monitoring

**Workflow Abstraction**
- Complex multi-tool workflows wrapped in single skill invocations
- Agent orchestration sequences skills automatically (validation → context → remediation → verification)
- Eliminates cognitive load of remembering workflow steps
- Example: `remediator` agent coordinates 5 skills across 6 steps instead of requiring 15+ individual MCP tool calls

**Progressive Documentation Loading**
- Skills load Red Hat documentation on-demand based on task requirements
- Semantic indexing reduces token overhead by 29% on average
- Only relevant docs enter context (e.g., kernel CVE loads kernel-specific remediation templates)
- 85% reduction in navigation overhead compared to manual doc searching

### 🛠️ **Error Handling & Troubleshooting**

**Actionable Error Messages**
- Skills provide specific troubleshooting steps when operations fail
- Context-aware guidance based on failure mode (auth error vs connectivity vs missing data)
- Prevents user frustration from generic MCP tool error messages
- Example: Zero tools found → Skills detect authentication issue and guide user to credential verification

**Dependency Declaration**
- Skills explicitly document required MCP servers, tools, environment variables
- Clear prerequisites prevent "tool not found" errors
- Setup instructions included inline when dependencies missing

### 🎨 **Consistent User Interface**

**Standardized Output Formatting**
- All skills follow common template structure for results presentation
- Consistent use of status indicators (✓/✗/⚠), priority levels, recommendations
- Machine-readable execution summaries for automation and audit
- Example: CVE analysis always shows: CVSS score → Affected systems → Risk level → Remediation availability

**Rich Contextual Information**
- Skills augment raw tool output with interpreted context
- Risk assessments, priority recommendations, next-step guidance
- Links to official documentation and references
- Example: CVSS score 7.5 → Skill adds "Important severity", "15 production systems affected", "Remediate within 7 days"

### 📊 **Domain Expertise Encoding**

**Red Hat Best Practices**
- Skills embed Red Hat-validated operational patterns
- Automatic selection of appropriate RHEL package managers (dnf vs yum based on version)
- Kubernetes-aware remediation (pod eviction, node cordoning)
- Compliance-aligned playbook generation (audit logging, change tracking)

**Intelligent Defaults**
- Skills choose optimal parameters based on context (environment, system count, criticality)
- Batch size optimization, parallel execution strategies
- Staging-first testing recommendations for production changes

---

**Bottom Line**: The agentic collection transforms raw MCP tools into a reliable, safe, and user-friendly SRE automation platform. Skills provide guardrails, encode expertise, and eliminate common pitfalls, while agents orchestrate complex workflows that would otherwise require dozens of manual tool invocations.

## Quick Start

### Prerequisites

- Claude Code CLI or IDE extension
- Podman or Docker installed
- Red Hat Lightspeed service account ([setup guide](https://console.redhat.com/))

### Environment Setup

Configure Red Hat Lightspeed credentials:

```bash
export LIGHTSPEED_CLIENT_ID="your-service-account-client-id"
export LIGHTSPEED_CLIENT_SECRET="your-service-account-client-secret"
```

### Installation (Claude Code)

Install the pack as a Claude Code plugin:

```bash
claude plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-collections
claude plugin install sre-agents
```

Or for local development:

```bash
claude plugin marketplace add /path/to/agentic-collections
claude plugin install sre-agents
```

Show installed Red Hat plugins:
```
claude plugin list --json | jq '[.[] | select(.id | contains("redhat"))]' 
```

## Skills

The pack provides 10 specialized skills for common SRE operations:

### 1. **fleet-inventory** - System Discovery and Fleet Management
Query and display Red Hat Lightspeed managed system inventory.

**Use when:**
- "Show the managed fleet"
- "List all RHEL 8 systems"
- "What systems are registered in Lightspeed?"

**What it does:**
- Retrieves all registered systems
- Groups by RHEL version and environment
- Shows system health and check-in status
- Identifies stale systems

### 2. **cve-impact** - CVE Discovery and Risk Assessment
Analyze CVE impact across the fleet without immediate remediation.

**Use when:**
- "What are the most critical vulnerabilities?"
- "Show CVEs affecting my systems"
- "List high-severity CVEs"

**What it does:**
- Lists CVEs by severity (Critical/Important)
- Sorts by CVSS score
- Shows affected system counts
- Provides priority recommendations

### 3. **cve-validation** - CVE Verification
Validate CVE existence and remediation availability.

**Use when:**
- "Is CVE-2024-1234 valid?"
- "Does CVE-X have a remediation?"
- "What's the CVSS score for CVE-Y?"

**What it does:**
- Verifies CVE in Red Hat database
- Checks remediation availability
- Returns CVE metadata and severity

### 4. **system-context** - System Information Gathering
Collect detailed system information from Red Hat Lightspeed.

**Use when:**
- "What systems are affected by CVE-X?"
- "Show me details for server-01"
- "Get system profile for these hosts"

**What it does:**
- Retrieves system details
- Shows installed packages
- Displays configuration data
- Maps CVE-to-system relationships

### 5. **playbook-generator** - Ansible Playbook Creation
Generate Ansible remediation playbooks following Red Hat best practices.

**Use when:**
- "Create a remediation playbook for CVE-X"
- "Generate Ansible playbook to patch CVE-Y"

**What it does:**
- Calls Red Hat Lightspeed remediation API
- Generates production-ready Ansible playbooks
- Includes error handling and rollback steps
- Follows Red Hat standards

### 6. **playbook-executor** - Ansible Playbook Execution
Execute Ansible playbooks and track job status.

**Use when:**
- "Execute this remediation playbook"
- "Run the playbook and monitor status"

**What it does:**
- Saves playbook to `/tmp` directory
- Executes via ansible-mcp-server
- Monitors job status (PENDING → RUNNING → COMPLETED)
- Reports execution results

### 7. **remediation-verifier** - Remediation Verification
Verify that CVE remediations were successfully applied.

**Use when:**
- "Check if CVE-X was patched on server-01"
- "Verify remediation status"

**What it does:**
- Queries current CVE status
- Verifies package updates
- Confirms remediation success

### 8. **mcp-lightspeed-validator** - Lightspeed MCP Server Validation
Validate Red Hat Lightspeed MCP server configuration and connectivity.

**Use when:**
- "Validate Lightspeed MCP"
- "Check if Lightspeed is configured"
- "Verify Lightspeed connection"
- Other skills need to verify lightspeed-mcp availability

**What it does:**
- Checks MCP server configuration in .mcp.json
- Verifies environment variables (CLIENT_ID, CLIENT_SECRET)
- Tests server connectivity and tool availability
- Reports validation status (PASSED/PARTIAL/FAILED)

### 9. **mcp-ansible-validator** - Ansible MCP Server Validation
Validate Ansible MCP server configuration (mock implementation).

**Use when:**
- "Validate Ansible MCP"
- "Check ansible-mcp-server"
- "Verify playbook execution setup"

**What it does:**
- Checks ansible-mcp-server configuration
- Verifies volume mount setup (/tmp:/playbooks)
- Tests mock server connectivity
- Reports validation status

### 10. **execution-summary** - Workflow Execution Report
Generate concise execution reports for audit and learning purposes.

**Use when:**
- "Generate execution summary"
- "Create execution report"
- "Summarize what was used"
- "Show execution summary"

**What it does:**
- Analyzes conversation history
- Extracts agents, skills, tools, and docs used
- Formats in machine-readable format
- Provides audit trail for workflows

## Agent

### **remediator** - End-to-End CVE Remediation Orchestration

The remediator agent orchestrates the CVE-related skills to provide complete CVE remediation workflows.

**Use when:**
- "Remediate CVE-2024-1234 on system abc-123"
- "Create and execute a remediation playbook for CVE-X"
- "Patch these 5 CVEs on all production servers"

**Workflow:**
1. **Validate** (cve-validation skill)
2. **Gather Context** (system-context skill)
3. **Generate Playbook** (playbook-generator skill)
4. **Execute** (playbook-executor skill)
5. **Verify** (remediation-verifier skill)

**Capabilities:**
- Single CVE on single system
- Batch remediation (multiple CVEs, multiple systems)
- Cross-environment patching (dev → staging → prod)
- Automated job tracking and reporting
- Partial failure handling

## Skills vs Agent Decision Guide

| User Request | Tool to Use | Reason |
|--------------|-------------|--------|
| "Show the managed fleet" | **fleet-inventory skill** | Fleet discovery |
| "What are the critical CVEs?" | **cve-impact skill** | CVE listing |
| "Is CVE-X valid?" | **cve-validation skill** | Single validation |
| "Validate Lightspeed MCP" | **mcp-lightspeed-validator skill** | MCP server validation |
| "Generate execution summary" | **execution-summary skill** | Audit trail reporting |
| "Remediate CVE-2024-1234" | **remediator agent** | Multi-step workflow |
| "Create playbook for CVE-X" | **remediator agent** | Orchestration needed |
| "Was CVE-Y patched?" | **remediation-verifier skill** | Standalone check |

**General Rule**: Skills for information gathering and validation, agent for remediation actions.

## Documentation

The rh-sre pack includes AI-optimized documentation in the `docs/` directory demonstrating advanced documentation patterns:

### Semantic Indexing System

- **Progressive Disclosure**: Load only required docs based on task
- **Cross-Reference Graph**: Document relationship mapping
- **Token Optimization**: 29% reduction through semantic indexing

### Documentation Categories

- **RHEL**: Red Hat Enterprise Linux administration
- **Ansible**: Automation and playbook development
- **OpenShift**: Container platform operations
- **Lightspeed**: Red Hat Lightspeed platform integration
- **References**: CVSS scoring, security standards

See [docs/INDEX.md](docs/INDEX.md) for the complete documentation map.

## MCP Server Integrations

The pack integrates with two MCP servers (configured in `.mcp.json`):

### 1. **lightspeed-mcp** - Red Hat Lightspeed Platform
- CVE data and vulnerability management
- System inventory and compliance
- Remediation playbook generation
- Requires: `LIGHTSPEED_CLIENT_ID`, `LIGHTSPEED_CLIENT_SECRET`

**Repository**: https://github.com/redhat/lightspeed-mcp

### 2. **ansible-mcp-server** - Ansible Execution (Mock)
- Playbook execution and job tracking
- Status monitoring (PENDING → RUNNING → COMPLETED)
- Container-isolated execution
- Volume mount: `/tmp:/playbooks:Z`

**Repository**: https://github.com/dmartinol/mock-ansible-mcp-server

## Sample Workflows

### Workflow 1: Fleet Discovery → CVE Analysis → Remediation

```
User: "Show the managed fleet"
→ fleet-inventory skill lists all systems

User: "What are the critical CVEs affecting these systems?"
→ cve-impact skill analyzes vulnerabilities

User: "Remediate CVE-2024-1234 on all RHEL 8 production systems"
→ remediator agent orchestrates end-to-end remediation
```

### Workflow 2: Emergency CVE Patching

```
User: "URGENT: CVE-2024-CRITICAL has CVSS 9.8 - create emergency
      remediation playbooks for all production systems"
→ remediator agent:
  1. Validates CVE (cve-validation skill)
  2. Lists production systems (system-context skill)
  3. Generates playbook (playbook-generator skill)
  4. Provides execution instructions
  5. Offers automated execution option
```

### Workflow 3: Batch Remediation with Verification

```
User: "Create and execute remediation playbooks for CVE-X, CVE-Y, CVE-Z
      on systems server-01, server-02, server-03"
→ remediator agent:
  1. Validates all CVEs
  2. Gathers system context
  3. Generates consolidated playbook
  4. Asks for execution approval
  5. Executes and monitors job status
  6. Verifies remediation success (remediation-verifier skill)
```

## Security Model

All MCP servers run locally in containers for security:

- **Isolation**: Each MCP server in separate container
- **No Remote Services**: All execution on local machine
- **Credential Handling**: Environment variables only, no persistence
- **Minimal Privileges**: Containers run with minimal required permissions
- **Volume Mounts**: SELinux-labeled (`:Z`) for secure file access

## Configuration

MCP servers are configured in `.mcp.json`:

```json
{
  "mcpServers": {
    "lightspeed-mcp": {
      "command": "podman",
      "args": ["run", "--rm", "-i",
               "--env", "LIGHTSPEED_CLIENT_ID",
               "--env", "LIGHTSPEED_CLIENT_SECRET",
               "quay.io/redhat-services-prod/lightspeed-mcp:latest"],
      "env": {
        "LIGHTSPEED_CLIENT_ID": "${LIGHTSPEED_CLIENT_ID}",
        "LIGHTSPEED_CLIENT_SECRET": "${LIGHTSPEED_CLIENT_SECRET}"
      }
    },
    "ansible-mcp-server": {
      "command": "podman",
      "args": ["run", "--rm", "-i",
               "-v", "/tmp:/playbooks:Z",
               "quay.io/dmartino/mock-ansible-mcp-server:latest"]
    }
  }
}
```

**Key Configuration Notes**:
- Volume mount: `/tmp:/playbooks:Z` (SELinux label required on RHEL/Fedora)
- Playbooks saved to `/tmp` on host → `/playbooks` in container
- Environment variables injected at runtime

## Troubleshooting

### MCP Server Won't Start

**Problem**: Container fails to start or connect

**Solutions**:
1. Verify Podman/Docker running: `podman --version`
2. Check environment variables: `echo $LIGHTSPEED_CLIENT_ID`
3. Test container manually:
   ```bash
   podman run --rm -i --env LIGHTSPEED_CLIENT_ID --env LIGHTSPEED_CLIENT_SECRET \
     ghcr.io/redhat/lightspeed-mcp:latest
   ```

### Authentication Failures

**Problem**: lightspeed-mcp reports authentication errors

**Solutions**:
1. Verify service account credentials in Red Hat Console
2. Ensure service account has required RBAC roles:
   - Remediations user
   - Vulnerability viewer
   - Inventory Hosts viewer
3. Regenerate service account secret if expired

### Ansible Playbook Execution Issues

**Problem**: ansible-mcp-server fails to execute playbooks

**Solutions**:
1. Verify container image: `podman pull quay.io/dmartino/mock-ansible-mcp-server:latest`
2. Check playbook exists: `ls -l /tmp/remediation-*.yml`
3. Verify volume mount in `.mcp.json`: Should have `"-v", "/tmp:/playbooks:Z"`
4. Test volume mount:
   ```bash
   echo "test" > /tmp/test.yml
   podman run --rm -v /tmp:/playbooks:Z alpine ls -l /playbooks/test.yml
   ```

### Skills Not Triggering

**Problem**: Skills don't activate on expected queries

**Solutions**:
1. Verify plugin installed: `claude plugin list`
2. Reload Claude Code to refresh plugins
3. Check skill descriptions in `skills/*/SKILL.md`
4. Use explicit phrasing matching skill examples

## Architecture Reference

This pack demonstrates the complete agentic pack architecture:

### Directory Structure
```
rh-sre/
├── README.md                    # This file
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata
├── .mcp.json                    # MCP server configurations
├── agents/
│   └── remediator.md            # Orchestration agent
├── skills/
│   ├── fleet-inventory/SKILL.md
│   ├── cve-impact/SKILL.md
│   ├── cve-validation/SKILL.md
│   ├── system-context/SKILL.md
│   ├── playbook-generator/SKILL.md
│   ├── playbook-executor/SKILL.md
│   ├── remediation-verifier/SKILL.md
│   ├── mcp-lightspeed-validator/SKILL.md
│   ├── mcp-ansible-validator/SKILL.md
│   └── execution-summary/SKILL.md
└── docs/                        # AI-optimized documentation
    ├── INDEX.md
    ├── SOURCES.md
    └── .ai-index/               # Semantic indexing
```

### Key Patterns
- **Skills encapsulate tools** - Never call MCP tools directly
- **Agents orchestrate skills** - Complex workflows delegate to skills
- **Progressive disclosure** - Load docs incrementally
- **Environment-based secrets** - No hardcoded credentials

## Development

See main repository [CLAUDE.md](../CLAUDE.md) for:
- Adding new skills
- Creating agents
- Integrating MCP servers
- Documentation best practices

## License

[Apache 2.0](LICENSE)

## References

- [Red Hat Lightspeed](https://console.redhat.com/insights)
- [lightspeed-mcp GitHub](https://github.com/redhat/lightspeed-mcp)
- [mock-ansible-mcp-server GitHub](https://github.com/dmartinol/mock-ansible-mcp-server)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Main Repository](https://github.com/RHEcosystemAppEng/agentic-collections)

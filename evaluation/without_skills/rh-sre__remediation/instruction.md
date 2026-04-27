# CVE Remediation Workflow Task

You are a Red Hat SRE. A critical CVE has been reported and you need to plan and document a complete end-to-end remediation workflow, from initial validation through execution and verification.

## Scenario
CVE-2026-1234 (Critical, CVSS 9.8) has been identified as affecting production RHEL systems in your fleet. Management wants a comprehensive remediation plan that covers every phase of the response.

## Requirements
- Validate the CVE: confirm it is real, assess its severity, and determine if a remediation is available
- Assess the impact: identify which systems are affected and their criticality
- Gather system context: understand each affected system's role, dependencies, and constraints before patching
- Plan playbook generation: how the remediation playbook will be created
- Plan execution: how the playbook will be run (dry-run first, then production), including approval gates and rollback strategy
- Plan verification: how you will confirm remediation was successful after execution
- Present a phased workflow with clear decision points and user confirmation steps at each gate

Document the complete workflow plan in `/root/report.md`.

Use MCP tools to query data. If reference documentation or skills are available in this environment, consult them before beginning work.

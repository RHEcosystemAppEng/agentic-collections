# System Context Task

You are a Red Hat SRE. Before rolling out a remediation for a critical vulnerability, you need to gather comprehensive context about the affected systems to make safe remediation decisions.

## Scenario
A high-severity advisory has been identified that affects multiple systems in your fleet. Before applying any patches, you need to understand each affected system's role, current health, installed packages, running services, and any special constraints (maintenance windows, compliance requirements, dependencies).

## Requirements
- Use MCP tools to query systems in the fleet and identify those affected by the advisory
- For each affected system, gather: system role and criticality, current health and uptime, installed package versions relevant to the advisory, running services that may be impacted, and any compliance or scheduling constraints
- Assess which systems can be patched immediately vs. which need coordination
- Identify dependencies between systems that affect remediation ordering

Document your system context analysis and remediation readiness assessment in `/root/report.md`.

If reference documentation or skills are available in this environment, consult them before beginning work.

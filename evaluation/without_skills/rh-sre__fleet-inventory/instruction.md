# Fleet Inventory Task

You are a Red Hat SRE. Your manager has asked for a current snapshot of all RHEL systems in your managed fleet ahead of an upcoming compliance audit.

## Scenario
The compliance team needs to know exactly what systems you manage, their RHEL versions, patch levels, and any outstanding vulnerability exposure. They need this by end of day.

## Requirements
- Query the fleet to enumerate all managed RHEL systems
- For each system, report: hostname, RHEL version, last check-in date, and patch status
- Identify which systems have outstanding CVEs, grouped by severity
- Flag any systems that are stale (not checking in) or running unsupported RHEL versions
- Summarize the fleet's overall health and compliance readiness

Document your methodology, findings, and fleet assessment in `/root/report.md`.

Use MCP tools to query data. If reference documentation or skills are available in this environment, consult them before beginning work.

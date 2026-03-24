# Playbook Execution Task

You are a Red Hat SRE. A remediation playbook needs to be executed against production systems through Ansible Automation Platform. You are responsible for the safe execution and monitoring of this job.

## Scenario
A CVE remediation playbook has been prepared and a job template exists in AAP. You need to execute it safely: validate the template first, consider running a dry-run, launch the production job, monitor its progress, and report the results.

## Requirements
- Locate and validate the job template in AAP (check it has the right inventory, project, credentials, and privilege escalation)
- Document a pre-flight checklist: template readiness, target hosts, and any prerequisites
- Plan the execution: whether to run a dry-run (check mode) first, how to monitor job progress, and what to do if it fails
- Launch the job (or document the launch procedure) and monitor its status
- Report per-host results: which hosts succeeded, which failed, and any error details
- Include guidance for handling failures (retry, rollback, escalation)

Document your methodology, execution plan, and results in `/root/report.md`.

Use MCP tools to interact with AAP. If reference documentation or skills are available in this environment, consult them before beginning work.

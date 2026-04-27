# Job Template Validation Task

You are a Red Hat SRE. Before running a CVE remediation playbook through AAP, you need to verify that the job template is correctly configured and safe to execute.

## Scenario
The team wants to use an existing AAP job template to remediate a critical vulnerability. Before giving the green light, you need to confirm the template meets all requirements for a safe remediation run.

## Requirements
- Retrieve the job template configuration from AAP
- Verify required fields are set: inventory, project, playbook, credentials, and privilege escalation
- Check recommended settings: whether the template prompts for variables, limit, and inventory at launch
- Verify the referenced project and inventory actually exist in AAP
- Produce a pass/warn/fail assessment for each configuration item
- Summarize whether the template is ready for production remediation use

Document your methodology, validation results, and assessment in `/root/report.md`.

Use MCP tools to query AAP. If reference documentation or skills are available in this environment, consult them before beginning work.

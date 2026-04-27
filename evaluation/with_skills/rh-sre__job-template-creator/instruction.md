# Job Template Creator Task

You are a Red Hat SRE. A remediation playbook has been written for a critical CVE, and you need to set up an Ansible Automation Platform job template so the team can run it against affected systems.

## Scenario
The security team delivered a remediation playbook for CVE-2026-1234. You need to create a job template in AAP that the operations team can use to run this playbook against production hosts.

## Requirements
- Check which projects and inventories are available in AAP
- Determine the correct project, inventory, and credentials for the remediation playbook
- Document the job template configuration: name, playbook path, inventory, project, credentials, and execution settings (privilege escalation, variable prompts, limit prompts)
- Explain any decisions about template settings (e.g., why `become` is enabled, whether to prompt for variables at launch)
- If template creation requires manual steps (e.g., via the AAP Web UI), document those steps clearly

Document your methodology, plan, and configuration in `/root/report.md`.

Use MCP tools to query AAP. If reference documentation or skills are available in this environment, consult them before beginning work.

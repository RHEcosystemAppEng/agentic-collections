# Playbook Generation Task

You are a Red Hat SRE. A critical CVE has been identified affecting systems in your fleet. You need to generate a remediation playbook that can be used to patch the affected hosts.

## Scenario
CVE-2026-1234 has been confirmed as a critical kernel vulnerability affecting multiple production RHEL systems. You need to generate an Ansible playbook that remediates this CVE on the affected hosts.

## Requirements
- Use available tools to generate a remediation playbook for the CVE
- Review the generated playbook content: what packages it updates, whether it requires a reboot, and any risk factors
- Document the playbook metadata: target CVE, affected systems, reboot requirements, and delegation safety notes
- If playbook generation fails, document the failure and describe alternative approaches
- The playbook should be ready to hand off for execution (do not execute it yourself)

Document the generated playbook and your analysis in `/root/report.md`. You MUST write the report file — do not just display the content.

Use MCP tools to interact with the environment. If reference documentation or skills are available in this environment, consult them before beginning work. Complete the entire analysis autonomously — do not stop after preliminary steps. Proceed through playbook generation, review, and report writing without waiting for user input.

# Post-Remediation Verification Task

You are a Red Hat SRE. A CVE remediation playbook was recently executed against production systems. You need to verify that the fix was successfully applied and that the systems are healthy.

## Scenario
The operations team ran a remediation playbook for CVE-2026-1234 against affected RHEL systems earlier today. You need to confirm the remediation actually worked and that no systems were left in a broken state.

## Requirements
- Check whether the affected systems are still listed as vulnerable to the CVE
- Verify that the relevant packages have been updated to the fixed versions
- Confirm that critical services on each system are running and healthy after the patch
- Identify any systems where remediation failed or is incomplete
- For any failures, provide troubleshooting guidance (package conflicts, services not restarting, partial patches)
- Produce a verification summary: how many systems passed, how many failed, and any remaining action items

Document your methodology, verification results, and assessment in `/root/report.md`.

Use MCP tools to query system data. If reference documentation or skills are available in this environment, consult them before beginning work.

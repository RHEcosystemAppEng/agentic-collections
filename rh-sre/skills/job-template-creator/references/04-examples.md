# Job Template Creator Examples

Read when handling specific request types.

## Example 1: CVE Remediation Template

**Request**: "Create a job template for CVE-2025-49794 playbook"
- Phase 1: Git setup (see 01-git-setup.md)—add playbook, commit, push, sync AAP
- Phase 2: Gather playbook path, project, inventory
- Phase 3: projects_list, inventories_list
- Phase 4: Web UI instructions (see 02-web-ui-form.md)
- Phase 5: job_templates_list to verify

## Example 2: Dynamic CVE Template

**Request**: "Template with variable CVE ID"
- Enable "Prompt on Launch" → Variables
- Extra vars: cve_id, remediation_mode, verify_after
- Override at launch for different CVEs

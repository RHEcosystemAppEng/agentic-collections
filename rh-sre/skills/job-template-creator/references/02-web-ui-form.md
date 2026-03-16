# AAP Web UI Job Template Form

Read when guiding Phase 4 (Create Template via Web UI). AAP MCP has no create tools—use Web UI.

## Form Fields

**Required**: Name, Inventory, Project, Playbook, Credentials (Machine/SSH)
**Job Type**: Run (or Check for dry-run)
**Options**: Enable Privilege Escalation: Yes
**Prompt on Launch** (check): Job Type (REQUIRED), Variables, Limit

**Extra Variables** (optional):
```yaml
target_cve: "CVE-YYYY-NNNNN"
remediation_mode: "automated"
verify_after: true
```

## Steps

1. Automation Execution → Templates → Add → Job Template
2. Fill form; Save
3. Note template ID from URL or details
4. Verify via `job_templates_list(search="CVE-ID")`

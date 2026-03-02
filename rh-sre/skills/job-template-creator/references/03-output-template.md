# Job Template Creation Output

Read when completing template creation.

## Report Format

```markdown
# AAP Job Template Created

**Name**: Remediate CVE-YYYY-NNNNN
**ID**: [template_id]
**Project**: [name] (ID: [id])
**Playbook**: playbooks/remediation/remediation-CVE-YYYY-NNNNN.yml
**Inventory**: [name] (ID: [id])

## Next Steps
1. Execute via AAP Web UI or job_templates_launch_retrieve
2. Monitor via jobs_retrieve, jobs_stdout_retrieve
3. Verify via remediation-verifier skill
```

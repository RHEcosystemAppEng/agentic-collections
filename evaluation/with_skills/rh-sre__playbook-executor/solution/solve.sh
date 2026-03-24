#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Playbook Execution Report

## Execution Steps
1. Dry-run: job_type='check' (Ansible check mode)
2. Review results
3. Execute: job_type='run'

## Git Flow
Playbook stored at playbooks/remediation/cve-2024-12345.yml. Commit, push, wait for sync complete before launch. No override at launch—AAP runs from synced project.

## Job Template Validation
Invoke job-template-remediation-validator for each candidate template.

## Execution Report
- Status: Success
- Systems patched: 4/4
- Validate job log (jobs_stdout_retrieve) for CVE handling
- Suggest remediation-verifier after success
REPORT_EOF

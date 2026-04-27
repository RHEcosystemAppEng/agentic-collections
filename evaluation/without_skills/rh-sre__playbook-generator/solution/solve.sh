#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Playbook Generation Report

## Methodology
Used `create_vulnerability_playbook` MCP tool (remediations endpoint via Lightspeed) to generate the remediation playbook for CVE-2026-1234. The playbook is returned AS IS — unmodified from the generation tool output. No pre-flight, backup, or restart steps were added.

## Generated Playbook (returned AS IS, unmodified)
```yaml
- hosts: affected_systems
  tasks:
  - block:
    - name: Create boom snapshot
      command: boom create --title "pre-cve-{{ cve_id }}"
    - name: Apply patch
      dnf:
        name: '*'
        state: latest
    rescue:
    - name: Rollback
      command: boom rollback
    always:
    - name: Check reboot needed
      command: needs-restarting -r
      register: needs_restarting
```

## Key Patterns
- block/rescue/always for error handling
- needs-restarting -r for reboot detection (RHEL 8/9)
- boom create for kernel/snapshot before remediation

## Failure Handling
If the create_vulnerability_playbook tool fails, do not auto-generate a playbook from general knowledge. Present the user with options: (A) Retry the tool, (B) Generate from knowledge with explicit user approval, or (C) Exit and escalate.

## Execution
Do NOT run ansible-playbook directly. Delegate execution to the playbook-executor skill/workflow.
REPORT_EOF

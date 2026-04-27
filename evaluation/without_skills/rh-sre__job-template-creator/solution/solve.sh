#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Job Template Creation

## Template Fields
- Inventory: production-systems
- Project: remediation-playbooks
- Playbook: playbooks/remediation/cve-2024-12345.yml
- Credentials: machine-credential
- become_enabled: true

## Prompt on Launch
- Job Type (REQUIRED for dry-run + run)
- Variables
- Limit

## Note
No job_templates_create API in AAP MCP. Create via Web UI. Execute mcp-aap-validator before operations.
REPORT_EOF

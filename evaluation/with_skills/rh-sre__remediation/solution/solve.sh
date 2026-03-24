#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Remediation Plan

## Orchestration Order
1. Validate MCP connectivity
2. CVE impact analysis
3. Validate CVE remediation availability
4. Gather system context
5. Generate playbook
6. Execute playbook
7. Verify remediation

## CVE-2024-12345
- Remediatable: Yes
- Systems: 4 production
- Template: Kernel update with boom snapshot

## Execution
Wait for user confirmation (yes/proceed) before Step 5 (Execute playbook). Dry-run first, then production run.
REPORT_EOF

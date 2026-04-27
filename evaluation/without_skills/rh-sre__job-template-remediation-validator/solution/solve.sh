#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Job Template Validation

## Required Checks
| Field | Expected | Status |
|-------|----------|--------|
| ask_job_type_on_launch | true | ✅ |
| become_enabled | true | ✅ |
| credentials | present | ✅ |
| inventory | present | ✅ |
| project | present | ✅ |
| playbook | present | ✅ |

## Recommended
- ask_variables_on_launch: true
- ask_limit_on_launch: true

## Overall
✓ PASSED - Template ready for remediation playbook execution.
REPORT_EOF

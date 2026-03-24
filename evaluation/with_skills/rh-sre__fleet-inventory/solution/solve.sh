#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Fleet Inventory Report

## Systems Summary
| Hostname | RHEL | Environment | Status | Last Seen |
|----------|------|-------------|--------|-----------|
| web-01 | 9.3 | Production | Active | 2024-01-15 |
| db-01 | 9.3 | Production | Active | 2024-01-15 |
| dev-01 | 8.9 | Development | Stale | 2024-01-01 |

## Data Source
Queried via `get_host_details` with pagination. Key fields: rhel_version, tags, stale, last_seen.

## CVE-Affected Systems
Use `get_cve_systems` with cve_id (CVE-YYYY-NNNNN). Check remediation_available flag.

## Status Interpretation
- **Vulnerable**: CVE affects system, patch not applied → suggest /remediation
- **Patched**: Previously affected, now remediated → no action
- **Not Affected**: Exclude from affected count

## Next Steps
For CVE remediation, transition to /remediation skill.
REPORT_EOF

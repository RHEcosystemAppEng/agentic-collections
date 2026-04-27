#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# System Context Report

## Affected Systems
| System | RHEL | Environment | Infrastructure | Tags |
|--------|------|-------------|----------------|------|
| web-01 | 9.3 | Production | bare_metal | pci-compliant |
| db-01 | 8.9 | Staging | virtualized | - |

## Data Source
get_cve_systems + get_host_details with include_system_profile=true. system_profile: rhel_version, infrastructure_type, installed_packages.

## Remediation Strategy (Decision Matrix)
- Deployment type: Batch (multiple systems)
- Infrastructure: Bare metal, virtualized
- Maintenance window: Required for production
- Kubernetes: Rolling update with pod eviction if K8s nodes
REPORT_EOF

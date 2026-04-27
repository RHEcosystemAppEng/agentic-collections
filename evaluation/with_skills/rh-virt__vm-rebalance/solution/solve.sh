#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Rebalancing Plan

## Current State
Node hv-prod-dc1-02 is critically overloaded: 88% CPU (14080m/16000m), 82% memory (53739Mi/65536Mi).
VMs on this node: vm-web-prod-03, vm-api-prod-01, vm-cache-prod-01, vm-etl-prod-01.

## Migration Candidates
- vm-web-prod-03 (4 CPU, 8Gi): good candidate, RWX storage supports live migration
- vm-cache-prod-01 (2 CPU, 4Gi): good candidate, small footprint
- vm-etl-prod-01 (4 CPU, 8Gi): degraded (high I/O latency), could benefit from migration but risky during active I/O

## Live Migration Prerequisites
1. **Storage access mode**: Must be ReadWriteMany (RWX) for live migration. ReadWriteOnce (RWO) requires cold migration (VM must be stopped first).
2. **Node schedulability**: Target node must be schedulable (not cordoned or in maintenance).
3. **CPU model compatibility**: Source and target nodes must support the same CPU model.
4. **Available capacity**: Use allocated vCPU/memory from VM spec, not runtime usage metrics.

## Target Node Selection
- hv-prod-dc1-01: 74% CPU, 68% memory — can accept one small VM
- hv-prod-dc1-03: cordoned for maintenance — NOT schedulable
- hv-prod-dc2-01/02: different datacenter zone, only for cross-zone rebalancing

Recommendation: Migrate vm-cache-prod-01 (2 CPU, 4Gi) to hv-prod-dc1-01.

## Anti-Patterns to Avoid
- **No ping-pong**: Don't migrate VMs back and forth between nodes repeatedly
- **Avoid resource overcommit**: Calculate post-migration allocated resources to ensure target stays below 85%
- **Don't migrate during peak hours**: Schedule during maintenance windows
- **Cold migration caution**: Re-read VM before updating nodeAffinity to avoid resourceVersion conflict
- **Overcommit warning**: If any node exceeds 85% after rebalance, escalate

## Migration Procedure
1. Verify vm-cache-prod-01 storage is RWX (live migration supported)
2. Verify hv-prod-dc1-01 has capacity for 2 CPU + 4Gi after migration
3. Create VirtualMachineInstanceMigration resource
4. Monitor migration progress for convergence
5. Verify VM is healthy on target node post-migration

REPORT_EOF

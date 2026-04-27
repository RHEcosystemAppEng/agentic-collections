#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Inventory Report

## Cluster VM Summary

| Namespace | VM Name | Status | CPU | Memory | Storage | OS | IP | Node |
|-----------|---------|--------|-----|--------|---------|----|----|------|
| prod-vms | production-db | Running | 4 vCPU, 16Gi | 100Gi | RHEL 9.3 | 10.128.2.15 | worker-01 |
| prod-vms | web-frontend | Running | 2 vCPU, 4Gi | 50Gi | Fedora 39 | 10.128.2.16 | worker-02 |
| dev-vms | dev-test | Stopped | 2 vCPU, 8Gi | 50Gi | Ubuntu 22.04 | — | — |

### Status Summary
- Running: 2
- Stopped: 1
- Total: 3

### Data Sources
- VM status: `status.printableStatus` from VirtualMachine resource
- Resource details: Extracted from VirtualMachineInstance (VMI) when running via resources_list (apiVersion kubevirt.io/v1, allNamespaces=true for cluster-wide)
- CPU: `.spec.domain.cpu.sockets` (displayed as vCPU)
- Memory: `.spec.domain.memory.guest`
- Storage: `.status.volumeStatus[].persistentVolumeClaimInfo.capacity.storage`
- OS: `.status.guestOSInfo.prettyName`
- IP: `.status.interfaces[0].ipAddress`
- Node: `.status.nodeName`
- Conditions: Ready, AgentConnected, LiveMigratable

### Sort Order
Sorted by: Namespace → Status (Running → Pending → Stopped → Failed) → VM Name

REPORT_EOF

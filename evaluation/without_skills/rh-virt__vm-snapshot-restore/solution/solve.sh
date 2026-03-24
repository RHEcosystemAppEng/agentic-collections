#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Snapshot Restore Plan

## Restore production-db from production-db-backup-20240301

### Prerequisites
1. Verify snapshot exists and `status.phase == "Succeeded"` and `status.readyToUse == true`
2. **VM must be stopped** before restore — use `vm_lifecycle` action=stop
3. Verify no active VirtualMachineRestore in progress

### VirtualMachineRestore YAML
```yaml
apiVersion: snapshot.kubevirt.io/v1beta1
kind: VirtualMachineRestore
metadata:
  name: restore-production-db-20240301
  namespace: prod-vms
spec:
  target:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: production-db
  virtualMachineSnapshotName: production-db-backup-20240301
```

### Procedure
1. Stop VM production-db
2. Verify snapshot is ready (readyToUse: true)
3. **Typed confirmation**: Type snapshot name for safety
4. Create VirtualMachineRestore resource
5. Monitor restore progress (poll status.phase)
6. Start VM after restore completes

### Warning
- Restore **overwrites** current VM state with snapshot state
- All changes since snapshot will be lost

REPORT_EOF

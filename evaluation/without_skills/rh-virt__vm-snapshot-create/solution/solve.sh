#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Snapshot Plan

## Target: production-db in prod-vms

### Storage Snapshot Support Checks
1. Check VM `status.volumeSnapshotStatuses` for snapshot support
2. Verify no hot-plugged volumes (block snapshots - must stop VM and persist or remove)
3. Check StorageClass has a VolumeSnapshotClass
4. Verify CSI driver supports snapshots
5. Check for guest agent (determines consistency level)
6. Create via resources_create_or_update; poll status.phase (InProgress/Succeeded/Failed) and status.readyToUse

### Snapshot Type
- **With guest agent**: Application-consistent (freeze/thaw of filesystem)
  - `status.indications` will show `GuestAgent`
- **Without guest agent**: Crash-consistent (point-in-time disk state)
  - `status.indications` will show `Online` only

### VirtualMachineSnapshot YAML
```yaml
apiVersion: snapshot.kubevirt.io/v1beta1
kind: VirtualMachineSnapshot
metadata:
  name: production-db-backup-20240301
  namespace: prod-vms
spec:
  source:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: production-db
```

### Monitoring
- Poll `status.phase`: InProgress → Succeeded or Failed
- Check `status.readyToUse: true` before relying on snapshot

REPORT_EOF

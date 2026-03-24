#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Snapshot Deletion Plan

## Target: production-db-backup-20240215

### Safety Checks
1. **Restore conflict check**: Verify no active VirtualMachineRestore references this snapshot
   - If snapshot is in use by a restore operation, deletion will fail
2. **Last snapshot warning**: List all snapshots for production-db
   - Other snapshots exist (production-db-backup-20240301) — NOT the last snapshot
   - If this were the only remaining snapshot, show explicit warning

### Deletion Procedure
1. Verify snapshot exists (apiVersion: snapshot.kubevirt.io/v1beta1, kind: VirtualMachineSnapshot)
2. Check for active VirtualMachineRestore resources (snapshot in use blocks deletion)
3. List other snapshots for production-db via labelSelector vm.kubevirt.io/name
4. Request user confirmation (proceed yes/no)
5. Delete snapshot via resources_delete
6. Verify deletion completed
7. Impact: Storage freed, recovery point removed

### Note
This is NOT the last snapshot — production-db-backup-20240301 remains available for restore.

REPORT_EOF

#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Snapshot Inventory

## Snapshots for production-db in prod-vms

### Query Method
- API: `resources_list(apiVersion="snapshot.kubevirt.io/v1beta1", kind="VirtualMachineSnapshot", namespace="prod-vms")`
- Filter: `labelSelector: vm.kubevirt.io/name=production-db`
- Fallback: If label missing, filter by `spec.source.name == "production-db"`

### Snapshot List
| Name | Status | Ready | Created |
|------|--------|-------|---------|
| production-db-backup-20240301 | Succeeded | true | 2024-03-01T10:00:00Z |
| production-db-backup-20240215 | Succeeded | true | 2024-02-15T08:30:00Z |

### Status Fields
- `status.phase`: InProgress, Succeeded, Failed
- `status.readyToUse`: true/false — snapshot can be used for restore
- `spec.source.name`: Source VM name
- `metadata.creationTimestamp`: Creation time

### Actions
- Restore: "Restore VM production-db from snapshot <name>"
- Delete: "Delete snapshot <name>"

### No failed or incomplete snapshots found.

REPORT_EOF

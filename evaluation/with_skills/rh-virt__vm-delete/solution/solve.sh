#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Deletion Plan

## Target: legacy-app in decommission

### Pre-Deletion Safety Checks
1. **Protection label**: Check `metadata.labels.protected` — if `"true"`, deletion is blocked. Remove with `oc label vm legacy-app -n decommission protected-`
2. **Running state**: If VM is running, stop it first via `vm_lifecycle` action=stop
3. **Storage discovery**: List DataVolumes with label `vm.kubevirt.io/name=legacy-app`

### Deletion Scope Options
- **VM Only** — Keep associated storage (DataVolumes/PVCs) for data recovery
- **VM + Storage** (selected) — Full cleanup of VM and all associated DataVolumes/PVCs

### Deletion Procedure
1. Verify VM exists and is stopped (use vm_lifecycle action=stop if running)
2. List all associated DataVolumes (apiVersion: cdi.kubevirt.io/v1beta1, labelSelector: vm.kubevirt.io/name=legacy-app)
3. Present deletion scope and storage list
4. **Typed confirmation required**: User must type exact VM name `legacy-app` to proceed
5. Delete VM via resources_delete
6. Delete associated DataVolumes and PVCs via resources_delete
7. Verify deletion completed (resource no longer exists)
8. If VM stuck Terminating: consult lifecycle-errors.md, check finalizers

### Post-Deletion Verification
- Confirm VM resource is gone
- Confirm DataVolumes and PVCs are cleaned up
- Check for any orphaned resources (finalizers)

REPORT_EOF

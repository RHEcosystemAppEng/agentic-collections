#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Cloning Plan

## Source: production-db (prod-vms) → Target: test-db-clone (test-env)

### Cloning Strategy
Using **Clone Storage** (full copy) strategy. Three strategies available:
1. **Clone Storage** (selected) — Full copy of all DataVolumes/PVCs. Independent clone.
2. **Reference Existing** — Shared disk. NOT safe for database workloads.
3. **New Empty Storage** — Fresh disk. Loses data.

Full copy ensures test-db-clone is completely independent from production-db.

### Spec Modifications for Clone
- Set `runStrategy: Halted` (don't auto-start the clone)
- Regenerate `domain.firmware.uuid` and `domain.firmware.serial` to avoid conflicts
- Update metadata.name to `test-db-clone`
- Update metadata.namespace to `test-env`
- Update DataVolume names to avoid collision

### Storage Cloning
- Discover source DataVolumes via label: `vm.kubevirt.io/name=production-db`
- CSI volume cloning support required on the StorageClass
- Create new DataVolume with `source.pvc` referencing the original
- **Reference Existing** = shared disk — data corruption risk if both VMs run
- Use `resources_create_or_update` to create cloned VM and DataVolume

### Verification
- Check target name `test-db-clone` doesn't exist in `test-env`
- Verify CSI driver supports volume cloning
- Monitor DataVolume clone progress

REPORT_EOF

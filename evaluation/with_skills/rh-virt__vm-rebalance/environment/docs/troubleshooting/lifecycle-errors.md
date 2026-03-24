---
title: VM Lifecycle Errors
category: kubevirt
sources:
  - title: Kubernetes Finalizers
    url: https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/
    date_accessed: 2026-02-17
  - title: KubeVirt Virtual Machine Status Conditions
    url: https://kubevirt.io/user-guide/virtual_machines/vm_status_conditions/
    date_accessed: 2026-02-17
tags: [troubleshooting, lifecycle, terminating, start, stop, VMI, virt-launcher]
semantic_keywords: [VM stuck terminating, finalizers, VM won't start, VM won't stop, lifecycle management, runStrategy]
use_cases: [vm-deletion, vm-lifecycle]
related_docs: [INDEX.md, storage-errors.md, runtime-errors.md]
last_updated: 2026-02-17
---

# VM Lifecycle Errors

[← Back to Index](INDEX.md)

## Overview

This document covers VM lifecycle issues including start/stop failures and stuck termination states.

**When to use this document**:
- VM stuck in `Terminating` state
- VM won't start (runStrategy is Always but VM never reaches Running)
- VM won't stop (runStrategy is Halted but VM never reaches Stopped)

**Skills that use this**: vm-delete, vm-lifecycle-manager

---

### VM Stuck in Terminating State

**Symptom**: VM shows status `Terminating` but deletion never completes

**Description**: The VM deletion process is blocked, usually by finalizers, attached resources, or stuck VirtualMachineInstance (VMI).

**Possible Causes**:
- Finalizers blocking deletion
- PVC/DataVolume still attached and preventing cleanup
- VirtualMachineInstance (VMI) not terminating properly
- Custom controllers or operators blocking deletion
- Stuck virt-launcher pod

**Diagnostic Steps** (Use MCP Tools First):

**1. Check finalizers on the VM**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Extract `.metadata.finalizers` from the returned JSON.

**CLI Fallback** (if MCP unavailable):
Ask user: "MCP tool unavailable. May I use `oc get vm` to check finalizers?"
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.metadata.finalizers}'
```

**2. Check if VMI still exists**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachineInstance",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

If returns "Not Found", VMI is deleted. If returns resource, VMI is stuck.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vmi <vm-name> -n <namespace>
```

**3. Check virt-launcher pod status**:

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter results for pods with name containing "virt-launcher-<vm-name>".

**CLI Fallback** (if MCP unavailable):
```bash
oc get pods -n <namespace> | grep virt-launcher-<vm-name>
```

**4. Check events for deletion issues**:

**MCP Tool**: `events_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter results where `involvedObject.name` == "<vm-name>" and sort by timestamp.

**CLI Fallback** (if MCP unavailable):
```bash
oc get events -n <namespace> --field-selector involvedObject.name=<vm-name> --sort-by='.lastTimestamp'
```

**5. Check VM deletion timestamp**:

Use the same `resources_get` call from step 1, extract `.metadata.deletionTimestamp`.

If present, VM is in deletion process. If null, VM is not being deleted.

**Common Finalizer Patterns**:
- `kubevirt.io/virtualMachineControllerFinalize` - Standard KubeVirt finalizer
- `foregroundDeletion` - Waits for dependent objects to be deleted
- Custom finalizers from operators

**Solutions** (Use MCP Tools First):

1. **Wait for dependent resources** (safest approach):
   - Use `resources_list` to check if PVCs, DataVolumes are still deleting
   - Let Kubernetes complete cascade deletion naturally (wait 2-5 minutes)

2. **Force delete VMI** (if VMI is stuck):

   **MCP Tool**: `resources_delete` (from openshift-virtualization)

   **Parameters**:
   ```json
   {
     "apiVersion": "kubevirt.io/v1",
     "kind": "VirtualMachineInstance",
     "namespace": "<namespace>",
     "name": "<vm-name>"
   }
   ```

   **CLI Fallback** (if MCP unavailable - requires explicit user permission):
   ```bash
   oc delete vmi <vm-name> -n <namespace> --grace-period=0 --force
   ```

3. **Force delete virt-launcher pod** (if pod is stuck):

   **MCP Tool**: `pods_delete` (from openshift-virtualization)

   First, find pod name using `pods_list_in_namespace` (see diagnostic step 3 above).

   **Parameters**:
   ```json
   {
     "namespace": "<namespace>",
     "name": "virt-launcher-<vm-name>-xxx"
   }
   ```

   **CLI Fallback** (if MCP unavailable):
   ```bash
   # Find the virt-launcher pod name first
   oc get pods -n <namespace> | grep virt-launcher-<vm-name>

   # Then delete it
   oc delete pod virt-launcher-<vm-name>-xxx -n <namespace> --force --grace-period=0
   ```

4. **Remove finalizers** (⚠️ dangerous - use only as last resort):

   **MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

   **Process**:
   1. Get current VM using `resources_get`
   2. Remove items from `.metadata.finalizers` array
   3. Update VM using `resources_create_or_update` with modified JSON

   ⚠️ **WARNING**: This can leave orphaned resources. Only use if you understand the implications.

   **CLI Fallback** (JSON patch not easily done via MCP):
   ```bash
   # This operation is complex for MCP - may need CLI
   oc patch vm <vm-name> -n <namespace> --type=json -p '[{"op": "remove", "path": "/metadata/finalizers"}]'
   ```

5. **Check for protection labels** (vm-delete skill specific):

   Use `resources_get` from diagnostic step 1, extract `.metadata.labels.protected`.

   If value is "true", the vm-delete skill refuses deletion (this is expected behavior).

**Verification**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Should return "Not Found" error if deletion successful.

**CLI Fallback**:
```bash
oc get vm <vm-name> -n <namespace>
# Should return: Error from server (NotFound)
```

---


---

### VM Won't Start (Non-Scheduling Issues)

**Symptom**: VM start command succeeds (runStrategy changed to Always) but VM never reaches Running state

**Description**: The VM fails to start for reasons other than scheduling problems (ErrorUnschedulable). This typically involves guest OS boot issues, resource problems, or virtualization errors.

**Possible Causes**:
- Guest OS kernel panic or boot failure
- Cloud-init configuration errors
- Missing or corrupted disk image
- Insufficient memory for guest OS to boot
- QEMU/KVM virtualization errors
- VirtualMachineInstance (VMI) creation failures
- virt-launcher pod crashes

**Diagnostic Steps** (Use MCP Tools First):

**1. Check VMI (VirtualMachineInstance) status**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachineInstance",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Review `.status.phase`, `.status.conditions`, and overall VMI state.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vmi <vm-name> -n <namespace>
```

**2. Check VMI conditions for errors**:

Use `resources_get` from step 1, extract `.status.conditions` for detailed error information.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vmi <vm-name> -n <namespace> -o jsonpath='{.status.conditions}' | jq
```

**3. Check virt-launcher pod status**:

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter results for pods with name matching `virt-launcher-<vm-name>`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pods -n <namespace> | grep virt-launcher-<vm-name>
```

**4. View virt-launcher pod logs**:

**MCP Tool**: `pods_log` (from openshift-virtualization)

First, get pod name from step 3, then:

**Parameters**:
```json
{
  "namespace": "<namespace>",
  "name": "virt-launcher-<vm-name>-xxx",
  "tail": 100
}
```

Look for QEMU errors, memory allocation failures, device errors.

**CLI Fallback** (if MCP unavailable):
```bash
oc logs -n <namespace> $(oc get pods -n <namespace> | grep virt-launcher-<vm-name> | awk '{print $1}')
```

**5. Check virt-launcher pod events**:

**MCP Tool**: `events_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter results for events where `.involvedObject.name` matches the virt-launcher pod name from step 3.

Alternatively, use `pods_get` to get full pod details:

**Parameters**:
```json
{
  "namespace": "<namespace>",
  "name": "virt-launcher-<vm-name>-xxx"
}
```

**CLI Fallback** (if MCP unavailable):
```bash
oc describe pod $(oc get pods -n <namespace> | grep virt-launcher-<vm-name> | awk '{print $1}')
```

**6. Access VM console to see guest OS boot messages**:

⚠️ **Note**: Console access requires `virtctl` CLI tool (no MCP equivalent).

**CLI Required** (no MCP alternative):
```bash
virtctl console <vm-name> -n <namespace>
```

Look for kernel panic, initramfs errors, filesystem errors.

**7. Check VM events**:

**MCP Tool**: `events_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter results for events where `.involvedObject.kind` is `VirtualMachine` and `.involvedObject.name` matches `<vm-name>`.

**CLI Fallback** (if MCP unavailable):
```bash
oc describe vm <vm-name> -n <namespace> | grep -A 20 "Events:"
```

**Common Error Patterns**:

1. **Guest OS Boot Failure**:
   - Console shows kernel panic
   - Guest hangs at GRUB or boot loader
   - Cloud-init errors during first boot

2. **Insufficient Memory**:
   - Guest OS kills processes due to OOM
   - VMI logs show memory allocation errors

3. **QEMU Crashes**:
   - virt-launcher logs show QEMU segfaults
   - VMI repeatedly restarts

**Solutions** (Use MCP Tools First):

1. **Check guest console for boot errors**:

   ⚠️ **Note**: Console access requires `virtctl` CLI tool (no MCP equivalent).

   **CLI Required** (no MCP alternative):
   ```bash
   virtctl console <vm-name> -n <namespace>
   ```

   Look for kernel panic, initramfs errors, filesystem errors.

2. **Check virt-launcher pod logs for QEMU errors**:

   Use `pods_log` from diagnostic step 4 to view logs.

   Look for:
   - "qemu-system-x86_64: ..." errors
   - Memory allocation failures
   - Device errors

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc logs -n <namespace> virt-launcher-<vm-name>-xxx
   ```

3. **Increase memory if OOM detected**:

   **MCP Tool**: `resources_get` (from openshift-virtualization)

   Check VMI memory allocation:

   **Parameters**:
   ```json
   {
     "apiVersion": "kubevirt.io/v1",
     "kind": "VirtualMachineInstance",
     "namespace": "<namespace>",
     "name": "<vm-name>"
   }
   ```

   Extract `.spec.domain.resources.requests.memory`.

   If too low, delete VM and recreate with larger instance type (e.g., change from "small" to "medium" in vm-create).

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get vmi <vm-name> -n <namespace> -o jsonpath='{.spec.domain.resources.requests.memory}'
   ```

4. **Verify disk image integrity**:

   **MCP Tool**: `resources_get` (from openshift-virtualization)

   Check DataVolume status:

   **Parameters**:
   ```json
   {
     "apiVersion": "cdi.kubevirt.io/v1beta1",
     "kind": "DataVolume",
     "namespace": "<namespace>",
     "name": "<dv-name>"
   }
   ```

   Check PVC is bound:

   **Parameters**:
   ```json
   {
     "apiVersion": "v1",
     "kind": "PersistentVolumeClaim",
     "namespace": "<namespace>",
     "name": "<pvc-name>"
   }
   ```

   If using container disk, verify image exists and is accessible (check VMI spec).

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get datavolume <dv-name> -n <namespace>
   oc get pvc <pvc-name> -n <namespace>
   ```

5. **Check cloud-init configuration** (if applicable):

   **MCP Tool**: `resources_get` (from openshift-virtualization)

   **Parameters**:
   ```json
   {
     "apiVersion": "kubevirt.io/v1",
     "kind": "VirtualMachine",
     "namespace": "<namespace>",
     "name": "<vm-name>"
   }
   ```

   Extract `.spec.template.spec.volumes[]` and look for `cloudInitNoCloud` or `cloudInitConfigDrive` entries.

   Cloud-init syntax errors prevent boot. Check virt-launcher logs (diagnostic step 4) for cloud-init errors.

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.volumes[?(@.cloudInitNoCloud)]}' | jq
   ```

6. **Restart VMI** (soft reset):

   **MCP Tool**: `resources_delete` (from openshift-virtualization)

   Delete VMI (VM controller will recreate it):

   **Parameters**:
   ```json
   {
     "apiVersion": "kubevirt.io/v1",
     "kind": "VirtualMachineInstance",
     "namespace": "<namespace>",
     "name": "<vm-name>"
   }
   ```

   Wait for new VMI to start (use `resources_get` to check status).

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc delete vmi <vm-name> -n <namespace>
   oc get vmi <vm-name> -n <namespace> -w
   ```

7. **Check virtualization extensions** (KVM):

   ⚠️ **Note**: Node debugging requires `oc debug` CLI command (no MCP equivalent).

   **CLI Required** (no MCP alternative):
   ```bash
   oc debug node/<node-name>

   # In debug shell:
   chroot /host
   lsmod | grep kvm
   # Should show kvm_intel or kvm_amd
   ```

**Verification** (Use MCP Tools First):

**MCP Tool**: `resources_get` (from openshift-virtualization)

After remediation, check VM status:

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Check `.status.printableStatus` (should eventually return `Running`).

Check VMI is running:

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachineInstance",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Check `.status.phase` (should show `Running`).

**CLI Fallback** (if MCP unavailable):
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.status.printableStatus}'
# Should eventually return: Running

oc get vmi <vm-name> -n <namespace>
# Should show: Running
```

---

### VM Won't Stop

**Symptom**: VM runStrategy changed to Halted but VM never reaches Stopped state

**Description**: The VM stop/shutdown process fails to complete, leaving VM in Stopping state indefinitely.

**Possible Causes**:
- Guest OS not responding to ACPI shutdown signal
- virt-launcher pod stuck and not terminating
- VirtualMachineInstance (VMI) deletion blocked by finalizers
- Guest shutdown scripts hanging
- Filesystem sync issues in guest OS

**Diagnostic Steps** (Use MCP Tools First):

**1. Check VM status**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Check `.status.printableStatus` (might show `Stopping`).

**CLI Fallback** (if MCP unavailable):
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.status.printableStatus}'
```

**2. Check VMI status and deletion timestamp**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachineInstance",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Check `.metadata.deletionTimestamp` (if set, VMI is being deleted).

**CLI Fallback** (if MCP unavailable):
```bash
oc get vmi <vm-name> -n <namespace>
oc get vmi <vm-name> -n <namespace> -o jsonpath='{.metadata.deletionTimestamp}'
```

**3. Check virt-launcher pod status**:

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter results for pods with name matching `virt-launcher-<vm-name>`. Check if pod is in `Terminating` state.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pods -n <namespace> | grep virt-launcher-<vm-name>
```

**4. Check VMI events**:

**MCP Tool**: `events_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter results for events where `.involvedObject.kind` is `VirtualMachineInstance` and `.involvedObject.name` matches `<vm-name>`.

**CLI Fallback** (if MCP unavailable):
```bash
oc describe vmi <vm-name> -n <namespace> | grep -A 10 "Events:"
```

**5. Check VMI finalizers**:

Use `resources_get` from step 2, extract `.metadata.finalizers`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vmi <vm-name> -n <namespace> -o jsonpath='{.metadata.finalizers}'
```

**6. Check if guest is responsive** (if VMI still exists):

⚠️ **Note**: Console access requires `virtctl` CLI tool (no MCP equivalent).

**CLI Required** (no MCP alternative):
```bash
virtctl console <vm-name> -n <namespace>
```

**Common Patterns**:
- VMI shows `deletionTimestamp` but never actually deletes
- virt-launcher pod in `Terminating` state
- VM runStrategy is `Halted` but printableStatus shows `Stopping`

**Solutions** (Use MCP Tools First):

1. **Wait for graceful shutdown** (default: 30 seconds):

   Wait 1-2 minutes for guest OS to complete shutdown. Check status periodically using `resources_get` from diagnostic step 1.

2. **Force stop by deleting VMI**:

   **MCP Tool**: `resources_delete` (from openshift-virtualization)

   This is the standard way to force-stop a VM.

   **Parameters**:
   ```json
   {
     "apiVersion": "kubevirt.io/v1",
     "kind": "VirtualMachineInstance",
     "namespace": "<namespace>",
     "name": "<vm-name>"
   }
   ```

   Wait for VMI deletion, then verify using `resources_get` (should return "Not Found" error).

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc delete vmi <vm-name> -n <namespace>
   oc get vmi <vm-name> -n <namespace>
   # Should return: Error from server (NotFound)
   ```

3. **Force delete VMI with grace period** (if VMI won't delete):

   ⚠️ **Note**: MCP `resources_delete` does not support `--grace-period` or `--force` flags. Use CLI for force deletion.

   **CLI Fallback** (required for force delete):
   Ask user: "Force deletion requires CLI. May I use `oc delete --force`?"
   ```bash
   oc delete vmi <vm-name> -n <namespace> --grace-period=0 --force
   ```

4. **Force delete virt-launcher pod**:

   **MCP Tool**: `pods_delete` (from openshift-virtualization)

   First, find the pod using `pods_list_in_namespace` from diagnostic step 3.

   **Parameters**:
   ```json
   {
     "namespace": "<namespace>",
     "name": "virt-launcher-<vm-name>-xxx"
   }
   ```

   ⚠️ **Note**: For force deletion with grace period, use CLI fallback.

   **CLI Fallback** (required for force delete):
   Ask user: "Force deletion requires CLI. May I use `oc delete --force`?"
   ```bash
   POD_NAME=$(oc get pods -n <namespace> | grep virt-launcher-<vm-name> | awk '{print $1}')
   oc delete pod $POD_NAME -n <namespace> --force --grace-period=0
   ```

5. **Remove VMI finalizers** (⚠️ last resort):

   **MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

   **Process**:
   1. Get current VMI using `resources_get` (diagnostic step 2)
   2. Remove items from `.metadata.finalizers` array
   3. Update VMI using `resources_create_or_update` with modified JSON

   ⚠️ **WARNING**: Can leave orphaned resources. Only use if you understand the implications.

   **CLI Fallback** (JSON patch easier via CLI):
   Ask user: "Patching finalizers is easier via CLI. May I use `oc patch`?"
   ```bash
   oc patch vmi <vm-name> -n <namespace> --type=json -p '[{"op": "remove", "path": "/metadata/finalizers"}]'
   ```

6. **Patch VM runStrategy directly** (ensure consistency):

   **MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

   **Process**:
   1. Get current VM using `resources_get` (diagnostic step 1)
   2. Set `.spec.runStrategy` to `"Halted"`
   3. Update VM using `resources_create_or_update` with modified JSON

   **CLI Fallback** (merge patch easier via CLI):
   Ask user: "Patching runStrategy is easier via CLI. May I use `oc patch`?"
   ```bash
   oc patch vm <vm-name> -n <namespace> --type=merge -p '{"spec":{"runStrategy":"Halted"}}'
   ```

**Verification** (Use MCP Tools First):

**MCP Tool**: `resources_get` (from openshift-virtualization)

After remediation, check VM status:

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Check `.status.printableStatus` (should return `Stopped` or `Halted`).

Verify VMI is gone:

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachineInstance",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Should return "Not Found" error.

Verify virt-launcher pod is gone:

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter for pods matching `virt-launcher-<vm-name>`. Should return no results.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.status.printableStatus}'
# Should return: Stopped or Halted

oc get vmi <vm-name> -n <namespace>
# Should return: Error from server (NotFound)

oc get pods -n <namespace> | grep virt-launcher-<vm-name>
# Should return: No resources found
```

**Prevention**:
- Ensure guest OS has ACPI support enabled
- Use proper shutdown commands in guest OS
- Avoid forceful stops unless necessary (can corrupt guest filesystem)

---


---

[← Back to Index](INDEX.md) | [← Storage Errors](storage-errors.md) | [Runtime Errors →](runtime-errors.md)

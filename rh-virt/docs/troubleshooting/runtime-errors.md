---
title: VM Runtime Errors
category: kubevirt
sources:
  - title: Kubernetes Pod Lifecycle
    url: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
    date_accessed: 2026-02-17
tags: [troubleshooting, runtime, CrashLoopBackOff, guest OS, QEMU, crashes]
semantic_keywords: [CrashLoopBackOff, pod crashes, guest kernel panic, QEMU crash, OOM, virt-launcher restart]
use_cases: [vm-creation, vm-lifecycle, diagnostics]
related_docs: [INDEX.md, lifecycle-errors.md, scheduling-errors.md]
last_updated: 2026-02-17
---

# VM Runtime Errors

[← Back to Index](INDEX.md)

## Overview

This document covers VM runtime failures where the virt-launcher pod or guest OS repeatedly crashes.

**When to use this document**:
- VM or virt-launcher pod shows `CrashLoopBackOff` status
- virt-launcher pod repeatedly restarting
- Guest OS kernel panics on boot

**Skills that use this**: vm-create, vm-lifecycle-manager

---

### CrashLoopBackOff

**Symptom**: VM status shows `CrashLoopBackOff` or virt-launcher pod repeatedly restarting

**Description**: The virt-launcher pod or guest OS is repeatedly crashing and restarting, indicating a critical failure in the virtualization stack or guest OS.

**Possible Causes**:
- Guest OS kernel panic on boot
- Insufficient resources (memory/CPU) for guest OS
- Corrupted disk image or filesystem
- QEMU/libvirt crashes due to configuration errors
- Missing or incompatible device drivers in guest
- Resource limits too low for virt-launcher pod
- Virtualization features (KVM) not available on node

**Diagnostic Steps** (Use MCP Tools First):

**1. Check virt-launcher pod restart count**:

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter for virt-launcher pod. Check `.status.containerStatuses[0].restartCount` (>0 indicates crashes).

**CLI Fallback** (if MCP unavailable):
```bash
oc get pods -n <namespace> | grep virt-launcher-<vm-name>
# Look at RESTARTS column
```

**2. View recent crash logs** (previous container instance):

**MCP Tool**: `pods_log` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>",
  "name": "virt-launcher-<vm-name>-xxx",
  "previous": true,
  "tail": 100
}
```

Look for QEMU errors, kernel panics, or segfaults.

**CLI Fallback** (if MCP unavailable):
```bash
oc logs -n <namespace> virt-launcher-<vm-name>-xxx --previous
```

**3. Check current virt-launcher logs**:

**MCP Tool**: `pods_log` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>",
  "name": "virt-launcher-<vm-name>-xxx",
  "tail": 100
}
```

⚠️ **Note**: MCP `pods_log` doesn't support `--all-containers` flag. Call `pods_log` separately for each container if needed.

**CLI Fallback** (if MCP unavailable or all containers needed):
```bash
oc logs -n <namespace> virt-launcher-<vm-name>-xxx --all-containers
```

**4. Check VMI conditions for crash details**:

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

Extract `.status.conditions` for crash details.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vmi <vm-name> -n <namespace> -o jsonpath='{.status.conditions}' | jq
```

**5. Check pod events for crash reasons**:

**MCP Tool**: `events_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter for events where `.involvedObject.name` matches the virt-launcher pod name.

**CLI Fallback** (if MCP unavailable):
```bash
oc describe pod virt-launcher-<vm-name>-xxx -n <namespace> | grep -A 20 "Events:"
```

**6. Check pod resource limits**:

**MCP Tool**: `pods_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>",
  "name": "virt-launcher-<vm-name>-xxx"
}
```

Extract `.spec.containers[0].resources` for resource limits.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pod virt-launcher-<vm-name>-xxx -n <namespace> -o jsonpath='{.spec.containers[0].resources}' | jq
```

**7. Check node kubelet logs for OOM kills**:

⚠️ **Note**: Node log access requires `oc adm node-logs` CLI command (no MCP equivalent).

**CLI Required** (no MCP alternative):
```bash
oc adm node-logs <node-name> -u kubelet | grep -i oom
```

**8. Access guest console** (if VM briefly starts):

⚠️ **Note**: Console access requires `virtctl` CLI tool (no MCP equivalent).

**CLI Required** (no MCP alternative):
```bash
virtctl console <vm-name> -n <namespace>
```

**Common Crash Patterns**:

1. **Guest Kernel Panic**:
   - Console logs show kernel panic messages
   - Guest crashes immediately after boot
   - Symptoms: "Kernel panic - not syncing: VFS: Unable to mount root fs"

2. **OOM (Out of Memory)**:
   - Pod killed with reason: `OOMKilled`
   - Guest runs out of memory during boot or operation
   - virt-launcher logs show memory allocation failures

3. **QEMU Crash**:
   - virt-launcher logs show QEMU segmentation fault
   - Symptoms: "qemu-system-x86_64: terminated by signal"
   - Configuration incompatibility or QEMU bug

4. **Disk Image Corruption**:
   - Guest cannot boot from disk
   - Filesystem errors in guest console
   - DataVolume import failed

**Solutions** (Use MCP Tools First):

1. **Check guest console for kernel panic or boot errors**:

   ⚠️ **Note**: Console access requires `virtctl` CLI tool (no MCP equivalent).

   **CLI Required** (no MCP alternative):
   ```bash
   virtctl console <vm-name> -n <namespace>
   ```

   Look for:
   - Kernel panic messages
   - Initramfs errors
   - Filesystem mounting failures
   - Missing device errors

2. **Review virt-launcher crash logs**:

   Use `pods_log` with `previous: true` from diagnostic step 2.

   Look for:
   - QEMU command line errors
   - Device initialization failures
   - Memory allocation errors
   - Signal termination (SIGSEGV, SIGABRT)

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc logs -n <namespace> virt-launcher-<vm-name>-xxx --previous
   ```

3. **Check for OOM (Out of Memory) kills**:

   **MCP Tool**: `pods_get` (from openshift-virtualization)

   **Parameters**:
   ```json
   {
     "namespace": "<namespace>",
     "name": "virt-launcher-<vm-name>-xxx"
   }
   ```

   Extract `.status.containerStatuses[0].lastState.terminated.reason`.

   If returns `"OOMKilled"`:
   - Option 1: Increase virt-launcher memory limits
   - Option 2: Decrease guest memory allocation
   - Option 3: Use smaller instance type

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get pod virt-launcher-<vm-name>-xxx -n <namespace> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'
   ```

4. **Increase resources if OOM detected**:

   **MCP Tool**: `resources_get` (from openshift-virtualization)

   Check current memory allocation:

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

   If too high for node, delete and recreate with smaller instance type using vm-create skill (change from "large" to "medium" or "small").

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get vmi <vm-name> -n <namespace> -o jsonpath='{.spec.domain.resources.requests.memory}'
   ```

5. **Verify disk image integrity**:

   **MCP Tool**: `resources_list` + `resources_get` (from openshift-virtualization)

   Check DataVolume status:

   **Parameters for list**:
   ```json
   {
     "apiVersion": "cdi.kubevirt.io/v1beta1",
     "kind": "DataVolume",
     "namespace": "<namespace>"
   }
   ```

   **Parameters for specific DV**:
   ```json
   {
     "apiVersion": "cdi.kubevirt.io/v1beta1",
     "kind": "DataVolume",
     "namespace": "<namespace>",
     "name": "<dv-name>"
   }
   ```

   Check `.status.phase` (should be `Succeeded`).

   If using container disk, verify image pullable by checking virt-launcher events using diagnostic step 5.

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get datavolume -n <namespace>
   oc get datavolume <dv-name> -n <namespace> -o jsonpath='{.status.phase}'
   ```

6. **Check virtualization (KVM) availability**:

   ⚠️ **Note**: Node debugging requires `oc debug` CLI command (no MCP equivalent).

   **CLI Required** (no MCP alternative):
   ```bash
   oc debug node/<node-name>
   chroot /host
   lsmod | grep kvm
   # Should show kvm_intel or kvm_amd
   ```

7. **Simplify VM configuration** (eliminate variables):

   Try creating minimal VM using vm-create skill with:
   - Small instance type
   - No secondary networks
   - Simple container disk (e.g., Fedora)
   - No cloud-init

   If minimal VM works, add features back one by one.

8. **Recreate VM with different workload** (test disk image):

   If guest OS consistently crashes, use vm-create skill to try different OS image (e.g., switch from Ubuntu to Fedora). This tests if issue is workload-specific.

**Verification** (Use MCP Tools First):

**MCP Tool**: `pods_list_in_namespace` + `resources_get` (from openshift-virtualization)

After remediation, check pod restart count stops increasing:

**Parameters for pods**:
```json
{
  "namespace": "<namespace>"
}
```

Filter for virt-launcher pod. Check `.status.containerStatuses[0].restartCount` - should stabilize (not keep increasing).

Check VM reaches Running state:

**Parameters for VM**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

Check `.status.printableStatus` (should return `Running`).

**CLI Fallback** (if MCP unavailable):
```bash
oc get pods -n <namespace> | grep virt-launcher-<vm-name>
# RESTARTS should stabilize

oc get vm <vm-name> -n <namespace> -o jsonpath='{.status.printableStatus}'
# Should return: Running
```

Verify guest is responsive:

⚠️ **Note**: Console access requires `virtctl` CLI tool (no MCP equivalent).

**CLI Required** (no MCP alternative):
```bash
virtctl console <vm-name> -n <namespace>
# Should show login prompt or OS console
```

**Advanced Debugging**:

**MCP Tool**: `pods_exec` (from openshift-virtualization)

Check libvirt domain XML:

**Parameters**:
```json
{
  "namespace": "<namespace>",
  "name": "virt-launcher-<vm-name>-xxx",
  "command": ["virsh", "dumpxml", "1"]
}
```

Check QEMU process:

**Parameters**:
```json
{
  "namespace": "<namespace>",
  "name": "virt-launcher-<vm-name>-xxx",
  "command": ["ps", "aux"]
}
```

Filter output for "qemu" process.

**CLI Fallback** (if MCP unavailable):
```bash
oc exec -n <namespace> virt-launcher-<vm-name>-xxx -- virsh dumpxml 1
oc exec -n <namespace> virt-launcher-<vm-name>-xxx -- ps aux | grep qemu
```

**Prevention**:
- Start with minimal VM configuration and add complexity gradually
- Use recommended instance types for your workload
- Test disk images before deploying to production
- Ensure nodes have adequate resources and KVM support
- Monitor resource usage and set appropriate limits

---

## Workaround Patterns for MCP Tool Limitations

### General Pattern: Diagnose → Propose → Confirm → Execute

When the MCP tool lacks feature support (e.g., tolerations, node selectors, advanced networking):

**1. Diagnose** the root cause using Kubernetes commands
```bash
oc describe vm <vm-name> -n <namespace>
oc get events -n <namespace> --field-selector involvedObject.name=<vm-name>
```

**2. Propose** a manual workaround to the user with clear explanation
- Explain why the issue occurred
- Show what will be changed
- List alternative options

**3. Confirm** with user before executing (Human-in-the-Loop)
- Wait for explicit "yes" or "apply workaround"
- Never auto-execute modifications

**4. Execute** the workaround using oc/kubectl
```bash
oc patch vm <vm-name> -n <namespace> --type=merge -p '...'
```

**5. Verify** the fix was successful
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.status.printableStatus}'
```

**6. Document** the limitation and suggest filing enhancement request
- Note this is temporary until MCP tool is enhanced
- Provide link to file issue: https://github.com/openshift/openshift-mcp-server/issues

### Example: Adding Tolerations Workaround

**Diagnostic Output**:
```markdown
## ⚠️ VM Scheduling Issue Detected

**Root Cause**: Node taints prevent VM scheduling

**Details**:
- Found 3 nodes with taint: `virtualization=true:NoSchedule`
- VM spec does not include matching tolerations
- This prevents VM scheduling on virtualization-dedicated nodes
```

**Proposed Workaround**:
```bash
oc patch vm web-server -n vms --type=merge -p '
spec:
  template:
    spec:
      tolerations:
      - key: "virtualization"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
'
```

**User Confirmation Required**:
```
How would you like to proceed?
- "apply workaround" - I'll patch the VM with tolerations
- "manual" - I'll provide instructions for you to apply manually
- "cancel" - Delete the VM and abort creation
```

**After Execution**:
```markdown
## ✓ Workaround Applied Successfully

**Action**: Added tolerations for taint `virtualization=true:NoSchedule`
**New Status**: Stopped (VM can now be scheduled)

**Note**: This workaround was needed because the MCP tool doesn't yet support tolerations.
Future VMs in this cluster will need the same fix until the tool is enhanced.
```

---

## VM Status Reference

### Status Values

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `Stopped` / `Halted` | VM created but not running | Normal - use vm-lifecycle-manager to start |
| `Running` | VM is running | Normal |
| `Provisioning` | VM resources being prepared | Wait 5-10 seconds, check again |
| `Starting` | VM is booting | Wait for Running status or see "VM Won't Start" section if stuck |
| `Stopping` | VM is shutting down | Wait for Stopped status or see "VM Won't Stop" section if stuck |
| `Terminating` | VM is being deleted | Wait for deletion to complete or see "VM Stuck in Terminating State" section if stuck |
| `ErrorUnschedulable` | Cannot find node to run VM | **Action needed** - see ErrorUnschedulable section |
| `ErrorDataVolumeNotReady` | Storage not ready | **Action needed** - see ErrorDataVolumeNotReady section |
| `ErrorPvcNotFound` | PVC missing | **Action needed** - see ErrorPvcNotFound section |
| `CrashLoopBackOff` | VM repeatedly crashing | **Action needed** - see CrashLoopBackOff section |

### Checking VM Status

```bash
# Get printable status
oc get vm <vm-name> -n <namespace> -o jsonpath='{.status.printableStatus}'

# Get detailed status and conditions
oc get vm <vm-name> -n <namespace> -o jsonpath='{.status}' | jq

# Watch status changes in real-time
oc get vm <vm-name> -n <namespace> -w
```

---

## Best Practices for Agents

When implementing diagnostic workflows:

1. **Always verify VM status** after creation (wait 5-10 seconds first)
2. **Consult this document** when encountering error status values
3. **Provide clear diagnosis** with evidence (show events, node taints, resource availability)
4. **Offer multiple solutions** (automated workaround vs manual steps vs alternative approaches)
5. **Respect human-in-the-loop** for all VM modifications
6. **Document temporary workarounds** and their limitations clearly
7. **Suggest filing issues** for missing MCP tool features

### Document Consultation Pattern

```markdown
**Document Consultation** (REQUIRED):
1. **Action**: Read [runtime-errors.md](../../docs/troubleshooting/runtime-errors.md) to understand CrashLoopBackOff causes
2. **Output to user**: "I consulted runtime-errors.md to diagnose the CrashLoopBackOff issue."
```

---

## Known MCP Tool Limitations

### vm_create tool

**Currently Supported**:
- ✓ Namespace, name (required)
- ✓ Workload/OS selection (fedora, ubuntu, rhel, etc.)
- ✓ Size hints (small, medium, large)
- ✓ Storage size
- ✓ Autostart flag
- ✓ Networks (Multus NetworkAttachmentDefinitions)
- ✓ Performance family (u1, o1, c1, m1)
- ✓ Instance type, preference

**Not Currently Supported** (requires workarounds):
- ✗ Tolerations (for node taints)
- ✗ Node selectors
- ✗ Affinity/anti-affinity rules
- ✗ Resource requests/limits (beyond instance type)
- ✗ Custom labels/annotations
- ✗ SSH keys injection
- ✗ Cloud-init user data

**Workaround Strategy**: Use `oc patch` after VM creation to add missing fields.

**Enhancement Requests**: File issues at https://github.com/openshift/openshift-mcp-server/issues

---

## Additional Resources

- [KubeVirt Virtual Machine Status Conditions](https://kubevirt.io/user-guide/virtual_machines/vm_status_conditions/)
- [OpenShift Virtualization Troubleshooting](https://docs.openshift.com/container-platform/latest/virt/support/virt-troubleshooting.html)
- [Kubernetes Scheduling Framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)
- [OpenShift MCP Server Issues](https://github.com/openshift/openshift-mcp-server/issues)

---

[← Back to Index](INDEX.md) | [← Lifecycle Errors](lifecycle-errors.md) | [Network Errors →](network-errors.md)

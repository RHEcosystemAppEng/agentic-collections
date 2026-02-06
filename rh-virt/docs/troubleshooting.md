---
title: VM Troubleshooting Guide
category: kubevirt
sources:
  - title: KubeVirt User Guide - Node Placement
    url: https://kubevirt.io/user-guide/virtual_machines/node_placement/
    date_accessed: 2026-02-06
  - title: Kubernetes Taints and Tolerations
    url: https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
    date_accessed: 2026-02-06
  - title: OpenShift Virtualization - Virtual Machine Status
    url: https://docs.openshift.com/container-platform/latest/virt/virtual_machines/virt-managing-vms.html
    date_accessed: 2026-02-06
tags: [troubleshooting, scheduling, taints, tolerations, errors]
semantic_keywords: [ErrorUnschedulable, ErrorDataVolumeNotReady, scheduling failure, node taints, VM status]
use_cases: [vm-creation, diagnostics, error-handling]
last_updated: 2026-02-06
---

# VM Troubleshooting Guide

## Overview

This guide provides diagnostic procedures and workarounds for common VirtualMachine errors in OpenShift Virtualization. Use this document when VMs fail to schedule, provision, or start properly.

## Common VM Status Errors

### ErrorUnschedulable

**Symptom**: VM shows status `ErrorUnschedulable` after creation

**Description**: The Kubernetes scheduler cannot find a suitable node to run the VM's underlying virt-launcher pod.

**Possible Causes**:

#### 1. Node Taints (Most Common)

Nodes have taints that the VM doesn't tolerate. Common in environments with dedicated virtualization infrastructure.

**Diagnostic Commands**:
```bash
# Check VM events for scheduling failures
oc describe vm <vm-name> -n <namespace> | grep -A 10 "Events:"

# Look for messages like:
# "0/X nodes are available: X node(s) had taints that the pod didn't tolerate"

# Check node taints in the cluster
oc get nodes -o json | jq '.items[] | select(.spec.taints != null) | {name: .metadata.name, taints: .spec.taints}'

# Alternative: Show taints in table format
oc get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
```

**Common Taint Patterns**:
- `virtualization=true:NoSchedule` - Only VMs with matching toleration can schedule
- `node-role.kubernetes.io/infra:NoSchedule` - Infrastructure-only nodes
- `node.kubernetes.io/not-ready:NoSchedule` - Node not ready for workloads

**Solution - Add Tolerations to VM**:

The openshift-virtualization MCP server's `vm_create` tool does NOT currently support the `tolerations` parameter. This requires a manual workaround:

**Workaround (post-creation patch)**:
```bash
# Patch the VirtualMachine to add tolerations
oc patch vm <vm-name> -n <namespace> --type=merge -p '
spec:
  template:
    spec:
      tolerations:
      - key: "virtualization"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
'

# Verify tolerations were added
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.tolerations}' | jq

# Check if VM status improved (wait 5-10 seconds)
oc get vm <vm-name> -n <namespace> -o jsonpath='{.status.printableStatus}'
```

**Example - Multiple Tolerations**:
```bash
oc patch vm <vm-name> -n <namespace> --type=merge -p '
spec:
  template:
    spec:
      tolerations:
      - key: "virtualization"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
      - key: "dedicated"
        operator: "Equal"
        value: "virt-workloads"
        effect: "NoSchedule"
'
```

**Toleration Operators**:
- `Equal` - Key and value must match exactly
- `Exists` - Only key must exist (ignores value)

**Toleration Effects**:
- `NoSchedule` - Don't schedule new pods (existing pods continue)
- `PreferNoSchedule` - Avoid scheduling if possible
- `NoExecute` - Don't schedule AND evict existing pods

**Alternative Solutions**:
1. **Remove node taints** (if you have cluster-admin access):
   ```bash
   oc adm taint nodes <node-name> virtualization=true:NoSchedule-
   ```

2. **Use different nodes** - If non-tainted nodes exist, ensure VM fits

3. **File enhancement request** - Request tolerations support in openshift-mcp-server:
   https://github.com/openshift/openshift-mcp-server/issues

#### 2. Insufficient Resources

Not enough CPU, memory, or storage available on any node.

**Diagnostic Commands**:
```bash
# Check VM resource requests
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.domain.resources}'

# Check node resource availability
oc describe nodes | grep -A 5 "Allocated resources"

# Look for VM events mentioning "Insufficient"
oc describe vm <vm-name> -n <namespace> | grep "Insufficient"
```

**Example Event**:
```
0/5 nodes are available: 2 Insufficient cpu, 3 Insufficient memory.
```

**Solutions**:
1. **Scale cluster** - Add more worker nodes
2. **Reduce VM resources** - Delete and recreate with smaller instance type
3. **Delete unused VMs** - Free up resources
4. **Check resource quotas**:
   ```bash
   oc describe quota -n <namespace>
   oc describe limitrange -n <namespace>
   ```

#### 3. Node Selector Mismatch

VM requires specific node labels that don't exist in the cluster.

**Diagnostic Commands**:
```bash
# Check VM node selector requirements
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.nodeSelector}'

# List available node labels
oc get nodes --show-labels

# Check if any nodes match the selector
oc get nodes -l <selector-key>=<selector-value>
```

**Solution**:
Remove node selector or add required labels to nodes:
```bash
# Option 1: Remove node selector from VM
oc patch vm <vm-name> -n <namespace> --type=json -p '[{"op": "remove", "path": "/spec/template/spec/nodeSelector"}]'

# Option 2: Add label to nodes
oc label node <node-name> <label-key>=<label-value>
```

---

### ErrorDataVolumeNotReady

**Symptom**: VM shows status `ErrorDataVolumeNotReady`

**Description**: The DataVolume (persistent storage) backing the VM is not ready.

**Possible Causes**:

#### 1. DataVolume Still Provisioning

Storage provisioning takes time, especially for large disks or when importing images.

**Diagnostic Commands**:
```bash
# Check DataVolume status
oc get datavolume -n <namespace>

# Look for status: Pending, ImportScheduled, ImportInProgress
# Wait for status: Succeeded

# Get detailed DataVolume information
oc describe datavolume <dv-name> -n <namespace>

# Check PVC (PersistentVolumeClaim) bound status
oc get pvc -n <namespace>
```

**Solution**: Wait for DataVolume provisioning to complete (can take 1-5 minutes).

#### 2. Storage Class Not Found

The requested storage class doesn't exist in the cluster.

**Diagnostic Commands**:
```bash
# List available storage classes
oc get storageclass

# Check DataVolume's requested storage class
oc get datavolume <dv-name> -n <namespace> -o jsonpath='{.spec.pvc.storageClassName}'
```

**Solution**:
1. Use a valid storage class from the cluster
2. Recreate VM with correct storage class parameter

#### 3. Insufficient Storage Quota

Namespace has insufficient storage quota to provision the PVC.

**Diagnostic Commands**:
```bash
# Check resource quotas
oc describe quota -n <namespace>

# Check storage usage
oc get pvc -n <namespace> -o custom-columns=NAME:.metadata.name,STORAGE:.spec.resources.requests.storage,STATUS:.status.phase
```

**Solution**:
1. Request quota increase from cluster admin
2. Delete unused PVCs to free quota
3. Reduce VM storage size

---

### ErrorPvcNotFound

**Symptom**: VM references a PersistentVolumeClaim that doesn't exist.

**Diagnostic Commands**:
```bash
# List PVCs in namespace
oc get pvc -n <namespace>

# Check VM's PVC references
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.volumes[*].persistentVolumeClaim.claimName}'
```

**Solution**:
- Wait for DataVolume to create the PVC
- Manually create missing PVC
- Fix VM spec to reference correct PVC name

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
| `Starting` | VM is booting | Wait for Running status |
| `Stopping` | VM is shutting down | Wait for Stopped status |
| `Terminating` | VM is being deleted | Wait for deletion to complete |
| `ErrorUnschedulable` | Cannot find node to run VM | **Action needed** - see ErrorUnschedulable section |
| `ErrorDataVolumeNotReady` | Storage not ready | **Action needed** - see ErrorDataVolumeNotReady section |
| `ErrorPvcNotFound` | PVC missing | **Action needed** - see ErrorPvcNotFound section |
| `CrashLoopBackOff` | VM repeatedly crashing | Check VM logs, guest OS issues |

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
1. **Action**: Read [troubleshooting.md](../../docs/troubleshooting.md) to understand error causes
2. **Output to user**: "I consulted troubleshooting.md to diagnose the <error-type> issue."
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

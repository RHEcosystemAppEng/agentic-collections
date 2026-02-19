---
title: VM Scheduling Errors
category: kubevirt
sources:
  - title: KubeVirt User Guide - Node Placement
    url: https://kubevirt.io/user-guide/virtual_machines/node_placement/
    date_accessed: 2026-02-06
  - title: Kubernetes Taints and Tolerations
    url: https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
    date_accessed: 2026-02-06
tags: [troubleshooting, scheduling, taints, tolerations, ErrorUnschedulable, node selector, resources]
semantic_keywords: [ErrorUnschedulable, scheduling failure, node taints, insufficient resources, node selector mismatch, tolerations]
use_cases: [vm-creation, vm-lifecycle]
related_docs: [INDEX.md, storage-errors.md, runtime-errors.md]
last_updated: 2026-02-17
---

# VM Scheduling Errors

[← Back to Index](INDEX.md)

## Overview

This document covers VM scheduling failures where the Kubernetes scheduler cannot find a suitable node to run the VM's underlying virt-launcher pod.

**When to use this document**:
- VM shows status `ErrorUnschedulable` after creation or start attempt
- VM events mention scheduling failures, taints, resources, or node selectors

**Skills that use this**: vm-create, vm-lifecycle-manager

---

## ErrorUnschedulable

**Symptom**: VM shows status `ErrorUnschedulable` after creation

**Description**: The Kubernetes scheduler cannot find a suitable node to run the VM's underlying virt-launcher pod.

**Possible Causes**:

### 1. Node Taints (Most Common)

Nodes have taints that the VM doesn't tolerate. Common in environments with dedicated virtualization infrastructure.

**Diagnostic Steps** (Use MCP Tools First):

**1. Check VM events for scheduling failures**:

**MCP Tool**: `events_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter results for events where `involvedObject.name` == "<vm-name>" and look for messages like:
- "0/X nodes are available: X node(s) had taints that the pod didn't tolerate"

**CLI Fallback** (if MCP unavailable):
```bash
oc get events -n <namespace> --field-selector involvedObject.name=<vm-name>
```

**2. Check node taints in the cluster**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "Node"
}
```

Extract `.spec.taints` from each node in the returned list. Filter for nodes with non-null taints.

**CLI Fallback** (if MCP unavailable):
```bash
oc get nodes -o json | jq '.items[] | select(.spec.taints != null) | {name: .metadata.name, taints: .spec.taints}'
```

**Common Taint Patterns**:
- `virtualization=true:NoSchedule` - Only VMs with matching toleration can schedule
- `node-role.kubernetes.io/infra:NoSchedule` - Infrastructure-only nodes
- `node.kubernetes.io/not-ready:NoSchedule` - Node not ready for workloads

**Solution - Add Tolerations to VM**:

The openshift-virtualization MCP server's `vm_create` tool does NOT currently support the `tolerations` parameter. This requires a post-creation workaround using MCP tools.

**Workaround (post-creation using MCP Tools)**:

**Step 1**: Get current VM spec

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

**Step 2**: Modify the returned JSON to add tolerations

Add to `.spec.template.spec.tolerations`:
```json
{
  "tolerations": [
    {
      "key": "virtualization",
      "operator": "Equal",
      "value": "true",
      "effect": "NoSchedule"
    }
  ]
}
```

**Step 3**: Update VM with modified spec

**MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

**Parameters**:
```json
{
  "resource": "<full-modified-vm-yaml-or-json>"
}
```

Pass the complete modified VM resource as YAML or JSON string.

**Step 4**: Verify tolerations were added

Use `resources_get` again and check `.spec.template.spec.tolerations` in response.

**Step 5**: Check if VM status improved

Wait 5-10 seconds, then use `resources_get` and check `.status.printableStatus`.

**CLI Fallback** (if MCP patch is too complex):
```bash
# Ask user permission first: "MCP patch is complex. May I use oc patch instead?"
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

# Verify tolerations
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.tolerations}' | jq

# Check status
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

---

### 2. Insufficient Resources

Not enough CPU, memory, or storage available on any node.

**Diagnostic Steps** (Use MCP Tools First):

**1. Check VM resource requests**:

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

Extract `.spec.template.spec.domain.resources` to see CPU/memory requests.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.domain.resources}'
```

**2. Check node resource availability**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "Node"
}
```

For each node in `.items[]`, review `.status.allocatable` and `.status.capacity` for available resources.

Alternatively, use `nodes_top` MCP tool for current resource usage.

**CLI Fallback** (if MCP unavailable):
```bash
oc describe nodes | grep -A 5 "Allocated resources"
```

**3. Look for VM events mentioning "Insufficient"**:

**MCP Tool**: `events_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter for events where `.involvedObject.name` matches `<vm-name>` and `.message` contains "Insufficient".

**CLI Fallback** (if MCP unavailable):
```bash
oc describe vm <vm-name> -n <namespace> | grep "Insufficient"
```

**Example Event**:
```
0/5 nodes are available: 2 Insufficient cpu, 3 Insufficient memory.
```

**Solutions** (Use MCP Tools First):

1. **Scale cluster** - Add more worker nodes (cluster admin task, no MCP tool)
2. **Reduce VM resources** - Delete and recreate with smaller instance type using vm-create skill
3. **Delete unused VMs** - Use vm-delete skill to free up resources
4. **Check resource quotas**:

   **MCP Tool**: `resources_list` (from openshift-virtualization)

   **Parameters for quota**:
   ```json
   {
     "apiVersion": "v1",
     "kind": "ResourceQuota",
     "namespace": "<namespace>"
   }
   ```

   **Parameters for limit range**:
   ```json
   {
     "apiVersion": "v1",
     "kind": "LimitRange",
     "namespace": "<namespace>"
   }
   ```

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc describe quota -n <namespace>
   oc describe limitrange -n <namespace>
   ```

---

### 3. Node Selector Mismatch

VM requires specific node labels that don't exist in the cluster.

**Diagnostic Steps** (Use MCP Tools First):

**1. Check VM node selector requirements**:

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

Extract `.spec.template.spec.nodeSelector` to see required node labels.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.nodeSelector}'
```

**2. List available node labels**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "Node"
}
```

For each node in `.items[]`, review `.metadata.labels` for available labels.

**CLI Fallback** (if MCP unavailable):
```bash
oc get nodes --show-labels
```

**3. Check if any nodes match the selector**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "Node",
  "labelSelector": "<selector-key>=<selector-value>"
}
```

Should return at least one node with matching labels.

**CLI Fallback** (if MCP unavailable):
```bash
oc get nodes -l <selector-key>=<selector-value>
```

**Solutions** (Use MCP Tools First):

**Option 1: Remove node selector from VM**

**MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

**Process**:
1. Get current VM using `resources_get` (diagnostic step 1)
2. Remove `.spec.template.spec.nodeSelector` field
3. Update VM using `resources_create_or_update` with modified JSON

**CLI Fallback** (JSON patch easier via CLI):
Ask user: "Patching node selector is easier via CLI. May I use `oc patch`?"
```bash
oc patch vm <vm-name> -n <namespace> --type=json -p '[{"op": "remove", "path": "/spec/template/spec/nodeSelector"}]'
```

**Option 2: Add label to nodes**

**MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

**Process**:
1. Get node using `resources_get`
2. Add label to `.metadata.labels`
3. Update node using `resources_create_or_update`

⚠️ **Note**: Node labeling typically requires cluster admin privileges.

**CLI Fallback** (simpler via CLI):
Ask user: "Adding node labels is easier via CLI. May I use `oc label`?"
```bash
oc label node <node-name> <label-key>=<label-value>
```

---

[← Back to Index](INDEX.md) | [Storage Errors →](storage-errors.md)

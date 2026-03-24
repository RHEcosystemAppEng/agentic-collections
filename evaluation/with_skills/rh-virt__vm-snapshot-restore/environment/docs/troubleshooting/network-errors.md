---
title: VM Network Errors
category: kubevirt
sources:
  - title: Multus CNI - Network Attachment Definitions
    url: https://github.com/k8snetworkplumbingwg/multus-cni
    date_accessed: 2026-02-17
tags: [troubleshooting, networking, Multus, NAD, SR-IOV, secondary networks]
semantic_keywords: [network attachment failures, Multus, NetworkAttachmentDefinition, SR-IOV, secondary networks]
use_cases: [vm-creation, network-troubleshooting]
related_docs: [INDEX.md, scheduling-errors.md]
last_updated: 2026-02-17
---

# VM Network Errors

[← Back to Index](INDEX.md)

## Overview

This document covers VM secondary network attachment failures using Multus CNI and NetworkAttachmentDefinitions.

**When to use this document**:
- VM created successfully but secondary networks not attached
- NetworkAttachmentDefinition not found errors
- Multus CNI failures
- SR-IOV device attachment issues

**Skills that use this**: vm-create

---

### Network Attachment Failures

**Symptom**: VM created successfully but secondary networks (Multus) not attached or not working

**Description**: The VM fails to attach to secondary networks defined via NetworkAttachmentDefinitions (Multus CNI).

**Possible Causes**:
- NetworkAttachmentDefinition doesn't exist in the namespace
- Multus CNI not installed or not configured on cluster
- Namespace mismatch (NAD in different namespace than VM)
- Interface name conflicts in VM spec
- Bridge/network configuration errors in NAD
- SR-IOV device not available (if using SR-IOV)

**Diagnostic Steps** (Use MCP Tools First):

**1. List NetworkAttachmentDefinitions in namespace**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "k8s.cni.cncf.io/v1",
  "kind": "NetworkAttachmentDefinition",
  "namespace": "<namespace>"
}
```

Review `.items[].metadata.name` for available NADs.

**CLI Fallback** (if MCP unavailable):
```bash
oc get network-attachment-definitions -n <namespace>
```

**2. List NetworkAttachmentDefinitions in all namespaces**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "k8s.cni.cncf.io/v1",
  "kind": "NetworkAttachmentDefinition"
}
```

Omit `namespace` parameter to list across all namespaces.

**CLI Fallback** (if MCP unavailable):
```bash
oc get network-attachment-definitions -A
```

**3. Check specific NetworkAttachmentDefinition**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "k8s.cni.cncf.io/v1",
  "kind": "NetworkAttachmentDefinition",
  "namespace": "<namespace>",
  "name": "<nad-name>"
}
```

Review `.spec.config` for CNI configuration.

**CLI Fallback** (if MCP unavailable):
```bash
oc get network-attachment-definition <nad-name> -n <namespace> -o yaml
```

**4. Check VM network configuration**:

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

Extract `.spec.template.spec.networks` to see network references.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.networks}' | jq
```

**5. Check VM domain interfaces**:

Use `resources_get` from step 4, extract `.spec.template.spec.domain.devices.interfaces`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.domain.devices.interfaces}' | jq
```

**6. Check virt-launcher pod network annotations** (shows actual attachments):

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter for virt-launcher pod, then extract `.metadata.annotations["k8s.v1.cni.cncf.io/network-status"]`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pod virt-launcher-<vm-name>-xxx -n <namespace> -o jsonpath='{.metadata.annotations.k8s\.v1\.cni\.cncf\.io/network-status}' | jq
```

**7. Check Multus is installed**:

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "openshift-multus"
}
```

Should show Multus CNI pods running.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pods -n openshift-multus
```

**8. Check for errors in virt-launcher pod events**:

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
oc describe pod virt-launcher-<vm-name>-xxx -n <namespace>
```

**Common Error Messages**:
- `"network-attachment-definition not found"` - NAD doesn't exist in namespace
- `"multus CNI not configured"` - Multus not installed or misconfigured
- `"interface name conflict"` - Duplicate interface names in VM spec
- `"failed to add network"` - CNI plugin error (check NAD config)
- `"no available devices"` - SR-IOV device not available (if using SR-IOV)

**Solutions** (Use MCP Tools First):

1. **Verify NetworkAttachmentDefinition exists in correct namespace**:

   Use `resources_list` from diagnostic step 1 to check if NAD exists in VM's namespace.

   If NAD is in different namespace, copy it to VM namespace:

   **MCP Tool**: `resources_get` + `resources_create_or_update` (from openshift-virtualization)

   **Process**:
   1. Get NAD from source namespace using `resources_get`
   2. Modify `.metadata.namespace` to target namespace
   3. Create NAD in target namespace using `resources_create_or_update`

   **CLI Fallback** (stream processing easier via CLI):
   Ask user: "Copying NAD across namespaces is easier via CLI. May I use `oc` with sed?"
   ```bash
   oc get network-attachment-definition <nad-name> -n <source-namespace> -o yaml | \
     sed "s/namespace: <source-namespace>/namespace: <target-namespace>/" | \
     oc apply -f -
   ```

2. **Create missing NetworkAttachmentDefinition**:

   **MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

   Example: Linux bridge network

   **Parameters**:
   ```json
   {
     "apiVersion": "k8s.cni.cncf.io/v1",
     "kind": "NetworkAttachmentDefinition",
     "metadata": {
       "name": "vlan100",
       "namespace": "<namespace>"
     },
     "spec": {
       "config": "{\"cniVersion\":\"0.3.1\",\"type\":\"bridge\",\"bridge\":\"br1\",\"vlan\":100,\"ipam\":{\"type\":\"host-local\",\"subnet\":\"192.168.100.0/24\"}}"
     }
   }
   ```

   **CLI Fallback** (YAML easier via CLI):
   Ask user: "Creating NAD with complex config is easier via CLI. May I use `oc apply -f`?"
   ```bash
   cat <<EOF | oc apply -f -
   apiVersion: k8s.cni.cncf.io/v1
   kind: NetworkAttachmentDefinition
   metadata:
     name: vlan100
     namespace: <namespace>
   spec:
     config: '{
       "cniVersion": "0.3.1",
       "type": "bridge",
       "bridge": "br1",
       "vlan": 100,
       "ipam": {
         "type": "host-local",
         "subnet": "192.168.100.0/24"
       }
     }'
   EOF
   ```

3. **Check Multus CNI installation**:

   Use `pods_list_in_namespace` from diagnostic step 7 to verify Multus pods are running.

   To check cluster network operator:

   **MCP Tool**: `resources_list` (from openshift-virtualization)

   **Parameters**:
   ```json
   {
     "apiVersion": "config.openshift.io/v1",
     "kind": "ClusterOperator"
   }
   ```

   Filter for `network` operator.

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get pods -n openshift-multus
   oc get clusteroperators network
   ```

4. **Fix interface name conflicts** (if VM has duplicate names):

   Use `resources_get` from diagnostic step 4, extract `.spec.template.spec.domain.devices.interfaces[*].name`.

   Each interface must have unique name. If duplicates found, edit VM using `resources_create_or_update`.

   **CLI Fallback** (interactive edit easier via CLI):
   Ask user: "Editing VM is easier via CLI. May I use `oc edit`?"
   ```bash
   oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.domain.devices.interfaces[*].name}'
   oc edit vm <vm-name> -n <namespace>
   ```

5. **Validate NAD configuration syntax**:

   Use `resources_get` from diagnostic step 3, extract `.spec.config`.

   Ensure valid JSON. Common issues: missing quotes, wrong CNI type, invalid IPAM config.

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get network-attachment-definition <nad-name> -n <namespace> -o jsonpath='{.spec.config}'
   ```

6. **Check SR-IOV device availability** (if using SR-IOV networks):

   **MCP Tool**: `resources_list` (from openshift-virtualization)

   List SR-IOV network node policies:

   **Parameters**:
   ```json
   {
     "apiVersion": "sriovnetwork.openshift.io/v1",
     "kind": "SriovNetworkNodePolicy",
     "namespace": "openshift-sriov-network-operator"
   }
   ```

   Check SR-IOV device plugin pods:

   **MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

   **Parameters**:
   ```json
   {
     "namespace": "openshift-sriov-network-operator"
   }
   ```

   Filter for pods with "device-plugin" in name.

   Check available SR-IOV devices on node:

   **MCP Tool**: `resources_get` (from openshift-virtualization)

   **Parameters**:
   ```json
   {
     "apiVersion": "v1",
     "kind": "Node",
     "name": "<node-name>"
   }
   ```

   Review `.status.allocatable` for SR-IOV resources.

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get sriovnetworknodepolicy -n openshift-sriov-network-operator
   oc get pods -n openshift-sriov-network-operator | grep device-plugin
   oc describe node <node-name> | grep -A 10 "Allocatable:"
   ```

7. **Recreate VM with corrected network configuration** (if needed):

   If network attachment is fundamentally broken, delete and recreate VM with correct NAD references using vm-create skill.

**Verification** (Use MCP Tools First):

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

After remediation, check virt-launcher pod network status:

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

Filter for virt-launcher pod, then extract `.metadata.annotations["k8s.v1.cni.cncf.io/network-status"]`.

Should show all attached networks with status. Example output:
```json
[
  {
    "name": "openshift-sdn",
    "interface": "eth0",
    "ips": ["10.128.2.10"],
    "default": true
  },
  {
    "name": "vlan100",
    "interface": "net1",
    "ips": ["192.168.100.5"]
  }
]
```

**CLI Fallback** (if MCP unavailable):
```bash
oc get pod virt-launcher-<vm-name>-xxx -n <namespace> -o jsonpath='{.metadata.annotations.k8s\.v1\.cni\.cncf\.io/network-status}' | jq
```

**Check from inside VM** (via console):

⚠️ **Note**: Console access requires `virtctl` CLI tool (no MCP equivalent).

**CLI Required** (no MCP alternative):
```bash
virtctl console <vm-name> -n <namespace>
# In guest OS:
ip addr show
# Should show all network interfaces (eth0, net1, etc.)
```

**Common Network Types**:
- **Linux Bridge**: Layer 2 bridge for VLAN networks
- **SR-IOV**: High-performance direct device assignment
- **macvlan**: MAC-based VLAN for container networks
- **OVN-Kubernetes**: OpenShift native overlay network

---


---

[← Back to Index](INDEX.md) | [← Runtime Errors](runtime-errors.md)

---
title: VM Storage Errors
category: kubevirt
sources:
  - title: KubeVirt CDI - DataVolumes
    url: https://kubevirt.io/user-guide/storage/containerized_data_importer/
    date_accessed: 2026-02-17
  - title: Kubernetes Persistent Volumes
    url: https://kubernetes.io/docs/concepts/storage/persistent-volumes/
    date_accessed: 2026-02-17
tags: [troubleshooting, storage, DataVolume, PVC, ErrorDataVolumeNotReady, ErrorPvcNotFound, cloning, CDI]
semantic_keywords: [ErrorDataVolumeNotReady, ErrorPvcNotFound, storage deletion, PVC, DataVolume cloning, storage provisioning, storage class]
use_cases: [vm-creation, vm-deletion, vm-cloning]
related_docs: [INDEX.md, scheduling-errors.md, lifecycle-errors.md]
last_updated: 2026-02-17
---

# VM Storage Errors

[← Back to Index](INDEX.md)

## Overview

This document covers VM storage-related failures including storage provisioning, deletion, and cloning issues.

**When to use this document**:
- VM shows status `ErrorDataVolumeNotReady` or `ErrorPvcNotFound`
- Storage deletion fails after VM deletion
- DataVolume cloning operations fail
- PVC provisioning issues

**Skills that use this**: vm-create, vm-delete, vm-clone

---

### ErrorDataVolumeNotReady

**Symptom**: VM shows status `ErrorDataVolumeNotReady`

**Description**: The DataVolume (persistent storage) backing the VM is not ready.

**Possible Causes**:

#### 1. DataVolume Still Provisioning

Storage provisioning takes time, especially for large disks or when importing images.

**Diagnostic Steps** (Use MCP Tools First):

**1. Check DataVolume status**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<namespace>"
}
```

Look for status in response: `Pending`, `ImportScheduled`, `ImportInProgress`, or `Succeeded`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get datavolume -n <namespace>
```

**2. Get detailed DataVolume information**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<namespace>",
  "name": "<dv-name>"
}
```

Check `.status.phase` and `.status.conditions` for provisioning details.

**CLI Fallback** (if MCP unavailable):
```bash
oc get datavolume <dv-name> -n <namespace> -o json
```

**3. Check PVC (PersistentVolumeClaim) bound status**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>"
}
```

Check `.status.phase` for each PVC (should be `Bound`).

**CLI Fallback** (if MCP unavailable):
```bash
oc get pvc -n <namespace>
```

**Solution**: Wait for DataVolume provisioning to complete (can take 1-5 minutes). Check status periodically using `resources_get`.

#### 2. Storage Class Not Found

The requested storage class doesn't exist in the cluster.

**Diagnostic Steps** (Use MCP Tools First):

**1. List available storage classes**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "storage.k8s.io/v1",
  "kind": "StorageClass"
}
```

Review the list of available storage classes (check `.items[].metadata.name`).

**CLI Fallback** (if MCP unavailable):
```bash
oc get storageclass
```

**2. Check DataVolume's requested storage class**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<namespace>",
  "name": "<dv-name>"
}
```

Check `.spec.pvc.storageClassName` in the returned JSON.

**CLI Fallback** (if MCP unavailable):
```bash
oc get datavolume <dv-name> -n <namespace> -o jsonpath='{.spec.pvc.storageClassName}'
```

**Solution**:
1. Use a valid storage class from the cluster
2. Recreate VM with correct storage class parameter

#### 3. Insufficient Storage Quota

Namespace has insufficient storage quota to provision the PVC.

**Diagnostic Steps** (Use MCP Tools First):

**1. Check resource quotas**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "ResourceQuota",
  "namespace": "<namespace>"
}
```

Review `.items[].status.hard` (quota limits) and `.items[].status.used` (current usage).

**CLI Fallback** (if MCP unavailable):
```bash
oc describe quota -n <namespace>
```

**2. Check storage usage**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>"
}
```

For each PVC, check `.metadata.name`, `.spec.resources.requests.storage`, and `.status.phase`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pvc -n <namespace> -o custom-columns=NAME:.metadata.name,STORAGE:.spec.resources.requests.storage,STATUS:.status.phase
```

**Solution**:
1. Request quota increase from cluster admin
2. Delete unused PVCs to free quota
3. Reduce VM storage size

---

### ErrorPvcNotFound

**Symptom**: VM references a PersistentVolumeClaim that doesn't exist.

**Diagnostic Steps** (Use MCP Tools First):

**1. List PVCs in namespace**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>"
}
```

Review the list of available PVCs (check `.items[].metadata.name`).

**CLI Fallback** (if MCP unavailable):
```bash
oc get pvc -n <namespace>
```

**2. Check VM's PVC references**:

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

Extract `.spec.template.spec.volumes[*].persistentVolumeClaim.claimName` from the returned JSON to see which PVCs the VM is referencing.

**CLI Fallback** (if MCP unavailable):
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.volumes[*].persistentVolumeClaim.claimName}'
```

**Solution**:
- Wait for DataVolume to create the PVC
- Manually create missing PVC
- Fix VM spec to reference correct PVC name

---


---

### Storage Deletion Failures

**Symptom**: VM deleted successfully but PVC or DataVolume remains in namespace

**Description**: Storage resources (PersistentVolumeClaims, DataVolumes) fail to delete after VM removal.

**Possible Causes**:
- PVC still bound to active PersistentVolume with `Retain` policy
- DataVolume still being referenced by another resource
- CDI (Containerized Data Importer) controller issues
- Storage class retention policy preventing deletion
- Finalizers on PVC/DataVolume blocking cleanup
- PVC still mounted by a pod

**Diagnostic Steps** (Use MCP Tools First):

**1. Check PVC status**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>"
}
```

Review `.items[].metadata.name` and `.items[].status.phase` for each PVC.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pvc -n <namespace>
```

**2. Check specific PVC phase**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>",
  "name": "<pvc-name>"
}
```

Check `.status.phase` (should be `Released` or `Bound`).

**CLI Fallback** (if MCP unavailable):
```bash
oc get pvc <pvc-name> -n <namespace> -o jsonpath='{.status.phase}'
```

**3. Check DataVolume status**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<namespace>"
}
```

Review `.items[].metadata.name` and `.items[].status.phase` for each DataVolume.

**CLI Fallback** (if MCP unavailable):
```bash
oc get datavolume -n <namespace>
```

**4. Check what's using the PVC**:

**MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>"
}
```

For each pod in `.items[]`, check `.spec.volumes[].persistentVolumeClaim.claimName` to find pods using the PVC.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pods -n <namespace> -o json | jq '.items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName=="<pvc-name>") | .metadata.name'
```

**5. Check PVC finalizers**:

Use `resources_get` from step 2, extract `.metadata.finalizers` from the returned JSON.

**6. Check DataVolume finalizers**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<namespace>",
  "name": "<dv-name>"
}
```

Extract `.metadata.finalizers` from the returned JSON.

**CLI Fallback** (if MCP unavailable):
```bash
oc get datavolume <dv-name> -n <namespace> -o jsonpath='{.metadata.finalizers}'
```

**7. Check PV reclaim policy**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolume"
}
```

Filter results for PV where `.spec.claimRef.name` matches `<pvc-name>`.

To get specific PV policy:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolume",
  "name": "<pv-name>"
}
```

Check `.spec.persistentVolumeReclaimPolicy`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pv | grep <pvc-name>
oc get pv <pv-name> -o jsonpath='{.spec.persistentVolumeReclaimPolicy}'
```

**Common Finalizer Patterns**:
- `kubernetes.io/pvc-protection` - Protects PVC while in use
- `cdi.kubevirt.io/dataVolumeFinalizer` - CDI cleanup finalizer

**Solutions** (Use MCP Tools First):

1. **Delete DataVolume first, then PVC**:

   **MCP Tool**: `resources_delete` (from openshift-virtualization)

   Delete DataVolume first (often blocks PVC deletion):

   **Parameters**:
   ```json
   {
     "apiVersion": "cdi.kubevirt.io/v1beta1",
     "kind": "DataVolume",
     "namespace": "<namespace>",
     "name": "<dv-name>"
   }
   ```

   Wait a few seconds, then delete PVC:

   **Parameters**:
   ```json
   {
     "apiVersion": "v1",
     "kind": "PersistentVolumeClaim",
     "namespace": "<namespace>",
     "name": "<pvc-name>"
   }
   ```

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc delete datavolume <dv-name> -n <namespace>
   oc delete pvc <pvc-name> -n <namespace>
   ```

2. **Check for pods still using PVC**:

   **MCP Tool**: `pods_list_in_namespace` (from openshift-virtualization)

   **Parameters**:
   ```json
   {
     "namespace": "<namespace>"
   }
   ```

   Filter results for pods where `.spec.volumes[].persistentVolumeClaim.claimName` equals `<pvc-name>`.

   Then delete the pods using `pods_delete`:

   **Parameters**:
   ```json
   {
     "namespace": "<namespace>",
     "name": "<pod-name>"
   }
   ```

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get pods -n <namespace> -o json | jq -r '.items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName=="<pvc-name>") | .metadata.name'
   oc delete pod <pod-name> -n <namespace>
   ```

3. **Force delete PVC** (if safe to do so):

   ⚠️ **Note**: MCP `resources_delete` does not support `--grace-period` or `--force` flags. Use CLI for force deletion.

   **CLI Fallback** (required for force delete):
   Ask user: "Force deletion requires CLI. May I use `oc delete --force`?"
   ```bash
   oc delete pvc <pvc-name> -n <namespace> --grace-period=0 --force
   ```

4. **Remove finalizers from PVC** (⚠️ last resort):

   **MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

   **Process**:
   1. Get current PVC using `resources_get` (diagnostic step 2)
   2. Remove items from `.metadata.finalizers` array
   3. Update PVC using `resources_create_or_update` with modified JSON

   ⚠️ **WARNING**: Can leave orphaned storage. Only use if you understand the implications.

   **CLI Fallback** (JSON patch easier via CLI):
   Ask user: "Patching finalizers is easier via CLI. May I use `oc patch`?"
   ```bash
   oc patch pvc <pvc-name> -n <namespace> --type=json -p '[{"op": "remove", "path": "/metadata/finalizers"}]'
   ```

5. **Remove finalizers from DataVolume** (⚠️ last resort):

   **MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

   **Process**:
   1. Get current DataVolume using `resources_get` (diagnostic step 6)
   2. Remove items from `.metadata.finalizers` array
   3. Update DataVolume using `resources_create_or_update` with modified JSON

   ⚠️ **WARNING**: Can leave orphaned storage. Only use if you understand the implications.

   **CLI Fallback** (JSON patch easier via CLI):
   Ask user: "Patching finalizers is easier via CLI. May I use `oc patch`?"
   ```bash
   oc patch datavolume <dv-name> -n <namespace> --type=json -p '[{"op": "remove", "path": "/metadata/finalizers"}]'
   ```

6. **Change PV reclaim policy** (if PV has Retain policy):

   **MCP Tool**: `resources_get` + `resources_create_or_update` (from openshift-virtualization)

   **Process**:
   1. Get current PV policy using `resources_get` (diagnostic step 7)
   2. Modify `.spec.persistentVolumeReclaimPolicy` to `"Delete"`
   3. Update PV using `resources_create_or_update` with modified JSON

   ⚠️ **WARNING**: Setting to `Delete` will delete underlying storage.

   **CLI Fallback** (JSON patch easier via CLI):
   Ask user: "Patching PV reclaim policy is easier via CLI. May I use `oc patch`?"
   ```bash
   oc get pv <pv-name> -o jsonpath='{.spec.persistentVolumeReclaimPolicy}'
   oc patch pv <pv-name> -p '{"spec":{"persistentVolumeReclaimPolicy":"Delete"}}'
   ```

**Storage Quota Check** (Use MCP Tools First):

After deletion, verify storage quota is freed:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters for quota check**:
```json
{
  "apiVersion": "v1",
  "kind": "ResourceQuota",
  "namespace": "<namespace>"
}
```

Review `.items[].status.used` to verify storage quota is freed.

**Parameters for PVC verification**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>"
}
```

**CLI Fallback** (if MCP unavailable):
```bash
oc describe quota -n <namespace>
oc get pvc -n <namespace>
```

**Verification** (Use MCP Tools First):

**MCP Tool**: `resources_get` (from openshift-virtualization)

Confirm PVC is deleted:

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>",
  "name": "<pvc-name>"
}
```

Should return "Not Found" error.

Confirm DataVolume is deleted:

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<namespace>",
  "name": "<dv-name>"
}
```

Should return "Not Found" error.

**CLI Fallback** (if MCP unavailable):
```bash
oc get pvc <pvc-name> -n <namespace>
# Should return: Error from server (NotFound)

oc get datavolume <dv-name> -n <namespace>
# Should return: Error from server (NotFound)
```

---

### DataVolume Cloning Failures

**Symptom**: VM clone created successfully but DataVolume clone operation fails

**Description**: The DataVolume cloning process (used by vm-clone skill) fails to create a copy of the source storage.

**Possible Causes**:
- CSI driver doesn't support volume cloning
- Source PVC storage class incompatible with cloning
- Cross-namespace cloning not permitted by storage backend
- Insufficient storage quota in target namespace
- Source PVC not in `Bound` state
- Storage class doesn't have volume cloning enabled
- CDI (Containerized Data Importer) controller issues

**Diagnostic Steps** (Use MCP Tools First):

**1. Check DataVolume clone status**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<target-namespace>",
  "name": "<target-dv-name>"
}
```

Review `.status.phase`, `.status.conditions`, and `.metadata.name`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get datavolume <target-dv-name> -n <target-namespace>
```

**2. Check DataVolume events for errors**:

**MCP Tool**: `events_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<target-namespace>"
}
```

Filter results for events related to the DataVolume (check `.involvedObject.name` equals `<target-dv-name>`).

**CLI Fallback** (if MCP unavailable):
```bash
oc describe datavolume <target-dv-name> -n <target-namespace>
```

**3. Check DataVolume phase**:

Use `resources_get` from step 1, extract `.status.phase`.

**CLI Fallback** (if MCP unavailable):
```bash
oc get datavolume <target-dv-name> -n <target-namespace> -o jsonpath='{.status.phase}'
```

**4. Check if storage class supports cloning**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "storage.k8s.io/v1",
  "kind": "StorageClass",
  "name": "<sc-name>"
}
```

Review the full YAML output for cloning-related configurations.

**CLI Fallback** (if MCP unavailable):
```bash
oc get storageclass <sc-name> -o yaml | grep -A 5 -i clone
```

**5. Check CSI driver capabilities**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "storage.k8s.io/v1",
  "kind": "CSIDriver"
}
```

Review `.items[].metadata.name` for available CSI drivers.

**CLI Fallback** (if MCP unavailable):
```bash
oc get csidriver
```

**6. Check source PVC status**:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<source-namespace>",
  "name": "<source-pvc-name>"
}
```

Check `.status.phase` (should be `Bound` for cloning to work).

**CLI Fallback** (if MCP unavailable):
```bash
oc get pvc <source-pvc-name> -n <source-namespace>
```

**7. Check target namespace storage quota**:

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "ResourceQuota",
  "namespace": "<target-namespace>"
}
```

Review `.items[].status.hard` (limits) and `.items[].status.used` (current usage).

**CLI Fallback** (if MCP unavailable):
```bash
oc describe quota -n <target-namespace>
```

**8. Check CDI controller logs**:

**MCP Tool**: `pods_list_in_namespace` + `pods_log` (from openshift-virtualization)

First, list pods in openshift-cnv namespace:

**Parameters for pods_list_in_namespace**:
```json
{
  "namespace": "openshift-cnv",
  "labelSelector": "app.kubernetes.io/component=cdi-deployment"
}
```

Then get logs using `pods_log`:

**Parameters**:
```json
{
  "namespace": "openshift-cnv",
  "name": "<cdi-pod-name>",
  "tail": 100
}
```

**CLI Fallback** (if MCP unavailable or easier via CLI):
```bash
oc logs -n openshift-cnv $(oc get pods -n openshift-cnv | grep cdi-deployment | awk '{print $1}')
```

**Common Error Messages**:
- `"volume cloning is not supported"` - CSI driver lacks clone capability
- `"cross namespace clone is not supported"` - Cloning between namespaces forbidden by storage
- `"source PVC not found"` - Source PVC doesn't exist or wrong namespace
- `"insufficient quota"` - Target namespace lacks storage quota
- `"source PVC not bound"` - Source PVC must be in Bound state for cloning
- `"StorageClass does not support cloning"` - Storage class configuration issue

**Solutions** (Use MCP Tools First):

1. **Check storage class clone support**:

   **MCP Tool**: `resources_list` (from openshift-virtualization)

   **Parameters**:
   ```json
   {
     "apiVersion": "storage.k8s.io/v1",
     "kind": "StorageClass"
   }
   ```

   For each storage class in `.items[]`, check:
   - `.metadata.name` (storage class name)
   - `.provisioner` (CSI driver)

   Storage classes using CSI drivers typically support cloning. Look for provisioners like:
   - `csi.ovirt.org` (oVirt CSI)
   - `openshift-storage.rbd.csi.ceph.com` (Ceph RBD)
   - `ebs.csi.aws.com` (AWS EBS CSI)

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get storageclass -o custom-columns=NAME:.metadata.name,PROVISIONER:.provisioner
   ```

2. **Verify source PVC is bound**:

   Use `resources_get` from diagnostic step 6, check `.status.phase` (should be `Bound`).

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc get pvc <source-pvc> -n <source-namespace> -o jsonpath='{.status.phase}'
   ```

3. **Check target namespace quota**:

   Use `resources_list` from diagnostic step 7 to check quota.

   If quota increase needed, this requires cluster admin privileges (cannot be done via MCP).

   **CLI Fallback** (if MCP unavailable):
   ```bash
   oc describe quota -n <target-namespace>
   ```

4. **Use snapshot-based cloning** (alternative method):

   **MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

   **Step 1**: Create VolumeSnapshot of source PVC

   **Parameters**:
   ```json
   {
     "apiVersion": "snapshot.storage.k8s.io/v1",
     "kind": "VolumeSnapshot",
     "metadata": {
       "name": "<vm-name>-snapshot",
       "namespace": "<source-namespace>"
     },
     "spec": {
       "source": {
         "persistentVolumeClaimName": "<source-pvc>"
       }
     }
   }
   ```

   **Step 2**: Wait for snapshot to be ready (use `resources_get` to check `.status.readyToUse`)

   **Step 3**: Create new DataVolume from snapshot

   **Parameters**:
   ```json
   {
     "apiVersion": "cdi.kubevirt.io/v1beta1",
     "kind": "DataVolume",
     "metadata": {
       "name": "<target-vm>-rootdisk",
       "namespace": "<target-namespace>"
     },
     "spec": {
       "source": {
         "snapshot": {
           "name": "<vm-name>-snapshot",
           "namespace": "<source-namespace>"
         }
       },
       "storage": {
         "resources": {
           "requests": {
             "storage": "50Gi"
           }
         },
         "storageClassName": "<storage-class>"
       }
     }
   }
   ```

   **CLI Fallback** (YAML easier via CLI):
   Ask user: "Snapshot-based cloning involves complex YAML. May I use `oc apply -f` instead?"
   ```bash
   cat <<EOF | oc apply -f -
   apiVersion: snapshot.storage.k8s.io/v1
   kind: VolumeSnapshot
   metadata:
     name: <vm-name>-snapshot
     namespace: <source-namespace>
   spec:
     source:
       persistentVolumeClaimName: <source-pvc>
   EOF

   oc get volumesnapshot <vm-name>-snapshot -n <source-namespace>

   cat <<EOF | oc apply -f -
   apiVersion: cdi.kubevirt.io/v1beta1
   kind: DataVolume
   metadata:
     name: <target-vm>-rootdisk
     namespace: <target-namespace>
   spec:
     source:
       snapshot:
         name: <vm-name>-snapshot
         namespace: <source-namespace>
     storage:
       resources:
         requests:
           storage: 50Gi
       storageClassName: <storage-class>
   EOF
   ```

5. **Use "new empty storage" option** (vm-clone skill):
   - If cloning isn't supported, create VM with empty storage
   - Manually copy data if needed

6. **Cross-namespace cloning workaround**:
   - Some storage backends require snapshot for cross-namespace cloning
   - Create snapshot in source namespace, restore in target namespace (see solution 4 above)

**Verification** (Use MCP Tools First):

**MCP Tool**: `resources_get` (from openshift-virtualization)

Check DataVolume reached Succeeded phase:

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<target-namespace>",
  "name": "<target-dv-name>"
}
```

Check `.status.phase` (should return `Succeeded`).

Check PVC was created and bound:

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<target-namespace>",
  "name": "<target-vm>-rootdisk"
}
```

Check `.status.phase` (should return `Bound`).

**CLI Fallback** (if MCP unavailable):
```bash
oc get datavolume <target-dv-name> -n <target-namespace> -o jsonpath='{.status.phase}'
# Should return: Succeeded

oc get pvc <target-vm>-rootdisk -n <target-namespace> -o jsonpath='{.status.phase}'
# Should return: Bound
```

**Alternative**: If cloning continuously fails, use vm-create skill to create new VM with container disk or DataSource instead.

---


---

[← Back to Index](INDEX.md) | [← Scheduling Errors](scheduling-errors.md) | [Lifecycle Errors →](lifecycle-errors.md)

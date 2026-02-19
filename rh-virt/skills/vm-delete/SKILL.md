---
name: vm-delete
description: |
  Permanently delete virtual machines and their associated resources from OpenShift Virtualization. Use this skill when users request:
  - "Delete VM [name]"
  - "Remove virtual machine [name]"
  - "Destroy VM [name]"
  - "Clean up VM [name]"

  This skill handles permanent VM deletion with strict safety confirmations and typed verification.

  NOT for power management (use vm-lifecycle-manager to stop VMs).

model: inherit
color: red
---

# /vm-delete Skill

Permanently delete virtual machines and their associated resources (storage, DataVolumes) from OpenShift Virtualization clusters. This skill enforces strict safety protocols including typed confirmation and pre-deletion validation.

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_get` (from openshift-virtualization) - Verify VM exists and get details
- `resources_delete` (from openshift-virtualization) - Delete Kubernetes resources
- `resources_list` (from openshift-virtualization) - List dependent resources (PVCs, DataVolumes)
- `vm_lifecycle` (from openshift-virtualization) - Stop running VMs before deletion

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to delete VirtualMachine and PVC resources
- Target VM must exist

### Prerequisite Verification

**Before executing, verify MCP server availability:**

1. **Check MCP Server Configuration**
   - Verify `openshift-virtualization` exists in `.mcp.json`
   - If missing → Report to user with setup instructions

2. **Check Environment Variables**
   - Verify `KUBECONFIG` is set (check presence only, never expose value)
   - If missing → Report to user

3. **Check RBAC Permissions** (optional verification)
   - Verify ServiceAccount can delete VirtualMachine resources
   - Verify ServiceAccount can delete PVC/DataVolume resources

**Human Notification Protocol:**

When prerequisites fail:

```
❌ Cannot execute vm-delete: MCP server 'openshift-virtualization' is not available

📋 Setup Instructions:
1. Add openshift-virtualization to .mcp.json:
   {
     "mcpServers": {
       "openshift-virtualization": {
         "command": "podman",
         "args": [
           "run",
           "--rm",
           "-i",
           "--network=host",
           "--userns=keep-id:uid=65532,gid=65532",
           "-v", "${KUBECONFIG}:/kubeconfig:ro,Z",
           "--entrypoint", "/app/kubernetes-mcp-server",
           "quay.io/ecosystem-appeng/openshift-mcp-server:latest",
           "--kubeconfig", "/kubeconfig",
           "--toolsets", "core,kubevirt"
         ],
         "env": {
           "KUBECONFIG": "${KUBECONFIG}"
         }
       }
     }
   }

2. Set KUBECONFIG environment variable:
   export KUBECONFIG="/path/to/your/kubeconfig"

3. Restart Claude Code to reload MCP servers

🔗 Documentation: https://github.com/openshift/openshift-mcp-server

❓ How would you like to proceed?
Options:
- "setup" - Help configure the MCP server now
- "skip" - Skip this skill
- "abort" - Stop workflow

Please respond with your choice.
```

⚠️ **SECURITY**: Never display actual KUBECONFIG path or credential values in output.

## When to Use This Skill

**Trigger this skill when:**
- User explicitly invokes `/vm-delete` command
- User requests permanent VM deletion
- User wants to clean up test/development VMs
- User needs to free cluster resources by removing VMs
- User wants to decommission VMs

**User phrases that trigger this skill:**
- "Delete VM test-vm in namespace dev"
- "Remove the virtual machine web-server"
- "Destroy VM old-database"
- "Clean up all VMs in namespace test"
- "/vm-delete" (explicit command)

**Do NOT use this skill when:**
- User wants to stop a VM temporarily → Use `/vm-lifecycle-manager` skill instead
- User wants to create a VM → Use `/vm-create` skill instead
- User wants to view VMs → Use `/vm-inventory` skill instead
- User wants to pause or suspend VM → Use lifecycle management (not deletion)

## Workflow

### Step 1: Gather VM Information and Validate

**CRITICAL**: This step MUST complete BEFORE asking for user confirmation.

**Required Information from User:**
1. **VM Name** - Name of the virtual machine to delete
2. **Namespace** - OpenShift namespace where VM exists

If user doesn't provide namespace, ask for it explicitly.

**Pre-Deletion Validation (Execute ALL checks):**

**1.1: Verify VM Exists**

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",  // User-provided
  "name": "<vm-name>"          // User-provided
}
```

**Expected Output**: VirtualMachine resource with metadata, spec, and status

**Error Handling**:
- If VM not found → Report error to user, suggest checking VM name/namespace with vm-inventory skill
- If permission denied → Report RBAC error

**1.2: Check Protection Label**

**From the VM resource returned in step 1.1**, check `metadata.labels` for `protected: "true"`.

**If protected label exists:**
```markdown
❌ Cannot Delete Protected VM

**VM**: `<vm-name>` (namespace: `<namespace>`)

**Protection Status**: This VM has the `protected: "true"` label.

**Reason**: Protected VMs cannot be deleted to prevent accidental removal of critical infrastructure.

**To delete this VM:**
1. Remove the protection label first:
   ```
   oc label vm <vm-name> -n <namespace> protected-
   ```
2. Then retry deletion

**Alternative**: Use vm-inventory skill to verify this is the correct VM.

Operation cancelled.
```

**STOP workflow** - Do not proceed with deletion.

**1.3: Check VM Running State**

**From the VM resource returned in step 1.1**, check `status.printableStatus` or `status.ready`.

**Running States**: "Running", "Starting", "Migrating"
**Stopped States**: "Stopped", "Halted", "Terminated"

**If VM is running:**
```markdown
⚠️ VM is Currently Running

**VM**: `<vm-name>` (namespace: `<namespace>`)
**Status**: Running

**Safety Requirement**: VMs must be stopped before deletion to ensure graceful shutdown.

**Options:**
1. "stop-and-delete" - Stop the VM first, then proceed with deletion
2. "cancel" - Cancel deletion operation

How would you like to proceed?
```

**Wait for user response.**

- If "stop-and-delete" → Continue to Step 1.4
- If "cancel" → Stop workflow, cancel operation

**1.4: Stop Running VM (if applicable)**

**ONLY execute if user chose "stop-and-delete" in step 1.3.**

**MCP Tool**: `vm_lifecycle` (from openshift-virtualization)

**Parameters**:
```json
{
  "namespace": "<namespace>",
  "name": "<vm-name>",
  "action": "stop"
}
```

**Expected Output**: VM runStrategy changed to "Halted", VM stopping

**Report to user**:
```markdown
⏸️ Stopping VM before deletion...

VM `<vm-name>` is being stopped gracefully.

Wait 10-30 seconds for VM to fully stop, then deletion will proceed.
```

**Wait 10 seconds**, then verify VM is stopped by checking status again.

**1.5: Discover Dependent Resources**

**Find DataVolumes and PVCs associated with this VM.**

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters for DataVolumes**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<namespace>",
  "labelSelector": "vm.kubevirt.io/name=<vm-name>"
}
```

**Parameters for PVCs** (if DataVolumes not found):
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>",
  "labelSelector": "vm.kubevirt.io/name=<vm-name>"
}
```

**Expected Output**: List of DataVolumes or PVCs owned by this VM

**Parse results**:
- Extract resource names
- Calculate total storage size (sum of all PVC sizes)
- Store list for deletion scope presentation

**If no storage found**: VM uses ephemeral storage or container disks (no persistent storage to delete)

### Step 2: Present Deletion Scope and Get Deletion Options

**After completing ALL validation in Step 1**, present the complete deletion scope to user.

**Display deletion scope:**

```markdown
## ⚠️ VM Deletion - Review Scope

**Virtual Machine**: `<vm-name>`
**Namespace**: `<namespace>`
**Current Status**: <Stopped|Running> (stopped in step 1.4 if was running)

### Resources Found

**VirtualMachine Resource:**
- VM: `<vm-name>`
- Age: <age>
- vCPU: <cpu>, Memory: <memory>

**Persistent Storage:** (if found)
- DataVolume: `<dv-name>` (30Gi)
- PVC: `<pvc-name>` (30Gi)
- **Total Storage**: 30Gi

**OR** (if no storage found)

**Persistent Storage:**
- None (VM uses ephemeral/container disk storage)

---

### Deletion Options

**What should be deleted?**

**Option 1: VM Only** (preserve storage)
- Deletes: VirtualMachine resource
- Preserves: DataVolumes and PVCs for potential reuse
- Use case: Recreating VM with same storage later

**Option 2: VM + Storage** (complete cleanup) ← Recommended for test/dev VMs
- Deletes: VirtualMachine resource
- Deletes: All DataVolumes and PVCs
- Frees: 30Gi cluster storage
- Use case: Permanently removing VM and reclaiming resources

**Option 3: Cancel**
- No resources deleted
- VM remains in cluster

---

**Select deletion option** (1, 2, or 3):
```

**Wait for user to select option 1, 2, or 3.**

**Handle user response:**
- If "3" or "cancel" → Cancel operation, stop workflow
- If "1" → Proceed to Step 3 with delete_storage=false
- If "2" → Proceed to Step 3 with delete_storage=true

### Step 3: Typed Confirmation (MANDATORY)

**CRITICAL**: User MUST type the exact VM name to proceed.

**Present typed confirmation prompt:**

```markdown
## 🔴 PERMANENT DELETION - Typed Confirmation Required

**This action CANNOT be undone.**

### What will be deleted:

✗ VirtualMachine: `<vm-name>` (namespace: `<namespace>`)
<if delete_storage=true>
✗ DataVolume: `<dv-name>` (30Gi)
✗ PVC: `<pvc-name>` (30Gi)
✗ **All VM data will be lost permanently**
</if>

<if delete_storage=false>
✓ Storage PRESERVED: DataVolumes and PVCs will remain for reuse
</if>

---

**⚠️ IMPORTANT**: This deletion is permanent. Deleted resources cannot be recovered.

**To confirm deletion, type the VM name exactly as shown:**

Type `<vm-name>` to confirm: _____
```

**Wait for user to type the VM name.**

**Validation:**
- Compare user input with VM name (case-sensitive, exact match)
- **If match**: Proceed to Step 4
- **If mismatch**: Cancel operation

**On mismatch:**
```markdown
❌ Confirmation Failed

**You typed**: `<user-input>`
**Expected**: `<vm-name>`

**Names do not match.** Deletion cancelled for safety.

To retry, use:
```
"Delete VM <vm-name> in namespace <namespace>"
```

Operation cancelled. No resources were deleted.
```

**STOP workflow** - Do not proceed with deletion.

### Step 4: Final Confirmation Before Execution

**After typed verification succeeds**, ask for final explicit confirmation.

```markdown
## ✓ Typed Verification Passed

**Confirmation received for VM**: `<vm-name>`

### Ready to Delete:

<if delete_storage=true>
- VirtualMachine: `<vm-name>`
- DataVolume: `<dv-name>` (30Gi)
- PVC: `<pvc-name>` (30Gi)

**Impact**: VM and all associated data will be permanently deleted. 30Gi storage will be freed.
</if>

<if delete_storage=false>
- VirtualMachine: `<vm-name>` (storage preserved)

**Impact**: VM will be deleted. DataVolumes and PVCs will remain for potential reuse.
</if>

---

**Proceed with permanent deletion?**
- Type "yes" to execute deletion
- Type "cancel" to abort

Your choice: _____
```

**Wait for user response.**

**Handle response:**
- If "yes" → Proceed to Step 5 (execute deletion)
- If "cancel", "no", "wait", or anything else → Cancel operation

**On cancellation:**
```markdown
Operation cancelled by user. No resources were deleted.

VM `<vm-name>` remains in namespace `<namespace>`.
```

**STOP workflow**.

### Step 5: Execute Deletion

**ONLY PROCEED AFTER**:
- ✓ Step 1: Validation complete
- ✓ Step 2: User selected deletion option
- ✓ Step 3: User typed VM name correctly
- ✓ Step 4: User confirmed "yes"

**5.1: Delete VirtualMachine Resource**

**MCP Tool**: `resources_delete` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

**Expected Output**: VirtualMachine deleted successfully

**Error Handling**:
- If deletion fails → Report error, do not proceed with storage deletion
- If permission denied → Report RBAC error
- If VM not found → May have been deleted externally, continue anyway

**Report progress:**
```markdown
🗑️ Deleting VirtualMachine resource...
✓ VirtualMachine `<vm-name>` deleted
```

**5.2: Delete Storage (if delete_storage=true)**

**ONLY execute if user selected Option 2 in Step 2.**

**For each DataVolume found in Step 1.5:**

**MCP Tool**: `resources_delete` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<namespace>",
  "name": "<datavolume-name>"
}
```

**For each PVC found in Step 1.5** (if DataVolumes not used):

**MCP Tool**: `resources_delete` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<namespace>",
  "name": "<pvc-name>"
}
```

**Expected Output**: Storage resources deleted successfully

**Error Handling**:
- If deletion fails → Report which resources failed, continue with others
- If permission denied → Report RBAC error for specific resource

**Report progress for each deletion:**
```markdown
🗑️ Deleting storage resources...
✓ DataVolume `<dv-name>` deleted (30Gi freed)
✓ PVC `<pvc-name>` deleted
```

### Step 6: Report Deletion Results

**On successful deletion:**

**If delete_storage=true (complete cleanup):**
```markdown
## ✓ VM Deleted Successfully (Complete Cleanup)

**Deleted Resources:**
- ✓ VirtualMachine: `<vm-name>` (namespace: `<namespace>`)
- ✓ DataVolume: `<dv-name>`
- ✓ PVC: `<pvc-name>`

**Storage Freed**: 30Gi

**Impact:**
- VM and all associated data permanently removed
- Cluster resources freed
- VM cannot be recovered

**To verify deletion:**
```
"List VMs in namespace <namespace>"
```

The VM should no longer appear in the inventory.
```

**If delete_storage=false (storage preserved):**
```markdown
## ✓ VM Deleted Successfully (Storage Preserved)

**Deleted Resources:**
- ✓ VirtualMachine: `<vm-name>` (namespace: `<namespace>`)

**Preserved Resources:**
- ✓ DataVolume: `<dv-name>` (30Gi) - Available for reuse
- ✓ PVC: `<pvc-name>` (30Gi) - Available for reuse

**Impact:**
- VM removed from cluster
- Storage remains available for attaching to new VMs
- Data preserved on PVCs

**To reuse storage:**
Create a new VM and reference the existing DataVolume or PVC.

**To delete storage later:**
```
oc delete datavolume <dv-name> -n <namespace>
oc delete pvc <pvc-name> -n <namespace>
```
```

**On partial failure (VM deleted but storage deletion failed):**

**OPTIONAL**: If storage deletion fails, consult documentation for storage-related deletion issues.

**Document Consultation** (OPTIONAL - when storage deletion fails):
1. **Action**: Read [storage-errors.md](../../docs/troubleshooting/storage-errors.md) using the Read tool to understand storage deletion issues and PVC cleanup strategies
2. **Output to user**: "I consulted [storage-errors.md](../../docs/troubleshooting/storage-errors.md) to understand the storage deletion failure."

```markdown
## ⚠️ Partial Deletion Completed

**Successfully Deleted:**
- ✓ VirtualMachine: `<vm-name>`

**Failed to Delete:**
- ✗ DataVolume: `<dv-name>` - Error: <error-message>
- ✗ PVC: `<pvc-name>` - Error: <error-message>

**Storage remains in cluster.** You may need to delete these resources manually:

```
oc delete datavolume <dv-name> -n <namespace>
oc delete pvc <pvc-name> -n <namespace>
```

**Possible causes:**
- Insufficient RBAC permissions to delete PVCs
- PVC in use by another resource
- Storage class retention policy

Would you like help troubleshooting the storage deletion failure?
```

**On complete failure (VM deletion failed):**

**OPTIONAL**: If deletion operation fails, consult documentation for common deletion failure scenarios.

**Document Consultation** (OPTIONAL - when deletion fails):
1. **Action**: Read [lifecycle-errors.md](../../docs/troubleshooting/lifecycle-errors.md) using the Read tool to understand VM deletion failure scenarios, finalizer issues, and stuck Terminating states
2. **Output to user**: "I consulted [lifecycle-errors.md](../../docs/troubleshooting/lifecycle-errors.md) to understand potential causes for the deletion failure."

**When to consult**:
- VM deletion fails with finalizer errors
- VM stuck in Terminating state
- Storage deletion fails (PVC/DataVolume errors)
- Unexpected error messages from resources_delete tool

**When NOT to consult**:
- Simple "VM not found" errors (clear cause)
- RBAC permission errors (clear cause)
- Namespace doesn't exist (clear cause)

```markdown
## ❌ VM Deletion Failed

**Error**: <error-message-from-tool>

**VM**: `<vm-name>` (namespace: `<namespace>`)

**Common Causes:**
- **Insufficient RBAC permissions** - ServiceAccount lacks delete permission for VirtualMachines
- **VM not found** - May have been deleted externally
- **Finalizers blocking deletion** - VM has finalizers preventing deletion
- **Resource in use** - VM or associated resources locked by another process

**Troubleshooting Steps:**

1. **Check permissions:**
   ```
   oc auth can-i delete virtualmachines -n <namespace>
   ```

2. **Verify VM exists:**
   ```
   "List VMs in namespace <namespace>"
   ```

3. **Check for finalizers:**

   Consult [lifecycle-errors.md](../../docs/troubleshooting/lifecycle-errors.md) "VM Stuck in Terminating State" section for MCP-first diagnostic steps using `resources_get` to check finalizers.

4. **Manual deletion (if needed):**

   Use `resources_delete` MCP tool or consult [lifecycle-errors.md](../../docs/troubleshooting/lifecycle-errors.md) for proper deletion procedure.

Would you like help troubleshooting this error?
```

## Advanced Features

### Dry-Run Mode (Preview Deletion)

Allow user to preview what would be deleted without actually deleting.

**User request:** "Show me what would be deleted if I delete VM test-vm"

**Workflow:**
1. Execute Step 1 (validation and discovery)
2. Execute Step 2 (present deletion scope)
3. **Skip Steps 3-5** (no confirmation, no deletion)
4. Report: "This is a preview. No resources were deleted."

**Output:**
```markdown
## 🔍 Deletion Preview (Dry-Run)

**If you delete VM** `test-vm` **(namespace:** `dev`**):**

**Would be deleted (Option 1 - VM only):**
- VirtualMachine: `test-vm`

**Would be deleted (Option 2 - VM + storage):**
- VirtualMachine: `test-vm`
- DataVolume: `test-vm-disk` (30Gi)
- PVC: `test-vm-disk` (30Gi)
- **Storage freed**: 30Gi

**Would be preserved:**
- None (complete cleanup)

---

**This is a preview only. No resources were deleted.**

To execute deletion:
```
"Delete VM test-vm in namespace dev"
```
```

### Batch Deletion (Multiple VMs)

**User request:** "Delete VMs test-01, test-02, test-03 in namespace dev"

**Workflow:**
1. Execute Step 1 (validation) **for each VM**
2. Present combined deletion scope for all VMs
3. Require typed confirmation: "type 'DELETE-3-VMS' to confirm"
4. Execute deletion for each VM sequentially

**Typed confirmation for batch:**
```markdown
## 🔴 BATCH DELETION - Typed Confirmation Required

**Deleting 3 VMs in namespace** `dev`**:**

1. ✗ VirtualMachine: `test-01` + storage (30Gi)
2. ✗ VirtualMachine: `test-02` + storage (30Gi)
3. ✗ VirtualMachine: `test-03` + storage (30Gi)

**Total Impact:**
- 3 VMs permanently deleted
- 90Gi storage freed
- All VM data lost

**To confirm batch deletion, type:** `DELETE-3-VMS`

Type confirmation: _____
```

### Protected VM Label Check

**Automatic protection enforcement:**

If VM has label `protected: "true"`, **refuse deletion** in Step 1.2.

**Example VM with protection:**
```yaml
metadata:
  name: production-database
  labels:
    protected: "true"
    env: production
```

**Skill response:**
```markdown
❌ Cannot Delete Protected VM

**VM**: `production-database` has protection enabled.

**To delete:**
1. Remove protection: `oc label vm production-database protected- -n <namespace>`
2. Retry deletion

This safeguard prevents accidental deletion of critical infrastructure.
```

## Common Issues

### Issue 1: VM Not Found

**Error**: "VirtualMachine 'xyz' not found in namespace 'abc'"

**Solution:**
1. Verify VM name spelling
2. Check namespace is correct
3. List VMs in namespace: Use `/vm-inventory` skill
4. VM may have already been deleted

### Issue 2: Permission Denied

**Error**: "Forbidden: User cannot delete VirtualMachines in namespace 'xyz'"

**Solution:**
- Verify KUBECONFIG has appropriate RBAC permissions
- Required permissions: delete VirtualMachine, delete PVC, delete DataVolume
- Contact cluster admin for permission grant
- Check ServiceAccount role bindings:
  ```
  oc auth can-i delete virtualmachines -n <namespace>
  oc auth can-i delete persistentvolumeclaims -n <namespace>
  ```

### Issue 3: VM Has Finalizers

**Error**: "VM deletion blocked by finalizers"

**Solution:**
- VMs with finalizers require finalizer removal before deletion
- Consult [lifecycle-errors.md](../../docs/troubleshooting/lifecycle-errors.md) "VM Stuck in Terminating State" section for MCP-first approach:
  - Use `resources_get` to check finalizers
  - Use `resources_create_or_update` to remove finalizers (if needed)
- Common finalizers: `kubevirt.io/virtualMachineControllerFinalize`
- Wait for controllers to remove finalizers, or manually patch VM (advanced)

### Issue 4: Storage Deletion Fails

**Error**: "PVC deletion failed: resource in use"

**Solution:**
1. Verify VM was deleted first (VMs must be deleted before storage)
2. Consult [storage-errors.md](../../docs/troubleshooting/storage-errors.md) "Storage Deletion Failures" section for MCP-first diagnostics:
   - Use `pods_list_in_namespace` to check if PVC is mounted by other resources
   - Use `resources_get` to check PVC status
3. Wait for VM pod termination (can take 30-60 seconds)
4. Use `resources_delete` to delete PVC, or consult storage-errors.md for proper procedure

### Issue 5: User Typed Wrong VM Name

**Error**: User typed "test-vm-01" instead of "test-vm"

**Solution:**
- **Skill automatically cancels** operation (Step 3 validation)
- No resources deleted
- User must retry with correct typed confirmation

**Example:**
```markdown
❌ Confirmation Failed

You typed: `test-vm-01`
Expected: `test-vm`

Names do not match. Deletion cancelled for safety.
```

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with core and kubevirt toolsets

### Required MCP Tools
- `resources_get` (from openshift-virtualization) - Get VirtualMachine details and verify existence
  - Parameters: apiVersion, kind, namespace, name
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go

- `resources_delete` (from openshift-virtualization) - Delete Kubernetes resources
  - Parameters: apiVersion, kind, namespace, name
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go

- `resources_list` (from openshift-virtualization) - List dependent resources (DataVolumes, PVCs)
  - Parameters: apiVersion, kind, namespace, labelSelector
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go

- `vm_lifecycle` (from openshift-virtualization) - Stop running VMs before deletion
  - Parameters: namespace, name, action
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/kubevirt/vm.go

### Related Skills
- `vm-inventory` - Verify VM exists and get details before deletion
- `vm-lifecycle-manager` - Stop running VMs before deletion (used internally by vm-delete)
- `vm-create` - Create VMs after cleanup operations

### Reference Documentation
- [lifecycle-errors.md](../../docs/troubleshooting/lifecycle-errors.md) - VM deletion failure scenarios, finalizer issues, and stuck Terminating states (optionally consulted when deletion operations fail)
- [storage-errors.md](../../docs/troubleshooting/storage-errors.md) - Storage deletion strategies and PVC cleanup procedures (optionally consulted when storage deletion fails)
- [Troubleshooting INDEX](../../docs/troubleshooting/INDEX.md) - Navigation hub for discovering additional error categories when encountering unexpected issues outside the categories above
- [OpenShift Virtualization Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt/about_virt/about-virt.html)
- [KubeVirt VirtualMachine API](https://kubevirt.io/api-reference/)
- [Kubernetes Finalizers](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/)
- [PVC Deletion](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#delete)
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server)

## Critical: Human-in-the-Loop Requirements

**CRITICAL: This skill performs IRREVERSIBLE operations.** You MUST:

1. **Pre-Deletion Validation** (Execute FIRST, before asking for confirmation)
   - Verify VM exists using `resources_get`
   - Check VM running state
   - Discover dependent resources (DataVolumes, PVCs)
   - Check for protection labels (`protected: "true"`)

2. **Safety Checks**
   - **REFUSE deletion** if VM has label `protected: "true"`
   - **REQUIRE VM to be stopped first** if currently running
   - **List all resources** that will be deleted (VM, storage, DataVolumes)

3. **Typed Confirmation Protocol** (MANDATORY)
   - Display complete deletion scope
   - **Require user to type the exact VM name** to confirm
   - Accept only exact match (case-sensitive)
   - If name doesn't match → Cancel operation, do not proceed

4. **Deletion Options**
   - Ask user what to delete:
     - Option 1: VM only (preserve storage)
     - Option 2: VM + storage (complete cleanup)
     - Option 3: Cancel
   - **NEVER assume** which option user wants

5. **Final Confirmation Before Each Deletion**
   - After typed confirmation, show exactly what will be deleted
   - Ask: "Proceed with permanent deletion? (yes/cancel)"
   - Wait for explicit "yes"

6. **Never Auto-Execute**
   - **NEVER delete without explicit typed confirmation**
   - **NEVER proceed if user says "no", "wait", "cancel"**
   - **NEVER skip the typed verification step**

**Why This Matters:**
- **Permanent**: Deleted VMs cannot be recovered
- **Data Loss**: Storage deletion destroys all VM data
- **Service Impact**: Deleting running VMs causes immediate service outage
- **Accidental Deletion**: Typed verification prevents mistakes (typos, wrong VM name)

## Security Considerations

- **RBAC Enforcement**: Deletion requires explicit RBAC permissions for VirtualMachine, PVC, and DataVolume resources
- **Typed Verification**: Prevents accidental deletion through typos or wrong VM names
- **Protection Labels**: `protected: "true"` label blocks deletion entirely
- **Audit Trail**: All deletions logged in Kubernetes API audit logs
- **Graceful Shutdown**: Running VMs stopped before deletion to ensure clean shutdown
- **KUBECONFIG Security**: Credentials never exposed in output
- **Namespace Isolation**: Can only delete VMs in namespaces where ServiceAccount has permissions
- **No Force Delete**: Skill does not use `--force` or `--grace-period=0` flags

## Example Usage

### Example 1: Delete VM with Storage (Complete Cleanup)

```
User: "Delete VM test-vm in namespace dev"

Agent: [Invokes /vm-delete skill]
       [Step 1: Validation]
       [Calls resources_get to verify VM exists]
       [Checks protection label - none found]
       [Checks VM status - Stopped]
       [Calls resources_list to find DataVolumes/PVCs]
       [Found: test-vm-disk DataVolume, 30Gi]

## ⚠️ VM Deletion - Review Scope

Virtual Machine: `test-vm`
Namespace: `dev`
Current Status: Stopped

### Resources Found

VirtualMachine Resource:
- VM: `test-vm`
- Age: 5 days
- vCPU: 2, Memory: 4Gi

Persistent Storage:
- DataVolume: `test-vm-disk` (30Gi)
- PVC: `test-vm-disk` (30Gi)
- Total Storage: 30Gi

---

### Deletion Options

What should be deleted?

Option 1: VM Only (preserve storage)
- Deletes: VirtualMachine resource
- Preserves: DataVolumes and PVCs for potential reuse

Option 2: VM + Storage (complete cleanup) ← Recommended for test/dev VMs
- Deletes: VirtualMachine resource
- Deletes: All DataVolumes and PVCs
- Frees: 30Gi cluster storage

Option 3: Cancel
- No resources deleted

Select deletion option (1, 2, or 3):

User: "2"

Agent: [Step 2: User selected Option 2 - delete VM + storage]
       [Step 3: Typed confirmation]

## 🔴 PERMANENT DELETION - Typed Confirmation Required

This action CANNOT be undone.

### What will be deleted:

✗ VirtualMachine: `test-vm` (namespace: `dev`)
✗ DataVolume: `test-vm-disk` (30Gi)
✗ PVC: `test-vm-disk` (30Gi)
✗ All VM data will be lost permanently

---

⚠️ IMPORTANT: This deletion is permanent. Deleted resources cannot be recovered.

To confirm deletion, type the VM name exactly as shown:

Type `test-vm` to confirm:

User: "test-vm"

Agent: [Step 3: Typed verification passed]
       [Step 4: Final confirmation]

## ✓ Typed Verification Passed

Confirmation received for VM: `test-vm`

### Ready to Delete:

- VirtualMachine: `test-vm`
- DataVolume: `test-vm-disk` (30Gi)
- PVC: `test-vm-disk` (30Gi)

Impact: VM and all associated data will be permanently deleted. 30Gi storage will be freed.

---

Proceed with permanent deletion?
- Type "yes" to execute deletion
- Type "cancel" to abort

Your choice:

User: "yes"

Agent: [Step 5: Execute deletion]
       [Calls resources_delete for VirtualMachine]

🗑️ Deleting VirtualMachine resource...
✓ VirtualMachine `test-vm` deleted

       [Calls resources_delete for DataVolume]

🗑️ Deleting storage resources...
✓ DataVolume `test-vm-disk` deleted (30Gi freed)
✓ PVC `test-vm-disk` deleted

       [Step 6: Report results]

## ✓ VM Deleted Successfully (Complete Cleanup)

Deleted Resources:
- ✓ VirtualMachine: `test-vm` (namespace: `dev`)
- ✓ DataVolume: `test-vm-disk`
- ✓ PVC: `test-vm-disk`

Storage Freed: 30Gi

Impact:
- VM and all associated data permanently removed
- Cluster resources freed
- VM cannot be recovered

To verify deletion:
```
"List VMs in namespace dev"
```

The VM should no longer appear in the inventory.
```

### Example 2: Delete VM Only (Preserve Storage)

```
User: "Delete VM web-server but keep the storage"

Agent: "Which namespace is the VM in?"

User: "production"

Agent: [Invokes /vm-delete skill]
       [Step 1: Validation]
       [VM exists, stopped, has storage]
       [Step 2: Present deletion scope]

## ⚠️ VM Deletion - Review Scope

Virtual Machine: `web-server`
Namespace: `production`

[... deletion scope details ...]

Select deletion option (1, 2, or 3):

User: "1"

Agent: [Step 3: Typed confirmation]

## 🔴 PERMANENT DELETION - Typed Confirmation Required

### What will be deleted:

✗ VirtualMachine: `web-server` (namespace: `production`)

✓ Storage PRESERVED: DataVolumes and PVCs will remain for reuse

Type `web-server` to confirm:

User: "web-server"

Agent: [Typed verification passed]

## ✓ Typed Verification Passed

Ready to Delete:
- VirtualMachine: `web-server` (storage preserved)

Impact: VM will be deleted. DataVolumes and PVCs will remain for potential reuse.

Proceed with permanent deletion? (yes/cancel):

User: "yes"

Agent: [Deletes VM only]

## ✓ VM Deleted Successfully (Storage Preserved)

Deleted Resources:
- ✓ VirtualMachine: `web-server` (namespace: `production`)

Preserved Resources:
- ✓ DataVolume: `web-server-disk` (50Gi) - Available for reuse
- ✓ PVC: `web-server-disk` (50Gi) - Available for reuse

Impact:
- VM removed from cluster
- Storage remains available for attaching to new VMs
- Data preserved on PVCs
```

### Example 3: Protected VM (Deletion Refused)

```
User: "Delete VM production-database in namespace production"

Agent: [Invokes /vm-delete skill]
       [Step 1: Validation]
       [Calls resources_get]
       [Checks protection label - found "protected: true"]

❌ Cannot Delete Protected VM

VM: `production-database` (namespace: `production`)

Protection Status: This VM has the `protected: "true"` label.

Reason: Protected VMs cannot be deleted to prevent accidental removal of critical infrastructure.

To delete this VM:
1. Remove the protection label first:
   ```
   oc label vm production-database -n production protected-
   ```
2. Then retry deletion

Alternative: Use vm-inventory skill to verify this is the correct VM.

Operation cancelled.
```

### Example 4: Stop Running VM Before Deletion

```
User: "Delete VM api-server in namespace production"

Agent: [Invokes /vm-delete skill]
       [Step 1: Validation]
       [VM exists, RUNNING]
       [Step 1.3: VM is running]

⚠️ VM is Currently Running

VM: `api-server` (namespace: `production`)
Status: Running

Safety Requirement: VMs must be stopped before deletion to ensure graceful shutdown.

Options:
1. "stop-and-delete" - Stop the VM first, then proceed with deletion
2. "cancel" - Cancel deletion operation

How would you like to proceed?

User: "stop-and-delete"

Agent: [Step 1.4: Stop VM]
       [Calls vm_lifecycle with action="stop"]

⏸️ Stopping VM before deletion...

VM `api-server` is being stopped gracefully.

Wait 10-30 seconds for VM to fully stop, then deletion will proceed.

       [Waits 10 seconds]
       [Verifies VM stopped]
       [Continues to Step 2: Present deletion scope]
       [...rest of workflow...]
```

### Example 5: User Cancels at Typed Confirmation

```
User: "Delete VM test-vm in namespace dev"

Agent: [Validation complete]
       [User selects Option 2 - VM + storage]
       [Step 3: Typed confirmation]

Type `test-vm` to confirm:

User: "wait, cancel this"

Agent: ❌ Confirmation Failed

You typed: `wait, cancel this`
Expected: `test-vm`

Names do not match. Deletion cancelled for safety.

To retry, use:
```
"Delete VM test-vm in namespace dev"
```

Operation cancelled. No resources were deleted.
```

### Example 6: Dry-Run Preview

```
User: "What would happen if I delete VM test-vm in dev?"

Agent: [Invokes /vm-delete skill in dry-run mode]
       [Step 1: Validation and discovery only]

## 🔍 Deletion Preview (Dry-Run)

If you delete VM `test-vm` (namespace: `dev`):

Would be deleted (Option 1 - VM only):
- VirtualMachine: `test-vm`

Would be deleted (Option 2 - VM + storage):
- VirtualMachine: `test-vm`
- DataVolume: `test-vm-disk` (30Gi)
- PVC: `test-vm-disk` (30Gi)
- Storage freed: 30Gi

Would be preserved:
- None (complete cleanup)

---

This is a preview only. No resources were deleted.

To execute deletion:
```
"Delete VM test-vm in namespace dev"
```
```

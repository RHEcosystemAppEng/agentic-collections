---
name: vm-snapshot-delete
description: |
  Permanently delete virtual machine snapshots to free storage space.

  Use when:
  - "Delete snapshot [snapshot-name]"
  - "Remove old snapshots for VM [name]"
  - "Free up snapshot storage"

  Requires user confirmation before deletion.

  NOT for restoring VMs (use vm-snapshot-restore instead).

model: inherit
color: yellow
---

# /vm-snapshot-delete Skill

Permanently delete virtual machine snapshots in OpenShift Virtualization. Deleting snapshots frees storage but removes recovery points.

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_get` (from openshift-virtualization) - Verify snapshot exists
- `resources_list` (from openshift-virtualization) - List related snapshots
- `resources_delete` (from openshift-virtualization) - Delete snapshot

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to delete VirtualMachineSnapshot resources

### Prerequisite Verification

**Before executing, verify MCP server availability:**

1. **Check MCP Server Configuration**
   - Verify `openshift-virtualization` exists in `.mcp.json`
   - If missing → Report to user with setup instructions

2. **Check Environment Variables**
   - Verify `KUBECONFIG` is set (check presence only, never expose value)
   - If missing → Report to user

## When to Use This Skill

**Trigger this skill when:**
- User wants to free storage by removing old snapshots
- User wants to delete a specific snapshot
- User wants to implement snapshot retention policies

**User phrases that trigger this skill:**
- "Delete snapshot pre-upgrade-backup"
- "Remove old snapshots for VM database-01"
- "Delete all snapshots older than 7 days"
- "Free up snapshot storage"

**Do NOT use this skill when:**
- User wants to create snapshots → Use `vm-snapshot-create` skill
- User wants to restore from snapshot → Use `vm-snapshot-restore` skill
- User wants to list snapshots → Use `vm-snapshot-list` skill

## Workflow

### Step 1: Gather Delete Information

**Required Information from User:**
1. **Snapshot Name** - Name of snapshot to delete
2. **Namespace** - Namespace where snapshot exists

If namespace not provided, ask for it.

### Step 2: Verify Snapshot Exists

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "snapshot.kubevirt.io/v1beta1",
  "kind": "VirtualMachineSnapshot",
  "namespace": "<namespace>",
  "name": "<snapshot-name>"
}
```

**Expected Output**: VirtualMachineSnapshot resource

**Error Handling**:
- If snapshot not found → Report error

**If snapshot not found:**
```markdown
❌ Snapshot Not Found

**Snapshot**: `<snapshot-name>` not found in namespace `<namespace>`.

**To list available snapshots:**
"List snapshots in namespace <namespace>"

Delete operation cancelled.
```

**STOP workflow**.

**If snapshot found**, extract snapshot details:
- `spec.source.name` - VM name
- `metadata.creationTimestamp` - Creation timestamp
- `status.phase` - Snapshot status
- Calculate age from creationTimestamp

### Step 3: List Other Snapshots for Same VM

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "snapshot.kubevirt.io/v1beta1",
  "kind": "VirtualMachineSnapshot",
  "namespace": "<namespace>",
  "labelSelector": "vm.kubevirt.io/name=<vm-name>"
}
```

**Fallback**: If label selector doesn't work, list all snapshots and filter by `spec.source.name`.

**Count snapshots** for the VM to determine if this is the last snapshot.

### Step 4: Present Snapshot Details and Confirm Deletion

```markdown
## ⚠️ Snapshot Deletion - Review

**Snapshot to Delete**: `<snapshot-name>`

### Snapshot Details
- **Snapshot Name**: `<snapshot-name>`
- **VM**: `<vm-name>`
- **Namespace**: `<namespace>`
- **Created**: <creation-timestamp>
- **Age**: <snapshot-age>
- **Status**: <status>

### Impact of Deletion
- ✗ Snapshot will be permanently deleted
- ✗ This recovery point will be lost
- ✗ Cannot restore VM to this snapshot state after deletion
- ✓ Storage will be freed

### Recovery Impact
**Before deletion, consider:**
- Is this snapshot still needed for recovery?
- Are there other recovery points available?
- Could you need to restore to this state in the future?

**Available snapshots for VM `<vm-name>`:**
<list other snapshots for the same VM, if any>

<if no other snapshots>
⚠️ **WARNING**: This is the ONLY snapshot for VM `<vm-name>`. After deletion, no snapshot recovery points will exist.
</if>

---

**Proceed with snapshot deletion? This action cannot be undone. (yes/no)**
```

**Wait for user confirmation.**

**Handle response:**
- If "yes" → Proceed to Step 5 (execute deletion)
- If "no", "cancel", or anything else → Cancel operation

**On cancellation:**
```markdown
Snapshot deletion cancelled by user. Snapshot `<snapshot-name>` preserved.
```

**STOP workflow**.

### Step 5: Delete the Snapshot

**ONLY PROCEED AFTER user confirmation in Step 4.**

**MCP Tool**: `resources_delete` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "snapshot.kubevirt.io/v1beta1",
  "kind": "VirtualMachineSnapshot",
  "namespace": "<namespace>",
  "name": "<snapshot-name>"
}
```

**Example tool invocation:**
```json
resources_delete({
  "apiVersion": "snapshot.kubevirt.io/v1beta1",
  "kind": "VirtualMachineSnapshot",
  "namespace": "production",
  "name": "old-snapshot"
})
```

**Expected Output**: VirtualMachineSnapshot deleted successfully

**Error Handling**:
- If snapshot not found → Report error (may have been deleted externally)
- If permission denied → Report RBAC error
- If snapshot in use → Report error (snapshot may be in restore process)

**Report progress:**
```markdown
🗑️ Deleting snapshot...
✓ Snapshot `<snapshot-name>` deleted
```

### Step 6: Report Deletion Results

**On success:**

```markdown
## ✓ Snapshot Deleted Successfully

**Snapshot**: `<snapshot-name>` (VM: `<vm-name>`, namespace: `<namespace>`)

### Deletion Summary
- ✓ Snapshot permanently deleted
- ✓ Storage freed
- ✓ Recovery point removed

### Impact
- ✗ Cannot restore VM to <snapshot-creation-timestamp> state
- ✗ Snapshot `<snapshot-name>` no longer available

<if other snapshots exist>
### Remaining Snapshots for VM `<vm-name>`

<list remaining snapshots>

These snapshots are still available for recovery.
</if>

<if no other snapshots>
⚠️ **No snapshots remain** for VM `<vm-name>`. Consider creating new snapshots for future recovery points.
</if>

---

### Next Steps

**To create a new snapshot:**
"Create snapshot of VM <vm-name>"

**To list remaining snapshots:**
"List snapshots for VM <vm-name>"
```

**On failure:**

```markdown
## ❌ Snapshot Deletion Failed

**Error**: <error-message>

**Snapshot**: `<snapshot-name>` (VM: `<vm-name>`, namespace: `<namespace>`)

**Common Causes:**
- **Snapshot not found** - May have been deleted externally
- **Insufficient RBAC permissions** - ServiceAccount lacks delete permissions
- **Snapshot in use** - Snapshot may be in active restore process
- **Storage backend error** - CSI driver or storage backend issue

**Troubleshooting Steps:**

1. **Verify snapshot still exists:**
   "List snapshots for VM <vm-name>"

2. **Check if snapshot is being used for restore:**
   Use `resources_list` to check for active VirtualMachineRestore resources

3. **Check permissions:**
   Use CLI: `oc auth can-i delete virtualmachinesnapshots -n <namespace>`

4. **Wait and retry** if snapshot is in use by restore operation

Would you like help troubleshooting this error?
```

## Common Issues

### Issue 1: Snapshot Not Found

**Error**: "Snapshot `<name>` not found in namespace `<namespace>`"

**Cause**: Snapshot doesn't exist, was deleted, or wrong namespace/name.

**Solution:**
1. List snapshots to verify name: "List snapshots in namespace <namespace>"
2. Check spelling (names are case-sensitive)
3. Try listing in other namespaces if unsure

### Issue 2: Snapshot In Use During Restore

**Error**: "Snapshot is in use by restore operation"

**Cause**: An active VirtualMachineRestore is using this snapshot.

**Solution:**
1. Check for active restores: Use `resources_list` with apiVersion="snapshot.kubevirt.io/v1beta1", kind="VirtualMachineRestore"
2. Wait for restore to complete, or delete the VirtualMachineRestore resource
3. Retry snapshot deletion

### Issue 3: Permission Denied

**Error**: "Forbidden: User lacks permissions to delete virtualmachinesnapshots"

**Cause**: Missing RBAC permissions for snapshot deletion.

**Solution:**
1. Check permissions: `oc auth can-i delete virtualmachinesnapshots -n <namespace>`
2. Contact cluster admin to grant delete permissions for virtualmachinesnapshots
3. Required permissions: delete verb on snapshot.kubevirt.io/virtualmachinesnapshots

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with kubevirt toolset

### Required MCP Tools
- `resources_get` (from openshift-virtualization) - Get snapshot details
  - Parameters: apiVersion, kind, namespace, name
  - Source: https://github.com/openshift/openshift-mcp-server

- `resources_list` (from openshift-virtualization) - List related snapshots
  - Parameters: apiVersion, kind, namespace, labelSelector
  - Source: https://github.com/openshift/openshift-mcp-server

- `resources_delete` (from openshift-virtualization) - Delete Kubernetes resources
  - Parameters: apiVersion, kind, namespace, name
  - Source: https://github.com/openshift/openshift-mcp-server

### Related Skills
- `vm-snapshot-list` - List snapshots before deletion
- `vm-snapshot-create` - Create new snapshots
- `vm-snapshot-restore` - Restore VMs from snapshots

### Reference Documentation
- [OpenShift Virtualization Snapshots](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt-managing-vm-snapshots)
- [KubeVirt VM Snapshots](https://kubevirt.io/user-guide/operations/snapshot_restore_api/)

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill performs destructive operations. You MUST:

1. **Before Deleting Snapshots**
   - Show snapshot details (VM, age, size)
   - Confirm snapshot won't be needed for recovery
   - List other available snapshots for the VM
   - Ask: "Proceed with snapshot deletion? (yes/no)"
   - Wait for explicit "yes"

2. **Never Auto-Execute**
   - **NEVER delete without user confirmation**
   - **ALWAYS show what will be lost before deletion**

**Why This Matters:**
- **Recovery Point Loss**: Deleting snapshots removes recovery options permanently
- **No Undo**: Snapshot deletion cannot be reversed
- **Last Snapshot Warning**: Users must know if deleting the only snapshot for a VM

## Security Considerations

- **RBAC Enforcement**: Requires delete permissions for VirtualMachineSnapshot resources
- **User Confirmation**: Always requires explicit "yes" before deletion
- **Last Snapshot Warning**: Warns users when deleting the only snapshot for a VM
- **Namespace Isolation**: Snapshots scoped to namespace boundaries
- **Audit Trail**: Deletions logged in Kubernetes API audit logs

## Example Usage

```
User: "Delete snapshot database-01-daily-backup"

Agent: "Which namespace is the snapshot in?"

User: "production"

Agent: [Invokes vm-snapshot-delete skill]
       [Step 2: Verifies snapshot exists]
       [Step 3: Lists other snapshots]
       [Step 4: Presents deletion confirmation]

## ⚠️ Snapshot Deletion - Review

Snapshot to Delete: `database-01-daily-backup`

Snapshot Details:
- Name: `database-01-daily-backup`
- VM: `database-01`
- Namespace: `production`
- Created: 2024-01-14 02:00:00 UTC
- Age: 1 day

Impact of Deletion:
- ✗ Snapshot will be permanently deleted
- ✗ This recovery point will be lost
- ✓ Storage will be freed

Available snapshots for VM `database-01`:
- `database-01-pre-upgrade` (created 2024-01-15 10:30)

Proceed with snapshot deletion? This action cannot be undone. (yes/no)

User: "yes"

Agent: [Step 5: Deletes snapshot]

🗑️ Deleting snapshot...
✓ Snapshot `database-01-daily-backup` deleted

       [Step 6: Reports results]

## ✓ Snapshot Deleted Successfully

Snapshot: `database-01-daily-backup`

Deletion Summary:
- ✓ Snapshot permanently deleted
- ✓ Storage freed
- ✓ Recovery point removed

Remaining Snapshots for VM `database-01`:
- `database-01-pre-upgrade` (created 2024-01-15 10:30)

This snapshot is still available for recovery.
```

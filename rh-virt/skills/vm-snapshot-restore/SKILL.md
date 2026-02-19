---
name: vm-snapshot-restore
description: |
  Restore virtual machines from snapshots with strict safety confirmations to prevent data loss.

  Use when:
  - "Restore VM [name] from snapshot [snapshot-name]"
  - "Roll back VM [name] to snapshot"
  - "Recover VM [name] from backup"

  CRITICAL: Requires VM to be stopped and typed snapshot name confirmation before restore.

  NOT for creating snapshots (use vm-snapshot-create instead).

model: inherit
color: red
---

# /vm-snapshot-restore Skill

Restore virtual machines from snapshots in OpenShift Virtualization. **CRITICAL**: This operation replaces current VM state with snapshot data. ALL changes since the snapshot will be LOST.

**Implementation Note**: This skill uses generic Kubernetes resource tools (`resources_create_or_update`) to create VirtualMachineRestore resources. Dedicated restore tools do not currently exist in the openshift-virtualization MCP server.

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_create_or_update` (from openshift-virtualization) - Create VirtualMachineRestore
- `resources_get` (from openshift-virtualization) - Verify VM/snapshot exists, monitor restore
- `vm_lifecycle` (from openshift-virtualization) - Stop VM if running

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to create VirtualMachineRestore resources

## When to Use This Skill

**Trigger this skill when:**
- User wants to restore a VM to a previous state
- User wants to recover from failed changes/upgrades
- User explicitly requests snapshot restore

**User phrases that trigger this skill:**
- "Restore VM api-server from snapshot snapshot-20240115"
- "Roll back database-01 to pre-upgrade snapshot"
- "Recover VM web-server from backup"

**Do NOT use this skill when:**
- User wants to create snapshots → Use `vm-snapshot-create` skill
- User wants to list snapshots → Use `vm-snapshot-list` skill
- User wants to clone a VM → Use `vm-clone` skill

## Workflow

### Step 1: Gather Restore Information

**Required Information from User:**
1. **VM Name** - VM to restore
2. **Namespace** - Namespace where VM exists
3. **Snapshot Name** - Snapshot to restore from

If any information missing, ask for it.

### Step 2: Verify VM Exists

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

**Error Handling**:
- If VM not found → Report error
- If permission denied → Report RBAC error

### Step 3: Check VM Running State

**From the VM resource in Step 2**, check `status.printableStatus`.

**If VM is Running:**
```markdown
⚠️ VM Must Be Stopped Before Restore

**VM**: `<vm-name>` (namespace: `<namespace>`)
**Status**: Running

**Safety Requirement**: VMs must be stopped before restore to prevent data corruption.

**Options:**
1. "stop-and-restore" - Stop the VM first, then restore from snapshot
2. "cancel" - Cancel restore operation

How would you like to proceed?
```

**Wait for user response.**

- If "stop-and-restore" → Stop VM using vm_lifecycle, then continue
- If "cancel" → Stop workflow

### Step 4: Verify Snapshot Exists

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

**If snapshot not found:**
```markdown
❌ Snapshot Not Found

**Snapshot**: `<snapshot-name>` does not exist in namespace `<namespace>`.

**To list available snapshots:**
"List snapshots for VM <vm-name>"

Restore operation cancelled.
```

**STOP workflow**.

**Extract snapshot details:**
- `metadata.creationTimestamp` - Creation time
- `status.phase` - Must be "Succeeded"
- `status.readyToUse` - Must be `true`
- `spec.source.name` - Verify it matches the VM name

**If snapshot status is not Ready:**
```markdown
❌ Snapshot Not Ready

**Snapshot**: `<snapshot-name>`
**Status**: <status.phase>
**Ready to Use**: <status.readyToUse>

Snapshot is not ready for restore. Only snapshots with "Succeeded" phase and readyToUse=true can be used.

Restore operation cancelled.
```

**STOP workflow**.

### Step 5: Present Restore Preview and Get Typed Confirmation

**CRITICAL: User must type the snapshot name to confirm.**

```markdown
## 🔴 VM RESTORE - Data Loss Warning

**⚠️ THIS WILL REPLACE CURRENT VM STATE WITH SNAPSHOT DATA ⚠️**

### What Will Happen

**VM to Restore**: `<vm-name>` (namespace: `<namespace>`)
**Snapshot to Restore From**: `<snapshot-name>`

**Current VM State** (WILL BE LOST):
- **Last Modified**: <current-timestamp>
- **Changes Since Snapshot**: ALL changes made after <snapshot-creation-timestamp> WILL BE PERMANENTLY LOST

**Snapshot State** (WILL BE RESTORED):
- **Created**: <snapshot-creation-timestamp>
- **Age**: <snapshot-age>

**Time Range of Data Loss**:
- **⚠️ ALL CHANGES in the last <time-diff> WILL BE LOST ⚠️**

### What Will Be Restored
- ✓ VM configuration (from snapshot time)
- ✓ Disk data (from snapshot time)

### What Will Be Lost
- ✗ **ALL disk changes** made after <snapshot-creation-timestamp>
- ✗ **ALL configuration changes** made after <snapshot-creation-timestamp>

---

**⚠️ CRITICAL: This restore is permanent. Current VM state cannot be recovered unless you create a snapshot now.**

**To proceed with restore, type the snapshot name exactly as shown:**

Type `<snapshot-name>` to confirm: _____
```

**Wait for user to type the snapshot name.**

**Validation:**
- Compare user input with snapshot name (case-sensitive, exact match)
- **If match**: Proceed to Step 6
- **If mismatch**: Cancel operation

**On mismatch:**
```markdown
❌ Confirmation Failed

**You typed**: `<user-input>`
**Expected**: `<snapshot-name>`

Names do not match. Restore cancelled for safety.

Operation cancelled. Current VM state preserved.
```

**STOP workflow**.

### Step 6: Final Confirmation Before Restore

**After typed verification succeeds**, ask for final explicit confirmation.

```markdown
## ✓ Typed Verification Passed

**Confirmation received for snapshot**: `<snapshot-name>`

### Ready to Restore

**VM**: `<vm-name>` (namespace: `<namespace>`)
**From Snapshot**: `<snapshot-name>`

**Impact**:
- Current VM state will be replaced with snapshot state
- All changes in the last <time-diff> will be permanently lost

---

**Proceed with VM restore? This action cannot be undone.**
- Type "yes" to execute restore
- Type "cancel" to abort

Your choice: _____
```

**Wait for user response.**

**Handle response:**
- If "yes" → Proceed to Step 7 (execute restore)
- If "cancel", "no", "wait", or anything else → Cancel operation

**On cancellation:**
```markdown
Restore operation cancelled by user. Current VM state preserved.
```

**STOP workflow**.

### Step 7: Execute Restore

**ONLY PROCEED AFTER**:
- ✓ VM verified (exists, stopped)
- ✓ Snapshot verified (exists, ready)
- ✓ User typed snapshot name correctly
- ✓ User confirmed "yes"

**MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

**Construct VirtualMachineRestore YAML:**

```yaml
apiVersion: snapshot.kubevirt.io/v1beta1
kind: VirtualMachineRestore
metadata:
  name: <restore-name>
  namespace: <namespace>
spec:
  target:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: <vm-name>
  virtualMachineSnapshotName: <snapshot-name>
```

**Generate restore name**:
- Format: `restore-<vm-name>-<timestamp>`
- Example: `restore-database-01-20260218-143500`

**Parameters**:
```json
{
  "resource": "apiVersion: snapshot.kubevirt.io/v1beta1\nkind: VirtualMachineRestore\nmetadata:\n  name: <restore-name>\n  namespace: <namespace>\nspec:\n  target:\n    apiGroup: kubevirt.io\n    kind: VirtualMachine\n    name: <vm-name>\n  virtualMachineSnapshotName: <snapshot-name>"
}
```

**Report progress:**
```markdown
🔄 Restoring VM from snapshot...
⏳ This may take several minutes...
```

### Step 8: Monitor Restore Progress

**Use `resources_get` to monitor VirtualMachineRestore status.**

Check `status.complete`:
- `true` → Restore completed
- `false` → Restore in progress

**Wait up to 10 minutes for restore to complete.**

### Step 9: Report Restore Results

**On success:**

```markdown
## ✓ VM Restored Successfully

**VM**: `<vm-name>` (namespace: `<namespace>`)
**Restored From**: Snapshot `<snapshot-name>`

### Restore Details
- **Snapshot Created**: <snapshot-creation-timestamp>
- **Restore Completed**: <current-timestamp>
- **VM Status**: Stopped (ready to start)

### Data Loss Confirmation
- ⚠️ All changes made after <snapshot-creation-timestamp> have been lost

### Next Steps

**To start the restored VM:**
"Start VM <vm-name> in namespace <namespace>"
```

**On failure:**

```markdown
## ❌ VM Restore Failed

**Error**: <error-message>

**VM**: `<vm-name>`
**Snapshot**: `<snapshot-name>`

**Current VM State**: UNKNOWN - may be partially restored or unchanged

**CRITICAL**: Do not start VM until restore issue is resolved

**Recovery Options:**
1. Try restore again after resolving the error
2. Restore from a different snapshot
3. Contact cluster admin for investigation
```

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with kubevirt toolset

### Required MCP Tools
- `resources_create_or_update` (from openshift-virtualization) - Create VirtualMachineRestore
- `resources_get` (from openshift-virtualization) - Verify and monitor
- `vm_lifecycle` (from openshift-virtualization) - Stop VM if running

### Related Skills
- `vm-snapshot-list` - List snapshots before restore
- `vm-snapshot-create` - Create snapshots before risky operations
- `vm-snapshot-delete` - Delete old snapshots
- `vm-lifecycle-manager` - Start VM after restore

### Reference Documentation

**Official Red Hat Documentation:**
- [OpenShift Virtualization Snapshots - OpenShift 4.20](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt-managing-vm-snapshots)

**Upstream Documentation:**
- [KubeVirt VM Snapshots](https://kubevirt.io/user-guide/operations/snapshot_restore_api/)

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill performs DESTRUCTIVE operations. You MUST:

1. **Before Restoring Snapshots** (CRITICAL - Data Loss Risk)
   - **REQUIRE VM to be stopped first** if currently running
   - Display what will be lost (current VM state since snapshot)
   - Show snapshot details (creation time, age)
   - **Require typed confirmation** - user must type snapshot name exactly
   - Ask: "Proceed with restore? This will replace current VM state. (yes/cancel)"
   - Wait for explicit "yes"

2. **Never Auto-Execute**
   - **NEVER restore without user confirmation**
   - **NEVER restore to running VMs** without stopping first
   - **NEVER skip typed verification for restore operations**

**Why This Matters:**
- **Data Loss on Restore**: Restoring replaces current VM state - all changes since snapshot are PERMANENTLY LOST
- **No Undo**: Restore cannot be reversed - current data cannot be recovered
- **Typed Confirmation**: Prevents accidental restores to wrong snapshots

## Common Issues

### Issue 1: Restore Fails - Insufficient Storage Capacity

**Error**: "Failed to restore: insufficient storage capacity" or "PVC provisioning failed"

**Cause**: The namespace doesn't have enough storage quota or the storage backend is full.

**Solution:**
1. **Check namespace storage quota**: Use `resources_list` with apiVersion="v1", kind="ResourceQuota" to check available storage
2. **Check PVC status**: Use `resources_list` to check PersistentVolumeClaims in the namespace
3. **Delete unnecessary snapshots**: Use vm-snapshot-delete skill to free up storage
4. **Request quota increase**: Contact cluster admin to increase namespace storage quota
5. **Try restore again**: Once storage is available, retry the restore operation

### Issue 2: Restore Stuck in Progress

**Error**: VirtualMachineRestore status shows `complete: false` for extended period

**Cause**: The storage backend is slow, the snapshot is corrupted, or there's a CSI driver issue.

**Solution:**
1. **Check VirtualMachineRestore status**: Use `resources_get` to check `status.conditions` for detailed error messages
2. **Check snapshot health**: Use vm-snapshot-list skill to verify snapshot is in "Succeeded" state
3. **Check storage backend logs**: Review CSI driver logs for errors (requires cluster admin access)
4. **Wait longer**: Large VMs may take 10+ minutes to restore
5. **Cancel and retry**: Delete the VirtualMachineRestore resource and try again
6. **Alternative snapshot**: If restore continues to fail, try restoring from a different snapshot

**Related**: If the issue persists, there may be a storage backend problem requiring cluster administrator investigation.

### Issue 3: User Typed Wrong Snapshot Name

**Error**: "Confirmation Failed - Names do not match"

**Cause**: User made a typo when typing the snapshot name for confirmation.

**Solution:**
1. **Retry with exact name**: Copy-paste the snapshot name from the previous message
2. **Check capitalization**: Snapshot names are case-sensitive
3. **Check for spaces**: Ensure no leading/trailing spaces in the typed name
4. **Use autocomplete**: If available in your terminal, use tab completion
5. **List snapshots**: Use vm-snapshot-list skill to see all available snapshots and verify the correct name

**This safety mechanism is intentional** - it prevents accidental data loss from restoring to the wrong snapshot.

## Security Considerations

- **Data Protection**: Restore requires TWO confirmations (typed + yes) to prevent accidental data loss
- **VM Stop Requirement**: VMs must be stopped before restore
- **Typed Verification**: User must type exact snapshot name
- **RBAC Enforcement**: Requires permissions for VirtualMachineRestore resources
- **Namespace Isolation**: Restore scoped to namespace boundaries
- **Audit Trail**: All restore operations logged in Kubernetes API audit logs
- **No Rollback**: Restore is permanent - current state cannot be recovered after restore

## Example Usage

### Example 1: Restore Failed Upgrade

```
User: "The database upgrade failed. Restore database-01 from snapshot pre-upgrade-snapshot"

Agent: "Which namespace is database-01 in?"

User: "production"

Agent: [Invokes vm-snapshot-restore skill]
       [Step 2: Verifies VM exists]
       [Step 3: Checks VM status - Running]

⚠️ VM Must Be Stopped Before Restore

**VM**: `database-01` (namespace: `production`)
**Status**: Running

**Safety Requirement**: VMs must be stopped before restore to prevent data corruption.

**Options:**
1. "stop-and-restore" - Stop the VM first, then restore from snapshot
2. "cancel" - Cancel restore operation

How would you like to proceed?

User: "stop-and-restore"

Agent: [Stops VM using vm_lifecycle]

⏸️ Stopping VM before restore...

VM `database-01` is being stopped gracefully.

       [Waits 10 seconds, verifies stopped]
       [Step 4: Verifies snapshot exists and is ready]
       [Step 5: Presents restore preview]

## 🔴 VM RESTORE - Data Loss Warning

**⚠️ THIS WILL REPLACE CURRENT VM STATE WITH SNAPSHOT DATA ⚠️**

**VM to Restore**: `database-01` (namespace: `production`)
**Snapshot to Restore From**: `pre-upgrade-snapshot`

**Current VM State** (WILL BE LOST):
- **Last Modified**: 2026-02-18 16:30:00 UTC
- **Changes Since Snapshot**: ALL changes made after 2026-02-18 10:00:00 WILL BE PERMANENTLY LOST

**Snapshot State** (WILL BE RESTORED):
- **Created**: 2026-02-18 10:00:00 UTC
- **Age**: 6 hours 30 minutes

**Time Range of Data Loss**:
- **⚠️ ALL CHANGES in the last 6 hours 30 minutes WILL BE LOST ⚠️**

**To proceed with restore, type the snapshot name exactly as shown:**

Type `pre-upgrade-snapshot` to confirm: _____

User: "pre-upgrade-snapshot"

Agent: [Step 6: Typed verification passed]
       [Step 7: Final confirmation]

## ✓ Typed Verification Passed

**Confirmation received for snapshot**: `pre-upgrade-snapshot`

**VM**: `database-01`
**From Snapshot**: `pre-upgrade-snapshot`

**Impact**:
- Current VM state will be replaced with snapshot state
- All changes in the last 6 hours 30 minutes will be permanently lost

**Proceed with VM restore? This action cannot be undone.**
- Type "yes" to execute restore
- Type "cancel" to abort

Your choice: _____

User: "yes"

Agent: [Step 8: Executes restore]

🔄 Restoring VM from snapshot...
⏳ This may take several minutes...

       [Step 9: Monitors progress]

⏳ Restore in progress...

       [Step 10: Reports results]

## ✓ VM Restored Successfully

**VM**: `database-01` (namespace: `production`)
**Restored From**: Snapshot `pre-upgrade-snapshot`

### Restore Details
- **Snapshot Created**: 2026-02-18 10:00:00 UTC
- **Restore Completed**: 2026-02-18 16:35:22 UTC
- **VM Status**: Stopped (ready to start)

### Data Loss Confirmation
- ⚠️ All changes made after 2026-02-18 10:00:00 UTC have been lost

### Next Steps

**To start the restored VM:**
"Start VM database-01 in namespace production"

The database has been restored to its pre-upgrade state. The failed upgrade has been rolled back.
```

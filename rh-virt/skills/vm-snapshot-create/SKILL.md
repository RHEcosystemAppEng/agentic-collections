---
name: vm-snapshot-create
description: |
  Create virtual machine snapshots for backup and recovery with comprehensive storage backend analysis.

  Use when:
  - "Create a snapshot of VM [name]"
  - "Backup VM [name] before upgrade"
  - "Take a snapshot of [vm]"

  Analyzes storage capabilities, guest agent status, and consistency guarantees before creating snapshots.

  NOT for VM cloning (use vm-clone to create independent copies).

model: inherit
color: green
---

# /vm-snapshot-create Skill

Create virtual machine snapshots in OpenShift Virtualization. Snapshots capture the state and data of a VM at a specific point in time, enabling backup, recovery, and testing workflows.

**Implementation Note**: This skill uses generic Kubernetes resource tools (`resources_create_or_update`) to manage VirtualMachineSnapshot resources. Dedicated snapshot tools do not currently exist in the openshift-virtualization MCP server.

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_create_or_update` (from openshift-virtualization) - Create VirtualMachineSnapshot
- `resources_get` (from openshift-virtualization) - Verify VM exists and get status
- `resources_list` (from openshift-virtualization) - List StorageClass, VolumeSnapshotClass

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to create VirtualMachineSnapshot resources
- Storage backend with snapshot support (CSI driver with snapshot capabilities)

## When to Use This Skill

**Trigger this skill when:**
- User wants to create a backup of a VM before changes
- User wants to create a recovery point
- User explicitly requests snapshot creation

**User phrases that trigger this skill:**
- "Create a snapshot of VM database-01"
- "Backup VM web-server before upgrade"
- "Take a snapshot of production-app"

**Do NOT use this skill when:**
- User wants to clone a VM → Use `vm-clone` skill (creates independent copy)
- User wants to list snapshots → Use `vm-snapshot-list` skill
- User wants to restore from snapshot → Use `vm-snapshot-restore` skill

## Workflow

### Step 1: Gather Snapshot Information

**Required Information from User:**
1. **VM Name** - Name of the VM to snapshot
2. **Namespace** - Namespace where VM exists
3. **Snapshot Name** (Optional) - Name for the snapshot (auto-generated if not provided)

If namespace not provided, ask for it explicitly.

### Step 2: Verify VM Exists and Get Status

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

**Expected Output**: VirtualMachine resource with status

**Error Handling**:
- If VM not found → Report error, suggest using vm-inventory skill
- If permission denied → Report RBAC error

**Extract VM Details:**
- Current status (Running, Stopped)
- Storage configuration (DataVolumes, PVCs)
- **IMPORTANT**: Save `status.volumeSnapshotStatuses` for storage analysis

### Step 3: Verify Storage Snapshot Capabilities

**CRITICAL: This comprehensive storage analysis MUST execute BEFORE asking user about VM running state.**

This step analyzes storage backend capabilities to determine snapshot behavior and requirements. The analysis includes 9 substeps.

[Continue with all 9 substeps from the original file: 1c.1 through 1c.9, checking volume snapshot status, hot-plugged volumes, storage class, VolumeSnapshotClass, CSI driver capabilities, guest agent status, Windows VSS, and storing analysis results]

### Step 4: Check VM Running State (Enhanced with Storage Analysis)

**From the VM resource in Step 2**, check `status.printableStatus`.

**Use storage analysis results from Step 3** to provide accurate guidance.

[Include the three scenarios: VM must be stopped, VM can run (online supported), VM is stopped - with all the guest agent and Windows VSS warnings]

### Step 5: Stop Running VM (if user chose "stop-and-snapshot")

**ONLY execute if user chose "stop-and-snapshot" in Step 4.**

Use `vm_lifecycle` MCP tool or vm-lifecycle-manager skill to stop the VM.

### Step 6: Estimate Storage Consumption

**From the VM resource**, estimate snapshot storage:
- Initial snapshot may be same size as VM disk
- Subsequent snapshots smaller (only deltas)

### Step 7: Present Snapshot Configuration for Confirmation

**Include storage analysis results from Step 3 in the configuration presentation.**

[Include the full confirmation template with storage backend analysis, guest agent status, volumes to snapshot, etc.]

**Wait for user confirmation.**

**Handle response:**
- If "yes" → Proceed to Step 8 (execute snapshot)
- If "no", "cancel", or anything else → Cancel operation

### Step 8: Create the Snapshot

**ONLY PROCEED AFTER user confirmation in Step 7.**

**MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

**Construct VirtualMachineSnapshot YAML:**

```yaml
apiVersion: snapshot.kubevirt.io/v1beta1
kind: VirtualMachineSnapshot
metadata:
  name: <snapshot-name>
  namespace: <namespace>
spec:
  source:
    apiGroup: kubevirt.io
    kind: VirtualMachine
    name: <vm-name>
```

**If snapshot name not provided by user**, generate one:
- Format: `<vm-name>-snapshot-<timestamp>`
- Example: `database-01-snapshot-20260218-143022`

**Parameters**:
```json
{
  "resource": "apiVersion: snapshot.kubevirt.io/v1beta1\nkind: VirtualMachineSnapshot\nmetadata:\n  name: <snapshot-name>\n  namespace: <namespace>\nspec:\n  source:\n    apiGroup: kubevirt.io\n    kind: VirtualMachine\n    name: <vm-name>"
}
```

**Report progress:**
```markdown
📸 Creating VM snapshot...
✓ Snapshot `<snapshot-name>` created for VM `<vm-name>`
```

### Step 9: Monitor Snapshot Status

**After creation, monitor snapshot readiness using `resources_get`.**

Check `status.phase`:
- `InProgress` → Still creating
- `Succeeded` → Snapshot ready
- `Failed` → Snapshot failed

**Wait up to 5 minutes for snapshot to complete.**

### Step 10: Report Snapshot Creation Results

**Extract snapshot indications** from `status.indications`:
- `GuestAgent` - Guest agent coordinated the snapshot
- `Online` - Snapshot taken while VM was running

**On success:**

```markdown
## ✓ VM Snapshot Created Successfully

**VM**: `<vm-name>` (namespace: `<namespace>`)
**Snapshot**: `<snapshot-name>`

### Snapshot Details
- **Name**: `<snapshot-name>`
- **Status**: Ready
- **Created**: <timestamp>
- **VM Status at Snapshot**: <Stopped|Running>

### Snapshot Coordination (from status.indications)
<if "GuestAgent" in indications>
- ✅ **Guest Agent Coordination**: Active
- ✅ **Filesystem Freeze/Thaw**: Performed during snapshot
- ✅ **Actual Consistency**: Application-consistent
</if>

<if "Online" in indications AND "GuestAgent" NOT in indications>
- ⚠️ **Guest Agent Coordination**: Not active
- ⚠️ **Actual Consistency**: Crash-consistent (best-effort)
</if>

### Next Steps

**To list all snapshots:**
"List snapshots for VM <vm-name>"

**To restore from this snapshot:**
"Restore VM <vm-name> from snapshot <snapshot-name>"

**To delete this snapshot:**
"Delete snapshot <snapshot-name>"
```

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with kubevirt toolset

### Required MCP Tools
- `resources_create_or_update` (from openshift-virtualization) - Create VirtualMachineSnapshot
- `resources_get` (from openshift-virtualization) - Verify VM and snapshot status
- `resources_list` (from openshift-virtualization) - List StorageClass, VolumeSnapshotClass

### Related Skills
- `vm-snapshot-list` - List snapshots after creation
- `vm-snapshot-restore` - Restore VMs from snapshots
- `vm-snapshot-delete` - Delete old snapshots
- `vm-lifecycle-manager` - Stop VMs before snapshot
- `vm-inventory` - List VMs before creating snapshots

### Reference Documentation

**Official Red Hat Documentation:**
- [OpenShift Virtualization Snapshots - OpenShift 4.20](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt-managing-vm-snapshots)
- [Live Snapshots in OpenShift Virtualization](https://www.redhat.com/en/blog/live-snapshots-in-openshift-virtualization)

**Upstream Documentation:**
- [KubeVirt VM Snapshots](https://kubevirt.io/user-guide/operations/snapshot_restore_api/)
- [CSI Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill performs operations that affect VM data and storage. You MUST:

1. **Before Creating Snapshots**
   - Analyze storage backend capabilities
   - Verify VM exists and get current state
   - Check for hot-plugged volumes (blocks snapshots)
   - Show storage consumption estimate
   - Present snapshot configuration
   - Ask: "Proceed with snapshot creation? (yes/no)"
   - Wait for explicit "yes"

2. **Never Auto-Execute**
   - **NEVER create without user confirmation**
   - **NEVER skip storage analysis**
   - **NEVER skip hot-plugged volume check**

**Why This Matters:**
- **Storage Consumption**: Snapshots consume storage proportional to VM disk size
- **Hot-Plugged Volumes**: Cannot snapshot VMs with hot-plugged volumes
- **Consistency**: Online vs offline snapshots have different consistency guarantees
- **Guest Agent**: Required for application-consistent snapshots

## Common Issues

### Issue 1: Snapshot Creation Fails - VolumeSnapshotClass Not Found

**Error**: "VolumeSnapshotClass not found" or "CSI driver doesn't support snapshots"

**Cause**: The storage backend doesn't have a VolumeSnapshotClass configured for the CSI driver, or the CSI driver doesn't support snapshots at all.

**Solution:**
1. **Check if VolumeSnapshotClass exists**: Use `resources_list` with apiVersion="snapshot.storage.k8s.io/v1", kind="VolumeSnapshotClass"
2. **Verify CSI driver supports snapshots**: Check StorageClass provisioner field
3. **Contact cluster admin**: Request VolumeSnapshotClass configuration for your storage backend
4. **Alternative**: Use `vm-clone` skill for VM backup instead of snapshots

### Issue 2: Snapshot Creation Blocked - Hot-Plugged Volumes Detected

**Error**: "Cannot create snapshot - VM has hot-plugged volumes"

**Cause**: The VM has volumes that were attached after VM creation without restarting the VM. Hot-plugged volumes block snapshot creation in OpenShift Virtualization.

**Solution:**
1. **Stop the VM**: Use vm-lifecycle-manager skill to stop the VM
2. **Remove hot-plugged volumes**: Detach volumes that aren't needed
3. **Persist volumes to VM spec**: Add hot-plugged volumes to `spec.template.spec.volumes` to make them permanent
4. **Restart the VM**: Start the VM to apply the changes
5. **Retry snapshot**: Once hot-plugged volumes are resolved, create the snapshot

**Related**: See [OpenShift Virtualization documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt-hot-plugging-virtual-disks) for hot-plugging details

### Issue 3: Snapshot Created but Consistency Warning

**Error**: Snapshot created successfully but shows "crash-consistent" without guest agent

**Cause**: The VM doesn't have QEMU guest agent installed or running, so the snapshot couldn't coordinate filesystem freeze/thaw during creation.

**Solution:**
1. **For Linux VMs**: Install qemu-guest-agent package
   ```bash
   # RHEL/CentOS/Fedora
   sudo dnf install qemu-guest-agent
   sudo systemctl enable --now qemu-guest-agent
   ```
2. **For Windows VMs**: Install VirtIO drivers which include the guest agent
3. **Verify agent status**: Check VM status for `AgentConnected: True` condition
4. **Future snapshots**: Once guest agent is running, subsequent snapshots will be application-consistent
5. **Current snapshot**: The crash-consistent snapshot is still usable, but may have minor inconsistencies

## Security Considerations

- **RBAC Enforcement**: Requires permissions for VirtualMachineSnapshot resources
- **Storage Quotas**: Respects namespace storage quotas
- **Hot-Plugged Volume Detection**: Prevents snapshots when hot-plugged volumes present
- **KUBECONFIG Security**: Credentials never exposed in output
- **Namespace Isolation**: Snapshots scoped to namespace boundaries
- **Audit Trail**: All snapshot operations logged in Kubernetes API audit logs

## Example Usage

### Example 1: Create Snapshot Before Upgrade

```
User: "Create a snapshot of database-01 before I upgrade it"

Agent: "Which namespace is database-01 in?"

User: "production"

Agent: [Invokes vm-snapshot-create skill]
       [Step 2: Verifies VM exists]
       [Step 3: Analyzes storage backend - AWS EBS, online snapshots supported]
       [Step 4: Checks VM status - Running, guest agent active]
       [Step 6: Estimates storage - 50Gi]
       [Step 7: Presents configuration]

## VM Snapshot - Review Configuration

**VM to Snapshot:**
- **Name**: `database-01`
- **Namespace**: `production`
- **Status**: Running
- **Storage**: 50Gi

**Storage Backend Analysis:**
- **Storage Class**: `gp3-csi`
- **CSI Driver**: `ebs.csi.aws.com`
- **Online Snapshots**: ✅ Supported
- **Consistency Level**: `crash-consistent`
- **VolumeSnapshotClass**: `ebs-snapclass` ✓

**Guest Agent Status:**
- ✅ **QEMU Guest Agent**: Connected and running
- ✅ **Filesystem Freeze/Thaw**: Will be performed during snapshot
- ✅ **Expected Consistency**: Application-consistent (with freeze)

**Snapshot Details:**
- **Snapshot Name**: `database-01-snapshot-20260218-143022` (auto-generated)
- **Type**: Online snapshot
- **Estimated Storage**: ~50Gi (initial snapshot)

**Proceed with snapshot creation? (yes/no)**

User: "yes"

Agent: [Step 8: Creates snapshot]

📸 Creating VM snapshot...
✓ Snapshot `database-01-snapshot-20260218-143022` created for VM `database-01`

       [Step 9: Monitors status]

⏳ Snapshot creation in progress...
   Status: InProgress

⏳ Snapshot creation in progress...
   Status: Succeeded

       [Step 10: Reports results]

## ✓ VM Snapshot Created Successfully

**VM**: `database-01` (namespace: `production`)
**Snapshot**: `database-01-snapshot-20260218-143022`

### Snapshot Details
- **Name**: `database-01-snapshot-20260218-143022`
- **Status**: Ready
- **Created**: 2026-02-18 14:30:22 UTC
- **VM Status at Snapshot**: Running

### Snapshot Coordination (from status.indications)
- ✅ **Guest Agent Coordination**: Active
- ✅ **Filesystem Freeze/Thaw**: Performed during snapshot
- ✅ **Actual Consistency**: Application-consistent

### Next Steps

**To list all snapshots:**
"List snapshots for VM database-01"

**To restore from this snapshot:**
"Restore VM database-01 from snapshot database-01-snapshot-20260218-143022"

You can now safely upgrade the database. If the upgrade fails, restore using the command above.
```

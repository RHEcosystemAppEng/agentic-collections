---
name: vm-clone
description: |
  Clone existing virtual machines for testing, scaling, or creating templates. Use this skill when users request:
  - "Clone VM [source] to [target]"
  - "Create a copy of VM [name]"
  - "Duplicate VM [name] for testing"
  - "Create 3 copies of template-vm"

  This skill clones VM configuration and optionally creates new storage or references existing storage.

  NOT for snapshots (use vm-snapshot for point-in-time backups).

model: inherit
color: blue
---

# /vm-clone Skill

Clone existing virtual machines in OpenShift Virtualization, creating new VMs with copied configuration and optional storage cloning. This skill is ideal for creating test environments, scaling workloads, or duplicating VM templates.

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_get` (from openshift-virtualization) - Get source VM configuration
- `resources_create_or_update` (from openshift-virtualization) - Create cloned VM
- `resources_list` (from openshift-virtualization) - List DataVolumes, PVCs, VMs

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to create VirtualMachine and PVC resources
- Source VM must exist

### Prerequisite Verification

**Before executing, verify MCP server availability:**

1. **Check MCP Server Configuration**
   - Verify `openshift-virtualization` exists in `.mcp.json`
   - If missing → Report to user with setup instructions

2. **Check Environment Variables**
   - Verify `KUBECONFIG` is set (check presence only, never expose value)
   - If missing → Report to user

3. **Check RBAC Permissions** (optional verification)
   - Verify ServiceAccount can create VirtualMachine resources
   - Verify ServiceAccount can create PVC/DataVolume resources

**Human Notification Protocol:**

When prerequisites fail:

```
❌ Cannot execute vm-clone: MCP server 'openshift-virtualization' is not available

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
- User explicitly invokes `/vm-clone` command
- User wants to duplicate an existing VM
- User needs to create test/dev copies of production VMs
- User wants to scale horizontally by creating VM copies
- User wants to create VMs from a template VM

**User phrases that trigger this skill:**
- "Clone VM web-server to web-server-test"
- "Create a copy of database-vm"
- "Duplicate production-vm for staging"
- "Make 3 copies of template-vm"
- "/vm-clone" (explicit command)

**Do NOT use this skill when:**
- User wants to create a new VM from scratch → Use `/vm-create` skill instead
- User wants a point-in-time backup → Use snapshots instead
- User wants to move/migrate a VM → Use migration tools instead
- User wants to resize a VM → Modify existing VM instead

## Workflow

### Step 1: Gather Source VM Information

**Required Information from User:**
1. **Source VM Name** - Name of the VM to clone
2. **Source Namespace** - Namespace where source VM exists
3. **Target VM Name** - Name for the cloned VM
4. **Target Namespace** - Namespace for the cloned VM (can be same or different)

If user doesn't provide all information, ask for missing details.

**1.1: Verify Source VM Exists**

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<source-namespace>",
  "name": "<source-vm-name>"
}
```

**Expected Output**: Complete VirtualMachine resource specification

**Error Handling**:
- If VM not found → Report error, suggest using vm-inventory to find VMs
- If permission denied → Report RBAC error

**1.2: Check Target VM Name Availability**

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<target-namespace>",
  "name": "<target-vm-name>"
}
```

**If VM already exists:**
```markdown
❌ Target VM Name Already Exists

**VM**: `<target-vm-name>` already exists in namespace `<target-namespace>`

**Options:**
1. Choose a different name for the clone
2. Delete the existing VM first (use vm-delete skill)
3. Cancel cloning operation

What would you like to do?
```

**Wait for user decision.**

**1.3: Discover Source VM Storage**

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters for DataVolumes**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<source-namespace>",
  "labelSelector": "vm.kubevirt.io/name=<source-vm-name>"
}
```

**Parameters for PVCs** (if DataVolumes not found):
```json
{
  "apiVersion": "v1",
  "kind": "PersistentVolumeClaim",
  "namespace": "<source-namespace>"
}
```

**Parse results:**
- Extract storage resource names referenced by source VM
- Calculate total storage size
- Determine if storage uses DataSources or container disks

### Step 2: Ask User for Cloning Strategy

**Present storage cloning options to user:**

```markdown
## VM Cloning - Storage Strategy

**Source VM**: `<source-vm-name>` (namespace: `<source-namespace>`)

### Storage Configuration

**Source VM Storage:**
- DataVolume/PVC: `<source-disk>` (50Gi)
- Total Storage: 50Gi

---

### Cloning Options

**How should storage be cloned?**

**Option 1: Clone Storage** (full copy)
- Creates new DataVolume/PVC for target VM
- Clones all data from source storage
- Target VM has independent storage
- Storage required: 50Gi (new allocation)
- Time: ~5-10 minutes (depends on size)
- Use case: Independent test/dev environments

**Option 2: Reference Existing Storage** (shared storage - not recommended)
- Target VM references same PVC as source
- No storage cloning
- ⚠️ Both VMs share the same disk (dangerous!)
- Storage required: 0Gi (no new allocation)
- Use case: Only if you know what you're doing

**Option 3: Create New Empty Storage** (fresh disk)
- Creates new empty DataVolume/PVC for target VM
- Does NOT clone data from source
- Target VM starts with clean disk
- Storage required: 50Gi (new allocation)
- Use case: Creating VMs from templates without data

**Option 4: Cancel**
- No cloning performed

---

**Select storage strategy** (1, 2, 3, or 4):
```

**Wait for user to select option 1, 2, 3, or 4.**

**Handle user response:**
- If "4" or "cancel" → Cancel operation, stop workflow
- If "1" → Proceed with storage cloning (clone_storage=true)
- If "2" → Proceed with shared storage (share_storage=true) + warn user
- If "3" → Proceed with new empty storage (new_storage=true)

**If user selects Option 2 (shared storage), issue warning:**
```markdown
⚠️ WARNING: Shared Storage is Dangerous

You selected to share storage between source and target VMs.

**Risks:**
- Both VMs writing to the same disk will cause **data corruption**
- Only safe if source VM is stopped and will remain stopped
- Not recommended for production use

**Recommendation**: Use Option 1 (Clone Storage) instead for independent VMs.

**Proceed with shared storage anyway? (yes/cancel)**
```

Wait for explicit "yes" to continue with shared storage.

### Step 3: Present Clone Configuration for Confirmation

**After determining cloning strategy, present complete configuration:**

```markdown
## VM Clone Configuration - Review

**Please review the clone configuration:**

### Source VM
- **Name**: `<source-vm-name>`
- **Namespace**: `<source-namespace>`
- **Instance Type**: <instance-type>
- **vCPU**: <cpu>, **Memory**: <memory>
- **Storage**: <storage-size>
- **Status**: <current-status>

### Target VM (Clone)
- **Name**: `<target-vm-name>`
- **Namespace**: `<target-namespace>`
- **Instance Type**: <instance-type> (copied from source)
- **vCPU**: <cpu>, **Memory**: <memory> (copied from source)
- **Storage**: <storage-strategy-description>
- **Initial Status**: Stopped (will not auto-start)

### Storage Strategy
<if clone_storage=true>
- **Strategy**: Clone Storage (full copy)
- **New Storage**: 50Gi DataVolume/PVC will be created
- **Clone Time**: ~5-10 minutes
- **Storage Class**: <storage-class> (from source)
</if>

<if share_storage=true>
- **Strategy**: Shared Storage ⚠️
- **WARNING**: Both VMs will share the same disk
- **Ensure source VM is stopped** to avoid data corruption
</if>

<if new_storage=true>
- **Strategy**: New Empty Storage
- **New Storage**: 50Gi empty DataVolume/PVC will be created
- **No data cloned** from source
</if>

### Resource Impact
- **CPU**: <cpu> vCPUs consumed
- **Memory**: <memory> RAM consumed
- **Storage**: <new-storage-size> (if applicable)

### What Will Be Copied
- ✓ Instance type and preference
- ✓ vCPU and memory configuration
- ✓ Network configuration
- ✓ Tolerations and affinity rules
- ✓ Cloud-init configuration (if any)
<if clone_storage=true>
- ✓ Disk data (full clone)
</if>

### What Will NOT Be Copied
- ✗ VM running state (clone starts stopped)
- ✗ IP addresses (new IPs assigned)
- ✗ Hostname (uses target VM name)
- ✗ MAC addresses (new MACs generated)

---

**Proceed with VM cloning? (yes/no)**
```

**Wait for user confirmation.**

**Handle response:**
- If "yes" → Proceed to Step 4 (execute cloning)
- If "no", "cancel", "wait", or anything else → Cancel operation

**On cancellation:**
```markdown
VM cloning cancelled by user. No resources were created.
```

**STOP workflow**.

### Step 4: Execute VM Cloning

**ONLY PROCEED AFTER**:
- ✓ Step 1: Source VM validated, target name available
- ✓ Step 2: User selected storage strategy
- ✓ Step 3: User confirmed clone configuration

**4.1: Prepare Cloned VM Specification**

**From the source VM resource obtained in Step 1.1**, create a modified spec:

1. **Change metadata**:
   - `metadata.name` → `<target-vm-name>`
   - `metadata.namespace` → `<target-namespace>`
   - Remove `metadata.uid`, `metadata.resourceVersion`, `metadata.creationTimestamp`
   - Remove status section entirely

2. **Update storage references**:
   - If `clone_storage=true`: Create new DataVolume with source as sourceRef
   - If `share_storage=true`: Keep existing PVC references (no changes)
   - If `new_storage=true`: Create new empty DataVolume

3. **Update runStrategy**:
   - Set to `Halted` (clone starts stopped)

4. **Generate new firmware UUIDs**:
   - Generate new `spec.template.spec.domain.firmware.uuid`
   - Generate new `spec.template.spec.domain.firmware.serial`

5. **Preserve from source**:
   - Instance type and preference
   - Tolerations
   - Network configuration
   - Cloud-init (if any)

**4.2: Create Storage Resources (if clone_storage=true or new_storage=true)**

**If cloning storage:**

**MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

**Create DataVolume that clones from source:**
```yaml
apiVersion: cdi.kubevirt.io/v1beta1
kind: DataVolume
metadata:
  name: <target-vm-name>-rootdisk
  namespace: <target-namespace>
spec:
  source:
    pvc:
      name: <source-pvc-name>
      namespace: <source-namespace>
  storage:
    resources:
      requests:
        storage: <size-from-source>
    storageClassName: <storage-class-from-source>
```

**If creating new empty storage:**

**MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

**Create empty DataVolume:**
```yaml
apiVersion: cdi.kubevirt.io/v1beta1
kind: DataVolume
metadata:
  name: <target-vm-name>-rootdisk
  namespace: <target-namespace>
spec:
  source:
    blank: {}
  storage:
    resources:
      requests:
        storage: <size-from-source>
    storageClassName: <storage-class-from-source>
```

**Report progress:**
```markdown
📦 Creating storage for cloned VM...
<if clone_storage=true>
⏳ Cloning storage (this may take 5-10 minutes)...
</if>
<if new_storage=true>
✓ Creating new empty storage...
</if>
```

**4.3: Create Cloned VirtualMachine**

**MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

**Parameters**: Use the prepared VM spec from Step 4.1

**Expected Output**: VirtualMachine created successfully

**Error Handling**:
- If creation fails → Report error, rollback storage if created
- If permission denied → Report RBAC error
- If namespace doesn't exist → Report namespace error

**Report progress:**
```markdown
🖥️ Creating cloned VirtualMachine...
✓ VirtualMachine `<target-vm-name>` created in namespace `<target-namespace>`
```

**4.4: Monitor Storage Cloning Progress (if clone_storage=true)**

**If storage is being cloned, monitor DataVolume status:**

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "cdi.kubevirt.io/v1beta1",
  "kind": "DataVolume",
  "namespace": "<target-namespace>",
  "name": "<target-vm-name>-rootdisk"
}
```

**Check `status.phase`:**
- `Pending` → Still cloning
- `Succeeded` → Clone complete
- `Failed` → Clone failed

**Report progress every 30 seconds:**
```markdown
⏳ Storage cloning in progress...
   Phase: <phase>
   Progress: <progress-percentage-if-available>
```

**Wait up to 15 minutes for cloning to complete.**

### Step 5: Report Cloning Results

**On successful clone:**

```markdown
## ✓ VM Cloned Successfully

**Source VM**: `<source-vm-name>` (namespace: `<source-namespace>`)
**Target VM**: `<target-vm-name>` (namespace: `<target-namespace>`)

### Cloned VM Details
- **Name**: `<target-vm-name>`
- **Namespace**: `<target-namespace>`
- **Instance Type**: <instance-type>
- **vCPU**: <cpu>, **Memory**: <memory>
- **Storage**: <storage-size>
- **Status**: Stopped (ready to start)

<if clone_storage=true>
### Storage Cloning
- ✓ Storage cloned successfully
- ✓ DataVolume: `<target-vm-name>-rootdisk` (50Gi)
- ✓ Clone completed in <time-elapsed>
- ✓ Target VM has independent storage
</if>

<if new_storage=true>
### Storage Creation
- ✓ New empty storage created
- ✓ DataVolume: `<target-vm-name>-rootdisk` (50Gi)
- ℹ️ Storage is empty (no data from source)
</if>

<if share_storage=true>
### Storage Configuration
- ⚠️ Shared storage configured
- ⚠️ Both VMs share PVC: `<source-pvc-name>`
- ⚠️ **Keep source VM stopped to avoid data corruption**
</if>

---

### Next Steps

**To start the cloned VM:**
```
"Start VM <target-vm-name> in namespace <target-namespace>"
```

**To view VM details:**
```
"Get details of VM <target-vm-name>"
```

**To access the VM console:**
- VNC Console: OpenShift Console → Virtualization → VirtualMachines → `<target-vm-name>` → Console
- Serial Console: `virtctl console <target-vm-name> -n <target-namespace>`

### Important Notes

<if clone_storage=true>
- ✓ The cloned VM has **independent storage** from the source
- ✓ Changes to the clone will **not affect** the source VM
- ✓ You can safely start and modify both VMs
</if>

<if share_storage=true>
- ⚠️ **CRITICAL**: Both VMs share the same disk
- ⚠️ **Never run both VMs simultaneously** - data corruption will occur
- ⚠️ Only start one VM at a time
- ℹ️ Recommended: Convert to cloned storage using vm-snapshot or manual PVC cloning
</if>

<if new_storage=true>
- ℹ️ The clone has **empty storage** (no data from source)
- ℹ️ OS installation or configuration may be required
- ℹ️ Useful for creating fresh VMs from a template configuration
</if>

### Configuration Differences
- **Hostname**: Will use `<target-vm-name>` (different from source)
- **IP Address**: New IP will be assigned (different from source)
- **MAC Address**: New MAC addresses generated (different from source)
- **Firmware UUID**: New UUID generated (different from source)

---

**To verify the clone:**
```
"List VMs in namespace <target-namespace>"
```

Both source and target VMs should appear in the inventory.
```

**On cloning failure:**

**OPTIONAL**: If cloning operation fails, consult documentation for common cloning failure scenarios.

**Document Consultation** (OPTIONAL - when cloning fails):
1. **Action**: Read [storage-errors.md](../../docs/troubleshooting/storage-errors.md) using the Read tool to understand VM cloning failure scenarios, storage provisioning issues, and DataVolume cloning errors
2. **Output to user**: "I consulted [storage-errors.md](../../docs/troubleshooting/storage-errors.md) to understand potential causes for the cloning failure."

**When to consult**:
- Storage cloning fails (DataVolume provisioning errors)
- VM creation fails during cloning workflow
- PVC clone not supported errors
- Storage class issues during cloning

**When NOT to consult**:
- Simple "VM already exists" errors (clear cause)
- RBAC permission errors (clear cause)
- Namespace not found errors (clear cause)

```markdown
## ❌ VM Cloning Failed

**Error**: <error-message>

**Source VM**: `<source-vm-name>` (namespace: `<source-namespace>`)
**Target VM**: `<target-vm-name>` (namespace: `<target-namespace>`)

**Common Causes:**
- **Insufficient storage quota** - Namespace lacks storage capacity for clone
- **Insufficient RBAC permissions** - ServiceAccount lacks create permissions
- **Storage class not available** - Target namespace cannot access storage class
- **PVC clone not supported** - Storage class doesn't support cloning
- **Source VM still running** - Some storage backends require source VM to be stopped

**Troubleshooting Steps:**

Consult [storage-errors.md](../../docs/troubleshooting/storage-errors.md) for MCP-first diagnostic procedures:

1. **Check storage quota:**

   See "ErrorDataVolumeNotReady - Insufficient Storage Quota" section
   - Use `resources_list` to check ResourceQuota in target namespace

2. **Check permissions:**

   Use `resources_list` with appropriate apiVersion/kind to verify RBAC permissions
   (Note: `oc auth can-i` has no direct MCP equivalent - use CLI if needed)

3. **Check storage class:**

   See "DataVolume Cloning Failures" section
   - Use `resources_get` to check StorageClass configuration
   - Use `resources_list` to list available storage classes

4. **Check if source VM is stopped:**

   Use vm-inventory skill: "Show status of VM <source-vm-name>"

5. **Check DataVolume status** (if storage cloning):

   See "DataVolume Cloning Failures" section
   - Use `resources_get` to check DataVolume status and phase

**Partial Resources Created:**
<if any resources were created>
Some resources may have been created before the failure:
- VirtualMachine: `<target-vm-name>` (may need cleanup)
- DataVolume: `<target-vm-name>-rootdisk` (may need cleanup)

To clean up partial resources:
```
"Delete VM <target-vm-name> in namespace <target-namespace>"
```
</if>

Would you like help troubleshooting this error?
```

## Advanced Features

### Batch Cloning (Multiple Copies)

**User request:** "Create 3 copies of template-vm named web-01, web-02, web-03"

**Workflow:**
1. Execute Step 1 (validate source VM once)
2. Generate target names: web-01, web-02, web-03
3. Check all target names for availability
4. Present combined cloning scope for all copies
5. Ask for storage strategy (applies to all clones)
6. Confirm batch operation
7. Execute cloning for each VM sequentially

**Batch confirmation:**
```markdown
## Batch VM Cloning - Review

**Source VM**: `template-vm`

**Target VMs**:
1. `web-01` (namespace: `production`)
2. `web-02` (namespace: `production`)
3. `web-03` (namespace: `production`)

**Storage Strategy**: Clone Storage (full copy for each)

**Total Resource Impact**:
- **VMs**: 3 new VMs
- **Storage**: 150Gi (3 × 50Gi)
- **vCPUs**: 12 total (3 × 4)
- **Memory**: 24Gi total (3 × 8Gi)

**Estimated Time**: ~20-30 minutes (clones created sequentially)

Proceed with batch cloning? (yes/no)
```

### Cross-Namespace Cloning

**User request:** "Clone production-vm from production namespace to staging namespace"

**Workflow:**
- Source namespace: `production`
- Target namespace: `staging`
- Storage cloning may require cross-namespace PVC access
- Present warning if namespaces have different quotas/policies

**Cross-namespace note:**
```markdown
ℹ️ **Cross-Namespace Cloning**

**Source**: `production` namespace
**Target**: `staging` namespace

**Considerations**:
- Storage will be cloned from `production` to `staging`
- Network policies may differ between namespaces
- Resource quotas may differ between namespaces
- RBAC permissions required in both namespaces

Verify that the `staging` namespace has sufficient resources.
```

### Clone with Modifications

**Future enhancement: Allow users to modify clone configuration:**

```
"Clone database-vm to test-db with 8Gi memory instead of 16Gi"
```

Modifications could include:
- Instance type/size
- Storage size
- Network configuration
- Cloud-init customization

## Common Issues

### Issue 1: Target VM Name Already Exists

**Error**: "VirtualMachine 'web-clone' already exists in namespace 'dev'"

**Solution:**
1. Choose a different target name
2. Delete existing VM with same name (if safe to do so)
3. Use vm-inventory to check existing VMs

### Issue 2: Insufficient Storage Quota

**Error**: "Namespace quota exceeded"

**Solution:**
- Check namespace resource quotas
- Request quota increase from cluster admin
- Use shared storage option (if appropriate)
- Delete unused PVCs to free quota

### Issue 3: Storage Class Not Accessible

**Error**: "StorageClass 'xyz' not found or not accessible"

**Solution:**
- Verify storage class exists in target namespace
- Check if storage class allows cross-namespace cloning
- Use different storage class for target
- Contact cluster admin for access

### Issue 4: PVC Clone Not Supported

**Error**: "Storage backend does not support PVC cloning"

**Solution:**
- Some storage classes don't support CSI volume cloning
- Use "new empty storage" option instead
- Manually snapshot and restore (alternative approach)
- Check storage class capabilities

### Issue 5: Source VM Running During Clone

**Error**: "Cannot clone from running VM with this storage backend"

**Solution:**
- Stop source VM before cloning
- Use snapshot-based cloning instead
- Check storage backend requirements

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with core and kubevirt toolsets

### Required MCP Tools
- `resources_get` (from openshift-virtualization) - Get source VM and storage details
  - Parameters: apiVersion, kind, namespace, name
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go

- `resources_create_or_update` (from openshift-virtualization) - Create cloned VM and storage
  - Parameters: resource (YAML/JSON)
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go

- `resources_list` (from openshift-virtualization) - List DataVolumes, PVCs, VMs
  - Parameters: apiVersion, kind, namespace, labelSelector
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go

### Related Skills
- `vm-create` - Create new VMs from scratch (alternative to cloning)
- `vm-inventory` - List and verify source/target VMs
- `vm-lifecycle-manager` - Start cloned VMs after creation
- `vm-delete` - Clean up failed clones or unwanted copies

### Reference Documentation
- [storage-errors.md](../../docs/troubleshooting/storage-errors.md) - VM cloning failure scenarios, storage provisioning issues, and DataVolume cloning errors (optionally consulted when cloning operations fail)
- [Troubleshooting INDEX](../../docs/troubleshooting/INDEX.md) - Navigation hub for discovering additional error categories when encountering unexpected issues outside the categories above
- [OpenShift Virtualization Cloning](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt/virtual_machines/cloning_vms/virt-cloning-vm.html)
- [DataVolume Cloning](https://github.com/kubevirt/containerized-data-importer/blob/main/doc/datavolumes.md#cloning)
- [KubeVirt VirtualMachine API](https://kubevirt.io/api-reference/)
- [CSI Volume Cloning](https://kubernetes.io/docs/concepts/storage/volume-pvc-datasource/)

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill creates new resources that consume cluster capacity. You MUST:

1. **Before Cloning**
   - Verify source VM exists and get full configuration
   - Ask user for clone configuration (name, namespace, storage strategy)
   - Present clone preview with resource impact
   - Wait for explicit user confirmation

2. **Configuration Confirmation**
   - Display source VM details
   - Show target VM configuration
   - Indicate storage cloning strategy
   - Estimate resource consumption (CPU, memory, storage)
   - Ask: "Proceed with VM cloning? (yes/no)"
   - Wait for explicit "yes"

3. **Never Auto-Execute**
   - **NEVER clone without user confirmation**
   - **NEVER assume storage strategy** - always ask user
   - **NEVER proceed if user says "no", "wait", "cancel"**

**Why This Matters:**
- **Resource Consumption**: Clones consume cluster resources (CPU, memory, storage)
- **Storage Costs**: Storage cloning can consume significant disk space
- **Naming Conflicts**: Duplicate names cause errors
- **Network Configuration**: May need adjustment for clones

## Security Considerations

- **RBAC Enforcement**: Requires create permissions in target namespace
- **Namespace Isolation**: Cannot clone across namespaces without proper permissions
- **Storage Quotas**: Respects namespace storage quotas
- **MAC Address Generation**: Automatic generation prevents MAC conflicts
- **UUID Generation**: New firmware UUIDs prevent conflicts
- **No Credential Exposure**: KUBECONFIG never exposed in output
- **Audit Trail**: All cloning operations logged in Kubernetes API audit logs

## Example Usage

### Example 1: Simple Clone with Storage

```
User: "Clone web-server to web-server-test in namespace dev"

Agent: [Invokes /vm-clone skill]
       [Step 1: Validation]
       [Calls resources_get for source VM]
       [Checks target name availability]
       [Discovers source storage: 50Gi]

## VM Cloning - Storage Strategy

Source VM: `web-server` (namespace: `production`)

Storage Configuration:
- DataVolume/PVC: `web-server-rootdisk` (50Gi)

Select storage strategy (1, 2, 3, or 4):

User: "1"  (Clone Storage)

Agent: [Step 3: Present configuration]

## VM Clone Configuration - Review

Source VM:
- Name: `web-server`
- Namespace: `production`
- Instance Type: u1.medium
- vCPU: 2, Memory: 4Gi
- Storage: 50Gi

Target VM (Clone):
- Name: `web-server-test`
- Namespace: `dev`
- Instance Type: u1.medium (copied)
- vCPU: 2, Memory: 4Gi (copied)
- Storage: Clone Storage (50Gi new allocation)

Storage Strategy:
- Strategy: Clone Storage (full copy)
- New Storage: 50Gi DataVolume/PVC
- Clone Time: ~5-10 minutes

Resource Impact:
- CPU: 2 vCPUs consumed
- Memory: 4Gi RAM consumed
- Storage: 50Gi

Proceed with VM cloning? (yes/no)

User: "yes"

Agent: [Step 4: Execute cloning]
       [Creates DataVolume with PVC clone source]

📦 Creating storage for cloned VM...
⏳ Cloning storage (this may take 5-10 minutes)...

       [Creates VirtualMachine]

🖥️ Creating cloned VirtualMachine...
✓ VirtualMachine `web-server-test` created in namespace `dev`

       [Monitors DataVolume status]

⏳ Storage cloning in progress...
   Phase: CloneInProgress
   Progress: 45%

⏳ Storage cloning in progress...
   Phase: Succeeded

       [Step 5: Report results]

## ✓ VM Cloned Successfully

Source VM: `web-server` (namespace: `production`)
Target VM: `web-server-test` (namespace: `dev`)

Cloned VM Details:
- Name: `web-server-test`
- Namespace: `dev`
- Instance Type: u1.medium
- vCPU: 2, Memory: 4Gi
- Storage: 50Gi
- Status: Stopped (ready to start)

Storage Cloning:
- ✓ Storage cloned successfully
- ✓ DataVolume: `web-server-test-rootdisk` (50Gi)
- ✓ Clone completed in 7m23s
- ✓ Target VM has independent storage

Next Steps:

To start the cloned VM:
```
"Start VM web-server-test in namespace dev"
```
```

### Example 2: Clone with New Empty Storage

```
User: "Clone template-vm to app-01 with empty storage"

Agent: [Invokes /vm-clone skill]
       [Validation complete]
       [Step 2: Storage strategy]

Select storage strategy (1, 2, 3, or 4):

User: "3"  (Create New Empty Storage)

Agent: [Presents configuration]

Storage Strategy:
- Strategy: New Empty Storage
- New Storage: 30Gi empty DataVolume/PVC
- No data cloned from source

Proceed with VM cloning? (yes/no)

User: "yes"

Agent: [Creates empty DataVolume and VM]

## ✓ VM Cloned Successfully

Storage Creation:
- ✓ New empty storage created
- ✓ DataVolume: `app-01-rootdisk` (30Gi)
- ℹ️ Storage is empty (no data from source)

Important Notes:
- ℹ️ The clone has empty storage (no data from source)
- ℹ️ OS installation or configuration may be required
```

### Example 3: Batch Cloning

```
User: "Create 3 copies of template-vm named web-01, web-02, web-03 in production namespace"

Agent: [Invokes /vm-clone skill]
       [Validates source VM]
       [Generates target names]
       [Checks all names for availability]

## Batch VM Cloning - Review

Source VM: `template-vm`

Target VMs:
1. `web-01` (namespace: `production`)
2. `web-02` (namespace: `production`)
3. `web-03` (namespace: `production`)

Storage Strategy: Clone Storage (full copy for each)

Total Resource Impact:
- VMs: 3 new VMs
- Storage: 90Gi (3 × 30Gi)
- vCPUs: 6 total (3 × 2)
- Memory: 12Gi total (3 × 4Gi)

Estimated Time: ~20-30 minutes

Proceed with batch cloning? (yes/no)

User: "yes"

Agent: [Clones VMs sequentially]

📦 Cloning VM 1 of 3: web-01...
✓ web-01 created and storage cloning in progress

📦 Cloning VM 2 of 3: web-02...
✓ web-02 created and storage cloning in progress

📦 Cloning VM 3 of 3: web-03...
✓ web-03 created and storage cloning in progress

## ✓ Batch Cloning Completed

Successfully cloned 3 VMs from `template-vm`:
- ✓ web-01 (production)
- ✓ web-02 (production)
- ✓ web-03 (production)

Total resources created:
- 3 VirtualMachines
- 90Gi storage
- All VMs in Stopped state (ready to start)
```

### Example 4: Shared Storage Warning

```
User: "Clone db-vm to db-test"

Agent: [Validation complete]

Select storage strategy (1, 2, 3, or 4):

User: "2"  (Reference Existing Storage)

Agent: [Issues warning]

⚠️ WARNING: Shared Storage is Dangerous

You selected to share storage between source and target VMs.

Risks:
- Both VMs writing to the same disk will cause data corruption
- Only safe if source VM is stopped and will remain stopped

Recommendation: Use Option 1 (Clone Storage) instead.

Proceed with shared storage anyway? (yes/cancel)

User: "cancel"

Agent: VM cloning cancelled by user. No resources were created.
```

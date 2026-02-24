---
name: vm-rebalance
description: |
  Orchestrate VM migrations across cluster nodes for load balancing, maintenance, and resource optimization.

  Use when:
  - "Move VM database-01 to worker-03"
  - "Rebalance VMs to optimize CPU load"
  - "Drain worker-02 for maintenance"
  - "Automatically rebalance the cluster"

  Supports Manual (user-driven) and Automatic (AI-driven) modes.

  NOT for creating VMs (use vm-create) or lifecycle only (use vm-lifecycle-manager).

model: inherit
color: yellow
---

# /vm-rebalance Skill

Orchestrate virtual machine migrations across OpenShift cluster nodes for load balancing, maintenance, and resource optimization. Supports manual and automatic rebalancing modes with both live migration (zero downtime) and cold migration (brief downtime) strategies.

**Implementation**: Uses KubeVirt's VirtualMachineInstanceMigration API for live migrations and node affinity for cold migrations, following official KubeVirt patterns.

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_list` - List VMs and nodes
- `resources_get` - Get VM and node details
- `resources_create_or_update` - Create migrations and update VM specs
- `vm_lifecycle` - Start/stop VMs for cold migration
- `nodes_top` - Monitor node resource usage
- `pods_top` - Monitor VM resource consumption

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file

**Required Cluster Setup**:
- OpenShift cluster (>= 4.17)
- OpenShift Virtualization operator installed
- ServiceAccount with permissions: get/list/update for VMs, create for VirtualMachineInstanceMigration
- For live migration: RWX storage and sufficient network bandwidth

### Prerequisite Verification

**Before executing:**

1. **Check MCP Server** - Verify `openshift-virtualization` exists in `.mcp.json`
2. **Check Environment** - Verify `KUBECONFIG` is set (check presence only, never expose value)
3. **Check Capability** (for live migration):
   - Use `resources_get` to check PVC access mode is ReadWriteMany (RWX)
   - Verify VM has running VirtualMachineInstance

**If Prerequisites Fail:**

```
❌ Cannot execute vm-rebalance: MCP server 'openshift-virtualization' is not available

📋 Setup Instructions:
1. Add openshift-virtualization to .mcp.json
2. Set KUBECONFIG environment variable
3. Ensure ServiceAccount has required permissions
4. Restart Claude Code to reload MCP servers

🔗 Documentation: https://github.com/openshift/openshift-mcp-server

Options: "setup" | "skip" | "abort"
```

⚠️ **SECURITY**: Never display KUBECONFIG path or credential values in output.

## When to Use This Skill

**Trigger when:**
- User explicitly invokes `/vm-rebalance` command
- User requests moving specific VM(s) to specific node(s)
- User wants to drain a node for maintenance
- User requests load balancing or resource optimization
- User wants to redistribute VMs across cluster

**User phrases:**
- "Move VM database-01 to worker-03"
- "Live migrate web-server to worker-05"
- "Drain worker-02 for maintenance"
- "Balance CPU load across nodes"
- "Automatically rebalance the cluster"

**Do NOT use when:**
- Creating VMs → Use `/vm-create`
- Start/stop only → Use `/vm-lifecycle-manager`
- Cloning VMs → Use `/vm-clone`
- Deleting VMs → Use `/vm-delete`

## Workflow

### Step 1: Determine Rebalancing Mode

**Analyze user request:**

**Manual Mode Indicators:**
- User specifies VM name(s) and target node(s)
- Examples: "Move VM database-01 to worker-03", "Migrate web-server to worker-05"

**Automatic Mode Indicators:**
- User requests AI-driven rebalancing with high-level goal
- Examples: "Rebalance VMs based on CPU", "Automatically optimize cluster load"

### Step 2: Load Strategy File and Execute

**For Manual Mode:**

**Document Consultation** (REQUIRED - Execute FIRST):
1. Read [REBALANCE_MANUAL.md](./REBALANCE_MANUAL.md) using Read tool
2. Output: "I consulted [REBALANCE_MANUAL.md](rh-virt/skills/vm-rebalance/REBALANCE_MANUAL.md) to understand the manual migration workflow."

**Then execute**: Follow workflow in REBALANCE_MANUAL.md

---

**For Automatic Mode:**

**Document Consultation** (REQUIRED - Execute FIRST):
1. Read [REBALANCE_AUTOMATIC.md](./REBALANCE_AUTOMATIC.md) using Read tool
2. Output: "I consulted [REBALANCE_AUTOMATIC.md](rh-virt/skills/vm-rebalance/REBALANCE_AUTOMATIC.md) to understand the automatic rebalancing workflow."

**Then execute**: Follow workflow in REBALANCE_AUTOMATIC.md

## Common Validation Logic

**This validation is shared by ALL migration strategies.**

Before executing any VM migration, perform these validations for each VM:

### Validation 1: Verify VM Exists

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
- `apiVersion`: "kubevirt.io/v1"
- `kind`: "VirtualMachine"
- `name`: "<vm-name>"
- `namespace`: "<namespace>"

**Extract**:
- `spec.template.spec.volumes[].persistentVolumeClaim.claimName` - PVC names
- `status.ready` - VM ready state

**Error Handling**:
- VM not found → "VM '<vm-name>' does not exist in namespace '<namespace>'. Use '/vm-inventory' to see available VMs."
- Namespace not found → "Namespace '<namespace>' does not exist. Verify namespace name."
- Permission denied → "Insufficient permissions. ServiceAccount needs 'get' permission for VirtualMachine resources."

### Validation 2: Check Current VM Location

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters** (only if VM is running):
- `apiVersion`: "kubevirt.io/v1"
- `kind`: "VirtualMachineInstance"
- `name`: "<vm-name>"
- `namespace`: "<namespace>"

**Extract**:
- `status.nodeName` - Current node
- `status.phase` - Current phase

**Validation**:
- If already on target node → "VM '<vm-name>' is already on '<target-node>'. No migration needed."

### Validation 3: Validate Storage Compatibility

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
- `apiVersion`: "v1"
- `kind`: "PersistentVolumeClaim"
- `name`: "<pvc-name>"
- `namespace`: "<namespace>"

**Extract**:
- `spec.accessModes` - Contains "ReadWriteMany" (RWX) → Live migration supported
- Only "ReadWriteOnce" (RWO) → Live migration NOT supported

**Error Handling for live migration**:
- If RWO → "Cannot perform live migration. VM uses ReadWriteOnce (RWO) storage. Use cold migration instead (brief downtime ~30-60s)."
- If VM not running → "Cannot perform live migration. VM is not running. Use cold migration or start VM first."

**Reference**: See [references/live-migration-best-practices.md](./references/live-migration-best-practices.md) for complete storage requirements.

### Validation 4: Verify Target Node Exists

**MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
- `apiVersion`: "v1"
- `kind`: "Node"

**Validation**:
- Verify target node exists in list
- Check `status.conditions[]` shows Ready=True
- Check node is schedulable (not cordoned)

**Error Handling**:
- Not found → "Target node '<target-node>' does not exist."
- Not Ready → "Target node '<target-node>' is not Ready. Choose different target."
- Cordoned → "Target node '<target-node>' is cordoned (SchedulingDisabled). Choose different target or uncordon node."

**Reference**: See [../../docs/troubleshooting/scheduling-errors.md](../../docs/troubleshooting/scheduling-errors.md) for scheduling issues.

## Node Selection for Automatic Rebalancing

**Applies to Automatic Mode only. Manual Mode uses user-specified nodes.**

### Suitable Node Criteria

**Use `resources_list` with apiVersion="v1", kind="Node"**

Filter nodes where ALL conditions are true:
1. `metadata.labels["kubevirt.io/schedulable"] == "true"` (official KubeVirt marker)
2. `status.capacity["devices.kubevirt.io/kvm"]` > "0" (KVM devices available)
3. No `node-role.kubernetes.io/control-plane` or `node-role.kubernetes.io/master` label (worker nodes only)

**If no nodes found**: "No suitable nodes found. Check OpenShift Virtualization operator status and node hardware virtualization support."

**Note**: Ignore cluster-specific custom taints (e.g., `node-purpose=virtualization`). Always use official KubeVirt labels.

## Common Migration Types

### Live Migration
- **Zero downtime** - VM stays running
- **Brief network pause** (<1 second) during cutover
- **Requires**: ReadWriteMany (RWX) storage
- **Process**: Memory transferred while VM runs
- **Use when**: Minimal disruption required

**Reference**: [references/live-migration-best-practices.md](./references/live-migration-best-practices.md)

### Cold Migration
- **Brief downtime** (~30-60 seconds)
- **Works with any storage** (RWO or RWX)
- **Process**: Stop VM → Update placement → Start on target
- **Use when**: Live migration not supported or acceptable downtime

**Reference**: See REBALANCE_MANUAL.md for cold migration workflow

## Common Plan Visualization

**All rebalancing strategies MUST use this standardized format when presenting plans to users.**

This ensures consistent, clear communication across Manual and Automatic modes.

### Information Relevance Principle

**Show only what matters to the user's decision:**

- **Include**: Deviations from defaults, user-specified criteria, or non-obvious context
- **Exclude**: Standard procedures, default settings, or information already visible in tables

**Examples**:
- ✅ Show node criteria IF user specified constraints ("only nodes with SSD")
- ❌ Don't show default criteria when using standard behavior
- ✅ Show analysis IF it reveals critical context (e.g., all VMs on one node)
- ❌ Don't repeat what's visible in the tables

**Apply this principle throughout the plan**: Only explain what's non-obvious, non-standard, or specifically requested.

### Standard Plan Format

**Present rebalancing plans using these two tables:**

#### Table 1: VM Rebalance Plan

Shows what will happen to each VM:

```markdown
## 📋 VM Rebalance Plan

| VM | Instance Type | Current Node | → | New Node | Type | Downtime | Notes |
|----|---------------|--------------|---|----------|------|----------|-------|
| vm-name-1 | u1.xlarge | worker-01 | → | worker-03 | Live | <1s pause | ContainerDisk - easy migration |
| vm-name-2 | u1.2xmedium | worker-01 | → | worker-02 | Cold | ~40s | RWO storage |
| vm-name-3 | u1.medium | worker-02 | - | *stays* | - | - | Already balanced |
```

**Column Definitions:**
- **VM**: VM name
- **Instance Type**: Instance type (e.g., u1.xlarge, u1.2xmedium)
- **Current Node**: Node where VM is currently running
- **→**: Visual indicator of movement
- **New Node**: Target node (or "*stays*" if no migration needed)
- **Type**: Migration type (Live, Cold, or "-" for no migration)
- **Downtime**: Expected downtime (<1s pause for live, ~30-60s for cold, "-" for no migration)
- **Notes**: Brief explanation (storage type, constraints, reason for staying, etc.)

#### Table 2: Node State Before → After

Shows cluster-wide impact:

```markdown
## 📊 Node State: Before → After

| Node | VMs Now | CPU Now | Memory Now | → | VMs After | CPU After | Memory After | Change |
|------|---------|---------|------------|---|-----------|-----------|--------------|--------|
| worker-01 | 5 | 85% | 72% | → | 3 | 68% | 59% | ✓ Reduced load |
| worker-02 | 2 | 42% | 48% | → | 3 | 58% | 61% | ← Receiving VMs |
| worker-03 | 3 | 38% | 51% | → | 4 | 55% | 63% | ← Receiving VMs |
```

**Column Definitions:**
- **Node**: Node name
- **VMs Now**: Current number of VMs on this node
- **CPU Now**: Current CPU utilization percentage
- **Memory Now**: Current memory utilization percentage
- **→**: Visual indicator of change
- **VMs After**: Number of VMs after rebalancing
- **CPU After**: Estimated CPU utilization after rebalancing
- **Memory After**: Estimated memory utilization after rebalancing
- **Change**: Brief description of what's happening (e.g., "✓ Reduced load", "← Receiving VMs", "✓ Balanced")

### Additional Plan Context

After the two tables, include:

**Key Improvement:**
```markdown
**Key Improvement:** [Brief description of main benefit]
Example: "Distribution from 1 node to 4 nodes hosting VMs"
Example: "CPU variance reduced from 22% to 4% (81% improvement)"
```

**Rebalance Summary (for batch operations):**
```markdown
**Rebalance Summary:**
- **Total VMs to Rebalance**: 5
- **Live**: 4 (zero downtime)
- **Cold**: 1 (brief downtime)
- **VMs Staying**: 2 (nodeAffinity constraints)
- **Total Downtime**: ~40s cumulative (cold only)
- **Estimated Duration**: 1-2 minutes (parallel execution)
```

**Execution Mode:**
```markdown
**Execution Mode**: **Parallel** (all VMs rebalance simultaneously)
- Default to parallel execution for time efficiency
- Only use sequential if user explicitly requests it or cluster constraints require it
```

**CRITICAL GUIDELINES:**
1. **Execution Default**: Parallel execution UNLESS user specifies sequential
2. **Risk Assessment**: ONLY include if there's a genuine risk users must understand (e.g., network saturation, resource exhaustion). Skip this section for normal rebalancing operations.

### Terminology Standards

**CRITICAL**: Use consistent terminology across all modes:

- ✅ **"VM Rebalance Plan"** - Correct term for this skill
- ❌ **"VM Migration Plan"** - Do NOT use (reserved for future migration skill)
- ✅ **"Rebalancing"** - Correct term for the overall operation
- ✅ **"Live/Cold migration"** - Correct for describing the method
- ✅ **"Current Node" / "New Node"** - Clear directional language
- ✅ **"VMs Now" / "VMs After"** - Clear temporal language

### When to Use This Format

**Manual Mode**: Use when presenting plan for user confirmation (Step 3)
**Automatic Mode**: Use when presenting generated plan for user approval (Step 3)

**Reference**: Both REBALANCE_MANUAL.md and REBALANCE_AUTOMATIC.md must follow this format.

## Common Error Handling

**All migration strategies use this error handling logic.**

### Error 1: Live Migration Fails - Storage Not RWX

**Symptom**: "Cannot live migrate VM: PVC access mode is ReadWriteOnce"

**Cause**: Live migration requires RWX storage. VMs with RWO cannot be live migrated.

**Solution**:
1. Use cold migration (works with RWO)
2. Or convert PVC to RWX storage class (requires data migration)

**Reference**: [../../docs/troubleshooting/storage-errors.md](../../docs/troubleshooting/storage-errors.md)

### Error 2: VM Stuck in ErrorUnschedulable After Cold Migration

**Symptom**: "VM cannot be scheduled on target node: ErrorUnschedulable"

**Cause**: Target node has insufficient resources, taints, or scheduling constraints.

**Solution**:
1. Check node capacity using `nodes_top` MCP tool
2. Verify node has no blocking taints using `resources_get` for Node
3. Add tolerations to VM if node has taints
4. Choose different target node
5. Remove nodeSelector to allow scheduler flexibility

**Reference**: [../../docs/troubleshooting/scheduling-errors.md](../../docs/troubleshooting/scheduling-errors.md)

### Error 3: Live Migration Times Out

**Symptom**: "Migration exceeded timeout: 150 seconds per GiB"

**Cause**: Large VM memory or high dirty page rate preventing convergence.

**Solution**:
1. Retry migration (may succeed on second attempt)
2. Reduce VM workload during migration
3. Use cold migration (guaranteed to complete)
4. Increase timeout in HyperConverged CR (see performance-tuning reference)

**Reference**: [references/performance-tuning.md](./references/performance-tuning.md)

### Error 4: Migration Rejected - Cluster Limit Reached

**Symptom**: "Migration rejected: cluster migration limit reached (5 concurrent)"

**Cause**: KubeVirt limits concurrent migrations (default: 5 cluster-wide, 2 per node).

**Solution**:
1. Wait for ongoing migrations to complete (monitor with `resources_list` for VirtualMachineInstanceMigration)
2. Retry migration
3. For batch operations, migrate sequentially
4. Increase cluster limit in HyperConverged CR (if network allows)

**Reference**: [references/performance-tuning.md](./references/performance-tuning.md)

### Error 5: RBAC Permission Denied

**Symptom**: "Forbidden: User cannot create VirtualMachineInstanceMigration"

**Cause**: ServiceAccount lacks RBAC permissions.

**Solution**:
1. Verify KUBECONFIG has appropriate permissions
2. Required: `create` on VirtualMachineInstanceMigration, `update` on VirtualMachine
3. Contact cluster admin to grant permissions

### Error 6: Network Saturation During Concurrent Migrations

**Symptom**: Multiple migrations slow or fail; high network utilization

**Cause**: Too many concurrent migrations saturating network bandwidth.

**Solution**:
1. Reduce concurrent migrations in HyperConverged CR
2. Set bandwidth limit per migration
3. Use dedicated migration network

**Reference**: [references/performance-tuning.md](./references/performance-tuning.md)

### Error 7: Resource Version Conflict During Cold Migration

**Symptom**: "Apply failed with 1 conflict: conflict with 'kubernetes-mcp-server' using kubevirt.io/v1: .spec.runStrategy"

**Cause**: Using stale VM resourceVersion when updating nodeAffinity after `vm_lifecycle` operation.

**Solution**:
After `vm_lifecycle` stop, re-read VM using `resources_get` before updating nodeAffinity. This gets fresh resourceVersion.

**Workflow**: Stop VM → Wait for completion → Re-read VM → Update nodeAffinity → Start VM

**Reference**: [REBALANCE_MANUAL.md - Sub-step 4b.2.5](./REBALANCE_MANUAL.md)

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with KubeVirt toolset
  - Source: https://github.com/openshift/openshift-mcp-server

### Required MCP Tools

- `resources_list` - List cluster resources (VMs, nodes, PVCs, migrations)
- `resources_get` - Get resource details (VM specs, VMI status, PVC access modes)
- `resources_create_or_update` - Create migrations, update VM nodeAffinity
- `vm_lifecycle` - Start/stop VMs for cold migration
- `nodes_top` - Monitor node resource usage
- `pods_top` - Monitor VM resource consumption
- `nodes_stats_summary` - Detailed node statistics

**Source**: https://github.com/openshift/openshift-mcp-server

### Related Skills

- `vm-inventory` - List VMs and check placement before migration
- `vm-lifecycle-manager` - Simple start/stop without migration
- `vm-create` - Create VMs with initial placement preferences
- `vm-snapshot-create` - Backup VMs before risky migrations

### Reference Documentation

**Skill Strategy Files**:
- [REBALANCE_MANUAL.md](./REBALANCE_MANUAL.md) - User-driven migration workflow
- [REBALANCE_AUTOMATIC.md](./REBALANCE_AUTOMATIC.md) - AI-driven rebalancing workflow

**Performance and Best Practices**:
- [references/live-migration-best-practices.md](./references/live-migration-best-practices.md) - Configuration, requirements, dedicated networks
- [references/performance-tuning.md](./references/performance-tuning.md) - Right-sizing, overcommit, bandwidth tuning
- [references/anti-patterns.md](./references/anti-patterns.md) - Common mistakes to avoid
- [references/production-considerations.md](./references/production-considerations.md) - HA strategies, capacity planning, security

**Troubleshooting**:
- [../../docs/troubleshooting/INDEX.md](../../docs/troubleshooting/INDEX.md) - Master troubleshooting index
- [../../docs/troubleshooting/scheduling-errors.md](../../docs/troubleshooting/scheduling-errors.md) - ErrorUnschedulable, taints, resources
- [../../docs/troubleshooting/storage-errors.md](../../docs/troubleshooting/storage-errors.md) - PVC access mode issues
- [../../docs/troubleshooting/lifecycle-errors.md](../../docs/troubleshooting/lifecycle-errors.md) - VM start/stop failures

**Official Red Hat Documentation**:
- [OpenShift Virtualization - Live Migration](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt-live-migration)
- [OpenShift Virtualization - Node Placement](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt-node-placement)

**Upstream KubeVirt Documentation**:
- [Live Migration - KubeVirt User Guide](https://kubevirt.io/user-guide/compute/live_migration/)
- [Node Assignment - KubeVirt User Guide](https://kubevirt.io/user-guide/compute/node_assignment/)
- [VirtualMachineInstanceMigration API](https://kubevirt.io/api-reference/main/definitions.html#_v1_virtualmachineinstancemigration)

## Critical: Human-in-the-Loop Requirements

**IMPORTANT**: This skill performs VM migrations affecting workload placement and availability. You MUST:

1. **Before Initiating Migration**
   - Present complete rebalance plan (VM, nodes, type, impact)
   - Clearly explain downtime (live = <1s pause, cold = 30-60s)
   - Show current vs target placement
   - Ask: "Confirm this migration?"
   - Wait for explicit user confirmation

2. **Never Auto-Execute**
   - **NEVER migrate without confirmation**
   - **NEVER assume live vs cold** - ask or infer from storage
   - **NEVER skip impact explanation**
   - **NEVER proceed if validation fails** - report issues first

3. **For Batch Operations**
   - Present all VMs to be migrated
   - Show total impact (e.g., "3 VMs, 2 live + 1 cold")
   - Confirm entire batch before starting
   - Report progress for each
   - Stop on first failure

**Why This Matters**:
- **Live Migration**: Brief pause, bandwidth usage, performance impact during transfer
- **Cold Migration**: Service downtime, dropped connections, application interruption
- **Wrong Node**: Performance degradation or scheduling conflicts
- **Batch**: Can saturate network or exhaust resources

**Rationale**: Prevents unintended disruption; maintains user control over placement and availability.

## Security Considerations

- **RBAC Enforcement**: Requires specific permissions (create/update/list)
- **Node Access**: Respects node taints and RBAC policies
- **Storage Security**: Data remains encrypted if using encrypted storage classes
- **Network Isolation**: Migrations respect NetworkPolicies
- **Audit Trail**: All operations logged in Kubernetes API audit logs
- **KUBECONFIG Security**: Credentials never exposed in output
- **Resource Quotas**: Respects namespace quotas and limits
- **Tenant Isolation**: Cannot migrate across namespaces without RBAC

---

**Strategy Implementation Status**:
- ✅ **REBALANCE_MANUAL.md** - Fully implemented
- ✅ **REBALANCE_AUTOMATIC.md** - Fully implemented

**Reference Documentation Status**:
- ✅ **live-migration-best-practices.md** - Complete
- ✅ **performance-tuning.md** - Complete
- ✅ **anti-patterns.md** - Complete
- ✅ **production-considerations.md** - Complete

---

**Last Updated**: 2026-02-24
**OpenShift Virtualization Versions**: 4.17, 4.18, 4.19, 4.20

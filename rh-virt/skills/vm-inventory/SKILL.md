---
name: vm-inventory
description: |
  List and view virtual machines across namespaces with status, resource usage, and health information. Use this skill when users request:
  - "List all VMs"
  - "Show VMs in namespace [name]"
  - "What VMs are running?"
  - "Get details of VM [name]"

  This skill provides comprehensive VM inventory and status reporting.

  NOT for creating or modifying VMs (use vm-create or vm-lifecycle-manager instead).

model: inherit
color: cyan
---

# /vm-inventory Skill

List and inspect virtual machines in OpenShift Virtualization clusters. This skill provides read-only access to VM information without making any modifications.

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_list` (from openshift-virtualization) - List Kubernetes resources including VirtualMachines
- `resources_get` (from openshift-virtualization) - Get specific Kubernetes resource details

**Fallback CLI Commands** (if MCP tools are unavailable):
- `oc get virtualmachines` - List VirtualMachines using OpenShift CLI
- `oc get vm` - Shorthand for listing VirtualMachines
- `oc get vm <name> -n <namespace> -o yaml` - Get VM details in YAML format

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to list and get VirtualMachine resources

### Prerequisite Verification

**Before executing, verify MCP server availability:**

1. **Check MCP Server Configuration**
   - Verify `openshift-virtualization` exists in `.mcp.json`
   - If missing → Report to user with setup instructions

2. **Check Environment Variables**
   - Verify `KUBECONFIG` is set (check presence only, never expose value)
   - If missing → Report to user

3. **Verify Cluster Access** (optional quick check)
   - Test basic connectivity to cluster
   - If fails → Report connection error

**Human Notification Protocol:**

When prerequisites fail:

```
❌ Cannot execute vm-inventory: MCP server 'openshift-virtualization' is not available

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
- "cli" - Use OpenShift CLI commands as fallback (requires KUBECONFIG)
- "skip" - Skip this skill
- "abort" - Stop workflow

Please respond with your choice.
```

⚠️ **SECURITY**: Never display actual KUBECONFIG path or credential values in output.

**Note on Fallback Behavior**:
- If MCP server is unavailable but KUBECONFIG is set, the skill CAN proceed with CLI commands
- Always offer the user the choice between setup (MCP) or CLI fallback
- CLI fallback requires explicit user confirmation before executing any commands

## When to Use This Skill

**Trigger this skill when:**
- User explicitly invokes `/vm-inventory` command
- User wants to see all VMs or VMs in a specific namespace
- User asks about VM status or health
- User needs to find a VM by name
- User wants details about a specific VM configuration

**User phrases that trigger this skill:**
- "List all VMs"
- "Show VMs in production namespace"
- "What VMs are running?"
- "Get details of VM web-server"
- "Show me the status of database-vm"
- "/vm-inventory" (explicit command)

**Do NOT use this skill when:**
- User wants to create a VM → Use `/vm-create` skill instead
- User wants to start/stop VMs → Use `/vm-lifecycle-manager` skill instead
- User wants to modify VM configuration → Different operation (not inventory)

## Workflow

**CRITICAL EXECUTION PATTERN**:
1. **ALWAYS attempt MCP server tools FIRST** - Try `resources_list` or `resources_get` from the openshift-virtualization MCP server
2. **If MCP tools fail or are unavailable** - Propose to user to use CLI commands (`oc get vm`, `oc get virtualmachines`)
3. **Never skip MCP attempt** - Even if you suspect they might not be available, always try them first

**Tool Execution Priority**:
- **Primary**: MCP tools (`resources_list`, `resources_get`) from openshift-virtualization server
- **Fallback**: CLI commands (`oc`) - Only after MCP tools fail and with user confirmation

**MCP Tool Reference**:
- Tool source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go
- Tool names: `resources_list`, `resources_get`
- These tools provide direct access to Kubernetes resources through the MCP protocol

### Workflow A: List All VMs (Across All Namespaces)

**Step 1: Query VirtualMachine Resources Using MCP Tool**

**PRIMARY: MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "allNamespaces": true
}
```

**Expected Output**: List of VirtualMachine resources with:
- Name
- Namespace
- Status (Running/Stopped/Pending/Error)
- Resource specifications (vCPU, memory)
- Age
- Node assignment (for running VMs)

**Error Handling**:
If the MCP tool call fails (tool not found, connection error, etc.):

1. **Report to user**:
   ```
   ⚠️ MCP tool 'resources_list' is not available or failed to execute.

   📋 I can use the OpenShift CLI instead to list VMs.

   Would you like me to proceed with: `oc get virtualmachines -A`?

   (Respond "yes" to proceed with CLI, or "setup" to configure MCP server)
   ```

2. **Wait for user confirmation**

3. **If user approves**, execute CLI fallback:
   ```bash
   oc get virtualmachines -A -o json
   ```

**CLI Fallback Command**:
```bash
oc get virtualmachines --all-namespaces -o json
# or shorthand:
oc get vm -A -o json
```

**Step 2: Format and Display Results**

**CRITICAL FORMATTING RULE**:
- **If total VMs > 2**: Display results in a **table format** ordered by namespace and status
- **If total VMs ≤ 2**: Use list format organized by namespace

**Table Format (when VMs > 2):**

```markdown
## 📋 Virtual Machines (All Namespaces)

| Namespace | VM Name | Status | Age | Resources | Node |
|-----------|---------|--------|-----|-----------|------|
| default | alejandro-test | ✓ Running | 1h | 2 vCPU, 4Gi | ip-10-0-15-252 |
| production | database-vm | ✗ Stopped | 30d | 8 vCPU, 16Gi | - |
| production | web-server-01 | ✓ Running | 15d | 4 vCPU, 8Gi | worker-01 |
| production | web-server-02 | ✓ Running | 15d | 4 vCPU, 8Gi | worker-02 |
| development | debug-vm | ⚠ Pending | 2d | 2 vCPU, 4Gi | - |
| development | test-vm | ✓ Running | 5d | 2 vCPU, 4Gi | worker-03 |

**Summary:**
- **Total VMs**: 6
- **Running**: 4
- **Stopped**: 1
- **Pending**: 1
```

**List Format (when VMs ≤ 2):**

```markdown
## 📋 Virtual Machines (All Namespaces)

### Namespace: production
- ✓ **web-server-01** - Running (4 vCPU, 8Gi RAM)

### Namespace: development
- ✓ **test-vm** - Running (2 vCPU, 4Gi RAM)

### Summary:
- **Total VMs**: 2
- **Running**: 2
```

**Table Ordering Rules:**
1. **Primary sort**: Namespace (alphabetical)
2. **Secondary sort**: Status (Running → Pending → Stopped → Failed/Error)
3. **Tertiary sort**: VM Name (alphabetical within same namespace and status)

**Status Indicators:**
- ✓ Running/Ready
- ✗ Stopped/Halted
- ⚠ Pending/Starting/Terminating
- ❌ Failed/Error

### Workflow B: List VMs in Specific Namespace

**Step 1: Gather Namespace**

Ask user for namespace if not provided in the request.

**Step 2: Query VMs in Namespace Using MCP Tool**

**PRIMARY: MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>"  // REQUIRED - user-provided namespace
}
```

**Expected Output**: List of VirtualMachine resources in the specified namespace with status and configuration details

**Error Handling**:
If the MCP tool call fails:

1. **Report to user**:
   ```
   ⚠️ MCP tool 'resources_list' failed.

   📋 Fallback option: Use OpenShift CLI command:
   `oc get virtualmachines -n <namespace>`

   Would you like me to proceed with the CLI command?
   ```

2. **Wait for user confirmation**

3. **If approved**, execute CLI fallback:
   ```bash
   oc get virtualmachines -n <namespace> -o json
   ```

**CLI Fallback Command**:
```bash
oc get virtualmachines -n <namespace> -o json
# or shorthand:
oc get vm -n <namespace> -o json
```

**Step 3: Display Namespace-Specific Results**

```markdown
## 📋 Virtual Machines in 'production'

| Name | Status | vCPU | Memory | Age | Node |
|------|--------|------|--------|-----|------|
| web-server-01 | Running | 4 | 8Gi | 15d | worker-01 |
| web-server-02 | Running | 4 | 8Gi | 15d | worker-02 |
| database-vm | Stopped | 8 | 16Gi | 30d | - |

**Summary**: 3 VMs (2 running, 1 stopped)
```

### Workflow C: Get Details of Specific VM

**Step 1: Gather VM Information**

Required:
- VM name
- Namespace (ask if not provided)

**Step 2: Retrieve VM Resource Details Using MCP Tool**

**PRIMARY: MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",  // REQUIRED - user-provided or prompted
  "name": "<vm-name>"          // REQUIRED - user-provided
}
```

**Expected Output**: Complete VirtualMachine resource specification including:
- Metadata (name, namespace, labels, annotations, creation timestamp)
- Spec (instance type, workload, run strategy, resource requirements, volumes, networks)
- Status (conditions, phase, ready state, node assignment, pod IP, guest agent info)

**Error Handling**:
If the MCP tool call fails:

1. **Report to user**:
   ```
   ⚠️ MCP tool 'resources_get' failed.

   📋 Fallback option: Use OpenShift CLI command:
   `oc get vm <vm-name> -n <namespace> -o yaml`

   Would you like me to proceed with the CLI command?
   ```

2. **Wait for user confirmation**

3. **If approved**, execute CLI fallback:
   ```bash
   oc get virtualmachine <vm-name> -n <namespace> -o yaml
   ```

**CLI Fallback Command**:
```bash
oc get virtualmachine <vm-name> -n <namespace> -o yaml
# or shorthand:
oc get vm <vm-name> -n <namespace> -o yaml
```

**Step 3: Interpret Status and Conditions (Optional)**

**OPTIONAL**: If the VM has error status or complex conditions, consult documentation for interpretation.

**Document Consultation** (OPTIONAL - when VM has error/warning status):
1. **Action**: Read [troubleshooting/INDEX.md](../../docs/troubleshooting/INDEX.md) using the Read tool to understand status meanings (ErrorUnschedulable, ErrorDataVolumeNotReady, CrashLoopBackOff, etc.)
2. **Output to user**: "I consulted [troubleshooting/INDEX.md](../../docs/troubleshooting/INDEX.md) to interpret the VM status '<status-value>'."

**When to consult**:
- VM status is ErrorUnschedulable, ErrorDataVolumeNotReady, ErrorPvcNotFound
- VM conditions show warnings or errors
- VM in unexpected state (e.g., CrashLoopBackOff, Terminating stuck)

**When NOT to consult**:
- VM status is normal (Running, Stopped, Provisioning)
- Simple status queries without error conditions

**Step 4: Display Detailed Information**

```markdown
## 🖥️ Virtual Machine Details

### Basic Information
- **Name**: `web-server-01`
- **Namespace**: `production`
- **Status**: Running
- **Created**: 15 days ago

### Configuration
- **Instance Type**: u1.medium
- **Workload**: Fedora
- **Run Strategy**: Always (auto-restart on crash)

### Resources
- **vCPU**: 4 cores
- **Memory**: 8Gi
- **Storage**: 50Gi
- **Storage Class**: ocs-storagecluster-ceph-rbd

### Network
- **Primary**: default (pod network)
- **Secondary**: vlan100 (multus - 192.168.100.5)

### Volumes
- **rootdisk**: 50Gi (DataVolume/PVC)

### Current State
- **Phase**: Running
- **Ready**: True
- **Node**: worker-01
- **Pod IP**: 10.129.2.45
- **Guest OS Uptime**: 12 days

### Conditions
- ✓ Ready
- ✓ LiveMigratable
- ✓ AgentConnected

### Labels
- app: web
- env: production
- tier: frontend
```

### Workflow D: Filter VMs by Criteria

**Step 1: Query VMs with Filters Using MCP Tool**

**PRIMARY: MCP Tool**: `resources_list` (from openshift-virtualization)

**Parameters** (with label selector):
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "allNamespaces": true,           // or specify "namespace": "<namespace>"
  "labelSelector": "app=web"       // OPTIONAL - filter by labels (e.g., "app=web", "env=production")
}
```

**Error Handling**:
If the MCP tool call fails:

1. **Report to user**:
   ```
   ⚠️ MCP tool 'resources_list' failed.

   📋 Fallback: Use OpenShift CLI with label selector:
   `oc get virtualmachines -A -l app=web`

   Would you like me to proceed with the CLI command?
   ```

2. **Wait for user confirmation**

3. **If approved**, execute CLI fallback:
   ```bash
   oc get virtualmachines -A -l <labelSelector> -o json
   ```

**CLI Fallback Command**:
```bash
# With label selector
oc get virtualmachines --all-namespaces -l <labelSelector> -o json
# Example:
oc get vm -A -l app=web -o json
```

**Filtering options:**

1. **By Labels** (via labelSelector parameter):
   - `"app=web"` - Single label match
   - `"app=web,env=production"` - Multiple labels (AND logic)
   - `"tier in (frontend,backend)"` - Set-based selector

2. **By Status** (post-processing after retrieval):
   - Filter returned results by status field
   - Running VMs: `status.printableStatus == "Running"`
   - Stopped VMs: `status.printableStatus == "Stopped"`
   - VMs in error state: Check status.conditions for errors

3. **By Resource Size** (post-processing after retrieval):
   - Parse instance type or resource specs from returned VMs
   - Filter based on vCPU/memory requirements

**Step 2: Display Filtered Results**

**Display filtered results with explanation:**
```markdown
## 📋 VMs with label 'app=web'

Found 3 VMs:
- web-server-01 (production) - Running
- web-server-02 (production) - Running
- web-dev-01 (development) - Running
```

## Common Issues

### "Show me all running VMs"

```markdown
## ✓ Running Virtual Machines

### production
- web-server-01 (4 vCPU, 8Gi RAM, worker-01)
- web-server-02 (4 vCPU, 8Gi RAM, worker-02)

### development
- test-vm (2 vCPU, 4Gi RAM, worker-03)

**Total**: 3 running VMs
```

### "Which VMs are in production namespace?"

```markdown
## 📋 VMs in 'production' namespace

1. **web-server-01** - Running
   - Resources: 4 vCPU, 8Gi RAM
   - Age: 15 days

2. **web-server-02** - Running
   - Resources: 4 vCPU, 8Gi RAM
   - Age: 15 days

3. **database-vm** - Stopped
   - Resources: 8 vCPU, 16Gi RAM
   - Age: 30 days
```

### "Get status of VM web-server-01"

```markdown
## Status: web-server-01

- **Namespace**: production
- **Status**: ✓ Running
- **Health**: Healthy
- **Uptime**: 12 days
- **Node**: worker-01
- **IP**: 10.129.2.45

All systems operational.
```

### "Show me VMs that are stopped"

```markdown
## ✗ Stopped Virtual Machines

### production
- database-vm (8 vCPU, 16Gi RAM)
  - Stopped 5 days ago
  - Reason: Manual shutdown

### development
- old-test-vm (2 vCPU, 4Gi RAM)
  - Stopped 20 days ago

**Total**: 2 stopped VMs

To start a VM, use:
```
"Start VM <name> in namespace <namespace>"
```
```

## Health Dashboard

When user asks for overall health, provide summary:

```markdown
## 🏥 VM Health Summary

### ✓ Healthy (8 VMs)
All VMs running as expected with no issues.

### ⚠️ Warning (2 VMs)
- **test-vm** (development)
  - High memory usage (95%)
  - Recommendation: Monitor or increase memory

- **staging-db** (staging)
  - Pod restart count: 5
  - Recommendation: Check application logs

### ❌ Critical (1 VM)
- **broken-vm** (development)
  - Status: CrashLoopBackOff
  - Recommendation: Use /vm-troubleshooter skill to diagnose

### Summary
- **Total**: 11 VMs
- **Healthy**: 73%
- **Need Attention**: 27%

**Recommendations:**
1. Investigate test-vm memory usage
2. Check staging-db logs using vm-troubleshooter
3. Fix broken-vm configuration
```

## Output Formatting Guidelines

**Use consistent status indicators:**
- ✓ Running/Healthy/Ready
- ✗ Stopped/Halted
- ⚠ Warning/Pending/Migrating
- ❌ Critical/Failed/Error

**Include key information always:**
- VM name and namespace
- Current status
- Resource allocation (vCPU, memory)
- Age/creation time
- Node placement (for running VMs)

**Organize by namespace** when showing multiple VMs:
- Groups VMs logically
- Easier to scan
- Clear separation

**Provide actionable next steps:**
- How to start stopped VMs
- How to get more details
- When to use other skills (troubleshooter, lifecycle-manager)

## Common Issues

### Issue 1: No VMs Found

**Result**: Empty list when querying VMs

**Possible Causes:**
1. No VMs exist in the cluster/namespace
2. Wrong namespace specified
3. Insufficient RBAC permissions to list VMs

**Response:**
```markdown
## No Virtual Machines Found

**Namespace**: production

No VMs were found in this namespace.

**Possible reasons:**
- No VMs have been created yet
- VMs may exist in a different namespace
- Insufficient permissions to view VMs

**Next steps:**
- Create a VM: Use /vm-create skill
- List all namespaces: "Show me all namespaces"
- Check permissions: `oc auth can-i list virtualmachines -n production`
```

### Issue 2: Permission Denied

**Error**: "Forbidden: User cannot list VirtualMachines"

**Solution:**
- Verify KUBECONFIG has appropriate RBAC permissions
- Required permissions: list/get VirtualMachine resources
- Contact cluster admin for permission grant
- Check ServiceAccount role bindings

### Issue 3: Cluster Connection Error

**Error**: "Unable to connect to cluster"

**Solution:**
1. Verify KUBECONFIG is set and valid
2. Check cluster is accessible: `oc cluster-info`
3. Verify network connectivity
4. Check if cluster credentials are expired

## Integration with Other Skills

**Before creating a VM** (vm-create):
- Use vm-inventory to check if VM name already exists
- Verify namespace exists and has capacity

**Before lifecycle operations** (vm-lifecycle-manager):
- Check current VM status using vm-inventory
- Verify VM exists before attempting start/stop/restart

**For troubleshooting**:
- Get VM overview with vm-inventory first
- Then use vm-troubleshooter (if available) for deep diagnostics

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server (https://github.com/openshift/openshift-mcp-server)

### Required MCP Tools (PRIMARY - Always try these first)
- `resources_list` (from openshift-virtualization) - List Kubernetes resources including VirtualMachines
  - Parameters: apiVersion, kind, namespace (optional), allNamespaces (optional), labelSelector (optional)
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go
- `resources_get` (from openshift-virtualization) - Get specific Kubernetes resource details
  - Parameters: apiVersion, kind, namespace, name
  - Source: https://github.com/openshift/openshift-mcp-server/blob/main/pkg/toolsets/core/resources.go

### CLI Fallback Commands (Use only if MCP tools fail)
- `oc get virtualmachines` or `oc get vm` - List VirtualMachines
- `oc get vm <name> -n <namespace>` - Get specific VM
- `oc get vm -A` - List VMs across all namespaces
- `oc get vm -n <namespace>` - List VMs in specific namespace
- `oc get vm -l <selector>` - Filter VMs by label selector

**Important**: Always attempt MCP tools first. Only use CLI commands after MCP tool failure and with user confirmation.

### Related Skills
- `vm-create` - Create VMs after checking inventory
- `vm-lifecycle-manager` - Manage VMs discovered in inventory
- `vm-troubleshooter` (planned) - Diagnose problematic VMs from inventory

### Reference Documentation
- [Troubleshooting INDEX](../../docs/troubleshooting/INDEX.md) - VM status interpretation and navigation hub for discovering error-specific troubleshooting guides (optionally consulted when displaying VM details with error states)
- [OpenShift Virtualization Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt/about_virt/about-virt.html)
- [KubeVirt VirtualMachine API](https://kubevirt.io/api-reference/)
- [Accessing VMs](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt/virtual_machines/virt-accessing-vm-consoles.html)
- [VM Status Conditions](https://kubevirt.io/user-guide/virtual_machines/vm_status_conditions/)

## Critical: Human-in-the-Loop Requirements

**Not applicable** - This skill performs read-only operations and does not modify any cluster resources. No user confirmation is required.

**Read-only operations:**
- Listing VirtualMachines across namespaces or in specific namespaces
- Retrieving VM details, status, and resource configurations
- Displaying VM health conditions and resource usage
- Filtering VMs by labels or field selectors
- Viewing VM network, storage, and node placement information

**No modifications performed:**
- ✓ Does not change VM state (start/stop/restart)
- ✓ Does not modify VM configuration
- ✓ Does not delete VMs or resources
- ✓ Does not consume cluster resources

## Security Considerations

- Read-only operations - no modifications to VMs
- Respects Kubernetes RBAC permissions
- Only shows VMs in namespaces user has access to
- KUBECONFIG credentials never exposed in output
- No sensitive VM configuration details displayed by default
- All queries audited in Kubernetes API logs

## Example Usage

**Example 1: List all VMs (using MCP tool - Table format for > 2 VMs)**

```
User: "List all VMs"

Agent: [Invokes /vm-inventory skill]
       [Attempts MCP tool: resources_list with apiVersion="kubevirt.io/v1", kind="VirtualMachine", allNamespaces=true]
       [Tool succeeds]
       [4 VMs found - using table format]

## 📋 Virtual Machines (All Namespaces)

| Namespace | VM Name | Status | Age | Resources | Node |
|-----------|---------|--------|-----|-----------|------|
| development | test-vm | ✓ Running | 5d | 2 vCPU, 4Gi | worker-03 |
| production | database-vm | ✗ Stopped | 30d | 8 vCPU, 16Gi | - |
| production | web-server-01 | ✓ Running | 15d | 4 vCPU, 8Gi | worker-01 |
| production | web-server-02 | ✓ Running | 15d | 4 vCPU, 8Gi | worker-02 |

**Summary:**
- **Total VMs**: 4
- **Running**: 3
- **Stopped**: 1
```

**Example 1b: List all VMs (MCP tool unavailable, CLI fallback)**

```
User: "List all VMs"

Agent: [Invokes /vm-inventory skill]
       [Attempts MCP tool: resources_list]
       [Tool fails - not available]

⚠️ MCP tool 'resources_list' is not available.

📋 Fallback option: Use OpenShift CLI command:
`oc get virtualmachines -A`

Would you like me to proceed with the CLI command?

User: "yes"

Agent: [Executes: oc get virtualmachines -A -o json]
       [4 VMs found - using table format]

## 📋 Virtual Machines (All Namespaces)

[Same table output as Example 1 above]
```

**Example 1c: List all VMs (List format for ≤ 2 VMs)**

```
User: "List all VMs"

Agent: [Invokes /vm-inventory skill]
       [Attempts MCP tool: resources_list with apiVersion="kubevirt.io/v1", kind="VirtualMachine", allNamespaces=true]
       [Tool succeeds]
       [2 VMs found - using list format]

## 📋 Virtual Machines (All Namespaces)

### Namespace: default
- ✓ **web-server** - Running (4 vCPU, 8Gi RAM, worker-01)

### Namespace: production
- ✓ **database-vm** - Running (8 vCPU, 16Gi RAM, worker-02)

**Summary:**
- **Total VMs**: 2
- **Running**: 2
```

**Example 2: Get details of specific VM**

```
User: "Show me details of web-server-01 in production"

Agent: [Invokes /vm-inventory skill]
       [Attempts MCP tool: resources_get with apiVersion="kubevirt.io/v1", kind="VirtualMachine", namespace="production", name="web-server-01"]
       [Tool succeeds]

## 🖥️ Virtual Machine Details

Name: web-server-01
Namespace: production
Status: ✓ Running

Configuration:
- vCPU: 4 cores
- Memory: 8Gi
- Storage: 50Gi
- OS: Fedora

Network:
- Pod IP: 10.129.2.45
- Node: worker-01

Health: All systems operational
Uptime: 12 days
```

**Example 3: Filter by namespace**

```
User: "What VMs are in the development namespace?"

Agent: [Invokes /vm-inventory skill]
       [Attempts MCP tool: resources_list with apiVersion="kubevirt.io/v1", kind="VirtualMachine", namespace="development"]
       [Tool succeeds]

## 📋 VMs in 'development' namespace

| Name | Status | Resources | Age |
|------|--------|-----------|-----|
| test-vm | Running | 2 vCPU, 4Gi | 5d |
| debug-vm | Stopped | 2 vCPU, 4Gi | 10d |

Summary: 2 VMs (1 running, 1 stopped)
```

**Example 4: No VMs found**

```
User: "List VMs in namespace test"

Agent: [Invokes /vm-inventory skill]
       [Attempts MCP tool: resources_list with apiVersion="kubevirt.io/v1", kind="VirtualMachine", namespace="test"]
       [Returns empty list]

## No Virtual Machines Found

Namespace: test

No VMs exist in this namespace.

To create a VM:
```
"Create a VM in namespace test"
```

The /vm-create skill will help you set up a new virtual machine.
```

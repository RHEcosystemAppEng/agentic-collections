---
name: vm-inventory
description: |
  List and view virtual machines across namespaces with status, resource usage, and health information. Use this skill when users request:
  - "List all VMs"
  - "Show VMs in namespace [name]"
  - "What VMs are running?"
  - "Get details of VM [name]"

  This skill provides comprehensive VM inventory and status reporting.

model: inherit
color: cyan
---

# /vm-inventory Skill

List and inspect virtual machines in OpenShift Virtualization clusters. This skill provides read-only access to VM information without making any modifications.

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- Kubernetes API access for VirtualMachine resources (via MCP server)
- Standard Kubernetes resource listing and retrieval capabilities

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
         "command": "npx",
         "args": ["-y", "@openshift/openshift-mcp-server", "--toolset", "kubevirt"],
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
- User wants to create a VM → Use `/vm-creator` skill instead
- User wants to start/stop VMs → Use `/vm-lifecycle-manager` skill instead
- User wants to modify VM configuration → Different operation (not inventory)

## Workflow

### Workflow A: List All VMs (Across All Namespaces)

**Step 1: Query VirtualMachine Resources**

Use Kubernetes API to list all VirtualMachine resources across namespaces.

**Implementation approach:**
```
oc get virtualmachines -A
# or
kubectl get vms -A
```

**Via MCP**: Use standard Kubernetes resource listing with:
- `apiVersion`: `kubevirt.io/v1`
- `kind`: `VirtualMachine`
- No namespace specified (all namespaces)

**Step 2: Format and Display Results**

Present VMs organized by namespace with key information:

```markdown
## 📋 Virtual Machines (All Namespaces)

### Namespace: production
- ✓ **web-server-01** - Running (4 vCPU, 8Gi RAM)
- ✓ **web-server-02** - Running (4 vCPU, 8Gi RAM)
- ✗ **database-vm** - Stopped (8 vCPU, 16Gi RAM)

### Namespace: development
- ✓ **test-vm** - Running (2 vCPU, 4Gi RAM)
- ⚠ **debug-vm** - Pending (2 vCPU, 4Gi RAM)

### Summary:
- **Total VMs**: 5
- **Running**: 3
- **Stopped**: 1
- **Pending**: 1
```

**Status Indicators:**
- ✓ Running/Ready
- ✗ Stopped/Halted
- ⚠ Pending/Starting/Terminating
- ❌ Failed/Error

### Workflow B: List VMs in Specific Namespace

**Step 1: Gather Namespace**

Ask user for namespace if not provided in the request.

**Step 2: Query VMs in Namespace**

Use Kubernetes API to list VirtualMachines in the specified namespace.

**Implementation:**
```
oc get virtualmachines -n <namespace>
# or
kubectl get vms -n <namespace>
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

**Step 2: Retrieve VM Resource Details**

Use Kubernetes API to get the specific VirtualMachine resource.

**Implementation:**
```
oc get virtualmachine <vm-name> -n <namespace> -o yaml
# or
kubectl get vm <vm-name> -n <namespace> -o yaml
```

**Step 3: Display Detailed Information**

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

**Filtering options:**

1. **By Status**:
   - Running VMs only
   - Stopped VMs only
   - VMs in error state

2. **By Labels**:
   ```
   User: "Show me all VMs with label app=web"

   Filter: -l app=web
   ```

3. **By Resource Size**:
   - Large VMs (> 8 vCPU)
   - Small VMs (< 4 vCPU)

**Display filtered results with explanation:**
```markdown
## 📋 VMs with label 'app=web'

Found 3 VMs:
- web-server-01 (production) - Running
- web-server-02 (production) - Running
- web-dev-01 (development) - Running
```

## Common Queries and Responses

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
- Create a VM: Use /vm-creator skill
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

**Before creating a VM** (vm-creator):
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
- `openshift-virtualization` - OpenShift MCP server with KubeVirt toolset

### Required MCP Tools
- Kubernetes API access for VirtualMachine resources
- Standard resource listing and retrieval capabilities

### Related Skills
- `vm-creator` - Create VMs after checking inventory
- `vm-lifecycle-manager` - Manage VMs discovered in inventory
- `vm-troubleshooter` (planned) - Diagnose problematic VMs from inventory

### Reference Documentation
- [OpenShift Virtualization Documentation](https://docs.openshift.com/container-platform/latest/virt/about_virt/about-virt.html)
- [KubeVirt VirtualMachine API](https://kubevirt.io/api-reference/)
- [Accessing VMs](https://docs.openshift.com/container-platform/latest/virt/virtual_machines/virt-accessing-vm-consoles.html)
- [VM Status Conditions](https://kubevirt.io/user-guide/virtual_machines/vm_status_conditions/)

## Security Considerations

- Read-only operations - no modifications to VMs
- Respects Kubernetes RBAC permissions
- Only shows VMs in namespaces user has access to
- KUBECONFIG credentials never exposed in output
- No sensitive VM configuration details displayed by default
- All queries audited in Kubernetes API logs

## Example Usage

**Example 1: List all VMs**

```
User: "List all VMs"

Agent: [Invokes /vm-inventory skill]
       [Queries all VirtualMachine resources across namespaces]

## 📋 Virtual Machines (All Namespaces)

Namespace: production
- ✓ web-server-01 - Running (4 vCPU, 8Gi)
- ✓ web-server-02 - Running (4 vCPU, 8Gi)
- ✗ database-vm - Stopped (8 vCPU, 16Gi)

Namespace: development
- ✓ test-vm - Running (2 vCPU, 4Gi)

Summary: 4 VMs (3 running, 1 stopped)
```

**Example 2: Get details of specific VM**

```
User: "Show me details of web-server-01 in production"

Agent: [Invokes /vm-inventory skill]
       [Retrieves specific VirtualMachine resource]

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
       [Queries VMs in development namespace]

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
       [Queries VMs in test namespace]

## No Virtual Machines Found

Namespace: test

No VMs exist in this namespace.

To create a VM:
```
"Create a VM in namespace test"
```

The /vm-creator skill will help you set up a new virtual machine.
```

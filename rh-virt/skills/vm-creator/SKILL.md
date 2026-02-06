---
name: vm-creator
description: |
  Create new virtual machines in OpenShift Virtualization with automatic instance type resolution and OS selection. Use this skill when users request:
  - "Create a new VM"
  - "Deploy a virtual machine with [OS]"
  - "Set up a VM in namespace [name]"
  - "Provision a [size] VM"

  This skill handles VM creation with intelligent defaults for OpenShift Virtualization.

model: inherit
color: green
---

# /vm-creator Skill

Create virtual machines in OpenShift Virtualization using the `vm_create` tool from the openshift-virtualization MCP server.

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill requires explicit user confirmation before creating VMs. You MUST:

1. **Wait for user confirmation** on all VM configuration parameters before executing `vm_create`
2. **Do NOT proceed** with VM creation until the user explicitly approves the configuration
3. **Present configuration clearly** in a table format and wait for user response
4. **Never auto-execute** VM creation without user approval - creating VMs is a destructive operation that consumes cluster resources
5. **Allow modifications** - If user wants to change parameters, update and re-confirm before proceeding

If the user says "no" or wants modifications, address their concerns before proceeding.

**Why this matters:**
- VM creation consumes cluster resources (CPU, memory, storage)
- VMs persist until explicitly deleted
- Incorrect configuration can impact cluster performance
- User should verify namespace, sizing, and other parameters

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `vm_create` (from openshift-virtualization) - Create VirtualMachine resources

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to create VirtualMachine resources
- Namespace with appropriate permissions

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
❌ Cannot execute vm-creator: MCP server 'openshift-virtualization' is not available

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
- User explicitly invokes `/vm-creator` command
- User requests creating a new virtual machine
- Deploying VMs with specific OS (Fedora, Ubuntu, RHEL, CentOS, Debian)
- Setting up VMs with custom sizing (small, medium, large)
- Provisioning VMs with specific storage requirements

**User phrases that trigger this skill:**
- "Create a Fedora VM in namespace vms"
- "Deploy a medium Ubuntu VM with 100Gi disk"
- "Set up a RHEL VM called database-01"
- "/vm-creator" (explicit command)

**Do NOT use this skill when:**
- User wants to start/stop existing VMs → Use `/vm-lifecycle-manager` skill instead
- User wants to list VMs → Use `/vm-inventory` skill instead
- User only wants information about VMs (not creation) → Use `/vm-inventory` skill instead

## Workflow

### Step 1: Gather VM Requirements and Confirm Configuration

**Collect information from user**, then present for confirmation before proceeding.

**Required Parameters:**
1. **VM Name** - Name for the virtual machine
   - Example: "web-server", "database-01", "test-vm"

2. **Namespace** - OpenShift namespace where VM will be created
   - Example: "vms", "production", "dev-environment"

**Optional Parameters (with defaults):**
3. **Operating System** (`workload`) - Default: `"fedora"`
   - Supported: `fedora`, `ubuntu`, `centos`, `centos-stream`, `debian`, `rhel`, `opensuse`, `opensuse-tumbleweed`, `opensuse-leap`
   - Can also accept full container disk image URLs

4. **Size** (`size`) - VM sizing hint
   - Options: `small`, `medium`, `large`, `xlarge`
   - If not specified, MCP server uses default instance type

5. **Storage** (`storage`) - Default: `"30Gi"`
   - Root disk size: `"30Gi"`, `"50Gi"`, `"100Gi"`, etc.

6. **Autostart** (`autostart`) - Default: `false`
   - `true`: VM starts automatically after creation
   - `false`: VM created in halted state

**After gathering parameters, present configuration for confirmation:**

```markdown
## Virtual Machine Configuration

**Please review and confirm the VM configuration:**

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `web-server` | [from user input] |
| Namespace | `vms` | [from user input] |
| Operating System | `fedora` | [default / user specified] |
| Size | `medium` | [user specified / omitted for default] |
| Storage | `50Gi` | [user specified / default: 30Gi] |
| Autostart | `no` | [default / user specified] |

**This will create a new VirtualMachine resource consuming cluster resources.**

Confirm these settings or tell me what to change.
- yes - Proceed with VM creation
- no - Cancel operation
- modify - Change specific parameters
```

**WAIT for user confirmation before proceeding to Step 2.** Do NOT continue until user explicitly confirms with "yes" or provides modifications.

### Step 2: Create the Virtual Machine

**ONLY PROCEED AFTER USER CONFIRMATION IN STEP 1.**

**Use the openshift-virtualization MCP tool:**

Call `vm_create` with the confirmed parameters from Step 1.

**MCP Tool**: `vm_create` (from openshift-virtualization)

**Parameters** (based on user input from Step 1):

```json
{
  "namespace": "<namespace>",           // REQUIRED
  "name": "<vm-name>",                  // REQUIRED
  "workload": "<os-choice>",            // OPTIONAL (default: "fedora")
  "size": "<small|medium|large>",       // OPTIONAL
  "storage": "<disk-size>",             // OPTIONAL (default: "30Gi")
  "autostart": <true|false>             // OPTIONAL (default: false)
}
```

**Example tool invocation:**
```json
vm_create({
  "namespace": "vms",
  "name": "web-server",
  "workload": "fedora",
  "size": "medium",
  "storage": "50Gi",
  "autostart": false
})
```

**Expected Output:**
- Success: VirtualMachine resource created
- Failure: Error message with reason (permissions, resources, etc.)

**Error Handling:**
- If namespace doesn't exist: Report error, suggest creating namespace first
- If insufficient resources: Report error with resource requirements
- If permission denied: Report RBAC error, suggest checking ServiceAccount permissions

### Step 3: Verify VM Status and Diagnose Issues

**CRITICAL**: After VM creation, verify it can be scheduled successfully.

**Verification Steps**:

1. **Wait 5-10 seconds** for initial scheduling attempt

2. **Check VM status** using Kubernetes API:

**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
- `apiVersion`: "kubevirt.io/v1"
- `kind`: "VirtualMachine"
- `name`: "<vm-name>" (from Step 1)
- `namespace`: "<namespace>" (from Step 1)

Extract `status.printableStatus` from the response.

**Status Interpretation**:
- `Stopped` / `Halted` → Normal (VM created successfully, not started)
- `Running` → Normal (if autostart=true)
- `Provisioning` → Wait 5 seconds and check again
- `ErrorUnschedulable` → **Proceed to diagnostic workflow below**
- `ErrorDataVolumeNotReady` → Storage issue, proceed to diagnostic workflow

**Diagnostic Workflow (when ErrorUnschedulable detected)**:

#### 3a. Consult Troubleshooting Documentation

**Document Consultation** (REQUIRED):
1. **Action**: Read [troubleshooting.md](../../docs/troubleshooting.md) using the Read tool to understand ErrorUnschedulable causes
2. **Output to user**: "I detected the VM is ErrorUnschedulable. I consulted [troubleshooting.md](../../docs/troubleshooting.md) to diagnose the issue."

#### 3b. Gather Diagnostic Information

**Execute diagnostic commands** using MCP tools or bash:

```bash
# Get VM events to see scheduling failures
oc describe vm <vm-name> -n <namespace> | grep -A 10 "Events:"

# Check node taints
oc get nodes -o json | jq '.items[] | select(.spec.taints != null) | {name: .metadata.name, taints: .spec.taints}'
```

**Parse results** to identify root cause:
- Events contain "taints that the pod didn't tolerate" → **Taints/Tolerations issue**
- Events contain "Insufficient cpu" or "Insufficient memory" → **Resource constraints**
- Events contain "no nodes available" → **No suitable nodes**

#### 3c. Present Diagnosis to User

**Report findings in clear format**:

```markdown
## ⚠️ VM Scheduling Issue Detected

**VM Name**: `<vm-name>`
**Namespace**: `<namespace>`
**Status**: ErrorUnschedulable

### Diagnosis

**Root Cause**: Node taints prevent VM scheduling

**Details**:
- Found X nodes with taint: `virtualization=true:NoSchedule`
- VM spec does not include matching tolerations
- This prevents the VM from being scheduled on virtualization-dedicated nodes

**Affected Nodes**:
- <node-1> (taint: <taint-spec>)
- <node-2> (taint: <taint-spec>)

### Recommended Solution

I can apply a workaround to add the required tolerations to your VM.

**Workaround**: Patch the VirtualMachine to add tolerations

**Command that will be executed**:
```bash
oc patch vm <vm-name> -n <namespace> --type=merge -p '
spec:
  template:
    spec:
      tolerations:
      - key: "<detected-taint-key>"
        operator: "Equal"
        value: "<detected-taint-value>"
        effect: "<detected-taint-effect>"
'
```

**Impact**:
- ✓ VM will be able to schedule on virtualization nodes
- ✓ VM configuration will be updated
- ⚠️ This is a manual workaround (MCP tool doesn't support tolerations yet)

**Alternative Options**:
1. Accept workaround and I'll apply the patch now
2. Manually apply the patch yourself
3. Contact cluster admin to remove node taints
4. Cancel and delete the VM

⚠️ **This is a temporary limitation**: The openshift-virtualization MCP server doesn't yet support tolerations parameter in vm_create. Consider filing an issue at: https://github.com/openshift/openshift-mcp-server/issues
```

#### 3d. Wait for User Decision (Human-in-the-Loop)

**CRITICAL**: Do NOT execute the workaround without explicit user confirmation.

**Prompt user**:
```
How would you like to proceed?
- "apply workaround" - I'll patch the VM with tolerations
- "manual" - I'll provide instructions for you to apply manually
- "cancel" - Delete the VM and abort creation
- "ignore" - Keep the VM as-is (will remain unschedulable)

Please respond with your choice.
```

#### 3e. Execute Workaround (ONLY if user confirms)

**ONLY if user responds with "apply workaround" or similar confirmation:**

**Execute patch command**:
```bash
oc patch vm <vm-name> -n <namespace> --type=merge -p '
spec:
  template:
    spec:
      tolerations:
      - key: "<detected-taint-key>"
        operator: "Equal"
        value: "<detected-taint-value>"
        effect: "<detected-taint-effect>"
'
```

**Verify patch success**:
```bash
# Check if tolerations were added
oc get vm <vm-name> -n <namespace> -o jsonpath='{.spec.template.spec.tolerations}'

# Wait 5 seconds and check status again
sleep 5
oc get vm <vm-name> -n <namespace> -o jsonpath='{.status.printableStatus}'
```

**Report result**:
```markdown
## ✓ Workaround Applied Successfully

**VM Name**: `<vm-name>`
**Namespace**: `<namespace>`
**Action**: Added tolerations for taint `<taint-spec>`

**New Status**: <new-status> (VM can now be scheduled)

**Next Steps**:
To start the VM:
```
"Start VM <vm-name> in namespace <namespace>"
```

**Note**: This workaround was needed because the MCP tool doesn't yet support tolerations. Future VMs in this cluster will need the same fix until the tool is enhanced.
```

### Step 4: Report Creation Status

**Present results to user in a clear, actionable format:**

**On Success:**

```markdown
## ✓ Virtual Machine Created Successfully

**VM Details:**
- **Name**: `web-server`
- **Namespace**: `vms`
- **Operating System**: Fedora
- **Size**: medium
- **Storage**: 50Gi
- **Status**: Halted (VM is created but not running)

**Next Steps:**

To start the VM:
```
"Start VM web-server in namespace vms"
```

To check VM status:
```
"Show status of VM web-server"
```

To view full VM details:
```
"Get details of web-server VM"
```

**Note**: The VM is created in a halted state. Use the `/vm-lifecycle-manager` skill to start it.
```

**On Failure:**

```markdown
## ❌ Failed to Create Virtual Machine

**Error**: <error-message-from-tool>

**Common Causes:**
- **Namespace doesn't exist** - Create the namespace first: `oc create namespace <name>`
- **Insufficient RBAC permissions** - ServiceAccount lacks permission to create VirtualMachines
- **Cluster resource constraints** - Insufficient CPU, memory, or storage available
- **Invalid parameter values** - Check OS name, size specification, or storage format
- **OpenShift Virtualization not installed** - Operator must be installed on cluster

**Troubleshooting:**
1. Verify namespace exists: `oc get namespace <namespace>`
2. Check permissions: `oc auth can-i create virtualmachines -n <namespace>`
3. View cluster capacity: `oc describe nodes`
4. Verify operator installed: `oc get csv -n openshift-cnv`

Would you like help troubleshooting this error?
```

## Advanced Usage

### Custom Container Disk Images

Users can provide full container image URLs for the `workload` parameter:

```
User: "Create a VM using quay.io/containerdisks/fedora:latest"

vm_create({
  "namespace": "vms",
  "name": "custom-vm",
  "workload": "quay.io/containerdisks/fedora:latest"
})
```

### Secondary Networks

Attach additional networks using the `networks` parameter (requires NetworkAttachmentDefinition resources):

```json
vm_create({
  "namespace": "vms",
  "name": "network-vm",
  "workload": "fedora",
  "networks": ["vlan-network", "storage-network"]
})
```

Or with custom interface names:

```json
vm_create({
  "namespace": "vms",
  "name": "network-vm",
  "workload": "fedora",
  "networks": [
    {"name": "eth1", "networkName": "vlan-network"}
  ]
})
```

### Performance Tuning

Use the `performance` parameter to select instance type family:

```json
vm_create({
  "namespace": "vms",
  "name": "compute-vm",
  "workload": "fedora",
  "performance": "c1",  // compute-optimized
  "size": "large"
})
```

Options:
- `"u1"` - general-purpose (default)
- `"o1"` - overcommitted
- `"c1"` - compute-optimized
- `"m1"` - memory-optimized

### Explicit Instance Type

Specify exact instance type instead of using `size`:

```json
vm_create({
  "namespace": "vms",
  "name": "precise-vm",
  "workload": "fedora",
  "instancetype": "u1.large"
})
```

## Common Issues

### Issue 1: Namespace Not Found

**Error**: "Namespace 'xyz' not found"

**Solution:**
1. List available namespaces: Suggest using `oc get namespaces` or `kubectl get ns`
2. Create namespace if needed: `oc create namespace <name>`
3. Verify ServiceAccount has access to the namespace

### Issue 2: Insufficient Permissions

**Error**: "Forbidden: User cannot create VirtualMachines in namespace 'xyz'"

**Solution:**
- Verify KUBECONFIG has appropriate RBAC permissions
- Required permissions: create VirtualMachine resources
- Contact cluster admin for permission grant
- Check ServiceAccount role bindings

### Issue 3: Resource Constraints

**Error**: "Insufficient resources to schedule VM"

**Solution:**
1. Check cluster capacity: CPU, memory available
2. Try smaller `size` (e.g., change "large" to "medium")
3. Reduce `storage` size if possible
4. Contact cluster admin to scale nodes

### Issue 4: OpenShift Virtualization Not Installed

**Error**: "VirtualMachine CRD not found"

**Solution:**
- OpenShift Virtualization operator must be installed
- Verify: `oc get csv -n openshift-cnv`
- Contact cluster admin to install operator

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with KubeVirt toolset

### Required MCP Tools
- `vm_create` (from openshift-virtualization) - Create VirtualMachine resources

### Related Skills
- `vm-lifecycle-manager` - Start VMs after creation
- `vm-inventory` - List and view created VMs

### Reference Documentation
- [troubleshooting.md](../../docs/troubleshooting.md) - VM error diagnosis and workarounds
- [OpenShift Virtualization Documentation](https://docs.openshift.com/container-platform/latest/virt/about_virt/about-virt.html)
- [KubeVirt VirtualMachine API](https://kubevirt.io/api-reference/)
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server)

## Security Considerations

- VMs are created in user-specified namespace (namespace isolation)
- Storage uses cluster-configured storage classes
- Network access controlled by NetworkPolicies
- KUBECONFIG credentials never exposed in output
- All operations audited in Kubernetes API logs
- ServiceAccount permissions limit VM creation scope

## Example Usage

**Example 1: Simple VM creation with defaults**

```
User: "Create a Fedora VM called web-01 in namespace apps"

Agent: [Invokes /vm-creator skill]

## Virtual Machine Configuration

Please review and confirm the VM configuration:

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `web-01` | from user input |
| Namespace | `apps` | from user input |
| Operating System | `fedora` | default |
| Size | (default) | MCP server will select |
| Storage | `30Gi` | default |
| Autostart | `no` | default |

This will create a new VirtualMachine resource consuming cluster resources.

Confirm these settings or tell me what to change.

User: "yes"

Agent: [Calls vm_create with namespace="apps", name="web-01", workload="fedora"]

## ✓ Virtual Machine Created Successfully

VM Details:
- Name: `web-01`
- Namespace: `apps`
- OS: Fedora
- Status: Halted

Next Steps: "Start VM web-01 in namespace apps"
```

**Example 2: Custom configuration with modifications**

```
User: "Deploy a large RHEL VM with 100Gi storage called db-server in production namespace"

Agent: [Invokes /vm-creator skill]

## Virtual Machine Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `db-server` | from user input |
| Namespace | `production` | from user input |
| Operating System | `rhel` | from user input |
| Size | `large` | from user input |
| Storage | `100Gi` | from user input |
| Autostart | `no` | default |

Confirm these settings or tell me what to change.

User: "Actually, autostart it"

Agent: [Updates configuration]

## Updated Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Autostart | `yes` | updated per user request |

Confirm?

User: "yes"

Agent: [Calls vm_create with all parameters including autostart=true]

## ✓ Virtual Machine Created and Started

VM Details:
- Name: `db-server`
- Namespace: `production`
- OS: RHEL
- Size: large
- Storage: 100Gi
- Status: Running (autostarted)
```

**Example 3: User cancels after reviewing configuration**

```
User: "Create a VM named test in namespace dev"

Agent: [Invokes /vm-creator skill]

## Virtual Machine Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `test` | from user input |
| Namespace | `dev` | from user input |
| Operating System | `fedora` | default |
| Storage | `30Gi` | default |

Confirm these settings or tell me what to change.

User: "no, cancel"

Agent: VM creation cancelled. No resources were created.
```

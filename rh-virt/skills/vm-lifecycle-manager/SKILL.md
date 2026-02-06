---
name: vm-lifecycle-manager
description: |
  Manage virtual machine lifecycle operations including start, stop, and restart. Use this skill when users request:
  - "Start VM [name]"
  - "Stop the virtual machine [name]"
  - "Restart VM [name]"
  - "Power on/off VM [name]"

  This skill handles VM state transitions safely with user confirmation for each action.

model: inherit
color: blue
---

# /vm-lifecycle-manager Skill

Control virtual machine power state and lifecycle operations in OpenShift Virtualization using the `vm_lifecycle` tool from the openshift-virtualization MCP server.

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill requires explicit user confirmation before executing lifecycle actions. You MUST:

1. **Wait for user confirmation** on the specific action (start/stop/restart) before executing `vm_lifecycle`
2. **Do NOT proceed** with the lifecycle operation until the user explicitly approves
3. **Present the action clearly** with VM name, namespace, and intended state change
4. **Never auto-execute** VM lifecycle changes without user approval - these operations impact running services
5. **Warn about consequences** - stopping VMs interrupts services, starting consumes resources, restarting causes brief downtime

If the user says "no" or wants to reconsider, do not proceed with the operation.

**Why this matters:**
- **Start**: Consumes cluster resources (CPU, memory), affects resource availability for other VMs
- **Stop**: Interrupts running services and applications, may cause service downtime
- **Restart**: Causes brief service interruption, running processes will be terminated
- User should verify they're targeting the correct VM and understand the impact

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `vm_lifecycle` (from openshift-virtualization) - Manage VM power state

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to update VirtualMachine resources
- Target VM must already exist

### Prerequisite Verification

**Before executing, verify MCP server availability:**

1. **Check MCP Server Configuration**
   - Verify `openshift-virtualization` exists in `.mcp.json`
   - If missing → Report to user with setup instructions

2. **Check Environment Variables**
   - Verify `KUBECONFIG` is set (check presence only, never expose value)
   - If missing → Report to user

3. **Verify VM Exists** (optional quick check)
   - Confirm target VM exists in specified namespace
   - If VM not found → Report error to user

**Human Notification Protocol:**

When prerequisites fail:

```
❌ Cannot execute vm-lifecycle-manager: MCP server 'openshift-virtualization' is not available

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
- User explicitly invokes `/vm-lifecycle-manager` command
- User requests starting a stopped/halted VM
- User requests stopping a running VM
- User requests restarting a VM (stop + start)
- User wants to change VM power state

**User phrases that trigger this skill:**
- "Start VM web-server in namespace vms"
- "Stop the database VM"
- "Restart test-vm"
- "Power on the VM called api-server"
- "/vm-lifecycle-manager" (explicit command)

**Do NOT use this skill when:**
- User wants to create a new VM → Use `/vm-creator` skill instead
- User wants to list VMs → Use `/vm-inventory` skill instead
- User wants to delete a VM → Different operation (not lifecycle management)

## Workflow

### Step 1: Gather Lifecycle Operation Details and Confirm

**Collect information from user**, then present for confirmation before proceeding.

**Required Parameters:**
1. **VM Name** - Name of the virtual machine
   - Example: "web-server", "database-01", "test-vm"

2. **Namespace** - OpenShift namespace where VM exists
   - Example: "vms", "production", "dev-environment"

3. **Action** - Lifecycle operation to perform
   - `start` - Power on the VM (sets runStrategy: Always)
   - `stop` - Power off the VM (sets runStrategy: Halted)
   - `restart` - Stop then start the VM (brief service interruption)

**After gathering parameters, present operation for confirmation:**

```markdown
## VM Lifecycle Operation

**Please review and confirm the lifecycle operation:**

| Parameter | Value | Impact |
|-----------|-------|--------|
| VM Name | `web-server` | [from user input] |
| Namespace | `vms` | [from user input] |
| Action | `start` | VM will power on and consume cluster resources |
| Current Status | `Stopped` | [if known] |
| New Status | `Running` | After successful start |

**Impact of this operation:**
- **start**: VM will consume CPU and memory resources, applications will start
- **stop**: VM will shut down gracefully, running processes will terminate
- **restart**: VM will stop and start again, causing brief service interruption (~1-2 minutes)

**This operation will change the VM power state.**

Confirm this action or tell me what to change.
- yes - Proceed with lifecycle operation
- no - Cancel operation
- modify - Change parameters
```

**WAIT for user confirmation before proceeding to Step 2.** Do NOT continue until user explicitly confirms with "yes".

### Step 2: Execute the Lifecycle Operation

**ONLY PROCEED AFTER USER CONFIRMATION IN STEP 1.**

**Use the openshift-virtualization MCP tool:**

Call `vm_lifecycle` with the confirmed parameters from Step 1.

**MCP Tool**: `vm_lifecycle` (from openshift-virtualization)

**Parameters** (based on user input from Step 1):

```json
{
  "namespace": "<namespace>",  // REQUIRED
  "name": "<vm-name>",         // REQUIRED
  "action": "<start|stop|restart>"  // REQUIRED
}
```

**Example tool invocation:**
```json
vm_lifecycle({
  "namespace": "vms",
  "name": "web-server",
  "action": "start"
})
```

**Expected Output:**
- Success: VirtualMachine runStrategy updated, state transition initiated
- Failure: Error message with reason (VM not found, permissions, already in desired state, etc.)

**Error Handling:**
- If VM not found: Report error, suggest checking VM name and namespace
- If permission denied: Report RBAC error, suggest checking ServiceAccount permissions
- If VM already in desired state: Inform user (e.g., "VM is already running")
- If state transition fails: Report error with details

### Step 3: Report Operation Status

**Present results to user in a clear, actionable format:**

**On Success (start):**

```markdown
## ✓ Virtual Machine Started Successfully

**VM Details:**
- **Name**: `web-server`
- **Namespace**: `vms`
- **Action**: start
- **Previous Status**: Stopped
- **Current Status**: Running
- **RunStrategy**: Always (VM will auto-restart on crash)

**Next Steps:**

To check VM status:
```
"Show status of VM web-server"
```

To view VM details:
```
"Get details of web-server VM"
```

To access the VM:
- Use virtctl console or SSH (depending on VM configuration)

**Note**: The VM is now consuming cluster resources (CPU, memory).
```

**On Success (stop):**

```markdown
## ✓ Virtual Machine Stopped Successfully

**VM Details:**
- **Name**: `database-vm`
- **Namespace**: `vms`
- **Action**: stop
- **Previous Status**: Running
- **Current Status**: Stopped
- **RunStrategy**: Halted (VM will remain off until started)

**Impact:**
- VM is no longer consuming cluster resources
- All running processes have been terminated
- VM state preserved (can be started again)

**Next Steps:**

To start the VM again:
```
"Start VM database-vm in namespace vms"
```

**Note**: The VM will remain stopped until explicitly started.
```

**On Success (restart):**

```markdown
## ✓ Virtual Machine Restarted Successfully

**VM Details:**
- **Name**: `test-vm`
- **Namespace**: `vms`
- **Action**: restart
- **Status**: Running (after stop + start)
- **RunStrategy**: Always

**What happened:**
1. VM was gracefully stopped
2. VM was started again
3. Applications inside the VM are now restarting

**Expected behavior:**
- Brief service interruption occurred (~1-2 minutes)
- VM is now running with fresh state
- Applications may take additional time to fully initialize

**Note**: Monitor application logs to confirm services are healthy after restart.
```

**On Failure:**

```markdown
## ❌ Failed to Execute Lifecycle Operation

**Error**: <error-message-from-tool>

**Common Causes:**
- **VM not found** - Check VM name and namespace are correct
- **Insufficient RBAC permissions** - ServiceAccount lacks permission to update VirtualMachines
- **VM already in desired state** - VM is already running/stopped
- **VM in transition** - VM is currently starting/stopping, wait for completion
- **Resource constraints** (for start) - Insufficient cluster resources to start VM

**Troubleshooting:**
1. Verify VM exists: `oc get vm <vm-name> -n <namespace>`
2. Check permissions: `oc auth can-i update virtualmachines -n <namespace>`
3. View VM status: Use /vm-inventory skill to check current state
4. Check cluster capacity: `oc describe nodes` (for start operations)

Would you like help troubleshooting this error?
```

## Common Issues

### Issue 1: VM Not Found

**Error**: "VirtualMachine 'xyz' not found in namespace 'abc'"

**Solution:**
1. Verify VM name spelling is correct
2. Check namespace is correct
3. List VMs in namespace: Use `/vm-inventory` skill
4. VM may have been deleted

### Issue 2: VM Already in Desired State

**Warning**: "VM is already running" (when attempting start)

**Solution:**
- This is not an error - VM is already in the desired state
- No action needed
- If you intended to restart, use `action="restart"` instead
- Inform user VM is already running

### Issue 3: Permission Denied

**Error**: "Forbidden: User cannot update VirtualMachines in namespace 'xyz'"

**Solution:**
- Verify KUBECONFIG has appropriate RBAC permissions
- Required permissions: update VirtualMachine resources
- Contact cluster admin for permission grant
- Check ServiceAccount role bindings

### Issue 4: VM Stuck in Transitioning State

**Error**: "VM is stuck in 'Terminating' or 'Starting' state"

**Solution:**
1. Wait 30-60 seconds for state transition to complete
2. Check VM events for errors: `oc describe vm <name> -n <namespace>`
3. Use `/vm-troubleshooter` skill (if available) to diagnose
4. Check virt-launcher pod status
5. May require cluster admin intervention

### Issue 5: Insufficient Resources (Start Operation)

**Error**: "Insufficient CPU/memory to start VM"

**Solution:**
1. Check cluster resource availability
2. Stop other VMs first to free resources
3. Consider scaling cluster nodes
4. Resize VM to smaller instance type (using `/vm-creator` to recreate)

## Understanding RunStrategy

When you execute lifecycle actions, the VM's `runStrategy` changes:

| Action | RunStrategy After | Behavior |
|--------|------------------|----------|
| start | Always | VM runs and auto-restarts on crash |
| stop | Halted | VM stops and stays stopped |
| restart | Always | VM stops, then starts, then auto-restarts on crash |

**RunStrategy Values:**
- `Always` - VM should always be running (restarts automatically on crash)
- `Halted` - VM should be stopped (stays off)
- `Manual` - VM controlled manually (not modified by this skill)
- `RerunOnFailure` - Restart only on failure (not used by this skill)

**Note**: This skill sets `Always` for start/restart and `Halted` for stop.

## Advanced Usage

### Batch Operations

Execute lifecycle operations on multiple VMs:

```
User: "Stop VMs web-01, web-02, web-03 in namespace production"

For each VM:
1. Gather parameters (namespace, name, action=stop)
2. Confirm with user (show all VMs to be stopped)
3. Execute vm_lifecycle for each VM sequentially
4. Report results for each
```

**Confirmation format for batch:**
```markdown
## Batch Lifecycle Operation

Stopping 3 VMs in namespace 'production':
- web-01
- web-02
- web-03

**Impact**: All 3 VMs will shut down, services will be interrupted.

Proceed? (yes/no)
```

### Conditional Operations

Start VM only if currently stopped:

```
User: "Start web-server if it's not running"

1. Check current status (using vm-inventory or describe)
2. If stopped: proceed with start operation
3. If running: inform user "VM is already running"
4. If unknown: attempt start (will fail gracefully if already running)
```

## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with KubeVirt toolset

### Required MCP Tools
- `vm_lifecycle` (from openshift-virtualization) - Manage VM power state (start/stop/restart)

### Related Skills
- `vm-creator` - Create VMs before managing their lifecycle
- `vm-inventory` - Check current VM status before lifecycle operations
- `vm-troubleshooter` (planned) - Diagnose VM startup/shutdown issues

### Reference Documentation
- [OpenShift Virtualization Documentation](https://docs.openshift.com/container-platform/latest/virt/about_virt/about-virt.html)
- [KubeVirt VirtualMachine Lifecycle](https://kubevirt.io/user-guide/virtual_machines/lifecycle/)
- [RunStrategy Documentation](https://kubevirt.io/user-guide/virtual_machines/run_strategies/)
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server)

## Security Considerations

- VM lifecycle changes require RBAC permissions (update VirtualMachine resources)
- Stop operations gracefully shut down VMs (no data loss)
- Start operations consume cluster resources (quota limits apply)
- All operations audited in Kubernetes API logs
- KUBECONFIG credentials never exposed in output
- ServiceAccount permissions limit which VMs can be controlled

## Example Usage

**Example 1: Start a stopped VM**

```
User: "Start VM web-server in namespace vms"

Agent: [Invokes /vm-lifecycle-manager skill]

## VM Lifecycle Operation

Please review and confirm the lifecycle operation:

| Parameter | Value | Impact |
|-----------|-------|--------|
| VM Name | `web-server` | from user input |
| Namespace | `vms` | from user input |
| Action | `start` | VM will power on and consume cluster resources |

This operation will change the VM power state.

Confirm this action or tell me what to change.

User: "yes"

Agent: [Calls vm_lifecycle with namespace="vms", name="web-server", action="start"]

## ✓ Virtual Machine Started Successfully

VM Details:
- Name: `web-server`
- Namespace: `vms`
- Action: start
- Current Status: Running
- RunStrategy: Always

The VM is now running and consuming cluster resources.
```

**Example 2: Stop a running VM with user reconsidering**

```
User: "Stop the database VM in production namespace"

Agent: [Invokes /vm-lifecycle-manager skill]

## VM Lifecycle Operation

| Parameter | Value | Impact |
|-----------|-------|--------|
| VM Name | `database` | from user input |
| Namespace | `production` | from user input |
| Action | `stop` | VM will shut down gracefully, running processes will terminate |

**Impact**: VM will shut down, database services will stop, causing service interruption.

Confirm this action or tell me what to change.

User: "wait, no, don't stop it"

Agent: Operation cancelled. VM 'database' in namespace 'production' remains running.
```

**Example 3: Restart a VM**

```
User: "Restart test-vm in namespace dev"

Agent: [Invokes /vm-lifecycle-manager skill]

## VM Lifecycle Operation

| Parameter | Value | Impact |
|-----------|-------|--------|
| VM Name | `test-vm` | from user input |
| Namespace | `dev` | from user input |
| Action | `restart` | VM will stop and start again, causing brief service interruption |

**Impact**: Brief service interruption (~1-2 minutes) while VM restarts.

Confirm this action?

User: "yes"

Agent: [Calls vm_lifecycle with namespace="dev", name="test-vm", action="restart"]

## ✓ Virtual Machine Restarted Successfully

VM Details:
- Name: `test-vm`
- Namespace: `dev`
- Action: restart
- Status: Running (after stop + start)

Brief service interruption occurred. Monitor application logs to confirm services are healthy.
```

**Example 4: VM already in desired state**

```
User: "Start web-server in namespace vms"

Agent: [Invokes /vm-lifecycle-manager skill]
       [Calls vm_lifecycle with action="start"]

## ℹ️ VM Already Running

**VM Details:**
- **Name**: `web-server`
- **Namespace**: `vms`
- **Current Status**: Running

**Result**: No action taken - VM is already in the desired state.

If you intended to restart the VM, use:
```
"Restart VM web-server in namespace vms"
```
```

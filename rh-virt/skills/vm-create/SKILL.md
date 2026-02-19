---
name: vm-create
description: |
  Create new virtual machines in OpenShift Virtualization with automatic instance type resolution and OS selection. Use this skill when users request:
  - "Create a new VM"
  - "Deploy a virtual machine with [OS]"
  - "Set up a VM in namespace [name]"
  - "Provision a [size] VM"

  This skill handles VM creation with intelligent defaults for OpenShift Virtualization.

  NOT for managing existing VMs (use vm-lifecycle-manager or vm-delete instead).

model: inherit
color: green
---

# /vm-create Skill

Create virtual machines in OpenShift Virtualization using the `vm_create` tool from the openshift-virtualization MCP server.

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
❌ Cannot execute vm-create: MCP server 'openshift-virtualization' is not available

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
- User explicitly invokes `/vm-create` command
- User requests creating a new virtual machine
- Deploying VMs with specific OS (Fedora, Ubuntu, RHEL, CentOS, Debian)
- Setting up VMs with custom sizing (small, medium, large)
- Provisioning VMs with specific storage requirements

**User phrases that trigger this skill:**
- "Create a Fedora VM in namespace vms"
- "Deploy a medium Ubuntu VM with 100Gi disk"
- "Set up a RHEL VM called database-01"
- "/vm-create" (explicit command)

**Do NOT use this skill when:**
- User wants to start/stop existing VMs → Use `/vm-lifecycle-manager` skill instead
- User wants to list VMs → Use `/vm-inventory` skill instead
- User only wants information about VMs (not creation) → Use `/vm-inventory` skill instead

## Workflow

### Step 1: Gather VM Requirements and Confirm Configuration

**CRITICAL**: When user does NOT explicitly specify all VM parameters, you MUST use the AskUserQuestion tool to present an interactive menu.

#### Step 1a: Determine What Information Is Missing

**First: Detect Current Namespace from KUBECONFIG Context**

Before asking for namespace, detect the current context:

**Note**: There is no MCP tool equivalent for detecting the current kubeconfig context namespace. This is one of the rare cases where kubectl CLI is acceptable:

```bash
# Get current namespace from kubeconfig context
kubectl config view --minify -o jsonpath='{..namespace}' 2>/dev/null || echo "default"
```

**Store this as the default namespace** to use in the interactive menu.

**VM Name Validation Rules:**
- Lowercase alphanumeric characters or hyphens only
- Must start with a letter
- Must end with alphanumeric character
- Maximum 63 characters
- Must be unique within the namespace

**Check if user explicitly provided:**
1. **VM Name** - Required, always ask if not provided. Validate against rules above.
2. **Namespace** - Required, always ask if not provided. Use detected namespace as default.
3. **Operating System** - If not specified, use interactive menu (default: `fedora`)
4. **Size** - If not specified, use interactive menu (default: `medium`)
5. **Storage** - If not specified, use interactive menu (default: `30Gi`)
6. **Storage Class** - If not specified, use interactive menu (default: cluster default)
7. **Performance Profile** - If not specified, use interactive menu (default: `u1` general-purpose)
8. **Autostart** - If not specified, use interactive menu (default: `false`)

#### Step 1b: Gather Missing Parameters via Interactive Menu

**BEFORE presenting the menu, gather cluster information using MCP tools:**

1. **Detect current namespace** (if not provided by user):

   **Note**: No MCP equivalent exists - use kubectl:
   ```bash
   kubectl config view --minify -o jsonpath='{..namespace}' 2>/dev/null || echo "default"
   ```

2. **Get available namespaces**:

   **Use MCP Tool**: `namespaces_list` (from openshift-virtualization)

   **Parameters**: None

   This returns a list of all namespaces in the cluster.

3. **Get available StorageClasses and identify default**:

   **Use MCP Tool**: `resources_list` (from openshift-virtualization)

   **Parameters**:
   - `apiVersion`: "storage.k8s.io/v1"
   - `kind`: "StorageClass"

   This returns all StorageClass resources with full details including annotations and specifications.

4. **Analyze StorageClasses** for the menu:
   - **Performance**: Check `volumeBindingMode` (Immediate = faster provisioning, WaitForFirstConsumer = delayed)
   - **Live Migration Support**: Check access modes - RWX (ReadWriteMany) supports live migration, RWO (ReadWriteOnce) does not
   - Extract from MCP tool response:
     - `.metadata.annotations["storageclass.kubernetes.io/is-default-class"]` = "true" for default
     - `.volumeBindingMode` for performance
     - `.provisioner` for hints (rbd/cephfs = likely RWX support)

**If ANY parameters are missing, use AskUserQuestion tool with the following structure:**

**Use the AskUserQuestion tool** to present an interactive menu for missing configuration parameters:

```json
{
  "questions": [
    {
      "question": "What is the name for your new virtual machine?",
      "header": "VM Name",
      "multiSelect": false,
      "options": [
        {
          "label": "Enter custom name",
          "description": "Provide VM name (lowercase, alphanumeric+hyphens, start with letter, max 63 chars)"
        }
      ]
    },
    {
      "question": "Which namespace should this VM be created in?",
      "header": "Namespace",
      "multiSelect": false,
      "options": [
        {
          "label": "<detected-current-namespace> (Current)",
          "description": "Your current namespace from kubeconfig context"
        },
        {
          "label": "Other namespace",
          "description": "Specify a different namespace from: <list-of-namespaces>"
        }
      ]
    },
    {
      "question": "Which operating system should the VM run?",
      "header": "OS",
      "multiSelect": false,
      "options": [
        {
          "label": "Fedora (Recommended)",
          "description": "Latest Fedora Linux distribution - general purpose"
        },
        {
          "label": "Ubuntu",
          "description": "Ubuntu Linux distribution - popular for web services"
        },
        {
          "label": "RHEL",
          "description": "Red Hat Enterprise Linux - enterprise-grade stability"
        },
        {
          "label": "CentOS Stream",
          "description": "CentOS Stream - upstream for RHEL"
        },
        {
          "label": "Debian",
          "description": "Debian Linux - stable and minimal"
        },
        {
          "label": "OpenSUSE",
          "description": "OpenSUSE - community-driven Linux distribution"
        }
      ]
    },
    {
      "question": "What performance profile do you need?",
      "header": "Performance",
      "multiSelect": false,
      "options": [
        {
          "label": "General Purpose (u1) (Recommended)",
          "description": "Balanced CPU/memory ratio - suitable for most workloads"
        },
        {
          "label": "Compute Optimized (c1)",
          "description": "More CPU, less memory - CPU-intensive applications"
        },
        {
          "label": "Memory Optimized (m1)",
          "description": "More memory, less CPU - memory-intensive applications"
        },
        {
          "label": "Overcommitted (o1)",
          "description": "Lower resource guarantees - development/testing environments"
        }
      ]
    },
    {
      "question": "What size should the VM be?",
      "header": "Size",
      "multiSelect": false,
      "options": [
        {
          "label": "Small",
          "description": "1 vCPU, 2Gi RAM - lightweight workloads"
        },
        {
          "label": "Medium (Recommended)",
          "description": "2-4 vCPU, 4-8Gi RAM - general purpose applications"
        },
        {
          "label": "Large",
          "description": "4-8 vCPU, 8-16Gi RAM - resource-intensive workloads"
        },
        {
          "label": "XLarge",
          "description": "8+ vCPU, 16+ Gi RAM - high-performance applications"
        }
      ]
    },
    {
      "question": "How much storage should the VM have?",
      "header": "Storage",
      "multiSelect": false,
      "options": [
        {
          "label": "30Gi (Recommended)",
          "description": "30 Gigabytes - sufficient for most workloads"
        },
        {
          "label": "50Gi",
          "description": "50 Gigabytes - moderate storage needs"
        },
        {
          "label": "100Gi",
          "description": "100 Gigabytes - large storage requirements"
        },
        {
          "label": "Custom size",
          "description": "Specify a custom storage size (e.g., 75Gi, 200Gi)"
        }
      ]
    },
    {
      "question": "Which StorageClass should be used for the VM disk?",
      "header": "Storage Class",
      "multiSelect": false,
      "options": [
        {
          "label": "<default-sc-name> (Default)",
          "description": "Cluster default - <performance-hint>, <live-migration-hint>"
        },
        {
          "label": "<sc-name-1>",
          "description": "<performance-hint>, <live-migration-hint>"
        },
        {
          "label": "<sc-name-2>",
          "description": "<performance-hint>, <live-migration-hint>"
        }
      ]
    },
    {
      "question": "Should the VM start automatically after creation?",
      "header": "Autostart",
      "multiSelect": false,
      "options": [
        {
          "label": "No (Recommended)",
          "description": "Create VM in stopped state - start manually when ready"
        },
        {
          "label": "Yes",
          "description": "VM will start automatically after creation"
        }
      ]
    }
  ]
}
```

**Important Notes:**
- Only ask questions for parameters NOT explicitly provided by the user
- If user said "Create a Fedora VM", don't ask about OS - they specified Fedora
- If user said "in namespace production", don't ask about namespace
- Always include "Recommended" on the default options
- The "Other" option is automatically added by the system for each question
- For namespace: Use detected current namespace from kubeconfig context as default
- For StorageClass: Populate options dynamically from cluster, mark default
  - Performance hints: "Immediate provisioning" or "Delayed provisioning"
  - Live migration hints: "Supports live migration (RWX)" or "No live migration (RWO)"

#### Step 1c: Process Interactive Menu Responses

**After receiving AskUserQuestion responses, map them to VM parameters:**

1. **VM Name**:
   - Use custom text input from user
   - **Validate** against rules: lowercase, alphanumeric+hyphens, start with letter, max 63 chars
   - If invalid: Prompt user to provide valid name

2. **Namespace**:
   - "<detected-current-namespace> (Current)" → use detected namespace
   - "Other namespace" → use custom text input
   - Store for use in existence check (Step 1d)

3. **Operating System**:
   - "Fedora (Recommended)" → `"fedora"`
   - "Ubuntu" → `"ubuntu"`
   - "RHEL" → `"rhel"`
   - "CentOS Stream" → `"centos-stream"`
   - "Debian" → `"debian"`
   - "OpenSUSE" → `"opensuse"`
   - Other → custom text input (could be `opensuse-tumbleweed`, `opensuse-leap`, container image URL)

4. **Performance Profile**:
   - "General Purpose (u1) (Recommended)" → `"u1"`
   - "Compute Optimized (c1)" → `"c1"`
   - "Memory Optimized (m1)" → `"m1"`
   - "Overcommitted (o1)" → `"o1"`

5. **Size**:
   - "Small" → `"small"`
   - "Medium (Recommended)" → `"medium"`
   - "Large" → `"large"`
   - "XLarge" → `"xlarge"`

6. **Storage**:
   - "30Gi (Recommended)" → `"30Gi"`
   - "50Gi" → `"50Gi"`
   - "100Gi" → `"100Gi"`
   - "Custom size" → use custom text input (validate format: number + unit, e.g., "75Gi")

7. **StorageClass**:
   - "<default-sc-name> (Default)" → use cluster default SC name
   - "<sc-name-X>" → use selected SC name
   - Store SC name for inclusion in vm_create parameters (if MCP tool supports it)

8. **Autostart**:
   - "No (Recommended)" → `false`
   - "Yes" → `true`

#### Step 1d: Check VM Existence and Present Final Configuration for Confirmation

**CRITICAL: Before presenting configuration, check if VM already exists**

**Use MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

**Handle result:**
- **If VM exists**:
  ```markdown
  ⚠️ **VM Already Exists**

  A VirtualMachine named `<vm-name>` already exists in namespace `<namespace>`.

  **Current VM status**: <status>

  **Options:**
  1. Choose a different VM name
  2. Delete existing VM first (use vm-inventory and manual deletion)
  3. Cancel operation

  What would you like to do?
  ```
  **STOP and wait for user decision.** Do NOT proceed with configuration confirmation.

- **If VM does not exist**: Proceed to configuration confirmation below

---

**After confirming VM doesn't exist, present configuration table:**

```markdown
## Virtual Machine Configuration

**Please review and confirm the VM configuration:**

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `<vm-name>` | from user input (validated) |
| Namespace | `<namespace>` | from user selection/input or current context |
| Operating System | `<os>` | from user selection/input |
| Performance Profile | `<performance>` | from user selection (default: u1) |
| Size | `<size>` | from user selection (default: medium) |
| Storage | `<storage>` | from user selection (default: 30Gi) |
| Storage Class | `<storage-class>` | from user selection (default: cluster default) |
| Autostart | `<yes/no>` | from user selection (default: no) |

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
  "size": "<small|medium|large|xlarge>",// OPTIONAL
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

#### 3a. Consult Troubleshooting Documentation (REQUIRED)

**CRITICAL**: Document consultation MUST happen BEFORE diagnostic commands.

**When ErrorUnschedulable is detected**, consult documentation first to understand root causes.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [scheduling-errors.md](../../docs/troubleshooting/scheduling-errors.md) using the Read tool to understand ErrorUnschedulable root causes (node taints, resource constraints, node selectors) and workaround patterns
2. **Output to user**: "I detected the VM is ErrorUnschedulable. I consulted [scheduling-errors.md](../../docs/troubleshooting/scheduling-errors.md) to understand the diagnosis and remediation strategies."

**Expected Knowledge Gained from Documentation**:
- ErrorUnschedulable is caused by: node taints, insufficient resources, or node selector mismatches
- Most common cause: Node taints that VM doesn't tolerate
- Workaround pattern: Diagnose → Propose → Confirm → Execute using `oc patch`
- MCP tool limitation: `vm_create` doesn't support tolerations parameter

#### 3b. Analyze Error and Gather Diagnostic Information

**Based on the troubleshooting guide**, proceed with diagnostics to identify the specific root cause.

**Output to user**: "I'm now gathering diagnostic information to identify the specific issue."

#### 3c. Gather Diagnostic Information

**Execute diagnostic commands using MCP tools:**

1. **Get VM events to see scheduling failures:**

   **Use MCP Tool**: `events_list` (from openshift-virtualization)

   **Parameters**:
   - `namespace`: "<namespace>" (the VM's namespace)

   Filter events related to the VirtualMachine or VirtualMachineInstance to identify scheduling issues.

2. **Get VM details to see conditions:**

   **Use MCP Tool**: `resources_get` (from openshift-virtualization)

   **Parameters**:
   - `apiVersion`: "kubevirt.io/v1"
   - `kind`: "VirtualMachine"
   - `name`: "<vm-name>"
   - `namespace`: "<namespace>"

   Check `.status.conditions` array for error messages and details.

3. **Check node taints (if taint issue suspected):**

   **Use MCP Tool**: `resources_list` (from openshift-virtualization)

   **Parameters**:
   - `apiVersion`: "v1"
   - `kind`: "Node"

   Parse results to extract `.spec.taints` from each node to identify taints that might block scheduling.

**Parse results** to identify root cause:
- Events contain "taints that the pod didn't tolerate" → **Taints/Tolerations issue**
- Events contain "Insufficient cpu" or "Insufficient memory" → **Resource constraints**
- Events contain "no nodes available" → **No suitable nodes**
- Conditions array shows "Unschedulable" reason → Check reason field for details

#### 3d. Present Diagnosis to User

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

#### 3e. Wait for User Decision (Human-in-the-Loop)

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

#### 3f. Execute Workaround (ONLY if user confirms)

**ONLY if user responds with "apply workaround" or similar confirmation:**

**Option 1: Try MCP Tool First** (Preferred):

**Use MCP Tool**: `resources_create_or_update` (from openshift-virtualization)

Fetch the current VM using `resources_get`, add the tolerations to `.spec.template.spec.tolerations`, then update using `resources_create_or_update`.

**Option 2: Use CLI Patch** (If MCP approach doesn't work):

**Note**: Strategic merge patch via CLI is acceptable when MCP tools cannot perform the same operation.

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

**Verify patch success using MCP Tools**:

1. **Check if tolerations were added:**

   **Use MCP Tool**: `resources_get` (from openshift-virtualization)

   **Parameters**:
   - `apiVersion`: "kubevirt.io/v1"
   - `kind`: "VirtualMachine"
   - `name`: "<vm-name>"
   - `namespace`: "<namespace>"

   Inspect `.spec.template.spec.tolerations` in the response.

2. **Wait 5-10 seconds and check status again:**

   **Use MCP Tool**: `resources_get` (from openshift-virtualization) - same parameters as above

   Check `.status.printableStatus` for the new status.

3. **CRITICAL: Restart the VM to apply the toleration:**

   Simply patching the VM spec does NOT immediately update the existing VirtualMachineInstance. You must restart the VM to force the old VMI to be deleted and a new one created with the updated tolerations.

   **Use MCP Tool**: `vm_lifecycle` (from openshift-virtualization)

   **Parameters**:
   - `namespace`: "<namespace>"
   - `name`: "<vm-name>"
   - `action`: "restart"

   This will:
   - Delete the old VirtualMachineInstance (created without tolerations)
   - Create a new VirtualMachineInstance with the updated spec (including tolerations)
   - Force the scheduler to re-evaluate the VM placement

4. **Wait for VM to reach Running status:**

   After restart, wait 15-20 seconds for the VM to:
   - Schedule on the virtualization node (with new tolerations)
   - Provision the DataVolume (if first boot)
   - Reach Running status

   **Use MCP Tool**: `resources_get` (from openshift-virtualization)

   **Parameters**:
   - `apiVersion`: "kubevirt.io/v1"
   - `kind`: "VirtualMachine"
   - `name`: "<vm-name>"
   - `namespace`: "<namespace>"

   Check `.status.printableStatus` should transition: Stopped → Provisioning → Running

**Report result**:
```markdown
## ✓ Workaround Applied Successfully

**VM Name**: `<vm-name>`
**Namespace**: `<namespace>`
**Action**: Added tolerations for taint `<taint-spec>` and restarted VM

**Status Progression**:
- ✓ Toleration patch applied
- ✓ VM restarted to force rescheduling
- ✓ New VirtualMachineInstance created with tolerations
- ✓ VM successfully scheduled on virtualization node
- ✓ Current Status: <current-status> (should be Running or Provisioning)

**What happened:**
1. Added toleration to VM spec
2. Restarted VM to delete old VirtualMachineInstance
3. New VirtualMachineInstance created with updated spec (generation increased)
4. Scheduler successfully placed VM on virtualization node
5. VM is now running (or provisioning)

**Note**: This workaround was needed because the MCP tool doesn't yet support tolerations. Future VMs in this cluster will need the same fix until the tool is enhanced.

**Next Steps**: Your VM is now running and ready to use! See the "Accessing the VM" section above for connection options.
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
- **Performance**: General Purpose (u1)
- **Size**: medium
- **Storage**: 50Gi (StorageClass: <storage-class-name>)
- **Status**: Halted (VM is created but not running)

**What happens next:**
- DataVolume provisioning: ~2-5 minutes (depends on image size and StorageClass)
- VM will be in "Provisioning" status during image import
- Once complete, status changes to "Stopped" (if autostart=no) or "Running" (if autostart=yes)

**To monitor progress:**
```
"Show status of VM web-server"
```
Watch for status transition: Provisioning → Stopped → Running (when started)

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

---

## 🔐 Accessing the VM

**After the VM is running**, you can access it using:

### Option 1: Serial Console (virtctl)
```bash
virtctl console web-server -n vms
```
- Direct terminal access to VM
- Requires virtctl CLI tool installed

### Option 2: VNC Console (OpenShift Web Console)
1. Navigate to: OpenShift Console → Virtualization → VirtualMachines
2. Select namespace: `vms`
3. Click on VM: `web-server`
4. Click "Console" tab
5. Use VNC or Serial console

### Option 3: SSH Access (if configured)
```bash
# Requires cloud-init SSH key configuration
# Get VM IP using MCP tool: resources_get with apiVersion="kubevirt.io/v1", kind="VirtualMachineInstance", name="web-server", namespace="vms"
# Extract .status.interfaces[0].ipAddress from the response

# Then SSH:
ssh <user>@<vm-ip>
```

### Option 4: Port Forwarding
```bash
# Forward a port from VM to localhost
virtctl port-forward vmi/web-server -n vms 8080:80
# Access via: http://localhost:8080
```

---

## 👤 Default Credentials

Would you like me to display the default credentials for the VM? (yes/no)

**If yes**, I'll show the OS-specific default credentials:
- **Fedora**: User: `fedora`, Password: (none - requires SSH key or console access to set)
- **Ubuntu**: User: `ubuntu`, Password: (none - requires SSH key or console access to set)
- **RHEL**: User: `cloud-user`, Password: (none - requires SSH key)
- **CentOS**: User: `centos`, Password: (none - requires SSH key)
- **Debian**: User: `debian`, Password: (none - requires SSH key)
- **OpenSUSE**: User: `opensuse`, Password: (none - requires SSH key)

**Note**: Most cloud images require SSH key authentication. To set a password:
1. Access via console: `virtctl console <vm-name> -n <namespace>`
2. Login (may auto-login on first boot)
3. Set password: `sudo passwd <username>`

---

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
1. Verify namespace exists using MCP tool: `namespaces_list`
2. Check permissions using CLI (no MCP equivalent): `oc auth can-i create virtualmachines -n <namespace>`
3. View cluster capacity using MCP tool: `nodes_top` or `resources_list` for Node resources
4. Verify operator installed using MCP tool: `resources_list` with apiVersion="operators.coreos.com/v1alpha1", kind="ClusterServiceVersion", namespace="openshift-cnv"

Would you like help troubleshooting this error?
```

## Advanced Features

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
1. List available namespaces using MCP tool: `namespaces_list`
2. Create namespace if needed using MCP tool: `resources_create_or_update` with Namespace resource, OR use CLI: `oc create namespace <name>`
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
1. Check cluster capacity using MCP tool `nodes_top` or `resources_list` for Node resources
2. Try smaller `size` (e.g., change "large" to "medium")
3. Reduce `storage` size if possible
4. Contact cluster admin to scale nodes

### Issue 4: OpenShift Virtualization Not Installed

**Error**: "VirtualMachine CRD not found"

**Solution:**
- OpenShift Virtualization operator must be installed
- Verify using MCP tool: `resources_list` with apiVersion="operators.coreos.com/v1alpha1", kind="ClusterServiceVersion", namespace="openshift-cnv"
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
- [scheduling-errors.md](../../docs/troubleshooting/scheduling-errors.md) - ErrorUnschedulable root causes and workarounds (consulted during diagnostic workflows)
- [storage-errors.md](../../docs/troubleshooting/storage-errors.md) - ErrorDataVolumeNotReady and storage provisioning issues
- [runtime-errors.md](../../docs/troubleshooting/runtime-errors.md) - CrashLoopBackOff and guest OS failures
- [network-errors.md](../../docs/troubleshooting/network-errors.md) - Network attachment failures
- [Troubleshooting INDEX](../../docs/troubleshooting/INDEX.md) - Navigation hub for discovering additional error categories when encountering unexpected issues outside the categories above
- [OpenShift Virtualization Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt/about_virt/about-virt.html)
- [Troubleshooting VMs](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#virt/virtual_machines/troubleshooting_vms.html)
- [KubeVirt VirtualMachine API](https://kubevirt.io/api-reference/)
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server)
- [StorageClass Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.21/html-single/virtualization/index#storage/understanding-persistent-storage.html)

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill requires explicit user confirmation before creating VMs. You MUST:

1. **Wait for user confirmation** on all VM configuration parameters before executing `vm_create`.
2. **Do NOT proceed** with VM creation until the user explicitly approves the configuration.
3. **Present configuration clearly** in a table format and wait for user response.
4. **Never auto-execute** VM creation without user approval - creating VMs is a additive operation that consumes cluster resources, affects quotas and may incur cost.
5. **Allow modifications** - If user wants to change parameters, update and re-confirm before proceeding.

If the user says "no" or wants modifications, address their concerns before proceeding.

**Why this matters:**
- VM creation consumes cluster resources (CPU, memory, storage)
- VMs persist until explicitly deleted
- Incorrect configuration can impact cluster performance
- User should verify namespace, sizing, and other parameters

## Security Considerations

- VMs are created in user-specified namespace (namespace isolation)
- Storage uses cluster-configured storage classes
- Network access controlled by NetworkPolicies
- KUBECONFIG credentials never exposed in output
- All operations audited in Kubernetes API logs
- ServiceAccount permissions limit VM creation scope

## Example Usage

**Example 1: Complete interactive menu workflow (no user input)**

```
User: "Create a VM"

Agent: [Invokes /vm-create skill]
       [Detects current namespace from kubeconfig: "production"]
       [Queries available StorageClasses, finds default: "ocs-storagecluster-ceph-rbd"]
       [No parameters provided, uses AskUserQuestion for full interactive menu]

[Interactive Menu Presented - User selects:]
- VM Name: my-app-server
- Namespace: production (Current)
- Operating System: Fedora (Recommended)
- Performance Profile: General Purpose (u1) (Recommended)
- Size: Medium (Recommended)
- Storage: 30Gi (Recommended)
- Storage Class: ocs-storagecluster-ceph-rbd (Default) - Immediate provisioning, Supports live migration (RWX)
- Autostart: No (Recommended)

Agent: [Validates VM name: "my-app-server" ✓]
       [Checks if VM exists in namespace "production": Not found ✓]
       [Processes responses]

## Virtual Machine Configuration

Please review and confirm the VM configuration:

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `my-app-server` | from interactive menu (validated) |
| Namespace | `production` | from interactive menu (current context) |
| Operating System | `fedora` | from interactive menu |
| Performance Profile | `u1` | from interactive menu (default) |
| Size | `medium` | from interactive menu (default) |
| Storage | `30Gi` | from interactive menu (default) |
| Storage Class | `ocs-storagecluster-ceph-rbd` | from interactive menu (default: cluster default) |
| Autostart | `no` | from interactive menu (default) |

This will create a new VirtualMachine resource consuming cluster resources.

Confirm these settings or tell me what to change.

User: "yes"

Agent: [Calls vm_create with namespace="production", name="my-app-server", workload="fedora", performance="u1", size="medium", storage="30Gi", autostart=false]

## ✓ Virtual Machine Created Successfully

VM Details:
- Name: `my-app-server`
- Namespace: `production`
- OS: Fedora
- Performance: General Purpose (u1)
- Size: medium
- Storage: 30Gi (ocs-storagecluster-ceph-rbd)
- Status: Provisioning → Stopped (wait 2-5 minutes)

[Displays full access instructions and credential prompt]

Next Steps: "Start VM my-app-server in namespace production"
```

**Example 2: Partial interactive menu (some parameters specified by user)**

```
User: "Create an Ubuntu VM called web-01 in namespace apps"

Agent: [Invokes /vm-create skill]
       [Detects VM name="web-01", namespace="apps", OS="ubuntu"]
       [Queries StorageClasses for menu]
       [Uses AskUserQuestion only for: Performance, Size, Storage, Storage Class, Autostart]

[Interactive Menu Presented - User selects:]
- Performance Profile: General Purpose (u1) (Recommended)
- Size: Large
- Storage: 100Gi
- Storage Class: local-storage - Delayed provisioning, No live migration (RWO)
- Autostart: Yes

Agent: [Validates VM name: "web-01" ✓]
       [Checks if VM exists in namespace "apps": Not found ✓]
       [Processes responses]

## Virtual Machine Configuration

Please review and confirm the VM configuration:

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `web-01` | from user input (validated) |
| Namespace | `apps` | from user input |
| Operating System | `ubuntu` | from user input |
| Performance Profile | `u1` | from interactive menu (default) |
| Size | `large` | from interactive menu |
| Storage | `100Gi` | from interactive menu |
| Storage Class | `local-storage` | from interactive menu |
| Autostart | `yes` | from interactive menu |

This will create a new VirtualMachine resource consuming cluster resources.

Confirm these settings or tell me what to change.

User: "yes"

Agent: [Calls vm_create with namespace="apps", name="web-01", workload="ubuntu", performance="u1", size="large", storage="100Gi", autostart=true]

## ✓ Virtual Machine Created and Starting

VM Details:
- Name: `web-01`
- Namespace: `apps`
- OS: Ubuntu
- Performance: General Purpose (u1)
- Size: large
- Storage: 100Gi (local-storage)
- Status: Provisioning → Running (autostarted)

[Displays full access instructions]
```

**Example 3: User modifies configuration before confirming**

```
User: "Deploy a memory-optimized RHEL VM called db-server in production namespace"

Agent: [Invokes /vm-create skill]
       [Detects: name="db-server", namespace="production", OS="rhel", performance="m1" (memory-optimized)]
       [Uses AskUserQuestion for: Size, Storage, Storage Class, Autostart]

[Interactive Menu - User selects:]
- Size: Large
- Storage: 100Gi
- Storage Class: ceph-rbd (Default)
- Autostart: No (Recommended)

Agent: [Validates and checks existence ✓]

## Virtual Machine Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `db-server` | from user input (validated) |
| Namespace | `production` | from user input |
| Operating System | `rhel` | from user input |
| Performance Profile | `m1` | from user input (memory-optimized) |
| Size | `large` | from interactive menu |
| Storage | `100Gi` | from interactive menu |
| Storage Class | `ceph-rbd` | from interactive menu (default) |
| Autostart | `no` | from interactive menu (default) |

Confirm these settings or tell me what to change.

User: "Actually, autostart it and make it compute-optimized instead"

Agent: [Updates configuration]

## Updated Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Performance Profile | `c1` | updated per user request (compute-optimized) |
| Autostart | `yes` | updated per user request |

Confirm?

User: "yes"

Agent: [Calls vm_create with namespace="production", name="db-server", workload="rhel", performance="c1", size="large", storage="100Gi", autostart=true]

## ✓ Virtual Machine Created and Starting

VM Details:
- Name: `db-server`
- Namespace: `production`
- OS: RHEL
- Performance: Compute Optimized (c1)
- Size: large
- Storage: 100Gi (ceph-rbd)
- Status: Provisioning → Running (autostarted)

[Displays access instructions]
```

**Example 4: VM name already exists - user prompted to choose different name**

```
User: "Create a VM named apache-server in namespace vms"

Agent: [Invokes /vm-create skill]
       [Validates name: "apache-server" ✓]
       [Checks if VM exists...]

⚠️ **VM Already Exists**

A VirtualMachine named `apache-server` already exists in namespace `vms`.

**Current VM status**: Stopped

**Options:**
1. Choose a different VM name
2. Delete existing VM first (use vm-inventory and manual deletion)
3. Cancel operation

What would you like to do?

User: "Choose a different name: apache-server-02"

Agent: [Validates new name: "apache-server-02" ✓]
       [Checks existence: Not found ✓]
       [Continues with interactive menu for remaining parameters...]

## Virtual Machine Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `apache-server-02` | from user input (updated, validated) |
| Namespace | `vms` | from user input |
...

[Continues normally]
```

**Example 5: User cancels after reviewing configuration**

```
User: "Create a VM named test in namespace dev"

Agent: [Invokes /vm-create skill]
       [Interactive menu presented...]
       [Processes responses]

## Virtual Machine Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| VM Name | `test` | from user input (validated) |
| Namespace | `dev` | from user input |
| Operating System | `fedora` | from interactive menu (default) |
| Performance Profile | `u1` | from interactive menu (default) |
| Size | `medium` | from interactive menu (default) |
| Storage | `30Gi` | from interactive menu (default) |
| Storage Class | `default-sc` | from interactive menu (default) |
| Autostart | `no` | from interactive menu (default) |

Confirm these settings or tell me what to change.

User: "no, cancel"

Agent: VM creation cancelled. No resources were created.
```

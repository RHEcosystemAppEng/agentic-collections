# Red Hat Virtualization Collection (rh-virt)

Skills for managing virtual machines in OpenShift Virtualization (KubeVirt). Covers VM lifecycle, snapshots, cloning, and rebalancing. Uses a quality-controlled skill template with mandatory Common Issues and Example Usage sections.

- **Persona**: Virtualization Administrator
- **Marketplaces**: Claude Code, Cursor

## Prerequisites

### MCP Server

Configure in `rh-virt/.mcp.json`.

```json { .api }
{
  "mcpServers": {
    "openshift-virtualization": {
      "command": "podman",
      "args": [
        "run", "--rm", "-i", "--network=host",
        "--userns=keep-id:uid=65532,gid=65532",
        "-v", "${KUBECONFIG}:/kubeconfig:ro,Z",
        "--entrypoint", "/app/kubernetes-mcp-server",
        "quay.io/ecosystem-appeng/openshift-mcp-server:latest",
        "--kubeconfig", "/kubeconfig",
        "--toolsets", "core,kubevirt"
      ],
      "env": { "KUBECONFIG": "${KUBECONFIG}" },
      "description": "OpenShift MCP server with KubeVirt toolset",
      "security": { "isolation": "container", "network": "local", "credentials": "env-only" }
    }
  }
}
```

**Platform notes:**
- **Linux**: `--userns=keep-id:uid=65532,gid=65532` is included for proper UID/GID mapping
- **macOS**: Omit `--userns` flag (unsupported inside Podman VM)

### Environment Variables

| Variable | Description |
|----------|-------------|
| `KUBECONFIG` | Path to kubeconfig with OpenShift cluster access |

### Cluster Requirements

- OpenShift >= 4.19
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions for VirtualMachine resources
- Namespace with appropriate permissions

## Capabilities

### /vm-create — Create Virtual Machines

Creates new VMs with automatic instance type resolution and OS selection.

```markdown { .api }
Skill: vm-create
Invocation: /vm-create
Model: inherit
Color: green

MCP Tool: vm_create (from openshift-virtualization)
Parameters:
  namespace: str     REQUIRED
  name: str          REQUIRED — lowercase, alphanumeric+hyphens, starts letter, max 63 chars
  workload: str      OPTIONAL — fedora (default) | ubuntu | rhel | centos-stream | debian | opensuse
  size: str          OPTIONAL — small | medium (default) | large | xlarge
  storage: str       OPTIONAL — e.g. "30Gi" (default) | "50Gi" | "100Gi"
  performance: str   OPTIONAL — u1 (general, default) | c1 (compute) | m1 (memory) | o1 (overcommit)
  autostart: bool    OPTIONAL — false (default) | true

Human-in-the-Loop: REQUIRED — displays configuration table before creation
```

**Size/performance reference:**

| Size | vCPU | Memory |
|------|------|--------|
| small | 1 | 2Gi |
| medium | 2-4 | 4-8Gi |
| large | 4-8 | 8-16Gi |
| xlarge | 8+ | 16+Gi |

| Performance | Use Case |
|-------------|----------|
| u1 | General purpose, balanced |
| c1 | CPU-intensive workloads |
| m1 | Memory-intensive workloads |
| o1 | Dev/test, overcommitted |

**Default credentials after creation:**

| OS | Username |
|----|----------|
| Fedora | fedora |
| Ubuntu | ubuntu |
| RHEL | cloud-user |
| CentOS Stream | centos |
| Debian | debian |

**VM access methods:**
```bash
# Serial console
virtctl console <vm-name> -n <namespace>

# VNC: OpenShift Console → Virtualization → VMs → <name> → Console

# SSH (after getting IP from VMI)
ssh <user>@<ip>

# Port forwarding
virtctl port-forward vmi/<vm-name> -n <namespace> 8080:80
```

**Custom image/network examples:**
```
vm_create({"namespace": "vms", "name": "web", "workload": "quay.io/containerdisks/fedora:latest", ...})
vm_create({"namespace": "vms", "name": "web", "networks": ["vlan-network"], ...})
vm_create({"namespace": "vms", "name": "web", "instancetype": "u1.large", ...})
```

**Error handling:**

| Status | Meaning | Action |
|--------|---------|--------|
| Stopped/Halted | VM created, not started | Success |
| Running | VM created and running (autostart=true) | Success |
| Provisioning | Still provisioning (wait 2-5 min) | Wait |
| ErrorUnschedulable | Scheduling issue (taints/resources) | Run diagnostic workflow |
| ErrorDataVolumeNotReady | Storage issue | Check StorageClass |

---

### /vm-inventory — VM Inventory and Status

Lists and views VMs across namespaces with status, resource usage, and health information.

```markdown { .api }
Skill: vm-inventory
Invocation: /vm-inventory
Model: inherit
Color: cyan

Read-only: no confirmation required

Provides: VM list, status (Running/Stopped/Provisioning), resource allocation,
          health indicators, namespace grouping

Use when: "List all VMs", "Show VMs in namespace X", "What VMs are running?",
          "Get details of VM X"
NOT for: creating or modifying VMs
```

---

### /vm-lifecycle-manager — VM Start/Stop/Restart

Manages VM lifecycle state transitions safely.

```markdown { .api }
Skill: vm-lifecycle-manager
Invocation: /vm-lifecycle-manager
Model: inherit
Color: blue (reversible)

MCP Tool: vm_lifecycle (from openshift-virtualization)
  action: start | stop | restart
  namespace: str
  name: str

Human-in-the-Loop: Required before each state change

Use when: "Start VM X", "Stop VM X", "Restart VM X", "Power on/off VM X"
NOT for: creating VMs (use /vm-create) or deleting VMs (use /vm-delete)
```

---

### /vm-delete — VM Deletion

Permanently deletes VMs and associated resources.

```markdown { .api }
Skill: vm-delete
Invocation: /vm-delete
Model: inherit
Color: red (irreversible)

Human-in-the-Loop: REQUIRED
  1. Display VM details and resources that will be deleted
  2. Ask: "Type exact VM name to confirm: <name>"
  3. Verify exact match — cancel on mismatch
  4. Ask: "Type 'DELETE' to proceed"
  5. Only proceed on exact match

CRITICAL: This operation is IRREVERSIBLE.
NOT for: power management (use /vm-lifecycle-manager to stop VMs)
```

---

### /vm-clone — VM Cloning

Clones existing VMs for testing, scaling, or creating templates.

```markdown { .api }
Skill: vm-clone
Invocation: /vm-clone
Model: inherit
Color: green

Supports: single VM clone, batch cloning (multiple copies)
Storage options: create new storage (independent copy) or reference existing storage
Source: can clone any existing VM or VM template

Human-in-the-Loop: Required before cloning

Use when: "Clone VM X to Y", "Create a copy of VM X",
          "Duplicate VM X for testing", "Create 3 copies of template-vm"
NOT for: snapshots (use /vm-snapshot-create for point-in-time backups)
```

---

### /vm-rebalance — VM Migration and Load Balancing

Orchestrates VM migrations across cluster nodes for load balancing, maintenance, or resource optimization.

```markdown { .api }
Skill: vm-rebalance
Invocation: /vm-rebalance
Model: inherit
Color: yellow (potentially disruptive)

Modes:
  Manual:    User-driven — user selects specific VMs and target nodes
  Automatic: AI-driven — analyzes cluster load and recommends migrations

Use when: "Move VM X to worker-03", "Rebalance VMs to optimize CPU load",
          "Drain worker-02 for maintenance", "Automatically rebalance the cluster"
NOT for: creating VMs or simple start/stop (use /vm-lifecycle-manager)
```

---

### /vm-snapshot-create — Create VM Snapshots

Creates VM snapshots for backup and recovery.

```markdown { .api }
Skill: vm-snapshot-create
Invocation: /vm-snapshot-create
Model: inherit
Color: green

Pre-flight checks:
  - Storage class snapshot support validation
  - CSI driver capabilities check
  - Guest agent status check

Human-in-the-Loop: Required before snapshot creation

Use when: "Create a snapshot of VM X", "Backup VM X before upgrade",
          "Take a snapshot of [vm]"
NOT for: VM cloning (use /vm-clone for independent copies)
```

---

### /vm-snapshot-list — List VM Snapshots

Lists VM snapshots with status, age, and recovery information.

```markdown { .api }
Skill: vm-snapshot-list
Invocation: /vm-snapshot-list
Model: inherit
Color: cyan (read-only)

Read-only: no confirmation required
Provides: snapshot name, VM, namespace, status, creation age, recoverability

Use when: "List snapshots for VM X", "Show snapshots in namespace Y",
          "What snapshots exist for [vm]?"
```

---

### /vm-snapshot-delete — Delete VM Snapshots

Permanently deletes VM snapshots to free storage.

```markdown { .api }
Skill: vm-snapshot-delete
Invocation: /vm-snapshot-delete
Model: inherit
Color: yellow (destructive but recoverable in theory)

Human-in-the-Loop: Required confirmation before deletion

Use when: "Delete snapshot X", "Remove old snapshots for VM X",
          "Free up snapshot storage"
NOT for: restoring from snapshots (use /vm-snapshot-restore)
```

---

### /vm-snapshot-restore — Restore VM from Snapshot

Restores a VM from a snapshot with strict safety confirmations.

```markdown { .api }
Skill: vm-snapshot-restore
Invocation: /vm-snapshot-restore
Model: inherit
Color: red (irreversible — overwrites current VM state)

CRITICAL requirements:
  1. VM MUST be stopped before restore
  2. User must type the exact snapshot name to confirm
  3. All changes since snapshot are LOST

Human-in-the-Loop: REQUIRED — typed snapshot name confirmation

Use when: "Restore VM X from snapshot Y", "Roll back VM X",
          "Recover VM X from backup"
NOT for: creating snapshots (use /vm-snapshot-create)
```

## OpenShift Virtualization MCP Tools

```python { .api }
# openshift-virtualization MCP server tools (KubeVirt toolset)

vm_create(
    namespace: str,        # REQUIRED
    name: str,             # REQUIRED — kebab-case, max 63 chars
    workload: str,         # OPTIONAL — OS type or container image URL
    size: str,             # OPTIONAL — small | medium | large | xlarge
    storage: str,          # OPTIONAL — e.g. "30Gi"
    performance: str,      # OPTIONAL — u1 | c1 | m1 | o1
    autostart: bool,       # OPTIONAL — default false
    instancetype: str,     # OPTIONAL — explicit instance type e.g. "u1.large"
    networks: list,        # OPTIONAL — additional network interfaces
) -> dict                  # VirtualMachine resource status

vm_lifecycle(
    namespace: str,        # REQUIRED
    name: str,             # REQUIRED
    action: str            # REQUIRED — "start" | "stop" | "restart"
) -> dict

resources_get(
    apiVersion: str,       # e.g. "kubevirt.io/v1"
    kind: str,             # e.g. "VirtualMachine", "VirtualMachineInstance"
    namespace: str,
    name: str
) -> dict                  # Full Kubernetes resource

resources_list(
    apiVersion: str,       # e.g. "kubevirt.io/v1", "storage.k8s.io/v1", "v1"
    kind: str,             # e.g. "VirtualMachine", "StorageClass", "Node"
    namespace: str         # OPTIONAL
) -> list[dict]

resources_create_or_update(
    resource: dict         # Full Kubernetes resource JSON
) -> dict

resources_delete(
    apiVersion: str,       # e.g. "kubevirt.io/v1"
    kind: str,             # e.g. "VirtualMachineInstance"
    namespace: str,
    name: str
) -> dict

# Pod operations
pods_list_in_namespace(namespace: str) -> list[dict]
pods_get(name: str, namespace: str) -> dict
pods_log(name: str, namespace: str) -> str
pods_exec(name: str, namespace: str, command: list[str]) -> str
pods_delete(name: str, namespace: str) -> dict
pods_top(namespace: str) -> list[dict]  # Pod CPU/memory usage

# Cluster operations
namespaces_list() -> list[dict]
events_list(namespace: str) -> list[dict]
nodes_top() -> list[dict]     # Node CPU/memory usage
nodes_log(name: str) -> str   # Node system logs
nodes_stats_summary(name: str) -> dict  # Detailed node statistics
```

## Troubleshooting Documentation

The rh-virt pack includes a semantic-indexed troubleshooting guide in `rh-virt/docs/troubleshooting/`. Skills consult these docs **before** using MCP tools when diagnosing errors.

```python { .api }
# rh-virt/docs/troubleshooting/ structure:
# INDEX.md             — master navigation hub; read first for skill-to-doc mapping
# scheduling-errors.md — ErrorUnschedulable (node taints, insufficient resources, node selector)
# storage-errors.md    — ErrorDataVolumeNotReady, ErrorPvcNotFound, storage deletion failures,
#                        DataVolume cloning failures
# lifecycle-errors.md  — VM stuck in Terminating, VM won't start/stop
# runtime-errors.md    — CrashLoopBackOff (kernel panic, QEMU crash, OOM, guest OS)
# network-errors.md    — Network attachment failures (Multus, SR-IOV, NetworkAttachmentDefinition)
#
# .ai-index/semantic-index.json — AI-optimized discovery index; read first (~200 tokens)
#
# Quick navigation by skill:
#   vm-create:           scheduling-errors.md, storage-errors.md, runtime-errors.md, network-errors.md
#   vm-delete:           lifecycle-errors.md, storage-errors.md
#   vm-clone:            storage-errors.md
#   vm-lifecycle-manager: lifecycle-errors.md, scheduling-errors.md
#   vm-inventory:        INDEX.md (general guidance)
```

**MCP-first diagnostic pattern** (all troubleshooting docs follow this):
```
1. TRY: MCP Tool (resources_get, resources_list, pods_log, events_list, etc.)
2. IF FAILS: Ask user permission to use CLI command
3. LAST RESORT: Execute CLI command (oc/kubectl) with explicit user approval
```

**CLI commands with no MCP equivalent** (require explicit user approval):
- `virtctl` commands (console access, VNC)
- `oc debug node` (node debugging)
- `oc auth can-i` (permission checks)
- `oc adm taint` (node taint management)

## Skill Development Template

The rh-virt collection includes `rh-virt/SKILL_TEMPLATE.md` — a comprehensive template for creating new skills. It documents:
- YAML frontmatter schema with color coding guide (cyan/green/blue/yellow/red)
- Mandatory section order (Prerequisites → When to Use → Workflow → Common Issues → Dependencies → Human-in-the-Loop → Security → Example Usage)
- Document consultation patterns (consulting troubleshooting docs before MCP tool invocation)
- Precise parameter specification format
- Human-in-the-Loop confirmation patterns
- Comprehensive validation checklist (12 categories)

## Common Issues

| Issue | Error | Solution |
|-------|-------|----------|
| Namespace not found | "Namespace 'xyz' not found" | List with `namespaces_list`, create with `resources_create_or_update` |
| Insufficient permissions | "Forbidden: cannot create VirtualMachines" | Verify KUBECONFIG RBAC, requires create VirtualMachine permissions |
| Resource constraints | "0/N nodes: Insufficient cpu/memory" | Try smaller size, use o1 overcommitted, or scale cluster |
| Node taints | "0/N nodes: taints pod didn't tolerate" | Apply tolerations workaround (patch + vm_lifecycle restart) |
| Storage not ready | "PVC pending" or "StorageClass not found" | Verify StorageClass annotation `is-default-class`, check provisioner |
| DataVolume import | "image pull error" | Verify internet access, check DV status, verify OS name |
| Operator missing | "VirtualMachine CRD not found" | Verify OpenShift Virtualization operator installed |

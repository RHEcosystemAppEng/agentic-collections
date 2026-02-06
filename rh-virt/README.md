# Red Hat Virtualization Agentic Pack

OpenShift Virtualization management tools for administering virtual machines on OpenShift clusters. This pack provides automation capabilities for VM lifecycle management, provisioning, and inventory operations using KubeVirt.

**Persona**: Virtualization Administrator, OpenShift Administrator
**Marketplaces**: Claude Code, Cursor

## Overview

The rh-virt collection provides specialized tools for managing virtual machines in OpenShift Virtualization environments:

- **3 specialized skills** for VM administration tasks
- **OpenShift MCP server integration** for KubeVirt operations
- **VM lifecycle management** from creation to operational monitoring

## Quick Start

### Prerequisites

- Claude Code CLI or IDE extension
- OpenShift cluster (>= 4.19) with Virtualization operator installed
- ServiceAccount with appropriate RBAC permissions for VirtualMachine resources
- KUBECONFIG environment variable configured with cluster access

### Environment Setup

Configure OpenShift cluster access:

```bash
export KUBECONFIG="/path/to/your/kubeconfig"
```

Verify access to the cluster:

```bash
oc get virtualmachines -A
# or
kubectl get vms -A
```

### Installation (Claude Code)

Install the pack as a Claude Code plugin:

```bash
claude plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-collections
claude plugin install openshift-virtualization
```

Or for local development:

```bash
claude plugin marketplace add /path/to/agentic-collections
claude plugin install openshift-virtualization
```

## Skills

The pack provides 3 specialized skills for common virtualization operations:

### 1. **vm-creator** - Virtual Machine Provisioning

Create new virtual machines in OpenShift Virtualization with automatic error diagnosis and workarounds.

**Use when:**
- "Create a new VM"
- "Deploy a virtual machine"
- "Provision a VM with specific configuration"

**What it does:**
- Creates VirtualMachine resources
- Configures instance specifications
- Sets up storage and networking
- **Automatically diagnoses scheduling issues** (e.g., node taints, resource constraints)
- **Proposes workarounds** for MCP tool limitations
- **Applies fixes** with user confirmation (human-in-the-loop)

### 2. **vm-lifecycle-manager** - VM Power Management

Control VM lifecycle operations including start, stop, and restart.

**Use when:**
- "Start VM [name]"
- "Stop the virtual machine [name]"
- "Restart VM [name]"

**What it does:**
- Starts stopped/halted VMs
- Stops running VMs gracefully
- Restarts VMs (stop + start sequence)
- Manages VM runStrategy transitions

### 3. **vm-inventory** - VM Discovery and Status

List and inspect virtual machines across namespaces.

**Use when:**
- "List all VMs"
- "Show VMs in namespace [name]"
- "Get details of VM [name]"
- "What VMs are running?"

**What it does:**
- Lists VMs across namespaces
- Shows VM status and health
- Provides detailed VM configuration
- Filters VMs by labels or fields

## MCP Server Integration

The pack integrates with the OpenShift MCP server (configured in `.mcp.json`):

### **openshift-virtualization** - OpenShift MCP Server (KubeVirt Toolset)

Provides access to KubeVirt virtual machine operations through the Model Context Protocol.

**Repository**: https://github.com/openshift/openshift-mcp-server

**Available Tools**:
- `vm_create` - Create new VirtualMachines
- `vm_lifecycle` - Manage VM power state (start/stop/restart)

**Configuration**:
```json
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
```

## Sample Workflows

### Workflow 1: Create and Start VM

```
User: "Create a VM called web-server in namespace production"
→ vm-creator skill creates the VM

User: "Start the web-server VM"
→ vm-lifecycle-manager skill starts the VM

User: "Check if it's running"
→ vm-inventory skill shows VM status
```

### Workflow 2: VM Inventory Check

```
User: "Show all VMs in production namespace"
→ vm-inventory skill lists all VMs with status

User: "What's the status of database-vm?"
→ vm-inventory skill shows detailed VM information
```

### Workflow 3: VM Lifecycle Management

```
User: "Stop all VMs in development namespace"
→ vm-lifecycle-manager skill stops each VM

User: "Restart the api-server VM"
→ vm-lifecycle-manager skill restarts the VM
```

### Workflow 4: Automatic Error Diagnosis and Remediation

```
User: "Create a Fedora VM called test-vm in namespace demo"
→ vm-creator skill creates the VM
→ Detects ErrorUnschedulable status
→ Consults troubleshooting.md documentation
→ Diagnoses: Node taints prevent scheduling
→ Proposes workaround: Add tolerations to VM spec

Agent: "⚠️ VM Scheduling Issue Detected
        Root Cause: Node taints prevent VM scheduling

        I can apply a workaround to add the required tolerations.
        How would you like to proceed?"

User: "apply workaround"
→ vm-creator patches VM with tolerations
→ Verifies VM can now be scheduled
→ Reports success

Agent: "✓ Workaround Applied Successfully
        VM can now be scheduled on virtualization nodes"
```

**Key Features**:
- **Automatic diagnosis**: Detects ErrorUnschedulable and other common errors
- **Documentation consultation**: Reads troubleshooting.md for domain knowledge
- **Intelligent workarounds**: Proposes fixes for MCP tool limitations
- **Human-in-the-loop**: Requires explicit user confirmation before applying patches
- **Transparent**: Explains temporary limitations and suggests filing enhancement requests

## Configuration

MCP server is configured in `.mcp.json`:

```json
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
```

**Key Configuration Notes**:
- Uses `KUBECONFIG` environment variable for cluster authentication
- Requires OpenShift Virtualization operator installed on the cluster
- ServiceAccount needs RBAC permissions for VirtualMachine resources

## Troubleshooting

### Automatic Diagnosis (Recommended)

The **vm-creator** skill includes automatic error diagnosis and workaround proposals. When VMs encounter scheduling issues:

1. **Detection**: Skill automatically detects ErrorUnschedulable and other error states
2. **Diagnosis**: Consults `docs/troubleshooting.md` to understand root cause
3. **Investigation**: Executes diagnostic commands (node taints, resource availability, events)
4. **Proposal**: Presents clear diagnosis with workaround options
5. **Remediation**: Applies fix with user confirmation (human-in-the-loop)

**Common Issues Handled**:
- **ErrorUnschedulable** - Node taints/tolerations mismatch, resource constraints, node selector issues
- **ErrorDataVolumeNotReady** - Storage provisioning delays, storage class issues, quota exceeded

**For comprehensive troubleshooting guidance**, see [docs/troubleshooting.md](docs/troubleshooting.md).

### MCP Server Won't Start

**Problem**: Server fails to connect to cluster

**Solutions**:
1. Verify KUBECONFIG is set: `echo $KUBECONFIG`
2. Test cluster access: `oc get nodes` or `kubectl get nodes`
3. Check ServiceAccount permissions: `oc auth can-i create virtualmachines -A`

### VM Operations Fail

**Problem**: VM creation or lifecycle operations return errors

**Solutions**:
1. Verify OpenShift Virtualization operator is installed
2. Check namespace exists and ServiceAccount has access
3. Verify RBAC permissions for VirtualMachine resources
4. Check cluster resource availability (CPU, memory, storage)
5. Let vm-creator skill run automatic diagnosis (see Workflow 4 above)

### Skills Not Triggering

**Problem**: Skills don't activate on expected queries

**Solutions**:
1. Verify plugin installed: `claude plugin list`
2. Reload Claude Code to refresh plugins
3. Check skill descriptions match query intent
4. Use explicit phrasing from skill examples

## Architecture Reference

### Directory Structure

```
rh-virt/
├── README.md                    # This file
├── .claude-plugin/
│   └── plugin.json              # Plugin metadata
├── .mcp.json                    # MCP server configuration
├── docs/                        # AI-optimized knowledge base
│   └── troubleshooting.md       # VM error diagnosis and workarounds
└── skills/
    ├── vm-creator/SKILL.md      # VM provisioning with auto-diagnosis
    ├── vm-lifecycle-manager/SKILL.md  # VM power management
    └── vm-inventory/SKILL.md    # VM discovery and status
```

### Key Patterns

- **Skills encapsulate operations** - Each skill handles one category of VM tasks
- **MCP provides tools** - OpenShift MCP server exposes KubeVirt operations
- **Environment-based auth** - KUBECONFIG for secure cluster access
- **Automatic diagnosis** - Skills detect errors, consult docs, propose workarounds
- **Document consultation** - Skills read troubleshooting.md for domain knowledge
- **Human-in-the-loop** - User approval required before applying fixes
- **Workaround transparency** - Clear communication of MCP tool limitations and temporary solutions

## Security Model

**Cluster access**:
- Uses KUBECONFIG for authentication
- Respects Kubernetes RBAC permissions
- ServiceAccount-based authorization
- No credential storage or caching

**VM operations**:
- Namespace isolation enforced
- Resource quotas respected
- All operations audited in Kubernetes API logs

## Development

See main repository [README.md](../README.md) for:
- Adding new skills
- Creating agents
- Integrating MCP servers
- Testing and validation

## License

[Apache 2.0](../LICENSE)

## References

- [OpenShift Virtualization Documentation](https://docs.openshift.com/container-platform/latest/virt/about_virt/about-virt.html)
- [KubeVirt User Guide](https://kubevirt.io/user-guide/)
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Main Repository](https://github.com/RHEcosystemAppEng/agentic-collections)

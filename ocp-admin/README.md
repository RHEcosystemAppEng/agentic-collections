# OpenShift Administration Agentic Pack

Administration and management tools for OpenShift Container Platform. This pack provides automation capabilities for cluster lifecycle management, multi-cluster operations, workload orchestration, and security policies.

**Persona**: OpenShift Administrator
**Marketplaces**: Claude Code, Cursor

---

## Overview

The ocp-admin collection provides specialized tools for managing OpenShift clusters throughout their lifecycle:

- **Complete cluster lifecycle**: Creation, configuration, monitoring, and operations
- **Multi-cluster management**: Consolidated reporting across multiple clusters
- **Assisted Installer integration**: Automated cluster deployment with validation
- **Comprehensive documentation**: 17 reference documents covering all aspects of OpenShift administration

---

## Quick Start

### Prerequisites

- Claude Code CLI or IDE extension
- **For cluster creation**:
  - Red Hat account with access to cloud.redhat.com
  - Offline token from https://cloud.redhat.com/openshift/token
  - Python 3.10+ with `uv` installed
  - Assisted Service MCP server (see setup below)
- **For cluster operations**:
  - OpenShift cluster access via `KUBECONFIG`
  - For multi-cluster reports, a kubeconfig with multiple contexts

### Installation (Claude Code)

Install the pack as a Claude Code plugin:

```bash
# Option 1: From GitHub (when published)
claude plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-collections
claude plugin install ocp-admin

# Option 2: Local development
claude plugin marketplace add /path/to/agentic-collections
claude plugin install ocp-admin
```

Verify installation:

```bash
claude plugin list
# Should show: ocp-admin@redhat-agentic-collections
```

---

## Environment Setup

### Important: MCP Server Configuration

**⚠️ CRITICAL**: The `mcps.json` file in this plugin is for **reference only**. MCP servers are **NOT automatically installed** by Claude Code plugins.

**You must manually configure MCP servers** in your Claude Code settings using **one of these methods**:

#### Option A: Using Claude Code `/mcp` Command (Recommended)

1. Open Claude Code
2. Type `/mcp` to open MCP Server Manager
3. Click "Add Server" for each server below
4. Copy the configuration from `mcps.json`

#### Option B: Manual Settings Configuration

Add the MCP servers to your settings file:

**Linux/macOS**: `~/.claude/settings.json`
**Windows**: `%APPDATA%\.claude\settings.json`

```json
{
  "mcpServers": {
    "openshift-self-managed": {
      // ... copy from mcps.json
    },
    "openshift-ocm-managed": {
      // ... copy from mcps.json
    }
  }
}
```

---

### 1. MCP Servers for Cluster Management

This plugin requires **TWO MCP servers** for complete functionality:

| MCP Server | Purpose | Cluster Types | Required For |
|-----------|---------|---------------|--------------|
| `openshift-self-managed` | Assisted Installer API | OCP, SNO | cluster-creator, cluster-inventory |
| `openshift-ocm-managed` | OCM API | ROSA, ARO, OSD | cluster-inventory |

Both servers use the same container image but with different configurations.

---

### 2. Get Your Red Hat Offline Token

**Required for both MCP servers**:

1. Visit https://cloud.redhat.com/openshift/token
2. Log in with your Red Hat account
3. Click **"Load token"** → **"Copy to clipboard"**
4. Set environment variable:

```bash
export OFFLINE_TOKEN="your-token-here"

# Verify
test -n "$OFFLINE_TOKEN" && echo "✓ Set" || echo "✗ Missing"

# Make persistent (add to shell profile)
echo 'export OFFLINE_TOKEN="your-token-here"' >> ~/.bashrc
source ~/.bashrc
```

**Note**: Token is long-lived (30 days), auto-refreshes on use.

---

### 3. Configure MCP Servers in Claude Code

Copy the **entire configuration** from `ocp-admin/mcps.json` to your Claude Code settings:

**From**: `ocp-admin/mcps.json` (reference)
**To**: `~/.claude/settings.json` (active configuration)

**Full Configuration** (copy this to your settings):

```json
{
  "mcpServers": {
    "openshift-self-managed": {
      "command": "bash",
      "args": [
        "-c",
        "U=(); \
         [ \"$(uname -s)\" = Linux ] && U=(--userns=keep-id:uid=1001,gid=0); \
         exec podman run \"${U[@]}\" \
           --rm \
           -i \
           --network=host \
           -e OFFLINE_TOKEN=\"${OFFLINE_TOKEN}\" \
           -e TRANSPORT=stdio \
           -e INVENTORY_URL=\"${INVENTORY_URL:-https://api.openshift.com/api/assisted-install/v2}\" \
           -e PULL_SECRET_URL=\"${PULL_SECRET_URL:-https://api.openshift.com/api/accounts_mgmt/v1/access_token}\" \
           -e OCM_URL=\"${OCM_URL:-https://api.openshift.com/api/clusters_mgmt/v1}\" \
           quay.io/ecosystem-appeng/assisted-service-mcp:latest"
      ],
      "env": {
        "OFFLINE_TOKEN": "${OFFLINE_TOKEN}",
        "INVENTORY_URL": "${INVENTORY_URL}",
        "PULL_SECRET_URL": "${PULL_SECRET_URL}",
        "OCM_URL": "${OCM_URL}"
      },
      "description": "Red Hat Assisted Installer MCP server for self-managed clusters (OCP, SNO)"
    },
    "openshift-ocm-managed": {
      "command": "bash",
      "args": [
        "-c",
        "U=(); \
         [ \"$(uname -s)\" = Linux ] && U=(--userns=keep-id:uid=1001,gid=0); \
         exec podman run \"${U[@]}\" \
           --rm \
           -i \
           --network=host \
           -e OFFLINE_TOKEN=\"${OFFLINE_TOKEN}\" \
           -e TRANSPORT=stdio \
           -e INVENTORY_URL=\"${INVENTORY_URL:-https://api.openshift.com/api/assisted-install/v2}\" \
           -e PULL_SECRET_URL=\"${PULL_SECRET_URL:-https://api.openshift.com/api/accounts_mgmt/v1/access_token}\" \
           -e OCM_URL=\"${OCM_URL:-https://api.openshift.com/api/clusters_mgmt/v1}\" \
           quay.io/ecosystem-appeng/assisted-service-mcp:latest"
      ],
      "env": {
        "OFFLINE_TOKEN": "${OFFLINE_TOKEN}",
        "OCM_URL": "${OCM_URL}"
      },
      "description": "Red Hat OCM MCP server for managed service clusters (ROSA, ARO, OSD)"
    }
  }
}
```

**Verify Podman is installed**:

```bash
# Check Podman
podman --version

# Test container pull
podman pull quay.io/ecosystem-appeng/assisted-service-mcp:latest
```

**Test the MCP servers**:

```bash
# Restart Claude Code after configuration
# Then try:
# "List all my OpenShift clusters"
```

### 2. OpenShift MCP Server (for cluster operations)

The `cluster-report` skill uses the OpenShift MCP server for multi-cluster operations.

**Build the container image** (if not already built):

```bash
# Clone the repository
git clone https://github.com/openshift/openshift-mcp-server.git
cd openshift-mcp-server

# Build with Podman
podman build -t quay.io/ecosystem-appeng/openshift-mcp-server:latest -f Dockerfile .

# Verify the build
podman images quay.io/ecosystem-appeng/openshift-mcp-server:latest
```

**Configure cluster access**:

```bash
# Set KUBECONFIG to your cluster
export KUBECONFIG="/path/to/your/kubeconfig"

# Verify access
oc get nodes
# or
kubectl get nodes
```

---

## Skills

### 1. **cluster-creator** - End-to-End Cluster Deployment

Create OpenShift clusters using the Red Hat Assisted Installer with full workflow automation.

**Use when**:
- "Create a new OpenShift cluster"
- "Install OpenShift on my servers"
- "Set up a single-node cluster for edge deployment"
- "Deploy a production HA cluster"

**MCP Server**: `openshift-installer` (Assisted Service)

**What it does**:
- Interactive cluster configuration gathering
- Support for SNO and HA deployments
- Platform-specific setup (baremetal, vsphere, oci, nutanix)
- VIP configuration for HA clusters
- Static networking with NMState
- ISO generation and host discovery
- Role assignment and validation
- Installation monitoring
- Credential retrieval and secure storage
- **18-step guided workflow** with human-in-the-loop at critical points

**Available Tools** (11 total):
- `list_versions` - List available OpenShift versions
- `create_cluster` - Create cluster definition
- `cluster_info` - Get cluster details and status
- `set_cluster_vips` - Configure API and Ingress VIPs
- `set_host_role` - Assign master/worker roles to hosts
- `cluster_iso_download_url` - Get discovery ISO URL
- `install_cluster` - Start cluster installation
- `cluster_credentials_download_url` - Download kubeconfig and credentials
- `generate_nmstate_yaml` - Generate NMState network configuration
- `validate_nmstate_yaml` - Validate network configuration
- `alter_static_network_config_nmstate_for_host` - Apply static networking to hosts

**Documentation**:
- [Input Validation Guide](docs/input-validation-guide.md) - Parameter requirements
- [Providers](docs/providers.md) - Infrastructure providers (baremetal, vsphere, oci, nutanix)
- [Platforms](docs/platforms.md) - OpenShift types (SNO, OCP, ROSA, ARO, OSD)
- [Networking](docs/networking.md) - Network configuration, VIPs, CIDR planning
- [Static Networking Guide](docs/static-networking-guide.md) - NMState configuration
- [Host Requirements](docs/host-requirements.md) - Hardware specifications
- [Examples](docs/examples.md) - 10 real-world configurations
- [Troubleshooting](docs/troubleshooting.md) - Common errors and solutions
- [INDEX.md](docs/INDEX.md) - Complete documentation navigation

### 2. **cluster-inventory** - Cluster Discovery and Status

List and inspect ALL OpenShift cluster types with comprehensive status information.

**Use when**:
- "List my OpenShift clusters"
- "Show cluster status"
- "Get details about cluster [name]"
- "What clusters are installing?"
- "Show all my clusters" (self-managed and managed services)

**MCP Server**: `openshift-installer` (Dual API: Assisted Service + OCM)

**What it does**:
- **Dual API Query**: Queries both Assisted Installer and OCM APIs
- Lists self-managed clusters (OCP, SNO) from Assisted Installer
- Lists managed service clusters (ROSA, ARO, OSD) from OCM
- Merges and normalizes results into unified view
- Shows cluster status and installation progress
- Provides detailed cluster events and validation errors (Assisted Installer only)
- Read-only operations (safe for continuous monitoring)

**Supported Cluster Types**:
- **Self-Managed**: OCP (OpenShift Container Platform), SNO (Single-Node OpenShift)
- **Managed Services**: ROSA (Red Hat OpenShift Service on AWS), ARO (Azure Red Hat OpenShift), OSD (OpenShift Dedicated)

### 3. **cluster-report** - Multi-Cluster Health Reporting

Generate consolidated health reports across multiple OpenShift clusters.

**Use when**:
- "Generate a health report for all my clusters"
- "Show resource usage across clusters"
- "List pods with issues in the fleet"
- "What's the GPU allocation across clusters?"

**MCP Server**: `openshift` (OpenShift MCP Server)

**What it does**:
- Aggregates metrics from multiple clusters
- Reports CPU, memory, GPU usage
- Identifies failed pods and attention items
- Provides per-cluster and fleet-wide summaries
- Supports 10–100+ clusters via service account tokens

**Helper Scripts**:
- `assemble.py` - Resolves file references and loads MCP output
- `aggregate.py` - Computes metrics and identifies issues

---

## Multi-Cluster Authentication

For running `cluster-report` across many clusters (10–100+), use service account tokens instead of interactive `oc login`. This avoids repeated browser-based OAuth sessions and produces non-expiring tokens.

| Script / Manifest | Purpose |
|-------------------|---------|
| [`build-kubeconfig.py`](scripts/cluster-report/build-kubeconfig.py) | Builds merged kubeconfig from SA tokens (`setup` + `build` subcommands) |
| [`cluster-reporter-rbac.yaml`](scripts/cluster-report/cluster-reporter-rbac.yaml) | Read-only RBAC resources (ClusterRole, ClusterRoleBinding) |

> **Required permissions**: The RBAC setup creates cluster-scoped resources, so the user running `setup` needs `cluster-admin` privileges. This is a one-time step per cluster. If RBAC has already been applied, use `--skip-rbac`.

**Quick start**:

```bash
# 1. One-time setup (requires cluster-admin): apply RBAC and extract tokens
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py setup --all-contexts

# If RBAC is already configured, skip the apply step
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py setup --all-contexts --skip-rbac

# 2. Build merged kubeconfig from saved tokens
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py \
  build --clusters ~/.ocp-clusters/clusters.json --verify

# 3. Export and run
export KUBECONFIG=/tmp/cluster-report-kubeconfig
# In Claude Code: /cluster-report
```

See [docs/multi-cluster-auth.md](docs/multi-cluster-auth.md) for the full setup guide, token rotation, and troubleshooting.

---

## MCP Server Integration

The pack integrates with two MCP servers for comprehensive cluster management:

### **openshift-installer** - Assisted Service MCP Server

Provides access to Red Hat Assisted Installer API for cluster lifecycle operations.

**Repository**: https://github.com/openshift-assisted/assisted-service-mcp

**Technology**: Python with `uv` runtime

**Available Tools**: 15+ tools across categories:
- **Cluster Management**: list_clusters, cluster_info, create_cluster, install_cluster, set_cluster_vips
- **Host Management**: set_host_role
- **Networking**: generate_nmstate_yaml, validate_nmstate_yaml, alter_static_network_config_nmstate_for_host
- **Downloads**: cluster_iso_download_url, cluster_credentials_download_url
- **Events**: cluster_events, host_events
- **Versions**: list_versions, list_operator_bundles
- **Operators**: add_operator_bundle_to_cluster

**Configuration** (in `mcps.json`):
```json
{
  "mcpServers": {
    "openshift-installer": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/assisted-service-mcp",
        "run",
        "mcp",
        "run",
        "/path/to/assisted-service-mcp/assisted_service_mcp/src/main.py"
      ],
      "env": {
        "OFFLINE_TOKEN": "${OFFLINE_TOKEN}"
      },
      "description": "Red Hat Assisted Installer MCP server for cluster creation and management",
      "security": {
        "credentials": "env-only"
      }
    }
  }
}
```

**Key Configuration Notes**:
- Uses `uv` for Python environment management (faster than pip/virtualenv)
- Requires `OFFLINE_TOKEN` from https://cloud.redhat.com/openshift/token
- Communicates with Red Hat Hybrid Cloud Console APIs
- No container required (pure Python STDIO transport)

### **openshift** - OpenShift MCP Server

Provides access to Kubernetes/OpenShift cluster operations for multi-cluster management.

**Repository**: https://github.com/openshift/openshift-mcp-server

**Technology**: Go binary in container

**Enabled Toolsets**: `core` and `config` (via `--toolsets core,config`)

**Available Tools**:
- **Resources**: resources_list, resources_get, resources_create_or_update, resources_delete
- **Pods**: pods_list, pods_get, pods_log, pods_exec, pods_top
- **Nodes**: nodes_top, nodes_log, nodes_stats_summary
- **Namespaces**: namespaces_list, projects_list
- **Events**: events_list

**Configuration** (in `mcps.json`):
```json
{
  "mcpServers": {
    "openshift": {
      "command": "bash",
      "args": [
        "-c",
        "U=(); [ \"$(uname -s)\" = Linux ] && U=(--userns=keep-id:uid=65532,gid=65532); exec podman run \"${U[@]}\" --rm -i --network=host -v \"${KUBECONFIG}:/kubeconfig:ro,Z\" --entrypoint /app/kubernetes-mcp-server quay.io/ecosystem-appeng/openshift-mcp-server:latest --kubeconfig /kubeconfig --read-only --toolsets core,config"
      ],
      "env": {
        "KUBECONFIG": "${KUBECONFIG}"
      },
      "description": "Red Hat OpenShift MCP server for multi-cluster administration and reporting",
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only"
      }
    }
  }
}
```

**Key Configuration Notes**:
- Uses Podman to run container image `quay.io/ecosystem-appeng/openshift-mcp-server:latest`
- `--userns=keep-id:uid=65532,gid=65532` - Rootless container security (Linux only)
- Mounts `KUBECONFIG` as read-only with `,Z` for SELinux labeling
- `--read-only` - Enforces read-only operations (safe for reporting)
- `--toolsets core,config` - Enables Kubernetes core and config operations
- `--network=host` - Required for local/remote cluster access

> **Container UID mapping**: On Linux, the MCP server automatically adds `--userns=keep-id:uid=65532,gid=65532` to map the host user to the container's non-root UID (65532), allowing the container to read `chmod 600` files like `KUBECONFIG` without weakening file permissions. On macOS the flag is omitted automatically since Podman runs inside a VM where `--userns` can cause startup failures.

---

## Sample Workflows

### Workflow 1: Create Single-Node Cluster

```
User: "Create a single-node OpenShift cluster for edge deployment"
→ cluster-creator skill guides through:
  - Cluster name, domain, version selection
  - SSH key configuration
  - ISO generation
  - Host discovery and validation
  - Installation monitoring
  - Credential download

Result: Fully operational SNO cluster in ~45 minutes
```

### Workflow 2: Create HA Cluster with Static IPs

```
User: "Create a 3-master, 2-worker cluster on bare metal with static IPs"
→ cluster-creator skill configures:
  - HA cluster type
  - VIP addresses (API + Ingress)
  - Static networking (NMState YAML per host)
  - Host role assignment
  - Installation with validation

Result: Production HA cluster with static networking
```

### Workflow 3: Multi-Cluster Health Report

```
User: "Generate a health report for all my clusters"
→ cluster-report skill:
  - Connects to all clusters in KUBECONFIG
  - Gathers metrics (CPU, memory, GPU, pods)
  - Identifies issues (high utilization, failed pods)
  - Produces consolidated report

Result: Fleet-wide health summary with attention items
```

### Workflow 4: Check Cluster Installation Progress

```
User: "What's the status of my cluster installation?"
→ cluster-inventory skill:
  - Lists all clusters
  - Shows installation progress
  - Displays recent events
  - Reports validation errors (if any)

Result: Real-time installation status without leaving Claude
```

---

## Documentation

The pack includes 17 comprehensive reference documents covering all aspects of OpenShift administration:

### Installation & Planning
- [Input Validation Guide](docs/input-validation-guide.md) - Parameter validation rules
- [Providers](docs/providers.md) - Infrastructure providers (baremetal, vsphere, oci, nutanix)
- [Platforms](docs/platforms.md) - OpenShift platform types (SNO, OCP, ROSA, ARO, OSD)
- [Host Requirements](docs/host-requirements.md) - Hardware specifications
- [Networking](docs/networking.md) - Network configuration, VIPs, CIDR planning, Egress IP, Multus, SR-IOV, Dual-Stack
- [Static Networking Guide](docs/static-networking-guide.md) - NMState configuration (Simple/Advanced/Manual modes)
- [Storage](docs/storage.md) - Storage options, CSI drivers, ODF
- [Examples](docs/examples.md) - 10 real-world cluster configurations

### Post-Installation
- [Credentials Management](docs/credentials-management.md) - Authentication, OAuth, RBAC, identity providers
- [Multi-Cluster Authentication](docs/multi-cluster-auth.md) - Service account tokens, kubeconfig merging
- [Day-2 Operations](docs/day-2-operations.md) - Monitoring, logging, updates, scaling, maintenance
- [Certificate Management](docs/certificate-management.md) - Certificate lifecycle and rotation
- [Backup and Restore](docs/backup-restore.md) - etcd backup/restore procedures

### Reference & Troubleshooting
- [Quick Reference](docs/quick-reference.md) - Common `oc` commands and scenarios
- [Troubleshooting](docs/troubleshooting.md) - Common errors and resolutions
- [INDEX.md](docs/INDEX.md) - Complete documentation navigation
- [TODO_LIST.md](docs/TODO_LIST.md) - Future documentation topics

**All documentation**:
- Derived from official Red Hat sources
- Optimized for AI context usage (concise)
- Production-ready examples (no toy code)
- Comprehensive cross-references
- Validated against OpenShift 4.18

---

## Troubleshooting

### MCP Server Won't Start (openshift-installer)

**Problem**: Server fails to connect or times out

**Solutions**:
1. Verify `uv` is installed: `uv --version`
2. Check OFFLINE_TOKEN is set: `echo "OFFLINE_TOKEN is ${OFFLINE_TOKEN:+set}"`
3. Verify path in `mcps.json` points to your local `assisted-service-mcp` clone
4. Test manually:
   ```bash
   cd /path/to/assisted-service-mcp
   OFFLINE_TOKEN="your-token" uv run assisted_service_mcp.src.main
   ```
5. Check network connectivity to cloud.redhat.com

### MCP Server Won't Start (openshift)

**Problem**: Container fails to start or can't access cluster

**Solutions**:
1. Verify KUBECONFIG is set: `echo $KUBECONFIG`
2. Test cluster access: `oc get nodes` or `kubectl get nodes`
3. Check container image exists: `podman images | grep openshift-mcp-server`
4. Verify SELinux context on kubeconfig file (Linux): `ls -Z $KUBECONFIG`
5. Test container manually:
   ```bash
   podman run --rm -i --network=host \
     -v "${KUBECONFIG}:/kubeconfig:ro,Z" \
     quay.io/ecosystem-appeng/openshift-mcp-server:latest \
     --kubeconfig /kubeconfig --read-only --toolsets core,config
   ```

### Cluster Creation Fails

**Problem**: Cluster stays in "insufficient" or validation error state

**Solutions**:
1. Check host requirements match cluster type (SNO vs HA)
2. Verify VIPs are in same subnet as nodes
3. Review cluster events: Use `cluster-inventory` skill
4. Check troubleshooting guide: [docs/troubleshooting.md](docs/troubleshooting.md)
5. Verify network connectivity between hosts

### Skills Not Triggering

**Problem**: Skills don't activate on expected queries

**Solutions**:
1. Verify plugin installed: `claude plugin list`
2. Reload Claude Code to refresh plugins
3. Check skill descriptions match query intent
4. Use explicit phrasing from skill examples

---

## Architecture Reference

### Directory Structure

```
ocp-admin/
├── README.md                    # This file
├── mcps.json                    # MCP server configurations
├── docs/                        # Comprehensive reference documentation (17 files)
│   ├── INDEX.md                 # Master documentation navigation
│   ├── input-validation-guide.md
│   ├── providers.md
│   ├── platforms.md
│   ├── networking.md
│   ├── static-networking-guide.md
│   ├── host-requirements.md
│   ├── storage.md
│   ├── examples.md
│   ├── credentials-management.md
│   ├── multi-cluster-auth.md
│   ├── day-2-operations.md
│   ├── certificate-management.md
│   ├── backup-restore.md
│   ├── quick-reference.md
│   ├── troubleshooting.md
│   └── TODO_LIST.md
├── skills/
│   ├── cluster-creator/SKILL.md      # End-to-end cluster deployment
│   ├── cluster-inventory/SKILL.md    # Cluster discovery and status
│   └── cluster-report/SKILL.md       # Multi-cluster health reporting
└── scripts/
    └── cluster-report/
        ├── build-kubeconfig.py       # Multi-cluster authentication
        ├── cluster-reporter-rbac.yaml
        ├── assemble.py               # MCP output assembly
        └── aggregate.py              # Metrics aggregation
```

*Optional:* `.claude-plugin/plugin.json` — only if publishing via Claude Code’s plugin format; not required for [Lola](https://github.com/RedHatProductSecurity/lola) install.

### Key Patterns

- **Skills encapsulate operations** - Each skill handles one category of cluster tasks
- **Complete lifecycle coverage** - Create → Configure → Monitor → Operate
- **Dual MCP integration** - Assisted Installer (creation) + OpenShift (operations)
- **Environment-based auth** - OFFLINE_TOKEN (Assisted Installer) + KUBECONFIG (cluster ops)
- **Human-in-the-loop** - User approval required before critical operations
- **Comprehensive documentation** - 17 reference docs covering all aspects
- **Production-ready** - Real examples, validation, error handling

---

## Security Model

**Assisted Installer access**:
- Uses OFFLINE_TOKEN for Red Hat Hybrid Cloud Console authentication
- Token scoped to user's Red Hat account
- No credential storage or caching
- All operations audited in Red Hat console

**Cluster access**:
- Uses KUBECONFIG for Kubernetes authentication
- Respects Kubernetes RBAC permissions
- ServiceAccount-based authorization for multi-cluster
- Read-only operations by default (cluster-report)

---

## Development

See main repository [README.md](../README.md) for:
- Adding new skills
- Creating agents
- Integrating MCP servers
- Testing and validation

---

## License

[Apache 2.0](../LICENSE)

---

## References

- [OpenShift Container Platform Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18)
- [Assisted Installer Documentation](https://docs.redhat.com/en/documentation/assisted_installer_for_openshift_container_platform/)
- [Assisted Service MCP Server](https://github.com/openshift-assisted/assisted-service-mcp)
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Main Repository](https://github.com/RHEcosystemAppEng/agentic-collections)

# OpenShift Administration Agentic Pack

Administration and management tools for OpenShift Container Platform. This pack provides automation capabilities for cluster management, workload orchestration, security policies, and operational tasks.

**Persona**: OpenShift Administrator
**Marketplaces**: Claude Code, Cursor

## Skills

| Command | Description |
| ------- | ----------- |
| `/cluster-report` | Generate a consolidated health report across multiple OpenShift clusters (nodes, CPU, memory, GPUs, namespaces, pods) |

## Prerequisites

- OpenShift cluster access via `KUBECONFIG`
- For multi-cluster reports, a kubeconfig with multiple contexts

## Multi-Cluster Authentication

For running `cluster-report` across many clusters (10–100+), use service account tokens instead of interactive `oc login`. This avoids repeated browser-based OAuth sessions and produces non-expiring tokens.

| Script / Manifest | Purpose |
|-------------------|---------|
| [`build-kubeconfig.py`](scripts/cluster-report/build-kubeconfig.py) | Builds a merged kubeconfig from SA tokens (`setup` + `build` subcommands) |
| [`cluster-reporter-rbac.yaml`](scripts/cluster-report/cluster-reporter-rbac.yaml) | Read-only RBAC resources applied once per cluster |

> **Required permissions**: The RBAC setup creates cluster-scoped resources (ClusterRole, ClusterRoleBinding), so the user running `setup` needs `cluster-admin` privileges. This is a one-time step per cluster. If RBAC has already been applied, use `--skip-rbac` to skip the apply step and only extract existing SA tokens.

**Quick start:**

```bash
# 1. One-time (requires cluster-admin): apply RBAC and extract tokens for all clusters you're logged into
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py setup --all-contexts

# If RBAC is already configured, skip the apply step and only extract tokens
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py setup --all-contexts --skip-rbac

# 2. Build merged kubeconfig from saved tokens
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py \
  build --clusters ~/.ocp-clusters/clusters.json --verify

# 3. Export and run
export KUBECONFIG=/tmp/cluster-report-kubeconfig
# In Claude Code: /cluster-report
```

See [docs/multi-cluster-auth.md](docs/multi-cluster-auth.md) for the full setup guide, token rotation, and troubleshooting.

## Helper Scripts

The `cluster-report` skill uses two Python scripts (stdlib only, no dependencies) in `scripts/cluster-report/`:

| Script | Purpose |
|--------|---------|
| `assemble.py` | Resolves `$file` references in the manifest JSON, loading persisted MCP output from disk into a complete data structure. With `--aggregate`, pipes into `aggregate.py` automatically. |
| `aggregate.py` | Computes per-cluster and fleet-wide metrics (CPU/memory usage, pod status counts, GPU totals, top namespaces) and flags attention items (>85% utilization, failed pods, missing metrics). |

Both scripts read from stdin and write to stdout. They are invoked as a pipeline by the skill and should be treated as black boxes.

## MCP Servers

- **openshift** - OpenShift cluster management with multi-cluster support

> **Container UID mapping**: On Linux, the MCP server automatically adds `--userns=keep-id:uid=65532,gid=65532` to map the host user to the container's non-root UID (65532), allowing the container to read `chmod 600` files like `KUBECONFIG` without weakening file permissions. On macOS the flag is omitted automatically since Podman runs inside a VM where `--userns` can cause startup failures.

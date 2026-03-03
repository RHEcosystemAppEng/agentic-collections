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

## Helper Scripts

The `cluster-report` skill uses two Python scripts (stdlib only, no dependencies) in `scripts/cluster-report/`:

| Script | Purpose |
|--------|---------|
| `assemble.py` | Resolves `$file` references in the manifest JSON, loading persisted MCP output from disk into a complete data structure. With `--aggregate`, pipes into `aggregate.py` automatically. |
| `aggregate.py` | Computes per-cluster and fleet-wide metrics (CPU/memory usage, pod status counts, GPU totals, top namespaces) and flags attention items (>85% utilization, failed pods, missing metrics). |

Both scripts read from stdin and write to stdout. They are invoked as a pipeline by the skill and should be treated as black boxes.

## MCP Servers

- **openshift** - OpenShift cluster management with multi-cluster support

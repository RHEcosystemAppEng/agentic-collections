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

## MCP Servers

- **openshift** - OpenShift cluster management with multi-cluster support

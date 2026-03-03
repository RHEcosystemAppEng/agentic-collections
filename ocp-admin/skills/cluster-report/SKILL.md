---
name: cluster-report
description: |
  Generate a consolidated health report across multiple OpenShift clusters.
  Collects node resources (CPU, memory, GPUs), namespace counts, and pod
  status from all kubeconfig contexts into a single comparison view.
  Use when:
  - "Show me a report across all clusters"
  - "Compare cluster health"
  - "Multi-cluster status overview"
  - "How are my clusters doing?"
  NOT for single-cluster deep-dives or troubleshooting specific pods.
model: inherit
color: cyan
metadata:
  user_invocable: "true"
---

# Multi-Cluster Report Skill

Generate a unified health and resource report across multiple OpenShift/Kubernetes clusters using the OpenShift MCP server's multi-cluster capabilities.

## Prerequisites

**Required MCP Servers**: `openshift` (configured in [.mcp.json](../../.mcp.json))

**Required MCP Tools** (all from `openshift` server):
- `configuration_contexts_list` - Discover available cluster contexts
- `nodes_top` - Node CPU and memory consumption
- `resources_list` - List Kubernetes resources (used for Node specs and GPU detection)
- `namespaces_list` - List namespaces per cluster
- `projects_list` - List OpenShift projects per cluster
- `pods_list` - List pods with status information

**Required Environment Variables**:
- `KUBECONFIG` - Path to kubeconfig file containing multi-cluster contexts

**Multi-Cluster Requirement**: The kubeconfig must contain at least one context. For meaningful comparison, two or more cluster contexts are recommended.

### Prerequisite Validation

**CRITICAL**: Before executing any operations, validate the environment in Step 0.

## When to Use This Skill

**Use this skill when**:
- Comparing resource utilization across clusters
- Getting a fleet-wide overview of cluster health
- Checking GPU availability across clusters
- Auditing namespace and pod counts across environments
- Preparing capacity planning reports

**Do NOT use this skill when**:
- Debugging a specific pod or workload (use `/debug-pod` instead)
- Managing a single cluster's resources
- Deploying or modifying cluster resources

## Workflow

### Step 0: Validate Environment

**Action**: Verify KUBECONFIG is set and the MCP server is accessible.

```bash
# Check KUBECONFIG is set (NEVER print its value)
if [ -z "$KUBECONFIG" ]; then
  echo "ERROR: KUBECONFIG not set"
else
  echo "OK: KUBECONFIG is configured"
fi
```

**CRITICAL**: Never expose the KUBECONFIG path or its contents to the user. Only confirm it is set.

**Handle validation result**:
- **If KUBECONFIG is set**: Continue to Step 1
- **If KUBECONFIG is not set**: Stop and instruct user:
  ```
  KUBECONFIG environment variable is not set.

  To configure:
    export KUBECONFIG=/path/to/kubeconfig

  For multi-cluster, merge configs:
    export KUBECONFIG=~/.kube/config-cluster1:~/.kube/config-cluster2
  ```

### Step 1: Discover Available Clusters

**MCP Tool**: `configuration_contexts_list` (from openshift)

**Purpose**: List all kubeconfig contexts to identify available clusters.

**Parameters**: None required (discovers all contexts automatically).

**Expected Response**:
```json
[
  {
    "name": "prod-us",
    "cluster": "api-prod-us-example-com:6443",
    "server": "https://api.prod-us.example.com:6443",
    "namespace": "default"
  },
  {
    "name": "dev-eu",
    "cluster": "api-dev-eu-example-com:6443",
    "server": "https://api.dev-eu.example.com:6443",
    "namespace": "default"
  }
]
```

**Verification Checklist**:
- At least one context is returned
- Server URLs are present for each context
- No authentication errors

**Output to user**: Present the discovered clusters and ask for confirmation.

```markdown
## Discovered Clusters

| # | Context Name | Server |
|---|-------------|--------|
| 1 | prod-us     | https://api.prod-us.example.com:6443 |
| 2 | dev-eu      | https://api.dev-eu.example.com:6443 |

Generate report for all clusters, or select specific ones?
```

**WAIT**: Do not proceed until user confirms which clusters to include.

### Step 2: Collect Cluster Data

For **each selected cluster context**, execute the following data collection steps. Pass `context=<context-name>` to every tool call.

#### Step 2a: Node Resources (CPU/Memory)

**MCP Tool**: `nodes_top` (from openshift)

**Parameters**:
```
nodes_top(context="prod-us")
```

**Purpose**: Get CPU and memory consumption for all nodes in the cluster.

**Expected Response**: Table or list of nodes with CPU cores used/allocatable and memory used/allocatable.

**Key Fields to Extract**:
- Node name
- CPU usage (cores) and CPU capacity
- Memory usage (bytes/GiB) and memory capacity
- Node roles (control-plane, worker, infra)

**Error Handling**: If the Metrics Server is not installed, `nodes_top` will fail. In this case:
- Log: `"Cluster <context>: Metrics Server not available — CPU/memory usage data unavailable"`
- Fall back to `resources_list(context=X, apiVersion=v1, kind=Node)` for node count and capacity only (without live usage)
- Mark usage columns as "N/A" in the report

#### Step 2b: GPU Detection

**MCP Tool**: `resources_list` (from openshift)

**Parameters**:
```
resources_list(
  context="prod-us",
  apiVersion="v1",
  kind="Node"
)
```

**Purpose**: Inspect node `.status.allocatable` for GPU resources.

**GPU Detection Logic**:
```
For each node in response:
  Check node.status.allocatable for keys:
    - "nvidia.com/gpu"
    - "amd.com/gpu"
    - "intel.com/gpu"
  If any GPU key exists and value > 0:
    Record: node_name, gpu_type, gpu_count
  Else:
    gpu_count = 0
```

**Note**: This step also provides node capacity data as fallback if Step 2a fails.

#### Step 2c: Namespaces / Projects

**MCP Tool**: `projects_list` (from openshift) — preferred for OpenShift clusters

**Parameters**:
```
projects_list(context="prod-us")
```

**Fallback**: If `projects_list` fails (vanilla Kubernetes cluster), use:
```
namespaces_list(context="prod-us")
```

**Key Fields to Extract**:
- Total count of namespaces/projects
- List of namespace names (for per-namespace pod breakdown)

#### Step 2d: Pod Inventory

**MCP Tool**: `pods_list` (from openshift)

**Parameters**:
```
pods_list(context="prod-us")
```

**Purpose**: Get all pods across all namespaces with their status.

**Key Fields to Extract**:
- Total pod count
- Status breakdown: Running, Pending, Succeeded, Failed, Unknown
- Per-namespace pod counts (top 10 by pod count for the report)

**Pod Status Classification**:
```
Running   → healthy, actively running
Pending   → waiting for scheduling or resources
Succeeded → completed successfully (Jobs/CronJobs)
Failed    → terminated with error
Unknown   → node communication lost
```

### Step 3: Generate Unified Report

Assemble collected data into the consolidated report format below.

**Report Structure**:

```markdown
# Multi-Cluster Report

**Generated**: YYYY-MM-DDTHH:MM:SSZ
**Clusters**: <count> clusters reporting

---

## Cluster Overview

| Cluster | Nodes | CPU (used/total) | Memory (used/total) | GPUs | Projects | Pods (Running/Total) |
|---------|-------|-------------------|---------------------|------|----------|---------------------|
| prod-us | 12    | 48/96 cores (50%) | 192/384 GiB (50%)   | 8    | 45       | 312/320             |
| dev-eu  | 4     | 8/32 cores (25%)  | 32/128 GiB (25%)    | 0    | 12       | 87/92               |
| **Total** | **16** | **56/128 cores (44%)** | **224/512 GiB (44%)** | **8** | **57** | **399/412** |

---

## Per-Cluster Details

### <context-name> (<server-url>)

#### Node Resources

| Node | Role | CPU Used | CPU Total | Memory Used | Memory Total | GPUs |
|------|------|----------|-----------|-------------|--------------|------|
| node-1 | worker | 4 cores | 8 cores | 16 GiB | 32 GiB | 2 |
| node-2 | worker | 3 cores | 8 cores | 12 GiB | 32 GiB | 0 |
| node-3 | control-plane | 2 cores | 4 cores | 8 GiB | 16 GiB | 0 |

#### Pod Status

| Status | Count |
|--------|-------|
| Running | 312 |
| Pending | 5 |
| Succeeded | 0 |
| Failed | 3 |
| Unknown | 0 |

#### Top Namespaces (by pod count)

| Namespace | Pods | Running | Pending | Failed |
|-----------|------|---------|---------|--------|
| openshift-monitoring | 24 | 24 | 0 | 0 |
| my-app-prod | 18 | 17 | 1 | 0 |
| openshift-ingress | 12 | 12 | 0 | 0 |

[Repeat for each cluster]

---

## Attention Required

List any issues detected:
- Clusters with unreachable nodes
- Pods in Failed or Unknown state
- Nodes with CPU or memory usage > 85%
- Pending pods (possible resource constraints)
```

### Step 4: Offer Next Steps

```markdown
## Next Steps

Would you like to:
1. **Drill down** into a specific cluster or namespace
2. **Check alerts** — query Prometheus/Alertmanager for active alerts (requires observability toolset)
3. **Export** this report for sharing
4. **Refresh** — re-run the report with updated data
```

## Dependencies

### Required MCP Servers
- `openshift` - OpenShift MCP server with multi-cluster support enabled

### Required MCP Tools

| Tool | Server | Purpose |
|------|--------|---------|
| `configuration_contexts_list` | openshift | Discover all cluster contexts from kubeconfig |
| `nodes_top` | openshift | Get node CPU/memory metrics from Metrics Server |
| `resources_list` | openshift | List node resources for GPU detection and capacity |
| `namespaces_list` | openshift | List namespaces (Kubernetes fallback) |
| `projects_list` | openshift | List OpenShift projects (preferred) |
| `pods_list` | openshift | List all pods with status across namespaces |

### Related Skills
- None currently (first skill in ocp-admin pack)

### Reference Documentation
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server) - MCP server with multi-cluster support
- [Kubernetes MCP Server Tools](https://github.com/containers/kubernetes-mcp-server#tools) - Full tool reference and multi-cluster configuration

## Error Handling

### Cluster Unreachable

```
Cluster <context-name>: Connection refused

The cluster at <server-url> is not reachable.
Possible causes:
1. Cluster is down or API server unavailable
2. VPN not connected
3. Credentials expired — try: oc login <server-url>

Continuing with remaining clusters...
```

**Behavior**: Skip unreachable cluster, report on remaining clusters. Never fail the entire report due to one cluster being unavailable.

### Metrics Server Not Available

```
Cluster <context-name>: Metrics Server not installed

CPU and memory usage data is unavailable.
Node capacity (allocatable) will be shown instead.

To install Metrics Server:
  oc apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

**Behavior**: Fall back to node capacity from `resources_list`. Mark usage columns as "N/A".

### No GPU Resources

**Behavior**: Display "0" in the GPU column. This is not an error — most clusters do not have GPU nodes.

### Authentication Expired

```
Cluster <context-name>: Authentication failed (401)

Your credentials for this cluster have expired.

To re-authenticate:
  oc login <server-url>

Or refresh your token:
  oc whoami --show-token
```

**Behavior**: Skip cluster with auth failure, report on remaining clusters.

### Empty Cluster

**Behavior**: Report the cluster with all zeros. Do not skip it — an empty cluster is valid data.

## Output Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CLUSTERS_REPORTED` | Number of clusters successfully queried | `2` |
| `CLUSTERS_FAILED` | Number of clusters that failed | `1` |
| `TOTAL_NODES` | Sum of nodes across all clusters | `16` |
| `TOTAL_GPUS` | Sum of GPUs across all clusters | `8` |
| `TOTAL_PODS` | Sum of pods across all clusters | `412` |
| `ALERTS` | List of attention items detected | `["3 failed pods in prod-us"]` |

## Examples

### Example 1: Two-Cluster Report

**User Request**: "Show me a report across all clusters"

**Skill Execution**:
1. Validate KUBECONFIG is set: OK
2. Call `configuration_contexts_list()` — discovers: prod-us, dev-eu
3. Present cluster list, user confirms: "all"
4. For prod-us:
   - `nodes_top(context="prod-us")` — 12 nodes, 48/96 CPU cores
   - `resources_list(context="prod-us", apiVersion="v1", kind="Node")` — 8 GPUs found
   - `projects_list(context="prod-us")` — 45 projects
   - `pods_list(context="prod-us")` — 320 pods (312 Running, 5 Pending, 3 Failed)
5. For dev-eu:
   - `nodes_top(context="dev-eu")` — 4 nodes, 8/32 CPU cores
   - `resources_list(context="dev-eu", apiVersion="v1", kind="Node")` — 0 GPUs
   - `projects_list(context="dev-eu")` — 12 projects
   - `pods_list(context="dev-eu")` — 92 pods (87 Running, 5 Pending)
6. Generate unified report with overview table and per-cluster details
7. Flag: "prod-us: 3 pods in Failed state" in Attention Required section

### Example 2: Single Cluster with Metrics Server Missing

**User Request**: "How are my clusters doing?"

**Skill Execution**:
1. Validate KUBECONFIG is set: OK
2. Call `configuration_contexts_list()` — discovers: staging
3. Present single cluster, user confirms
4. For staging:
   - `nodes_top(context="staging")` — **FAILS**: Metrics Server not installed
   - Fallback: `resources_list(context="staging", apiVersion="v1", kind="Node")` — 3 nodes, capacity: 24 cores, 96 GiB
   - `projects_list(context="staging")` — 8 projects
   - `pods_list(context="staging")` — 45 pods (42 Running, 3 Pending)
5. Generate report with "N/A" for CPU/memory usage, show capacity only
6. Note: "Metrics Server not installed — install for live resource usage data"

### Example 3: Partial Failure

**User Request**: "Compare cluster health"

**Skill Execution**:
1. Call `configuration_contexts_list()` — discovers: prod, staging, dev
2. User confirms all three
3. prod: data collected successfully
4. staging: **connection refused** — cluster unreachable
5. dev: data collected successfully
6. Generate report for prod and dev only
7. Attention Required: "staging: Cluster unreachable — connection refused at https://api.staging.example.com:6443"

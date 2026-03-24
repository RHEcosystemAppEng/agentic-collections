---
name: cluster-report
description: |
  Generate a consolidated health report across multiple OpenShift clusters.
  Verifies each kubeconfig context is a genuine OpenShift cluster before
  reporting. Non-OpenShift contexts are skipped by default.
  Collects node resources (CPU, memory, GPUs), namespace counts, and pod
  status into a single comparison view.
  Use when:
  - "Show me a report across all clusters"
  - "Compare cluster health"
  - "Multi-cluster status overview"
  - "How are my clusters doing?"
  - "Include all clusters including non-OpenShift" (override default filter)
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
- `configuration_contexts_list` — list all kubeconfig contexts and server URLs
- `resources_get` — get a single Kubernetes resource by apiVersion/kind/name
- `nodes_top` — node CPU and memory usage from Metrics Server
- `resources_list` — list Kubernetes resources by apiVersion/kind
- `namespaces_list` — list all namespaces in a cluster
- `projects_list` — list all OpenShift projects
- `pods_list` — list all pods across namespaces

**Required Environment Variables**: `KUBECONFIG` — must contain at least one cluster context. Two or more recommended for comparison.

**Multi-Cluster Setup**: For large-scale deployments using service account tokens instead of interactive `oc login`, see [multi-cluster-auth.md](../../docs/multi-cluster-auth.md) and the [build-kubeconfig.py](../../scripts/cluster-report/build-kubeconfig.py) helper script.

**Helper Scripts** (Python 3, stdlib only — treat as black boxes):
- [`assemble.py`](../../scripts/cluster-report/assemble.py) — resolves `$file` references into complete raw data JSON
- [`aggregate.py`](../../scripts/cluster-report/aggregate.py) — aggregates raw data into structured report JSON

**CRITICAL Script Rules**:
- **NEVER** read the source code of `aggregate.py` or `assemble.py`
- **NEVER** write ad-hoc Python to parse or transform MCP output
- **NEVER** manually reconstruct data already available in MCP output

**Verification Steps:**
1. Confirm `openshift` MCP server is available in `.mcp.json`
2. Verify `KUBECONFIG` is set: `test -n "$KUBECONFIG"` (never expose path or contents)
3. If either check fails → Human Notification Protocol

**Human Notification Protocol:**

When prerequisites fail:
1. **Stop immediately** — do not make any MCP tool calls
2. **Report error:**
   ```
   Cannot execute skill: [specific failure]
   Setup: [instructions + link to .mcp.json or KUBECONFIG docs]
   ```
3. **Request decision:** "How to proceed? (setup/skip/abort)"
4. **Wait for user input**

**Security:** Never display KUBECONFIG path, contents, or any credential values.

## When to Use This Skill

**Use when**:
- Comparing resource utilization across clusters
- Getting a fleet-wide health overview
- Preparing capacity planning reports

**Do NOT use when**:
- Debugging a specific pod or workload (use `/debug-pod`)

## Workflow

### Step 0: Validate Environment

Check that `KUBECONFIG` is set. **Never expose the path or contents** — only confirm it is set. If not set, stop and instruct the user to `export KUBECONFIG=/path/to/kubeconfig`.

### Step 1: Discover and Verify Clusters

#### Step 1a: List Contexts

**MCP Tool**: `configuration_contexts_list`

Collect all context names and server URLs. Do NOT present results to the user yet.

**Expected Output**: List of context names with associated server URLs.

**Error Handling**:
- If no contexts found: Stop and instruct user to verify KUBECONFIG points to a valid file with cluster contexts
- If tool call fails: Report MCP server connectivity issue, suggest checking `.mcp.json` configuration

#### Step 1b: Verify OpenShift Clusters

For **each** context discovered in Step 1a, probe for the OpenShift `ClusterVersion` resource:

**MCP Tool**: `resources_get`

| Parameter | Value |
|---|---|
| `apiVersion` | `config.openshift.io/v1` |
| `kind` | `ClusterVersion` |
| `name` | `version` |
| `context` | `<context-name>` |

**Classification rules**:

| Probe Result | Classification | Default Behavior |
|---|---|---|
| Success (resource returned) | **OpenShift** — extract version from `.status.desired.version` | Include |
| 403 Forbidden | **OpenShift (unverified)** — API group exists, RBAC restricts access | Include (version shown as "unknown") |
| 404 / resource not found | **Non-OpenShift** (vanilla Kubernetes or other distribution) | Exclude |
| Timeout / connection refused / 401 | **Unreachable** | Always exclude |

**Performance**: Issue all `resources_get` calls in parallel (one per context) since they are independent.

#### Step 1c: Present Verification Results

Present a categorized summary to the user:

```markdown
## Cluster Discovery Results

### OpenShift Clusters (will be included in report)

| Context | Server | OpenShift Version |
|---------|--------|-------------------|
| prod-us | https://api.prod-us.example.com:6443 | 4.16.3 |
| staging | https://api.staging.example.com:6443 | 4.15.12 |

### Non-OpenShift Clusters (excluded by default)

| Context | Server | Reason |
|---------|--------|--------|
| dev-k8s | https://dev-k8s.example.com:6443 | No ClusterVersion resource (vanilla Kubernetes) |

### Unreachable Clusters (excluded)

| Context | Server | Error |
|---------|--------|-------|
| old-cluster | https://old.example.com:6443 | Connection refused |

**Proceeding with 2 OpenShift clusters.** To include non-OpenShift clusters, say "include all clusters".
```

**Presentation rules**:
- Omit any section that has no entries (e.g., skip "Non-OpenShift" section if all contexts are OpenShift).
- If ALL contexts are OpenShift, simplify to: "All N contexts are verified OpenShift clusters."
- If ALL contexts are non-OpenShift, inform the user: "No OpenShift clusters found. To include non-OpenShift clusters, say 'include all clusters'."

**User override handling**:

If the user responds with "include all clusters", "include non-OpenShift", "report on all clusters", or any clear intent to include non-OpenShift contexts, add them back into the selected set. Unreachable clusters are always excluded.

If the user's **original prompt** (before the skill started) already contains phrases like "all clusters", "including non-OpenShift", or "all contexts", pre-select the override and present verification results as: "Including all clusters as requested."

Proceed automatically with the discovered OpenShift clusters unless the user explicitly requests changes.

### Step 2: Collect Cluster Data

For each selected cluster, pass `context=<context-name>` to every tool call. Collect data using:

| Manifest Key | MCP Tool | Extra Parameters | Fallback |
|---|---|---|---|
| `nodes_top` | `nodes_top` | — | Set null if Metrics Server unavailable |
| `nodes_list` | `resources_list` | `apiVersion=v1`, `kind=Node` | — |
| `projects` | `projects_list` | — | Use `namespaces_list` if fails |
| `pods` | `pods_list` | — | — |

**Error policy**: Skip unreachable clusters. Set failed fields to `null` and append the error to the cluster's `errors` array. Never abort the entire report.

#### Persist MCP Output to Files

For each MCP tool call, **immediately save the output to a file** under `/tmp/cluster-report/`.
This ensures data is available for the assembly pipeline regardless of output size.

**Naming convention**: `/tmp/cluster-report/<context-short>-<field>.txt`

Use a sanitized short name for the context (e.g., `prod-us`, `dev-eu`). Create the directory first:

```bash
mkdir -p /tmp/cluster-report
```

**How to save**: After each MCP tool call, use Bash to write the output to disk. `$file` references
accept **both plain text and JSON files** — no special formatting is required.

If Claude Code auto-persisted the output to a file (shown as `persisted-output` in the tool result),
reference that file path directly.

#### Assemble Manifest

Write the manifest to `/tmp/cluster-report-manifest.json` with `$file` references to the saved files:

```json
{
  "generated_at": "2026-03-03T14:30:00Z",
  "clusters": {
    "<context-name>": {
      "context": "<context-name>",
      "server": "<server-url>",
      "cluster_type": "openshift",
      "openshift_version": "4.16.3",
      "nodes_top": {"$file": "/tmp/cluster-report/<ctx>-nodes_top.txt"} or null,
      "nodes_list": {"$file": "/tmp/cluster-report/<ctx>-nodes_list.txt"} or null,
      "projects": {"$file": "/tmp/cluster-report/<ctx>-projects.txt"} or null,
      "namespaces": {"$file": "/tmp/cluster-report/<ctx>-namespaces.txt"} or null,
      "pods": {"$file": "/tmp/cluster-report/<ctx>-pods.txt"} or null,
      "errors": ["<error messages for failed tools>"]
    }
  }
}
```

**Manifest fields from verification**:
- `cluster_type`: `"openshift"` or `"kubernetes"`. Determined during Step 1b verification.
- `openshift_version`: The OpenShift version string (e.g., `"4.16.3"`) or `null` for non-OpenShift clusters.

Fields may also be inlined as raw text strings or set to `null` for failed/unavailable data.

### Step 3: Aggregate Data

Run the assembly and aggregation pipeline:

```bash
python3 ocp-admin/scripts/cluster-report/assemble.py --aggregate < /tmp/cluster-report-manifest.json
```

If the pipeline exits with code 1, display the error JSON to the user and stop.

### Step 4: Render Report

Render the structured JSON output as markdown using this template:

```markdown
# Multi-Cluster Report

**Generated**: YYYY-MM-DDTHH:MM:SSZ
**Clusters**: <clusters_reported> clusters reporting

---

## Cluster Overview

| Cluster | Version | Nodes | CPU (used/total) | Memory (used/total) | GPUs | Projects | Pods (Running/Total) |
|---------|---------|-------|-------------------|---------------------|------|----------|---------------------|
| prod-us | OCP 4.16.3 | 12 | 48/96 cores (50%) | 192/384 GiB (50%) | 8    | 45       | 312/320             |
| dev-eu  | OCP 4.15.12 | 4  | 8/32 cores (25%)  | 32/128 GiB (25%)  | 0    | 12       | 87/92               |
| **Total** | | **16** | **56/128 cores (44%)** | **224/512 GiB (44%)** | **8** | **57** | **399/412** |

---

## Per-Cluster Details

### <cluster> (<server>) — OpenShift <version>

#### Node Resources

| Node | Role | CPU Used | CPU Total | Memory Used | Memory Total | GPUs |
|------|------|----------|-----------|-------------|--------------|------|
| node-1 | worker | 4 cores | 8 cores | 16 GiB | 32 GiB | 2 |

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

[Repeat for each cluster]

---

## Attention Required

[Render each item from the `attention` array]
```

### Step 5: Offer Next Steps

```markdown
## Next Steps

Would you like to:
1. **Drill down** into a specific cluster or namespace
2. **Check alerts** — query Prometheus/Alertmanager for active alerts
3. **Refresh** — re-run the report with updated data
```

## Dependencies

### Required MCP Servers
- `openshift` — with multi-cluster support enabled

### Required MCP Tools
- `configuration_contexts_list` (from openshift) — list all kubeconfig contexts and server URLs
- `resources_get` (from openshift) — get a single Kubernetes resource by apiVersion/kind/name
  - Parameters: `apiVersion`, `kind`, `name`, `context`
- `nodes_top` (from openshift) — node CPU and memory usage from Metrics Server
  - Parameters: `context`
- `resources_list` (from openshift) — list Kubernetes resources by apiVersion/kind
  - Parameters: `apiVersion`, `kind`, `context`
- `namespaces_list` (from openshift) — list all namespaces in a cluster
  - Parameters: `context`
- `projects_list` (from openshift) — list all OpenShift projects
  - Parameters: `context`
- `pods_list` (from openshift) — list all pods across namespaces
  - Parameters: `context`

### Helper Scripts
- [`ocp-admin/scripts/cluster-report/assemble.py`](../../scripts/cluster-report/assemble.py)
- [`ocp-admin/scripts/cluster-report/aggregate.py`](../../scripts/cluster-report/aggregate.py)

### Related Skills
- None currently

### Reference Documentation
- [OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server)
- [Kubernetes MCP Server Tools](https://github.com/containers/kubernetes-mcp-server#tools)

## Error Handling

| Error | Behavior |
|---|---|
| ClusterVersion probe succeeds | Classify as OpenShift, include by default |
| ClusterVersion probe 404/not found | Classify as non-OpenShift, exclude by default |
| ClusterVersion probe 403 Forbidden | Classify as OpenShift (unverified), include by default with version "unknown" |
| ClusterVersion probe timeout/unreachable | Classify as unreachable, always exclude |
| All contexts are non-OpenShift | Inform user, suggest "include all clusters" override |
| User overrides to include non-OpenShift | Proceed normally; `projects_list` may fail (use `namespaces_list` fallback) |
| Cluster unreachable | Skip, continue with remaining clusters |
| Metrics Server missing | Set `nodes_top` to null, show N/A for CPU/memory usage |
| Auth expired (401) | Skip cluster, suggest: re-run `build-kubeconfig.py build --verify` or `oc login <server-url>` |
| No GPUs found | Display 0 (not an error) |
| Empty cluster | Report with all zeros (valid data) |

## Example Usage

### Multi-Cluster Report (Default: OpenShift Only)

**User**: "Show me a report across all clusters"

**Execution**:
1. Validate KUBECONFIG — OK
2. `configuration_contexts_list()` discovers: prod-us, dev-eu, dev-k8s
3. Verify each context with `resources_get(apiVersion="config.openshift.io/v1", kind="ClusterVersion", name="version", context=<ctx>)`
4. Results: prod-us (OCP 4.16.3), dev-eu (OCP 4.15.12), dev-k8s (non-OpenShift)
5. Present: "2 OpenShift clusters found. dev-k8s excluded (non-OpenShift). Include all?"
6. User confirms default selection
7. Collect data for prod-us and dev-eu only
8. Write manifest with `cluster_type` and `openshift_version` fields
9. Run `assemble.py --aggregate` pipeline
10. Render report with OpenShift version column
11. Flag attention items

### Multi-Cluster Report (Include All)

**User**: "Report on all my clusters including non-OpenShift"

**Execution**:
1. Validate KUBECONFIG — OK
2. `configuration_contexts_list()` discovers: prod-us, dev-eu, dev-k8s
3. Verify each context (same as above)
4. Results: prod-us (OCP 4.16.3), dev-eu (OCP 4.15.12), dev-k8s (non-OpenShift)
5. User's initial message indicates "include all" — present verification results and confirm
6. User confirms all clusters including dev-k8s
7. Collect data for all three clusters (`projects_list` fails on dev-k8s, falls back to `namespaces_list`)
8. Write manifest; dev-k8s has `cluster_type: "kubernetes"`, `openshift_version: null`
9. Run pipeline, render report
10. dev-k8s shown as "K8s" in version column

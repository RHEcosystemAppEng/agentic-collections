# OpenShift Administration Collection (ocp-admin)

OpenShift administration skills for multi-cluster reporting and health monitoring. Uses OpenShift MCP server in read-only mode.

- **Persona**: OpenShift Administrator
- **Marketplaces**: Claude Code, Cursor

## Prerequisites

### MCP Server

Configure in `ocp-admin/.mcp.json`.

```json { .api }
{
  "mcpServers": {
    "openshift": {
      "command": "bash",
      "args": ["-c", "U=(); [ \"$(uname -s)\" = Linux ] && U=(--userns=keep-id:uid=65532,gid=65532); exec podman run \"${U[@]}\" --rm -i --network=host -v \"${KUBECONFIG}:/kubeconfig:ro,Z\" --entrypoint /app/kubernetes-mcp-server quay.io/ecosystem-appeng/openshift-mcp-server:latest --kubeconfig /kubeconfig --read-only --toolsets core,config"],
      "env": { "KUBECONFIG": "${KUBECONFIG}" },
      "description": "OpenShift MCP server, read-only (toolsets: core,config)",
      "security": { "isolation": "container", "network": "local", "credentials": "env-only" }
    }
  }
}
```

**Note**: `--read-only` flag ensures cluster safety for admin reporting.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `KUBECONFIG` | Kubeconfig containing contexts for all clusters to report on |

**Multi-cluster setup**: For large deployments using service account tokens instead of `oc login`, use:
- `ocp-admin/scripts/cluster-report/build-kubeconfig.py` — builds kubeconfig from service account tokens
- See `ocp-admin/docs/multi-cluster-auth.md` for detailed setup instructions

## Capabilities

### /cluster-report — Multi-Cluster Health Report

Generates a unified health and resource comparison report across multiple OpenShift clusters.

```markdown { .api }
Skill: cluster-report
Invocation: /cluster-report
Model: inherit
Color: cyan (read-only)

Reports per cluster:
  - Node resources: CPU usage, memory usage, GPU count
  - Namespace/project count
  - Pod status breakdown (Running, Pending, Failed, etc.)
  - Cluster identity and OpenShift version

Behavior:
  - Verifies each kubeconfig context is a genuine OpenShift cluster (not plain Kubernetes)
  - Non-OpenShift contexts are SKIPPED by default
  - Override: "Include all clusters including non-OpenShift"

Minimum: 1 cluster context in KUBECONFIG; 2+ recommended for comparison

Use when: "Show me a report across all clusters", "Compare cluster health",
          "Multi-cluster status overview", "How are my clusters doing?"
NOT for: single-cluster deep-dives or troubleshooting specific pods
```

## MCP Tools Used

```python { .api }
# openshift MCP server (read-only, toolsets: core,config)

configuration_contexts_list() -> list[dict]
# List all kubeconfig contexts with server URLs

resources_get(
    apiVersion: str,
    kind: str,
    namespace: str,
    name: str
) -> dict

resources_list(
    apiVersion: str,
    kind: str,
    namespace: str  # OPTIONAL
) -> list[dict]

nodes_top() -> list[dict]
# Node CPU and memory usage from Metrics Server

namespaces_list() -> list[dict]
projects_list() -> list[dict]
pods_list() -> list[dict]
```

## Helper Scripts

Located in `ocp-admin/scripts/cluster-report/`. Treat as black boxes — do NOT read source code.

```python { .api }
# assemble.py — resolves $file references into complete raw data JSON
# Usage: python3 ocp-admin/scripts/cluster-report/assemble.py <raw-data-dir>
# Output: complete-data.json with all MCP responses merged

# aggregate.py — aggregates raw data into structured report JSON
# Usage: python3 ocp-admin/scripts/cluster-report/aggregate.py <complete-data.json>
# Output: structured-report.json for display

# build-kubeconfig.py — builds kubeconfig from service account tokens
# Usage: See ocp-admin/docs/multi-cluster-auth.md
```

**CRITICAL rules for helper scripts:**
- **NEVER** read source code of `aggregate.py` or `assemble.py`
- **NEVER** write ad-hoc Python to parse or transform MCP output
- **NEVER** manually reconstruct data already available in MCP output
- Always pipe MCP output through these scripts

## Multi-Cluster Authentication

For production multi-cluster setups (service accounts instead of interactive `oc login`):

```bash
# Build kubeconfig from service account tokens
python3 ocp-admin/scripts/cluster-report/build-kubeconfig.py \
  --cluster cluster1=https://api.cluster1.example.com:6443 \
  --cluster cluster2=https://api.cluster2.example.com:6443 \
  --token-dir /path/to/tokens/
```

See `ocp-admin/docs/multi-cluster-auth.md` for complete setup instructions.

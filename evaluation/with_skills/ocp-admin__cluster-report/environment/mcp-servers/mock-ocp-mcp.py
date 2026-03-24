#!/usr/bin/env python3

import json
from fastmcp import FastMCP

mcp = FastMCP("openshift")

CONTEXTS = [
    ("prod-us-east", "https://api.prod-us-east.example.com:6443", "OpenShift 4.16.3", 6, "high"),
    ("prod-eu-west", "https://api.prod-eu-west.example.com:6443", "OpenShift 4.15.12", 4, "moderate"),
    ("staging-central", "https://api.staging-central.example.com:6443", "OpenShift 4.16.1", 3, "low"),
    ("dev-k8s", "https://dev-k8s.internal.example.com:6443", "Kubernetes", 2, "low"),
    ("legacy-dc", "https://legacy-dc.example.com:6443", "OpenShift 4.14", 5, "unknown"),
]

UNREACHABLE = {"legacy-dc"}
OPENSHIFT_CONTEXTS = {"prod-us-east", "prod-eu-west", "staging-central", "legacy-dc"}
NON_OPENSHIFT = {"dev-k8s"}


def _check_context(context):
    ctx = (context or "prod-us-east").strip()
    if ctx in UNREACHABLE:
        raise ConnectionError(f"Connection refused to {ctx}")
    valid = {c[0] for c in CONTEXTS}
    if ctx not in valid:
        raise ValueError(f"Unknown context: {ctx}")
    return ctx


def _format_tabular(headers, rows):
    if not headers or not rows:
        return ""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, h in enumerate(headers):
            val = str(row.get(h, ""))
            widths[i] = max(widths[i], len(val))
    lines = []
    header_line = "".join(h.ljust(w + 2) for h, w in zip(headers, widths))
    lines.append(header_line.rstrip())
    for row in rows:
        line = "".join(str(row.get(h, "")).ljust(w + 2) for h, w in zip(headers, widths))
        lines.append(line.rstrip())
    return "\n".join(lines)


# Node data for resources_get (Node kind)
NODE_DATA = {
    "prod-us-east": {
        "node-us-master-1": {
            "metadata": {"name": "node-us-master-1", "labels": {"node-role.kubernetes.io/master": ""}},
            "status": {"allocatable": {"cpu": "4", "memory": "16Gi", "pods": "250"}, "conditions": []},
        },
        "node-us-master-2": {
            "metadata": {"name": "node-us-master-2", "labels": {"node-role.kubernetes.io/master": ""}},
            "status": {"allocatable": {"cpu": "4", "memory": "16Gi", "pods": "250"}, "conditions": []},
        },
        "node-us-master-3": {
            "metadata": {"name": "node-us-master-3", "labels": {"node-role.kubernetes.io/master": ""}},
            "status": {"allocatable": {"cpu": "4", "memory": "16Gi", "pods": "250"}, "conditions": []},
        },
        "node-us-worker-1": {
            "metadata": {"name": "node-us-worker-1", "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {
                "allocatable": {"cpu": "32", "memory": "128Gi", "pods": "250", "nvidia.com/gpu": "4"},
                "conditions": [],
            },
        },
        "node-us-worker-2": {
            "metadata": {"name": "node-us-worker-2", "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {"allocatable": {"cpu": "16", "memory": "64Gi", "pods": "250"}, "conditions": []},
        },
        "node-us-worker-3": {
            "metadata": {"name": "node-us-worker-3", "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {
                "allocatable": {"cpu": "16", "memory": "64Gi", "pods": "250", "nvidia.com/gpu": "4"},
                "conditions": [],
            },
        },
    },
    "prod-eu-west": {
        "node-eu-master-1": {
            "metadata": {"name": "node-eu-master-1", "labels": {"node-role.kubernetes.io/master": ""}},
            "status": {"allocatable": {"cpu": "4", "memory": "16Gi", "pods": "250"}, "conditions": []},
        },
        "node-eu-worker-1": {
            "metadata": {"name": "node-eu-worker-1", "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {"allocatable": {"cpu": "16", "memory": "64Gi", "pods": "250"}, "conditions": []},
        },
        "node-eu-worker-2": {
            "metadata": {"name": "node-eu-worker-2", "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {"allocatable": {"cpu": "16", "memory": "64Gi", "pods": "250"}, "conditions": []},
        },
        "node-eu-worker-3": {
            "metadata": {"name": "node-eu-worker-3", "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {"allocatable": {"cpu": "16", "memory": "64Gi", "pods": "250"}, "conditions": []},
        },
    },
    "staging-central": {
        "node-staging-master-1": {
            "metadata": {"name": "node-staging-master-1", "labels": {"node-role.kubernetes.io/master": ""}},
            "status": {"allocatable": {"cpu": "4", "memory": "16Gi", "pods": "250"}, "conditions": []},
        },
        "node-staging-worker-1": {
            "metadata": {"name": "node-staging-worker-1", "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {"allocatable": {"cpu": "8", "memory": "32Gi", "pods": "250"}, "conditions": []},
        },
        "node-staging-worker-2": {
            "metadata": {"name": "node-staging-worker-2", "labels": {"node-role.kubernetes.io/worker": ""}},
            "status": {"allocatable": {"cpu": "8", "memory": "32Gi", "pods": "250"}, "conditions": []},
        },
    },
    "dev-k8s": {
        "node-dev-1": {
            "metadata": {"name": "node-dev-1", "labels": {"node-role.kubernetes.io/control-plane": ""}},
            "status": {"allocatable": {"cpu": "4", "memory": "8Gi", "pods": "110"}, "conditions": []},
        },
        "node-dev-2": {
            "metadata": {"name": "node-dev-2", "labels": {}},
            "status": {"allocatable": {"cpu": "4", "memory": "8Gi", "pods": "110"}, "conditions": []},
        },
    },
}


@mcp.tool()
def configuration_contexts_list() -> str:
    """List all kubeconfig contexts with server URLs and cluster info."""
    headers = ["CONTEXT", "SERVER", "VERSION", "NODES", "UTILIZATION"]
    rows = [{"CONTEXT": c[0], "SERVER": c[1], "VERSION": c[2], "NODES": str(c[3]), "UTILIZATION": c[4]} for c in CONTEXTS]
    return _format_tabular(headers, rows)


@mcp.tool()
def resources_get(
    apiVersion: str,
    kind: str,
    name: str,
    namespace: str | None = None,
    context: str | None = None,
) -> str:
    """Get a single Kubernetes resource by apiVersion, kind, and name."""
    ctx = _check_context(context)

    if apiVersion == "config.openshift.io/v1" and kind == "ClusterVersion":
        if ctx in NON_OPENSHIFT:
            raise ValueError("ClusterVersion not found (non-OpenShift cluster)")
        versions = {
            "prod-us-east": "4.16.3",
            "prod-eu-west": "4.15.12",
            "staging-central": "4.16.1",
            "legacy-dc": "4.14",
        }
        ver = versions.get(ctx, "4.16.0")
        return f'{{"apiVersion":"config.openshift.io/v1","kind":"ClusterVersion","metadata":{{"name":"version"}},"status":{{"desired":{{"version":"{ver}"}}}}}}'

    if apiVersion == "v1" and kind == "Node":
        nodes = NODE_DATA.get(ctx, {})
        if name not in nodes:
            raise ValueError(f"Node {name} not found")
        return json.dumps(nodes[name])

    raise ValueError(f"Unsupported resource: {apiVersion}/{kind}")


@mcp.tool()
def resources_list(
    apiVersion: str,
    kind: str,
    namespace: str | None = None,
    context: str | None = None,
) -> str:
    """List Kubernetes resources by apiVersion and kind."""
    ctx = _check_context(context)

    if apiVersion == "v1" and kind == "Node":
        nodes = NODE_DATA.get(ctx, {})
        return json.dumps(list(nodes.values()))

    if apiVersion == "v1" and kind == "Namespace":
        return namespaces_list(context=ctx)

    raise ValueError(f"Unsupported list: {apiVersion}/{kind}")


@mcp.tool()
def nodes_top(context: str | None = None) -> str:
    """Return node CPU and memory usage from Metrics Server."""
    ctx = _check_context(context)

    # prod-us-east: node-us-worker-1 (28.4/32=89%, 112.6/128=88%), node-us-worker-3 (14.2/16=89%, 56.8/64=89%)
    if ctx == "prod-us-east":
        rows = [
            {"NAME": "node-us-master-1", "CPU(cores)": "1.2", "MEMORY(bytes)": "4Gi"},
            {"NAME": "node-us-master-2", "CPU(cores)": "1.1", "MEMORY(bytes)": "3.8Gi"},
            {"NAME": "node-us-master-3", "CPU(cores)": "1.0", "MEMORY(bytes)": "3.6Gi"},
            {"NAME": "node-us-worker-1", "CPU(cores)": "28.4", "MEMORY(bytes)": "112.6Gi"},
            {"NAME": "node-us-worker-2", "CPU(cores)": "8.2", "MEMORY(bytes)": "32Gi"},
            {"NAME": "node-us-worker-3", "CPU(cores)": "14.2", "MEMORY(bytes)": "56.8Gi"},
        ]
    elif ctx == "prod-eu-west":
        rows = [
            {"NAME": "node-eu-master-1", "CPU(cores)": "0.8", "MEMORY(bytes)": "3Gi"},
            {"NAME": "node-eu-worker-1", "CPU(cores)": "6.2", "MEMORY(bytes)": "24Gi"},
            {"NAME": "node-eu-worker-2", "CPU(cores)": "5.8", "MEMORY(bytes)": "22Gi"},
            {"NAME": "node-eu-worker-3", "CPU(cores)": "7.1", "MEMORY(bytes)": "28Gi"},
        ]
    elif ctx == "staging-central":
        rows = [
            {"NAME": "node-staging-master-1", "CPU(cores)": "0.5", "MEMORY(bytes)": "2Gi"},
            {"NAME": "node-staging-worker-1", "CPU(cores)": "2.1", "MEMORY(bytes)": "8Gi"},
            {"NAME": "node-staging-worker-2", "CPU(cores)": "1.8", "MEMORY(bytes)": "7Gi"},
        ]
    elif ctx == "dev-k8s":
        rows = [
            {"NAME": "node-dev-1", "CPU(cores)": "1.2", "MEMORY(bytes)": "3Gi"},
            {"NAME": "node-dev-2", "CPU(cores)": "2.0", "MEMORY(bytes)": "5Gi"},
        ]
    else:
        rows = []

    headers = ["NAME", "CPU(cores)", "MEMORY(bytes)"]
    return _format_tabular(headers, rows)


@mcp.tool()
def pods_list(namespace: str | None = None, context: str | None = None) -> str:
    """List pods across namespaces."""
    ctx = _check_context(context)

    if ctx == "prod-us-east":
        rows = [
            {"NAMESPACE": "batch-jobs", "NAME": "data-pipeline-batch-abc", "STATUS": "Failed"},
            {"NAMESPACE": "batch-jobs", "NAME": "data-pipeline-batch-def", "STATUS": "Failed"},
            {"NAMESPACE": "ci-cd", "NAME": "image-builder", "STATUS": "CrashLoopBackOff"},
            {"NAMESPACE": "app-platform", "NAME": "deploy-canary", "STATUS": "Pending"},
            {"NAMESPACE": "default", "NAME": "api-server", "STATUS": "Running"},
            {"NAMESPACE": "default", "NAME": "web-frontend", "STATUS": "Running"},
            {"NAMESPACE": "openshift-monitoring", "NAME": "prometheus-0", "STATUS": "Running"},
        ]
    elif ctx == "prod-eu-west":
        rows = [
            {"NAMESPACE": "security", "NAME": "compliance-scanner-failed", "STATUS": "Failed"},
            {"NAMESPACE": "default", "NAME": "api-eu", "STATUS": "Running"},
        ]
    elif ctx == "staging-central":
        rows = [
            {"NAMESPACE": "staging-apps", "NAME": "image-pull-broken-pod", "STATUS": "ImagePullBackOff"},
            {"NAMESPACE": "default", "NAME": "staging-api", "STATUS": "Running"},
        ]
    elif ctx == "dev-k8s":
        rows = [
            {"NAMESPACE": "default", "NAME": "dev-pod-1", "STATUS": "Running"},
            {"NAMESPACE": "kube-system", "NAME": "coredns-xyz", "STATUS": "Running"},
        ]
    else:
        rows = []

    headers = ["NAMESPACE", "NAME", "STATUS"]
    return _format_tabular(headers, rows)


@mcp.tool()
def projects_list(context: str | None = None) -> str:
    """List OpenShift projects."""
    ctx = _check_context(context)
    if ctx in NON_OPENSHIFT:
        raise ValueError("projects_list is OpenShift-only; use namespaces_list for vanilla Kubernetes")

    counts = {"prod-us-east": 21, "prod-eu-west": 16, "staging-central": 12, "legacy-dc": 8}
    n = counts.get(ctx, 5)
    rows = [{"NAME": f"project-{i}"} for i in range(1, n + 1)]
    headers = ["NAME"]
    return _format_tabular(headers, rows)


@mcp.tool()
def namespaces_list(context: str | None = None) -> str:
    """List all namespaces in a cluster."""
    ctx = _check_context(context)

    if ctx == "dev-k8s":
        # 6 namespaces for vanilla Kubernetes
        rows = [
            {"NAME": "default"},
            {"NAME": "kube-system"},
            {"NAME": "kube-public"},
            {"NAME": "kube-node-lease"},
            {"NAME": "app-dev"},
            {"NAME": "monitoring"},
        ]
    else:
        # OpenShift: projects map to namespaces
        counts = {"prod-us-east": 21, "prod-eu-west": 16, "staging-central": 12}
        n = counts.get(ctx, 5)
        rows = [{"NAME": f"project-{i}"} for i in range(1, n + 1)]

    headers = ["NAME"]
    return _format_tabular(headers, rows)


if __name__ == "__main__":
    mcp.run(transport="stdio")

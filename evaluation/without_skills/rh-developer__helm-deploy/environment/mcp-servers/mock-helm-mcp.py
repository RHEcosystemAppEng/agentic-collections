#!/usr/bin/env python3
"""
Mock Helm MCP Server for rh-developer helm-deploy benchmark task.

Simulates Helm CLI operations for OpenShift deployment planning.
"""

from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("helm")

# Mock data for existing releases
MOCK_RELEASES = [
    {
        "name": "api-service",
        "namespace": "api-platform",
        "revision": 3,
        "updated": "2026-02-15T10:30:00Z",
        "status": "deployed",
        "chart": "api-service-1.2.0",
        "app_version": "1.0.0",
    },
    {
        "name": "web-frontend",
        "namespace": "web-frontend",
        "revision": 1,
        "updated": "2026-02-14T14:20:00Z",
        "status": "deployed",
        "chart": "web-frontend-0.1.0",
        "app_version": "1.0.0",
    },
]

MOCK_CHART_METADATA = {
    "name": "my-app",
    "version": "0.1.0",
    "appVersion": "1.0.0",
    "description": "OpenShift deployment chart for my-app",
    "keywords": ["openshift", "deployment"],
    "maintainers": [{"name": "Red Hat", "email": "openshift@redhat.com"}],
}

MOCK_DEFAULT_VALUES = """replicaCount: 1

image:
  repository: quay.io/example/my-app
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080

route:
  enabled: true
  host: ""

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 256Mi
"""

MOCK_RENDERED_YAML = """---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: my-app
        image: quay.io/example/my-app:latest
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: my-app
---
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: my-app
spec:
  to:
    kind: Service
    name: my-app
  port:
    targetPort: 8080
"""


@mcp.tool
def helm_list(namespace: str) -> dict:
    """List installed Helm releases in a namespace.

    Args:
        namespace: The Kubernetes/OpenShift namespace to list releases from.
    """
    releases = [r for r in MOCK_RELEASES if r["namespace"] == namespace]
    return {
        "releases": releases,
        "count": len(releases),
        "namespace": namespace,
    }


@mcp.tool
def helm_show_chart(chart: str) -> dict:
    """Show chart metadata (name, version, description).

    Args:
        chart: Path to chart directory or chart name (e.g. ./chart or my-chart).
    """
    return {
        "chart": chart,
        "metadata": MOCK_CHART_METADATA,
    }


@mcp.tool
def helm_show_values(chart: str) -> dict:
    """Show default values for a chart.

    Args:
        chart: Path to chart directory or chart name.
    """
    return {
        "chart": chart,
        "values": MOCK_DEFAULT_VALUES,
    }


@mcp.tool
def helm_template(
    release_name: str,
    chart: str,
    namespace: str,
    values: Optional[str] = None,
) -> dict:
    """Render chart templates to YAML with given values.

    Args:
        release_name: Name for the release.
        chart: Path to chart directory.
        namespace: Target namespace.
        values: Optional YAML string of values to override defaults.
    """
    return {
        "release_name": release_name,
        "chart": chart,
        "namespace": namespace,
        "rendered": MOCK_RENDERED_YAML,
    }


@mcp.tool
def helm_install_dry_run(
    release_name: str,
    chart: str,
    namespace: str,
    values: Optional[str] = None,
) -> dict:
    """Simulate helm install (dry-run) to validate before deploying.

    Args:
        release_name: Name for the release.
        chart: Path to chart directory.
        namespace: Target namespace.
        values: Optional YAML string of values to override defaults.
    """
    return {
        "release_name": release_name,
        "chart": chart,
        "namespace": namespace,
        "dry_run": True,
        "status": "would_create",
        "resources": ["Deployment/my-app", "Service/my-app", "Route/my-app"],
    }


@mcp.tool
def helm_status(release_name: str, namespace: str) -> dict:
    """Get status of an installed Helm release.

    Args:
        release_name: Name of the release.
        namespace: The namespace where the release is installed.
    """
    release = next(
        (r for r in MOCK_RELEASES if r["name"] == release_name and r["namespace"] == namespace),
        None,
    )
    if release:
        return {
            "release": release_name,
            "namespace": namespace,
            "status": release,
        }
    return {
        "release": release_name,
        "namespace": namespace,
        "error": f"Release '{release_name}' not found in namespace '{namespace}'",
    }


if __name__ == "__main__":
    mcp.run()

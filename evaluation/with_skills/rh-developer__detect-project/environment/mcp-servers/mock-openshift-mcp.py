#!/usr/bin/env python3
"""
Mock OpenShift MCP Server for rh-developer benchmark task.

Simulates an OpenShift cluster with 3 namespaces, each containing a broken
deployment that requires different debugging skills to diagnose:

  1. api-platform / api-service  (Python FastAPI)
     - S2I build succeeded, pod crashes at runtime
     - Entry point is main.py (not app.py), no gunicorn installed
     - Requires python-s2i-entrypoints.md knowledge

  2. web-frontend / web-frontend (Node.js React)
     - Pod in CrashLoopBackOff, exit code 137 (OOMKilled)
     - Container memory limit 64Mi is too low for Node.js
     - Requires debugging-patterns.md exit code knowledge

  3. order-system / order-service (Java Quarkus)
     - Pod running, Route returns 503
     - Service selector mismatch: app=order-svc vs pod label app=order-service
     - Tekton PipelineRun failed, logs in step-build container
     - Requires debug-network + debug-pipeline knowledge

Also provides application source metadata for image recommendation.
"""

from typing import Optional
from fastmcp import FastMCP

mcp = FastMCP("openshift")


# ---------------------------------------------------------------------------
# Namespace / Project data
# ---------------------------------------------------------------------------

NAMESPACES = [
    {"name": "api-platform", "status": "Active", "labels": {"app-type": "backend"}},
    {"name": "web-frontend", "status": "Active", "labels": {"app-type": "frontend"}},
    {"name": "order-system", "status": "Active", "labels": {"app-type": "backend"}},
]


# ---------------------------------------------------------------------------
# Deployment data
# ---------------------------------------------------------------------------

DEPLOYMENTS = {
    "api-platform": [
        {
            "name": "api-service",
            "namespace": "api-platform",
            "replicas": 1,
            "available_replicas": 0,
            "ready_replicas": 0,
            "image": "image-registry.openshift-image-registry.svc:5000/api-platform/api-service:latest",
            "containers": [
                {
                    "name": "api-service",
                    "image": "image-registry.openshift-image-registry.svc:5000/api-platform/api-service:latest",
                    "resources": {
                        "requests": {"cpu": "100m", "memory": "256Mi"},
                        "limits": {"cpu": "500m", "memory": "512Mi"},
                    },
                    "env": [
                        {"name": "APP_SCRIPT", "value": ""},
                        {"name": "APP_FILE", "value": "main.py"},
                    ],
                }
            ],
            "labels": {"app": "api-service", "deployment": "api-service"},
            "strategy": "RollingUpdate",
            "status": "Available=False (0/1 replicas ready)",
        },
    ],
    "web-frontend": [
        {
            "name": "web-frontend",
            "namespace": "web-frontend",
            "replicas": 1,
            "available_replicas": 0,
            "ready_replicas": 0,
            "image": "image-registry.openshift-image-registry.svc:5000/web-frontend/web-frontend:latest",
            "containers": [
                {
                    "name": "web-frontend",
                    "image": "image-registry.openshift-image-registry.svc:5000/web-frontend/web-frontend:latest",
                    "resources": {
                        "requests": {"cpu": "50m", "memory": "32Mi"},
                        "limits": {"cpu": "200m", "memory": "64Mi"},
                    },
                }
            ],
            "labels": {"app": "web-frontend", "deployment": "web-frontend"},
            "strategy": "RollingUpdate",
            "status": "Available=False (0/1 replicas ready)",
        },
    ],
    "order-system": [
        {
            "name": "order-service",
            "namespace": "order-system",
            "replicas": 1,
            "available_replicas": 1,
            "ready_replicas": 1,
            "image": "image-registry.openshift-image-registry.svc:5000/order-system/order-service:latest",
            "containers": [
                {
                    "name": "order-service",
                    "image": "image-registry.openshift-image-registry.svc:5000/order-system/order-service:latest",
                    "resources": {
                        "requests": {"cpu": "200m", "memory": "512Mi"},
                        "limits": {"cpu": "1", "memory": "1Gi"},
                    },
                    "ports": [{"containerPort": 8080, "protocol": "TCP"}],
                }
            ],
            "labels": {"app": "order-service", "deployment": "order-service"},
            "strategy": "RollingUpdate",
            "status": "Available=True (1/1 replicas ready)",
        },
    ],
}


# ---------------------------------------------------------------------------
# Pod data
# ---------------------------------------------------------------------------

PODS = {
    "api-platform": [
        {
            "name": "api-service-7b8f9d4c5-x2k9m",
            "namespace": "api-platform",
            "status": "CrashLoopBackOff",
            "restart_count": 5,
            "labels": {"app": "api-service", "deployment": "api-service"},
            "containers": [
                {
                    "name": "api-service",
                    "state": "Waiting",
                    "reason": "CrashLoopBackOff",
                    "last_state": {
                        "terminated": {
                            "exit_code": 1,
                            "reason": "Error",
                            "message": "Application exited with error",
                        }
                    },
                    "ready": False,
                    "resources": {
                        "requests": {"cpu": "100m", "memory": "256Mi"},
                        "limits": {"cpu": "500m", "memory": "512Mi"},
                    },
                }
            ],
        },
    ],
    "web-frontend": [
        {
            "name": "web-frontend-6c5d8b7a9-p4n2j",
            "namespace": "web-frontend",
            "status": "CrashLoopBackOff",
            "restart_count": 8,
            "labels": {"app": "web-frontend", "deployment": "web-frontend"},
            "containers": [
                {
                    "name": "web-frontend",
                    "state": "Waiting",
                    "reason": "CrashLoopBackOff",
                    "last_state": {
                        "terminated": {
                            "exit_code": 137,
                            "reason": "OOMKilled",
                            "message": "Container exceeded memory limit",
                        }
                    },
                    "ready": False,
                    "resources": {
                        "requests": {"cpu": "50m", "memory": "32Mi"},
                        "limits": {"cpu": "200m", "memory": "64Mi"},
                    },
                }
            ],
        },
    ],
    "order-system": [
        {
            "name": "order-service-5a4b3c2d1-h7j6k",
            "namespace": "order-system",
            "status": "Running",
            "restart_count": 0,
            "labels": {"app": "order-service", "deployment": "order-service"},
            "containers": [
                {
                    "name": "order-service",
                    "state": "Running",
                    "ready": True,
                    "ports": [{"containerPort": 8080}],
                    "resources": {
                        "requests": {"cpu": "200m", "memory": "512Mi"},
                        "limits": {"cpu": "1", "memory": "1Gi"},
                    },
                }
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Pod logs
# ---------------------------------------------------------------------------

POD_LOGS = {
    "api-service-7b8f9d4c5-x2k9m": (
        "---> Running application from script (app.sh) ...\n"
        "sh: app.sh: No such file or directory\n"
        "---> Trying to run with gunicorn ...\n"
        "Traceback (most recent call last):\n"
        "  File \"/opt/app-root/bin/gunicorn\", line 5, in <module>\n"
        "    from gunicorn.app.wsgiapp import run\n"
        "ModuleNotFoundError: No module named 'gunicorn'\n"
        "---> Trying to run app.py ...\n"
        "Error: Could not find '/opt/app-root/src/app.py'\n"
        "---> Failed to find any valid entry point.\n"
        "     Set the APP_MODULE environment variable to specify your application callable.\n"
        "     Expected one of: app.sh, gunicorn with APP_MODULE, or app.py\n"
    ),
    "web-frontend-6c5d8b7a9-p4n2j": (
        "> react-app@1.0.0 start\n"
        "> node server.js\n"
        "\n"
        "Server starting on port 3000...\n"
        "Loading configuration...\n"
        "Initializing middleware...\n"
        "Killed\n"
    ),
    "order-service-5a4b3c2d1-h7j6k": (
        "__  ____  __  _____   ___  __ ____  ______ \n"
        " --/ __ \\/ / / / _ | / _ \\/ //_/ / / / __/ \n"
        " -/ /_/ / /_/ / __ |/ , _/ ,< / /_/ /\\ \\   \n"
        "--\\___\\_\\____/_/ |_/_/|_/_/|_|\\____/___/   \n"
        "2026-02-15 10:30:15,234 INFO  [io.quarkus] Quarkus 3.8.1 on JVM started in 2.345s.\n"
        "2026-02-15 10:30:15,236 INFO  [io.quarkus] Profile prod activated.\n"
        "2026-02-15 10:30:15,237 INFO  [io.quarkus] Installed features: [cdi, rest, smallrye-health]\n"
        "2026-02-15 10:30:15,238 INFO  [io.quarkus] Listening on: http://0.0.0.0:8080\n"
    ),
}


# ---------------------------------------------------------------------------
# Build data
# ---------------------------------------------------------------------------

BUILDS = {
    "api-platform": [
        {
            "name": "api-service-1",
            "namespace": "api-platform",
            "status": "Complete",
            "source_type": "Git",
            "source_uri": "https://github.com/example/api-service.git",
            "strategy": "Source",
            "builder_image": "image-registry.openshift-image-registry.svc:5000/openshift/python:3.11-ubi9",
            "output_image": "image-registry.openshift-image-registry.svc:5000/api-platform/api-service:latest",
            "duration": "2m15s",
        },
    ],
    "web-frontend": [
        {
            "name": "web-frontend-1",
            "namespace": "web-frontend",
            "status": "Complete",
            "source_type": "Git",
            "source_uri": "https://github.com/example/web-frontend.git",
            "strategy": "Source",
            "builder_image": "image-registry.openshift-image-registry.svc:5000/openshift/nodejs:20-ubi9",
            "output_image": "image-registry.openshift-image-registry.svc:5000/web-frontend/web-frontend:latest",
            "duration": "3m42s",
        },
    ],
    "order-system": [
        {
            "name": "order-service-1",
            "namespace": "order-system",
            "status": "Complete",
            "source_type": "Git",
            "source_uri": "https://github.com/example/order-service.git",
            "strategy": "Source",
            "builder_image": "image-registry.openshift-image-registry.svc:5000/openshift/openjdk-17:ubi9",
            "output_image": "image-registry.openshift-image-registry.svc:5000/order-system/order-service:latest",
            "duration": "4m08s",
        },
    ],
}

BUILD_LOGS = {
    "api-service-1": (
        "===> STEP 1: Fetching source from https://github.com/example/api-service.git\n"
        "Cloning into '/tmp/src'...\n"
        "===> STEP 2: Pulling builder image python:3.11-ubi9\n"
        "===> STEP 3: Running assemble script\n"
        "---> Installing application source ...\n"
        "---> Installing dependencies from requirements.txt ...\n"
        "Collecting fastapi==0.109.0\n"
        "Collecting uvicorn==0.27.0\n"
        "Collecting pydantic==2.5.3\n"
        "Successfully installed fastapi-0.109.0 uvicorn-0.27.0 pydantic-2.5.3\n"
        "---> Assemble script complete.\n"
        "===> STEP 4: Committing image\n"
        "===> STEP 5: Pushing image to image-registry.openshift-image-registry.svc:5000/api-platform/api-service:latest\n"
        "Push successful\n"
    ),
    "web-frontend-1": (
        "===> STEP 1: Fetching source from https://github.com/example/web-frontend.git\n"
        "Cloning into '/tmp/src'...\n"
        "===> STEP 2: Pulling builder image nodejs:20-ubi9\n"
        "===> STEP 3: Running assemble script\n"
        "---> Installing application source ...\n"
        "---> Installing dependencies from package.json ...\n"
        "---> Running build script: npm run build ...\n"
        "---> Build complete.\n"
        "===> STEP 4: Committing image\n"
        "===> STEP 5: Pushing image to image-registry.openshift-image-registry.svc:5000/web-frontend/web-frontend:latest\n"
        "Push successful\n"
    ),
    "order-service-1": (
        "===> STEP 1: Fetching source from https://github.com/example/order-service.git\n"
        "Cloning into '/tmp/src'...\n"
        "===> STEP 2: Pulling builder image openjdk-17:ubi9\n"
        "===> STEP 3: Running assemble script\n"
        "---> Installing application source ...\n"
        "---> Building with Maven ...\n"
        "[INFO] BUILD SUCCESS\n"
        "---> Assemble script complete.\n"
        "===> STEP 4: Committing image\n"
        "===> STEP 5: Pushing image to image-registry.openshift-image-registry.svc:5000/order-system/order-service:latest\n"
        "Push successful\n"
    ),
}


# ---------------------------------------------------------------------------
# Service data
# ---------------------------------------------------------------------------

SERVICES = {
    "api-platform": [
        {
            "name": "api-service",
            "namespace": "api-platform",
            "type": "ClusterIP",
            "cluster_ip": "172.30.45.112",
            "ports": [{"port": 8080, "target_port": 8080, "protocol": "TCP"}],
            "selector": {"app": "api-service"},
        },
    ],
    "web-frontend": [
        {
            "name": "web-frontend",
            "namespace": "web-frontend",
            "type": "ClusterIP",
            "cluster_ip": "172.30.89.201",
            "ports": [{"port": 3000, "target_port": 3000, "protocol": "TCP"}],
            "selector": {"app": "web-frontend"},
        },
    ],
    "order-system": [
        {
            "name": "order-service",
            "namespace": "order-system",
            "type": "ClusterIP",
            "cluster_ip": "172.30.67.55",
            "ports": [{"port": 8080, "target_port": 8080, "protocol": "TCP"}],
            "selector": {"app": "order-svc"},
        },
    ],
}


# ---------------------------------------------------------------------------
# Route data
# ---------------------------------------------------------------------------

ROUTES = {
    "api-platform": [
        {
            "name": "api-service",
            "namespace": "api-platform",
            "host": "api-service-api-platform.apps.cluster.example.com",
            "path": "/",
            "service": "api-service",
            "port": 8080,
            "tls_termination": "edge",
            "status": "Admitted",
        },
    ],
    "web-frontend": [
        {
            "name": "web-frontend",
            "namespace": "web-frontend",
            "host": "web-frontend-web-frontend.apps.cluster.example.com",
            "path": "/",
            "service": "web-frontend",
            "port": 3000,
            "tls_termination": "edge",
            "status": "Admitted",
        },
    ],
    "order-system": [
        {
            "name": "order-service",
            "namespace": "order-system",
            "host": "order-service-order-system.apps.cluster.example.com",
            "path": "/",
            "service": "order-service",
            "port": 8080,
            "tls_termination": "edge",
            "status": "Admitted",
            "conditions": [
                {
                    "type": "Admitted",
                    "status": "True",
                    "message": "Route admitted but backend returns 503 Service Unavailable",
                }
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

EVENTS = {
    "api-platform": [
        {"type": "Normal", "reason": "Created", "object": "Pod/api-service-7b8f9d4c5-x2k9m",
         "message": "Created container api-service"},
        {"type": "Normal", "reason": "Started", "object": "Pod/api-service-7b8f9d4c5-x2k9m",
         "message": "Started container api-service"},
        {"type": "Warning", "reason": "BackOff", "object": "Pod/api-service-7b8f9d4c5-x2k9m",
         "message": "Back-off restarting failed container api-service"},
    ],
    "web-frontend": [
        {"type": "Normal", "reason": "Created", "object": "Pod/web-frontend-6c5d8b7a9-p4n2j",
         "message": "Created container web-frontend"},
        {"type": "Normal", "reason": "Started", "object": "Pod/web-frontend-6c5d8b7a9-p4n2j",
         "message": "Started container web-frontend"},
        {"type": "Warning", "reason": "OOMKilled", "object": "Pod/web-frontend-6c5d8b7a9-p4n2j",
         "message": "Container web-frontend was OOMKilled (exit code 137). Memory limit: 64Mi."},
        {"type": "Warning", "reason": "BackOff", "object": "Pod/web-frontend-6c5d8b7a9-p4n2j",
         "message": "Back-off restarting failed container web-frontend"},
    ],
    "order-system": [
        {"type": "Normal", "reason": "Created", "object": "Pod/order-service-5a4b3c2d1-h7j6k",
         "message": "Created container order-service"},
        {"type": "Normal", "reason": "Started", "object": "Pod/order-service-5a4b3c2d1-h7j6k",
         "message": "Started container order-service"},
        {"type": "Normal", "reason": "Scheduled", "object": "Pod/order-service-5a4b3c2d1-h7j6k",
         "message": "Successfully assigned order-system/order-service-5a4b3c2d1-h7j6k to worker-2"},
        {"type": "Warning", "reason": "FailedPipelineRun", "object": "PipelineRun/order-service-deploy-run-7x2k",
         "message": "PipelineRun failed at task 'integration-test'. Check step-build and step-test containers for logs."},
    ],
}


# ---------------------------------------------------------------------------
# Tekton pipeline data
# ---------------------------------------------------------------------------

PIPELINE_RUNS = {
    "order-system": [
        {
            "name": "order-service-deploy-run-7x2k",
            "namespace": "order-system",
            "pipeline": "order-service-deploy",
            "status": "Failed",
            "start_time": "2026-02-15T09:15:00Z",
            "completion_time": "2026-02-15T09:22:30Z",
            "task_runs": [
                {
                    "name": "order-service-deploy-run-7x2k-build",
                    "task": "build",
                    "status": "Succeeded",
                    "steps": [
                        {"name": "step-git-clone", "status": "Completed", "exit_code": 0},
                        {"name": "step-build", "status": "Completed", "exit_code": 0},
                        {"name": "step-push", "status": "Completed", "exit_code": 0},
                    ],
                },
                {
                    "name": "order-service-deploy-run-7x2k-deploy",
                    "task": "deploy",
                    "status": "Succeeded",
                    "steps": [
                        {"name": "step-deploy", "status": "Completed", "exit_code": 0},
                    ],
                },
                {
                    "name": "order-service-deploy-run-7x2k-integration-test",
                    "task": "integration-test",
                    "status": "Failed",
                    "steps": [
                        {"name": "step-test", "status": "Failed", "exit_code": 1,
                         "log": (
                             "Running integration tests against order-service...\n"
                             "GET https://order-service-order-system.apps.cluster.example.com/api/health\n"
                             "Response: 503 Service Unavailable\n"
                             "FAIL: Health check returned 503, expected 200\n"
                             "Hint: Service endpoint is unreachable. Verify service routing.\n"
                         )},
                    ],
                },
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Application source metadata (for image recommendation)
# ---------------------------------------------------------------------------

APP_SOURCES = {
    "inventory-api": {
        "name": "inventory-api",
        "language": "Python",
        "version": "3.11",
        "framework": "Flask",
        "entry_point": "app.py",
        "dependencies": ["flask==3.0.0", "sqlalchemy==2.0.25", "gunicorn==21.2.0", "psycopg2-binary==2.9.9"],
        "target": "production",
        "has_dockerfile": False,
        "has_tests": True,
        "repo": "https://github.com/example/inventory-api.git",
    },
    "customer-portal": {
        "name": "customer-portal",
        "language": "Node.js",
        "version": "20",
        "framework": "React (Next.js)",
        "entry_point": "server.js",
        "dependencies": ["next@14.1.0", "react@18.2.0", "express@4.18.2"],
        "target": "production",
        "has_dockerfile": False,
        "has_tests": True,
        "repo": "https://github.com/example/customer-portal.git",
    },
    "payment-processor": {
        "name": "payment-processor",
        "language": "Java",
        "version": "17",
        "framework": "Quarkus",
        "entry_point": "src/main/java/com/example/Application.java",
        "build_tool": "Maven",
        "dependencies": ["quarkus-rest", "quarkus-hibernate-orm-panache", "quarkus-jdbc-postgresql"],
        "target": "production",
        "has_dockerfile": False,
        "has_tests": True,
        "repo": "https://github.com/example/payment-processor.git",
        "notes": "Quarkus application. Consider native compilation for production.",
    },
}


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool
def list_projects() -> dict:
    """List all OpenShift projects (namespaces) in the cluster.

    Returns project names, status, and labels.
    """
    return {"projects": NAMESPACES, "count": len(NAMESPACES)}


@mcp.tool
def get_deployments(namespace: str) -> dict:
    """Get deployments in a namespace.

    Args:
        namespace: The OpenShift namespace/project name.
    """
    deps = DEPLOYMENTS.get(namespace, [])
    return {"deployments": deps, "count": len(deps), "namespace": namespace}


@mcp.tool
def get_pods(namespace: str) -> dict:
    """Get pods in a namespace with their status and container details.

    Args:
        namespace: The OpenShift namespace/project name.
    """
    pods = PODS.get(namespace, [])
    return {"pods": pods, "count": len(pods), "namespace": namespace}


@mcp.tool
def pod_logs(pod_name: str, namespace: str, previous: bool = False) -> dict:
    """Get logs from a pod.

    Args:
        pod_name: Name of the pod.
        namespace: The OpenShift namespace/project name.
        previous: If True, get logs from the previous terminated container.
    """
    logs = POD_LOGS.get(pod_name, f"No logs available for pod {pod_name}")
    return {"pod": pod_name, "namespace": namespace, "logs": logs, "previous": previous}


@mcp.tool
def get_builds(namespace: str) -> dict:
    """Get builds in a namespace.

    Args:
        namespace: The OpenShift namespace/project name.
    """
    builds = BUILDS.get(namespace, [])
    return {"builds": builds, "count": len(builds), "namespace": namespace}


@mcp.tool
def get_build_log(build_name: str, namespace: str) -> dict:
    """Get the log output from a build.

    Args:
        build_name: Name of the build (e.g. 'api-service-1').
        namespace: The OpenShift namespace/project name.
    """
    log = BUILD_LOGS.get(build_name, f"No build log found for {build_name}")
    return {"build": build_name, "namespace": namespace, "log": log}


@mcp.tool
def get_services(namespace: str) -> dict:
    """Get services in a namespace with their selectors and ports.

    Args:
        namespace: The OpenShift namespace/project name.
    """
    svcs = SERVICES.get(namespace, [])
    return {"services": svcs, "count": len(svcs), "namespace": namespace}


@mcp.tool
def get_routes(namespace: str) -> dict:
    """Get routes in a namespace.

    Args:
        namespace: The OpenShift namespace/project name.
    """
    routes = ROUTES.get(namespace, [])
    return {"routes": routes, "count": len(routes), "namespace": namespace}


@mcp.tool
def get_events(namespace: str) -> dict:
    """Get events in a namespace.

    Args:
        namespace: The OpenShift namespace/project name.
    """
    events = EVENTS.get(namespace, [])
    return {"events": events, "count": len(events), "namespace": namespace}


@mcp.tool
def get_pipeline_runs(namespace: str) -> dict:
    """Get Tekton PipelineRuns in a namespace.

    Args:
        namespace: The OpenShift namespace/project name.
    """
    runs = PIPELINE_RUNS.get(namespace, [])
    return {"pipeline_runs": runs, "count": len(runs), "namespace": namespace}


@mcp.tool
def get_app_source_info(app_name: str) -> dict:
    """Get detected source information for an application project.

    Returns language, framework, version, dependencies, and deployment target.

    Args:
        app_name: Application name (e.g. 'inventory-api', 'customer-portal', 'payment-processor').
    """
    if app_name in APP_SOURCES:
        return APP_SOURCES[app_name]
    return {"error": f"Application '{app_name}' not found. Available: {list(APP_SOURCES.keys())}"}


@mcp.tool
def list_available_apps() -> dict:
    """List all application projects available for analysis.

    Returns names and basic metadata for applications that need
    image recommendations or deployment planning.
    """
    apps = []
    for name, info in APP_SOURCES.items():
        apps.append({
            "name": name,
            "language": info["language"],
            "version": info["version"],
            "framework": info["framework"],
            "target": info["target"],
        })
    return {"applications": apps, "count": len(apps)}


if __name__ == "__main__":
    mcp.run()

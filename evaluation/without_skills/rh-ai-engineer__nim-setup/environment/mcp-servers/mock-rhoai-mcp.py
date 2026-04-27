#!/usr/bin/env python3
"""Mock RHOAI MCP server for SkillsBench rh-ai-engineer task.

Simulates Red Hat OpenShift AI operations: Data Science Projects,
model serving, data connections, serving runtimes, inference services.

Scenario:
- ml-production: existing project with two broken deployments
  - text-gen-legacy: vLLM OOMKilled (max-model-len=32768 on A10G)
  - nim-llama-prod: NIM failing (Account CR not ready, NGC creds invalid)
- fraud-detection: does not exist yet (agent creates it)
"""

import json
from fastmcp import FastMCP

mcp = FastMCP("rhoai")

# ── In-memory state ──────────────────────────────────────────────────────

PROJECTS = {
    "ml-production": {
        "name": "ml-production",
        "display_name": "ML Production",
        "description": "Production ML workloads",
        "labels": {"opendatahub.io/dashboard": "true"},
        "model_serving_mode": "single",
        "pipeline_server": True,
    },
}

DATA_CONNECTIONS = {
    "ml-production": [
        {
            "name": "prod-model-store",
            "type": "S3",
            "bucket": "ml-models-prod",
            "endpoint": "https://s3.us-east-1.amazonaws.com",
            "region": "us-east-1",
        },
    ],
}

SERVING_RUNTIMES = {
    "__platform_templates__": [
        {
            "name": "vllm-runtime",
            "display_name": "vLLM ServingRuntime for KServe",
            "model_formats": ["vLLM"],
            "requires_instantiation": True,
            "source": "platform-template",
            "api_protocol": "REST",
            "supported_model_formats": [
                {"name": "vLLM", "version": "1", "autoSelect": True}
            ],
        },
        {
            "name": "caikit-tgis-runtime",
            "display_name": "Caikit+TGIS ServingRuntime",
            "model_formats": ["caikit"],
            "requires_instantiation": True,
            "source": "platform-template",
            "api_protocol": "gRPC",
        },
    ],
    "ml-production": [
        {
            "name": "vllm-runtime",
            "display_name": "vLLM ServingRuntime for KServe",
            "model_formats": ["vLLM"],
            "requires_instantiation": False,
            "source": "existing",
            "api_protocol": "REST",
        },
        {
            "name": "nim-serving-runtime",
            "display_name": "NVIDIA NIM ServingRuntime",
            "model_formats": ["NIM"],
            "requires_instantiation": False,
            "source": "nim-account",
            "api_protocol": "REST",
        },
        {
            "name": "ovms-1",
            "display_name": "OpenVINO Model Server",
            "model_formats": ["openvino_ir", "onnx"],
            "requires_instantiation": False,
            "source": "existing",
            "api_protocol": "REST",
        },
    ],
}

INFERENCE_SERVICES = {
    "ml-production": {
        "text-gen-legacy": {
            "name": "text-gen-legacy",
            "namespace": "ml-production",
            "runtime": "vllm-runtime",
            "model_format": "vLLM",
            "storage_uri": "hf://mistralai/Mistral-7B-Instruct-v0.3",
            "display_name": "Mistral 7B Legacy",
            "gpu_count": 1,
            "cpu_request": "4",
            "memory_request": "16Gi",
            "memory_limit": "16Gi",
            "min_replicas": 1,
            "max_replicas": 1,
            "ready": False,
            "url": "",
            "conditions": [
                {
                    "type": "Ready",
                    "status": "False",
                    "reason": "PredictorFailed",
                    "message": "Predictor pod is not ready",
                },
                {
                    "type": "PredictorReady",
                    "status": "False",
                    "reason": "ContainerCrashLoop",
                    "message": "Container kserve-container terminated: "
                    "OOMKilled (exit code 137). 5 restarts.",
                },
                {
                    "type": "IngressReady",
                    "status": "True",
                    "reason": "IngressReady",
                    "message": "Ingress is ready",
                },
            ],
            "age": "3d",
        },
        "nim-llama-prod": {
            "name": "nim-llama-prod",
            "namespace": "ml-production",
            "runtime": "nim-serving-runtime",
            "model_format": "NIM",
            "storage_uri": "nim://meta/llama-3.1-8b-instruct",
            "display_name": "Llama 3.1 8B (NIM)",
            "gpu_count": 1,
            "cpu_request": "4",
            "memory_request": "16Gi",
            "memory_limit": "32Gi",
            "min_replicas": 1,
            "max_replicas": 1,
            "ready": False,
            "url": "",
            "conditions": [
                {
                    "type": "Ready",
                    "status": "False",
                    "reason": "RuntimeNotReady",
                    "message": "ServingRuntime 'nim-serving-runtime' "
                    "is not in ready state",
                },
                {
                    "type": "PredictorReady",
                    "status": "Unknown",
                    "reason": "PodNotCreated",
                    "message": "Predictor pod has not been created. "
                    "Waiting for ServingRuntime to become ready.",
                },
                {
                    "type": "IngressReady",
                    "status": "Unknown",
                    "reason": "PredictorNotReady",
                    "message": "Waiting for predictor to become ready",
                },
            ],
            "age": "1d",
        },
    },
}

DEPLOYED_MODELS = {}

WORKBENCHES = {
    "ml-production": [
        {
            "name": "data-exploration-nb",
            "display_name": "Data Exploration",
            "image": "jupyter-pytorch-ubi9-python-3.9-2024.1",
            "status": "Running",
            "cpu_request": "1",
            "memory_request": "8Gi",
            "gpu_count": 0,
            "pvc_name": "data-exploration-nb-pvc",
            "pvc_size": "20Gi",
            "pvc_access_mode": "ReadWriteOnce",
            "creation": "2026-02-10T09:00:00Z",
        },
        {
            "name": "model-training-nb",
            "display_name": "Model Training",
            "image": "jupyter-pytorch-ubi9-python-3.9-2024.1",
            "status": "Stopped",
            "cpu_request": "4",
            "memory_request": "16Gi",
            "gpu_count": 1,
            "pvc_name": "model-training-nb-pvc",
            "pvc_size": "50Gi",
            "pvc_access_mode": "ReadWriteOnce",
            "creation": "2026-02-15T14:00:00Z",
        },
    ],
}

PIPELINE_SERVERS = {
    "ml-production": {
        "configured": True,
        "data_connection": "prod-model-store",
        "status": "Ready",
        "database": "MariaDB",
    },
}

NOTEBOOK_IMAGES = [
    {"name": "jupyter-pytorch-ubi9-python-3.9-2024.1", "display_name": "PyTorch 2024.1", "packages": ["torch", "transformers"]},
    {"name": "jupyter-tensorflow-ubi9-python-3.9-2024.1", "display_name": "TensorFlow 2024.1", "packages": ["tensorflow"]},
    {"name": "jupyter-datascience-ubi9-python-3.9-2024.1", "display_name": "Standard Data Science", "packages": ["pandas", "scikit-learn"]},
    {"name": "jupyter-minimal-ubi9-python-3.9-2024.1", "display_name": "Minimal Python", "packages": []},
]


# ── Project tools ────────────────────────────────────────────────────────


@mcp.tool()
def list_data_science_projects() -> str:
    """List all RHOAI Data Science Projects on the cluster."""
    projects = []
    for name, proj in PROJECTS.items():
        projects.append({
            "name": name,
            "display_name": proj["display_name"],
            "description": proj.get("description", ""),
            "model_serving_mode": proj.get("model_serving_mode", "not configured"),
        })
    return json.dumps(projects, indent=2)


@mcp.tool()
def create_data_science_project(
    name: str,
    display_name: str,
    description: str = "",
) -> str:
    """Create a new RHOAI Data Science Project (namespace with dashboard labels)."""
    if name in PROJECTS:
        raise ValueError(
            f"Project '{name}' already exists. Choose a different name "
            "or configure the existing project."
        )
    if not name.replace("-", "").replace("_", "").isalnum() or len(name) > 63:
        raise ValueError(
            f"Invalid project name '{name}'. Must be DNS-compatible: "
            "lowercase alphanumeric and hyphens, max 63 chars."
        )

    PROJECTS[name] = {
        "name": name,
        "display_name": display_name,
        "description": description,
        "labels": {"opendatahub.io/dashboard": "true"},
        "model_serving_mode": None,
        "pipeline_server": False,
    }
    DATA_CONNECTIONS[name] = []
    SERVING_RUNTIMES[name] = []
    INFERENCE_SERVICES[name] = {}

    return json.dumps({
        "status": "created",
        "name": name,
        "display_name": display_name,
        "namespace": name,
        "labels": {"opendatahub.io/dashboard": "true"},
    })


@mcp.tool()
def get_project_details(name: str) -> str:
    """Get detailed information about an RHOAI Data Science Project."""
    if name not in PROJECTS:
        raise ValueError(f"Project '{name}' not found")
    proj = PROJECTS[name]
    dc_count = len(DATA_CONNECTIONS.get(name, []))
    isvc_count = len(INFERENCE_SERVICES.get(name, {}))
    return json.dumps({
        "name": proj["name"],
        "display_name": proj["display_name"],
        "description": proj.get("description", ""),
        "labels": proj["labels"],
        "data_connections": dc_count,
        "inference_services": isvc_count,
        "model_serving_mode": proj.get("model_serving_mode"),
        "pipeline_server": proj.get("pipeline_server", False),
    })


@mcp.tool()
def get_project_status(namespace: str) -> str:
    """Get comprehensive status of an RHOAI Data Science Project."""
    if namespace not in PROJECTS:
        raise ValueError(f"Project '{namespace}' not found")
    proj = PROJECTS[namespace]
    dcs = DATA_CONNECTIONS.get(namespace, [])
    isvcs = INFERENCE_SERVICES.get(namespace, {})
    return json.dumps({
        "namespace": namespace,
        "display_name": proj["display_name"],
        "status": "Active",
        "components": {
            "data_connections": len(dcs),
            "inference_services": len(isvcs),
            "model_serving_mode": proj.get("model_serving_mode", "not configured"),
            "pipeline_server": "configured" if proj.get("pipeline_server") else "not configured",
        },
    })


# ── Data connection tools ────────────────────────────────────────────────


@mcp.tool()
def create_s3_data_connection(
    namespace: str,
    name: str,
    bucket: str,
    endpoint: str,
    access_key: str,
    secret_key: str,
    region: str = "",
) -> str:
    """Create an S3-compatible data connection in an RHOAI project."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")

    existing = DATA_CONNECTIONS.get(namespace, [])
    if any(dc["name"] == name for dc in existing):
        raise ValueError(
            f"Data connection '{name}' already exists in namespace '{namespace}'"
        )

    dc = {
        "name": name,
        "type": "S3",
        "bucket": bucket,
        "endpoint": endpoint,
        "region": region,
    }
    DATA_CONNECTIONS.setdefault(namespace, []).append(dc)

    return json.dumps({
        "status": "created",
        "name": name,
        "namespace": namespace,
        "type": "S3",
        "bucket": bucket,
        "endpoint": endpoint,
    })


@mcp.tool()
def list_data_connections(namespace: str) -> str:
    """List data connections in an RHOAI project namespace."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")
    dcs = DATA_CONNECTIONS.get(namespace, [])
    return json.dumps(dcs, indent=2)


# ── Model serving tools ─────────────────────────────────────────────────


@mcp.tool()
def set_model_serving_mode(namespace: str, mode: str) -> str:
    """Enable model serving on a Data Science Project (single or multi mode)."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")
    if mode not in ("single", "multi"):
        raise ValueError(f"Invalid mode '{mode}'. Must be 'single' or 'multi'.")

    PROJECTS[namespace]["model_serving_mode"] = mode

    if not SERVING_RUNTIMES.get(namespace):
        templates = SERVING_RUNTIMES.get("__platform_templates__", [])
        SERVING_RUNTIMES[namespace] = [
            {**t, "requires_instantiation": False, "source": "existing"}
            for t in templates
        ]

    return json.dumps({
        "status": "configured",
        "namespace": namespace,
        "mode": mode,
    })


@mcp.tool()
def list_serving_runtimes(
    namespace: str,
    include_templates: bool = False,
) -> str:
    """List available ServingRuntimes in a namespace."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")

    runtimes = list(SERVING_RUNTIMES.get(namespace, []))
    if include_templates:
        templates = SERVING_RUNTIMES.get("__platform_templates__", [])
        existing_names = {r["name"] for r in runtimes}
        for t in templates:
            if t["name"] not in existing_names:
                runtimes.append(t)

    return json.dumps(runtimes, indent=2)


# ── Inference service tools ──────────────────────────────────────────────


@mcp.tool()
def deploy_model(
    name: str,
    namespace: str,
    runtime: str,
    model_format: str,
    storage_uri: str,
    display_name: str = "",
    min_replicas: int = 1,
    max_replicas: int = 1,
    cpu_request: str = "1",
    cpu_limit: str = "2",
    memory_request: str = "4Gi",
    memory_limit: str = "8Gi",
    gpu_count: int = 0,
) -> str:
    """Deploy an AI/ML model as a KServe InferenceService."""
    if namespace not in PROJECTS:
        raise ValueError(
            f"Namespace '{namespace}' is not a Data Science Project. "
            "Create one via create_data_science_project first."
        )

    ns_runtimes = SERVING_RUNTIMES.get(namespace, [])
    runtime_names = [r["name"] for r in ns_runtimes]
    if runtime not in runtime_names:
        available = ", ".join(runtime_names) or "none"
        raise ValueError(
            f"ServingRuntime '{runtime}' not found in namespace '{namespace}'. "
            f"Available runtimes: {available}"
        )

    endpoint = f"https://{name}-{namespace}.apps.ocp-cluster.example.com"
    isvc = {
        "name": name,
        "namespace": namespace,
        "runtime": runtime,
        "model_format": model_format,
        "storage_uri": storage_uri,
        "display_name": display_name or name,
        "gpu_count": gpu_count,
        "cpu_request": cpu_request,
        "memory_request": memory_request,
        "min_replicas": min_replicas,
        "max_replicas": max_replicas,
        "ready": True,
        "url": endpoint,
        "conditions": [
            {"type": "Ready", "status": "True", "reason": "Ready", "message": ""},
            {"type": "PredictorReady", "status": "True", "reason": "PodReady", "message": ""},
            {"type": "IngressReady", "status": "True", "reason": "IngressReady", "message": ""},
        ],
        "age": "0s",
    }

    INFERENCE_SERVICES.setdefault(namespace, {})[name] = isvc
    DEPLOYED_MODELS[f"{namespace}/{name}"] = isvc

    return json.dumps({
        "status": "deployed",
        "name": name,
        "namespace": namespace,
        "runtime": runtime,
        "endpoint": endpoint,
        "ready": True,
    })


@mcp.tool()
def list_inference_services(
    namespace: str,
    verbosity: str = "standard",
) -> str:
    """List deployed InferenceServices in a namespace."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")

    isvcs = INFERENCE_SERVICES.get(namespace, {})
    results = []
    for isvc_name, isvc in isvcs.items():
        entry = {
            "name": isvc["name"],
            "runtime": isvc["runtime"],
            "ready": isvc["ready"],
            "url": isvc.get("url", ""),
            "age": isvc.get("age", ""),
        }
        if verbosity == "full":
            entry["conditions"] = isvc.get("conditions", [])
            entry["storage_uri"] = isvc.get("storage_uri", "")
            entry["gpu_count"] = isvc.get("gpu_count", 0)
        results.append(entry)

    return json.dumps(results, indent=2)


@mcp.tool()
def get_inference_service(
    name: str,
    namespace: str,
    verbosity: str = "standard",
) -> str:
    """Get detailed status of a specific InferenceService."""
    isvcs = INFERENCE_SERVICES.get(namespace, {})
    if name not in isvcs:
        raise ValueError(
            f"InferenceService '{name}' not found in namespace '{namespace}'"
        )

    isvc = isvcs[name]
    result = {
        "name": isvc["name"],
        "namespace": isvc["namespace"],
        "runtime": isvc["runtime"],
        "model_format": isvc.get("model_format", ""),
        "storage_uri": isvc.get("storage_uri", ""),
        "ready": isvc["ready"],
        "url": isvc.get("url", ""),
        "conditions": isvc.get("conditions", []),
        "gpu_count": isvc.get("gpu_count", 0),
        "replicas": {"min": isvc.get("min_replicas", 1), "max": isvc.get("max_replicas", 1)},
        "resources": {
            "cpu_request": isvc.get("cpu_request", "1"),
            "memory_request": isvc.get("memory_request", "4Gi"),
            "memory_limit": isvc.get("memory_limit", "8Gi"),
        },
        "age": isvc.get("age", ""),
    }
    return json.dumps(result, indent=2)


@mcp.tool()
def get_model_endpoint(name: str, namespace: str) -> str:
    """Get the inference endpoint URL for a deployed model."""
    isvcs = INFERENCE_SERVICES.get(namespace, {})
    if name not in isvcs:
        raise ValueError(
            f"InferenceService '{name}' not found in namespace '{namespace}'"
        )
    isvc = isvcs[name]
    if not isvc["ready"]:
        return json.dumps({
            "name": name,
            "namespace": namespace,
            "endpoint": "",
            "error": "InferenceService is not ready. Check conditions for details.",
        })
    return json.dumps({
        "name": name,
        "namespace": namespace,
        "endpoint": isvc["url"],
    })


# ── Workbench tools ──────────────────────────────────────────────────────


@mcp.tool()
def list_workbenches(namespace: str) -> str:
    """List workbenches (Jupyter notebooks) in a Data Science Project."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")
    wbs = WORKBENCHES.get(namespace, [])
    return json.dumps(wbs, indent=2)


@mcp.tool()
def create_workbench(
    namespace: str,
    name: str,
    display_name: str = "",
    image: str = "jupyter-datascience-ubi9-python-3.9-2024.1",
    cpu_request: str = "1",
    memory_request: str = "4Gi",
    gpu_count: int = 0,
    pvc_size: str = "20Gi",
) -> str:
    """Create a new workbench (Jupyter notebook) in a Data Science Project."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")

    valid_images = [img["name"] for img in NOTEBOOK_IMAGES]
    if image not in valid_images:
        raise ValueError(
            f"Image '{image}' not found. Available: {', '.join(valid_images)}"
        )

    wb = {
        "name": name,
        "display_name": display_name or name,
        "image": image,
        "status": "Running",
        "cpu_request": cpu_request,
        "memory_request": memory_request,
        "gpu_count": gpu_count,
        "pvc_name": f"{name}-pvc",
        "pvc_size": pvc_size,
        "pvc_access_mode": "ReadWriteOnce",
        "creation": "2026-03-02T12:00:00Z",
    }
    WORKBENCHES.setdefault(namespace, []).append(wb)

    return json.dumps({
        "status": "created",
        "name": name,
        "namespace": namespace,
        "image": image,
        "pvc": f"{name}-pvc",
    })


@mcp.tool()
def stop_workbench(namespace: str, name: str) -> str:
    """Stop a running workbench (preserves data)."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")
    wbs = WORKBENCHES.get(namespace, [])
    wb = next((w for w in wbs if w["name"] == name), None)
    if not wb:
        raise ValueError(f"Workbench '{name}' not found in '{namespace}'")
    wb["status"] = "Stopped"
    return json.dumps({"status": "stopped", "name": name, "namespace": namespace})


@mcp.tool()
def start_workbench(namespace: str, name: str) -> str:
    """Start a stopped workbench."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")
    wbs = WORKBENCHES.get(namespace, [])
    wb = next((w for w in wbs if w["name"] == name), None)
    if not wb:
        raise ValueError(f"Workbench '{name}' not found in '{namespace}'")
    wb["status"] = "Running"
    return json.dumps({"status": "running", "name": name, "namespace": namespace})


@mcp.tool()
def delete_workbench(namespace: str, name: str) -> str:
    """Delete a workbench. WARNING: PVC data may be lost if not backed up."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")
    wbs = WORKBENCHES.get(namespace, [])
    wb = next((w for w in wbs if w["name"] == name), None)
    if not wb:
        raise ValueError(f"Workbench '{name}' not found in '{namespace}'")
    wbs.remove(wb)
    return json.dumps({
        "status": "deleted",
        "name": name,
        "namespace": namespace,
        "warning": "Associated PVC data has been deleted",
    })


@mcp.tool()
def list_notebook_images() -> str:
    """List available notebook images for workbench creation."""
    return json.dumps(NOTEBOOK_IMAGES, indent=2)


# ── Pipeline server tools ───────────────────────────────────────────────


@mcp.tool()
def configure_pipeline_server(
    namespace: str,
    data_connection: str,
    database: str = "MariaDB",
) -> str:
    """Configure a pipeline server for a Data Science Project."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")
    dcs = DATA_CONNECTIONS.get(namespace, [])
    if not any(dc["name"] == data_connection for dc in dcs):
        available = [dc["name"] for dc in dcs]
        raise ValueError(
            f"Data connection '{data_connection}' not found. Available: {available}"
        )

    PIPELINE_SERVERS[namespace] = {
        "configured": True,
        "data_connection": data_connection,
        "status": "Ready",
        "database": database,
    }
    PROJECTS[namespace]["pipeline_server"] = True

    return json.dumps({
        "status": "configured",
        "namespace": namespace,
        "data_connection": data_connection,
        "database": database,
    })


@mcp.tool()
def get_pipeline_server_status(namespace: str) -> str:
    """Get the status of the pipeline server in a Data Science Project."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")
    ps = PIPELINE_SERVERS.get(namespace)
    if not ps:
        return json.dumps({"namespace": namespace, "configured": False})
    return json.dumps({
        "namespace": namespace,
        "configured": ps["configured"],
        "data_connection": ps["data_connection"],
        "status": ps["status"],
        "database": ps["database"],
    })


# ── Serving runtime creation ────────────────────────────────────────────


@mcp.tool()
def create_serving_runtime(
    namespace: str,
    name: str,
    display_name: str = "",
    model_formats: list = None,
    container_image: str = "",
    container_port: int = 8080,
    multi_model: bool = False,
    api_protocol: str = "REST",
) -> str:
    """Create a custom ServingRuntime in a Data Science Project."""
    if namespace not in PROJECTS:
        raise ValueError(f"Namespace '{namespace}' is not a Data Science Project")

    if not model_formats:
        raise ValueError("model_formats must specify at least one model format")

    runtime = {
        "name": name,
        "display_name": display_name or name,
        "model_formats": model_formats,
        "requires_instantiation": False,
        "source": "custom",
        "api_protocol": api_protocol,
        "container_image": container_image,
        "container_port": container_port,
        "multi_model": multi_model,
    }
    SERVING_RUNTIMES.setdefault(namespace, []).append(runtime)

    return json.dumps({
        "status": "created",
        "name": name,
        "namespace": namespace,
        "model_formats": model_formats,
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")

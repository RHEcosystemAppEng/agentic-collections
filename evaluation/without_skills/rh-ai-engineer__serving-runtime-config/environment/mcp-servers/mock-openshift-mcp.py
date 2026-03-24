#!/usr/bin/env python3
"""Mock OpenShift MCP server for SkillsBench rh-ai-engineer task.

Simulates Kubernetes resource CRUD, pod management, logs, and events.

Key scenario elements:
- LimitRange in namespaces: min CPU=100m, min memory=128Mi
  (conflicts with KServe sidecar containers hardcoded at 10m CPU/15Mi memory)
- GPU node with custom taint ai-workload=true:NoSchedule
- NIM Account CR in ml-production: not ready (NGC credentials invalid)
- text-gen-legacy pods: OOMKilled (max-model-len=32768 on A10G)
- nim-llama-prod: no pods created (Account CR not ready)
"""

import json
from fastmcp import FastMCP

mcp = FastMCP("openshift")

# ── Cluster state ────────────────────────────────────────────────────────

GPU_NODE = {
    "apiVersion": "v1",
    "kind": "Node",
    "metadata": {
        "name": "gpu-worker-1",
        "labels": {
            "node-role.kubernetes.io/worker": "",
            "nvidia.com/gpu.present": "true",
            "nvidia.com/gpu.product": "NVIDIA-A10G",
        },
    },
    "spec": {
        "taints": [
            {
                "key": "ai-workload",
                "value": "true",
                "effect": "NoSchedule",
            },
        ],
    },
    "status": {
        "allocatable": {
            "cpu": "48",
            "memory": "192Gi",
            "nvidia.com/gpu": "2",
            "pods": "250",
        },
        "capacity": {
            "cpu": "48",
            "memory": "192Gi",
            "nvidia.com/gpu": "2",
            "pods": "250",
        },
        "conditions": [
            {"type": "Ready", "status": "True"},
        ],
    },
}

CPU_NODE = {
    "apiVersion": "v1",
    "kind": "Node",
    "metadata": {
        "name": "cpu-worker-1",
        "labels": {
            "node-role.kubernetes.io/worker": "",
        },
    },
    "spec": {"taints": []},
    "status": {
        "allocatable": {"cpu": "16", "memory": "64Gi", "pods": "250"},
        "capacity": {"cpu": "16", "memory": "64Gi", "pods": "250"},
        "conditions": [{"type": "Ready", "status": "True"}],
    },
}

MASTER_NODE = {
    "apiVersion": "v1",
    "kind": "Node",
    "metadata": {
        "name": "master-1",
        "labels": {
            "node-role.kubernetes.io/master": "",
            "node-role.kubernetes.io/control-plane": "",
        },
    },
    "spec": {
        "taints": [
            {"key": "node-role.kubernetes.io/master", "effect": "NoSchedule"},
        ],
    },
    "status": {
        "allocatable": {"cpu": "8", "memory": "32Gi", "pods": "250"},
        "conditions": [{"type": "Ready", "status": "True"}],
    },
}

ALL_NODES = [GPU_NODE, CPU_NODE, MASTER_NODE]

# LimitRange applied by cluster policy to all DS project namespaces
NAMESPACE_LIMITRANGE = {
    "apiVersion": "v1",
    "kind": "LimitRange",
    "metadata": {
        "name": "default-limits",
    },
    "spec": {
        "limits": [
            {
                "type": "Container",
                "default": {
                    "cpu": "2",
                    "memory": "4Gi",
                },
                "defaultRequest": {
                    "cpu": "500m",
                    "memory": "256Mi",
                },
                "min": {
                    "cpu": "100m",
                    "memory": "128Mi",
                },
                "max": {
                    "cpu": "32",
                    "memory": "128Gi",
                },
            },
        ],
    },
}

NIM_ACCOUNT_CR = {
    "apiVersion": "nim.opendatahub.io/v1",
    "kind": "Account",
    "metadata": {
        "name": "nim-account",
        "namespace": "ml-production",
    },
    "spec": {
        "apiKeySecret": {
            "name": "ngc-api-key",
        },
    },
    "status": {
        "conditions": [
            {
                "type": "Ready",
                "status": "False",
                "reason": "NGCCredentialsInvalid",
                "message": "NGC API key validation failed: 401 Unauthorized. "
                "The API key in secret 'ngc-api-key' is expired or invalid. "
                "Re-create the secret with a valid NGC API key from "
                "https://ngc.nvidia.com/setup/api-key and restart the "
                "Account reconciliation.",
                "lastTransitionTime": "2026-03-14T12:00:00Z",
            },
        ],
        "nimPullSecretStatus": "Failed",
        "nimConfigStatus": "Pending",
    },
}

SERVING_RUNTIME_VLLM = {
    "apiVersion": "serving.kserve.io/v1alpha1",
    "kind": "ServingRuntime",
    "metadata": {
        "name": "vllm-runtime",
    },
    "spec": {
        "supportedModelFormats": [
            {"name": "vLLM", "version": "1", "autoSelect": True},
        ],
        "containers": [
            {
                "name": "kserve-container",
                "image": "quay.io/modh/vllm:rhoai-2.16",
                "ports": [{"containerPort": 8080, "protocol": "TCP"}],
            },
        ],
    },
}

SERVING_RUNTIME_NIM = {
    "apiVersion": "serving.kserve.io/v1alpha1",
    "kind": "ServingRuntime",
    "metadata": {
        "name": "nim-serving-runtime",
    },
    "spec": {
        "supportedModelFormats": [
            {"name": "NIM", "version": "1"},
        ],
        "containers": [
            {
                "name": "kserve-container",
                "image": "nvcr.io/nim/meta/llama-3.1-8b-instruct:latest",
                "ports": [{"containerPort": 8000, "protocol": "TCP"}],
                "env": [
                    {"name": "NGC_API_KEY", "valueFrom": {
                        "secretKeyRef": {"name": "ngc-api-key", "key": "api_key"},
                    }},
                ],
            },
        ],
    },
}

PODS_BY_NAMESPACE = {
    "ml-production": [
        {
            "name": "text-gen-legacy-predictor-00001-abc12",
            "namespace": "ml-production",
            "status": "CrashLoopBackOff",
            "restarts": 5,
            "node": "gpu-worker-1",
            "containers": [
                {
                    "name": "kserve-container",
                    "state": "waiting",
                    "reason": "CrashLoopBackOff",
                    "last_termination_reason": "OOMKilled",
                    "last_termination_exit_code": 137,
                },
            ],
            "labels": {
                "serving.kserve.io/inferenceservice": "text-gen-legacy",
            },
            "gpu": "1",
        },
        # nim-llama-prod: NO pods created (Account CR not ready)
    ],
}

POD_LOGS = {
    "text-gen-legacy-predictor-00001-abc12": (
        "INFO 2026-03-01 10:00:00 vllm_engine.py:125] vLLM engine starting...\n"
        "INFO 2026-03-01 10:00:01 config.py:89] Model: mistralai/Mistral-7B-Instruct-v0.3\n"
        "INFO 2026-03-01 10:00:01 config.py:92] max_model_len = 32768\n"
        "INFO 2026-03-01 10:00:02 gpu_executor.py:45] GPU 0: NVIDIA A10G (24576 MiB)\n"
        "INFO 2026-03-01 10:00:03 model_runner.py:88] Loading model weights...\n"
        "INFO 2026-03-01 10:00:15 model_runner.py:112] Model weights loaded: 13.5 GiB\n"
        "INFO 2026-03-01 10:00:15 worker.py:201] Allocating KV cache...\n"
        "ERROR 2026-03-01 10:00:16 worker.py:215] torch.cuda.OutOfMemoryError: "
        "CUDA out of memory. Tried to allocate 28.5 GiB for KV cache but only "
        "10.1 GiB available after loading model weights (13.5 GiB).\n"
        "ERROR 2026-03-01 10:00:16 vllm_engine.py:178] Engine failed to start\n"
        "Traceback (most recent call last):\n"
        "  File \"/opt/vllm/vllm/engine/engine.py\", line 175, in start\n"
        "    self._init_kv_cache()\n"
        "  File \"/opt/vllm/vllm/worker/worker.py\", line 215, in _init_kv_cache\n"
        "    raise torch.cuda.OutOfMemoryError(msg)\n"
        "torch.cuda.OutOfMemoryError: CUDA out of memory\n"
    ),
}

EVENTS_BY_NAMESPACE = {
    "ml-production": [
        {
            "type": "Warning",
            "reason": "BackOff",
            "object": "Pod/text-gen-legacy-predictor-00001-abc12",
            "message": "Back-off restarting failed container kserve-container in pod "
            "text-gen-legacy-predictor-00001-abc12",
            "count": 5,
            "first_timestamp": "2026-02-28T08:00:00Z",
            "last_timestamp": "2026-03-01T10:00:16Z",
        },
        {
            "type": "Warning",
            "reason": "OOMKilled",
            "object": "Pod/text-gen-legacy-predictor-00001-abc12",
            "message": "Container kserve-container was OOMKilled (exit code 137). "
            "GPU memory exhausted during KV cache allocation.",
            "count": 5,
            "first_timestamp": "2026-02-28T08:00:00Z",
            "last_timestamp": "2026-03-01T10:00:16Z",
        },
        {
            "type": "Normal",
            "reason": "Scheduled",
            "object": "Pod/text-gen-legacy-predictor-00001-abc12",
            "message": "Successfully assigned ml-production/"
            "text-gen-legacy-predictor-00001-abc12 to gpu-worker-1",
            "count": 1,
            "first_timestamp": "2026-02-28T08:00:00Z",
            "last_timestamp": "2026-02-28T08:00:00Z",
        },
        {
            "type": "Warning",
            "reason": "NIMAccountNotReady",
            "object": "InferenceService/nim-llama-prod",
            "message": "NIM Account 'nim-account' in namespace 'ml-production' "
            "is not ready",
            "count": 12,
            "first_timestamp": "2026-03-14T12:00:00Z",
            "last_timestamp": "2026-03-15T10:00:00Z",
        },
        {
            "type": "Warning",
            "reason": "ImagePullBackOff",
            "object": "InferenceService/nim-llama-prod",
            "message": "Failed to pull image 'nvcr.io/nim/meta/llama-3.1-8b-instruct:"
            "latest': unauthorized: authentication required",
            "count": 8,
            "first_timestamp": "2026-03-14T12:05:00Z",
            "last_timestamp": "2026-03-15T10:00:00Z",
        },
    ],
}


# ── Resource tools ───────────────────────────────────────────────────────


@mcp.tool()
def resources_get(
    apiVersion: str,
    kind: str,
    name: str,
    namespace: str = "",
) -> str:
    """Get a single Kubernetes resource by apiVersion, kind, and name."""
    if kind == "Node":
        for node in ALL_NODES:
            if node["metadata"]["name"] == name:
                return json.dumps(node, indent=2)
        raise ValueError(f"Node '{name}' not found")

    if kind == "ServingRuntime":
        if name == "vllm-runtime":
            cr = json.loads(json.dumps(SERVING_RUNTIME_VLLM))
            cr["metadata"]["namespace"] = namespace or "ml-production"
            return json.dumps(cr, indent=2)
        if name == "nim-serving-runtime":
            cr = json.loads(json.dumps(SERVING_RUNTIME_NIM))
            cr["metadata"]["namespace"] = namespace or "ml-production"
            return json.dumps(cr, indent=2)
        raise ValueError(f"ServingRuntime '{name}' not found in namespace '{namespace}'")

    if kind == "LimitRange":
        lr = json.loads(json.dumps(NAMESPACE_LIMITRANGE))
        lr["metadata"]["namespace"] = namespace
        return json.dumps(lr, indent=2)

    if kind == "Account" and "nim" in apiVersion.lower():
        if namespace == "ml-production" and name == "nim-account":
            return json.dumps(NIM_ACCOUNT_CR, indent=2)
        raise ValueError(
            f"Account '{name}' not found in namespace '{namespace}'"
        )

    if kind == "ClusterVersion" and apiVersion == "config.openshift.io/v1":
        return json.dumps({
            "apiVersion": "config.openshift.io/v1",
            "kind": "ClusterVersion",
            "metadata": {"name": "version"},
            "status": {"desired": {"version": "4.16.3"}},
        })

    raise ValueError(f"Resource {apiVersion}/{kind}/{name} not found")


@mcp.tool()
def resources_create_or_update(
    api_version: str,
    kind: str,
    namespace: str,
    name: str,
    body: str,
) -> str:
    """Create or update a Kubernetes resource. Accepts apiVersion, kind, namespace, name, and body (JSON)."""
    try:
        resource = json.loads(body)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON body: {e}") from e

    resource.setdefault("metadata", {})
    resource["metadata"]["name"] = name
    resource["metadata"]["namespace"] = namespace
    resource["apiVersion"] = api_version
    resource["kind"] = kind

    if kind == "ServingRuntime":
        resource.setdefault("status", {})
        resource["status"]["conditions"] = [
            {
                "type": "Ready",
                "status": "True",
                "reason": "ServingRuntimeReady",
                "message": "ServingRuntime is ready",
                "lastTransitionTime": "2026-03-17T12:00:00Z",
            },
        ]
        return json.dumps({
            "status": "created",
            "resource": resource,
            "message": f"ServingRuntime '{name}' created/updated in namespace '{namespace}'",
        }, indent=2)

    if kind == "Secret":
        resource.setdefault("type", "Opaque")
        return json.dumps({
            "status": "created",
            "resource": resource,
            "message": f"Secret '{name}' created/updated in namespace '{namespace}'",
        }, indent=2)

    if kind in ("NIMAccount", "Account") and "nim" in api_version.lower():
        resource.setdefault("status", {})
        resource["status"]["conditions"] = [
            {
                "type": "Ready",
                "status": "True",
                "reason": "NGCCredentialsValid",
                "message": "NGC API key validated successfully",
                "lastTransitionTime": "2026-03-17T12:00:00Z",
            },
        ]
        return json.dumps({
            "status": "created",
            "resource": resource,
            "message": f"NIM Account '{name}' created/updated in namespace '{namespace}'",
        }, indent=2)

    if kind == "ConfigMap":
        return json.dumps({
            "status": "created",
            "resource": resource,
            "message": f"ConfigMap '{name}' created/updated in namespace '{namespace}'",
        }, indent=2)

    raise ValueError(f"Unsupported kind for create/update: {kind}")


@mcp.tool()
def resources_list(
    apiVersion: str,
    kind: str,
    namespace: str = "",
    labelSelector: str = "",
) -> str:
    """List Kubernetes resources by apiVersion and kind."""
    if kind == "Node":
        nodes = ALL_NODES
        if labelSelector:
            parts = labelSelector.split("=", 1)
            key = parts[0]
            value = parts[1] if len(parts) > 1 else ""
            nodes = [
                n for n in nodes
                if n["metadata"]["labels"].get(key) == value
            ]
        return json.dumps(nodes, indent=2)

    if kind == "Service" and apiVersion == "serving.knative.dev/v1":
        return json.dumps({
            "kind": "ServiceList",
            "apiVersion": "serving.knative.dev/v1",
            "items": [],
            "metadata": {},
        })

    if kind == "LimitRange":
        lr = json.loads(json.dumps(NAMESPACE_LIMITRANGE))
        lr["metadata"]["namespace"] = namespace
        return json.dumps({
            "kind": "LimitRangeList",
            "items": [lr],
        })

    if kind == "InferenceService":
        return json.dumps({
            "kind": "InferenceServiceList",
            "items": [],
        })

    raise ValueError(f"Unsupported list: {apiVersion}/{kind}")


@mcp.tool()
def pods_list(
    namespace: str,
    labelSelector: str = "",
) -> str:
    """List pods in a namespace with optional label selector."""
    pods = PODS_BY_NAMESPACE.get(namespace, [])

    if labelSelector:
        key, _, value = labelSelector.partition("=")
        pods = [p for p in pods if p.get("labels", {}).get(key) == value]

    results = []
    for pod in pods:
        results.append({
            "name": pod["name"],
            "namespace": pod["namespace"],
            "status": pod["status"],
            "restarts": pod.get("restarts", 0),
            "node": pod.get("node", ""),
            "containers": pod.get("containers", []),
            "gpu": pod.get("gpu", "0"),
        })

    return json.dumps(results, indent=2)


@mcp.tool()
def pods_log(
    namespace: str,
    name: str,
    container: str = "",
) -> str:
    """Get logs from a pod container."""
    logs = POD_LOGS.get(name)
    if logs is None:
        raise ValueError(f"Pod '{name}' not found in namespace '{namespace}'")
    return logs


@mcp.tool()
def events_list(namespace: str) -> str:
    """List events in a namespace."""
    events = EVENTS_BY_NAMESPACE.get(namespace, [])
    return json.dumps(events, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")

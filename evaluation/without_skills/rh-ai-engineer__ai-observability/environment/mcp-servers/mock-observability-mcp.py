#!/usr/bin/env python3
"""Mock Observability MCP server for SkillsBench rh-ai-engineer__ai-observability task.

Simulates Prometheus/Grafana-style metrics for inference services: latency,
throughput, error rates, GPU utilization, resource usage, and alerts.

Scenario (aligned with rhoai/openshift mocks):
- ml-production namespace:
  - text-gen-legacy (Mistral 7B on vLLM): OOMKilled; before crash: 22GB/24GB GPU,
    p99=2800ms, throughput=3 req/s, error rate=15%
  - nim-llama-prod (Llama 3.1 8B on NIM): not running, no metrics (empty/error)
  - sentiment-classifier: running well, 4GB/24GB GPU, p99=45ms, throughput=150 req/s,
    error rate=0.1%
"""

import json
from fastmcp import FastMCP

mcp = FastMCP("observability")

# ── Mock metrics data ──────────────────────────────────────────────────────

# text-gen-legacy: OOMKilled, metrics from before crash
MODEL_METRICS = {
    "ml-production": {
        "text-gen-legacy": {
            "status": "OOMKilled",
            "latency_ms": {"p50": 1200, "p95": 2100, "p99": 2800},
            "throughput_req_per_sec": 3.0,
            "error_rate_percent": 15.0,
            "input_tokens_per_sec": 45,
            "output_tokens_per_sec": 12,
            "total_requests_24h": 259200,  # 3 * 86400
        },
        "nim-llama-prod": None,  # not running, no metrics
        "sentiment-classifier": {
            "status": "Running",
            "latency_ms": {"p50": 18, "p95": 38, "p99": 45},
            "throughput_req_per_sec": 150.0,
            "error_rate_percent": 0.1,
            "input_tokens_per_sec": 1200,
            "output_tokens_per_sec": 50,
            "total_requests_24h": 12960000,
        },
    },
}

GPU_UTILIZATION = {
    "ml-production": [
        {
            "pod": "text-gen-legacy-predictor-00001-abc12",
            "model": "text-gen-legacy",
            "gpu_memory_used_gb": 22.0,
            "gpu_memory_total_gb": 24.0,
            "gpu_memory_utilization_percent": 91.7,
            "gpu_compute_utilization_percent": 35.0,
            "status": "OOMKilled",
        },
        {
            "pod": "sentiment-classifier-predictor-00001-xyz99",
            "model": "sentiment-classifier",
            "gpu_memory_used_gb": 4.0,
            "gpu_memory_total_gb": 24.0,
            "gpu_memory_utilization_percent": 16.7,
            "gpu_compute_utilization_percent": 42.0,
            "status": "Running",
        },
        # nim-llama-prod: no pod
    ],
}

RESOURCE_USAGE = {
    "ml-production": [
        {
            "pod": "text-gen-legacy-predictor-00001-abc12",
            "model": "text-gen-legacy",
            "cpu_request": "4",
            "cpu_limit": "4",
            "memory_request": "16Gi",
            "memory_limit": "16Gi",
            "cpu_actual_usage": "3.2",
            "memory_actual_usage_mib": 16384,
            "status": "CrashLoopBackOff",
        },
        {
            "pod": "sentiment-classifier-predictor-00001-xyz99",
            "model": "sentiment-classifier",
            "cpu_request": "2",
            "cpu_limit": "4",
            "memory_request": "8Gi",
            "memory_limit": "16Gi",
            "cpu_actual_usage": "1.1",
            "memory_actual_usage_mib": 4096,
            "status": "Running",
        },
    ],
}

PROMETHEUS_ALERTS = {
    "ml-production": [
        {
            "name": "InferenceServiceOOMKilled",
            "severity": "critical",
            "state": "firing",
            "summary": "text-gen-legacy predictor pod OOMKilled",
            "description": "Container kserve-container was OOMKilled (exit code 137). "
            "GPU memory exhausted during KV cache allocation.",
            "labels": {
                "inference_service": "text-gen-legacy",
                "namespace": "ml-production",
            },
        },
        {
            "name": "HighInferenceLatency",
            "severity": "warning",
            "state": "firing",
            "summary": "text-gen-legacy p99 latency > 2000ms",
            "description": "Inference latency p99 is 2800ms, exceeding threshold of 2000ms.",
            "labels": {
                "inference_service": "text-gen-legacy",
                "namespace": "ml-production",
            },
        },
        {
            "name": "HighErrorRate",
            "severity": "warning",
            "state": "firing",
            "summary": "text-gen-legacy error rate 15%",
            "description": "Inference error rate is 15%, exceeding threshold of 5%.",
            "labels": {
                "inference_service": "text-gen-legacy",
                "namespace": "ml-production",
            },
        },
    ],
}


# ── Tools ──────────────────────────────────────────────────────────────────


@mcp.tool()
def query_model_metrics(
    model_name: str,
    namespace: str,
    metric_type: str = "all",
) -> str:
    """Query inference metrics for a model. Returns latency (p50/p95/p99), throughput
    (requests/sec), error rates, and token counts.

    metric_type: 'all', 'latency', 'throughput', 'errors', or 'tokens'
    """
    ns_data = MODEL_METRICS.get(namespace)
    if not ns_data:
        return json.dumps({"error": f"Namespace '{namespace}' not found"}, indent=2)

    metrics = ns_data.get(model_name)
    if metrics is None:
        return json.dumps({
            "error": f"No metrics for model '{model_name}' in namespace '{namespace}'. "
            "Model may not be running (e.g., nim-llama-prod has no pods).",
            "model_name": model_name,
            "namespace": namespace,
        }, indent=2)

    result = {
        "model_name": model_name,
        "namespace": namespace,
        "status": metrics["status"],
    }

    if metric_type in ("all", "latency"):
        result["latency_ms"] = metrics["latency_ms"]
    if metric_type in ("all", "throughput"):
        result["throughput_req_per_sec"] = metrics["throughput_req_per_sec"]
        result["total_requests_24h"] = metrics.get("total_requests_24h")
    if metric_type in ("all", "errors"):
        result["error_rate_percent"] = metrics["error_rate_percent"]
    if metric_type in ("all", "tokens"):
        result["input_tokens_per_sec"] = metrics["input_tokens_per_sec"]
        result["output_tokens_per_sec"] = metrics["output_tokens_per_sec"]

    return json.dumps(result, indent=2)


@mcp.tool()
def query_gpu_utilization(namespace: str) -> str:
    """Query GPU memory used/total and compute utilization per inference pod."""
    pods = GPU_UTILIZATION.get(namespace, [])
    if not pods:
        return json.dumps({
            "namespace": namespace,
            "pods": [],
            "message": "No GPU-backed inference pods found in namespace.",
        }, indent=2)
    return json.dumps({
        "namespace": namespace,
        "pods": pods,
    }, indent=2)


@mcp.tool()
def query_resource_usage(namespace: str) -> str:
    """Query actual CPU/memory usage vs requests/limits for inference pods."""
    pods = RESOURCE_USAGE.get(namespace, [])
    if not pods:
        return json.dumps({
            "namespace": namespace,
            "pods": [],
            "message": "No inference pods found in namespace.",
        }, indent=2)
    return json.dumps({
        "namespace": namespace,
        "pods": pods,
    }, indent=2)


@mcp.tool()
def list_prometheus_alerts(namespace: str) -> str:
    """List firing Prometheus alerts related to inference services in the namespace."""
    alerts = PROMETHEUS_ALERTS.get(namespace, [])
    return json.dumps({
        "namespace": namespace,
        "alerts": alerts,
        "firing_count": len(alerts),
    }, indent=2)


@mcp.tool()
def get_model_performance_summary(namespace: str) -> str:
    """Get aggregated performance data across all models in the namespace."""
    ns_data = MODEL_METRICS.get(namespace)
    if not ns_data:
        return json.dumps({"error": f"Namespace '{namespace}' not found"}, indent=2)

    models = []
    for name, metrics in ns_data.items():
        if metrics is None:
            models.append({
                "model_name": name,
                "status": "NotRunning",
                "error": "No metrics available (pod not created or not running)",
            })
        else:
            models.append({
                "model_name": name,
                "status": metrics["status"],
                "latency_p99_ms": metrics["latency_ms"]["p99"],
                "throughput_req_per_sec": metrics["throughput_req_per_sec"],
                "error_rate_percent": metrics["error_rate_percent"],
            })

    return json.dumps({
        "namespace": namespace,
        "models": models,
    }, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")

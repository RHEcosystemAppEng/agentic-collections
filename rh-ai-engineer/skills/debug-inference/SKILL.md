---
name: debug-inference
description: |
  Troubleshoot failed or slow InferenceService deployments on OpenShift AI.

  Use when:
  - "My InferenceService won't start"
  - "Model deployment is stuck"
  - "Inference endpoint returns errors"
  - "Model is slow / high latency"
  - "GPU scheduling failed for my model"

  Progressive diagnosis: status conditions, events, pod logs, GPU health, and observability analysis.

  NOT for deploying models (use /model-deploy).
  NOT for creating runtimes (use /serving-runtime-config).
---

# /debug-inference Skill

Troubleshoot failed, stuck, or slow InferenceService deployments on Red Hat OpenShift AI. Performs progressive diagnosis through status conditions, events, pod logs, related resources, and optional observability analysis. Follows a 6-step diagnosis pattern with human-in-the-loop confirmation at each step.

## Prerequisites

**Required MCP Server**: `openshift` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_get` (from openshift) - Get InferenceService status, ServingRuntime, Account CR
- `resources_list` (from openshift) - List InferenceServices in a namespace
- `pods_list` (from openshift) - Find predictor/transformer pods
- `pods_log` (from openshift) - Retrieve container logs
- `events_list` (from openshift) - Check events for errors

**Optional MCP Server**: `ai-observability` ([AI Observability MCP](https://github.com/rh-ai-quickstart/ai-observability-summarizer))

**Optional MCP Tools** (from ai-observability):
- `get_deployment_info` - Check model initialization status
- `analyze_vllm` - Analyze vLLM performance bottlenecks (latency, throughput, errors, token rates)
- `chat_vllm` - Conversational follow-up on vLLM metrics during diagnosis
- `get_gpu_info` - GPU inventory and utilization
- `analyze_openshift` - Check GPU health with "GPU & Accelerators" category
- `query_tempo_tool` - Trace request latency by service/operation/time range
- `get_trace_details_tool` - Get detailed span-level info for a specific trace ID
- `execute_promql` - Run custom PromQL queries for metrics not covered by standard analysis
- `korrel8r_get_correlated` - Correlate signals (logs, traces, metrics, alerts) across a pod/namespace for root cause analysis

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster with Red Hat OpenShift AI operator installed
- KServe model serving platform configured
- An existing InferenceService deployment to debug

See [skill-conventions.md](../../docs/references/skill-conventions.md) for prerequisite verification protocol, human-in-the-loop requirements, and security conventions.

## Workflow

### Step 1: Identify Target InferenceService

**Ask the user:**
- Which InferenceService is having issues? (name or "list all")
- What namespace is it in?
- What is the symptom? (won't start / slow / errors / other)

If user says "list all" or is unsure:

**MCP Tool**: `resources_list` (from openshift)

**Parameters**:
- `resource`: `"inferenceservices.serving.kserve.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

Present InferenceServices with their status:

| Name | Runtime | Ready | URL | Age |
|------|---------|-------|-----|-----|
| [name] | [runtime] | [True/False/Unknown] | [url or "N/A"] | [age] |

**WAIT for user to select which InferenceService to debug.**

### Step 2: Status Overview

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"inferenceservices.serving.kserve.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: the InferenceService name - REQUIRED

Present status conditions:

| Condition | Status | Reason | Message |
|-----------|--------|--------|---------|
| Ready | [True/False/Unknown] | [reason] | [message] |
| PredictorReady | [True/False/Unknown] | [reason] | [message] |
| IngressReady | [True/False/Unknown] | [reason] | [message] |

**Quick Assessment**: Based on conditions, provide initial assessment (e.g., "PredictorReady is False -- the model container is not running. Likely a pod-level issue.")

**Ask**: "Continue with deep analysis of events and pods? (yes/no)"

**WAIT for user confirmation.**

### Step 3: Events and Pod Analysis

**MCP Tool**: `events_list` (from openshift)

**Parameters**:
- `namespace`: user-specified namespace - REQUIRED

Filter events related to the InferenceService name.

**MCP Tool**: `pods_list` (from openshift)

**Parameters**:
- `namespace`: user-specified namespace - REQUIRED
- `labelSelector`: `"serving.kserve.io/inferenceservice=[isvc-name]"` - REQUIRED

Present findings:

**Events:**

| Time | Type | Reason | Message |
|------|------|--------|---------|
| [time] | [Normal/Warning] | [reason] | [message] |

**Predictor Pods:**

| Pod | Status | Restarts | Node | GPU |
|-----|--------|----------|------|-----|
| [pod-name] | [status] | [count] | [node] | [gpu-count] |

**Issues Found:**
- [Issue from events or pod status]

**Ask**: "Continue to view pod logs? (yes/no)"

**WAIT for user confirmation.**

### Step 4: Pod Logs Review

**MCP Tool**: `pods_log` (from openshift)

**Parameters**:
- `namespace`: user-specified namespace - REQUIRED
- `name`: predictor pod name from Step 3 - REQUIRED
- `container`: `"kserve-container"` - REQUIRED (main serving container)

If the container has restarted, also retrieve previous logs.

Present log analysis:

**Log Analysis:**
- [Error pattern identified, e.g., "CUDA out of memory", "S3 access denied", "Model not found"]
- [Relevant log line with explanation]

**For NIM-specific deployments**, also check:
- NGC authentication errors in logs
- TensorRT engine compilation status
- GPU compatibility messages

**If the error is unrecognized -> Trigger live doc lookup:**
1. **Action**: Read [live-doc-lookup.md](../../docs/references/live-doc-lookup.md) using the Read tool
2. Use **WebFetch** to look up the error message in RHOAI documentation
3. **Output to user**: "I looked up this error on [source]: [explanation and fix]"

**Ask**: "Continue to check related resources and observability? (yes/no)"

**WAIT for user confirmation.**

### Step 5: Related Resources and Observability

**Check ServingRuntime:**

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"servingruntimes.serving.kserve.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: runtime name from the InferenceService spec - REQUIRED

Verify the runtime exists and its model format matches the InferenceService.

**For NIM deployments -- Check Account CR:**

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"accounts.nim.opendatahub.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: `"nim-account"` - REQUIRED

**If ai-observability MCP is available:**

- `get_deployment_info`: Check if the model appears in monitoring and its initialization status
- `analyze_vllm`: Analyze performance metrics for slow inference (latency, throughput, errors, token rates)
- `chat_vllm`: Ask follow-up questions about analyzed metrics (e.g., "Why is latency spiking?")
- `analyze_openshift` with category `"GPU & Accelerators"`: Check GPU health and utilization
- `query_tempo_tool`: Trace request latency if the symptom is slow responses
- `get_trace_details_tool`: Drill into a specific trace ID to see span-level timing
- `execute_promql`: Run custom PromQL queries for deeper metric investigation (e.g., `vllm:request_success:ratio`, GPU memory utilization)
- `korrel8r_get_correlated`: Correlate signals across the inference stack -- find related logs, traces, metrics, and alerts for the failing pod/namespace (query example: `k8s:Pod:{"namespace":"[ns]","name":"[pod-name]"}`, goals: `["log:application", "metric:metric", "trace:span"]`)

**If ai-observability not available**: Skip with note: "Observability analysis skipped (ai-observability MCP not configured)."

**Present findings:**
- ServingRuntime status and compatibility
- NIM Account CR status (if applicable)
- Observability insights (if available)

**Ask**: "Continue to diagnosis summary? (yes/no)"

**WAIT for user confirmation.**

### Step 6: Diagnosis Summary

Present a structured diagnosis:

```
## Diagnosis Summary: [isvc-name]

### Root Cause

**Primary Issue:** [Categorized root cause]

| Category | Status | Details |
|----------|--------|---------|
| ServingRuntime | [OK/FAIL] | [details] |
| Pod Scheduling | [OK/FAIL] | [details] |
| Container Start | [OK/FAIL] | [details] |
| Model Loading | [OK/FAIL] | [details] |
| GPU Access | [OK/FAIL] | [details] |
| Endpoint Health | [OK/FAIL] | [details] |

### Evidence

- [Evidence 1 from events/logs/status]
- [Evidence 2]

### Recommended Actions

1. **[Action 1]** - [description]
2. **[Action 2]** - [description]
3. **[Action 3]** - [description]

### Verification Steps

After applying fixes:
1. Check InferenceService status: `resources_get` for the InferenceService
2. Verify pod is running: `pods_list` with label selector
3. Test endpoint: curl command to the inference URL
```

**End with options:**

```
Would you like me to:
1. Execute a recommended fix
2. Dig deeper into a specific area
3. Debug a related resource (ServingRuntime, pod, NIM Account)
4. Invoke /serving-runtime-config to fix runtime issues
5. Exit debugging
```

**WAIT for user to select next action.**

## Common Issues

### Issue 1: GPU Scheduling Failure

**Error**: Predictor pod stuck in Pending with "Insufficient nvidia.com/gpu" event

**Cause**: Cluster does not have enough available GPUs of the required type.

**Solution:**
1. Check GPU availability: `get_gpu_info` from ai-observability (if available) or inspect node resources via `resources_get`
2. Reduce GPU request or use a quantized model variant
3. Check if other InferenceServices are consuming GPU resources
4. Verify GPU Operator and NFD Operator are healthy

### Issue 2: OOMKilled During Model Loading

**Error**: Predictor pod terminated with OOMKilled, often during initial model weight loading

**Cause**: Model requires more memory than allocated. Common with large models or when `--max-model-len` is set too high.

**Solution:**
1. Increase memory limits in the InferenceService spec
2. Reduce `--max-model-len` to lower KV cache memory usage
3. Use a quantized model variant (AWQ/GPTQ/FP8)
4. Consult [known-model-profiles.md](../../docs/references/known-model-profiles.md) for correct resource sizing

### Issue 3: S3 Storage Access Denied

**Error**: Pod logs show "Access Denied" or "NoSuchBucket" when loading model weights

**Cause**: S3 credentials are missing, expired, or the bucket/path is incorrect.

**Solution:**
1. Verify the `storageUri` in the InferenceService spec
2. Check that the S3 credential Secret exists in the namespace
3. Verify the Secret is referenced by the ServiceAccount or data connection
4. Test S3 access independently to confirm credentials are valid

### Issue 4: NIM Authentication / GPU Incompatibility

**Error**: NIM pod logs show NGC authentication failure, or TensorRT engine fails to compile for the available GPU

**Cause**: NGC API key is invalid/expired, or the GPU type is not supported by the NIM model profile.

**Solution:**
1. Check Account CR status for credential errors: `resources_get` for `accounts.nim.opendatahub.io`
2. Verify NGC API key is valid at https://ngc.nvidia.com
3. Check NIM supported GPU matrix via live doc lookup against [NVIDIA NIM supported models](https://docs.nvidia.com/nim/large-language-models/latest/supported-models.html)
4. Re-run `/nim-setup` to refresh credentials if expired

## Dependencies

### MCP Tools Used

| Tool | Server | Purpose |
|------|--------|---------|
| `resources_get` | openshift | InferenceService status, ServingRuntime, Account CR |
| `resources_list` | openshift | List InferenceServices |
| `pods_list` | openshift | Find predictor pods |
| `pods_log` | openshift | Container logs for diagnosis |
| `events_list` | openshift | Scheduling, pull, and runtime events |
| `get_deployment_info` | ai-observability (optional) | Model initialization status |
| `analyze_vllm` | ai-observability (optional) | Performance bottleneck analysis |
| `chat_vllm` | ai-observability (optional) | Conversational follow-up on vLLM metrics |
| `get_gpu_info` | ai-observability (optional) | GPU inventory and utilization |
| `analyze_openshift` | ai-observability (optional) | GPU health check |
| `query_tempo_tool` | ai-observability (optional) | Request latency tracing |
| `get_trace_details_tool` | ai-observability (optional) | Span-level trace details |
| `execute_promql` | ai-observability (optional) | Custom PromQL metric queries |
| `korrel8r_get_correlated` | ai-observability (optional) | Cross-signal correlation (logs, traces, metrics, alerts) |

### Related Skills
- `/model-deploy` - Redeploy or modify the InferenceService after fixing issues
- `/serving-runtime-config` - Fix or create ServingRuntime if runtime is the issue
- `/nim-setup` - Re-run NIM platform setup if NIM credentials are the issue

### Reference Documentation
- [known-model-profiles.md](../../docs/references/known-model-profiles.md) - Correct resource sizing for common models
- [supported-runtimes.md](../../docs/references/supported-runtimes.md) - Runtime capabilities and known limitations
- [live-doc-lookup.md](../../docs/references/live-doc-lookup.md) - Protocol for looking up unrecognized errors

## Critical: Human-in-the-Loop Requirements

See [skill-conventions.md](../../docs/references/skill-conventions.md) for general HITL and security conventions.

**Skill-specific checkpoints:**
- After identifying target (Step 1): confirm which InferenceService to debug
- After status overview (Step 2): confirm before deep analysis
- After events/pod analysis (Step 3): confirm before viewing logs
- After log review (Step 4): confirm before checking related resources
- After diagnosis summary (Step 6): present options, wait for user decision
- **NEVER** auto-delete or auto-modify InferenceService resources without user confirmation
- **NEVER** execute remediation actions without presenting the plan and getting explicit approval

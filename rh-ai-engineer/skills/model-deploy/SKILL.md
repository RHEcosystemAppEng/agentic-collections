---
name: model-deploy
description: |
  Deploy AI/ML models on OpenShift AI using KServe with vLLM, NVIDIA NIM, or Caikit+TGIS runtimes.

  Use when:
  - "Deploy Llama 3 on my cluster"
  - "Set up a vLLM inference endpoint"
  - "Deploy a model with NIM"
  - "Create an InferenceService for Granite"
  - "I need to serve a model on OpenShift AI"

  Handles runtime selection, GPU validation, InferenceService CR creation, and rollout monitoring.

  NOT for NIM platform setup (use /nim-setup first).
  NOT for custom runtime creation (use /serving-runtime-config).
model: inherit
color: green
---

# /model-deploy Skill

Deploy AI/ML models on Red Hat OpenShift AI using KServe. Supports vLLM, NVIDIA NIM, and Caikit+TGIS serving runtimes. Handles runtime selection, hardware profile lookup (with live doc fallback), GPU pre-flight checks, InferenceService CR creation, rollout monitoring, and post-deployment validation.

## Prerequisites

**Required MCP Server**: `openshift` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_get` (from openshift) - Check InferenceService status, ServingRuntimes, Account CR
- `resources_list` (from openshift) - List resources in a namespace
- `resources_create_or_update` (from openshift) - Create InferenceService CR
- `pod_list` (from openshift) - Check predictor pod status during rollout
- `pod_logs` (from openshift) - Retrieve pod logs for debugging
- `events_list` (from openshift) - Check events for errors

**Optional MCP Server**: `ai-observability` ([AI Observability MCP](https://github.com/rh-ai-quickstart/ai-observability-summarizer))

**Optional MCP Tools** (from ai-observability):
- `get_gpu_info` - Pre-flight GPU inventory check
- `get_deployment_info` - Post-deployment validation
- `analyze_vllm` - Verify metrics are flowing after deployment

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster with Red Hat OpenShift AI operator installed
- KServe model serving platform configured
- Model serving enabled on the target namespace (label: `opendatahub.io/dashboard: "true"`)
- For NIM runtime: NIM platform set up via `/nim-setup`
- For vLLM/NIM: NVIDIA GPU nodes available in the cluster

See [skill-conventions.md](../../docs/references/skill-conventions.md) for prerequisite verification protocol, human-in-the-loop requirements, and security conventions.

## Workflow

### Step 1: Gather Deployment Information

Collect the following from the user. Use defaults where sensible, but always confirm.

**Ask the user for:**
- **Model name**: Which model to deploy (e.g., "Llama 3.1 8B", "Granite 3.1 8B")
- **Runtime preference**: vLLM (default), NIM, or Caikit+TGIS (auto-detect if not specified)
- **Namespace**: Target namespace (must have model serving enabled)
- **Model source**: Where the model weights are stored (S3, OCI registry, PVC, or NGC for NIM)
- **Deployment mode**: Serverless (Knative, default) or RawDeployment

**Present configuration table for review:**

| Setting | Value | Source |
|---------|-------|--------|
| Model | [model-name] | user input |
| Runtime | [to be determined in Step 2] | auto-detect / user input |
| Namespace | [namespace] | user input |
| Model Source | [source-uri] | user input |
| Deployment Mode | [Serverless/RawDeployment] | user input / default: Serverless |

**WAIT for user to confirm or modify these settings.**

### Step 2: Determine Runtime

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [supported-runtimes.md](../../docs/references/supported-runtimes.md) using the Read tool to understand runtime capabilities and selection criteria
2. **Output to user**: "I consulted [supported-runtimes.md](../../docs/references/supported-runtimes.md) to understand runtime capabilities."

**Runtime Selection Logic:**

- User explicitly requested a runtime -> Use that runtime
- Model available in NGC NIM catalog -> Suggest NIM (with vLLM as fallback)
- Model is a standard open-source LLM (HuggingFace-compatible) -> Default to vLLM
- Model is in Caikit format -> Caikit+TGIS
- None of the above -> Suggest custom runtime via `/serving-runtime-config`

**Present recommendation** with rationale. **WAIT for user confirmation.**

### Step 3: Look Up Model Hardware Profile

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [known-model-profiles.md](../../docs/references/known-model-profiles.md) using the Read tool to find hardware profile for the requested model
2. **Output to user**: "I consulted [known-model-profiles.md](../../docs/references/known-model-profiles.md) to find hardware requirements for [model-name]."

**If model IS in known-model-profiles.md:**
- Extract: GPU count, GPU type, VRAM, key vLLM args
- Present to user

**If model is NOT in known-model-profiles.md -> Trigger live doc lookup:**
1. **Action**: Read [live-doc-lookup.md](../../docs/references/live-doc-lookup.md) using the Read tool for the lookup protocol
2. **Output to user**: "Model [model-name] is not in my cached profiles. I'll look up its hardware requirements."
3. Use **WebFetch** tool to retrieve specs from:
   - For NIM models: `https://build.nvidia.com/models` or `https://docs.nvidia.com/nim/large-language-models/latest/supported-models.html`
   - For other models: `https://docs.redhat.com/en/documentation/red_hat_openshift_ai_cloud_service/1`
4. Extract: GPU requirements, model-specific args, known issues
5. **Output to user**: "I looked up [model-name] on [source] to confirm its hardware requirements: [summary]"

**Present hardware requirements** in a table (GPUs, VRAM, Key Args).

### Step 4: Pre-flight GPU Check (Optional)

**Condition**: Only if `ai-observability` MCP server is available.

**MCP Tool**: `get_gpu_info` (from ai-observability)

Compare available GPUs against model requirements from Step 3:
- If sufficient GPUs available -> Report match and proceed
- If insufficient -> Warn user with options: smaller model, quantized version, different cluster, or proceed at user's risk

**If ai-observability not available**: Skip with note: "GPU pre-flight check skipped (ai-observability MCP not configured)."

### Step 5: Verify NIM Platform (NIM Runtime Only)

**Condition**: Only when the selected runtime is NIM.

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"accounts.nim.opendatahub.io"` - REQUIRED
- `namespace`: target namespace - REQUIRED
- `name`: `"nim-account"` - REQUIRED

**If Account CR not found or not ready:**
Offer options: (1) Run `/nim-setup` now, (2) Switch to vLLM, (3) Abort. **WAIT for user decision.**

### Step 6: Generate InferenceService YAML

Generate the InferenceService manifest based on the selected runtime. Use values from Steps 1-3.

**For vLLM:**

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: [model-name]
  namespace: [namespace]
  annotations:
    serving.kserve.io/deploymentMode: [Serverless|RawDeployment]
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: [serving-runtime-name]
      storageUri: [model-source-uri]
      resources:
        limits:
          nvidia.com/gpu: [gpu-count]
        requests:
          cpu: [cpu-request]
          memory: [memory-request]
    args:
      - --max-model-len=[value-from-profile]
      - --tensor-parallel-size=[gpu-count]
      # Additional model-specific args from profile
```

**For NVIDIA NIM:**

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: [model-name]
  namespace: [namespace]
  annotations:
    serving.kserve.io/deploymentMode: [Serverless|RawDeployment]
spec:
  predictor:
    model:
      modelFormat:
        name: [nim-model-format]
      runtime: [nim-serving-runtime-name]
      resources:
        limits:
          nvidia.com/gpu: [gpu-count]
        requests:
          cpu: [cpu-request]
          memory: [memory-request]
    env:
      - name: NGC_API_KEY
        valueFrom:
          secretKeyRef:
            name: ngc-api-key
            key: NGC_API_KEY
```

**For Caikit+TGIS:**

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: [model-name]
  namespace: [namespace]
spec:
  predictor:
    model:
      modelFormat:
        name: caikit
      runtime: [caikit-tgis-runtime-name]
      storageUri: [model-source-uri]
      resources:
        limits:
          nvidia.com/gpu: [gpu-count]
```

**Verify ServingRuntime exists** before generating YAML:

**MCP Tool**: `resources_list` (from openshift)

**Parameters**:
- `resource`: `"servingruntimes.serving.kserve.io"` - REQUIRED
- `namespace`: target namespace - REQUIRED

Use the list to populate the `runtime` field with the correct ServingRuntime name.

### Step 7: User Review and Confirmation

**Display the complete InferenceService YAML** and a configuration summary table to the user.

**Ask**: "Proceed with creating this InferenceService? (yes/no/modify)"

**WAIT for explicit confirmation.**

- If **yes** -> Proceed to Step 8
- If **no** -> Abort
- If **modify** -> Ask what to change, regenerate YAML, return to this step

### Step 8: Create InferenceService

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `resource`: full InferenceService manifest as JSON string - REQUIRED
  - Example: `'{"apiVersion":"serving.kserve.io/v1beta1","kind":"InferenceService","metadata":{"name":"llama-3-8b","namespace":"my-ai-project","annotations":{"serving.kserve.io/deploymentMode":"Serverless"}},"spec":{...}}'`
- `namespace`: target namespace - REQUIRED

**Error Handling**:
- If namespace not found -> Report error, suggest creating namespace or using `/ds-project-setup`
- If ServingRuntime not found -> Report error, verify runtime name, suggest `/serving-runtime-config`
- If quota exceeded -> Report error, suggest reducing resource requests
- If RBAC error -> Report insufficient permissions

### Step 9: Monitor Rollout

Poll InferenceService status until ready or timeout (10 minutes).

**MCP Tool**: `resources_get` (from openshift)
- `resource`: `"inferenceservices.serving.kserve.io"`, `namespace`, `name`

**Check predictor pod status:**

**MCP Tool**: `pod_list` (from openshift)
- `namespace`: target namespace, `labelSelector`: `"serving.kserve.io/inferenceservice=[model-name]"`

Show deployment progress tracking: Pod Scheduled, Image Pulled, Container Started, Model Loaded, Ready. Include pod name, status, and restart count.

**On failure:** Check pod logs (`pod_logs`) and events (`events_list`) for diagnostics. Present options: (1) View full pod logs, (2) Check namespace events, (3) Invoke `/debug-inference`, (4) Delete and retry, (5) Continue waiting. **WAIT for user decision. NEVER auto-delete failed deployments.**

### Step 10: Deployment Complete

**Report success** showing: model name, runtime, namespace, GPUs, inference endpoint URL, API type (OpenAI-compatible REST), a curl quick-test command, and next steps (`/ai-observability`, `/model-monitor`, `/guardrails-config`).

**Post-deployment validation** (if ai-observability MCP available):
- `get_deployment_info` to confirm model appears in monitoring
- `analyze_vllm` with a short time range to verify initial metrics are flowing
- Report findings to user

## Common Issues

### Issue 1: InferenceService Stuck in "Unknown"

**Error**: InferenceService `status.conditions` shows "Unknown" state

**Cause**: ServingRuntime not found in the namespace, or model serving platform not enabled.

**Solution:**
1. Verify ServingRuntime exists: `resources_list` for `servingruntimes` in namespace
2. Ensure model serving is enabled: namespace has label `opendatahub.io/dashboard: "true"`
3. Check the runtime name in the InferenceService matches an available ServingRuntime
4. If no matching runtime, use `/serving-runtime-config` to create one

### Issue 2: Pod OOMKilled

**Error**: Predictor pod terminated with OOMKilled exit code

**Cause**: Model requires more memory than allocated in resource requests/limits.

**Solution:**
1. Increase memory limits in the InferenceService spec
2. Use a quantized model variant (AWQ/GPTQ/FP8) to reduce memory footprint
3. Reduce `--max-model-len` to limit KV cache memory usage
4. Verify GPU VRAM is sufficient using `get_gpu_info`

### Issue 3: GPU Scheduling Failure

**Error**: Pod stuck in Pending with events showing "Insufficient nvidia.com/gpu"

**Cause**: Cluster does not have enough available GPUs of the required type.

**Solution:**
1. Check GPU availability: `get_gpu_info` from ai-observability (if available)
2. Check node GPU resources: `resources_get` for nodes with `nvidia.com/gpu` capacity
3. Consider using fewer GPUs with `--tensor-parallel-size` reduction and quantization
4. Check if other workloads are consuming GPU resources

### Issue 4: NIM Image Pull Error

**Error**: Pod fails with `ErrImagePull` or `ImagePullBackOff` for NIM container images

**Cause**: NGC image pull secret is missing, expired, or not in the correct namespace.

**Solution:**
1. Verify NGC pull secret exists in namespace: `resources_get` for the secret
2. Re-run `/nim-setup` to recreate credentials if expired
3. Check Account CR status for credential-related errors

### Issue 5: Model Download Timeout

**Error**: Pod starts but times out while downloading model weights from S3 or OCI registry

**Cause**: Large model size combined with slow network connection to storage.

**Solution:**
1. Add `serving.knative.dev/progress-deadline` annotation with a longer timeout (e.g., `"1800s"`)
2. Verify S3/storage credentials are valid
3. Consider using a PVC with pre-downloaded model weights instead
4. Check network connectivity between the pod and storage endpoint

## Dependencies

### MCP Tools Used

| Tool | Server | Purpose |
|------|--------|---------|
| `resources_get` | openshift | Check InferenceService status, ServingRuntimes, Account CR |
| `resources_list` | openshift | List ServingRuntimes, find available runtimes |
| `resources_create_or_update` | openshift | Create InferenceService CR |
| `pod_list` | openshift | Monitor rollout pod status |
| `pod_logs` | openshift | Debug deployment failures |
| `events_list` | openshift | Diagnose scheduling and pull errors |
| `get_gpu_info` | ai-observability (optional) | Pre-flight GPU validation |
| `get_deployment_info` | ai-observability (optional) | Post-deployment validation |
| `analyze_vllm` | ai-observability (optional) | Verify metrics flowing |

### Related Skills
- `/nim-setup` - Prerequisite for NIM runtime deployments
- `/debug-inference` - Troubleshoot InferenceService failures
- `/ai-observability` - Analyze deployed model performance
- `/serving-runtime-config` - Create custom ServingRuntime CRs
- `/ds-project-setup` - Create a namespace with model serving enabled

### Reference Documentation
- [known-model-profiles.md](../../docs/references/known-model-profiles.md) - Hardware profiles for common models
- [supported-runtimes.md](../../docs/references/supported-runtimes.md) - Runtime capabilities and selection criteria
- [live-doc-lookup.md](../../docs/references/live-doc-lookup.md) - Protocol for fetching specs for unknown models

## Critical: Human-in-the-Loop Requirements

See [skill-conventions.md](../../docs/references/skill-conventions.md) for general HITL and security conventions.

**Skill-specific checkpoints:**
- After gathering settings (Step 1): confirm configuration table
- After runtime selection (Step 2): confirm runtime choice
- Before creating InferenceService (Step 7): display full YAML, confirm
- On deployment failure (Step 9): present diagnostic options, wait for user decision
- **NEVER** auto-delete failed deployments or auto-select runtimes without confirmation

## Example Usage

See [model-deploy examples](../../docs/examples/model-deploy.md) for complete deployment walkthroughs (vLLM and NIM).

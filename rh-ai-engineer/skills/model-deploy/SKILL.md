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

### Prerequisite Verification

**Before executing, verify MCP server availability:**

1. **Check MCP Server Configuration**
   - Verify `openshift` exists in `.mcp.json`
   - If missing -> Report to user with setup instructions

2. **Check Environment Variables**
   - Verify `KUBECONFIG` is set (check presence only, never expose value)
   - If missing -> Report to user

3. **Check Optional MCP Server**
   - If `ai-observability` is configured -> GPU pre-flight and post-deployment validation available
   - If not configured -> Skip GPU check and post-deployment metrics (non-blocking)

**Human Notification Protocol:**

When prerequisites fail:

```
Cannot execute model-deploy: MCP server `openshift` is not available

Setup Instructions:
1. Add openshift to `.mcp.json` (see: https://github.com/openshift/openshift-mcp-server)
2. Set KUBECONFIG environment variable: export KUBECONFIG="/path/to/kubeconfig"
3. Restart Claude Code to reload MCP servers

Documentation: https://github.com/openshift/openshift-mcp-server

How would you like to proceed?
Options:
- "setup" - Help configure the MCP server now
- "skip" - Skip this skill
- "abort" - Stop workflow

Please respond with your choice.
```

**SECURITY**: Never display actual KUBECONFIG path or credential values in output.

## When to Use This Skill

**Trigger this skill when:**
- User wants to deploy any AI/ML model on OpenShift AI
- User wants to create an InferenceService CR
- User wants to set up an inference endpoint for an LLM
- User wants to serve a model using vLLM, NIM, or Caikit+TGIS
- User explicitly invokes `/model-deploy` command

**User phrases that trigger this skill:**
- "Deploy Llama 3 on my cluster"
- "Set up a vLLM inference endpoint for Granite"
- "Deploy a model with NIM"
- "Create an InferenceService for Mixtral"
- "I need to serve a model on OpenShift AI"
- `/model-deploy` (explicit command)

**Do NOT use this skill when:**
- User wants to set up the NIM platform -> Use `/nim-setup` skill first
- User wants to create a custom ServingRuntime -> Use `/serving-runtime-config` skill instead
- User wants to debug a failing deployment -> Use `/debug-inference` skill instead
- User wants to analyze model performance -> Use `/ai-observability` skill instead
- User wants to set up a data science project -> Use `/ds-project-setup` skill instead

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

**Present recommendation:**

```
Based on [model-name] and [rationale]:

Recommended runtime: [runtime]
Reason: [why this runtime is best for this model]

Proceed with [runtime]? (yes / no / suggest alternative)
```

**WAIT for user confirmation.**

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

**Present hardware requirements:**

| Requirement | Value |
|-------------|-------|
| GPUs | [count]x [type] |
| VRAM | [total VRAM needed] |
| Key Args | [model-specific vLLM/NIM args] |

### Step 4: Pre-flight GPU Check (Optional)

**Condition**: Only if `ai-observability` MCP server is available.

**MCP Tool**: `get_gpu_info` (from ai-observability)

**Expected Output**: Cluster GPU inventory (count, vendors, models, VRAM)

**Compare** available GPUs against model requirements from Step 3:
- If sufficient GPUs available -> Report match and proceed
- If insufficient -> Warn user with options:
  - Use a smaller model variant
  - Use a quantized version (AWQ/GPTQ/FP8) to reduce GPU requirements
  - Deploy on a different cluster with adequate GPUs
  - Proceed anyway (user's risk)

**If ai-observability not available**: Skip with note: "GPU pre-flight check skipped (ai-observability MCP not configured). Ensure your cluster has sufficient GPUs."

### Step 5: Verify NIM Platform (NIM Runtime Only)

**Condition**: Only when the selected runtime is NIM.

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"accounts.nim.opendatahub.io"` - REQUIRED
- `namespace`: target namespace - REQUIRED
- `name`: `"nim-account"` - REQUIRED

**Expected Output**: Account object with ready status

**If Account CR not found or not ready:**
```
NIM platform is not set up in namespace [namespace].

The NIM runtime requires a one-time platform setup. Would you like to:
1. Run /nim-setup now to configure the NIM platform
2. Switch to vLLM runtime instead (no setup required)
3. Abort deployment

Please choose an option.
```

**WAIT for user decision.** If user chooses option 1, invoke `/nim-setup` skill.

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

**Display the complete InferenceService YAML** to the user.

**Show configuration summary table:**

| Setting | Value |
|---------|-------|
| Model | [model-name] |
| Runtime | [runtime-name] |
| GPUs | [count]x [type] |
| Namespace | [namespace] |
| Deployment Mode | [Serverless/RawDeployment] |
| Model Source | [source-uri] |

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
  - Example: `"my-ai-project"`

**Expected Output**: Created InferenceService object with `metadata.uid`

**Error Handling**:
- If namespace not found -> Report error, suggest creating namespace or using `/ds-project-setup`
- If ServingRuntime not found -> Report error, verify runtime name, suggest `/serving-runtime-config`
- If quota exceeded -> Report error, suggest reducing resource requests
- If RBAC error -> Report insufficient permissions

### Step 9: Monitor Rollout

Poll InferenceService status until ready or timeout (10 minutes).

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"inferenceservices.serving.kserve.io"` - REQUIRED
- `namespace`: target namespace - REQUIRED
- `name`: InferenceService name - REQUIRED

**Check predictor pod status:**

**MCP Tool**: `pod_list` (from openshift)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `labelSelector`: `"serving.kserve.io/inferenceservice=[model-name]"` - filter for relevant pods

**Show progress:**

```
Deployment Progress:

| Stage | Status |
|-------|--------|
| Pod Scheduled | [Pending/Complete] |
| Image Pulled | [Pending/Complete] |
| Container Started | [Pending/Complete] |
| Model Loaded | [Pending/Complete] |
| Ready | [Pending/Complete] |

Pod: [pod-name] | Status: [status] | Restarts: [count]
```

**On failure (Step 9a):**

Check pod logs and events for diagnostics:

**MCP Tool**: `pod_logs` (from openshift)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: pod name - REQUIRED

**MCP Tool**: `events_list` (from openshift)

**Parameters**:
- `namespace`: target namespace - REQUIRED

**Present diagnostic options:**

```
Deployment failed. Pod [pod-name] status: [status]

Error: [error-summary]

Options:
1. View full pod logs
2. Check namespace events
3. Invoke /debug-inference for detailed diagnosis
4. Delete InferenceService and retry
5. Continue waiting (may still be loading)

Which option would you like? (1-5)
```

**WAIT for user decision.**

Common failure patterns:
- **OOMKilled**: Model too large for allocated memory -> increase resources or use quantized model
- **GPU scheduling**: Insufficient GPUs -> check `get_gpu_info` or use fewer GPUs with quantization
- **ImagePullBackOff**: NIM image pull failure -> verify `/nim-setup` credentials
- **Model download timeout**: Large model on slow connection -> increase progress-deadline annotation
- **NGC auth failure**: Invalid or expired NGC API key -> re-run `/nim-setup`

### Step 10: Deployment Complete

**Report success:**

```
Model Deployment Successful

Model: [model-name]
Runtime: [runtime]
Namespace: [namespace]
GPUs: [count]x [type]

Inference Endpoint:
  URL: [endpoint-url]
  API: OpenAI-compatible REST

Quick Test:
  curl -X POST [endpoint-url]/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "[model-name]", "messages": [{"role": "user", "content": "Hello"}]}'

Next Steps:
  Monitor performance: "/ai-observability [model-name]"
  Configure monitoring: "/model-monitor [model-name]"
  Configure guardrails: "/guardrails-config [model-name]"
```

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

### Required MCP Servers
- `openshift` - OpenShift MCP server for Kubernetes resource CRUD
  - Source: https://github.com/openshift/openshift-mcp-server

### Optional MCP Servers
- `ai-observability` - AI Observability MCP server for GPU checks and deployment validation
  - Source: https://github.com/rh-ai-quickstart/ai-observability-summarizer

### Required MCP Tools
- `resources_get` (from openshift) - Check InferenceService status, ServingRuntimes, Account CR
  - **Used for**: Monitoring rollout, checking prerequisites, validating deployment
- `resources_list` (from openshift) - List ServingRuntimes, pods
  - **Used for**: Finding available runtimes, listing deployment pods
- `resources_create_or_update` (from openshift) - Create InferenceService CR
  - **Used for**: The core deployment operation
- `pod_list` (from openshift) - Check predictor pod status
  - **Used for**: Monitoring rollout progress
- `pod_logs` (from openshift) - Retrieve pod logs
  - **Used for**: Debugging deployment failures
- `events_list` (from openshift) - Check namespace events
  - **Used for**: Diagnosing scheduling and pull errors

### Optional MCP Tools
- `get_gpu_info` (from ai-observability) - Cluster GPU inventory
  - **Used for**: Pre-flight GPU validation (Step 4)
- `get_deployment_info` (from ai-observability) - Deployment detection
  - **Used for**: Post-deployment validation (Step 10)
- `analyze_vllm` (from ai-observability) - vLLM metrics analysis
  - **Used for**: Verifying metrics are flowing after deployment (Step 10)

### Related Skills
- `/nim-setup` - Prerequisite for NIM runtime deployments (creates NGC credentials and Account CR)
- `/debug-inference` - Troubleshoot InferenceService failures (invoked from Step 9a)
- `/ai-observability` - Analyze deployed model performance and GPU utilization
- `/serving-runtime-config` - Create custom ServingRuntime CRs for unsupported frameworks
- `/ds-project-setup` - Create a namespace with model serving enabled
- `/model-monitor` - Configure TrustyAI monitoring after deployment

### Reference Documentation
- [known-model-profiles.md](../../docs/references/known-model-profiles.md) - Hardware profiles for common models
- [supported-runtimes.md](../../docs/references/supported-runtimes.md) - Runtime capabilities and selection criteria
- [live-doc-lookup.md](../../docs/references/live-doc-lookup.md) - Protocol for fetching specs for unknown models
- [Red Hat OpenShift AI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_cloud_service/1) - Official RHOAI docs

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill creates InferenceService CRs that consume cluster GPU resources. You MUST:

1. **After Gathering Settings** (Step 1)
   - Display configuration table
   - Ask: "Are these settings correct? (yes/no/modify)"
   - Wait for explicit user confirmation

2. **After Runtime Selection** (Step 2)
   - Display recommended runtime with rationale
   - Ask: "Proceed with [runtime]? (yes/no/suggest alternative)"
   - Wait for explicit user confirmation

3. **Before Creating InferenceService** (Step 7)
   - Display the complete InferenceService YAML manifest
   - Display configuration summary table
   - Ask: "Proceed with creating this InferenceService? (yes/no/modify)"
   - Wait for explicit user confirmation
   - If "modify" -> ask what to change, regenerate, re-confirm

4. **On Deployment Failure** (Step 9a)
   - Present diagnostic options menu
   - Ask: "Which option would you like?"
   - Wait for user decision
   - **NEVER** auto-delete failed deployments

5. **Never Auto-Execute**
   - **NEVER** create an InferenceService without user reviewing the manifest
   - **NEVER** auto-select a runtime without user confirmation
   - **NEVER** delete or modify existing InferenceServices without confirmation
   - **NEVER** assume approval — always wait for explicit user confirmation

**Why This Matters:**
- **GPU Cost**: InferenceServices consume expensive GPU resources
- **Cluster Impact**: Deployments may affect other workloads competing for GPUs
- **Model Correctness**: Wrong runtime or configuration parameters lead to failed or incorrect inference
- **Security**: NIM deployments reference NGC credentials that must be correctly configured

## Security Considerations

- **NGC API Key**: Referenced via `secretKeyRef` in the InferenceService spec, never inline
- **KUBECONFIG**: Path and contents never exposed in output
- **Model Storage Credentials**: S3/OCI credentials referenced via existing Kubernetes secrets, not embedded in the InferenceService
- **Namespace Isolation**: All resources created in user-specified namespace only
- **Resource Limits**: Always specified in the InferenceService spec to prevent unbounded GPU/memory consumption
- **RBAC**: Skill checks for sufficient permissions before attempting resource creation

## Example Usage

### Example 1: Deploy Llama 3.1 8B with vLLM

```
User: "Deploy Llama 3.1 8B on my cluster"

Agent: [Invokes /model-deploy skill]
       [Reads supported-runtimes.md]

I consulted supported-runtimes.md to understand runtime capabilities.

Step 1 of 10: Gathering deployment information.

| Setting | Value | Source |
|---------|-------|--------|
| Model | Llama 3.1 8B Instruct | user input |
| Runtime | TBD | auto-detect |
| Namespace | ? | needs input |
| Model Source | ? | needs input |
| Deployment Mode | Serverless | default |

What namespace should I deploy to, and where are the model weights stored?
(e.g., S3 bucket, OCI registry, PVC)

User: "namespace: ai-models, model is on S3 at s3://my-bucket/llama-3.1-8b"

Agent: Step 2 of 10: Determining runtime.

I consulted supported-runtimes.md to understand runtime capabilities.

Based on Llama 3.1 8B (open-source HuggingFace model):

Recommended runtime: vLLM
Reason: Default runtime for open-source LLMs. Broad compatibility,
        OpenAI-compatible API, no additional setup required.

Proceed with vLLM? (yes / no / suggest alternative)

User: "yes"

Agent: Step 3 of 10: Looking up hardware profile.

I consulted known-model-profiles.md to find hardware requirements for Llama 3.1 8B.

| Requirement | Value |
|-------------|-------|
| GPUs | 1x A10G/L4/A100/H100 |
| VRAM | 16GB |
| Key Args | --max-model-len=4096 --tool-call-parser hermes |

Step 4 of 10: GPU pre-flight check skipped (ai-observability MCP not configured).
Ensure your cluster has at least 1 GPU with 16GB VRAM.

Step 5 of 10: Skipped (NIM platform check not needed for vLLM).

Step 6-7 of 10: Generating InferenceService YAML.

apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-3-1-8b
  namespace: ai-models
  annotations:
    serving.kserve.io/deploymentMode: Serverless
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: vllm-runtime
      storageUri: s3://my-bucket/llama-3.1-8b
      resources:
        limits:
          nvidia.com/gpu: "1"
        requests:
          cpu: "4"
          memory: "16Gi"
    args:
      - --max-model-len=4096
      - --tool-call-parser=hermes

| Setting | Value |
|---------|-------|
| Model | llama-3-1-8b |
| Runtime | vllm-runtime |
| GPUs | 1 |
| Namespace | ai-models |
| Mode | Serverless |

Proceed with creating this InferenceService? (yes/no/modify)

User: "yes"

Agent: Step 8 of 10: Creating InferenceService...
       [Creates via resources_create_or_update]

       InferenceService created. Monitoring rollout...

Step 9 of 10: Monitoring rollout.

| Stage | Status |
|-------|--------|
| Pod Scheduled | Complete |
| Image Pulled | Complete |
| Container Started | Complete |
| Model Loaded | Complete |
| Ready | Complete |

Step 10 of 10: Deployment complete!

Model Deployment Successful

Model: llama-3-1-8b
Runtime: vLLM
Namespace: ai-models
GPUs: 1

Inference Endpoint:
  URL: https://llama-3-1-8b-ai-models.apps.cluster.example.com
  API: OpenAI-compatible REST

Quick Test:
  curl -X POST https://llama-3-1-8b-ai-models.apps.cluster.example.com/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "llama-3-1-8b", "messages": [{"role": "user", "content": "Hello"}]}'

Next Steps:
  Monitor performance: "/ai-observability llama-3-1-8b"
```

### Example 2: Deploy a Model with NIM (NIM Not Set Up)

```
User: "Deploy Llama 3.1 70B with NIM"

Agent: [Invokes /model-deploy skill]
       ...
       Step 2: User requested NIM runtime.

       Step 5: Checking NIM platform...

NIM platform is not set up in namespace ai-models.

The NIM runtime requires a one-time platform setup. Would you like to:
1. Run /nim-setup now to configure the NIM platform
2. Switch to vLLM runtime instead (no setup required)
3. Abort deployment

User: "1"

Agent: [Invokes /nim-setup skill — walks through NGC credential setup]
       ...
       NIM Platform Setup Complete.

       Resuming model deployment...
       [Continues from Step 6 with NIM runtime]
```

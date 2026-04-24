# Mixtral 8x7B Instruct - Complete Deployment Guide

## Model Information

- **Model**: Mixtral 8x7B Instruct v0.1
- **Architecture**: Mixture of Experts (MoE) - 8 experts, 2 active per token
- **Parameters**: 47 billion total, ~13 billion active
- **HuggingFace ID**: `mistralai/Mixtral-8x7B-Instruct-v0.1`
- **Context Window**: 32,000 tokens (32K native support)
- **License**: Apache 2.0
- **GPU Requirements**: 1x NVIDIA H200 (or similar with 50GB+ VRAM)
- **VRAM Usage**: ~47GB
- **Use Case**: Fast inference, code generation, multilingual tasks, excellent quality-to-speed ratio

## Prerequisites

Before starting, ensure the following are installed and ready:

✅ **OpenShift Cluster**: Access with cluster-admin privileges  
✅ **GPU Operator**: Installed with GPUs available  
✅ **Red Hat OpenShift AI**: Installed (DataScienceCluster ready)  
✅ **Namespace and Storage**: Created per main documentation  
✅ **HuggingFace CLI**: Installed and authenticated per main documentation

For platform installation, storage setup, and HuggingFace CLI configuration, see [main documentation Sections 1-2.4](../../../air-gapped-env-setup.md#1-environment-pre-configuration).

### Verify GPU Availability

```bash
# Check GPU capacity and allocatable
oc describe nodes | awk '/Capacity:/,/Allocatable:/ {if (/nvidia.com\/gpu/) print "Capacity:", $0} /Allocatable:/,/Allocated resources:/ {if (/nvidia.com\/gpu/ && !/Capacity:/) print "Allocatable:", $0}'

# Expected output (X = number of GPUs in your cluster):
# Capacity:   nvidia.com/gpu:     X
# Allocatable:   nvidia.com/gpu:     X
```

---

## Complete Deployment Steps

### Step 1: Download Model (Internet-Connected Machine)

**✅ NO APPROVAL REQUIRED** - Mixtral 8x7B uses Apache 2.0 license (fully open)

**Prerequisites:** HuggingFace CLI installed and authenticated (see [main documentation Section 2.4](../../../air-gapped-env-setup.md#24-pre-download-models-internet-connected-machine))

**On a machine with internet access:**

```bash
# Login to HuggingFace (use your access token)
huggingface-cli login

# Download Mixtral 8x7B Instruct to cache directory
# Note: This is ~94GB - ensure you have sufficient disk space
# Note: ./models/cache is excluded from git via .gitignore
hf download mistralai/Mixtral-8x7B-Instruct-v0.1 \
  --local-dir ./models/cache/Mixtral/Mixtral-8x7B-Instruct-v0.1

# Verify download (should show ~19 files)
ls -lh ./models/cache/Mixtral/Mixtral-8x7B-Instruct-v0.1/
du -sh ./models/cache/Mixtral/Mixtral-8x7B-Instruct-v0.1/
```

---

### Step 2: Upload Model to OpenShift PVC

**Prerequisites:**
- `llm-models` namespace exists
- `models-storage` PVC exists and is bound
- `model-loader` pod is running
- `oc` CLI configured with access to the cluster

See [main documentation Sections 1-2](../../../README.md#21-prepare-shared-model-storage-one-time-setup) for setup instructions.

> **⚠️ NOTE**: This guide assumes the machine where you downloaded the model has direct `oc` access to the OpenShift cluster. If you access the cluster through a bastion/jump host, transfer the model directory to that bastion first before proceeding with the upload steps below.

**Upload to PVC:**

```bash
# Create destination directory in PVC
oc exec -n llm-models model-loader -- mkdir -p /mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1

# Copy model to PVC (with progress) - This will take 30-60 minutes for ~94GB
oc rsync --progress ./models/cache/Mixtral/Mixtral-8x7B-Instruct-v0.1/ llm-models/model-loader:/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1/

# Verify model files are present
oc exec -n llm-models model-loader -- ls -lh /mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1/
oc exec -n llm-models model-loader -- du -sh /mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1/
```

**Expected Output (ls -lh):**
```
total XXXM
-rw-r--r-- 1 ... config.json
-rw-r--r-- 1 ... generation_config.json
-rw-r--r-- 1 ... model-00001-of-00019.safetensors
-rw-r--r-- 1 ... model-00002-of-00019.safetensors
...
-rw-r--r-- 1 ... tokenizer.json
```

---

### Step 3: Deploy Model with OpenShift AI

This deployment uses **OpenShift AI RawDeployment mode** with KServe API (ServingRuntime + InferenceService).

#### 3.1. Create ServingRuntime

The ServingRuntime defines **HOW** to serve models (vLLM configuration, GPU allocation, resource limits).

```bash
oc apply -f models/mixtral-8x7b-instruct/servingruntime.yaml
```

**Verify ServingRuntime created:**
```bash
oc get servingruntime -n llm-models
```

**Expected output:**
```
NAME                        DISABLED   MODELTYPE   CONTAINERS   AGE
vllm-mixtral-8x7b-runtime   false      vLLM        kserve       10s
```

---

#### 3.2. Create InferenceService

The InferenceService defines **WHAT** model to serve (references the ServingRuntime and PVC).

```bash
oc apply -f models/mixtral-8x7b-instruct/inferenceservice.yaml
```

**Verify InferenceService created:**
```bash
oc get inferenceservice -n llm-models
```

**Expected output:**
```
NAME             URL                                           READY   PREV   LATEST
mixtral-8x7b     http://mixtral-8x7b.llm-models.svc.cluster    True           100
```

---

#### 3.3. Create Route for External Access

```bash
oc apply -f models/mixtral-8x7b-instruct/route-inferenceservice.yaml
```

**Get route URL:**
```bash
oc get route mixtral-8x7b-inference -n llm-models
```

**Expected output:**
```
NAME                      HOST/PORT                                               
mixtral-8x7b-inference    mixtral-8x7b-inference-llm-models.apps.example.com
```

---

### Step 4: Monitor Deployment

```bash
# Watch pod status (model loading takes 2-4 minutes for 8x7B)
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x7b -w

# Check pod events
oc describe pod -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x7b

# Follow logs (watch for "Application startup complete")
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x7b -o name | head -1)
oc logs -f $POD -n llm-models
```

**Key Log Messages to Look For:**
```
INFO: Starting to load model /mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1...
INFO: Loading MoE model with 8 experts (2 active per token)...
INFO: Loading weights took X seconds
INFO: Model loading took ~47 GiB memory
INFO: Application startup complete
```

**Pod Status Progression:**
```
NAME                                   READY   STATUS              RESTARTS   AGE
mixtral-8x7b-xxxxx-xxxxx               0/1     ContainerCreating   0          10s
mixtral-8x7b-xxxxx-xxxxx               0/1     Running             0          30s
mixtral-8x7b-xxxxx-xxxxx               1/1     Running             0          3m
```

---

### Step 5: Test Model API

```bash
# Get route URL
ROUTE_URL=$(oc get route mixtral-8x7b-inference -n llm-models -o jsonpath='{.spec.host}')
echo "Model endpoint: https://$ROUTE_URL"

# Test health endpoint
curl -k https://$ROUTE_URL/health

# List available models
curl -k https://$ROUTE_URL/v1/models

# Test simple completion
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1",
    "messages": [
      {"role": "user", "content": "Explain the Mixture of Experts architecture in one paragraph."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }'

# Test code generation
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1",
    "messages": [
      {"role": "system", "content": "You are an expert Python developer."},
      {"role": "user", "content": "Write a Python function to implement binary search with type hints."}
    ],
    "max_tokens": 400,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

# Test context retention
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1",
    "messages": [
      {"role": "user", "content": "My favorite programming language is Python"},
      {"role": "assistant", "content": "Great choice! Python is excellent for many use cases."},
      {"role": "user", "content": "What is my favorite programming language?"}
    ],
    "max_tokens": 50,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

# Test streaming response
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1",
    "messages": [
      {"role": "user", "content": "Explain asyncio in Python."}
    ],
    "max_tokens": 300,
    "stream": true
  }'
```

**Expected Response (example):**
```json
{
  "id": "chatcmpl-xxxxxxxxxxxxxxxx",
  "object": "chat.completion",
  "created": 1776789362,
  "model": "/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Mixture of Experts (MoE) is an architecture...",
        "refusal": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 85,
    "total_tokens": 113
  }
}
```

---

### Step 6: Performance Validation

```bash
# Check GPU utilization
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x7b -o name | head -1)
oc exec $POD -c kserve-container -- nvidia-smi

# Check vLLM metrics
curl -k https://$ROUTE_URL/metrics

# Get pod resource usage
oc adm top pod -n llm-models
```

**Expected nvidia-smi Output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2   |
|-------------------------------+----------------------+----------------------+
|   0  NVIDIA H200             On   | xxxxxxxxxx      |      0%      48C   |
| N/A   150W / 700W |  47000MiB / 143871MiB |      20%      Default |
+-------------------------------+----------------------+----------------------+
```

---

### Step 7: Configure OpenCode (Optional)

If you want to use this model with OpenCode for AI-assisted development:

#### 7.1. Update Base URL

First, get your deployed model's route URL:

```bash
ROUTE_URL=$(oc get route mixtral-8x7b-inference -n llm-models -o jsonpath='{.spec.host}')
echo "https://$ROUTE_URL/v1"
```

Edit `opencode.json` and update the `baseURL` with your route:

```json
{
  "provider": {
    "openshift-ai-mixtral": {
      "options": {
        "baseURL": "https://YOUR-ROUTE-URL/v1"
      }
    }
  }
}
```

#### 7.2. Copy Configuration

```bash
# Copy to your project directory
cp models/mixtral-8x7b-instruct/opencode.json /path/to/your/project/

# Or configure globally
mkdir -p ~/.config/opencode
cp models/mixtral-8x7b-instruct/opencode.json ~/.config/opencode/
```

#### 7.3. Start OpenCode

```bash
cd /path/to/your/project
opencode
```

OpenCode will now use your air-gapped Mixtral 8x7B model.

---

### OpenCode Configuration Reference

The `opencode.json` file configures Open Code to use your deployed model:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openshift-ai-mixtral": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "OpenShift AI - Mixtral 8x7B",
      "options": {
        "baseURL": "https://mixtral-8x7b-inference-llm-models.apps.example.com/v1"
      },
      "models": {
        "/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1": {
          "name": "Mixtral 8x7B Instruct (Air-Gapped)",
          "description": "Mixtral 8x7B MoE model deployed on OpenShift AI with vLLM and NVIDIA H200 GPU",
          "limit": {
            "context": 32768,
            "output": 2048
          }
        }
      }
    }
  },
  "model": "openshift-ai-mixtral//mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1"
}
```

#### Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `$schema` | `https://opencode.ai/config.json` | JSON schema for validation |
| `provider.*.npm` | `@ai-sdk/openai-compatible` | AI SDK provider for OpenAI-compatible APIs |
| `provider.*.name` | `OpenShift AI - Mixtral 8x7B` | Display name in Open Code |
| `provider.*.options.baseURL` | `https://<route>/v1` | Your model's OpenAI-compatible API endpoint |
| `models.*.limit.context` | `32768` | Total context window in tokens |
| `models.*.limit.output` | `2048` | Maximum output tokens per response |
| `model` | `openshift-ai-mixtral//mnt/...` | Active model identifier |

#### Understanding Token Limits

**The `limit` configuration is critical** for Open Code to work correctly:

```json
"limit": {
  "context": 32768,    // Total tokens (input + output)
  "output": 2048       // Maximum response length
}
```

**Why is `output` set to 2048?**

Open Code automatically loads context (skills, documentation, conversation history) that can consume **significant tokens**. With a 32K context window:

- **Typical Open Code context**: 15k-25k tokens (skills, system prompts, conversation)
- **Available for output**: 7k-17k tokens
- **Current configuration**: 2048 tokens provides good response length while leaving room for complex prompts

**If you see errors like:**
```
This model's maximum context length is 32768 tokens. However, you requested 
X output tokens and your prompt contains at least Y input tokens...
```

**Solution**: Reduce `output` to 1024 or 512 if working with very skill-heavy workflows.

#### Adjusting Token Limits

**For basic prompts without skills:**
```json
"limit": {
  "context": 32768,
  "output": 4096      // More room for longer responses
}
```

**For skill-heavy workflows (current configuration):**
```json
"limit": {
  "context": 32768,
  "output": 2048      // Balanced for skills + good response length
}
```

**Trade-off**: Lower `output` = shorter responses but more room for complex prompts.

#### Troubleshooting

**Problem**: "Unrecognized key: maxTokens"  
**Solution**: Use `limit.output` instead of `maxTokens` in the models section

**Problem**: "max_tokens is too large"  
**Solution**: Reduce `limit.output` in `opencode.json`

**Problem**: Context overflow with skills loaded  
**Solution**: 
1. Reduce `limit.output` to 512 or lower
2. Uninstall unused skills (`lola uninstall <module>`)
3. Use prompts without loading many skills at once

---

## Configuration Reference

### ServingRuntime Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Runtime Name** | `vllm-mixtral-8x7b-runtime` | ServingRuntime identifier |
| **Container Image** | `vllm/vllm-openai:latest` | Official vLLM OpenAI-compatible image |
| **Model Path** | `/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1` | Location in PVC |
| **GPUs** | 1 | Single GPU (no tensor parallelism) |
| **Max Model Length** | 32768 | Context window size in tokens (32K) |
| **Max Num Seqs** | 128 | Maximum concurrent sequences |
| **GPU Memory Util** | 0.90 | Percentage of VRAM to use (90%) |
| **Port** | 8080 | vLLM API port (KServe standard) |
| **Tool Call Parser** | hermes | Enable structured output/tool calling |

### Resource Allocation

```yaml
resources:
  requests:
    cpu: "8"
    memory: 64Gi
    nvidia.com/gpu: "1"
  limits:
    cpu: "16"
    memory: 128Gi
    nvidia.com/gpu: "1"
```

**Note**: Mixtral 8x7B is very efficient:
- **1 GPU only** - no tensor parallelism needed
- **128GB system RAM** recommended
- **~47GB VRAM** usage (plenty of room for KV cache on H200)
- **No quantization** - full precision for best quality

### InferenceService Configuration

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: mixtral-8x7b
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: vllm-mixtral-8x7b-runtime
      storageUri: pvc://models-storage/
    minReplicas: 1
    maxReplicas: 1
```

**Key Points:**
- `deploymentMode: RawDeployment` - Creates standard Kubernetes Deployment (not Knative)
- `runtime: vllm-mixtral-8x7b-runtime` - References the ServingRuntime
- `storageUri: pvc://models-storage/` - KServe syntax for PVC storage

---

## Performance Expectations

Based on 1x NVIDIA H200 GPU:

- **First Token Latency (TTFT)**: 30-60ms (very fast due to MoE)
- **Generation Speed**: 100-150 tokens/second (excellent throughput)
- **VRAM Usage**: ~47GB (leaves 96GB for KV cache on H200)
- **System RAM Usage**: ~40GB
- **Concurrent Requests**: 10-20 users with moderate contexts (8K+), 30-50 with short contexts (<2K)
- **Context Window**: 32,768 tokens (32K native support)
- **Model Loading Time**: 2-4 minutes (much faster than larger models)

**MoE Advantage**: Mixtral 8x7B activates only ~13B parameters per token (vs 47B total), resulting in:
- **3-4x faster** than dense 47B models
- **Similar quality** to models 2-3x larger
- **Excellent context retention** (no quantization issues)

---

## Scaling

### Horizontal Scaling (Multiple Replicas)

```bash
# Edit InferenceService
oc edit inferenceservice mixtral-8x7b -n llm-models

# Change:
# spec:
#   predictor:
#     minReplicas: 2
#     maxReplicas: 2

# Verify both pods are running
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x7b

# Service automatically load balances across replicas
```

**⚠️ Important**: Each replica requires **1 GPU**. For 2 replicas, you need **2 total GPUs** in your cluster.

### Vertical Scaling (Extended Context)

Mixtral 8x7B uses 32K context natively. You can reduce it if you need more concurrent request capacity:

```bash
# Edit ServingRuntime to reduce context window (increases throughput)
oc edit servingruntime vllm-mixtral-8x7b-runtime -n llm-models

# Change:
# args:
#   - --max-model-len
#   - "32768"
# to:
#   - --max-model-len
#   - "16384"

# Delete pod to restart with new config
oc delete pod -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x7b
```

**Note**: With 96GB of KV cache available, you have plenty of room for long contexts.

---

## Troubleshooting and Advanced Topics

For security hardening, monitoring, observability, and detailed troubleshooting procedures, see:

**📖 [troubleshooting.md](./troubleshooting.md)**

Includes:
- Security hardening (NetworkPolicy, OAuth authentication)
- Monitoring and observability (GPU metrics, vLLM metrics, logs)
- Common issues and solutions (CUDA errors, startup failures, performance issues)
- MoE-specific troubleshooting

---

## API Reference

### OpenAI-Compatible Endpoints

- **Base URL**: `https://<route-url>`
- **Authentication**: None (internal cluster use)

#### Chat Completions

```bash
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 200,
  "temperature": 0.7,
  "stream": false
}
```

#### Text Completions

```bash
POST /v1/completions
Content-Type: application/json

{
  "model": "/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1",
  "prompt": "Once upon a time",
  "max_tokens": 200,
  "temperature": 0.7
}
```

#### List Models

```bash
GET /v1/models
```

#### Health Check

```bash
GET /health
```

#### Metrics (Prometheus)

```bash
GET /metrics
```

---

## Model Strengths

Mixtral 8x7B Instruct excels at:

- **Fast Inference**: 3-4x faster than dense models of similar quality due to MoE
- **Code Generation**: Strong performance on Python, JavaScript, Go, Rust, and more
- **Multilingual**: Excellent across English, French, German, Spanish, Italian
- **Instruction Following**: Fine-tuned for precise instruction adherence
- **Context Retention**: Full precision (no quantization) = perfect context memory
- **Mathematical Reasoning**: Good performance on math and logic tasks
- **Tool Calling**: Built-in support with Hermes parser for structured outputs
- **Efficiency**: Only 47GB VRAM = fits comfortably on 1 GPU with room for large KV cache

**Perfect For**:
- **OpenCode/Agentic workflows** (needs context retention)
- **Real-time code assistance** (fast TTFT)
- **Production deployments** (1 GPU = lower cost)
- **Multi-user environments** (high concurrent capacity)

---

## References

- **HuggingFace Model Card**: https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1
- **Mistral AI Blog**: https://mistral.ai/news/mixtral-of-experts/
- **MoE Paper**: https://arxiv.org/abs/1701.06538
- **vLLM Documentation**: https://docs.vllm.ai/
- **License**: Apache 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
- **Main Documentation**: [air-gapped-env-setup.md](../../../air-gapped-env-setup.md)

---

## Cleanup

To remove the Mixtral 8x7B model deployment:

```bash
# Delete InferenceService (automatically deletes pods and services)
oc delete inferenceservice mixtral-8x7b -n llm-models

# Delete Route
oc delete route mixtral-8x7b-inference -n llm-models

# Delete ServingRuntime (if not used by other models)
oc delete servingruntime vllm-mixtral-8x7b-runtime -n llm-models

# Verify deletion
oc get inferenceservice,servingruntime,route -n llm-models
```

**Note**: This removes the deployment but keeps the model files in the PVC. To remove model files (~94GB), delete the directory `/mnt/models/Mixtral/Mixtral-8x7B-Instruct-v0.1/` from the PVC using the model-loader pod.

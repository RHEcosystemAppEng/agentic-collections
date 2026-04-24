# Mixtral 8x22B Instruct - Complete Deployment Guide

## Model Information

- **Model**: Mixtral 8x22B Instruct v0.1
- **Architecture**: Mixture of Experts (MoE) - 8 experts, 2 active per token
- **Parameters**: 141 billion total, ~39 billion active
- **HuggingFace ID**: `mistralai/Mixtral-8x22B-Instruct-v0.1`
- **Context Window**: 64,000 tokens (64K native support)
- **License**: Apache 2.0
- **GPU Requirements**: 4x NVIDIA H200 (141GB each) - Requires ~131GB VRAM total
- **VRAM Usage**: ~131GB (full precision, no quantization)
- **Use Case**: Advanced reasoning, multilingual tasks, code generation, fast inference with MoE architecture

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

**✅ NO APPROVAL REQUIRED** - Mixtral 8x22B uses Apache 2.0 license (fully open)

**Prerequisites:** HuggingFace CLI installed and authenticated (see [main documentation Section 2.4](../../../air-gapped-env-setup.md#24-pre-download-models-internet-connected-machine))

**On a machine with internet access:**

```bash
# Login to HuggingFace (use your access token)
huggingface-cli login

# Download Mixtral 8x22B Instruct to cache directory
# Note: This is ~280GB - ensure you have sufficient disk space
# Note: ./models/cache is excluded from git via .gitignore
hf download mistralai/Mixtral-8x22B-Instruct-v0.1 \
  --local-dir ./models/cache/Mixtral/Mixtral-8x22B-Instruct-v0.1

# Verify download (should show ~100+ files)
ls -lh ./models/cache/Mixtral/Mixtral-8x22B-Instruct-v0.1/
du -sh ./models/cache/Mixtral/Mixtral-8x22B-Instruct-v0.1/
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
oc exec -n llm-models model-loader -- mkdir -p /mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1

# Copy model to PVC (with progress) - This will take 2-3 hours for 280GB
oc rsync --progress ./models/cache/Mixtral/Mixtral-8x22B-Instruct-v0.1/ llm-models/model-loader:/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1/

# Verify model files are present
oc exec -n llm-models model-loader -- ls -lh /mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1/
oc exec -n llm-models model-loader -- du -sh /mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1/
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
oc apply -f models/mixtral-8x22b-instruct/servingruntime.yaml
```

**Verify ServingRuntime created:**
```bash
oc get servingruntime -n llm-models
```

**Expected output:**
```
NAME                   DISABLED   MODELTYPE   CONTAINERS   AGE
vllm-mixtral-runtime   false      vLLM        kserve       10s
```

---

#### 3.2. Create InferenceService

The InferenceService defines **WHAT** model to serve (references the ServingRuntime and PVC).

```bash
oc apply -f models/mixtral-8x22b-instruct/inferenceservice.yaml
```

**Verify InferenceService created:**
```bash
oc get inferenceservice -n llm-models
```

**Expected output:**
```
NAME              URL                                            READY   PREV   LATEST
mixtral-8x22b     http://mixtral-8x22b.llm-models.svc.cluster    True           100
```

---

#### 3.3. Create Route for External Access

```bash
oc apply -f models/mixtral-8x22b-instruct/route-inferenceservice.yaml
```

**Get route URL:**
```bash
oc get route mixtral-8x22b-inference -n llm-models
```

**Expected output:**
```
NAME                       HOST/PORT                                               
mixtral-8x22b-inference    mixtral-8x22b-inference-llm-models.apps.example.com
```

---

### Step 4: Monitor Deployment

```bash
# Watch pod status (model loading takes 3-8 minutes for MoE)
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -w

# Check pod events
oc describe pod -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b

# Follow logs (watch for "Application startup complete")
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
oc logs -f $POD -n llm-models
```

**Key Log Messages to Look For:**
```
INFO: Starting to load model /mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1...
INFO: Initializing tensor-parallel processes (4 GPUs)...
INFO: Loading MoE model with 8 experts (2 active per token)...
INFO: Loading weights took X seconds
INFO: Model loading took ~131 GiB memory across 4 GPUs
INFO: Application startup complete
```

**Pod Status Progression:**
```
NAME                                    READY   STATUS              RESTARTS   AGE
mixtral-8x22b-xxxxx-xxxxx               0/1     ContainerCreating   0          10s
mixtral-8x22b-xxxxx-xxxxx               0/1     Running             0          30s
mixtral-8x22b-xxxxx-xxxxx               1/1     Running             0          8m
```

**Note**: MoE models load faster than dense models of similar quality.

---

### Step 5: Test Model API

```bash
# Get route URL
ROUTE_URL=$(oc get route mixtral-8x22b-inference -n llm-models -o jsonpath='{.spec.host}')
echo "Model endpoint: https://$ROUTE_URL"

# Test health endpoint
curl -k https://$ROUTE_URL/health

# List available models
curl -k https://$ROUTE_URL/v1/models

# Test simple completion
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1",
    "messages": [
      {"role": "user", "content": "Explain the Mixture of Experts architecture in one paragraph."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }'

# Test multilingual capability (Mixtral excels at multilingual tasks)
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1",
    "messages": [
      {"role": "user", "content": "Explica la arquitectura de Mixture of Experts en español."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

# Test advanced reasoning
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1",
    "messages": [
      {"role": "system", "content": "You are an expert software architect."},
      {"role": "user", "content": "Design a distributed caching system with eventual consistency. Consider CAP theorem implications."}
    ],
    "max_tokens": 1024,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

# Test code generation
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1",
    "messages": [
      {"role": "system", "content": "You are a senior backend engineer."},
      {"role": "user", "content": "Implement a thread-safe LRU cache in Python with O(1) operations."}
    ],
    "max_tokens": 800,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

# Test streaming response
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1",
    "messages": [
      {"role": "user", "content": "Explain quantum entanglement step by step."}
    ],
    "max_tokens": 400,
    "stream": true
  }'
```

**Expected Response (example):**
```json
{
  "id": "chatcmpl-xxxxxxxxxxxxxxxx",
  "object": "chat.completion",
  "created": 1776789362,
  "model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Mixture of Experts (MoE) is an architecture where multiple specialized neural networks (experts) work together...",
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
# Check GPU utilization (should show all 4 GPUs)
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
oc exec $POD -c kserve-container -- nvidia-smi

# Check vLLM metrics
curl -k https://$ROUTE_URL/metrics

# Get pod resource usage
oc adm top pod -n llm-models
```

**Expected nvidia-smi Output (4 GPUs):**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2   |
|-------------------------------+----------------------+----------------------+
|   0  NVIDIA H200             On   | xxxxxxxxxx      |      0%      50C   |
| N/A   200W / 700W |  33000MiB / 143871MiB |      25%      Default |
|-------------------------------+----------------------+----------------------+
|   1  NVIDIA H200             On   | xxxxxxxxxx      |      0%      50C   |
| N/A   200W / 700W |  33000MiB / 143871MiB |      25%      Default |
|-------------------------------+----------------------+----------------------+
|   2  NVIDIA H200             On   | xxxxxxxxxx      |      0%      50C   |
| N/A   200W / 700W |  33000MiB / 143871MiB |      25%      Default |
|-------------------------------+----------------------+----------------------+
|   3  NVIDIA H200             On   | xxxxxxxxxx      |      0%      50C   |
| N/A   200W / 700W |  33000MiB / 143871MiB |      25%      Default |
+-------------------------------+----------------------+----------------------+

Total VRAM Usage: ~131GB across 4 GPUs (~33GB per GPU)
```

---

### Step 7: Configure OpenCode (Optional)

If you want to use this model with OpenCode for AI-assisted development:

#### 7.1. Update Base URL

First, get your deployed model's route URL:

```bash
ROUTE_URL=$(oc get route mixtral-8x22b-inference -n llm-models -o jsonpath='{.spec.host}')
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
cp models/mixtral-8x22b-instruct/opencode.json /path/to/your/project/

# Or configure globally
mkdir -p ~/.config/opencode
cp models/mixtral-8x22b-instruct/opencode.json ~/.config/opencode/
```

#### 7.3. Start OpenCode

```bash
cd /path/to/your/project
opencode
```

OpenCode will now use your air-gapped Mixtral 8x22B model.

---

### OpenCode Configuration Reference

The `opencode.json` file configures Open Code to use your deployed model:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openshift-ai-mixtral": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "OpenShift AI - Mixtral 8x22B",
      "options": {
        "baseURL": "https://mixtral-8x22b-inference-llm-models.apps.example.com/v1"
      },
      "models": {
        "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1": {
          "name": "Mixtral 8x22B Instruct (Air-Gapped)",
          "description": "Mixtral 8x22B MoE model deployed on OpenShift AI with vLLM and 4x NVIDIA H200 GPUs",
          "limit": {
            "context": 65536,
            "output": 8192
          }
        }
      }
    }
  },
  "model": "openshift-ai-mixtral//mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1"
}
```

#### Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `$schema` | `https://opencode.ai/config.json` | JSON schema for validation |
| `provider.*.npm` | `@ai-sdk/openai-compatible` | AI SDK provider for OpenAI-compatible APIs |
| `provider.*.name` | `OpenShift AI - Mixtral 8x22B` | Display name in Open Code |
| `provider.*.options.baseURL` | `https://<route>/v1` | Your model's OpenAI-compatible API endpoint |
| `models.*.limit.context` | `65536` | Total context window in tokens (64K) |
| `models.*.limit.output` | `8192` | Maximum output tokens per response |
| `model` | `openshift-ai-mixtral//mnt/...` | Active model identifier |

#### Understanding Token Limits

**The `limit` configuration is critical** for Open Code to work correctly:

```json
"limit": {
  "context": 65536,    // Total tokens (input + output) - 64K window
  "output": 8192       // Maximum response length
}
```

**Why is `output` set to 8192?**

With a 64K context window, Mixtral 8x22B can handle substantial context. Open Code automatically loads context (skills, documentation, conversation history):

- **Typical Open Code context**: 20k-40k tokens (skills, system prompts, conversation)
- **Available for output**: 25k-45k tokens
- **Recommended default**: 8192 tokens (8K) balances response length with input capacity

**If you see errors like:**
```
This model's maximum context length is 65536 tokens. However, you requested 
X output tokens and your prompt contains at least Y input tokens...
```

**Solution**: Reduce `output` to 4096 or 2048, or reduce loaded skills.

#### Adjusting Token Limits

**For long-form content generation:**
```json
"limit": {
  "context": 65536,
  "output": 16384     // Maximum output for complex responses
}
```

**For basic prompts without skills:**
```json
"limit": {
  "context": 65536,
  "output": 8192      // Balanced configuration
}
```

**For skill-heavy workflows with complex context:**
```json
"limit": {
  "context": 65536,
  "output": 4096      // More room for large skill content
}
```

**Trade-off**: Lower `output` = shorter responses but more room for complex prompts and skills.

#### Troubleshooting

**Problem**: "Unrecognized key: maxTokens"  
**Solution**: Use `limit.output` instead of `maxTokens` in the models section

**Problem**: "max_tokens is too large"  
**Solution**: Reduce `limit.output` in `opencode.json`

**Problem**: Context overflow with skills loaded  
**Solution**: 
1. Reduce `limit.output` to 4096 or lower
2. Uninstall unused skills (`lola uninstall <module>`)
3. Use prompts without loading many skills at once

---

## Configuration Reference

### ServingRuntime Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Runtime Name** | `vllm-mixtral-runtime` | ServingRuntime identifier |
| **Container Image** | `vllm/vllm-openai:latest` | Official vLLM OpenAI-compatible image |
| **Model Path** | `/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1` | Location in PVC |
| **GPUs** | 4 | Number of GPUs allocated (required for MoE) |
| **Tensor Parallel Size** | 4 | Distribute model across 4 GPUs |
| **Max Model Length** | 65536 | Context window size in tokens (64K) |
| **Max Num Seqs** | 128 | Maximum concurrent sequences |
| **GPU Memory Util** | 0.90 | Percentage of VRAM to use (90%) |
| **Port** | 8080 | vLLM API port (KServe standard) |
| **Tool Call Parser** | hermes | Enable structured output/tool calling |

### Resource Allocation

```yaml
resources:
  requests:
    cpu: "32"
    memory: 256Gi
    nvidia.com/gpu: "4"
  limits:
    cpu: "64"
    memory: 512Gi
    nvidia.com/gpu: "4"
```

**Note**: Mixtral 8x22B MoE architecture:
- **4 GPUs** for tensor parallelism (full precision, no quantization)
- **512GB system RAM** recommended
- **~131GB VRAM** total across GPUs (full precision)
- **Faster inference** than dense models due to MoE (only 39B params active)
- **Perfect context retention** with no quantization

### InferenceService Configuration

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: mixtral-8x22b
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
    openshift.io/display-name: "Mixtral 8x22B Instruct"
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: vllm-mixtral-runtime
      storageUri: pvc://models-storage/
    minReplicas: 1
    maxReplicas: 1
```

**Key Points:**
- `deploymentMode: RawDeployment` - Creates standard Kubernetes Deployment (not Knative)
- `runtime: vllm-mixtral-runtime` - References the ServingRuntime
- `storageUri: pvc://models-storage/` - KServe syntax for PVC storage
- Single replica recommended initially; scale based on load

---

## Performance Expectations

Based on 4x NVIDIA H200 GPUs with tensor parallelism and MoE architecture:

- **First Token Latency (TTFT)**: 30-60ms (faster than dense models due to MoE)
- **Generation Speed**: 120-180 tokens/second (significantly faster than dense 70B models)
- **VRAM Usage**: ~131GB total across 4 GPUs (~33GB per GPU)
- **System RAM Usage**: ~150GB
- **Concurrent Requests**: 10-15 users with long contexts (32K+), 20-30 with short contexts (<8K)
- **Context Window**: 65,536 tokens (64K native support)
- **Model Loading Time**: 4-10 minutes (multi-GPU initialization)

**MoE Advantage**: Mixtral 8x22B activates only ~39B parameters per token (vs 70B+ in dense models), resulting in much faster inference while maintaining quality comparable to larger dense models.

**Full Precision Benefit**: No quantization means perfect context retention and attention mechanisms work as designed.

---

## Scaling

### Horizontal Scaling (Multiple Replicas)

```bash
# Edit InferenceService
oc edit inferenceservice mixtral-8x22b -n llm-models

# Change:
# spec:
#   predictor:
#     minReplicas: 2
#     maxReplicas: 2

# Verify both pods are running
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b

# Service automatically load balances across replicas
```

**⚠️ Important**: Each replica requires **4 GPUs**. For 2 replicas, you need **8 total GPUs** in your cluster.

### Vertical Scaling (Extended Context)

Mixtral 8x22B uses 64K context natively. You can reduce it if you need more concurrent request capacity:

```bash
# Edit ServingRuntime to reduce context window (increases throughput)
oc edit servingruntime vllm-mixtral-runtime -n llm-models

# Change:
# args:
#   - --max-model-len
#   - "65536"
# to:
#   - --max-model-len
#   - "32768"

# Delete pod to restart with new config
oc delete pod -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b
```

**Note**: Longer context windows require more VRAM and reduce concurrent request capacity.

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
  "model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 1024,
  "temperature": 0.7,
  "stream": false
}
```

#### Text Completions

```bash
POST /v1/completions
Content-Type: application/json

{
  "model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1",
  "prompt": "Once upon a time",
  "max_tokens": 1024,
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

Mixtral 8x22B Instruct excels at:

- **Mixture of Experts Architecture**: Efficient inference with sparse activation (39B params active vs 141B total)
- **Fast Inference**: 2-3x faster than dense models of similar quality due to MoE
- **Multilingual Excellence**: Top-tier performance across English, French, German, Spanish, Italian
- **Advanced Reasoning**: Competitive with GPT-4 on many reasoning benchmarks
- **Code Generation**: Strong performance on HumanEval and MBPP coding benchmarks
- **Long Context**: 64K context window with good needle-in-haystack performance
- **Mathematical Reasoning**: Excellent on MATH and GSM8K benchmarks
- **Instruction Following**: Fine-tuned for precise instruction adherence

**MoE Benefits**:
- Lower inference cost per token
- Faster response times
- Reduced memory bandwidth requirements
- Better quality-to-speed ratio than dense models

---

## References

- **HuggingFace Model Card**: https://huggingface.co/mistralai/Mixtral-8x22B-Instruct-v0.1
- **Mistral AI Blog**: https://mistral.ai/news/mixtral-8x22b/
- **MoE Paper**: https://arxiv.org/abs/1701.06538
- **vLLM Documentation**: https://docs.vllm.ai/
- **License**: Apache 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
- **Main Documentation**: [air-gapped-env-setup.md](../../../air-gapped-env-setup.md)

---

## Cleanup

To remove the Mixtral 8x22B model deployment:

```bash
# Delete InferenceService (automatically deletes pods and services)
oc delete inferenceservice mixtral-8x22b -n llm-models

# Delete Route
oc delete route mixtral-8x22b-inference -n llm-models

# Delete ServingRuntime (if not used by other models)
oc delete servingruntime vllm-mixtral-runtime -n llm-models

# Verify deletion
oc get inferenceservice,servingruntime,route -n llm-models
```

**Note**: This removes the deployment but keeps the model files in the PVC. To remove model files (~280GB), delete the directory `/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1/` from the PVC using the model-loader pod.

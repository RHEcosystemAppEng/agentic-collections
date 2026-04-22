# Qwen 2.5 7B Instruct - Complete Deployment Guide

## Model Information

- **Model**: Qwen 2.5 7B Instruct
- **Parameters**: 7 billion
- **HuggingFace ID**: `Qwen/Qwen2.5-7B-Instruct`
- **Context Window**: 32,768 tokens (supports up to 128K)
- **License**: Apache 2.0
- **GPU Requirements**: 1x NVIDIA H200 (or similar with 14GB+ VRAM)
- **VRAM Usage**: ~14GB
- **Use Case**: Code generation, multilingual, math, reasoning

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

**Good news:** Qwen 2.5 7B Instruct is **open-access** - no approval needed! 🎉

**Prerequisites:** HuggingFace CLI installed and authenticated (see [main documentation Section 2.4](../../../air-gapped-env-setup.md#24-pre-download-models-internet-connected-machine))

**On a machine with internet access:**

```bash
# Download Qwen 2.5 7B Instruct to cache directory
# Note: ./models/cache is excluded from git via .gitignore
hf download Qwen/Qwen2.5-7B-Instruct \
  --local-dir ./models/cache/Qwen/Qwen2.5-7B-Instruct

# Verify download (should show ~15 files)
ls -lh ./models/cache/Qwen/Qwen2.5-7B-Instruct/
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
oc exec -n llm-models model-loader -- mkdir -p /mnt/models/Qwen/Qwen2.5-7B-Instruct

# Copy model to PVC (with progress)
oc rsync --progress ./models/cache/Qwen/Qwen2.5-7B-Instruct/ llm-models/model-loader:/mnt/models/Qwen/Qwen2.5-7B-Instruct/

# Verify model files are present
oc exec -n llm-models model-loader -- ls -lh /mnt/models/Qwen/Qwen2.5-7B-Instruct/
```

**Expected Output (ls -lh):**
```
total XXXM
-rw-r--r-- 1 ... config.json
-rw-r--r-- 1 ... generation_config.json
-rw-r--r-- 1 ... model-00001-of-00004.safetensors
-rw-r--r-- 1 ... model-00002-of-00004.safetensors
-rw-r--r-- 1 ... model-00003-of-00004.safetensors
-rw-r--r-- 1 ... model-00004-of-00004.safetensors
-rw-r--r-- 1 ... tokenizer.json
...
```

---

### Step 3: Deploy Model with OpenShift AI

This deployment uses **OpenShift AI RawDeployment mode** with KServe API (ServingRuntime + InferenceService).

#### 3.1. Create ServingRuntime

The ServingRuntime defines **HOW** to serve models (vLLM configuration, GPU allocation, resource limits).

```bash
oc apply -f models/qwen-2.5-7b-instruct/servingruntime.yaml
```

**Verify ServingRuntime created:**
```bash
oc get servingruntime -n llm-models
```

**Expected output:**
```
NAME                 DISABLED   MODELTYPE   CONTAINERS   AGE
vllm-qwen-runtime    false      vLLM        kserve       10s
```

---

#### 3.2. Create InferenceService

The InferenceService defines **WHAT** model to serve (references the ServingRuntime and PVC).

```bash
oc apply -f models/qwen-2.5-7b-instruct/inferenceservice.yaml
```

**Verify InferenceService created:**
```bash
oc get inferenceservice -n llm-models
```

**Expectedoutput:**
```
NAME            URL                                          READY   PREV   LATEST
qwen-2-5-7b     http://qwen-2-5-7b.llm-models.svc.cluster    True           100
```

---

#### 3.3. Create Route for External Access

```bash
oc apply -f route-inferenceservice.yaml
```

**Get route URL:**
```bash
oc get route qwen-2-5-7b-inference -n llm-models
```

**Expected output:**
```
NAME                     HOST/PORT                                               
qwen-2-5-7b-inference    qwen-2-5-7b-inference-llm-models.apps.example.com
```

---

### Step 4: Monitor Deployment

```bash
# Watch pod status (model loading takes 2-5 minutes)
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -w

# Check pod events
oc describe pod -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b

# Follow logs (watch for "Application startup complete")
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1)
oc logs -f $POD -n llm-models
```

**Key Log Messages to Look For:**
```
INFO: Starting to load model /mnt/models/Qwen/Qwen2.5-7B-Instruct...
INFO: Loading weights took X seconds
INFO: Model loading took 14.25 GiB memory
INFO: Compiling a graph for compile range
INFO: Application startup complete
```

**Pod Status Progression:**
```
NAME                                    READY   STATUS              RESTARTS   AGE
qwen-2-5-7b-xxxxx-xxxxx                 0/1     ContainerCreating   0          10s
qwen-2-5-7b-xxxxx-xxxxx                 0/1     Running             0          30s
qwen-2-5-7b-xxxxx-xxxxx                 1/1     Running             0          3m
```

---

### Step 5: Test Model API

```bash
# Get route URL
ROUTE_URL=$(oc get route qwen-2-5-7b-inference -n llm-models -o jsonpath='{.spec.host}')
echo "Model endpoint: https://$ROUTE_URL"

# Test health endpoint
curl -k https://$ROUTE_URL/health

# List available models
curl -k https://$ROUTE_URL/v1/models

# Test simple completion
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {"role": "user", "content": "Explain Kubernetes in one sentence."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'

# Test code generation (Qwen is excellent at code!)
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {"role": "system", "content": "You are a helpful coding assistant."},
      {"role": "user", "content": "Write a Python function to calculate fibonacci numbers using memoization."}
    ],
    "max_tokens": 512,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

# Test multilingual capability (Qwen supports Chinese, English, and more)
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {"role": "user", "content": "用中文解释什么是机器学习"}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }'

# Test streaming response
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/mnt/models/Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {"role": "user", "content": "Count from 1 to 10."}
    ],
    "max_tokens": 50,
    "stream": true
  }'
```

**Expected Response (example):**
```json
{
  "id": "chatcmpl-xxxxxxxxxxxxxxxx",
  "object": "chat.completion",
  "created": 1776789362,
  "model": "/mnt/models/Qwen/Qwen2.5-7B-Instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Kubernetes is an open-source container orchestration platform...",
        "refusal": null
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 34,
    "completion_tokens": 42,
    "total_tokens": 76
  }
}
```

---

### Step 6: Performance Validation

```bash
# Check GPU utilization
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1)
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
|   0  NVIDIA H200             On   | xxxxxxxxxx      |      0%      45C   |
| N/A   58W / 700W |  14336MiB / 143871MiB |      10%      Default |
+-------------------------------+----------------------+----------------------+
```

---

### Step 6: Configure OpenCode (Optional)

If you want to use this model with OpenCode for AI-assisted development:

#### 6.1. Update Base URL

First, get your deployed model's route URL:

```bash
ROUTE_URL=$(oc get route qwen-2-5-7b-inference -n llm-models -o jsonpath='{.spec.host}')
echo "https://$ROUTE_URL/v1"
```

Edit `opencode.json` and update the `baseURL` with your route:

```json
{
  "provider": {
    "openshift-ai-qwen": {
      "options": {
        "baseURL": "https://YOUR-ROUTE-URL/v1"
      }
    }
  }
}
```

#### 6.2. Copy Configuration

```bash
# Copy to your project directory
cp models/qwen-2.5-7b-instruct/opencode.json /path/to/your/project/

# Or configure globally
mkdir -p ~/.config/opencode
cp models/qwen-2.5-7b-instruct/opencode.json ~/.config/opencode/
```

#### 6.3. Start OpenCode

```bash
cd /path/to/your/project
opencode
```

OpenCode will now use your air-gapped Qwen 2.5 7B model.

---

### OpenCode Configuration Reference

The `opencode.json` file configures Open Code to use your deployed model:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openshift-ai-qwen": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "OpenShift AI - Qwen 2.5 7B",
      "options": {
        "baseURL": "https://qwen-2-5-7b-inference-llm-models.apps.example.com/v1"
      },
      "models": {
        "/mnt/models/Qwen/Qwen2.5-7B-Instruct": {
          "name": "Qwen 2.5 7B Instruct (Air-Gapped)",
          "description": "Qwen 2.5 7B instruction-tuned model deployed on OpenShift AI with vLLM and NVIDIA H200 GPU",
          "limit": {
            "context": 32768,
            "output": 1024
          }
        }
      }
    }
  },
  "model": "openshift-ai-qwen//mnt/models/Qwen/Qwen2.5-7B-Instruct"
}
```

#### Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `$schema` | `https://opencode.ai/config.json` | JSON schema for validation |
| `provider.*.npm` | `@ai-sdk/openai-compatible` | AI SDK provider for OpenAI-compatible APIs |
| `provider.*.name` | `OpenShift AI - Qwen 2.5 7B` | Display name in Open Code |
| `provider.*.options.baseURL` | `https://<route>/v1` | Your model's OpenAI-compatible API endpoint |
| `models.*.limit.context` | `32768` | Total context window in tokens |
| `models.*.limit.output` | `1024` | Maximum output tokens per response |
| `model` | `openshift-ai-qwen//mnt/...` | Active model identifier |

#### Understanding Token Limits

**The `limit` configuration is critical** for Open Code to work correctly:

```json
"limit": {
  "context": 32768,    // Total tokens (input + output)
  "output": 1024       // Maximum response length
}
```

**Why is `output` set to 1024?**

Open Code automatically loads context (skills, documentation, conversation history) that can consume **significant tokens**. With a 32k context window:

- **Typical Open Code context**: 20k-28k tokens (skills, system prompts, conversation)
- **Available for output**: 4k-12k tokens
- **Safe default**: 1024 tokens ensures room for input without overflow

**If you see errors like:**
```
This model's maximum context length is 32768 tokens. However, you requested 
X output tokens and your prompt contains at least Y input tokens...
```

**Solution**: Reduce `output` further (512 or 256) or work without loading many skills.

#### Adjusting Token Limits

**For basic prompts without skills:**
```json
"limit": {
  "context": 32768,
  "output": 4096      // More room for longer responses
}
```

**For skill-heavy workflows:**
```json
"limit": {
  "context": 32768,
  "output": 512       // Minimal to leave room for skill content
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
| **Runtime Name** | `vllm-qwen-runtime` | ServingRuntime identifier |
| **Container Image** | `vllm/vllm-openai:latest` | Official vLLM OpenAI-compatible image |
| **Model Path** | `/mnt/models/Qwen/Qwen2.5-7B-Instruct` | Location in PVC |
| **GPUs** | 1 | Number of GPUs allocated |
| **Max Model Length** | 32768 | Context window size in tokens |
| **GPU Memory Util** | 0.90 | Percentage of VRAM to use (90%) |
| **Port** | 8080 | vLLM API port (KServe standard) |

### Resource Allocation

```yaml
resources:
  requests:
    cpu: "8"
    memory: 24Gi
    nvidia.com/gpu: "1"
  limits:
    cpu: "16"
    memory: 48Gi
    nvidia.com/gpu: "1"
```

### InferenceService Configuration

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: qwen-2-5-7b
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: vllm-qwen-runtime
      storageUri: pvc://models-storage/
    minReplicas: 1
    maxReplicas: 1
```

**Key Points:**
- `deploymentMode: RawDeployment` - Creates standard Kubernetes Deployment (not Knative)
- `runtime: vllm-qwen-runtime` - References the ServingRuntime
- `storageUri: pvc://models-storage/` - KServe syntax for PVC storage

---

## Performance Expectations

Based on NVIDIA H200 GPU:

- **First Token Latency (TTFT)**: 40-80ms
- **Generation Speed**: 90-130 tokens/second
- **VRAM Usage**: ~14GB (out of 143GB available)
- **System RAM Usage**: ~6GB
- **Concurrent Requests**: 6-10 users (depending on context length)
- **Context Window**: 32,768 tokens (default), supports up to 128K

---

## Scaling

### Horizontal Scaling (Multiple Replicas)

```bash
# Edit InferenceService
oc edit inferenceservice qwen-2-5-7b -n llm-models

# Change:
# spec:
#   predictor:
#     minReplicas: 2
#     maxReplicas: 2

# Verify both pods are running
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b

# Service automatically load balances across replicas
```

**Note**: Each replica requires 1 GPU. The maximum number of replicas is limited by available GPUs in your cluster.

### Vertical Scaling (Extended Context)

```bash
# Edit ServingRuntime to increase context window
oc edit servingruntime vllm-qwen-runtime -n llm-models

# Change:
# args:
#   - --max-model-len
#   - "32768"
# to:
#   - --max-model-len
#   - "65536"

# Delete pod to restart with new config
oc delete pod -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b
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

---

## Cleanup

### Delete Model Deployment Only

```bash
# Delete InferenceService (automatically deletes pods and services)
oc delete inferenceservice qwen-2-5-7b -n llm-models

# Delete Route
oc delete route qwen-2-5-7b-inference -n llm-models

# Delete ServingRuntime (if not used by other models)
oc delete servingruntime vllm-qwen-runtime -n llm-models

# Verify deletion
oc get inferenceservice,servingruntime,route -n llm-models
```

### Delete Everything (Namespace and PVC)

```bash
# Delete entire namespace (removes all models and storage)
oc delete namespace llm-models

# Warning: This deletes ALL model files in the PVC
```

### Delete Model Files from PVC (Keep PVC)

```bash
# Create temporary pod
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: model-loader
  namespace: llm-models
spec:
  containers:
  - name: loader
    image: registry.access.redhat.com/ubi9/ubi-minimal:latest
    command: ["/bin/sh", "-c", "sleep 600"]
    volumeMounts:
    - name: models
      mountPath: /mnt/models
  volumes:
  - name: models
    persistentVolumeClaim:
      claimName: model-storage
EOF

# Wait for pod
oc wait --for=condition=Ready pod/model-loader -n llm-models --timeout=60s

# Delete model directory
oc exec -n llm-models model-loader -- rm -rf /mnt/models/Qwen/Qwen2.5-7B-Instruct/

# Delete pod
oc delete pod model-loader -n llm-models
```

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
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 100,
  "temperature": 0.7,
  "stream": false
}
```

#### Text Completions

```bash
POST /v1/completions
Content-Type: application/json

{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "prompt": "Once upon a time",
  "max_tokens": 100,
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

Qwen 2.5 7B Instruct excels at:

- **Code Generation**: Python, JavaScript, Go, Rust, and more
- **Math & Reasoning**: Strong mathematical and logical reasoning
- **Multilingual**: Chinese, English, and 27+ languages
- **Long Context**: Supports up to 128K tokens
- **Instruction Following**: Excellent at following complex instructions

---

## References

- **HuggingFace Model Card**: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- **Qwen Blog**: https://qwenlm.github.io/blog/qwen2.5/
- **vLLM Documentation**: https://docs.vllm.ai/
- **License**: Apache 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
- **Main Documentation**: [air-gapped-env-setup.md](../../../air-gapped-env-setup.md)

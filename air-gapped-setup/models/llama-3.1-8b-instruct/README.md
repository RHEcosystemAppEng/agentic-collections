# Llama 3.1 8B Instruct - Complete Deployment Guide

## Model Information

- **Model**: Meta Llama 3.1 8B Instruct
- **Parameters**: 8 billion
- **HuggingFace ID**: `meta-llama/Llama-3.1-8B-Instruct`
- **Context Window**: 8,192 tokens (configurable up to 128K with increased VRAM)
- **License**: Llama 3.1 Community License
- **GPU Requirements**: 1x NVIDIA H200 (or similar with 16GB+ VRAM)
- **VRAM Usage**: ~16GB
- **Use Case**: General purpose, code generation, fast inference

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

### Step 1: Request Access to Llama 3.1 Model

**IMPORTANT:** Llama 3.1 is a **gated model** 🔒 - you must request access from Meta before downloading.

**On HuggingFace web interface:**

1. Visit the model page: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
2. Click the **"Request Access"** button (visible when logged in)
3. Fill out the access request form
4. Wait for approval email from Meta (usually within minutes to hours)

**Note**: You must use the same HuggingFace account that requested access when downloading the model.

---

### Step 2: Download Model (Internet-Connected Machine)

**Prerequisites:** HuggingFace CLI installed and authenticated (see [main documentation Section 2.4](../../../air-gapped-env-setup.md#24-pre-download-models-internet-connected-machine))

**On a machine with internet access:**

```bash
# Download Llama 3.1 8B Instruct to cache directory
# Note: ./models/cache is excluded from git via .gitignore
hf download meta-llama/Llama-3.1-8B-Instruct \
  --local-dir ./models/cache/meta-llama/Llama-3.1-8B-Instruct

# Verify download (should show ~30 files)
ls -lh ./models/cache/meta-llama/Llama-3.1-8B-Instruct/

# Create tarball for transfer (maintains vendor/model structure)
tar -czf llama-3.1-8b.tar.gz -C ./models/cache .

# Check tarball size (~16GB)
ls -lh llama-3.1-8b.tar.gz
```

**Expected files after download:**
```
config.json
generation_config.json
model-00001-of-00004.safetensors (~4.0GB)
model-00002-of-00004.safetensors (~4.0GB)
model-00003-of-00004.safetensors (~4.0GB)
model-00004-of-00004.safetensors (~3.9GB)
model.safetensors.index.json
special_tokens_map.json
tokenizer.json
tokenizer_config.json
... (30 files total, ~16GB)
```

---

### Step 3: Transfer Model to Air-Gapped Cluster

**Transfer tarball to bastion/jump host:**

```bash
# Transfer tarball to bastion host with oc access
# (Use scp, rsync, or physical media)
scp llama-3.1-8b.tar.gz user@bastion:/tmp/
```

**On bastion host with oc access:**

```bash
# Create temporary pod with PVC mounted
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
    command: ["/bin/sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: models
      mountPath: /mnt/models
  volumes:
  - name: models
    persistentVolumeClaim:
      claimName: model-storage
  restartPolicy: Never
EOF

# Wait for pod to be ready
oc wait --for=condition=Ready pod/model-loader -n llm-models --timeout=120s

# Copy model tarball to PVC
oc cp /tmp/llama-3.1-8b.tar.gz llm-models/model-loader:/mnt/models/

# Extract tarball in PVC
oc exec -n llm-models model-loader -- tar -xzf /mnt/models/llama-3.1-8b.tar.gz -C /mnt/models/

# Remove tarball to save space
oc exec -n llm-models model-loader -- rm /mnt/models/llama-3.1-8b.tar.gz

# Verify model files are present
oc exec -n llm-models model-loader -- ls -lh /mnt/models/meta-llama/Llama-3.1-8B-Instruct/

# Delete loader pod
oc delete pod model-loader -n llm-models
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

### Step 4: Deploy Model

```bash
# Navigate to model manifest directory
cd models/llama-3.1-8b-instruct/

# Deploy all resources (deployment, service, route)
oc apply -f .

# Verify resources created
oc get deployment,service,route -n llm-models
```

**Expected Output:**
```
NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/vllm-llama-3-1-8b  0/1     1            0           5s

NAME                            TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
service/llm-llama-3-1-8b-svc    ClusterIP   172.30.xxx.xxx   <none>        8000/TCP   5s

NAME                                    HOST/PORT                                                      PATH   SERVICES               PORT   TERMINATION   WILDCARD
route.route.openshift.io/llama-3-1-8b   llama-3-1-8b-llm-models.apps.example.com                             llm-llama-3-1-8b-svc   http   edge          None
```

---

### Step 5: Monitor Deployment

```bash
# Watch pod status (model loading takes 2-5 minutes)
oc get pods -n llm-models -l model=llama-3.1-8b-instruct -w

# Check pod events
oc describe pod -n llm-models -l model=llama-3.1-8b-instruct

# Follow logs (watch for "Application startup complete")
POD=$(oc get pods -n llm-models -l model=llama-3.1-8b-instruct -o name | head -1)
oc logs -f $POD -n llm-models
```

**Key Log Messages to Look For:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Loading model weights...
INFO:     Model loaded successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Pod Status Progression:**
```
NAME                               READY   STATUS              RESTARTS   AGE
vllm-llama-3-1-8b-xxxxxxxxx-xxxxx  0/1     ContainerCreating   0          10s
vllm-llama-3-1-8b-xxxxxxxxx-xxxxx  0/1     Running             0          30s
vllm-llama-3-1-8b-xxxxxxxxx-xxxxx  1/1     Running             0          3m
```

---

### Step 6: Test Model API

```bash
# Get route URL
ROUTE_URL=$(oc get route llama-3-1-8b -n llm-models -o jsonpath='{.spec.host}')
echo "Model endpoint: https://$ROUTE_URL"

# Test health endpoint
curl -k https://$ROUTE_URL/health
# Expected: {"status":"ok"}

# List available models
curl -k https://$ROUTE_URL/v1/models

# Test simple completion
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [
      {"role": "user", "content": "Explain Kubernetes in one sentence."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }'

# Test code generation
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [
      {"role": "system", "content": "You are a helpful coding assistant."},
      {"role": "user", "content": "Write a Python function to calculate fibonacci numbers using memoization."}
    ],
    "max_tokens": 512,
    "temperature": 0.7
  }' | jq -r '.choices[0].message.content'

# Test streaming response
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
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
  "id": "cmpl-xxxxxxxxxxxxxxxxxxxxxxxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Kubernetes is an open-source container orchestration platform..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 42,
    "total_tokens": 57
  }
}
```

---

### Step 7: Performance Validation

```bash
# Check GPU utilization
POD=$(oc get pods -n llm-models -l model=llama-3.1-8b-instruct -o name | head -1)
oc exec $POD -- nvidia-smi

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
| N/A   60W / 700W |  16384MiB / 143871MiB |      10%      Default |
+-------------------------------+----------------------+----------------------+
```

---

## Configuration Reference

### Deployment Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Model Path** | `/mnt/models/meta-llama/Llama-3.1-8B-Instruct` | Location in PVC |
| **Served Model Name** | `meta-llama/Llama-3.1-8B-Instruct` | API model identifier |
| **GPUs** | 1 | Number of GPUs allocated |
| **Tensor Parallel** | 1 | GPU parallelization (1 for single GPU) |
| **Max Model Length** | 8192 | Context window size in tokens |
| **GPU Memory Util** | 0.90 | Percentage of VRAM to use (90%) |
| **Port** | 8000 | vLLM API port |

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

### vLLM Arguments

```yaml
args:
  - /mnt/models/meta-llama/Llama-3.1-8B-Instruct
  - --port=8000
  - --served-model-name=meta-llama/Llama-3.1-8B-Instruct
  - --trust-remote-code
  - --tensor-parallel-size=1
  - --gpu-memory-utilization=0.90
  - --max-model-len=8192
  - --dtype=auto
  - --disable-log-requests
```

---

## Performance Expectations

Based on NVIDIA H200 GPU:

- **First Token Latency (TTFT)**: 30-60ms
- **Generation Speed**: 100-150 tokens/second
- **VRAM Usage**: ~16GB (out of 143GB available)
- **System RAM Usage**: ~6GB
- **Concurrent Requests**: 8-12 users (depending on context length)
- **Context Window**: 8,192 tokens (default), supports up to 128K with increased VRAM

---

## Scaling

### Horizontal Scaling (Multiple Replicas)

```bash
# Increase replicas (requires additional GPUs)
oc scale deployment vllm-llama-3-1-8b -n llm-models --replicas=2

# Verify both pods are running
oc get pods -n llm-models -l model=llama-3.1-8b-instruct

# Service automatically load balances across replicas
```

**Note**: Each replica requires 1 GPU. The maximum number of replicas is limited by available GPUs in your cluster.

### Vertical Scaling (Extended Context)

```bash
# Edit deployment to increase context window
oc edit deployment vllm-llama-3-1-8b -n llm-models

# Change:
# - --max-model-len=8192
# to:
# - --max-model-len=16384

# Pod will restart with new configuration
```

**Note**: Longer context windows require more VRAM and reduce concurrent request capacity.

---

## Troubleshooting

### Pod Stuck in Pending

```bash
# Check events
oc describe pod -n llm-models -l model=llama-3.1-8b-instruct

# Common causes:
# - No available GPU: Check GPU allocation
#   oc describe nodes | grep nvidia.com/gpu
# - PVC not bound: Check PVC status
#   oc get pvc -n llm-models
```

### Pod CrashLoopBackOff

```bash
# Check logs
oc logs -n llm-models -l model=llama-3.1-8b-instruct --tail=100

# Common issues:
# - Model files not found: Verify PVC path
#   oc exec model-loader -n llm-models -- ls -lh /mnt/models/meta-llama/Llama-3.1-8B-Instruct/
# - OOM (Out of Memory): Reduce --max-model-len or --gpu-memory-utilization
# - GPU not available: Check GPU Operator is running
#   oc get pods -n nvidia-gpu-operator
```

### Slow Inference / High Latency

```bash
# Check GPU utilization
POD=$(oc get pods -n llm-models -l model=llama-3.1-8b-instruct -o name | head -1)
oc exec $POD -- nvidia-smi

# Check if model is loaded in GPU memory (VRAM usage should be ~16GB)
# Check concurrent request load
oc logs $POD | grep "num_requests"

# Reduce concurrent load or increase replicas
```

### Model Not Responding

```bash
# Check pod status
oc get pods -n llm-models -l model=llama-3.1-8b-instruct

# Check readiness probe
oc describe pod -n llm-models -l model=llama-3.1-8b-instruct | grep -A 5 Readiness

# Check route
oc get route llama-3-1-8b -n llm-models

# Test from within cluster (bypass route)
oc run -it --rm debug --image=registry.access.redhat.com/ubi9/ubi-minimal --restart=Never -- \
  curl http://llm-llama-3-1-8b-svc.llm-models.svc.cluster.local:8000/health
```

---

## Cleanup

### Delete Model Deployment Only

```bash
# Navigate to manifest directory
cd models/llama-3.1-8b-instruct/

# Delete resources
oc delete -f .

# Verify deletion
oc get pods,service,route -n llm-models
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
oc exec -n llm-models model-loader -- rm -rf /mnt/models/meta-llama/Llama-3.1-8B-Instruct/

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
  "model": "meta-llama/Llama-3.1-8B-Instruct",
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
  "model": "meta-llama/Llama-3.1-8B-Instruct",
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

Llama 3.1 8B Instruct excels at:

- **General Purpose**: Broad knowledge across domains
- **Code Generation**: Strong programming capabilities
- **Fast Inference**: Optimized for low latency
- **Instruction Following**: Excellent at following complex instructions
- **Reasoning**: Strong logical and analytical capabilities

---

## References

- **HuggingFace Model Card**: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
- **Meta Llama Blog**: https://ai.meta.com/blog/meta-llama-3-1/
- **vLLM Documentation**: https://docs.vllm.ai/
- **License**: Llama 3.1 Community License (https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/LICENSE)
- **Main Documentation**: [air-gapped-env-setup.md](../../../air-gapped-env-setup.md)

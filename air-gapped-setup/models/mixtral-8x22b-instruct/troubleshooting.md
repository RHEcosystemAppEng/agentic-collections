# Mixtral 8x22B Instruct - Troubleshooting & Advanced Topics

This document contains advanced configuration, monitoring, security hardening, and troubleshooting procedures for the Mixtral 8x22B deployment.

---

## Table of Contents

- [Security Hardening](#security-hardening)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting](#troubleshooting)
- [MoE-Specific Considerations](#moe-specific-considerations)

---

## Security Hardening

### Network Policies

Restrict network access to the model inference service:

```bash
cat <<EOF | oc apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mixtral-inference-netpol
  namespace: llm-models
spec:
  podSelector:
    matchLabels:
      serving.kserve.io/inferenceservice: mixtral-8x22b
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: openshift-ingress
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: openshift-apiserver
      ports:
        - protocol: TCP
          port: 443
    - to:
        - podSelector: {}
      ports:
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
EOF
```

**What this does:**
- Allows ingress only from OpenShift router
- Allows egress to OpenShift API server and DNS
- Blocks all other traffic

### API Authentication (Optional)

For production, consider adding authentication using OpenShift OAuth:

```bash
# Create ServiceAccount for API clients
oc create sa model-client -n llm-models

# Grant view permissions
oc adm policy add-role-to-user view system:serviceaccount:llm-models:model-client

# Get token for authentication
SA_TOKEN=$(oc sa get-token model-client -n llm-models)

# Use token in requests
curl -k -H "Authorization: Bearer $SA_TOKEN" \
  https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "/mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1", "messages": [{"role": "user", "content": "Test"}]}'
```

---

## Monitoring and Observability

### Real-time GPU Monitoring (2 GPUs)

```bash
# Get GPU utilization in real-time (all 2 GPUs)
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
watch -n 2 "oc exec $POD -c kserve-container -- nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv"

# Expected output: 2 GPUs, each using ~70GB VRAM
```

### vLLM Metrics

Check vLLM performance metrics:

```bash
# Get metrics endpoint
curl -k https://$ROUTE_URL/metrics

# Key metrics to monitor:
# - vllm:num_requests_running - Active inference requests
# - vllm:num_requests_waiting - Queued requests  
# - vllm:gpu_cache_usage_perc - KV cache utilization
# - vllm:time_to_first_token_seconds - Latency to first token (expect 40-80ms)
# - vllm:time_per_output_token_seconds - Generation speed (expect 80-120 tokens/s)
# - vllm:moe_expert_utilization - MoE expert activation patterns (Mixtral-specific)
```

### Pod Resource Usage

```bash
# Real-time resource consumption
oc adm top pod -n llm-models

# Detailed pod metrics
oc describe pod -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b | grep -A 20 "Requests:\|Limits:"

# Expected: 2 GPUs, ~80GB RAM usage
```

### Log Monitoring

```bash
# Follow vLLM logs
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
oc logs -f $POD -n llm-models

# Filter for errors
oc logs $POD -n llm-models | grep -i "error\|warn\|fail"

# Check tensor-parallel initialization
oc logs $POD -n llm-models | grep -i "tensor.*parallel"

# Check MoE expert loading
oc logs $POD -n llm-models | grep -i "expert\|moe"

# Check recent requests
oc logs $POD -n llm-models --tail=100 | grep "POST /v1/"
```

---

## Troubleshooting

### Pod Stuck in Pending

```bash
# Check events
oc describe pod -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b

# Common causes:
# - Not enough GPUs: Need 2 available GPUs
#   oc describe nodes | grep nvidia.com/gpu
#   Allocatable should show at least 2 GPUs available
# - PVC not bound: Check PVC status
#   oc get pvc -n llm-models
# - Insufficient RAM: Need 80-160GB available
#   oc describe nodes | grep -A 5 "Allocatable"
```

### Pod CrashLoopBackOff

```bash
# Check logs
oc logs -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b --tail=200

# Common issues:
# - Model files not found: Verify PVC path
#   oc exec model-loader -n llm-models -- ls -lh /mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1/
# - OOM (Out of Memory): Reduce --max-model-len or --gpu-memory-utilization
# - Tensor parallelism failure: Check all 2 GPUs are available and healthy
#   oc exec $POD -c kserve-container -- nvidia-smi
# - GPU not available: Check GPU Operator is running
#   oc get pods -n nvidia-gpu-operator
# - MoE loading failure: Check logs for expert loading errors
#   oc logs $POD | grep -i "expert.*error\|moe.*fail"
```

### Slow Inference / High Latency

```bash
# Check GPU utilization (should show all 2 GPUs active)
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
oc exec $POD -c kserve-container -- nvidia-smi

# Check if model is loaded in GPU memory (VRAM usage should be ~140GB total, ~70GB per GPU)
# Check concurrent request load
oc logs $POD | grep "num_requests"

# For Mixtral 8x22B MoE, expect:
# - First token: 40-80ms (faster than dense models)
# - Generation: 80-120 tokens/s
# - MoE should be faster than dense 70B+ models

# Check expert routing efficiency
oc logs $POD | grep "expert.*routing\|moe.*efficiency"

# Reduce concurrent load or increase replicas (requires 2 GPUs per replica)
```

### Model Not Responding

```bash
# Check InferenceService status
oc get inferenceservice mixtral-8x22b -n llm-models

# Check pod status
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b

# Check readiness probe
oc describe pod -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b | grep -A 5 Readiness

# Check route
oc get route mixtral-8x22b-inference -n llm-models

# Test from within cluster (bypass route)
SVC=$(oc get service -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1 | cut -d/ -f2)
oc run -it --rm debug --image=registry.access.redhat.com/ubi9/ubi-minimal --restart=Never -- \
  curl http://$SVC.llm-models.svc.cluster.local:8080/health
```

### CUDA Errors / GPU Issues

```bash
# Verify all 2 GPUs are allocated to pod
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
oc describe $POD | grep -A 5 "nvidia.com/gpu"

# Should show: nvidia.com/gpu: 2

# Check nvidia-smi works inside container (should show 2 GPUs)
oc exec $POD -c kserve-container -- nvidia-smi

# Common errors:
# - "CUDA error: out of memory" → Reduce --max-model-len or --gpu-memory-utilization
#   Mixtral 8x22B with 64K context requires ~140GB VRAM minimum
# - "CUDA error: device not found" → Check GPU Operator is running:
oc get pods -n nvidia-gpu-operator

# Verify GPU node labels
oc get nodes -l nvidia.com/gpu.present=true -o wide

# Check NCCL (multi-GPU communication) errors
oc logs $POD | grep -i "nccl\|tensor.*parallel"
```

### Tensor Parallelism Issues

```bash
# Specific to multi-GPU deployments like Mixtral 8x22B
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)

# Verify tensor-parallel-size matches GPU count
oc get servingruntime vllm-mixtral-runtime -n llm-models -o yaml | grep -A 2 "tensor-parallel-size"
# Should show: - "2"

# Check all GPUs are visible to the process
oc exec $POD -c kserve-container -- nvidia-smi -L
# Should show: GPU 0, GPU 1

# Check for NCCL/inter-GPU communication errors
oc logs $POD | grep -i "nccl\|peer.*access\|nvlink"

# Verify GPUs are on same node (required for tensor parallelism)
oc describe $POD | grep "Node:"
```

### vLLM Startup Failures

```bash
# Check detailed logs (MoE models take 3-8 minutes to load)
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
oc logs $POD --tail=200

# Common causes:
# 1. Model files not found
oc exec model-loader -n llm-models -- ls -lh /mnt/models/Mixtral/Mixtral-8x22B-Instruct-v0.1/

# 2. Insufficient resources (need 2 GPUs, 160GB RAM)
oc describe $POD | grep -A 10 "Events:"

# 3. Invalid vLLM arguments
oc get servingruntime vllm-mixtral-runtime -n llm-models -o yaml | grep -A 30 "args:"

# 4. Tensor parallelism misconfiguration
oc logs $POD | grep "tensor.*parallel"
# Should see: "Initializing distributed environment with 2 workers"

# 5. MoE-specific loading errors
oc logs $POD | grep "expert.*loading\|moe.*init"
# Should see: "Loading 8 experts" or similar
```

### Performance Issues

```bash
# Check if model is loaded across all 2 GPUs
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
oc exec $POD -c kserve-container -- nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv

# Expected: Each GPU showing ~70GB used (total ~140GB)
# GPU 0: ~70GB / 143GB
# GPU 1: ~70GB / 143GB

# Check concurrent request load
oc logs $POD | grep "num_requests" | tail -20

# If GPU memory is significantly lower than expected:
# - Model may not be fully loaded
# - Check for OOM errors in logs
# - Verify tensor-parallel-size=2
# - Check all 2 GPUs are visible: oc exec $POD -- nvidia-smi -L

# Performance expectations for Mixtral 8x22B MoE:
# - First token latency: 40-80ms (faster than dense models)
# - Generation speed: 80-120 tokens/s
# - MoE advantage: Only ~39B params active vs 141B total

# Check expert activation patterns
oc logs $POD | grep "expert.*activation\|moe.*routing" | tail -20
```

### Route/Network Issues

```bash
# Verify route exists and has correct URL
oc get route mixtral-8x22b-inference -n llm-models -o yaml

# Test route connectivity
ROUTE_URL=$(oc get route mixtral-8x22b-inference -n llm-models -o jsonpath='{.spec.host}')
curl -vk https://$ROUTE_URL/health

# Check if route backend is healthy
oc describe route mixtral-8x22b-inference -n llm-models | grep -A 5 "Status:"

# If timeout errors, check service endpoints
oc get endpoints -n llm-models

# MoE model loading takes 3-8 minutes, be patient on first startup
```

### Multi-GPU Specific Issues

```bash
# Mixtral 8x22B uses tensor parallelism - troubleshoot multi-GPU coordination

# 1. Verify all GPUs are on same physical node
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)
oc get $POD -o jsonpath='{.spec.nodeName}'

# Tensor parallelism requires GPUs on same node with NVLink

# 2. Check GPU topology (NVLink connections)
oc exec $POD -c kserve-container -- nvidia-smi topo -m

# 3. Verify NCCL (NVIDIA Collective Communications Library)
oc logs $POD | grep -i "nccl"

# 4. Check for GPU peer access errors
oc logs $POD | grep -i "peer.*access\|p2p"

# 5. If unbalanced GPU memory usage:
oc exec $POD -c kserve-container -- nvidia-smi --query-gpu=memory.used --format=csv
# Both should be similar (~70GB each)
```

---

## MoE-Specific Considerations

### Understanding Mixture of Experts Architecture

Mixtral 8x22B uses a Sparse Mixture of Experts (SMoE) architecture:

- **8 Expert Networks**: The model has 8 separate expert sub-networks
- **2 Active per Token**: For each token, only 2 of the 8 experts are activated
- **Router Network**: Decides which experts to activate for each token
- **Efficiency**: Only ~39B parameters active (vs 141B total), providing speed with quality

### Monitoring Expert Utilization

```bash
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=mixtral-8x22b -o name | head -1)

# Check expert activation patterns in logs
oc logs $POD | grep -i "expert"

# Look for balanced expert usage (all 8 experts should be used relatively equally)
# Unbalanced usage may indicate routing issues
```

### MoE Performance Characteristics

**Expected Behavior:**
- **Faster TTFT**: 40-80ms (vs 100-200ms for dense 70B models)
- **Higher Throughput**: 80-120 tokens/s (vs 30-50 for dense models)
- **Lower Memory Bandwidth**: Only 39B params need to be accessed per forward pass
- **Better Batching**: Can handle more concurrent requests due to sparse activation

**Troubleshooting MoE Issues:**

```bash
# If performance is slower than expected:

# 1. Check if expert routing is efficient
oc logs $POD | grep "routing\|expert.*selection"

# 2. Verify all experts loaded correctly
oc logs $POD | grep "expert.*load\|moe.*init"
# Should see all 8 experts initialized

# 3. Check for expert load imbalance
oc logs $POD | grep "expert.*utilization"
# Ideally all experts used ~equally

# 4. Monitor expert switching overhead
# Too frequent expert switching can cause slowdowns
```

### Common MoE-Specific Errors

**Error: "Expert routing failed"**
```bash
# Check logs for routing errors
oc logs $POD | grep -i "routing.*error\|expert.*fail"

# Usually caused by:
# - Insufficient VRAM (increase GPU memory or reduce context)
# - Corrupted model files (re-download)
```

**Error: "Expert load imbalance"**
```bash
# Some experts heavily used, others underutilized
# Usually not critical but may impact performance

# Check router network health
oc logs $POD | grep "router"
```

---

**[← Back to Main README](./README.md)**

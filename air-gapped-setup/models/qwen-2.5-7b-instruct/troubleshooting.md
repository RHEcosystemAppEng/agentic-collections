# Qwen 2.5 7B Instruct - Troubleshooting & Advanced Topics

This document contains advanced configuration, monitoring, security hardening, and troubleshooting procedures for the Qwen 2.5 7B deployment.

---

## Table of Contents

- [Security Hardening](#security-hardening)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting](#troubleshooting)

---

## Security Hardening

### Network Policies

Restrict network access to the model inference service:

```bash
cat <<EOF | oc apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: qwen-inference-netpol
  namespace: llm-models
spec:
  podSelector:
    matchLabels:
      serving.kserve.io/inferenceservice: qwen-2-5-7b
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
  -d '{"model": "/mnt/models/Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": "Test"}]}'
```

---

## Monitoring and Observability

### Real-time GPU Monitoring

```bash
# Get GPU utilization in real-time
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1)
watch -n 2 "oc exec $POD -c kserve-container -- nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv"
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
# - vllm:time_to_first_token_seconds - Latency to first token
# - vllm:time_per_output_token_seconds - Generation speed
```

### Pod Resource Usage

```bash
# Real-time resource consumption
oc adm top pod -n llm-models

# Detailed pod metrics
oc describe pod -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b | grep -A 20 "Requests:\|Limits:"
```

### Log Monitoring

```bash
# Follow vLLM logs
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1)
oc logs -f $POD -n llm-models

# Filter for errors
oc logs $POD -n llm-models | grep -i "error\|warn\|fail"

# Check recent requests
oc logs $POD -n llm-models --tail=100 | grep "POST /v1/"
```

---

## Troubleshooting

### Pod Stuck in Pending

```bash
# Check events
oc describe pod -n llm-models -l model=qwen-2.5-7b-instruct

# Common causes:
# - No available GPU: Check GPU allocation
#   oc describe nodes | grep nvidia.com/gpu
# - PVC not bound: Check PVC status
#   oc get pvc -n llm-models
```

### Pod CrashLoopBackOff

```bash
# Check logs
oc logs -n llm-models -l model=qwen-2.5-7b-instruct --tail=100

# Common issues:
# - Model files not found: Verify PVC path
#   oc exec model-loader -n llm-models -- ls -lh /mnt/models/Qwen/Qwen2.5-7B-Instruct/
# - OOM (Out of Memory): Reduce --max-model-len or --gpu-memory-utilization
# - GPU not available: Check GPU Operator is running
#   oc get pods -n nvidia-gpu-operator
```

### Slow Inference / High Latency

```bash
# Check GPU utilization
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1)
oc exec $POD -c kserve-container -- nvidia-smi

# Check if model is loaded in GPU memory (VRAM usage should be ~14GB)
# Check concurrent request load
oc logs $POD | grep "num_requests"

# Reduce concurrent load or increase replicas
```

### Model Not Responding

```bash
# Check InferenceService status
oc get inferenceservice qwen-2-5-7b -n llm-models

# Check pod status
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b

# Check readiness probe
oc describe pod -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b | grep -A 5 Readiness

# Check route
oc get route qwen-2-5-7b-inference -n llm-models

# Test from within cluster (bypass route)
SVC=$(oc get service -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1 | cut -d/ -f2)
oc run -it --rm debug --image=registry.access.redhat.com/ubi9/ubi-minimal --restart=Never -- \
  curl http://$SVC.llm-models.svc.cluster.local:8080/health
```

### CUDA Errors / GPU Issues

```bash
# Verify GPU is allocated to pod
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1)
oc describe $POD | grep -A 5 "nvidia.com/gpu"

# Check nvidia-smi works inside container
oc exec $POD -c kserve-container -- nvidia-smi

# Common errors:
# - "CUDA error: out of memory" → Reduce --max-model-len or --gpu-memory-utilization
# - "CUDA error: device not found" → Check GPU Operator is running:
oc get pods -n nvidia-gpu-operator

# Verify GPU node labels
oc get nodes -l nvidia.com/gpu.present=true -o wide
```

### vLLM Startup Failures

```bash
# Check detailed logs
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1)
oc logs $POD --tail=200

# Common causes:
# 1. Model files not found
oc exec model-loader -n llm-models -- ls -lh /mnt/models/Qwen/Qwen2.5-7B-Instruct/

# 2. Insufficient resources
oc describe $POD | grep -A 10 "Events:"

# 3. Invalid vLLM arguments
oc get servingruntime vllm-qwen-runtime -n llm-models -o yaml | grep -A 20 "args:"
```

### Performance Issues

```bash
# Check if model is loaded in GPU memory
POD=$(oc get pods -n llm-models -l serving.kserve.io/inferenceservice=qwen-2-5-7b -o name | head -1)
oc exec $POD -c kserve-container -- nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Expected: ~14GB used for Qwen 2.5 7B

# Check concurrent request load
oc logs $POD | grep "num_requests" | tail -20

# If GPU memory is low:
# - Model may not be fully loaded
# - Check for OOM errors in logs
# - Consider reducing --max-model-len
```

### Route/Network Issues

```bash
# Verify route exists and has correct URL
oc get route qwen-2-5-7b-inference -n llm-models -o yaml

# Test route connectivity
ROUTE_URL=$(oc get route qwen-2-5-7b-inference -n llm-models -o jsonpath='{.spec.host}')
curl -vk https://$ROUTE_URL/health

# Check if route backend is healthy
oc describe route qwen-2-5-7b-inference -n llm-models | grep -A 5 "Status:"

# If timeout errors, check service endpoints
oc get endpoints -n llm-models
```

---

**[← Back to Main README](./README.md)**

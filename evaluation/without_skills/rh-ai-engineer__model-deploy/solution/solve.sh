#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Model Deployment Plan

## Diagnosed Issues

### GPU VRAM Budget Analysis
The vLLM OOM is a **GPU VRAM constraint**, not a pod system memory issue:
- Model weights: ~13.5 GiB loaded into GPU
- KV cache allocation: ~28.5 GiB (at default max_model_len=32768)
- Available VRAM after model load: ~10.1 GiB on A10G (24576 MiB total)
- **Root cause**: Default max_model_len=32768 causes KV cache to exhaust GPU VRAM
- **Fix**: Set MAX_MODEL_LEN=4096 or GPU_MEMORY_UTILIZATION=0.85

### LimitRange Conflict
- Namespace LimitRange min CPU: 100m
- KServe sidecar containers request: 10m CPU, 15Mi memory
- **CONFLICT**: Sidecar resources below LimitRange minimum
- Fix: Adjust LimitRange or use annotation to override

### GPU Node Taints
- GPU nodes may have taint ai-app=true:NoSchedule
- Add matching tolerations to InferenceService predictor spec

### NIMAccount Dependency
- NIM deployments require a NIMAccount CR to be ready before ServingRuntime can pull images
- Check for NIMAccountNotReady condition if ImagePullBackOff occurs

## Recommended InferenceService YAML

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-3-8b
  namespace: ml-production
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: vllm-cuda-runtime
      storageUri: "hf://meta-llama/Llama-3-8B"
      resources:
        requests:
          cpu: "4"
          memory: "32Gi"
          nvidia.com/gpu: "1"
    containers:
    - name: kserve-container
      env:
      - name: MAX_MODEL_LEN
        value: "4096"
      - name: GPU_MEMORY_UTILIZATION
        value: "0.85"
```

## Endpoint
- get_model_endpoint for inference URL
- vLLM: /v1/completions, KServe v2: /v2/models/[model]/infer
REPORT_EOF

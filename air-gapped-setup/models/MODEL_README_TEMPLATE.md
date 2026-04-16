# [Model Name] - Deployment Guide

<!-- Template for creating new model deployment documentation -->
<!-- Copy this file to models/<model-name>/README.md and customize -->

## Model Information

- **Model**: [Full model name, e.g., Meta Llama 3.1 8B Instruct]
- **Parameters**: [Size in billions, e.g., 8 billion]
- **HuggingFace ID**: `[vendor]/[model-name]`
- **Context Window**: [Default tokens, e.g., 8,192 tokens]
- **License**: [License name, e.g., Llama 3.1 Community License]
- **GPU Requirements**: [Number and type, e.g., 1x NVIDIA H200 (or similar with 16GB+ VRAM)]

## Prerequisites

This guide assumes the following steps from the main documentation have been completed:

✅ **Section 1**: GPU Operator and RHOAI installed  
✅ **Section 2.1-2.3**: Namespace `llm-models` and PVC `model-storage` created  
✅ **Section 2.4**: Model files pre-downloaded to PVC at `/mnt/models/[vendor]/[model-name]`

If any prerequisite is missing, refer to [air-gapped-env-setup.md](../../../air-gapped-env-setup.md).

## Quick Deploy

```bash
# Navigate to this directory
cd models/[model-name]/

# Deploy all resources
oc apply -f .

# Verify deployment
oc get pods -n llm-models -l model=[model-label]
oc get route [route-name] -n llm-models
```

## Configuration Parameters

### Deployment Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Model Path** | `/mnt/models/[vendor]/[model-name]` | Location in PVC |
| **GPUs** | [number] | Number of GPUs allocated |
| **Tensor Parallel** | [1 or 2] | GPU parallelization (1 for single GPU) |
| **Max Model Length** | [tokens] | Context window size |
| **GPU Memory Util** | [0.85-0.95] | Percentage of VRAM to use |
| **Port** | 8000 | vLLM API port |

### Resource Allocation

```yaml
resources:
  requests:
    cpu: [cores]
    memory: [size]Gi
    nvidia.com/gpu: "[number]"
  limits:
    cpu: [cores]
    memory: [size]Gi
    nvidia.com/gpu: "[number]"
```

## Pre-Download Model

Before deploying, ensure the model is downloaded to the PVC:

**For Gated Models (if applicable):**
1. Request access at https://huggingface.co/[vendor]/[model-name]
2. Accept license agreement
3. Create access token at https://huggingface.co/settings/tokens

```bash
# On internet-connected machine
# Install huggingface-hub if not already installed
pip install huggingface-hub

# Login to HuggingFace if needed (required for gated models)
hf auth login
# Paste your access token when prompted

# Verify access (for gated models)
hf auth whoami

# Download model to cache directory
# Note: ./models/cache is excluded from git via .gitignore
hf download [vendor]/[model-name] \
  --local-dir ./models/cache/[vendor]/[model-name]

# Create tarball (maintains vendor/model structure)
tar -czf [model-name].tar.gz -C ./models/cache .

# Transfer and extract to PVC (see main documentation section 2.4)
```

## Testing

```bash
# Get route URL
ROUTE_URL=$(oc get route [route-name] -n llm-models -o jsonpath='{.spec.host}')

# Test health
curl -k https://$ROUTE_URL/health

# Test inference
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "[vendor]/[model-name]",
    "messages": [
      {"role": "user", "content": "Explain what is Kubernetes in one sentence."}
    ],
    "max_tokens": 100
  }'
```

## Performance Expectations

<!-- Customize based on testing -->

- **First Token Latency**: ~[X]-[Y]ms
- **Generation Speed**: ~[X]-[Y] tokens/second (on H200)
- **Memory Usage**: ~[X]GB VRAM + ~[Y]GB system RAM
- **Concurrent Requests**: Up to [X]-[Y] (depending on context length)

## Scaling

To increase capacity, adjust the replica count:

```bash
oc scale deployment [deployment-name] -n llm-models --replicas=2
```

**Note**: Each replica requires [number] GPU(s). Ensure sufficient GPU resources are available.

## Troubleshooting

### Pod Not Starting

```bash
# Check events
oc describe pod -n llm-models -l model=[model-label]

# Common issues:
# - No available GPU: Check GPU allocation
# - Model not found: Verify PVC contains model files
# - OOM: Reduce --max-model-len or --gpu-memory-utilization
```

### Slow Inference

```bash
# Check GPU utilization
POD=$(oc get pods -n llm-models -l model=[model-label] -o name | head -1)
oc exec $POD -- nvidia-smi

# Verify model is loaded in GPU memory
oc logs $POD | grep "model loaded"
```

## Model-Specific Notes

<!-- Add any special considerations for this model -->

- [Note 1]
- [Note 2]
- [Note 3]

## Cleanup

```bash
# Delete model deployment
oc delete -f route.yaml
oc delete -f service.yaml
oc delete -f deployment.yaml
```

## References

- **HuggingFace**: [URL to model card]
- **Model Documentation**: [URL to official docs]
- **License**: [URL to license]

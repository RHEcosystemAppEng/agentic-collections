# Model Deployment Manifests

This directory contains deployment manifests organized by model. Each model has its own subdirectory with complete deployment resources.

## Directory Structure

```
models/
├── llama-3.1-8b-instruct/      # Meta Llama 3.1 8B Instruct
├── llama-3.1-70b-instruct/     # Meta Llama 3.1 70B Instruct
├── mistral-nemo-12b/           # Mistral NeMo 12B Instruct
├── qwen-2.5-7b/                # Qwen 2.5 7B Instruct
├── qwen-2.5-32b/               # Qwen 2.5 32B Instruct
├── deepseek-coder-v2-16b/      # DeepSeek Coder V2 16B Lite
└── granite-3.1-8b/             # IBM Granite 3.1 8B Instruct
```

## Model Manifest Structure

Each model directory contains:

```
<model-name>/
├── deployment.yaml    # Kubernetes Deployment with vLLM container
├── service.yaml       # ClusterIP Service
├── route.yaml         # OpenShift Route for external access
└── README.md          # Model-specific documentation and config
```

## Quick Deployment

Deploy any model with:

```bash
cd models/<model-name>
oc apply -f deployment.yaml
oc apply -f service.yaml
oc apply -f route.yaml
```

## Prerequisites

Before deploying any model:

1. **Platform Setup Complete**: GPU Operator and RHOAI installed (manifests 01-07)
2. **Namespace Created**: `llm-models` namespace exists
3. **Storage Ready**: PVC `model-storage` exists in `llm-models` namespace
4. **Model Pre-downloaded**: Model files exist in PVC at expected path

## Model Selection Guide

| Model | Size | GPUs | Best For | Complexity |
|-------|------|------|----------|------------|
| **Llama 3.1 8B** | 8B | 1 | General purpose, fastest inference | Low |
| **Qwen 2.5 7B** | 7B | 1 | Code generation, multilingual | Low |
| **Granite 3.1 8B** | 8B | 1 | Enterprise, RAG applications | Low |
| **Mistral NeMo 12B** | 12B | 1 | Balanced quality/speed | Medium |
| **DeepSeek Coder 16B** | 16B | 1 | Advanced code generation | Medium |
| **Qwen 2.5 32B** | 32B | 1 | High quality, complex tasks | High |
| **Llama 3.1 70B** | 70B | 1-2 | Highest quality, production | High |

## Creating New Model Deployment

To add a new model:

1. **Create model directory**: `mkdir -p models/<model-name>/`
2. **Copy manifests** from an existing model directory (e.g., `llama-3.1-8b-instruct/`)
3. **Copy README template**: `cp MODEL_README_TEMPLATE.md models/<model-name>/README.md`
4. **Update `deployment.yaml`**:
   - Model path: `/mnt/models/<vendor>/<model-name>`
   - Served model name: `<vendor>/<model-name>`
   - Resource requirements (CPU, memory, GPU count)
   - Tensor parallel size (1 for single GPU, 2+ for multi-GPU)
5. **Update `service.yaml`**:
   - Service name
   - Labels (especially `model:` label)
6. **Update `route.yaml`**:
   - Route name
   - Labels (match deployment)
7. **Customize `README.md`** with model-specific details
8. **Test deployment** and document performance results
9. **Add subsection** to main documentation (`air-gapped-env-setup.md` section 2.5.X)

**Template Files:**
- `MODEL_README_TEMPLATE.md` - Documentation template with all sections
- `llama-3.1-8b-instruct/` - Reference implementation

## Common Configuration Changes

### Single GPU to Multi-GPU (70B models)

```yaml
# In deployment.yaml
args:
  - --tensor-parallel-size=2  # Change from 1 to 2
resources:
  limits:
    nvidia.com/gpu: "2"  # Change from "1" to "2"
```

### Adjust Context Window

```yaml
# In deployment.yaml
args:
  - --max-model-len=16384  # Increase from 8192
```

### Reduce Memory Usage

```yaml
# In deployment.yaml
args:
  - --gpu-memory-utilization=0.80  # Reduce from 0.90
```

## Deployment Order

For deploying multiple models:

```bash
# Deploy smallest models first (less VRAM)
cd llama-3.1-8b-instruct && oc apply -f .
cd ../qwen-2.5-7b && oc apply -f .
cd ../mistral-nemo-12b && oc apply -f .

# Verify GPU allocation before deploying larger models
oc describe nodes | grep nvidia.com/gpu
```

## Verification

After deploying any model:

```bash
# Check deployment status
oc get deployments -n llm-models

# Check pod readiness
oc get pods -n llm-models

# Get model endpoint
oc get routes -n llm-models

# Test health
ROUTE=$(oc get route <route-name> -n llm-models -o jsonpath='{.spec.host}')
curl -k https://$ROUTE/health
```

## Troubleshooting

### Pod Stuck in Pending

```bash
# Check GPU availability
oc describe nodes | grep -A 5 "Allocated resources" | grep nvidia.com/gpu

# Check PVC status
oc get pvc -n llm-models
```

### Pod CrashLoopBackOff

```bash
# Check logs
oc logs -n llm-models <pod-name>

# Common issues:
# - Model files not found → Check PVC mount path
# - OOM (Out of Memory) → Reduce max-model-len or gpu-memory-utilization
# - GPU not available → Verify GPU Operator is running
```

## Resource Planning

| Model Size | VRAM Usage | System RAM | Concurrent Users |
|------------|------------|------------|------------------|
| 7-8B | ~16GB | 32Gi | 8-12 |
| 12-16B | ~32GB | 48Gi | 4-8 |
| 32B | ~64GB | 64Gi | 2-4 |
| 70B | ~140GB | 128Gi | 1-2 |

**Note**: VRAM usage assumes FP16/BF16 precision. Quantized models (4-bit, 8-bit) use significantly less VRAM.

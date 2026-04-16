# Architecture Overview: Air-Gapped LLM Deployment

## Design Decision: Direct vLLM Deployments (No KServe)

### Why We Disabled KServe

KServe is the standard model serving framework in OpenShift AI, but it has significant complexity for air-gapped environments:

#### KServe Requirements:
- Red Hat OpenShift Service Mesh operator (Istio)
- Elasticsearch operator (logging)
- Jaeger operator (tracing)
- Kiali operator (observability)
- Complex networking with IngressGateway
- 20+ additional container images to mirror

#### Air-Gapped Challenges:
- Mirror and maintain 4 additional operators
- Configure Service Mesh in restricted network
- Troubleshoot Istio networking without internet access
- Significantly increased setup time and complexity

### Our Simplified Approach

```
┌─────────────────────────────────────────────────────┐
│  External Client (OpenCode)                         │
│  HTTPS Request to Route                             │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│  OpenShift Route (Edge TLS Termination)             │
│  https://llama-3-8b.apps.cluster.example.com        │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│  Service (ClusterIP)                                │
│  Type: ClusterIP                                    │
│  Port: 8000 → TargetPort: 8000                      │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│  Deployment                                         │
│  - Replicas: 1 (or more for HA)                     │
│  - Container: vllm/vllm-openai:latest               │
│  - Command: vllm serve <model>                      │
│  - GPU: 1x NVIDIA H200                              │
│  - Resources: 8 CPU, 32Gi RAM, 1 GPU                │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│  PersistentVolumeClaim                              │
│  - Storage: 200Gi (LVMS)                            │
│  - Contains: Pre-downloaded model from HuggingFace  │
└─────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Model Storage (PVC)
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-storage
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: lvms-vg1
  resources:
    requests:
      storage: 200Gi
```

**Purpose**: Store pre-downloaded models from HuggingFace
**Air-Gap Strategy**: Models downloaded once, cached in PVC

### 2. vLLM Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llama-3-8b
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        command: ["vllm", "serve"]
        args:
          - /models/meta-llama/Llama-3.1-8B-Instruct
          - --port=8000
          - --tensor-parallel-size=1
        resources:
          limits:
            nvidia.com/gpu: "1"
```

**Purpose**: Run vLLM inference server with GPU acceleration
**API**: OpenAI-compatible (Chat Completions API v1)

### 3. Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: llama-3-8b
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
```

**Purpose**: Internal cluster networking for the deployment

### 4. Route
```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: llama-3-8b
spec:
  to:
    kind: Service
    name: llama-3-8b
  port:
    targetPort: 8000
  tls:
    termination: edge
```

**Purpose**: External HTTPS access with automatic TLS

## Advantages of This Architecture

### Simplicity
- ✅ 4 simple Kubernetes resources (PVC, Deployment, Service, Route)
- ✅ No service mesh complexity
- ✅ Standard OpenShift patterns
- ✅ Easy to debug and troubleshoot

### Air-Gapped Friendly
- ✅ Minimal container images to mirror (vLLM only)
- ✅ No external dependencies during runtime
- ✅ Models pre-downloaded to PVC
- ✅ No operator coordination required

### Performance
- ✅ Direct container-to-GPU mapping
- ✅ No networking overhead from Istio sidecars
- ✅ Simple request path (Route → Service → Pod)
- ✅ Full control over vLLM parameters

### Maintainability
- ✅ Easy to update models (just change deployment)
- ✅ Easy to scale (increase replicas)
- ✅ Easy to monitor (standard Kubernetes metrics)
- ✅ Easy to rollback (standard deployment strategies)

## Comparison: KServe vs Direct Deployment

| Aspect | KServe | Direct Deployment |
|--------|--------|-------------------|
| **Complexity** | High (Service Mesh required) | Low (4 resources) |
| **Air-Gap Setup** | ~30 container images | ~3 container images |
| **Operators Required** | 5 (RHOAI, Service Mesh, ES, Jaeger, Kiali) | 2 (RHOAI, GPU) |
| **Networking** | IngressGateway (Istio) | Route (native) |
| **Model Switching** | Edit InferenceService | Edit Deployment |
| **Debugging** | Complex (Istio logs, sidecars) | Simple (pod logs) |
| **API Protocol** | OpenAI-compatible | OpenAI-compatible |
| **Performance** | Good (with sidecar overhead) | Excellent (direct) |
| **Scaling** | Auto-scaling support | Manual scaling |

## Model Lifecycle

### Pre-Download (One-Time Setup)
```bash
# On machine with internet access
podman run --rm -v ./models/cache:/models \
  python:3.11 bash -c "
    pip install huggingface-hub
    hf auth login
    hf download meta-llama/Llama-3.1-8B-Instruct \
      --local-dir /models/meta-llama/Llama-3.1-8B-Instruct
  "

# Create tarball
tar -czf llama-3.1-8b.tar.gz -C ./models/cache .

# Transfer to air-gapped cluster
oc cp llama-3.1-8b.tar.gz <pod>:/mnt/models/
```

### Deployment
```bash
oc apply -f deployment.yaml
oc apply -f service.yaml
oc apply -f route.yaml
```

### Access
```bash
ROUTE=$(oc get route llama-3-8b -o jsonpath='{.spec.host}')
curl https://$ROUTE/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "meta-llama/Llama-3.1-8B-Instruct", "messages": [...]}'
```

## OpenCode Integration

OpenCode connects directly via OpenAI-compatible API:

```json
{
  "provider": {
    "openshift-vllm": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "https://llama-3-8b.apps.cluster.example.com/v1"
      },
      "models": {
        "meta-llama/Llama-3.1-8B-Instruct": {
          "name": "Llama 3.1 8B on H200"
        }
      }
    }
  }
}
```

No difference from OpenCode's perspective - same API, simpler backend.

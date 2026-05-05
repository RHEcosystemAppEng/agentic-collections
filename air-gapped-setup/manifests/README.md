# Manifests Directory

This directory contains Kubernetes/OpenShift manifests for setting up the air-gapped LLM deployment environment.

## Manifest Execution Order

### Platform Operators (01-07)
Apply in numerical order for initial platform setup:

```bash
# GPU Operator
oc apply -f 01-gpu-operator-namespace.yaml
oc apply -f 02-gpu-operator-operatorgroup.yaml
oc apply -f 03-gpu-operator-subscription.yaml
oc apply -f 04-gpu-clusterpolicy.yaml

# RHOAI Operator
oc apply -f 05-rhoai-namespace.yaml
oc apply -f 06-rhoai-subscription.yaml
# Note: OperatorGroup is auto-created by RHOAI - do NOT create manually
oc apply -f 07-datasciencecluster.yaml
```

### Quick Apply All
```bash
# Apply all platform manifests in order
for manifest in {01..07}-*.yaml; do
  oc apply -f "$manifest"
  sleep 10
done
```

### Model Deployment
Models are organized in the `models/` subdirectory. Each model has its own directory with deployment manifests.

Example deployment for Llama 3.1 8B Instruct:

```bash
# Deploy from model directory
cd models/llama-3.1-8b-instruct/
oc apply -f .

# Or deploy specific manifests
oc apply -f deployment.yaml
oc apply -f service.yaml
oc apply -f route.yaml

# Verify deployment
oc get pods -n llm-models
oc get route llama-3-8b -n llm-models
```

**Note**: See `models/README.md` for complete model deployment guide and configuration options.

## Manifest Descriptions

### Platform Setup (01-07)

| File | Resource | Purpose |
|------|----------|---------|
| `01-gpu-operator-namespace.yaml` | Namespace | Creates `nvidia-gpu-operator` namespace |
| `02-gpu-operator-operatorgroup.yaml` | OperatorGroup | Configures GPU Operator scope |
| `03-gpu-operator-subscription.yaml` | Subscription | Installs NVIDIA GPU Operator |
| `04-gpu-clusterpolicy.yaml` | ClusterPolicy | Configures GPU drivers and device plugins |
| `05-rhoai-namespace.yaml` | Namespace | Creates `redhat-ods-operator` namespace |
| `06-rhoai-subscription.yaml` | Subscription | Installs Red Hat OpenShift AI |
| `07-datasciencecluster.yaml` | DataScienceCluster | Initializes RHOAI components (KServe disabled) |

### Model Deployment

Model deployment manifests are organized in the `models/` subdirectory:

```
models/
├── llama-3.1-8b-instruct/
│   ├── deployment.yaml   # vLLM Deployment with GPU
│   ├── service.yaml      # ClusterIP Service
│   ├── route.yaml        # External HTTPS Route
│   └── README.md         # Model-specific guide
└── README.md             # Model directory overview
```

| File | Resource | Purpose |
|------|----------|---------|
| `deployment.yaml` | Deployment | vLLM server with model-specific configuration and GPU allocation |
| `service.yaml` | Service | ClusterIP service for model endpoint |
| `route.yaml` | Route | External HTTPS access to model API |
| `README.md` | Documentation | Model-specific configuration, testing, and troubleshooting |

**Note**: Each model has its own directory with complete deployment resources. See `models/README.md` for model selection guide and deployment patterns.

## Important Notes

- All manifests are idempotent (safe to apply multiple times)
- **RHOAI OperatorGroup**: NOT included - operator creates it automatically
  - Creating a manual OperatorGroup causes `TooManyOperatorGroups` error
- Wait for operators to reach `Succeeded` state before proceeding
- GPU ClusterPolicy may take 5-10 minutes to label GPU nodes
- DataScienceCluster initialization may take 5-10 minutes

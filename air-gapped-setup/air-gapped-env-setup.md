# Air-Gapped LLM Model Deployment on OpenShift with OpenCode Integration

## Purpose

This guide demonstrates how to deploy and serve large language models (LLMs) on Red Hat OpenShift in an air-gapped environment and integrate them with OpenCode for local AI-assisted development. The setup simulates enterprise air-gapped scenarios where models must be pre-downloaded and deployed without direct internet access during runtime.

**Key Objectives:**
- Deploy production-grade LLM inference on OpenShift using GPU acceleration
- Simulate air-gapped deployment patterns (pre-downloaded models, local registry)
- Expose models via OpenAI-compatible API for OpenCode consumption
- Provide reproducible configurations for common LLM models

## Technology Stack

### Infrastructure
- **Platform**: Red Hat OpenShift Container Platform 4.x
- **Model Serving**: Red Hat OpenShift AI (RHOAI) v2.25.4
- **Inference Runtime**: vLLM (OpenAI-compatible API server)
- **Service Mesh**: KServe (Kubernetes-native model serving)
- **Storage**: LVMS (Logical Volume Manager Storage) - local storage provisioner
- **Networking**: OpenShift Routes (HTTPS edge termination)

### AI/ML Components
- **Framework**: KServe InferenceService + ServingRuntime
- **GPU Acceleration**: NVIDIA GPU Operator with H200 support
- **Model Format**: PyTorch / Safetensors from HuggingFace
- **API Protocol**: OpenAI Chat Completions API (v1)

### Development Tools
- **IDE Integration**: OpenCode CLI with OpenAI-compatible provider
- **Model Source**: HuggingFace Hub (pre-downloaded for air-gap)

## Hardware Specifications

**Note:** This section describes the reference lab environment used for testing. Your environment may differ.

### Compute Resources (Reference Lab)
| Component | Specification |
|-----------|---------------|
| **CPU** | 224 cores (Intel Xeon) |
| **Memory** | 2TB RAM (~2,113,236 Mi) |
| **GPU** | 8x NVIDIA H200 (143GB VRAM each) |
| **Total GPU VRAM** | 1,144 GB (1.1 TB) |
| **Storage Class** | lvms-vg1 (local storage) |

### GPU Details
```
Model: NVIDIA H200
Architecture: Hopper
Compute Capability: 9.0
Memory per GPU: 143,771 MiB (~143 GB)
Memory Bandwidth: High (HBM3)
FP16/BF16 Performance: Optimized for LLM inference
```

---

## 1. Air-Gapped Environment Setup

#### Air-Gapped Challenges:
- Mirror and maintain 4 additional operators
- Upload and save the models without internet connection

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

### 1.1 Environment Pre-configuration

This section covers the installation and configuration of required operators and platform components. All commands are idempotent and safe to execute multiple times.

#### 1.1.1 Prerequisites Verification

Verify cluster access and basic requirements:

```bash
# Verify cluster connection
oc whoami
oc version

# Check cluster nodes
oc get nodes

# Verify you have cluster-admin privileges
oc auth can-i create namespaces --all-namespaces
```

#### 1.1.2 NVIDIA GPU Operator Installation

The NVIDIA GPU Operator manages GPU resources and drivers on OpenShift nodes.

**Check if already installed:**

```bash
# Check for GPU Operator
oc get csv -n nvidia-gpu-operator 2>/dev/null | grep gpu-operator-certified || echo "GPU Operator not found"

# Check for GPU nodes
oc get nodes -l nvidia.com/gpu.present=true
```

**Install GPU Operator** (if not present):

```bash
# Apply GPU Operator manifests
oc apply -f manifests/01-gpu-operator-namespace.yaml
oc apply -f manifests/02-gpu-operator-operatorgroup.yaml
oc apply -f manifests/03-gpu-operator-subscription.yaml

# Wait for CSV to be created (may take 1-2 minutes)
until oc get csv -n nvidia-gpu-operator 2>/dev/null | grep -q gpu-operator-certified; do
  echo "Waiting for GPU Operator CSV to appear..."
  sleep 10
done

# Wait for CSV to reach Succeeded state (may take 3-5 minutes)
CSV_NAME=$(oc get csv -n nvidia-gpu-operator -o name | grep gpu-operator-certified)
oc wait --for=jsonpath='{.status.phase}'=Succeeded $CSV_NAME -n nvidia-gpu-operator --timeout=300s

# Verify installation
oc get csv -n nvidia-gpu-operator
```

**Create ClusterPolicy for GPU configuration:**

```bash
# Apply GPU ClusterPolicy
oc apply -f manifests/04-gpu-clusterpolicy.yaml

# Wait for GPU nodes to be labeled (may take 5-10 minutes)
sleep 60
oc get nodes -l nvidia.com/gpu.present=true

# Verify GPU resources
oc describe nodes | grep -A 10 "Capacity:" | grep nvidia.com/gpu
```

#### 1.1.3 Red Hat OpenShift AI (RHOAI) Installation

**Check if already installed:**

```bash
# Check for RHOAI operator
oc get csv --all-namespaces | grep rhods-operator || echo "RHOAI not found"

# Check for DataScienceCluster
oc get datasciencecluster --all-namespaces 2>/dev/null || echo "No DataScienceCluster found"
```

**Install RHOAI Operator** (if not present):

> **Note**: For air-gapped environments, ensure the RHOAI operator images are mirrored to your internal registry. This guide assumes operator catalogs are already configured.

```bash
# Apply RHOAI Operator manifests
# Note: OperatorGroup is NOT included - RHOAI creates it automatically
oc apply -f manifests/05-rhoai-namespace.yaml
oc apply -f manifests/06-rhoai-subscription.yaml

# Wait for CSV to be created (may take 1-2 minutes)
until oc get csv -n redhat-ods-operator 2>/dev/null | grep -q rhods-operator; do
  echo "Waiting for RHOAI CSV to appear..."
  sleep 10
done

# Wait for CSV to reach Succeeded state (may take 3-5 minutes)
CSV_NAME=$(oc get csv -n redhat-ods-operator -o name | grep rhods-operator)
oc wait --for=jsonpath='{.status.phase}'=Succeeded $CSV_NAME -n redhat-ods-operator --timeout=300s

# Verify installation
oc get csv -n redhat-ods-operator
```

**Create DataScienceCluster:**

The DataScienceCluster initializes RHOAI components. We **disable KServe** (requires Service Mesh - complex for air-gapped) and use **direct vLLM Deployments** with OpenShift Routes instead.

```bash
# Apply DataScienceCluster manifest
oc apply -f manifests/07-datasciencecluster.yaml

# Wait for components to initialize (may take 5-10 minutes)
oc get pods -n redhat-ods-applications -w
# Press Ctrl+C when pods are Running

# Verify core components are running
oc get pods -n redhat-ods-applications
```

> **Why Disable KServe?**
> - KServe requires Red Hat Service Mesh (Istio) which adds:
>   - 4 additional operators (Service Mesh, Elasticsearch, Jaeger, Kiali)
>   - Complex networking configuration
>   - Many additional container images to mirror for air-gapped
> 
> **Our Approach Instead:**
> - Use standard Kubernetes Deployments with vLLM containers
> - Expose via OpenShift Routes (native, simple, HTTPS)
> - Direct control over model serving configuration
> - Same end result: models accessible via OpenAI-compatible API

#### 1.1.4 Verification

Verify all components are ready:

```bash
# Check GPU Operator
oc get csv -n nvidia-gpu-operator | grep Succeeded

# Check RHOAI Operator
oc get csv --all-namespaces | grep rhods-operator | grep Succeeded

# Check DataScienceCluster status
oc get datasciencecluster default-dsc -o jsonpath='{.status.phase}'

# Check GPU nodes and availability
oc get nodes -l nvidia.com/gpu.present=true -o custom-columns=NAME:.metadata.name,GPU-COUNT:.status.capacity.'nvidia\.com/gpu'

# Verify RHOAI components are running
oc get pods -n redhat-ods-applications
```

**Expected Output:**
```
GPU Operator: Succeeded
RHOAI Operator: Succeeded
DataScienceCluster: Ready
GPU Nodes: 1 or more nodes with GPUs
RHOAI Pods: All Running (dashboard, pipelines, model-controller, etc.)
```

**Note**: KServe components will NOT be present (intentionally disabled). Model serving will use standard Kubernetes Deployments.

---

### 1.2 Model Deployment

This section demonstrates how to deploy an LLM model using direct vLLM Deployments with GPU acceleration. The example uses **Llama 3.1 8B Instruct**, but the manifests are designed to be easily adapted for other models.

#### 1.2.1 Pre-requisites

Before deploying, ensure:
- GPU Operator is installed and GPUs are available
- RHOAI is installed (DataScienceCluster ready)
- Model files are pre-downloaded and available (air-gapped scenario)

Verify GPU availability:

```bash
# Check GPU capacity and allocatable
oc describe nodes | awk '/Capacity:/,/Allocatable:/ {if (/nvidia.com\/gpu/) print "Capacity:", $0} /Allocatable:/,/Allocated resources:/ {if (/nvidia.com\/gpu/ && !/Capacity:/) print "Allocatable:", $0}'

# Expected output (X = number of GPUs in your cluster):
# Capacity:   nvidia.com/gpu:     X
# Allocatable:   nvidia.com/gpu:     X

# Alternative simpler command (shows both lines without labels)
oc describe nodes | grep -E "^\s+nvidia.com/gpu:" | head -2
```

#### 1.2.2 Deployment Architecture

```
Namespace (llm-models)
    ↓
PVC (model-storage) ← Pre-downloaded model files
    ↓
Deployment (vllm-llama-3-8b) ← vLLM container with GPU
    ↓
Service (llm-llama-3-8b-svc) ← Internal ClusterIP
    ↓
Route (llama-3-8b) ← External HTTPS access
```

#### 1.2.3 Create Namespace and Storage

```bash
# Create namespace for LLM models
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: llm-models
  labels:
    app: llm-serving
    project: air-gapped-llm
EOF

# Create PVC for model storage
cat <<EOF | oc apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: model-storage
  namespace: llm-models
  labels:
    app: llm-serving
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: lvms-vg1
  resources:
    requests:
      storage: 200Gi
EOF

# Wait for PVC to be bound
oc wait --for=jsonpath='{.status.phase}'=Bound pvc/model-storage -n llm-models --timeout=120s

# Verify
oc get pvc -n llm-models
```

#### 1.2.4 Pre-download Models (Air-Gapped Preparation)

This process is generic for all models. Configure the variables below for your specific model, then execute the commands.

**Important for Gated Models:**

Some models (Llama, Mistral, Gemma, etc.) require approval before downloading:
1. Visit the model's HuggingFace page (e.g., `https://huggingface.co/<HF_MODEL_ID>`)
2. Click "Request access to model" and accept the license agreement
3. Create a HuggingFace access token at https://huggingface.co/settings/tokens

**On a machine with internet access:**

```bash
# Configure these variables for your model
export HF_MODEL_ID="vendor/model-name"           # HuggingFace model ID (e.g., meta-llama/Llama-3.1-8B-Instruct)
export MODEL_VENDOR="vendor"                     # Vendor name (e.g., meta-llama, mistralai, Qwen)
export MODEL_NAME="model-name"                   # Model name (e.g., Llama-3.1-8B-Instruct)
export TARBALL_NAME="model-archive.tar.gz"       # Tarball filename (e.g., llama-3.1-8b.tar.gz)

# Install huggingface-hub (provides 'hf' CLI)
pip install huggingface-hub

# Login to HuggingFace (required for gated models)
hf auth login
# Paste your access token when prompted

# Verify authentication
hf auth whoami

# Download model to cache directory
# Note: ./models/cache is excluded from git via .gitignore
hf download ${HF_MODEL_ID} \
  --local-dir ./models/cache/${MODEL_VENDOR}/${MODEL_NAME}

# If you get "Access denied" error:
# - Verify you accepted the license at the model's HuggingFace page
# - Check your token has 'read' permission
# - Confirm login: hf auth whoami

# Create tarball for transfer (maintains vendor/model structure)
tar -czf ${TARBALL_NAME} -C ./models/cache .

# Verify tarball created
ls -lh ${TARBALL_NAME}
```

**Transfer to air-gapped cluster:**

```bash
# Transfer tarball to bastion/jump host with oc access
# (Use scp, rsync, or physical media depending on your environment)
# Example: scp ${TARBALL_NAME} user@bastion:/tmp/

# On bastion host with oc access:
# Set tarball name variable to match what you created
export TARBALL_NAME="model-archive.tar.gz"

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

# Copy tarball to PVC
oc cp ${TARBALL_NAME} llm-models/model-loader:/mnt/models/

# Extract tarball in pod
oc exec -n llm-models model-loader -- tar -xzf /mnt/models/${TARBALL_NAME} -C /mnt/models/

# Remove tarball to save space
oc exec -n llm-models model-loader -- rm /mnt/models/${TARBALL_NAME}

# Verify model files extracted correctly
oc exec -n llm-models model-loader -- ls -lh /mnt/models/

# Delete loader pod
oc delete pod model-loader -n llm-models
```

**Note:** The PVC can hold multiple models. Extract each model tarball to `/mnt/models/` maintaining the vendor directory structure (e.g., `meta-llama/`, `mistralai/`, `Qwen/`).

#### 1.2.5 Model-Specific Deployments

Each model has a dedicated README in `models/<model-name>/` with complete deployment instructions, configuration details, air-gapped setup, testing examples, and troubleshooting guides.

**Supported Models:**

| Model | Parameters | Architecture | GPU Requirements | VRAM Usage | Context Window | Status | Documentation |
|-------|------------|--------------|------------------|------------|----------------|--------|---------------|
| **Qwen 2.5 7B Instruct** | 7B | Dense | 1x H200 | ~14GB | 32K | ✅ Validated | [README](models/qwen-2.5-7b-instruct/README.md) |
| **Mixtral 8x7B Instruct** | 47B (13B active) | MoE | 1x H200 | ~47GB | 32K | ✅ Validated | [README](models/mixtral-8x7b-instruct/README.md) |
| **Mixtral 8x22B Instruct** | 141B (39B active) | MoE | 4x H200 | ~131GB | 64K | ✅ Validated | [README](models/mixtral-8x22b-instruct/README.md) |

**Model Selection Guide:**

- **Qwen 2.5 7B** - Best for: Code generation, math, multilingual tasks. Fastest inference, minimal GPU requirements.
- **Mixtral 8x7B** - Best for: OpenCode/agentic workflows, fast inference with strong quality. MoE architecture = 3-4x faster than dense models.
- **Mixtral 8x22B** - Best for: Advanced reasoning, complex tasks, long-context analysis. Top-tier quality with MoE efficiency.

**Key Features:**
- ✅ **No Quantization** - All models use full precision (FP16/auto) for perfect context retention
- ✅ **Tool Calling Support** - All models configured with `--enable-auto-tool-choice` and Hermes parser
- ✅ **OpenCode Compatible** - Pre-configured `opencode.json` files for AI-assisted development
- ✅ **Apache 2.0 License** - All models are fully open-source, no approval needed

**Deployment Steps:**

For any model listed above:
1. Follow the model's README for complete deployment instructions
2. Each README includes all necessary commands (namespace creation, model download, air-gapped transfer, deployment, verification)
3. All commands are ready for copy-paste execution

#### 1.2.6 Verify Deployment

These verification steps work for any deployed model. Adjust the selector labels or route names as needed.

```bash
# Check all deployments in llm-models namespace
oc get deployment -n llm-models

# Check all pods (may take 2-5 minutes to load model)
oc get pods -n llm-models

# Check logs for specific model (use label selector from your model)
export MODEL_LABEL="model=your-model-label"    # e.g., model=llama-3.1-8b-instruct
POD=$(oc get pods -n llm-models -l ${MODEL_LABEL} -o name | head -1)
oc logs -f $POD -n llm-models

# Get all routes
oc get routes -n llm-models

# Get specific route URL
export ROUTE_NAME="your-route-name"    # e.g., llama-3-8b
ROUTE_URL=$(oc get route ${ROUTE_NAME} -n llm-models -o jsonpath='{.spec.host}')
echo "Model endpoint: https://$ROUTE_URL"
```

#### 1.2.7 Test Model API

All models expose an OpenAI-compatible API. Adjust the route name and model name to match your deployment.

```bash
# Set your model configuration
export ROUTE_NAME="your-route-name"                    # e.g., llama-3-8b
export SERVED_MODEL_NAME="vendor/model-name"           # e.g., meta-llama/Llama-3.1-8B-Instruct

# Get route URL
ROUTE_URL=$(oc get route ${ROUTE_NAME} -n llm-models -o jsonpath='{.spec.host}')
echo "Testing model at: https://$ROUTE_URL"

# Test health endpoint
curl -k https://$ROUTE_URL/health
# Expected: {"status":"ok"}

# List available models
curl -k https://$ROUTE_URL/v1/models

# Test chat completions
curl -k https://$ROUTE_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"${SERVED_MODEL_NAME}\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Hello, who are you?\"}
    ],
    \"max_tokens\": 100,
    \"temperature\": 0.7
  }"
```

**Common API Endpoints:**
- `/health` - Health check
- `/v1/models` - List available models
- `/v1/chat/completions` - Chat completions (OpenAI-compatible)
- `/v1/completions` - Text completions
- `/metrics` - Prometheus metrics (if enabled)

**Note:** For model-specific testing examples and validation, see each model's README in `models/<model-name>/README.md`.

#### 1.2.8 Deploying Additional Models

Models are organized in `models/<model-name>/` directories. Each model directory contains:
- `servingruntime.yaml` - vLLM runtime configuration
- `inferenceservice.yaml` - KServe inference service definition
- `opencode.json` - OpenCode integration configuration
- `README.md` - Model-specific documentation

**To deploy additional models:**

1. **Set environment variables for your model:**

```bash
# Configure these variables for your new model
export MODEL_NAME="model-name"                           # e.g., mistral-7b-instruct
export MODEL_VENDOR="vendor"                             # e.g., mistralai, Qwen
export MODEL_FULL_NAME="Vendor/Model-Name"               # e.g., mistralai/Mistral-7B-Instruct-v0.3
export MODEL_PATH="/mnt/models/${MODEL_VENDOR}/${MODEL_FULL_NAME##*/}"
export GPU_COUNT="1"                                     # 1 for small models, 2-4 for large models
export MAX_MODEL_LEN="32768"                             # Context window (32768, 65536, etc.)
```

2. **Create model directory and copy template manifests:**

```bash
# Create directory structure
mkdir -p models/${MODEL_NAME}

# Copy manifests from a reference model (e.g., qwen-2.5-7b-instruct)
cp models/qwen-2.5-7b-instruct/*.yaml models/${MODEL_NAME}/
cp models/qwen-2.5-7b-instruct/opencode.json models/${MODEL_NAME}/
```

3. **Update key parameters in manifests:**

| Parameter | File | Location | Value to Set |
|-----------|------|----------|--------------|
| **Runtime Name** | `servingruntime.yaml` | `metadata.name` | `vllm-${MODEL_NAME}-runtime` |
| **Model Path** | `servingruntime.yaml` | `args: --model` | `${MODEL_PATH}` |
| **Context Length** | `servingruntime.yaml` | `args: --max-model-len` | `${MAX_MODEL_LEN}` |
| **GPU Count** | `servingruntime.yaml` | `args: --tensor-parallel-size` | `${GPU_COUNT}` |
| **GPU Resources** | `servingruntime.yaml` | `resources.limits.nvidia.com/gpu` | `"${GPU_COUNT}"` |
| **Service Name** | `inferenceservice.yaml` | `metadata.name` | `${MODEL_NAME}-inference` |
| **Runtime Reference** | `inferenceservice.yaml` | `spec.predictor.model.runtime` | `vllm-${MODEL_NAME}-runtime` |
| **Model Name** | `inferenceservice.yaml` | `spec.predictor.model.modelFormat.name` | `${MODEL_FULL_NAME}` |

4. **Update opencode.json configuration:**

```bash
# Update the provider name, model path, and endpoint URL
# Replace placeholders with your actual values:
# - Provider name: openshift-ai-<model-name>
# - Model path: ${MODEL_PATH}
# - Base URL: https://<model-name>-inference-llm-models.apps.<your-cluster>.com/v1
```

5. **Deploy the model:**

```bash
# Navigate to model directory
cd models/${MODEL_NAME}/

# Apply manifests
oc apply -f servingruntime.yaml
oc apply -f inferenceservice.yaml

# Verify deployment
oc get inferenceservice -n llm-models
oc get pods -n llm-models -l serving.kserve.io/inferenceservice=${MODEL_NAME}-inference
```

**Example: Complete deployment workflow**

```bash
# 1. Pre-download model following section 1.2.4
# 2. Configure environment variables
export MODEL_NAME="my-new-model"
export MODEL_VENDOR="vendor-name"
export MODEL_FULL_NAME="vendor-name/ModelName-Version"
export MODEL_PATH="/mnt/models/${MODEL_VENDOR}/${MODEL_FULL_NAME##*/}"
export GPU_COUNT="1"
export MAX_MODEL_LEN="32768"

# 3. Create and customize manifests
mkdir -p models/${MODEL_NAME}
cp models/qwen-2.5-7b-instruct/*.yaml models/${MODEL_NAME}/
# Edit manifests with the values from the table above

# 4. Deploy
cd models/${MODEL_NAME}/
oc apply -f .
```

See `models/<model-name>/README.md` for model-specific examples and configuration patterns.

---

### 1.3 OpenCode Integration

Each model directory includes an `opencode.json` file that configures OpenCode to use the deployed model for AI-assisted development.

#### What is OpenCode?

OpenCode is an AI coding assistant that connects to LLM APIs to provide:
- Code generation and completion
- Documentation generation
- Code review and refactoring suggestions
- Bug detection and fixes

#### Using OpenCode with Air-Gapped Models

**1. Copy the model's opencode.json to your project:**

```bash
# Example for Qwen 2.5 7B
cp models/qwen-2.5-7b-instruct/opencode.json /path/to/your/project/
```

**2. Set KUBECONFIG environment variable:**

OpenCode needs cluster access for the MCP (Model Context Protocol) server integration:

```bash
export KUBECONFIG=/path/to/your/kubeconfig
```

**3. Run OpenCode from the project directory:**

```bash
cd /path/to/your/project
opencode
```

#### OpenCode Configuration Explained

The `opencode.json` file contains:

```json
{
  "provider": {
    "openshift-ai-qwen": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "OpenShift AI - Qwen 2.5 7B",
      "options": {
        "baseURL": "https://qwen-2-5-7b-inference-llm-models.apps.<your-cluster>.com/v1"
      },
      "models": {
        "/mnt/models/Qwen/Qwen2.5-7B-Instruct": {
          "name": "Qwen 2.5 7B Instruct (Air-Gapped)",
          "description": "Qwen 2.5 7B instruction-tuned model deployed on OpenShift AI",
          "limit": {
            "context": 32768,
            "output": 1024
          }
        }
      }
    }
  },
  "model": "openshift-ai-qwen//mnt/models/Qwen/Qwen2.5-7B-Instruct",
  "mcp": {
    "openshift-virtualization": {
      "type": "local",
      "command": [
        "podman", "run", "--rm", "-i", "--network=host",
        "--userns=keep-id:uid=65532,gid=65532",
        "-v", "{env:KUBECONFIG}:/kubeconfig:ro,Z",
        "--entrypoint", "/app/kubernetes-mcp-server",
        "quay.io/ecosystem-appeng/openshift-mcp-server:latest",
        "--kubeconfig", "/kubeconfig",
        "--toolsets", "core,kubevirt"
      ],
      "environment": {
        "KUBECONFIG": "{env:KUBECONFIG}"
      }
    }
  }
}
```

**Key configuration points:**

- **baseURL**: Update with your actual InferenceService route
- **context**: Token limit for input context (32K for Qwen, 64K for Mixtral 8x22B)
- **output**: Maximum tokens for model response
- **MCP server**: Enables OpenCode to interact with OpenShift/Kubernetes resources

#### Installing Agentic Skills

The [agentic-collections](../) repository contains skill packs that extend OpenCode with domain-specific capabilities.

**Install the rh-virt pack (OpenShift Virtualization skills):**

```bash
# From air-gapped-setup directory
lola install rh-virt
```

**Available skills after installation:**
- `/vm-create` - Create virtual machines
- `/vm-lifecycle` - Manage VM lifecycle (start/stop/restart)
- And more...

**Usage:**
```bash
# In OpenCode prompt
/vm-create

# OpenCode will guide you through VM creation
```

#### Important Notes

**Running OpenCode from Correct Directory:**

⚠️ **Always run OpenCode from the `air-gapped-setup` directory**, not the repository root!

```bash
# ✅ CORRECT
cd /path/to/agentic-collections/air-gapped-setup
opencode

# ❌ WRONG - Will load too much context and exceed token limits
cd /path/to/agentic-collections
opencode
```

**Why?** OpenCode loads context from the current directory and its subdirectories. Running from the repo root loads all agentic packs, documentation, and files, easily exceeding the model's context window.

**Environment Variables:**

The MCP server configuration uses `{env:KUBECONFIG}` syntax to reference environment variables:

```json
"-v", "{env:KUBECONFIG}:/kubeconfig:ro,Z"
```

This is OpenCode's special syntax for variable expansion. Standard shell syntax `$KUBECONFIG` will NOT work in the JSON file.

---

### 1.4 Model Performance Results

This section documents performance benchmarks and compatibility results for various LLM models tested on this hardware configuration.

#### Test Environment

- **Hardware**: Dell PowerEdge XE9680L
- **GPUs**: NVIDIA H200 (143GB VRAM each)
- **Storage**: LVMS local storage
- **Network**: Internal cluster networking
- **Test Methodology**: OpenCode skill execution with predefined skill set

#### Performance Metrics

| Model | Version | Parameters | GPUs | GPU Type | Tokens/sec (Single User) | Context Window | Skills Comprehension ✓ | Status | Notes |
|-------|---------|------------|------|----------|--------------------------|----------------|----------------------|--------|-------|
| **Qwen 2.5** | 7B-Instruct | 7B | 1 | H200 | ~85-130 | 32K | ☑ | ✅ Validated | Basic comprehension of the skill but limited context |
| **Mixtral** | 8x7B-Instruct | 47B (13B active) | 1 | H200 | ~62-90 | 32K | ☑ | ✅ Validated | Basic comprehension of the skill but limited context |
| **Mixtral** | 8x22B-Instruct | 141B (39B active) | 4 | H200 | ~40-60* | 64K | ☑ | ✅ Validated | |

**Table Notes:**
- *Mixtral 8x22B performance estimated based on model size and MoE efficiency
- All measurements on unloaded GPU (excluding first request after model load)
- Tokens/sec varies based on prompt length, temperature, and concurrent requests

#### Legend

- **Parameters**: Total model parameters (B = billion)
- **GPUs**: Number of GPUs allocated for inference
- **Avg Response Time**: Average time to first token + generation time (seconds)
- **Skills Comprehension ✓**: 
  - ☑ = Model demonstrates good understanding and execution of loaded skills
  - ☐ = Not yet tested or insufficient skill comprehension
  - ☒ = Poor skill comprehension, not recommended

#### Skill Comprehension Criteria

Models are evaluated based on their ability to:
1. Understand skill descriptions and when to invoke them
2. Parse skill parameters correctly
3. Execute multi-step workflows using multiple skills
4. Maintain context across skill invocations
5. Handle error responses from skills appropriately

**Test Skills Used**: OpenCode agentic collections skill set (configured via Lola AI package manager)

> **Important**: Models must be compatible with **MCP (Model Context Protocol) servers** for skill execution. Skills and their associated MCP servers are managed and configured using **Lola AI package manager** (https://github.com/lola-tech/lola). This ensures standardized skill loading and MCP server orchestration across different model deployments.
>
> Models that fail to properly interpret MCP server responses or execute skill invocations will be marked with ☒ in the Skills Comprehension column.

#### Performance Notes

- **Inference Performance**:
  - Tokens/sec measured during typical OpenCode interactions
  - Single-user workload (concurrent users will reduce per-user tokens/sec)
  - Measured on unloaded GPU (first request after model load excluded)
  - MoE models (Mixtral) show better tokens/sec per active parameter compared to dense models

- **Memory Usage (Validated Models)**:
  - Qwen 2.5 7B: ~14GB VRAM (1x H200)
  - Mixtral 8x7B: ~47GB VRAM (1x H200)
  - Mixtral 8x22B: ~131GB VRAM (4x H200)

- **Recommendations**:
  - **For development/testing**: Qwen 2.5 7B (fastest, lowest resource requirements)
  - **For production OpenCode workflows**: Mixtral 8x7B (excellent balance of speed and quality)
  - **For complex reasoning tasks**: Mixtral 8x22B (best quality, requires multi-GPU setup)
  - **For multi-user scenarios**: Deploy multiple Qwen 2.5 7B instances on separate GPUs

---

## 2. Troubleshooting

For troubleshooting common issues, deployment problems, and getting diagnostic information, see the dedicated [Troubleshooting Guide](TROUBLESHOOTING.md).

---

## 3. License & Authors

### License
This documentation is part of the **Red Hat Agentic Collections** project.

```
Copyright 2024-2026 Red Hat Ecosystem AppEng

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

**SPDX-License-Identifier**: Apache-2.0

### Authors & Contributors
- **Upstream Repository**: [RHEcosystemAppEng/agentic-collections](https://github.com/RHEcosystemAppEng/agentic-collections)
- **Contributors**: Red Hat Ecosystem AppEng Team
- **Maintainer**: Alejandro Villegas (avillega@redhat.com)

### Acknowledgments
- Red Hat OpenShift AI Team
- NVIDIA GPU Operator Contributors
- vLLM Community
- KServe/KNative Community


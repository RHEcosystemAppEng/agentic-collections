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

### Cluster Configuration (Reference Lab)
```
Cluster: appeng-lab01.accl-001.lab.rdu2.dc.redhat.com
Architecture: Single-Node OpenShift (SNO) - High-Performance Lab
Node Type: Dell PowerEdge XE9680L
```

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

### Current Cluster Utilization (Reference Lab Example)
- **CPU Usage**: 48% (~108 cores in use)
- **Memory Usage**: 15% (~322 GB in use)
- **GPUs Available**: 3 of 8 (5 currently serving llm-d models)

### Network Configuration
- **Apps Domain**: `apps.appeng-lab01.accl-001.lab.rdu2.dc.redhat.com`
- **TLS Termination**: Edge (OpenShift Router)
- **External Access**: HTTPS Routes with auto-generated certificates

---

## Air-Gapped Environment Setup

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

### 1. Environment Pre-configuration

This section covers the installation and configuration of required operators and platform components. All commands are idempotent and safe to execute multiple times.

#### 1.1 Prerequisites Verification

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

#### 1.2 NVIDIA GPU Operator Installation

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

#### 1.3 Red Hat OpenShift AI (RHOAI) Installation

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

#### 1.4 Verification

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

### 2. Model Deployment

This section demonstrates how to deploy an LLM model using direct vLLM Deployments with GPU acceleration. The example uses **Llama 3.1 8B Instruct**, but the manifests are designed to be easily adapted for other models.

#### 2.1 Pre-requisites

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

#### 2.2 Deployment Architecture

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

#### 2.3 Create Namespace and Storage

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

#### 2.4 Pre-download Models (Air-Gapped Preparation)

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

#### 2.5 Model-Specific Deployments

Each model has a dedicated README in `models/<model-name>/` with complete deployment instructions, configuration details, air-gapped setup, testing examples, and troubleshooting guides.

**Supported Models:**

| Model | Parameters | GPU Requirements | VRAM Usage | Status | Documentation |
|-------|------------|------------------|------------|--------|---------------|
| **Qwen 2.5 7B Instruct** | 7B | 1x H200 | ~14GB | ✅ Open-access | [README](models/qwen-2.5-7b-instruct/README.md) |
| **Llama 3.1 8B Instruct** | 8B | 1x H200 | ~16GB | 🔒 Requires approval | [README](models/llama-3.1-8b-instruct/README.md) |

**Deployment Steps:**

For any model listed above:
1. Follow the model's README for complete deployment instructions
2. Each README includes all necessary commands (namespace creation, model download, air-gapped transfer, deployment, verification)
3. All commands are ready for copy-paste execution

#### 2.6 Verify Deployment

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

#### 2.7 Test Model API

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

#### 2.8 Deploying Additional Models

Models are organized in `models/<model-name>/` directories. Each model directory contains:
- `deployment.yaml` - vLLM deployment configuration
- `service.yaml` - ClusterIP service
- `route.yaml` - External HTTPS route
- `README.md` - Model-specific documentation

**To deploy additional models:**

1. Create model directory: `models/<model-name>/`
2. Copy and customize manifests from `llama-3.1-8b-instruct/`
3. Update key parameters:

| Parameter | Location | Example Values |
|-----------|----------|----------------|
| **Deployment Name** | `metadata.name` | `vllm-mistral-7b`, `vllm-qwen-32b` |
| **Model Path** | `args[0]` | `/mnt/models/mistralai/Mistral-7B-Instruct-v0.3` |
| **Model Name** | `--served-model-name` | `mistralai/Mistral-7B-Instruct-v0.3` |
| **GPU Count** | `--tensor-parallel-size` | `1` (8B models), `2` (70B models) |
| **GPU Resources** | `resources.limits.nvidia.com/gpu` | `"1"`, `"2"` |
| **Service Name** | `metadata.name` | `llm-mistral-7b-svc` |
| **Route Name** | `metadata.name` | `mistral-7b` |
| **Labels** | `model:` label | Update in all manifests for consistency |

**Example: Deploy Mistral 7B Instruct**

```bash
# 1. Pre-download model following section 2.4
# 2. Create model directory
mkdir -p models/mistral-7b-instruct
cp models/llama-3.1-8b-instruct/*.yaml models/mistral-7b-instruct/

# 3. Update manifests with Mistral parameters
# 4. Deploy
cd models/mistral-7b-instruct/
oc apply -f .
```

See `models/README.md` for model selection guide and configuration patterns.

---

### 3. Models

This section lists all models that have been tested and documented for deployment on this platform. Each model has a dedicated README with complete deployment instructions, configuration details, and validation steps.

#### Available Models

| Model | Parameters | GPU Requirements | VRAM Usage | Use Case | Access | Documentation |
|-------|------------|------------------|------------|----------|--------|---------------|
| **Qwen 2.5 7B Instruct** | 7B | 1x H200 | ~14GB | Code generation, multilingual, math & reasoning | ✅ Open-access | [README](models/qwen-2.5-7b-instruct/README.md) |
| **Llama 3.1 8B Instruct** | 8B | 1x H200 | ~16GB | General purpose, code generation, fast inference | 🔒 Requires approval | [README](models/llama-3.1-8b-instruct/README.md) |

#### Model Status

- ✅ **Open-access**: Model available immediately, no approval needed
- 🔒 **Requires approval**: Model requires accepting license/terms on HuggingFace
- 🔄 **In Progress**: Model documentation in development
- 📝 **Planned**: Model scheduled for testing

**Current Status:**
- ✅ **Qwen 2.5 7B Instruct** - Complete deployment guide, ready to use immediately
- 🔒 **Llama 3.1 8B Instruct** - Complete deployment guide, pending HuggingFace approval

#### Quick Reference

**Qwen 2.5 7B Instruct** ✅ Ready to use now
- **HuggingFace ID**: `Qwen/Qwen2.5-7B-Instruct`
- **Context Window**: 32,768 tokens (supports up to 128K)
- **Performance**: ~90-130 tokens/sec on H200
- **Strengths**: Code generation, multilingual, math & reasoning
- **Access**: Open-access, no approval needed
- **Deployment**: `cd models/qwen-2.5-7b-instruct/ && oc apply -f .`
- **Complete Guide**: [qwen-2.5-7b-instruct/README.md](models/qwen-2.5-7b-instruct/README.md)

**Llama 3.1 8B Instruct** 🔒 Pending approval
- **HuggingFace ID**: `meta-llama/Llama-3.1-8B-Instruct`
- **Context Window**: 8,192 tokens (configurable up to 128K)
- **Performance**: ~80-120 tokens/sec on H200
- **Access**: Requires HuggingFace approval (may take hours/days)
- **Deployment**: `cd models/llama-3.1-8b-instruct/ && oc apply -f .`
- **Complete Guide**: [llama-3.1-8b-instruct/README.md](models/llama-3.1-8b-instruct/README.md)

---

### 4. Model Performance Results

This section documents performance benchmarks and compatibility results for various LLM models tested on this hardware configuration.

#### Test Environment

- **Hardware**: Dell PowerEdge XE9680L
- **GPUs**: NVIDIA H200 (143GB VRAM each)
- **Storage**: LVMS local storage
- **Network**: Internal cluster networking
- **Test Methodology**: OpenCode skill execution with predefined skill set

#### Performance Metrics

| Model | Version | Parameters | GPUs | GPU Type | Avg Response Time | Skills Comprehension ✓ | Notes |
|-------|---------|------------|------|----------|-------------------|----------------------|-------|
| Llama 3.1 | 8B-Instruct | 8B | 1 | H200 | - | ☐ | TBD |
| Llama 3.1 | 70B-Instruct | 70B | 1 | H200 | - | ☐ | TBD |
| Mistral NeMo | 12B-Instruct | 12B | 1 | H200 | - | ☐ | TBD |
| Qwen 2.5 | 7B-Instruct | 7B | 1 | H200 | - | ☐ | TBD |
| Qwen 2.5 | 32B-Instruct | 32B | 1 | H200 | - | ☐ | TBD |
| DeepSeek Coder V2 | 16B-Lite | 16B | 1 | H200 | - | ☐ | TBD |
| Granite 3.1 | 8B-Instruct | 8B | 1 | H200 | - | ☐ | TBD |

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

- **Response Time** includes:
  - Time to first token (TTFT)
  - Average generation time for typical OpenCode interactions
  - Measured on unloaded GPU (first request after model load excluded)

- **Memory Usage**:
  - 8B models: ~16GB VRAM
  - 16B models: ~32GB VRAM
  - 32B models: ~64GB VRAM
  - 70B models: ~140GB VRAM (near H200 capacity)

- **Recommendations**:
  - For production workloads: Use models marked with ☑ in Skills Comprehension
  - For multi-user scenarios: Consider models ≤32B to allow multiple instances
  - For single-user high quality: 70B models provide best results

---

## License & Authors

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


# Air-Gapped LLM Deployment on OpenShift

## Context and Purpose

This documentation provides step-by-step instructions for deploying Large Language Models (LLMs) on Red Hat OpenShift in air-gapped (internet-disconnected) environments.

**Target Environment:**
- Red Hat OpenShift 4.20+
- Red Hat OpenShift AI 2.22+
- NVIDIA GPU-enabled infrastructure
- Completely disconnected from the internet

**Primary Goal:**
Enable organizations with strict security and compliance requirements to run powerful open-source LLMs locally on their OpenShift clusters, removing dependency on external cloud AI services while maintaining full data sovereignty.

**Use Case:**
Deploy and serve LLMs that can execute skills from the [agentic-collections](../) repository via OpenCode, providing AI-powered automation in secure, regulated environments where data cannot leave the network perimeter.

---

## Validated Models

This guide includes complete, tested deployment procedures for the following models:

| Model | Size | GPUs | Key Strengths | Status |
|-------|------|------|---------------|--------|
| **Qwen 2.5 7B Instruct** | 7B | 1x H200 | Fast inference, code generation, multilingual | ✅ Validated |
| **Mixtral 8x7B Instruct** | 47B (13B active) | 1x H200 | MoE efficiency, excellent quality-to-speed ratio | ✅ Validated |
| **Mixtral 8x22B Instruct** | 141B (39B active) | 4x H200 | Advanced reasoning, 64K context, top-tier quality | ✅ Validated |

**All models feature:**
- 🔒 **Full precision** (no quantization) for perfect context retention
- 🛠️ **Tool calling support** via Hermes parser
- 💻 **OpenCode integration** with pre-configured profiles
- 📜 **Apache 2.0 license** (no approval required)
- 🚀 **vLLM serving** with OpenAI-compatible API

---

## Setup

### 1. Operators installation

Before deploying LLM models, install the required operators in the following order.

#### 1.1. Node Feature Discovery (NFD) Operator

**Check if installed:**
```bash
oc get csv -n openshift-nfd | grep nfd
```

**Expected output if installed:**
```
nfd.v4.XX.X   Node Feature Discovery   X.XX.X   Succeeded
```

:warning: **If you see the above output, the operator is already installed. Skip the installation commands below.**

**Install:**
```bash
oc apply -f manifests/nfd/namespace.yaml
oc apply -f manifests/nfd/operatorgroup.yaml
oc apply -f manifests/nfd/subscription.yaml
```

**Validate:**
```bash
oc wait --for=condition=Ready csv -n openshift-nfd -l operators.coreos.com/nfd.openshift-nfd --timeout=300s
```

**Initialize:**
```bash
oc apply -f manifests/nfd/nodefeaturediscovery.yaml
```

**Verify NFD is running:**
```bash
oc get pods -n openshift-nfd
oc get nodefeaturediscovery -n openshift-nfd
```

---

#### 1.2. NVIDIA GPU Operator

**Check if installed:**
```bash
oc get csv -n nvidia-gpu-operator | grep gpu-operator
```

**Expected output if installed:**
```
gpu-operator-certified.vXX.X.X   NVIDIA GPU Operator   XX.X.X   Succeeded
```

:warning: **If you see the above output, the operator is already installed. Skip the installation commands below.**

**Install:**
```bash
oc apply -f manifests/gpu-operator/namespace.yaml
oc apply -f manifests/gpu-operator/operatorgroup.yaml
oc apply -f manifests/gpu-operator/subscription.yaml
```

**Validate:**
```bash
oc wait --for=condition=Ready csv -n nvidia-gpu-operator -l operators.coreos.com/gpu-operator-certified.nvidia-gpu-operator --timeout=300s
```

**Initialize:**
```bash
oc apply -f manifests/gpu-operator/clusterpolicy.yaml
```

**Verify GPU operator is running:**
```bash
oc get pods -n nvidia-gpu-operator
oc get clusterpolicy
```

**Verify GPU nodes are labeled:**
```bash
oc get nodes -l feature.node.kubernetes.io/pci-10de.present=true
```

---

#### 1.3. Red Hat OpenShift AI Operator

**Check if installed:**
```bash
oc get csv -n redhat-ods-operator | grep rhods
```

**Expected output if installed:**
```
rhods-operator.vX.XX.X   Red Hat OpenShift AI   X.XX.X   Succeeded
```

:warning: **If you see the above output, the operator is already installed. Skip the installation commands below.**

**Install:**
```bash
oc apply -f manifests/openshift-ai/namespace.yaml
oc apply -f manifests/openshift-ai/operatorgroup.yaml
oc apply -f manifests/openshift-ai/subscription.yaml
```

**Validate:**
```bash
oc wait --for=condition=Ready csv -n redhat-ods-operator -l operators.coreos.com/rhods-operator.redhat-ods-operator --timeout=300s
```

**Initialize (Step 1 - DSCInitialization):**
```bash
oc apply -f manifests/openshift-ai/dscinitialization.yaml
```

**Verify DSCInitialization is created:**
```bash
oc get dscinitialization default-dsci
```

**Initialize (Step 2 - DataScienceCluster):**
```bash
oc apply -f manifests/openshift-ai/datasciencecluster.yaml
```

**Wait for DataScienceCluster to be ready:**
```bash
oc wait --for=condition=Ready datasciencecluster default-dsc --timeout=300s
```

**Verify OpenShift AI components:**
```bash
oc get pods -n redhat-ods-applications
```

---

### 2. Model Deployment

All LLM models are deployed to a shared namespace: `llm-models`

This approach allows you to:
- Store multiple models in a single PVC
- Reuse the same infrastructure for different models
- Simplify operations and reduce resource overhead

---

#### 2.1. Prepare Shared Model Storage (One-Time Setup)

**Create namespace and PVC:**
```bash
oc apply -f manifests/llm-models/namespace.yaml
oc apply -f manifests/llm-models/pvc.yaml
```

**Check PVC is created (will be Pending until a pod mounts it):**
```bash
oc get pvc -n llm-models
```

**Expected output:**
```
NAME              STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
models-storage    Pending                                      gp3-csi
```

**Create model-loader helper pod (this will trigger PVC binding):**
```bash
oc apply -f manifests/llm-models/model-loader-pod.yaml
```

**Wait for pod to be ready (this also ensures PVC is bound):**
```bash
oc wait --for=condition=Ready pod/model-loader -n llm-models --timeout=300s
```

**Verify both PVC and pod are ready:**
```bash
oc get pvc,pod -n llm-models
```

**Expected output:**
```
NAME                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/models-storage   Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   500Gi      RWO            gp3-csi

NAME               READY   STATUS    RESTARTS   AGE
pod/model-loader   1/1     Running   0          45s
```

The `model-loader` pod is now ready to receive models via `oc cp` command.

---

#### 2.2. Deploy Specific Models

Each model has specific download and deployment instructions. Choose your model from the table below:

| Model | Parameters | Architecture | Disk Size | GPUs | VRAM Required | Context Window | Download & Deploy Guide |
|-------|------------|--------------|-----------|------|---------------|----------------|-------------------------|
| **Qwen 2.5 7B Instruct** | 7B | Dense | ~15 GB | 1x H200 | ~14 GB | 32K | [📖 models/qwen-2.5-7b-instruct/README.md](./models/qwen-2.5-7b-instruct/README.md) |
| **Mixtral 8x7B Instruct** | 47B (13B active) | MoE | ~94 GB | 1x H200 | ~47 GB | 32K | [📖 models/mixtral-8x7b-instruct/README.md](./models/mixtral-8x7b-instruct/README.md) |
| **Mixtral 8x22B Instruct** | 141B (39B active) | MoE | ~280 GB | 4x H200 | ~131 GB | 64K | [📖 models/mixtral-8x22b-instruct/README.md](./models/mixtral-8x22b-instruct/README.md) |

**Model Selection Guide:**

- **Qwen 2.5 7B** - Best for: Code generation, math, multilingual tasks. Fastest inference, minimal GPU requirements.
- **Mixtral 8x7B** - Best for: OpenCode/agentic workflows, fast inference with strong quality. MoE architecture = 3-4x faster than dense models.
- **Mixtral 8x22B** - Best for: Advanced reasoning, complex tasks, long-context analysis. Top-tier quality with MoE efficiency.

**Key Features:**
- ✅ **No Quantization** - All models use full precision (FP16/auto) for perfect context retention
- ✅ **Tool Calling Support** - All models configured with `--enable-auto-tool-choice` and Hermes parser
- ✅ **OpenCode Compatible** - Pre-configured `opencode.json` files for AI-assisted development
- ✅ **Apache 2.0 License** - All models are fully open-source, no approval needed

**After loading a model**, verify the structure inside the PVC:
```bash
oc exec -n llm-models model-loader -- ls -lh /mnt/models/
```

**Expected structure** (example with multiple models):
```
total 0
drwxr-xr-x. Qwen/
  └── Qwen2.5-7B-Instruct/
drwxr-xr-x. Mixtral/
  ├── Mixtral-8x7B-Instruct-v0.1/
  └── Mixtral-8x22B-Instruct-v0.1/
```

**Storage Planning:**

| Models Deployed | Total Disk Space Required |
|-----------------|---------------------------|
| Qwen 2.5 7B only | ~20 GB |
| Qwen 2.5 7B + Mixtral 8x7B | ~120 GB |
| All three models | ~400 GB |

Recommended PVC size: **500 GB** (allows room for multiple models + future additions)

---

#### 2.3. Keep model-loader Running (Optional)

The `model-loader` pod can stay running if you plan to upload more models later.

**To delete it** (saves resources when not in use):
```bash
oc delete pod model-loader -n llm-models
```

**To recreate it later** (when you need to upload another model):
```bash
oc apply -f manifests/llm-models/model-loader-pod.yaml
oc wait --for=condition=Ready pod/model-loader -n llm-models --timeout=300s
```

---

**Previous versions and reference materials** are preserved in [`extra_docs/`](./extra_docs/) for reference.

---

**Version:** 2.2  
**Status:** Production-ready  
**Last Updated:** 2026-04-23  
**Validated Models:** Qwen 2.5 7B, Mixtral 8x7B, Mixtral 8x22B

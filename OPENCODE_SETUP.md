# OpenCode Setup Guide - OpenShift GPU Deployment

Complete guide for running OpenCode with Ollama on OpenShift with GPU acceleration.

**Last Updated**: 2026-03-13
**Status**: Production (Active)

---

## Table of Contents

1. [Context](#1-context)
2. [Tested Models](#2-tested-models)
3. [Deployment Guide](#3-deployment-guide)
4. [Architecture](#4-architecture)
5. [Optimization Configurations](#5-optimization-configurations)
6. [Troubleshooting](#6-troubleshooting)
7. [Verification & Testing](#7-verification--testing)
8. [Known Limitations](#8-known-limitations)
9. [Future Improvements](#9-future-improvements)

---

## 1. Context

### Environment Overview

**OpenShift Cluster:**
- Version: 4.20
- Platform: AWS (us-east-1a)
- API Endpoint: `https://api.cn-ai-lab.2vn8.p1.openshiftapps.com:6443`
- Kubeconfig: `~/work/redhat/projects/ai/ai5/agentic-collections/kubeconfig`

**GPU Node (Dedicated AI Workloads):**
- **Instance Type**: AWS g6.12xlarge
- **Node Name**: `ip-10-0-46-226.ec2.internal`
- **vCPUs**: 48 cores (Intel Xeon Skylake, 47.38 allocatable)
- **RAM**: 192GB total (176GB allocatable)
- **GPUs**: 4x NVIDIA L4 (23GB VRAM each = 92GB total)
- **Storage**: EBS gp3 (IOPS optimized)
- **Network**: 50 Gbps
- **Taints**: `ai-app=true:NoSchedule`, `ai-node=big:NoSchedule`

**Operators & Components:**
- **NVIDIA GPU Operator**: v24.x (deployed in `nvidia-gpu-operator` namespace)
- **Driver**: NVIDIA 580.105.08 (CUDA 13.0)
- **Ollama Runtime**: Latest container (`docker.io/ollama/ollama:latest`)
- **OpenCode Version**: Latest (AI coding agent)

### Deployment Details

**Namespace**: `open-code-model-runtime`

**Current Model**: Qwen2.5:72B-instruct-Q4_K_M
- Parameters: 72.7 billion
- Quantization: 4-bit (Q4_K_M)
- Size on disk: 47GB
- Size in memory: 176GB (requires CPU/RAM offloading)
- Context window: 16,384 tokens (~12,000 words)

**Ollama Endpoint**:
- Internal: `http://172.30.115.181:11434`
- External (Route): `https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com`
- OpenAI-compatible API: `/v1/chat/completions`

**Resource Allocation**:
```yaml
Resources (Ollama Pod):
  requests:
    cpu: 40 cores
    memory: 150Gi
    nvidia.com/gpu: 4
  limits:
    cpu: 45 cores
    memory: 170Gi
    nvidia.com/gpu: 4
```

**Storage**:
- PVC: `ollama-models` (persistent model storage)
- Storage Class: Default cluster storage class
- Mount: `/data/.ollama`

### Cost Considerations

- **g6.12xlarge**: ~$4.32/hour on-demand
- **Reserved instances**: ~$2.50-3.00/hour (1-year term)
- **Spot pricing**: ~$1.50-2.00/hour (variable availability)
- Maximizing node utilization justifies dedicated allocation

---

## 2. Tested Models

### Production Models (GPU-Accelerated)

#### ✅ Qwen2.5:72B-instruct-Q4_K_M (Current - Production)

**Model ID**: `qwen2.5:72b-instruct-q6_K`

**Performance**:
- First request (cold start): 3-5 minutes (model loading)
- Subsequent requests: 25-35 seconds (after optimizations)
- Model persistence: 24 hours in memory

**Resource Usage**:
- VRAM: ~3GB / 92GB (3% - bottleneck identified)
- RAM: 105GB (model offloading to CPU/RAM)
- CPU: 51% (due to offloading)
- GPU: 49% (should be higher)

**Characteristics**:
- ✅ Excellent reasoning and complex task handling
- ✅ Superior code generation quality
- ✅ Strong tool calling support
- ❌ Slower than desired (~20-25s per response)
- ❌ Model size exceeds VRAM (176GB > 92GB)

**Use Cases**:
- Complex skill evaluation
- Advanced reasoning tasks
- Multi-step code generation
- When quality is more important than speed

---

#### ⚠️ Qwen2.5:32B-instruct-Q4_K_M (Previous - Replaced)

**Model ID**: `qwen2.5:32b-instruct-q4_K_M`

**Performance**:
- Response time: 15-20 seconds
- Model size: 19GB (fits in VRAM)
- GPU utilization: ~80%

**Characteristics**:
- ✅ Good balance of speed and quality
- ✅ Fits entirely in VRAM
- ✅ Strong agentic capabilities
- ⚠️ Aggressive function calling (overuses tools)

**Reason for replacement**: Upgraded to 72B for better reasoning

---

#### ⚠️ Mistral-NeMo:12B-instruct-2407-Q4_K_M (T4 Era - Deprecated)

**Model ID**: `mistral-nemo:12b-instruct-2407-q4_K_M`

**Performance** (on old T4 GPU):
- Response time: 12-15 seconds
- Model size: 7.5GB
- GPU utilization: 100%

**Characteristics**:
- ✅ Conservative function calling (not overly aggressive)
- ✅ Good for skill validation
- ✅ 128k context window
- ❌ Smaller model, less capable than Qwen 72B

**Reason for deprecation**: Upgraded GPU node (T4 → 4x L4)

---

### Candidate Models (Not Yet Deployed)

#### 🔥 Qwen2.5:72B-instruct-Q3_K_M (Recommended Next)

**Model ID**: `qwen2.5:72b-instruct-q3_K_M`

**Expected Performance**:
- Response time: 5-10 seconds (100% GPU)
- Model size: ~35GB (fits in 92GB VRAM)
- GPU utilization: 100% (no CPU offloading)

**Characteristics**:
- ✅ **10x faster** than current Q4_K_M
- ✅ Fits entirely in VRAM
- ✅ ~95% quality of Q4 (3-6% loss, imperceptible for code)
- ✅ Same 72B parameter base model

**Trade-off**: Slightly lower precision (3-bit vs 4-bit quantization)

**Status**: Ready to deploy (see Section 9)

---

#### 🎯 Qwen2.5:32B-instruct-Q8_0 (High Quality Alternative)

**Model ID**: `qwen2.5:32b-instruct-q8_0`

**Expected Performance**:
- Response time: 8-12 seconds
- Model size: ~35GB
- GPU utilization: 100%

**Characteristics**:
- ✅ Higher quantization (8-bit, better quality than Q4)
- ✅ Fits in VRAM
- ⚠️ Smaller model (32B vs 72B parameters)

**Use Case**: When quality > model size, but need speed

---

### CPU-Only Models (Local Development - Not on Cluster)

These were tested during initial local development (before GPU deployment):

#### Qwen2.5-Coder:3B-instruct
- **Response time**: 15-30 seconds (CPU: 22 vCPUs, 62GB RAM)
- **Model size**: 1.9GB
- **Use case**: Interactive development on CPU-only systems
- **Quality**: ⭐⭐⭐ (acceptable for simple tasks)

#### Qwen2.5-Coder:7B-instruct
- **Response time**: 60-120 seconds (CPU)
- **Model size**: 4.7GB
- **Use case**: Code review, documentation (batch processing)
- **Quality**: ⭐⭐⭐⭐ (good)
- **Limitation**: Too slow for interactive use on CPU

#### Qwen2.5-Coder:14B
- **Response time**: 2-5 minutes (CPU)
- **Model size**: 9GB
- **Use case**: Batch processing only
- **Quality**: ⭐⭐⭐⭐⭐ (excellent)
- **Limitation**: Impractical for interactive workflows

**Key Learning**: CPU inference is memory-bandwidth limited. GPU acceleration is mandatory for models >7B for interactive use.

---

### Model Selection Criteria

**For GPU deployment, always ensure**:
1. ✅ Model has `-instruct` suffix (function calling support required)
2. ✅ Model fits in available VRAM OR acceptable offloading performance
3. ✅ Context window ≥16k tokens (OpenCode requires 10k-15k)
4. ✅ Tool calling support verified

**Error signatures to avoid**:
```
registry.ollama.ai/library/model-name does not support tools
# Cause: Base model without -instruct variant
```

---

## 3. Deployment Guide

### Prerequisites

1. **OpenShift Cluster Access**:
   ```bash
   oc login https://api.cn-ai-lab.2vn8.p1.openshiftapps.com:6443
   oc whoami  # Verify authentication
   ```

2. **GPU Node Available**:
   ```bash
   # Verify GPU node exists
   oc get nodes -l node.kubernetes.io/instance-type=g6.12xlarge

   # Should output: ip-10-0-46-226.ec2.internal
   ```

3. **NVIDIA GPU Operator Installed**:
   ```bash
   oc get pods -n nvidia-gpu-operator

   # Should show running gpu-operator and driver daemonsets
   ```

4. **Namespace Created**:
   ```bash
   oc new-project open-code-model-runtime
   # OR
   oc project open-code-model-runtime
   ```

---

### Step 1: Configure GPU Operator for AI Node

The GPU operator must tolerate the AI node taints:

```bash
oc patch clusterpolicy gpu-cluster-policy -n nvidia-gpu-operator --type='json' -p='[
  {
    "op": "add",
    "path": "/spec/daemonsets/tolerations/-",
    "value": {
      "effect": "NoSchedule",
      "key": "ai-app",
      "operator": "Equal",
      "value": "true"
    }
  },
  {
    "op": "add",
    "path": "/spec/daemonsets/tolerations/-",
    "value": {
      "effect": "NoSchedule",
      "key": "ai-node",
      "operator": "Equal",
      "value": "big"
    }
  }
]'
```

**Verify GPU drivers deployed**:
```bash
oc get pods -n nvidia-gpu-operator -o wide | grep ip-10-0-46-226

# Should show:
# - nvidia-driver-daemonset-xxx (Running)
# - nvidia-device-plugin-daemonset-xxx (Running)
# - nvidia-container-toolkit-daemonset-xxx (Running)
```

---

### Step 2: Create Persistent Volume for Models

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ollama-models
  namespace: open-code-model-runtime
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
EOF
```

---

### Step 3: Create Service Account

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ollama
  namespace: open-code-model-runtime
EOF
```

---

### Step 4: Deploy Ollama with GPU Support

```bash
cat <<EOF | oc apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: open-code-model-runtime
  labels:
    app: ollama
    project: ai5
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: ollama
      project: ai5
  template:
    metadata:
      labels:
        app: ollama
        project: ai5
    spec:
      serviceAccountName: ollama
      nodeSelector:
        node.kubernetes.io/instance-type: g6.12xlarge
      tolerations:
        - key: ai-app
          operator: Equal
          value: "true"
          effect: NoSchedule
        - key: ai-node
          operator: Equal
          value: big
          effect: NoSchedule
      initContainers:
        - name: model-loader
          image: docker.io/ollama/ollama:latest
          command:
            - /bin/sh
            - -c
            - |
              echo "Starting Ollama server in background..."
              ollama serve &
              SERVER_PID=\$!

              echo "Waiting for Ollama to be ready..."
              until ollama list > /dev/null 2>&1; do
                sleep 2
              done

              echo "Pulling model: qwen2.5-coder:14b-instruct..."
              ollama pull qwen2.5-coder:14b-instruct

              echo "Model loaded successfully!"
              ollama list

              echo "Stopping Ollama server..."
              kill \$SERVER_PID
              wait \$SERVER_PID || true

              echo "Init container complete."
          env:
            - name: HOME
              value: /data
          volumeMounts:
            - name: models
              mountPath: /data/.ollama
          resources:
            requests:
              cpu: "12"
              memory: 48Gi
              nvidia.com/gpu: "4"
            limits:
              cpu: "16"
              memory: 64Gi
              nvidia.com/gpu: "4"
          securityContext:
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            seccompProfile:
              type: RuntimeDefault
            capabilities:
              drop:
                - ALL
      containers:
        - name: ollama
          image: docker.io/ollama/ollama:latest
          ports:
            - containerPort: 11434
              name: http
              protocol: TCP
          env:
            - name: OLLAMA_HOST
              value: "0.0.0.0:11434"
            - name: OLLAMA_ORIGINS
              value: "*"
            - name: OLLAMA_NUM_PARALLEL
              value: "1"
            - name: OLLAMA_MAX_LOADED_MODELS
              value: "1"
            - name: OLLAMA_KEEP_ALIVE
              value: "24h"
            - name: HOME
              value: /data
            - name: OLLAMA_NUM_GPU
              value: "999"
            - name: OLLAMA_GPU_OVERHEAD
              value: "0"
            - name: OLLAMA_FLASH_ATTENTION
              value: "1"
            - name: OLLAMA_CONTEXT_LENGTH
              value: "16384"
            - name: OLLAMA_MULTIUSER_CACHE
              value: "false"
            - name: OLLAMA_NOPRUNE
              value: "true"
          volumeMounts:
            - name: models
              mountPath: /data/.ollama
          resources:
            requests:
              cpu: "40"
              memory: 150Gi
              nvidia.com/gpu: "4"
            limits:
              cpu: "45"
              memory: 170Gi
              nvidia.com/gpu: "4"
          livenessProbe:
            httpGet:
              path: /
              port: 11434
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /
              port: 11434
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          securityContext:
            allowPrivilegeEscalation: false
            runAsNonRoot: true
            seccompProfile:
              type: RuntimeDefault
            capabilities:
              drop:
                - ALL
      volumes:
        - name: models
          persistentVolumeClaim:
            claimName: ollama-models
EOF
```

**Note**: Init container pre-loads a smaller model (14B) for faster first startup. You'll load the 72B model separately.

---

### Step 5: Create Service

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: open-code-model-runtime
spec:
  selector:
    app: ollama
    project: ai5
  ports:
    - name: http
      protocol: TCP
      port: 11434
      targetPort: 11434
  type: ClusterIP
EOF
```

---

### Step 6: Create Route (External Access)

```bash
cat <<EOF | oc apply -f -
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: ollama
  namespace: open-code-model-runtime
spec:
  to:
    kind: Service
    name: ollama
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
EOF
```

**Get route URL**:
```bash
oc get route ollama -n open-code-model-runtime -o jsonpath='{.spec.host}'
# Output: ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com
```

---

### Step 7: Load Production Model (Qwen2.5:72B)

Wait for deployment to be ready:
```bash
oc rollout status deployment/ollama -n open-code-model-runtime
```

Download the 72B model:
```bash
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama pull qwen2.5:72b-instruct-q6_K
```

**Expected time**: 8-12 minutes (~47GB download)

---

### Step 8: Configure OpenCode

Create or update `~/work/redhat/projects/ai/ai5/agentic-collections/opencode.json`:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama-ocp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama on OpenShift (4x NVIDIA L4 GPUs)",
      "options": {
        "baseURL": "https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/v1"
      },
      "models": {
        "qwen2.5:72b-instruct-q6_K": {
          "name": "Qwen 2.5 72B Instruct (Q6_K - Maximum Quality)",
          "description": "Most capable model with superior reasoning and agentic capabilities. 72.7B parameters, Q6_K quantization (6-bit precision), 128k context window. Superior accuracy for skill execution, MCP server integration, and multi-step workflows. Optimized for precision over speed. Runs on 4x NVIDIA L4 GPUs (92GB VRAM total, 176GB in memory with offloading). First request: ~3-5min (model load), subsequent: ~25-35s. Model stays loaded for 24h. Best for complex skill evaluation, advanced MCP workflows, and challenging reasoning tasks.",
          "options": {
            "numCtx": 131072,
            "maxTokens": 126976,
            "temperature": 0.3,
            "topP": 0.85,
            "topK": 20,
            "repeatPenalty": 1.05
          }
        },
        "qwen2.5:72b-instruct-q4_K_M": {
          "name": "Qwen 2.5 72B Instruct (Q4_K_M - Balanced)",
          "description": "Balanced model with good reasoning and agentic capabilities. 72.7B parameters, Q4_K_M quantization, 128k context window. Response time: ~18-25s. Alternative option when speed matters more than precision. Runs on 4x NVIDIA L4 GPUs (92GB VRAM total, 176GB in memory with offloading).",
          "options": {
            "numCtx": 131072,
            "maxTokens": 126976,
            "temperature": 0.3,
            "topP": 0.85,
            "topK": 20,
            "repeatPenalty": 1.05
          }
        },
        "qwen2.5:32b-instruct-q4_K_M": {
          "name": "Qwen 2.5 32B Instruct",
          "description": "Advanced quality model with excellent agentic capabilities. 32B parameters, Q4_K_M quantization, 128k context window. Strong tool use, reasoning, and multi-step task handling. Runs on 4x L4 GPUs (19GB model size, fully in VRAM). First request: ~2min (model load), subsequent: ~15-20s. Model stays loaded for 24h. Good balance of capability and performance.",
          "options": {
            "numCtx": 131072,
            "maxTokens": 126976,
            "temperature": 0.3
          }
        },
        "qwen2.5-coder:14b-instruct": {
          "name": "Qwen 2.5 Coder 14B Instruct",
          "description": "Code-specialized model with strong programming capabilities. 14B parameters, 128k context window. Pre-loaded with deployment, optimized for code generation, debugging, and technical tasks. Runs on 4x L4 GPUs (9GB model size, fully in VRAM). First request: ~1min (model load), subsequent: ~8-12s. Best for code-focused workflows and rapid iteration.",
          "options": {
            "numCtx": 131072,
            "maxTokens": 126976,
            "temperature": 0.3
          }
        },
        "mistral-nemo:12b-instruct-2407-q4_K_M": {
          "name": "Mistral NeMo 12B Instruct",
          "description": "Balanced quality model with excellent function calling support. 12B parameters, Q4_K_M quantization, 128k context window. Less aggressive with function calling than Qwen - uses tools intelligently. Runs on 4x L4 GPUs (7.5GB model size, fully in VRAM). First request: ~1min (model load), subsequent: ~8-10s. Best for skill validation with reasonable function calling behavior.",
          "options": {
            "numCtx": 131072,
            "maxTokens": 126976,
            "temperature": 0.8
          }
        }
      }
    }
  },
  "model": "ollama-ocp/qwen2.5:72b-instruct-q6_K"
}
```
```

---

### Step 9: Configure MCP Servers (Optional)

For OpenShift Virtualization integration, create project-level configuration:

**File**: `rh-virt/opencode.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "openshift-virtualization": {
      "type": "local",
      "command": [
        "podman",
        "run",
        "--rm",
        "-i",
        "--network=host",
        "--userns=keep-id:uid=65532,gid=65532",
        "-v",
        "/home/avillega/work/redhat/projects/ai/ai5/agentic-collections/kubeconfig:/kubeconfig:ro,Z",
        "--entrypoint",
        "/app/kubernetes-mcp-server",
        "quay.io/ecosystem-appeng/openshift-mcp-server:latest",
        "--kubeconfig",
        "/kubeconfig",
        "--toolsets",
        "core,kubevirt"
      ],
      "environment": {
        "KUBECONFIG": "/home/avillega/work/redhat/projects/ai/ai5/agentic-collections/kubeconfig"
      },
      "enabled": true,
      "timeout": 300000
    }
  }
}
```

**Prerequisites**:
```bash
# Export KUBECONFIG (add to ~/.bashrc)
export KUBECONFIG=~/work/redhat/projects/ai/ai5/agentic-collections/kubeconfig

# Verify access
oc whoami
```

**Usage**:
```bash
cd ~/work/redhat/projects/ai/ai5/agentic-collections/rh-virt
opencode  # Loads local opencode.json with MCP server
```

---

## 4. Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenShift Cluster                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Namespace: open-code-model-runtime                   │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │ Deployment: ollama (1 replica)               │    │  │
│  │  │                                                │    │  │
│  │  │  Init Container: model-loader                │    │  │
│  │  │    - Pre-loads qwen2.5-coder:14b-instruct    │    │  │
│  │  │    - Resources: 4 GPUs, 12-16 CPU, 48-64GB   │    │  │
│  │  │                                                │    │  │
│  │  │  Main Container: ollama                       │    │  │
│  │  │    - Runs Ollama server                       │    │  │
│  │  │    - Loads qwen2.5:72b-instruct-q6_K       │    │  │
│  │  │    - Resources: 4 GPUs, 40-45 CPU, 150-170GB │    │  │
│  │  │    - Port: 11434                              │    │  │
│  │  │                                                │    │  │
│  │  │  Volume: ollama-models (PVC)                  │    │  │
│  │  │    - 100Gi persistent storage                 │    │  │
│  │  │    - Stores model files                       │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  │                         ▲                             │  │
│  │                         │                             │  │
│  │  ┌──────────────────────┴──────────────────────┐    │  │
│  │  │ Service: ollama (ClusterIP)                  │    │  │
│  │  │   - IP: 172.30.115.181                        │    │  │
│  │  │   - Port: 11434                               │    │  │
│  │  └──────────────────────┬──────────────────────┘    │  │
│  │                         │                             │  │
│  │  ┌──────────────────────┴──────────────────────┐    │  │
│  │  │ Route: ollama (TLS edge termination)         │    │  │
│  │  │   - Host: ollama.apps.cn-ai-lab...           │    │  │
│  │  │   - HTTPS external access                     │    │  │
│  │  └──────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Namespace: nvidia-gpu-operator                       │  │
│  │                                                        │  │
│  │  DaemonSets (on GPU node):                            │  │
│  │    - nvidia-driver-daemonset                          │  │
│  │    - nvidia-device-plugin-daemonset                   │  │
│  │    - nvidia-container-toolkit-daemonset               │  │
│  │    - gpu-feature-discovery                            │  │
│  │                                                        │  │
│  │  Tolerations:                                          │  │
│  │    - ai-app=true:NoSchedule                           │  │
│  │    - ai-node=big:NoSchedule                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Node: ip-10-0-46-226.ec2.internal                    │  │
│  │  Instance Type: g6.12xlarge                            │  │
│  │                                                        │  │
│  │  Hardware:                                             │  │
│  │    - 48 vCPUs (Intel Xeon Skylake)                    │  │
│  │    - 192GB RAM                                         │  │
│  │    - 4x NVIDIA L4 GPUs (23GB VRAM each)               │  │
│  │                                                        │  │
│  │  Taints:                                               │  │
│  │    - ai-app=true:NoSchedule                           │  │
│  │    - ai-node=big:NoSchedule                           │  │
│  │                                                        │  │
│  │  Labels:                                               │  │
│  │    - node.kubernetes.io/instance-type=g6.12xlarge     │  │
│  │    - nvidia.com/gpu.present=true                      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

                            │
                            ▼
                  ┌───────────────────┐
                  │  OpenCode Client  │
                  │  (Local Workstation)│
                  │                   │
                  │  Endpoint:        │
                  │  https://ollama...│
                  │  /v1/chat/...     │
                  └───────────────────┘
```

### Data Flow

1. **Model Loading** (Init Container):
   - Downloads model from registry.ollama.ai
   - Stores in PVC (`/data/.ollama/models`)
   - Validates model integrity
   - Exits cleanly

2. **Inference Request**:
   ```
   OpenCode → HTTPS Route → Service → Ollama Pod → GPU Computation → Response
   ```

3. **GPU Allocation**:
   - Kubernetes schedules pod to GPU node (nodeSelector)
   - NVIDIA device plugin allocates 4 GPUs to container
   - Ollama runtime detects GPUs via CUDA
   - Model layers distributed across GPUs + RAM (due to size)

4. **Model Persistence**:
   - Model stays loaded in memory for 24 hours (`OLLAMA_KEEP_ALIVE=24h`)
   - After 24h of inactivity, model unloads automatically
   - Next request triggers reload (~3-5 min)

---

### Network Architecture

**Internal Communication**:
- Service: `ollama.open-code-model-runtime.svc.cluster.local:11434`
- ClusterIP: `172.30.115.181:11434`

**External Access**:
- Route: `https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com`
- TLS: Edge termination (OpenShift router handles SSL)
- Protocol: HTTPS (external) → HTTP (internal to service)

**API Endpoints**:
- Native Ollama API: `/api/generate`, `/api/chat`, `/api/tags`
- OpenAI-compatible API: `/v1/chat/completions`, `/v1/models`
- OpenCode uses: `/v1` prefix (OpenAI-compatible)

---

### Storage Architecture

**PersistentVolumeClaim**:
- Name: `ollama-models`
- Size: 100Gi
- Access Mode: ReadWriteOnce (RWO)
- Storage Class: Default cluster storage (EBS gp3)

**Mount Points**:
- Container path: `/data/.ollama`
- Model storage: `/data/.ollama/models/`
- Manifest cache: `/data/.ollama/manifests/`

**Disk Usage** (Typical):
- qwen2.5:72b-instruct-q6_K: 47GB
- qwen2.5:32b-instruct-q4_K_M: 19GB
- qwen2.5-coder:14b-instruct: 9GB
- mistral-nemo:12b-instruct: 7.5GB
- Overhead: ~2-3GB
- **Total**: ~85GB / 100GB

---

## 5. Optimization Configurations

### Applied Optimizations\n\n**Initial optimizations**: 2026-03-12 (performance tuning)\n**Latest update**: 2026-03-12 (context window \u0026 client configuration)

#### Environment Variables

| Variable | Value | Purpose | Impact |
|----------|-------|---------|--------|
| **OLLAMA_NUM_GPU** | `999` | Use all available GPUs | Enables 4-GPU utilization |
| **OLLAMA_GPU_OVERHEAD** | `0` | Minimize GPU memory overhead | More VRAM for model |
| **OLLAMA_KEEP_ALIVE** | `24h` | Keep model loaded | Avoid reload penalty |
| **OLLAMA_MAX_LOADED_MODELS** | `1` | Single model in memory | Maximize resources per model |
| **OLLAMA_FLASH_ATTENTION** | `1` | Optimized attention mechanism | ~15-20% faster |
| **OLLAMA_NUM_PARALLEL** | `1` | Single request processing | ~25-30% faster per request |
| **OLLAMA_CONTEXT_LENGTH** | `131072` | 128k token context (~98,000 words) | Maximum capacity for very long complex tasks |
| **OLLAMA_MULTIUSER_CACHE** | `false` | Disable multi-user cache | ~2-5% faster |
| **OLLAMA_NOPRUNE** | `true` | Prevent model pruning | ~2-5% faster |
| **OLLAMA_HOST** | `0.0.0.0:11434` | Listen on all interfaces | Network accessibility |
| **OLLAMA_ORIGINS** | `*` | Allow all origins (CORS) | OpenCode compatibility |

**Complete configuration**:
```bash
oc set env deployment/ollama -n open-code-model-runtime \
  OLLAMA_HOST=0.0.0.0:11434 \
  OLLAMA_ORIGINS='*' \
  OLLAMA_NUM_PARALLEL=1 \
  OLLAMA_MAX_LOADED_MODELS=1 \
  OLLAMA_KEEP_ALIVE=24h \
  OLLAMA_NUM_GPU=999 \
  OLLAMA_GPU_OVERHEAD=0 \
  OLLAMA_FLASH_ATTENTION=1 \
  OLLAMA_CONTEXT_LENGTH=131072 \
  OLLAMA_MULTIUSER_CACHE=false \
  OLLAMA_NOPRUNE=true
```

---

#### Resource Allocation

**Current (Optimized)**:
```yaml
resources:
  requests:
    cpu: "40"          # 83% of 48 vCPUs
    memory: "150Gi"    # 85% of 176GB allocatable
    nvidia.com/gpu: "4"
  limits:
    cpu: "45"          # 94% of 48 vCPUs
    memory: "170Gi"    # 97% of 176GB allocatable
    nvidia.com/gpu: "4"
```

**Rationale**:
- Node is dedicated to AI workloads (taints prevent other workloads)
- Model requires CPU/RAM offloading (176GB model > 92GB VRAM)
- More CPU = faster matrix operations during offloading
- More RAM = more model layers cached
- Leaves 3-8 vCPUs and 6-26GB for system processes

**Applied command**:
```bash
oc set resources deployment/ollama -n open-code-model-runtime \
  --limits=cpu=45,memory=170Gi,nvidia.com/gpu=4 \
  --requests=cpu=40,memory=150Gi,nvidia.com/gpu=4
```

---

#### Performance Impact

| Metric | Before Optimization | After Optimization | Improvement |
|--------|--------------------|--------------------|-------------|
| **Response time** | 30-45s → 18-25s | 25-35s | **Optimized for precision** |
| **CPU allocation** | 12-16 cores | 40-45 cores | +250% resources |
| **RAM allocation** | 96-128GB | 150-170GB | +33% resources |
| **Context window** | 16k tokens → 32k → 128k | 128k tokens | Maximum |
| **Concurrent requests** | 4 parallel | 1 sequential | Trade-off |
| **Model persistence** | 24h | 24h | No change |

---

#### Trade-offs

**✅ Gains**:
- Faster individual response times (~40% improvement)
- Better resource utilization (83-97% node capacity)
- More model layers cached in RAM
- Optimized attention mechanism (Flash Attention)

**⚠️ Trade-offs**:
- Reduced concurrent request handling (4→1)
  - **Acceptable**: OpenCode sends 1 request at a time (single-user)
- Optimized context window (32k tokens)
  - **Acceptable**: 32k = ~24,000 words (~48 pages), handles complex multi-step skill workflows
  - Typical OpenCode prompts: 500-2000 tokens
- Dedicated node resources
  - **Acceptable**: Node is tainted for AI workloads only

---

### Configuration Rationale

#### Context Length (131,072 tokens = 128k)

**Why 128k context (maximum)?**
- Very long complex tasks: 50k-100k+ tokens
  - Tool schemas: 2k-5k tokens
  - Skill definitions: 3k-8k tokens
  - File context: 10k-30k tokens
  - Conversation history: 10k-50k+ tokens
  - Multi-step orchestration: Can span 50+ exchanges
- 128k tokens = ~98,000 words = ~196 pages of text
- **Essential for extended workflows** with multiple skills and deep context
- Prevents context loss even in marathon sessions
- Enables codebase-level understanding

**Evolution**:
- Initially: 16k tokens (caused truncation)
- First update: 32k tokens (fixed basic context loss)
- **Current: 128k tokens (maximum model capacity)**

**Context size comparison**:

| Tokens | Words | Pages | Use Case |
|--------|-------|-------|----------|
| 8k | 6,000 | 12 | Basic tasks (too small) |
| 16k | 12,000 | 24 | Simple conversations |
| 32k | 24,000 | 48 | Complex workflows |
| 64k | 48,000 | 96 | Very large workflows |
| **128k (current)** | **98,000** | **196** | **Maximum - Extended complex tasks** |

**Trade-off**: Significant memory increase (~40-50GB additional RAM for 128k vs 32k)
- Current allocation: 170GB RAM → Plenty of headroom
- Performance: +5-10s per response (acceptable for complex tasks)

**When to use 128k**:
- ✅ Multi-skill orchestration (10+ skill invocations)
- ✅ Large file analysis (multiple modules, configs)
- ✅ Extended debugging sessions (50+ message exchanges)
- ✅ Codebase understanding (reviewing related files)
- ✅ Complex MCP workflows with deep tool call chains

---

#### OpenCode Client Configuration

**Critical optimization**: Model sampling parameters configured in `opencode.json`

**Purpose**:
- Prevents aggressive tool calling (respects human-in-the-loop)
- Maintains context window awareness
- Balances creativity vs determinism
- Improves conversation quality

**Configuration** (`opencode.json`):
```json
{
  "provider": {
    "ollama-ocp": {
      "models": {
        "qwen2.5:72b-instruct-q6_K": {
          "options": {
            "numCtx": 131072,        // 128k context window (matches server)
            "maxTokens": 126976,     // Max output tokens
            "temperature": 0.3,     // Balanced creativity (0.0=deterministic, 1.0=creative)
            "topP": 0.85,           // Nucleus sampling (quality control)
            "topK": 20,            // Top-k sampling (diversity)
            "repeatPenalty": 1.05   // Prevent repetition
          }
        }
      }
    }
  }
}
```

**Parameter explanations**:
- **numCtx**: Must match `OLLAMA_CONTEXT_LENGTH` server setting
- **maxTokens**: Maximum output length (reserve ~2k for overhead)
- **temperature**: 0.7 is balanced (lower = more focused, higher = more creative)
- **topP/topK**: Quality and diversity controls
- **repeatPenalty**: Reduces repetitive outputs

**Impact**:
- ✅ Fixed: Context loss during long conversations
- ✅ Fixed: Model skipping human-in-the-loop confirmations
- ✅ Improved: Response quality and coherence

**Before this optimization**:
- Model would "forget" earlier context after 10-15 exchanges
- Skipped interactive confirmation prompts from skills
- Aggressive tool calling without waiting for user input

**After this optimization**:
- Maintains context for 30+ exchanges
- Respects skill confirmation requests
- Better balanced tool use

---

#### Parallel Requests (1)

**Why single request instead of 4?**
- OpenCode sends 1 request at a time (sequential, not concurrent)
- Single-user development environment (not production multi-user API)
- Dedicating all resources to 1 request → faster response
- Can increase to 2-4 if concurrent use cases emerge

**Performance gain**: ~25-30% faster per individual request

---

#### Flash Attention

**What is Flash Attention?**
- Optimized attention mechanism for transformer models
- Reduces memory usage during inference
- Faster computation on GPU
- Enabled via `OLLAMA_FLASH_ATTENTION=1`

**Impact**: ~15-20% speedup on long contexts

---

#### No Resource Limits (Container Runtime)

**Critical Learning** (from CPU testing):
- Docker/Podman `--cpus` and `--memory` limits cause deadlocks with llama.cpp
- Ollama uses llama.cpp internally with its own CPU scheduling
- Container resource limits conflict with llama.cpp thread pool
- **Solution**: Let Kubernetes manage limits (via pod spec), not container runtime

**Symptoms if limits applied**:
- Infinite text generation without termination
- `ollama_runner` processes stuck at 100% CPU
- API requests never complete
- Thread contention and deadlocks

**Correct approach**:
```yaml
# Kubernetes pod resource limits (CORRECT)
resources:
  limits:
    cpu: "45"
    memory: "170Gi"
```

```bash
# Container runtime limits (WRONG - causes deadlocks)
podman run --cpus="16" --memory="32g" ollama/ollama  # DON'T DO THIS
```

---

### Optimization History

| Date | Change | Impact |
|------|--------|--------|
| 2026-03-06 | Initial deployment (T4 GPU, Mistral 12B) | Baseline |
| 2026-03-11 | Upgrade to g6.12xlarge (4x L4), Qwen 72B | 4x GPU capacity |
| 2026-03-12 | Add GPU operator tolerations | GPU drivers deployed |
| 2026-03-12 | Increase resources (40-45 CPU, 150-170GB RAM) | +250% CPU, +33% RAM |
| 2026-03-12 | Enable Flash Attention, reduce parallel requests | ~40% faster responses |
| 2026-03-12 | Reduce context 32k→16k | Frees 4-6GB VRAM |

---

## 6. Troubleshooting

### Performance Issues

#### Slow Response Times (>30 seconds)

**Symptoms**:
- Responses taking 30-45+ seconds
- Model showing 51% CPU / 49% GPU split
- Low VRAM usage (~2-3GB of 92GB)

**Diagnosis**:
```bash
# Check model status
oc exec -n open-code-model-runtime deployment/ollama -- ollama ps

# Look for CPU/GPU split
# GOOD: 0%/100% or 10%/90% CPU/GPU
# BAD: 50%/50% or 51%/49% CPU/GPU (offloading)

# Check GPU memory
oc exec -n open-code-model-runtime deployment/ollama -- \
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

**Root Cause**: Model size (176GB) exceeds VRAM (92GB), causing CPU/RAM offloading

**Solutions**:
1. **Short-term**: Already applied optimizations (~40% improvement)
2. **Long-term**: Switch to Q3_K_M model (see Section 9)

---

#### First Request Very Slow (~3-5 minutes)

**Symptom**: First request of the day takes 3-5 minutes

**Cause**: Model loading from disk to GPU/RAM

**Expected Behavior**: This is normal
- Model unloads after 24h of inactivity (`OLLAMA_KEEP_ALIVE=24h`)
- First request triggers reload
- Subsequent requests: ~18-25 seconds (model stays loaded)

**Pre-warm model**:
```bash
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q6_K "Hello"
```

---

### Model Issues

#### "does not support tools" Error

**Error message**:
```
registry.ollama.ai/library/model-name does not support tools
```

**Root Cause**: Model lacks function calling capability (not an `-instruct` variant)

**Resolution**:
1. Verify model name:
   ```bash
   oc exec -n open-code-model-runtime deployment/ollama -- ollama list
   ```
2. Ensure model has `-instruct` suffix
3. Download correct variant:
   ```bash
   oc exec -n open-code-model-runtime deployment/ollama -- \
     ollama pull qwen2.5-coder:14b-instruct
   ```

**Valid models**:
- ✅ `qwen2.5:72b-instruct-q6_K`
- ✅ `qwen2.5-coder:14b-instruct`
- ❌ `qwen2.5-coder:14b` (missing -instruct)

---

#### Context Truncation Warning

**Symptom**:
```
truncating input prompt limit=16384 prompt=18234
```

**Impact**:
- Tool calling schemas get cut off
- Model generates invalid JSON
- Requests may fail or loop infinitely

**Resolution**:
Increase context length (if needed):
```bash
oc set env deployment/ollama -n open-code-model-runtime \
  OLLAMA_CONTEXT_LENGTH=131072

# Wait for rollout
oc rollout status deployment/ollama -n open-code-model-runtime
```

**Trade-off**: More VRAM usage (~+4-6GB for 32k vs 16k)

**Monitor**:
```bash
oc logs -n open-code-model-runtime deployment/ollama --tail=50 | grep truncating
```

---

#### Model Download Fails

**Symptoms**:
- Init container stuck or failing
- `ollama pull` times out
- Network errors

**Diagnosis**:
```bash
# Check init container logs
oc logs -n open-code-model-runtime <pod-name> -c model-loader

# Check for network issues
oc exec -n open-code-model-runtime deployment/ollama -- \
  curl -I https://registry.ollama.ai
```

**Common causes**:
1. **Network connectivity**: Verify cluster egress
2. **Storage full**: Check PVC capacity
3. **Timeout**: Large models take 8-15 minutes to download

**Resolution**:
```bash
# Check PVC usage
oc exec -n open-code-model-runtime deployment/ollama -- df -h /data/.ollama

# Increase timeout if needed (in deployment spec)
terminationGracePeriodSeconds: 600
```

---

### GPU Issues

#### GPUs Not Detected

**Symptom**:
```bash
oc exec -n open-code-model-runtime deployment/ollama -- nvidia-smi
# Output: command not found OR no GPUs found
```

**Diagnosis**:
```bash
# Check GPU operator pods
oc get pods -n nvidia-gpu-operator -o wide

# Verify driver on GPU node
oc get pods -n nvidia-gpu-operator -o wide | grep ip-10-0-46-226

# Should show Running:
# - nvidia-driver-daemonset-xxx
# - nvidia-device-plugin-daemonset-xxx
```

**Common causes**:
1. **Driver not deployed**: GPU operator missing tolerations
2. **Node taints blocking**: Driver daemonset can't schedule

**Resolution**:
```bash
# Add tolerations to GPU operator (see Section 3, Step 1)
oc patch clusterpolicy gpu-cluster-policy -n nvidia-gpu-operator ...

# Verify drivers running
oc get daemonset -n nvidia-gpu-operator
```

---

#### GPU Memory Errors (OOM)

**Symptom**:
```
CUDA out of memory
```

**Cause**: Model + context exceeds VRAM

**Diagnosis**:
```bash
oc exec -n open-code-model-runtime deployment/ollama -- \
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv
```

**Solutions**:
1. Reduce context window: `OLLAMA_CONTEXT_LENGTH=8192`
2. Switch to smaller model: 32B or 14B
3. Reduce parallel requests: `OLLAMA_NUM_PARALLEL=1` (already set)

---

### Deployment Issues

#### Pod Stuck in Pending

**Symptom**:
```bash
oc get pods -n open-code-model-runtime
# NAME                     READY   STATUS    RESTARTS   AGE
# ollama-xxx-yyy           0/1     Pending   0          5m
```

**Diagnosis**:
```bash
oc describe pod <pod-name> -n open-code-model-runtime | grep -A 10 Events
```

**Common causes**:

1. **Insufficient GPU resources**:
   ```
   0/12 nodes available: ... Insufficient nvidia.com/gpu
   ```
   **Solution**: Check if another pod is using the GPUs
   ```bash
   oc get pods -A -o json | jq '.items[] | select(.spec.containers[].resources.limits."nvidia.com/gpu" != null) | {name: .metadata.name, namespace: .metadata.namespace, gpus: .spec.containers[].resources.limits."nvidia.com/gpu"}'
   ```

2. **Node selector mismatch**:
   ```
   0/12 nodes available: ... didn't match Pod's node affinity/selector
   ```
   **Solution**: Verify GPU node exists
   ```bash
   oc get nodes -l node.kubernetes.io/instance-type=g6.12xlarge
   ```

3. **Taint/toleration mismatch**:
   ```
   0/12 nodes available: ... had untolerated taint {ai-app: true}
   ```
   **Solution**: Verify pod has tolerations (see deployment YAML)

---

#### PVC Binding Issues

**Symptom**:
```bash
oc get pvc ollama-models -n open-code-model-runtime
# NAME            STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# ollama-models   Pending                                       gp3            5m
```

**Diagnosis**:
```bash
oc describe pvc ollama-models -n open-code-model-runtime
```

**Common causes**:
1. **Storage class doesn't exist**: Check available storage classes
   ```bash
   oc get storageclass
   ```
2. **No available volumes**: Check provisioner

**Resolution**:
```bash
# Recreate PVC with correct storage class
oc delete pvc ollama-models -n open-code-model-runtime
oc apply -f pvc.yaml  # With correct storageClassName
```

---

### Network Issues

#### Can't Access Ollama Route

**Symptom**:
```bash
curl -k https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com
# Connection refused or timeout
```

**Diagnosis**:
```bash
# Check route exists
oc get route ollama -n open-code-model-runtime

# Check service endpoints
oc get endpoints ollama -n open-code-model-runtime

# Check pod is running
oc get pods -n open-code-model-runtime
```

**Resolution**:
1. **Pod not ready**: Wait for pod to be Running (1/1)
2. **Service not targeting pod**: Check selector matches pod labels
3. **Route not created**: Create route (see Step 6)

---

#### OpenCode Connection Errors

**Symptom**: OpenCode can't connect to model

**Diagnosis**:
```bash
# Test from local machine
curl -k https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/api/tags

# Should return JSON with model list
```

**Common causes**:
1. **Wrong endpoint in opencode.json**: Verify `baseURL`
2. **Model not loaded**: Check `ollama ps`
3. **Route TLS issues**: Use `https://` not `http://`

**Resolution**:
```json
// opencode.json - Correct configuration
{
  "options": {
    "baseURL": "https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/v1"
    //         ^^^^^^                                                      ^^^
    //         HTTPS                                                       /v1 suffix
  }
}
```

---

### MCP Server Issues

#### MCP Server Not Loading in OpenCode

**Symptom**: OpenCode doesn't show tools from MCP server

**Diagnosis**:
```bash
# Verify KUBECONFIG is set
echo $KUBECONFIG
# Should output: /home/avillega/.../kubeconfig

# Test cluster access
oc whoami

# Test MCP server manually
cd rh-virt
podman run --rm -i \
  --network=host \
  --userns=keep-id:uid=65532,gid=65532 \
  -v $KUBECONFIG:/kubeconfig:ro,Z \
  --entrypoint /app/kubernetes-mcp-server \
  quay.io/ecosystem-appeng/openshift-mcp-server:latest \
  --kubeconfig /kubeconfig \
  --toolsets core,kubevirt
```

**Common causes**:
1. **KUBECONFIG not set**: Export in shell before running OpenCode
2. **Wrong directory**: Must run OpenCode from project directory with `opencode.json`
3. **Podman permission issues**: Check SELinux context (`:Z` flag)

**Resolution**:
```bash
# Add to ~/.bashrc
export KUBECONFIG=~/work/redhat/projects/ai/ai5/agentic-collections/kubeconfig

# Reload shell
source ~/.bashrc

# Start OpenCode from correct directory
cd ~/work/redhat/projects/ai/ai5/agentic-collections/rh-virt
opencode
```

---

## 7. Verification & Testing

### Post-Deployment Checks

#### 1. Verify Pod is Running

```bash
oc get pods -n open-code-model-runtime

# Expected output:
# NAME                      READY   STATUS    RESTARTS   AGE
# ollama-xxx-yyy            1/1     Running   0          5m
```

**Check pod details**:
```bash
oc describe pod -n open-code-model-runtime -l app=ollama | grep -A 5 "Conditions:"

# Should show:
# Ready: True
# ContainersReady: True
```

---

#### 2. Verify GPU Allocation

```bash
# Check GPUs are visible to container
oc exec -n open-code-model-runtime deployment/ollama -- nvidia-smi

# Expected output:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 580.105.08   Driver Version: 580.105.08   CUDA Version: 13.0   |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        ...  | ...                         | ...                  |
# |   0  NVIDIA L4   ...  | ...                         | ...                  |
# |   1  NVIDIA L4   ...  | ...                         | ...                  |
# |   2  NVIDIA L4   ...  | ...                         | ...                  |
# |   3  NVIDIA L4   ...  | ...                         | ...                  |
# +-----------------------------------------------------------------------------+
```

---

#### 3. Verify Model is Loaded

```bash
# List available models
oc exec -n open-code-model-runtime deployment/ollama -- ollama list

# Expected output (at minimum):
# NAME                                     ID              SIZE      MODIFIED
# qwen2.5:72b-instruct-q6_K              <hash>         47 GB     <time>
# qwen2.5-coder:14b-instruct               <hash>         9.0 GB    <time>

# Check if model is currently loaded in memory
oc exec -n open-code-model-runtime deployment/ollama -- ollama ps

# Expected output:
# NAME                           ID       SIZE    PROCESSOR        CONTEXT  UNTIL
# qwen2.5:72b-instruct-q6_K    <hash>   176GB   51%/49% CPU/GPU  16384    24h from now
```

---

#### 4. Verify Environment Variables

```bash
oc exec -n open-code-model-runtime deployment/ollama -- \
  sh -c 'env | grep OLLAMA_ | grep -v PORT | grep -v SERVICE | sort'

# Expected output (key variables):
# OLLAMA_CONTEXT_LENGTH=131072
# OLLAMA_FLASH_ATTENTION=1
# OLLAMA_GPU_OVERHEAD=0
# OLLAMA_HOST=0.0.0.0:11434
# OLLAMA_KEEP_ALIVE=24h
# OLLAMA_MAX_LOADED_MODELS=1
# OLLAMA_MULTIUSER_CACHE=false
# OLLAMA_NOPRUNE=true
# OLLAMA_NUM_GPU=999
# OLLAMA_NUM_PARALLEL=1
# OLLAMA_ORIGINS=*
```

---

#### 5. Verify Resource Allocation

```bash
oc get deployment ollama -n open-code-model-runtime \
  -o jsonpath='{.spec.template.spec.containers[0].resources}' | jq .

# Expected output:
# {
#   "limits": {
#     "cpu": "45",
#     "memory": "170Gi",
#     "nvidia.com/gpu": "4"
#   },
#   "requests": {
#     "cpu": "40",
#     "memory": "150Gi",
#     "nvidia.com/gpu": "4"
#   }
# }
```

---

#### 6. Test API Endpoint

**Test native Ollama API**:
```bash
# List models
curl -k https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/api/tags

# Expected: JSON response with model list
```

**Test OpenAI-compatible API**:
```bash
curl -k https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/v1/models

# Expected: JSON response in OpenAI format
```

**Test simple inference**:
```bash
curl -k https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/api/generate \
  -d '{
    "model": "qwen2.5:72b-instruct-q6_K",
    "prompt": "Say hello",
    "stream": false
  }'

# Expected: JSON response with generated text
# Note: First request may take 3-5 minutes (model loading)
```

---

### Performance Testing

#### Baseline Response Time Test

```bash
# 1. Warm up model (first request loads it)
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q6_K "Hello"

# Wait for completion (3-5 minutes first time)

# 2. Test simple prompt (expected: ~18-25s)
time oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q6_K "Write a Python hello world function"

# 3. Test medium complexity (expected: ~20-30s)
time oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q6_K "Write a Python function to read and parse a JSON file with error handling"

# 4. Test complex task (expected: ~18-25s (optimized))
time oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q6_K "Create a REST API with Flask for user management including CRUD operations"
```

**Record results**:
- Simple: ______ seconds
- Medium: ______ seconds
- Complex: ______ seconds

**Expected ranges** (after optimizations):
- Simple: 15-20 seconds
- Medium: 18-25 seconds
- Complex: 20-30 seconds

---

#### GPU Utilization Test

**During inference, check GPU usage**:
```bash
# In one terminal, start a request
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q6_K "Write a comprehensive REST API with authentication"

# In another terminal, monitor GPUs
oc exec -n open-code-model-runtime deployment/ollama -- \
  nvidia-smi dmon -c 10

# Expected output (during inference):
# # gpu   pwr  gtemp  mtemp     sm    mem    enc    dec   ...
# # Idx     W      C      C      %      %      %      %   ...
#     0    XX     XX     XX     XX     XX      0      0   ...
#     1    XX     XX     XX     XX     XX      0      0   ...
#     2    XX     XX     XX     XX     XX      0      0   ...
#     3    XX     XX     XX     XX     XX      0      0   ...
#
# Look for non-zero sm (streaming multiprocessor) and mem (memory) values
```

---

#### Memory Usage Test

```bash
# Check VRAM usage
oc exec -n open-code-model-runtime deployment/ollama -- \
  nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv

# Expected output (model loaded):
# index, memory.used [MiB], memory.total [MiB], utilization.gpu [%]
# 0, ~XXXX MiB, 23034 MiB, XX%
# 1, ~XXXX MiB, 23034 MiB, XX%
# 2, ~XXXX MiB, 23034 MiB, XX%
# 3, ~XXXX MiB, 23034 MiB, XX%

# Check system RAM usage
oc exec -n open-code-model-runtime deployment/ollama -- free -h

# Expected output:
#               total        used        free      shared  buff/cache   available
# Mem:          ~181Gi       ~90-100Gi   ...       ...     ...          ~80-90Gi
```

---

### OpenCode Integration Test

#### 1. Verify OpenCode Configuration

```bash
cat ~/work/redhat/projects/ai/ai5/agentic-collections/opencode.json

# Verify:
# - "baseURL": "https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/v1"
# - "model": "ollama-ocp/qwen2.5:72b-instruct-q6_K"
```

---

#### 2. Test Basic OpenCode Interaction

```bash
# Start OpenCode
cd ~/work/redhat/projects/ai/ai5/agentic-collections
opencode

# In OpenCode:
# 1. Press Tab to verify model is selected
# 2. Ask a simple question: "What is 2+2?"
# 3. Expected: Response in ~20-25 seconds (after warm-up)
```

---

#### 3. Test Tool Calling

```bash
cd ~/work/redhat/projects/ai/ai5/agentic-collections/rh-virt
opencode

# In OpenCode (Build mode):
# "List all virtual machines in the cluster"
#
# Expected:
# - Model uses MCP tools (resources_list)
# - Returns list of VMs
# - Response time: ~20-30 seconds
```

---

### Automated Health Check Script

Save this as `check-ollama-health.sh`:

```bash
#!/bin/bash

echo "=== Ollama Health Check ==="
echo ""

# 1. Pod status
echo "1. Pod Status:"
oc get pods -n open-code-model-runtime -l app=ollama
echo ""

# 2. GPU detection
echo "2. GPU Detection:"
oc exec -n open-code-model-runtime deployment/ollama -- \
  nvidia-smi --query-gpu=index,name --format=csv 2>/dev/null | tail -n +2 || echo "FAILED"
echo ""

# 3. Model loaded
echo "3. Model Status:"
oc exec -n open-code-model-runtime deployment/ollama -- ollama ps 2>/dev/null || echo "FAILED"
echo ""

# 4. API endpoint
echo "4. API Endpoint:"
curl -k -s https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/api/tags \
  | jq -r '.models[]?.name' 2>/dev/null | head -5 || echo "FAILED"
echo ""

# 5. Resource allocation
echo "5. Resource Allocation:"
oc get deployment ollama -n open-code-model-runtime \
  -o jsonpath='{.spec.template.spec.containers[0].resources}' | jq -r '.requests, .limits'
echo ""

echo "=== Health Check Complete ==="
```

**Run**:
```bash
chmod +x check-ollama-health.sh
./check-ollama-health.sh
```

---

## 8. Known Limitations

### Model Size vs VRAM Constraint

**Issue**: Current model (Qwen2.5:72B-Q4_K_M) is 176GB in memory, but only 92GB VRAM available.

**Impact**:
- ~50% of model offloads to CPU/RAM
- Slower inference (18-25s vs potential 5-10s)
- Suboptimal GPU utilization (49% vs 100%)
- Higher CPU usage (51%)

**Why not resolved**:
- Q4_K_M quantization maintains maximum quality
- Q3_K_M would fit entirely in VRAM but with 3-6% quality loss
- Trade-off between quality and speed

**Mitigation**:
- Applied CPU/RAM optimizations (40-45% improvement)
- Monitoring for real-world impact on skill evaluation
- Q3_K_M ready to deploy if speed becomes critical

---

### Single Request Processing

**Current**: `OLLAMA_NUM_PARALLEL=1`

**Limitation**: Can only handle 1 concurrent request at a time

**Impact**:
- If multiple OpenCode sessions connect, requests queue
- Second request waits for first to complete

**Why configured this way**:
- Single-user development environment (not production API)
- OpenCode sends sequential requests (not concurrent)
- Dedicating all resources to 1 request = ~25-30% faster per request

**Workaround**: If concurrent use needed, increase to 2-4:
```bash
oc set env deployment/ollama -n open-code-model-runtime OLLAMA_NUM_PARALLEL=4
```
**Trade-off**: Slower individual requests (~25-30% penalty)

---

### Context Window Reduction

**Current**: 16,384 tokens (~12,000 words)
**Previous**: 32,768 tokens (~24,000 words)

**Limitation**: Large files or very long conversations may hit limit

**Impact**:
- Context truncation for prompts >16k tokens
- Tool schemas + file context + conversation must fit

**Why configured this way**:
- 99% of OpenCode prompts are <10k tokens
- Frees ~4-6GB VRAM for model layers
- Avoids previous 8k limit issues (caused truncation errors)

**Workaround**: Increase to 32k if needed (costs ~4-6GB VRAM):
```bash
oc set env deployment/ollama -n open-code-model-runtime OLLAMA_CONTEXT_LENGTH=131072
```

---

### Model Loading Latency

**Issue**: First request after 24h idle takes 3-5 minutes

**Cause**:
- Model unloads after 24h (`OLLAMA_KEEP_ALIVE=24h`)
- Reload requires loading 176GB from disk to GPU/RAM

**Impact**: Cold start penalty once per day

**Why not resolved**:
- Keeping model loaded 24/7 wastes GPU resources during non-use
- 24h is reasonable for development workflow
- After first request, subsequent requests are fast (18-25s)

**Workaround**: Pre-warm before work session:
```bash
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q6_K "Hello"
```

---

### No Auto-scaling

**Current**: Fixed 1 replica deployment

**Limitation**: Can't scale horizontally for increased load

**Why**:
- GPU resources are dedicated (1 node with 4 GPUs)
- Model requires all 4 GPUs
- Scaling would require additional GPU nodes (~$4/hour each)

**Impact**: Single point of failure (if pod crashes)

**Mitigation**:
- Kubernetes auto-restarts failed pods
- Recreate strategy ensures clean startup
- For HA, would need multi-node GPU cluster (high cost)

---

### CPU-Based Inference Performance

**CPU-only systems** (not GPU cluster):
- 3B models: 15-30s (acceptable)
- 7B models: 60-120s (slow)
- 14B+ models: 2-5 minutes (impractical)

**Root cause**: CPU inference is memory-bandwidth limited

**Recommendation**: GPU acceleration mandatory for models >7B

---

### Container Resource Limits Incompatibility

**Critical**: Docker/Podman `--cpus` and `--memory` flags cause deadlocks with Ollama (llama.cpp)

**Symptoms**:
- Infinite generation without termination
- 100% CPU, no progress
- API requests never complete

**Why**:
- llama.cpp has its own thread scheduling
- Container limits conflict with llama.cpp work queue
- Thread starvation and deadlocks

**Solution**: Use Kubernetes resource limits only (never container runtime limits)

**Correct**:
```yaml
# Pod spec (YAML)
resources:
  limits:
    cpu: "45"
```

**Incorrect**:
```bash
# Container run command - DON'T DO THIS
podman run --cpus="16" ollama/ollama
```

---

### Tool Calling Model Requirement

**Limitation**: Only `-instruct` model variants support function calling

**Impact**:
- Base models (without `-instruct`) can't use tools
- OpenCode requires tool calling for MCP servers

**Error signature**:
```
registry.ollama.ai/library/model-name does not support tools
```

**Resolution**: Always use `-instruct` variants
- ✅ `qwen2.5:72b-instruct-q6_K`
- ❌ `qwen2.5:72b-q4_K_M` (missing -instruct)

---

## 9. Future Improvements

### High Priority: Switch to Q3_K_M Quantization

**Objective**: Achieve 100% GPU utilization and 10x faster responses

**Current State**:
- Model: Qwen2.5:72B-instruct-Q4_K_M (176GB, 51% CPU offloading)
- Response time: 18-25s

**Target State**:
- Model: Qwen2.5:72B-instruct-Q3_K_M (35GB, 100% GPU)
- Expected response time: 5-10s
- **10x performance improvement**

---

#### Deployment Guide for Q3_K_M

**Step 1: Download Q3_K_M model**:
```bash
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama pull qwen2.5:72b-instruct-q3_K_M

# Expected: ~8-12 minutes (~35GB download)
```

---

**Step 2: Test Q3_K_M performance**:
```bash
# Load model
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q3_K_M "Test loading"

# Check CPU/GPU split
oc exec -n open-code-model-runtime deployment/ollama -- ollama ps

# Expected output:
# NAME                           ID       SIZE    PROCESSOR        CONTEXT  UNTIL
# qwen2.5:72b-instruct-q3_K_M    <hash>   ~35GB   0%/100% CPU/GPU  16384    24h from now
#                                                 ^^^^^^^^^^^^^^^^
#                                                 100% GPU = OPTIMAL

# Benchmark response time
time oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q3_K_M "Write a Python function to calculate fibonacci"

# Expected: 5-10 seconds (vs 18-25s with Q4_K_M)
```

---

**Step 3: Update OpenCode configuration**:

Edit `~/work/redhat/projects/ai/ai5/agentic-collections/opencode.json`:

```json
{
  "model": "ollama-ocp/qwen2.5:72b-instruct-q3_K_M"
  //                                         ^^^
  //                                         Change q4 → q3
}
```

---

**Step 4: Validate quality (A/B testing)**:

Test same prompts with Q3 and Q4, compare quality:

```bash
# Q4_K_M (current)
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q6_K "Explain the difference between async and await in Python"

# Q3_K_M (new)
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama run qwen2.5:72b-instruct-q3_K_M "Explain the difference between async and await in Python"

# Compare:
# - Factual accuracy
# - Code quality
# - Coherence
```

**Expected**: 3-6% quality difference (minor, often imperceptible for code tasks)

---

**Step 5: Decision**:
- **If quality acceptable**: Keep Q3_K_M as default (10x faster)
- **If quality insufficient**: Revert to Q4_K_M (slower but more precise)

---

**Rollback (if needed)**:
```json
// opencode.json
{
  "model": "ollama-ocp/qwen2.5:72b-instruct-q6_K"
  //                                         ^^^
  //                                         Revert to Q4
}
```

---

#### Expected Performance Gains (Q3_K_M)

| Metric | Q4_K_M (Current) | Q3_K_M (Projected) | Improvement |
|--------|------------------|-------------------|-------------|
| **Response time** | 18-25s | 5-10s | **~10x faster** |
| **Model size** | 176GB | 35GB | Fits in VRAM |
| **GPU utilization** | 49% | 100% | Full GPU usage |
| **VRAM used** | 2.5GB | 36GB | 14x more VRAM |
| **CPU offloading** | 51% | 0% | Eliminated |
| **RAM usage** | 93GB | ~5GB | 95% reduction |
| **Quality** | 100% (reference) | ~95% | 3-6% loss |

---

### Medium Priority: Alternative Model Options

#### Option A: Qwen2.5:32B-Q8 (Higher Quality, Smaller Model)

**Profile**:
- Model size: ~35GB (fits in VRAM)
- Quantization: 8-bit (higher quality than Q4)
- Parameters: 32B (smaller than 72B)
- Expected response time: 8-12s

**Trade-off**: Smaller model but better quantization

**When to use**: If Q3_K_M quality is insufficient but Q4_K_M is too slow

**Deployment**:
```bash
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama pull qwen2.5:32b-instruct-q8_0
```

---

#### Option B: Specialized Code Models

For code-only workflows (no general reasoning):

**qwen2.5-coder:32b-instruct**:
- Code-specialized 32B model
- Fits in VRAM (~15GB)
- Faster than general 72B model
- Better code generation than general 32B

**Deployment**:
```bash
oc exec -n open-code-model-runtime deployment/ollama -- \
  ollama pull qwen2.5-coder:32b-instruct-q4_K_M
```

---

### Low Priority: Infrastructure Improvements

#### Multi-Model Support

**Current**: `OLLAMA_MAX_LOADED_MODELS=1` (only one model in memory)

**Enhancement**: Support 2-3 models simultaneously
- Q3_K_M for speed (most requests)
- Q4_K_M for quality (critical tasks)
- 14B-coder for simple code tasks

**Trade-off**:
- More VRAM usage (need to fit multiple models)
- Currently not feasible with 72B models

**When viable**: After switching to Q3_K_M (frees 140GB RAM)

---

#### Horizontal Pod Autoscaling

**Current**: Fixed 1 replica

**Enhancement**: Auto-scale based on request load
- Scale to 0 during inactivity (save costs)
- Scale to 2-3 during high demand

**Requirements**:
- Additional GPU nodes (g6.12xlarge)
- Cost: ~$4.32/hour per additional node
- Load balancer for request distribution

**ROI**: Only viable for production multi-user scenarios

---

#### Observability Enhancements

**Current**: Manual monitoring via `oc exec` and `nvidia-smi`

**Enhancement**: Prometheus + Grafana dashboards
- GPU utilization over time
- Response time percentiles (p50, p95, p99)
- Model loading frequency
- Error rate tracking

**Components needed**:
- NVIDIA DCGM Exporter (already available in GPU operator)
- Prometheus ServiceMonitor for Ollama
- Grafana dashboards

---

### Research: Emerging Models

Keep monitoring for new models:

**DeepSeek-V3** (70B-140B):
- Reported strong code generation
- Mixture-of-Experts architecture
- May offer better speed/quality trade-off

**Qwen2.5-Max** (future release):
- Rumored 100B+ parameter model
- Enhanced reasoning capabilities

**Meta Llama 4** (expected 2026):
- Next generation Llama family
- Likely improved efficiency

---

## Appendix

### Quick Reference Commands

```bash
# === Pod Management ===
# Check pod status
oc get pods -n open-code-model-runtime

# View logs
oc logs -n open-code-model-runtime deployment/ollama --tail=50 -f

# Restart deployment
oc rollout restart deployment/ollama -n open-code-model-runtime

# === Model Management ===
# List available models
oc exec -n open-code-model-runtime deployment/ollama -- ollama list

# Check loaded model
oc exec -n open-code-model-runtime deployment/ollama -- ollama ps

# Download model
oc exec -n open-code-model-runtime deployment/ollama -- ollama pull <model-name>

# Remove model
oc exec -n open-code-model-runtime deployment/ollama -- ollama rm <model-name>

# === GPU Monitoring ===
# Check GPU status
oc exec -n open-code-model-runtime deployment/ollama -- nvidia-smi

# Monitor GPU utilization
oc exec -n open-code-model-runtime deployment/ollama -- nvidia-smi dmon -c 10

# Check VRAM usage
oc exec -n open-code-model-runtime deployment/ollama -- \
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# === API Testing ===
# List models (external)
curl -k https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/api/tags

# Test inference
curl -k https://ollama.apps.cn-ai-lab.2vn8.p1.openshiftapps.com/api/generate \
  -d '{"model":"qwen2.5:72b-instruct-q6_K","prompt":"Hello","stream":false}'

# === Configuration ===
# View environment variables
oc exec -n open-code-model-runtime deployment/ollama -- \
  sh -c 'env | grep OLLAMA_ | sort'

# Check resource allocation
oc get deployment ollama -n open-code-model-runtime \
  -o jsonpath='{.spec.template.spec.containers[0].resources}' | jq .

# === OpenCode ===
# Start OpenCode (from project root)
cd ~/work/redhat/projects/ai/ai5/agentic-collections
opencode

# Start OpenCode with MCP server (from rh-virt)
cd ~/work/redhat/projects/ai/ai5/agentic-collections/rh-virt
opencode
```

---

### File Locations

| File | Path | Purpose |
|------|------|---------|
| OpenCode config | `~/work/redhat/projects/ai/ai5/agentic-collections/opencode.json` | Model and provider settings |
| MCP config (rh-virt) | `~/work/redhat/projects/ai/ai5/agentic-collections/rh-virt/opencode.json` | MCP server for VMs |
| Kubeconfig | `~/work/redhat/projects/ai/ai5/agentic-collections/kubeconfig` | Cluster authentication |
| This guide | `~/work/redhat/projects/ai/ai5/agentic-collections/OPENCODE_SETUP.md` | Complete documentation |

---

### Support Resources

**OpenCode**:
- Documentation: https://opencode.ai/docs
- GitHub: https://github.com/opencode-ai

**Ollama**:
- Documentation: https://ollama.ai/docs
- Model library: https://ollama.ai/library
- GitHub: https://github.com/ollama/ollama

**OpenShift**:
- Documentation: https://docs.openshift.com/
- NVIDIA GPU Operator: https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/

**Internal**:
- Repository: https://github.com/RHEcosystemAppEng/agentic-collections
- CLAUDE.md: Repository guidelines and architecture

---

**Document Version**: 2.0
**Last Updated**: 2026-03-13
**Status**: Production (Active)
**Deployment**: g6.12xlarge (4x NVIDIA L4)
**Model**: Qwen2.5:72B-instruct-Q4_K_M
**Next Optimization**: Q3_K_M migration (10x speedup)

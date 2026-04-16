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

**Initialize:**
```bash
oc apply -f manifests/openshift-ai/datasciencecluster.yaml
```

**Verify OpenShift AI is running:**
```bash
oc get datasciencecluster
oc get pods -n redhat-ods-applications
```

---

### 2. Model Deployment

This section covers deploying Llama 3.1 405B using KServe with RawDeployment mode and vLLM runtime.

#### 2.1. Prepare Model Storage

**Create namespace and PVC:**
```bash
oc apply -f manifests/models/llama31-405b/namespace.yaml
oc apply -f manifests/models/llama31-405b/pvc.yaml
```

**Verify PVC is bound:**
```bash
oc get pvc -n llama31-405b
```

**Load model into PVC:**

You need to copy the Llama 3.1 405B model files into the PVC. This can be done using a helper pod:

```bash
oc run -n llama31-405b model-loader --image=registry.access.redhat.com/ubi9/ubi:latest \
  --restart=Never --command -- sleep infinity

oc set volume pod/model-loader -n llama31-405b --add \
  --name=model-storage --type=persistentVolumeClaim \
  --claim-name=llama31-405b-model --mount-path=/mnt/models

oc wait --for=condition=Ready pod/model-loader -n llama31-405b --timeout=300s
```

Then copy the model files (from your bastion/mirror host):
```bash
oc cp /path/to/llama31-405b-fp8/ llama31-405b/model-loader:/mnt/models/
```

Verify the model files:
```bash
oc exec -n llama31-405b model-loader -- ls -lh /mnt/models/
```

Clean up the helper pod:
```bash
oc delete pod model-loader -n llama31-405b
```

#### 2.2. Deploy the Model

**Deploy ServingRuntime and InferenceService:**
```bash
oc apply -f manifests/models/llama31-405b/servingruntime.yaml
oc apply -f manifests/models/llama31-405b/inferenceservice.yaml
```

**Verify deployment:**
```bash
oc get inferenceservice -n llama31-405b
oc get pods -n llama31-405b
```

Wait for the predictor pod to be running:
```bash
oc wait --for=condition=Ready pod -l serving.kserve.io/inferenceservice=llama31-405b -n llama31-405b --timeout=600s
```

#### 2.3. Test the Model

**Get the inference service URL:**
```bash
oc get inferenceservice llama31-405b -n llama31-405b -o jsonpath='{.status.url}'
```

**Test the endpoint (from within the cluster):**
```bash
oc run -n llama31-405b test-client --image=registry.access.redhat.com/ubi9/ubi:latest \
  --restart=Never --rm -it -- bash -c "
curl -X POST http://llama31-405b-predictor.llama31-405b.svc.cluster.local:8080/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{
    \"model\": \"/mnt/models\",
    \"prompt\": \"What is OpenShift?\",
    \"max_tokens\": 100,
    \"temperature\": 0.7
  }'
"
```

---

**Previous versions and reference materials** are preserved in [`extra_docs/`](./extra_docs/) for reference.

---

## Tested Models

| Model | Size | Quantization | GPUs Required | Status | Notes |
|-------|------|--------------|---------------|--------|-------|
| Llama 3.1 405B | 405B | FP8 | 8x H100 80GB | Testing | Initial deployment |

---

**Version:** 2.0  
**Status:** In development  
**Last Updated:** 2026-04-07

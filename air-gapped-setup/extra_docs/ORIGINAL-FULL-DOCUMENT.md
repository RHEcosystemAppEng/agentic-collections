# AirGapped LLM Deployment with OpenShift AI and OpenCode

## Reference Document for LLM Deployment in AirGapped Environment

**Version**: 1.0
**Date**: 2026-04-03
**Author**: Agentic Collections Team
**Purpose**: Deploy a powerful open-source LLM on OpenShift 4.20+ using Red Hat OpenShift AI so users can execute all skills from the agentic-collections repository via OpenCode in an internet-disconnected environment. This document covers model selection, testing methodology, and complete deployment procedures.

---

## Table of Contents

1. [Context and Purpose](#context-and-purpose)
2. [Solution Architecture](#solution-architecture)
3. [Model Selection and Testing](#model-selection-and-testing)
4. [Red Hat Components](#red-hat-components)
5. [Air Gapped Environment Setup](#installation-air-gapped-environment)
6. [GPU Node Provisioning](#gpu-node-provisioning)
7. [OpenShift Cluster Configuration](#openshift-cluster-configuration)
8. [Red Hat OpenShift AI Installation](#red-hat-openshift-ai-installation)
9. [Model Deployment with vLLM](#model-deployment-with-vllm)
10. [OpenCode Configuration](#opencode-configuration)
11. [Validation and Testing](#validation-and-testing)
12. [Security Considerations](#security-considerations)
13. [Troubleshooting](#troubleshooting)
14. [References](#references)

---

## 1. Context and Purpose

### 1.1 Why an AirGapped Environment?

An **AirGapped** environment (disconnected from the internet) is essential for:

- **Security and Compliance**: Organizations with strict security requirements (government, defense, finance, healthcare)
- **Data Sovereignty**: Keep sensitive data completely isolated from external networks
- **Total Control**: Complete management of model lifecycle without external dependencies
- **Certifications**: Compliance with regulations requiring network isolation

### 1.2 Deployment Objective

Create a complete infrastructure where:

1. **Local LLM**: Selected open-source model running on OpenShift with dedicated GPUs
2. **User Interface**: OpenCode as client to interact with the model
3. **Complete Skills**: Ability to execute ALL skills from the agentic-collections repository
4. **Performance**: Real-time responses (order of seconds)
5. **Reproducibility**: Complete documentation to replicate the environment

### 1.3 Use Case

Users of the `agentic-collections` repository will be able to:

- Execute skills from `rh-sre`, `ocp-admin`, `rh-virt`, `rh-developer`, etc.
- Interact with the model via OpenCode without needing external cloud services
- Maintain privacy and total control over conversations and data

---

## 2. Solution Architecture

### 2.1 Architecture Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    OpenShift Cluster 4.20+                     │
│                                                                │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │ Master Node  │     │ Master Node  │     │ Master Node  │    │
│  │   (Control)  │     │   (Control)  │     │   (Control)  │    │
│  └──────────────┘     └──────────────┘     └──────────────┘    │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Worker Nodes (General Workloads)            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          GPU Worker Node (Dedicated for AI/ML)           │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │   Red Hat OpenShift AI (RHOAI) 2.20+             │    │  │
│  │  │                                                  │    │  │
│  │  │  ┌─────────────────────────────────────────────┐ │    │  │
│  │  │  │  vLLM Serving Runtime                       │ │    │  │
│  │  │  │  - Selected LLM Model (FP8 Quantized)       │ │    │  │
│  │  │  │  - Tensor Parallelism: Configured per model │ │    │  │
│  │  │  │  - Inference Server: OpenAI Compatible API  │ │    │  │
│  │  │  └─────────────────────────────────────────────┘ │    │  │
│  │  │                                                  │    │  │
│  │  │  ┌─────────────────────────────────────────────┐ │    │  │
│  │  │  │  KServe Inference Service                   │ │    │  │
│  │  │  │  - Service Route: llm-model.apps.ocp.com    │ │    │  │
│  │  │  │  - Protocol: HTTP/S (OpenAI compatible)     │ │    │  │
│  │  │  └─────────────────────────────────────────────┘ │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │                                                          │  │
│  │  Hardware: AWS GPU Instance (TBD based on model)         │  │
│  │  - NVIDIA GPUs (H100/A100)                               │  │
│  │  - GPU Memory: Scaled per model requirements            │  │
│  │  - High-speed GPU interconnect                           │  │
│  │  - EFA Network for distributed inference                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Object Storage (S3-Compatible)                  │  │
│  │          - Model Weights Storage                         │  │
│  │          - Quay.io Registry for Images                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/API
                              ▼
                   ┌──────────────────────┐
                   │   User Workstation   │
                   │                      │
                   │  OpenCode CLI        │
                   │  - Connected to:     │
                   │    LLM model route   │
                   │  - Executes Skills   │
                   └──────────────────────┘
```

### 2.2 Data Flow

1. **User → OpenCode**: User executes a command or skill in OpenCode
2. **OpenCode → OpenShift Route**: OpenCode sends HTTP requests to the model route
3. **KServe → vLLM**: KServe routes the request to the vLLM server
4. **vLLM → GPUs**: vLLM distributes inference across available GPUs using tensor parallelism
5. **Response**: The model generates the response and returns it via the same route
6. **OpenCode → User**: OpenCode presents the response to the user

### 2.3 Main Components

| Component | Version | Purpose |
|-----------|---------|---------|
| OpenShift Container Platform | 4.20+ | Container orchestration |
| Red Hat OpenShift AI | 2.20+ | ML/AI platform |
| vLLM | Latest (RHOAI 2.20) | Optimized inference server |
| Open Source LLM | TBD (see Section 3) | Language model |
| KServe | Included in RHOAI | ML model serving |
| Node Feature Discovery | Latest | GPU detection |
| NVIDIA GPU Operator | Latest | GPU driver management |
| Quay.io | Cloud | Image registry |

---

## 3. Model Selection and Testing

### 3.1 Testing Strategy

Rather than prescribing hardware requirements upfront, we will follow an empirical approach:

1. **Test multiple candidate models** with varying sizes and architectures
2. **Evaluate each model** against real skills from the agentic-collections repository
3. **Measure performance metrics**: latency, throughput, quality, and resource consumption
4. **Document hardware requirements** based on actual measurements
5. **Select the optimal model** balancing capability, cost, and performance

This approach ensures we make data-driven decisions rather than relying solely on theoretical specifications.

### 3.2 Candidate Models for Evaluation

The following models are candidates for testing:

| Model | Parameters | Architecture | License | Expected VRAM (FP8) |
|-------|------------|--------------|---------|---------------------|
| **Llama 3.1 405B** | 405B | Dense Transformer | Meta Llama 3.1 | ~486 GB |
| **Llama 3.1 70B** | 70B | Dense Transformer | Meta Llama 3.1 | ~85 GB |
| **Llama 3.3 70B** | 70B | Dense Transformer | Meta Llama 3.3 | ~85 GB |
| **Mixtral 8x22B** | ~175B (active) | Mixture of Experts | Apache 2.0 | ~220 GB |
| **Qwen 2.5 72B** | 72B | Dense Transformer | Apache 2.0 | ~90 GB |
| **DeepSeek V3** | 671B (37B active) | Mixture of Experts | MIT | ~70 GB |
| **Nemotron 70B** | 70B | Dense Transformer | NVIDIA Open Model | ~85 GB |

**Selection Criteria:**

- **Open Source**: Must have permissive licensing for commercial use
- **vLLM Support**: Must be compatible with vLLM serving runtime
- **Code Generation**: Strong performance on technical tasks
- **Multilingual**: Support for English and Spanish
- **Context Length**: At least 32K tokens (preferably 128K+)

### 3.3 Test Cases for Evaluation

Each model will be evaluated using representative skills from the repository:

#### Category 1: Simple Information Retrieval (Baseline)
- **Skill**: `/cluster-report` (list namespaces, basic queries)
- **Metrics**: Latency, accuracy
- **Pass Criteria**: <5s latency, 100% accuracy

#### Category 2: Complex Analysis
- **Skill**: `/cve-impact` (analyze CVE-2024-3094 xz backdoor)
- **Metrics**: Depth of analysis, actionable recommendations
- **Pass Criteria**: Identifies CVSS score, affected systems, mitigation steps

#### Category 3: Code Generation
- **Skill**: `/playbook-generator` (generate Ansible playbook for patching)
- **Metrics**: Syntactic correctness, idempotency, error handling
- **Pass Criteria**: Valid YAML, runs without errors, follows best practices

#### Category 4: Orchestration (Most Complex)
- **Skill**: `/remediation` (end-to-end CVE remediation workflow)
- **Metrics**: Multi-step reasoning, tool calling accuracy, workflow coherence
- **Pass Criteria**: Executes all 6 sub-skills correctly, generates valid outputs

#### Category 5: Long Context
- **Test**: Analyze all SKILL.md files in `rh-sre/skills/` directory
- **Metrics**: Context retention, summarization accuracy
- **Pass Criteria**: Processes >50K tokens without truncation or hallucination

### 3.4 Hardware Requirements per Model

**Note**: This section will be populated after testing is complete.

| Model | Min GPUs | GPU Type | Total VRAM | AWS Instance | Hourly Cost | Avg Latency | Quality Score |
|-------|----------|----------|------------|--------------|-------------|-------------|---------------|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

**Testing Infrastructure:**

We will use AWS instances with flexible GPU configurations:

| Instance Type | GPUs | GPU Memory | vCPUs | RAM | Hourly Cost | Use Case |
|---------------|------|------------|-------|-----|-------------|----------|
| **p5.48xlarge** | 8x H100 | 640 GB | 192 | 2 TB | ~$98.32 | 405B models |
| **p4d.24xlarge** | 8x A100 | 320 GB | 96 | 1.1 TB | ~$32.77 | 70B-175B models |
| **p4de.24xlarge** | 8x A100 | 640 GB | 96 | 1.1 TB | ~$40.97 | 70B-405B models |
| **g5.48xlarge** | 8x A10G | 192 GB | 192 | 768 GB | ~$16.29 | <70B models |

### 3.5 Selected Model and Justification

**Note**: This section will be completed after evaluation is finished.

**Selection will be based on:**

1. **Capability**: Can it execute all repository skills successfully?
2. **Performance**: Does it meet the <5s latency requirement for typical requests?
3. **Cost**: What is the total cost of ownership (instance + operational)?
4. **Reliability**: Does it produce consistent, high-quality results?
5. **Maintainability**: How easy is it to deploy, update, and troubleshoot?

**Current Status**: Testing in progress

### 3.6 OpenShift Cluster Requirements

Regardless of model selection, the OpenShift cluster will have:

#### Existing Infrastructure
- **3 Master Nodes**: Control plane (HA)
- **N Worker Nodes**: General workloads

#### GPU Node Configuration (to be provisioned)
- **Node Type**: AWS EC2 instance with NVIDIA GPUs (type TBD based on model selection)
- **Taints**: `nvidia.com/gpu=present:NoSchedule` (dedicated for GPU workloads)
- **Labels**: `node-role.kubernetes.io/gpu-worker=true`
- **Storage**: 2TB EBS gp3 volume for model weights

---

## 4. Red Hat Components

### 4.1 Red Hat OpenShift Container Platform

**Version**: 4.20+ (currently 4.21.5 available)

- **Purpose**: Enterprise Kubernetes container orchestration
- **Features**:
  - Application lifecycle management
  - Multi-tenancy and isolation
  - Advanced networking (SDN/OVN)
  - Operators for automation

### 4.2 Red Hat OpenShift AI (RHOAI)

**Version**: 2.20+ (latest compatible with OCP 4.21.5)

**Included components**:

| Component | Purpose |
|-----------|---------|
| **KServe** | Model serving framework |
| **vLLM Runtime** | Optimized LLM inference |
| **Model Mesh** | Multi-model serving (optional) |
| **Data Science Pipelines** | MLOps workflows |
| **Jupyter Notebooks** | Interactive development |
| **Model Registry** | Model versioning |

**Runtime Image**:
```
quay.io/modh/vllm:rhoai-2.20-cuda
```

**Source**: [Red Hat OpenShift AI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.20/html/serving_models/serving-large-models_serving-large-models)

### 4.3 Required Operators

1. **Red Hat OpenShift AI Operator**
   - Installation from OperatorHub
   - Namespace: `redhat-ods-operator`

2. **Node Feature Discovery (NFD) Operator**
   - Automatic GPU detection
   - Namespace: `openshift-nfd`

3. **NVIDIA GPU Operator**
   - NVIDIA drivers
   - CUDA toolkit
   - Namespace: `nvidia-gpu-operator`

---

## 5. Installation Air Gapped Environment

This section provides step-by-step instructions to configure a brand-new OpenShift cluster for LLM deployment in an air-gapped environment. All commands are designed to be copy-paste ready.

**Prerequisites:**
- OpenShift cluster 4.20+ installed and accessible
- `oc` CLI installed and authenticated as cluster-admin
- Internet-disconnected environment with mirrored registries configured (if applicable)

**Operator Installation Strategy:**

Based on Red Hat's official recommendations:
- **Single-Model Serving Platform** with KServe (recommended for LLMs)
- **RawDeployment mode** (Standard deployment mode in UI)
- **vLLM runtime** for NVIDIA GPU inference

**References:**
- [RHOAI 2.22 Model Serving Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.22/html/serving_models/about-model-serving_about-model-serving)
- [RHOAI 3.2 Deploying Models](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.2/html-single/deploying_models/index)

---

### 5.1 Verify and Install Required Operators

This section covers verification and installation of the three essential operators needed for LLM deployment.

#### Step 1: Check Current Operator Installation Status

Run the following commands to check if required operators are already installed:

```bash
# Check Node Feature Discovery Operator
echo "=== Node Feature Discovery Operator ==="
oc get csv -n openshift-nfd 2>/dev/null | grep nfd || echo "NOT INSTALLED"

# Check NVIDIA GPU Operator
echo -e "\n=== NVIDIA GPU Operator ==="
oc get csv -n nvidia-gpu-operator 2>/dev/null | grep gpu-operator || echo "NOT INSTALLED"

# Check Red Hat OpenShift AI Operator
echo -e "\n=== Red Hat OpenShift AI Operator ==="
oc get csv -n redhat-ods-operator 2>/dev/null | grep rhods-operator || echo "NOT INSTALLED"

# Summary check
echo -e "\n=== Summary ==="
oc get operators --all-namespaces 2>/dev/null | grep -E "nfd|gpu-operator|rhods-operator" || echo "No required operators found"
```

**Expected Output (if installed):**
```
=== Node Feature Discovery Operator ===
nfd.4.20.0-xxx   Node Feature Discovery Operator   4.20.0   Succeeded

=== NVIDIA GPU Operator ===
gpu-operator-certified.v25.0.0   NVIDIA GPU Operator   v25.0.0   Succeeded

=== Red Hat OpenShift AI Operator ===
rhods-operator.2.22.0   Red Hat OpenShift AI   2.22.0   Succeeded
```

#### Step 2: Install Node Feature Discovery (NFD) Operator

If NFD is not installed, run the following:

```bash
# Create namespace for NFD
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-nfd
  labels:
    openshift.io/cluster-monitoring: "true"
EOF

# Create OperatorGroup
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: nfd-operator-group
  namespace: openshift-nfd
spec:
  targetNamespaces:
    - openshift-nfd
EOF

# Create Subscription
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: nfd
  namespace: openshift-nfd
spec:
  channel: stable
  name: nfd
  source: redhat-operators
  sourceNamespace: openshift-marketplace
  installPlanApproval: Automatic
EOF
```

**Verify installation:**

```bash
# Wait for operator to be ready (may take 2-3 minutes)
echo "Waiting for NFD operator to be ready..."
oc wait --for=condition=Ready pod -l name=nfd-operator -n openshift-nfd --timeout=300s

# Check CSV status
oc get csv -n openshift-nfd

# Expected output should show "Succeeded" in PHASE column
```

**Create NodeFeatureDiscovery instance:**

```bash
cat <<EOF | oc apply -f -
apiVersion: nfd.openshift.io/v1
kind: NodeFeatureDiscovery
metadata:
  name: nfd-instance
  namespace: openshift-nfd
spec:
  operand:
    image: registry.redhat.io/openshift4/ose-node-feature-discovery:v4.20
    servicePort: 12000
  workerConfig:
    configData: |
      sources:
        pci:
          deviceClassWhitelist:
            - "0300"
            - "0302"
          deviceLabelFields:
            - "vendor"
            - "device"
EOF
```

**Verify NFD is running:**

```bash
# Check NFD pods
oc get pods -n openshift-nfd

# Expected output: nfd-controller-manager and nfd-worker pods should be Running
```

#### Step 3: Install NVIDIA GPU Operator

If NVIDIA GPU Operator is not installed, run the following:

```bash
# Create namespace for NVIDIA GPU Operator
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: nvidia-gpu-operator
  labels:
    openshift.io/cluster-monitoring: "true"
EOF

# Create OperatorGroup
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: nvidia-gpu-operator-group
  namespace: nvidia-gpu-operator
spec:
  targetNamespaces:
    - nvidia-gpu-operator
EOF

# Create Subscription
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: gpu-operator-certified
  namespace: nvidia-gpu-operator
spec:
  channel: v25.0
  name: gpu-operator-certified
  source: certified-operators
  sourceNamespace: openshift-marketplace
  installPlanApproval: Automatic
EOF
```

**Verify installation:**

```bash
# Wait for operator to be ready (may take 3-5 minutes)
echo "Waiting for NVIDIA GPU operator to be ready..."
oc wait --for=condition=Ready pod -l app=gpu-operator -n nvidia-gpu-operator --timeout=600s

# Check CSV status
oc get csv -n nvidia-gpu-operator

# Expected output should show "Succeeded" in PHASE column
```

**Note:** The ClusterPolicy for NVIDIA GPU Operator will be configured later in Section 7 after GPU nodes are available.

#### Step 4: Install Red Hat OpenShift AI Operator

If RHOAI is not installed, run the following:

```bash
# Create namespace for OpenShift AI
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: redhat-ods-operator
  labels:
    openshift.io/cluster-monitoring: "true"
EOF

# Create OperatorGroup
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: redhat-ods-operator-group
  namespace: redhat-ods-operator
spec: {}
EOF

# Create Subscription
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: rhods-operator
  namespace: redhat-ods-operator
spec:
  channel: stable-2.22
  name: rhods-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
  installPlanApproval: Automatic
EOF
```

**Verify installation:**

```bash
# Wait for operator to be ready (may take 3-5 minutes)
echo "Waiting for RHOAI operator to be ready..."
oc wait --for=condition=Ready pod -l name=rhods-operator -n redhat-ods-operator --timeout=600s

# Check CSV status
oc get csv -n redhat-ods-operator

# Expected output should show "Succeeded" in PHASE column
```

**Create DataScienceCluster:**

```bash
cat <<EOF | oc apply -f -
apiVersion: datasciencecluster.opendatahub.io/v1
kind: DataScienceCluster
metadata:
  name: default-dsc
spec:
  components:
    codeflare:
      managementState: Removed
    dashboard:
      managementState: Managed
    datasciencepipelines:
      managementState: Removed
    kserve:
      managementState: Managed
      serving:
        ingressGateway:
          certificate:
            type: SelfSigned
        managementState: Managed
        name: knative-serving
    modelmeshserving:
      managementState: Removed
    ray:
      managementState: Removed
    workbenches:
      managementState: Removed
EOF
```

**Important Notes:**
- **ModelMesh**: Set to `Removed` (deprecated since RHOAI 2.19)
- **KServe**: Set to `Managed` (recommended for LLM serving)
- **Knative Serving**: Enabled for RawDeployment mode support

**Verify DataScienceCluster is ready:**

```bash
# Check DataScienceCluster status
oc get datasciencecluster default-dsc -o jsonpath='{.status.phase}' && echo

# Expected output: "Ready"

# Check all RHOAI components
oc get pods -n redhat-ods-applications

# Expected: Multiple pods in Running state (dashboard, kserve-controller, etc.)
```

#### Step 5: Final Verification

Run a comprehensive check to ensure all operators are installed and ready:

```bash
echo "=== Final Operator Status Check ==="

# Check all operator namespaces
for ns in openshift-nfd nvidia-gpu-operator redhat-ods-operator; do
  echo -e "\n--- Namespace: $ns ---"
  oc get csv -n $ns
  oc get pods -n $ns --field-selector=status.phase!=Running 2>/dev/null && echo "WARNING: Some pods are not Running!" || echo "All pods Running"
done

# Check RHOAI applications namespace
echo -e "\n--- RHOAI Applications ---"
oc get pods -n redhat-ods-applications

# Check if KServe components are available
echo -e "\n--- KServe Components ---"
oc get crd | grep -E "inferenceservice|servingruntime"

# Expected output should include:
# inferenceservices.serving.kserve.io
# servingruntimes.serving.kserve.io
```

**Expected Result:**

All three operators should be installed with status "Succeeded" and all pods in "Running" state.

```
✓ Node Feature Discovery Operator: Installed
✓ NVIDIA GPU Operator: Installed (ClusterPolicy pending GPU nodes)
✓ Red Hat OpenShift AI Operator: Installed
✓ DataScienceCluster: Ready
✓ KServe CRDs: Available
```

---

**Next Steps:**

Once all operators are verified and running, proceed to:
- **Section 6: GPU Node Provisioning** - Provision hardware with GPUs
- **Section 7: OpenShift Cluster Configuration** - Configure GPU nodes and integrate with cluster

---

## 6. GPU Node Provisioning

### 5.1 Hardware Requirements Overview

Based on the model selected in Section 3, you will need to provision a GPU-enabled node with appropriate specifications. This node will be added to your OpenShift cluster as a dedicated worker for AI/ML workloads.

**Infrastructure Agnostic**: The provisioning process is specific to your infrastructure provider (AWS, Azure, GCP, VMware, bare metal, etc.). This document focuses on the OpenShift integration once the hardware is available.

### 5.2 Minimum Hardware Specifications

Provision a compute node with the following minimum specifications (adjust based on selected model from Section 3.5):

| Component | Specification | Notes |
|-----------|---------------|-------|
| **GPUs** | 4-8x NVIDIA GPUs | H100 (80GB), A100 (80GB), or A100 (40GB) depending on model |
| **GPU Memory** | 320-640 GB total | Based on model requirements (see Section 3.4) |
| **System Memory** | 512 GB - 2 TB | More is better for model loading and caching |
| **vCPUs** | 64-192 cores | For data preprocessing and system operations |
| **Storage** | 2-4 TB NVMe/SSD | Fast storage for model weights and temporary data |
| **Network** | 25-100 Gbps | High bandwidth for distributed inference |
| **OS** | RHEL CoreOS 4.20+ | Must match your OpenShift version |

### 5.3 Supported GPU Types

| GPU Model | Memory | Best For | Notes |
|-----------|--------|----------|-------|
| **NVIDIA H100** | 80 GB HBM3 | 405B models, highest performance | Recommended for production |
| **NVIDIA A100 (80GB)** | 80 GB HBM2e | 70B-405B models | Good balance of cost/performance |
| **NVIDIA A100 (40GB)** | 40 GB HBM2 | <70B models | Budget option for smaller models |
| **NVIDIA A10G** | 24 GB GDDR6 | <30B models | Development/testing only |

**Note**: This guide assumes NVIDIA GPUs. AMD GPUs (MI300X, MI250X) are also supported by OpenShift AI but require different operator configuration.

### 5.4 Reference Instance Types by Provider

For reference, here are example instance types from major cloud providers that meet the requirements:

#### AWS
- **p5.48xlarge**: 8x H100 (80GB), 640GB GPU RAM, 192 vCPUs, 2TB RAM - ~$98/hour
- **p4de.24xlarge**: 8x A100 (80GB), 640GB GPU RAM, 96 vCPUs, 1.1TB RAM - ~$41/hour
- **p4d.24xlarge**: 8x A100 (40GB), 320GB GPU RAM, 96 vCPUs, 1.1TB RAM - ~$33/hour

#### Azure
- **Standard_ND96isr_H100_v5**: 8x H100 (80GB), similar to AWS p5
- **Standard_ND96amsr_A100_v4**: 8x A100 (80GB), similar to AWS p4de

#### GCP
- **a3-highgpu-8g**: 8x H100 (80GB)
- **a2-ultragpu-8g**: 8x A100 (80GB)

#### On-Premises / Bare Metal
- Dell PowerEdge XE9680: Up to 8x H100/A100
- HPE Cray EX425: GPU-optimized node
- Supermicro SYS-421GE-TNHR: 8x GPU support

### 5.5 Provisioning Checklist

Before proceeding to Section 6, ensure your GPU node meets these criteria:

- [ ] Node is provisioned with required GPU count and memory
- [ ] Operating system is RHEL CoreOS matching OpenShift version
- [ ] Node has network connectivity to OpenShift cluster
- [ ] Node has at least 2TB fast storage attached for model weights
- [ ] Node has proper security group/firewall rules to communicate with cluster
- [ ] You have the node's hostname/IP address for cluster integration

### 5.6 Storage Considerations

**Model Weights Storage**: Plan for at least 2TB of high-performance storage:

- **Local NVMe**: Best performance for model loading (recommended)
- **Network-attached**: Acceptable if >10Gbps network bandwidth
- **Object Storage (S3/ODF)**: Used for model repository, not inference runtime

**Recommended Layout**:
```
/dev/nvme0n1  500GB   Root filesystem (RHEL CoreOS)
/dev/nvme1n1  2TB     Model weights and cache (/var/lib/vllm)
```

### 5.7 Network Requirements

The GPU node must have connectivity to:

| Destination | Port(s) | Protocol | Purpose |
|-------------|---------|----------|---------|
| OpenShift API | 6443 | TCP | Cluster API access |
| OpenShift Ingress | 80, 443 | TCP | Route traffic |
| Other worker nodes | 10250 | TCP | Kubelet |
| Other worker nodes | 9100-9999 | TCP | Metrics, monitoring |
| DNS servers | 53 | TCP/UDP | Name resolution |
| S3/Object Storage | 443 | TCP | Model repository access |

### 5.8 Next Steps

Once your GPU node is provisioned and meets all requirements in the checklist above, proceed to **Section 6: OpenShift Cluster Configuration** to integrate it into your cluster.

---

## 7. OpenShift Cluster Configuration

### 7.1 Add GPU Node to Cluster

#### Step 1: Generate MachineConfig for Ignition

The node must have correct Ignition configuration to join the cluster.

```bash
# Get bootstrap token
oc get secret -n openshift-machine-api worker-user-data \
  -o jsonpath='{.data.userData}' | base64 -d > ignition-config.json
```

#### Step 2: Approve Node CSR

```bash
# Monitor pending CSRs
watch oc get csr

# Approve CSRs from new node
oc get csr -o name | xargs oc adm certificate approve
```

#### Step 3: Verify Node Joined

```bash
# List all nodes
oc get nodes

# Verify new GPU node
oc get nodes -l node-role.kubernetes.io/worker -o wide
```

### 6.2 Label and Taint GPU Node

```bash
# Get node name
GPU_NODE=$(oc get nodes -o jsonpath='{.items[?(@.metadata.name=="ip-<PRIVATE_IP>.ec2.internal")].metadata.name}')

# Add GPU worker label
oc label node $GPU_NODE node-role.kubernetes.io/gpu-worker=true

# Add taint to dedicate node only to GPU workloads
oc adm taint node $GPU_NODE nvidia.com/gpu=present:NoSchedule

# Verify
oc describe node $GPU_NODE | grep -A5 Taints
```

### 6.3 Create MachineConfigPool for GPU Nodes

```yaml
# Save as gpu-mcp.yaml
cat <<EOF > gpu-mcp.yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfigPool
metadata:
  name: gpu-worker
spec:
  machineConfigSelector:
    matchExpressions:
      - key: machineconfiguration.openshift.io/role
        operator: In
        values:
          - worker
          - gpu-worker
  nodeSelector:
    matchLabels:
      node-role.kubernetes.io/gpu-worker: ""
  paused: false
EOF

# Apply
oc apply -f gpu-mcp.yaml

# Verify
oc get mcp gpu-worker
```

---

## 8. Red Hat OpenShift AI Installation

### 8.1 Install Node Feature Discovery Operator

#### Step 1: Create Namespace

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-nfd
EOF
```

#### Step 2: Create OperatorGroup

```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: nfd-operator-group
  namespace: openshift-nfd
spec:
  targetNamespaces:
    - openshift-nfd
EOF
```

#### Step 3: Create Subscription

```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: nfd
  namespace: openshift-nfd
spec:
  channel: stable
  name: nfd
  source: redhat-operators
  sourceNamespace: openshift-marketplace
  installPlanApproval: Automatic
EOF
```

#### Step 4: Verify Installation

```bash
# Wait for operator to be ready
oc wait --for=condition=Ready pod -l name=nfd-operator -n openshift-nfd --timeout=300s

# Verify CSV
oc get csv -n openshift-nfd
```

#### Step 5: Create NodeFeatureDiscovery Instance

```bash
cat <<EOF | oc apply -f -
apiVersion: nfd.openshift.io/v1
kind: NodeFeatureDiscovery
metadata:
  name: nfd-instance
  namespace: openshift-nfd
spec:
  operand:
    image: registry.redhat.io/openshift4/ose-node-feature-discovery:v4.20
    servicePort: 12000
  workerConfig:
    configData: |
      sources:
        pci:
          deviceClassWhitelist:
            - "0300"
            - "0302"
          deviceLabelFields:
            - "vendor"
            - "device"
EOF
```

#### Step 6: Verify GPU Detection

```bash
# Verify GPUs were detected
oc describe node $GPU_NODE | grep nvidia

# Should show something like:
# feature.node.kubernetes.io/pci-10de.present=true
# nvidia.com/gpu=8
```

### 7.2 Install NVIDIA GPU Operator

#### Step 1: Create Namespace

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: nvidia-gpu-operator
EOF
```

#### Step 2: Create OperatorGroup

```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: nvidia-gpu-operator-group
  namespace: nvidia-gpu-operator
spec:
  targetNamespaces:
    - nvidia-gpu-operator
EOF
```

#### Step 3: Create Subscription

```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: gpu-operator-certified
  namespace: nvidia-gpu-operator
spec:
  channel: v25.0
  name: gpu-operator-certified
  source: certified-operators
  sourceNamespace: openshift-marketplace
  installPlanApproval: Automatic
EOF
```

#### Step 4: Verify Installation

```bash
# Wait for operator to be ready
oc wait --for=condition=Ready pod -l app=gpu-operator -n nvidia-gpu-operator --timeout=600s

# Verify CSV
oc get csv -n nvidia-gpu-operator
```

#### Step 5: Create ClusterPolicy

```bash
cat <<EOF | oc apply -f -
apiVersion: nvidia.com/v1
kind: ClusterPolicy
metadata:
  name: gpu-cluster-policy
spec:
  operator:
    defaultRuntime: crio
    use_ocp_driver_toolkit: true
  driver:
    enabled: true
    version: "550.54.15"
    repository: nvcr.io/nvidia
    image: driver
    imagePullPolicy: IfNotPresent
    rdma:
      enabled: false
  toolkit:
    enabled: true
  devicePlugin:
    enabled: true
    version: v0.15.0
  dcgm:
    enabled: true
  dcgmExporter:
    enabled: true
    serviceMonitor:
      enabled: true
  gfd:
    enabled: true
  nodeStatusExporter:
    enabled: true
  mig:
    strategy: single
  validator:
    plugin:
      env:
        - name: WITH_WORKLOAD
          value: "true"
EOF
```

#### Step 6: Verify Driver Installation

```bash
# Verify GPU operator pods
oc get pods -n nvidia-gpu-operator

# Verify driver installed correctly
oc logs -n nvidia-gpu-operator -l app=nvidia-driver-daemonset --tail=50

# Verify device plugin
oc get pods -n nvidia-gpu-operator -l app=nvidia-device-plugin-daemonset
```

#### Step 7: Validate Available GPUs

```bash
# Verify 8 GPUs are available
oc describe node $GPU_NODE | grep -A10 "Allocatable:"

# Should show:
# nvidia.com/gpu: 8
```

### 7.3 Install Red Hat OpenShift AI Operator

#### Step 1: Create Namespace

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: redhat-ods-operator
EOF
```

#### Step 2: Create OperatorGroup

```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: redhat-ods-operator-group
  namespace: redhat-ods-operator
spec: {}
EOF
```

#### Step 3: Create Subscription

```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: rhods-operator
  namespace: redhat-ods-operator
spec:
  channel: stable-2.20
  name: rhods-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
  installPlanApproval: Automatic
EOF
```

#### Step 4: Verify Installation

```bash
# Wait for operator to be ready
oc wait --for=condition=Ready pod -l name=rhods-operator -n redhat-ods-operator --timeout=600s

# Verify CSV
oc get csv -n redhat-ods-operator
```

#### Step 5: Create DataScienceCluster

```bash
cat <<EOF | oc apply -f -
apiVersion: datasciencecluster.opendatahub.io/v1
kind: DataScienceCluster
metadata:
  name: default-dsc
spec:
  components:
    codeflare:
      managementState: Removed
    dashboard:
      managementState: Managed
    datasciencepipelines:
      managementState: Removed
    kserve:
      managementState: Managed
      serving:
        ingressGateway:
          certificate:
            type: SelfSigned
        managementState: Managed
        name: knative-serving
    modelmeshserving:
      managementState: Removed
    ray:
      managementState: Removed
    workbenches:
      managementState: Removed
EOF
```

#### Step 6: Verify Components

```bash
# Verify KServe is installed
oc get pods -n redhat-ods-applications

# Verify available serving runtimes
oc get servingruntimes -A
```

---

## 9. Model Deployment with vLLM

### 9.1 Prepare Model Weights

#### Step 1: Download the Model

You need access to Llama 3.1 405B. Two options:

**Option A: From Hugging Face**

```bash
# On a machine with internet access and sufficient storage (>1TB)
pip install huggingface-hub

# Login to Hugging Face (need to accept Meta's license)
huggingface-cli login

# Download FP8 quantized model (smaller)
huggingface-cli download meta-llama/Meta-Llama-3.1-405B-Instruct-FP8 \
  --local-dir /mnt/models/llama-3.1-405b-fp8 \
  --local-dir-use-symlinks False
```

**Option B: From Red Hat AI Model Registry** (if available with your subscription)

```bash
# Check availability in Red Hat registry
podman login registry.redhat.io
podman search registry.redhat.io/llama
```

#### Step 2: Upload Model to S3-Compatible Storage

For RHOAI, the model must be in S3-compatible storage.

**Option A: Use OpenShift Data Foundation (ODF)**

```bash
# Install ODF if not installed (out of scope for this doc)
# Create bucket for models
oc create -f - <<EOF
apiVersion: objectbucket.io/v1alpha1
kind: ObjectBucketClaim
metadata:
  name: llama-405b-models
  namespace: redhat-ods-applications
spec:
  generateBucketName: llama-405b-models
  storageClassName: openshift-storage.noobaa.io
EOF

# Get S3 credentials
oc get secret llama-405b-models -n redhat-ods-applications -o yaml

# Get endpoint
oc get configmap llama-405b-models -n redhat-ods-applications -o yaml
```

**Option B: Use AWS S3 (in connected environment)**

```bash
# Create bucket
aws s3 mb s3://airgapped-llm-models --region us-east-1

# Upload model (this may take hours due to size)
aws s3 sync /mnt/models/llama-3.1-405b-fp8/ \
  s3://airgapped-llm-models/llama-3.1-405b-fp8/ \
  --region us-east-1
```

#### Step 3: Create Data Connection in OpenShift AI

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: aws-connection-llama-models
  namespace: redhat-ods-applications
  labels:
    opendatahub.io/dashboard: "true"
    opendatahub.io/managed: "true"
  annotations:
    opendatahub.io/connection-type: s3
    openshift.io/display-name: "Llama Models S3 Storage"
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: "<YOUR_ACCESS_KEY>"
  AWS_SECRET_ACCESS_KEY: "<YOUR_SECRET_KEY>"
  AWS_S3_BUCKET: "airgapped-llm-models"
  AWS_S3_ENDPOINT: "https://s3.us-east-1.amazonaws.com"
  AWS_DEFAULT_REGION: "us-east-1"
EOF
```

### 8.2 Configure vLLM Serving Runtime

#### Step 1: Enable vLLM Runtime

```bash
cat <<EOF | oc apply -f -
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: vllm-nvidia-gpu-runtime
  namespace: redhat-ods-applications
  annotations:
    opendatahub.io/accelerator-name: nvidia-gpu
    opendatahub.io/template-display-name: "vLLM NVIDIA GPU ServingRuntime"
    opendatahub.io/template-name: vllm-nvidia-gpu-runtime
spec:
  supportedModelFormats:
    - name: pytorch
      version: "1"
      autoSelect: true
  multiModel: false
  containers:
    - name: kserve-container
      image: quay.io/modh/vllm:rhoai-2.20-cuda
      command:
        - python
        - -m
        - vllm.entrypoints.openai.api_server
      args:
        - --model
        - /mnt/models
        - --port
        - "8080"
        - --tensor-parallel-size
        - "8"
        - --dtype
        - "float8"
        - --max-model-len
        - "16384"
        - --gpu-memory-utilization
        - "0.95"
        - --trust-remote-code
      env:
        - name: HF_HOME
          value: /tmp/hf_home
      resources:
        requests:
          cpu: "24"
          memory: 200Gi
          nvidia.com/gpu: "8"
        limits:
          cpu: "96"
          memory: 400Gi
          nvidia.com/gpu: "8"
      volumeMounts:
        - name: shm
          mountPath: /dev/shm
  volumes:
    - name: shm
      emptyDir:
        medium: Memory
        sizeLimit: 12Gi
  tolerations:
    - key: nvidia.com/gpu
      operator: Exists
      effect: NoSchedule
  nodeSelector:
    node-role.kubernetes.io/gpu-worker: "true"
EOF
```

### 8.3 Create InferenceService

#### Step 1: Create Data Science Project

```bash
cat <<EOF | oc apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: llama-inference
  labels:
    opendatahub.io/dashboard: "true"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: project-metadata
  namespace: llama-inference
data:
  displayName: "Llama 3.1 405B Inference"
  description: "Production deployment of Llama 3.1 405B for OpenCode integration"
EOF
```

#### Step 2: Copy Data Connection Secret

```bash
oc get secret aws-connection-llama-models -n redhat-ods-applications -o yaml | \
  sed 's/namespace: redhat-ods-applications/namespace: llama-inference/' | \
  oc apply -f -
```

#### Step 3: Create InferenceService

```bash
cat <<EOF | oc apply -f -
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-405b
  namespace: llama-inference
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
    openshift.io/display-name: "Llama 3.1 405B Inference Service"
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      runtime: vllm-nvidia-gpu-runtime
      storage:
        key: aws-connection-llama-models
        path: llama-3.1-405b-fp8
      resources:
        requests:
          cpu: "24"
          memory: 200Gi
          nvidia.com/gpu: "8"
        limits:
          cpu: "96"
          memory: 400Gi
          nvidia.com/gpu: "8"
EOF
```

#### Step 4: Verify Deployment

```bash
# Monitor the pod
watch oc get pods -n llama-inference

# View vLLM container logs
oc logs -f -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b

# Verify service is ready
oc get inferenceservice llama-405b -n llama-inference

# Should show:
# NAME         URL                                           READY   AGE
# llama-405b   http://llama-405b.llama-inference.svc.local   True    5m
```

### 8.4 Expose the Service

#### Step 1: Create Route

```bash
cat <<EOF | oc apply -f -
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: llama-405b-route
  namespace: llama-inference
spec:
  to:
    kind: Service
    name: llama-405b-predictor
    weight: 100
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
  wildcardPolicy: None
EOF
```

#### Step 2: Get Service URL

```bash
ROUTE_URL=$(oc get route llama-405b-route -n llama-inference -o jsonpath='{.spec.host}')
echo "Llama 405B Inference Service: https://$ROUTE_URL"

# Save for OpenCode configuration
echo "https://$ROUTE_URL" > llama-405b-endpoint.txt
```

### 8.5 Test the Service

```bash
# Basic health test
curl -k https://$ROUTE_URL/health

# Inference test
curl -k https://$ROUTE_URL/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.1-405b-fp8",
    "prompt": "Explain what OpenShift is in one sentence.",
    "max_tokens": 50,
    "temperature": 0.7
  }'
```

**Expected response**:
```json
{
  "id": "cmpl-...",
  "object": "text_completion",
  "created": 1712102400,
  "model": "llama-3.1-405b-fp8",
  "choices": [
    {
      "text": "OpenShift is Red Hat's enterprise Kubernetes platform...",
      "index": 0,
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 18,
    "total_tokens": 28
  }
}
```

---

## 10. OpenCode Configuration

### 10.1 Prerequisites

```bash
# Verify OpenCode installation
claude --version

# If not installed:
npm install -g @anthropic-ai/claude-code
```

### 9.2 Configure OpenCode to Use Local Model

#### Step 1: Create Configuration File

```bash
# Create configuration directory
mkdir -p ~/.config/claude-code

# Create custom configuration
cat > ~/.config/claude-code/config.json <<EOF
{
  "providers": [
    {
      "name": "llama-405b-local",
      "type": "openai-compatible",
      "baseURL": "https://$ROUTE_URL/v1",
      "apiKey": "not-required",
      "models": [
        {
          "id": "llama-3.1-405b-fp8",
          "name": "Llama 3.1 405B (Local)",
          "maxTokens": 16384,
          "contextWindow": 128000
        }
      ],
      "default": true
    }
  ],
  "defaultModel": "llama-3.1-405b-fp8",
  "timeout": 120000,
  "verify_ssl": false
}
EOF
```

**Note**: `verify_ssl: false` is temporary for development. In production, configure valid certificates.

#### Step 2: Configure Environment Variables (Optional)

```bash
# Add to ~/.bashrc or ~/.zshrc
export CLAUDE_CODE_PROVIDER="llama-405b-local"
export CLAUDE_CODE_MODEL="llama-3.1-405b-fp8"
export CLAUDE_CODE_BASE_URL="https://$ROUTE_URL/v1"
```

### 9.3 Verify Connection

```bash
# Connectivity test
claude chat "Hello, can you confirm you're running locally on OpenShift?"

# Technical capabilities test
claude chat "List the main components of Red Hat OpenShift AI"

# Skill execution test (example)
claude exec "/health-check" --project ./agentic-collections/rh-sre
```

### 9.4 Configure OpenCode for the Repository

#### Step 1: Navigate to Repository

```bash
cd ~/agentic-collections
```

#### Step 2: Initialize OpenCode in Project

```bash
# Initialize project configuration
claude init

# Select provider: llama-405b-local
# Select model: llama-3.1-405b-fp8
```

#### Step 3: Test Repository Skills

```bash
# Test rh-sre skill
claude exec "/cve-impact" --cve CVE-2024-1234

# Test ocp-admin skill
claude exec "/cluster-report"

# Test rh-virt skill
claude exec "/vm-status"
```

---

## 11. Validation and Testing

### 11.1 Performance Testing

#### Latency Benchmark

```bash
# Benchmark script
cat > benchmark-latency.sh <<'EOF'
#!/bin/bash
ENDPOINT="https://$ROUTE_URL/v1/completions"

for i in {1..10}; do
  START=$(date +%s.%N)
  
  curl -k -s "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "llama-3.1-405b-fp8",
      "prompt": "Explain Kubernetes pods in one sentence.",
      "max_tokens": 100,
      "temperature": 0.7
    }' > /dev/null
  
  END=$(date +%s.%N)
  DURATION=$(echo "$END - $START" | bc)
  echo "Request $i: ${DURATION}s"
done
EOF

chmod +x benchmark-latency.sh
./benchmark-latency.sh
```

**Expected results**: 2-5 seconds per request with FP8 and 8x H100.

#### Throughput Test

```bash
# Test with multiple concurrent requests
cat > benchmark-throughput.sh <<'EOF'
#!/bin/bash
ENDPOINT="https://$ROUTE_URL/v1/completions"
CONCURRENT=4

parallel -j $CONCURRENT "curl -k -s '$ENDPOINT' \
  -H 'Content-Type: application/json' \
  -d '{
    \"model\": \"llama-3.1-405b-fp8\",
    \"prompt\": \"Test prompt {}\",
    \"max_tokens\": 100
  }' | jq -r '.choices[0].text'" ::: {1..20}
EOF

chmod +x benchmark-throughput.sh
./benchmark-throughput.sh
```

### 10.2 Complete Skills Testing

#### Test 1: rh-sre/cve-impact

```bash
claude chat "Using the /cve-impact skill, analyze CVE-2024-3094 (xz backdoor)"
```

**Validation**: Should generate complete impact analysis, severity, and recommendations.

#### Test 2: ocp-admin/cluster-report

```bash
claude chat "Generate a cluster health report using /cluster-report"
```

**Validation**: Should connect to cluster, collect metrics, and generate report.

#### Test 3: rh-virt/vm-deploy

```bash
claude chat "Using /vm-deploy, describe the steps to deploy a RHEL 9 VM on OpenShift Virtualization"
```

**Validation**: Should generate valid YAML and correct oc commands.

### 10.3 Long Context Test

```bash
# Test with skill requiring lots of context
claude chat "Analyze all SKILL.md files in rh-sre/skills/ and summarize their purposes"
```

**Validation**: Should process multiple files (>50K tokens) without truncating.

### 10.4 System Monitoring

#### GPU Utilization

```bash
# Inside vLLM pod
oc exec -n llama-inference -it $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) -- nvidia-smi

# Should show ~95% GPU memory utilization across 8 GPUs
```

#### vLLM Metrics

```bash
# vLLM metrics (if exposed)
curl -k https://$ROUTE_URL/metrics

# Key metrics:
# - vllm:num_requests_running
# - vllm:num_requests_waiting
# - vllm:gpu_cache_usage_perc
# - vllm:time_to_first_token_seconds
# - vllm:time_per_output_token_seconds
```

---

## 12. Security Considerations

### 12.1 Authentication and Authorization

#### Option 1: API Keys (Development)

```bash
# Create secret with API key
oc create secret generic llama-api-keys \
  -n llama-inference \
  --from-literal=api-key-1=$(openssl rand -hex 32)

# Modify InferenceService to require API key
# (Requires configuring vLLM with authentication middleware)
```

#### Option 2: OAuth2 with OpenShift OAuth (Recommended)

```bash
# Annotate service to use OAuth
oc annotate route llama-405b-route \
  -n llama-inference \
  haproxy.router.openshift.io/hsts_header="max-age=31536000;includeSubDomains;preload"

# Create ServiceAccount for OAuth
oc create sa llama-client -n llama-inference

# Grant permissions
oc adm policy add-role-to-user view system:serviceaccount:llama-inference:llama-client

# Get token
SA_TOKEN=$(oc sa get-token llama-client -n llama-inference)

# Use token in requests
curl -k -H "Authorization: Bearer $SA_TOKEN" \
  https://$ROUTE_URL/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-405b-fp8", "prompt": "Test"}'
```

### 11.2 Network Policies

```bash
cat <<EOF | oc apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: llama-inference-netpol
  namespace: llama-inference
spec:
  podSelector:
    matchLabels:
      serving.kserve.io/inferenceservice: llama-405b
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: openshift-ingress
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: openshift-apiserver
      ports:
        - protocol: TCP
          port: 443
    - to:
        - podSelector: {}
      ports:
        - protocol: TCP
          port: 53
        - protocol: UDP
          port: 53
EOF
```

### 11.3 TLS Certificates

#### Option 1: Let's Encrypt (requires public DNS)

```bash
# Install cert-manager
oc apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | oc apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: openshift-default
EOF

# Annotate route to use cert-manager
oc annotate route llama-405b-route \
  -n llama-inference \
  cert-manager.io/issuer-kind=ClusterIssuer \
  cert-manager.io/issuer-name=letsencrypt-prod
```

#### Option 2: Internal Certificate (Recommended for AirGapped)

```bash
# Generate internal CA
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
  -out ca.crt -subj "/CN=Internal CA"

# Generate certificate for the service
openssl genrsa -out llama-tls.key 2048
openssl req -new -key llama-tls.key -out llama-tls.csr \
  -subj "/CN=$ROUTE_URL"

openssl x509 -req -in llama-tls.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out llama-tls.crt -days 365 -sha256

# Create secret with certificate
oc create secret tls llama-tls-cert \
  -n llama-inference \
  --cert=llama-tls.crt \
  --key=llama-tls.key

# Modify route to use certificate
oc patch route llama-405b-route -n llama-inference \
  -p '{"spec":{"tls":{"certificate":"'"$(cat llama-tls.crt)"'","key":"'"$(cat llama-tls.key)"'"}}}'
```

### 11.4 Audit Logging

```bash
# Enable audit logging in OpenShift
cat <<EOF | oc apply -f -
apiVersion: config.openshift.io/v1
kind: APIServer
metadata:
  name: cluster
spec:
  audit:
    profile: WriteRequestBodies
EOF

# View audit logs
oc adm node-logs --role=master --path=openshift-apiserver/audit.log
```

---

## 13. Troubleshooting

### 13.1 Common Issues

#### Issue 1: Pod Won't Start - OOMKilled

**Symptom**:
```bash
oc get pods -n llama-inference
# NAME                          READY   STATUS      RESTARTS
# llama-405b-predictor-...      0/1     OOMKilled   3
```

**Solution**:
```bash
# Increase pod memory
oc edit inferenceservice llama-405b -n llama-inference

# Change:
resources:
  limits:
    memory: 600Gi  # Increase from 400Gi to 600Gi
```

#### Issue 2: GPUs Not Detected

**Symptom**:
```bash
oc logs -n llama-inference llama-405b-predictor-...
# Error: No GPUs found
```

**Solution**:
```bash
# Verify GPU operator
oc get pods -n nvidia-gpu-operator

# Restart device plugin
oc delete pod -n nvidia-gpu-operator -l app=nvidia-device-plugin-daemonset

# Verify node has GPUs
oc describe node $GPU_NODE | grep nvidia.com/gpu
```

#### Issue 3: Model Won't Download from S3

**Symptom**:
```bash
oc logs -n llama-inference llama-405b-predictor-...
# Error downloading model from S3: Access Denied
```

**Solution**:
```bash
# Verify S3 credentials
oc get secret aws-connection-llama-models -n llama-inference -o yaml

# Test access manually
oc run -it --rm debug --image=amazon/aws-cli --restart=Never -- \
  aws s3 ls s3://airgapped-llm-models/llama-3.1-405b-fp8/ \
  --region us-east-1
```

#### Issue 4: High Latency (>10s)

**Diagnosis**:
```bash
# Verify GPU utilization
oc exec -n llama-inference $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) -- nvidia-smi

# Review tensor parallelism configuration
oc get inferenceservice llama-405b -n llama-inference -o yaml | grep tensor-parallel-size

# Check vLLM logs
oc logs -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b --tail=100
```

**Solution**:
```bash
# Adjust vLLM parameters in ServingRuntime
oc edit servingruntime vllm-nvidia-gpu-runtime -n redhat-ods-applications

# Optimize:
args:
  - --max-model-len
  - "8192"  # Reduce if you don't need ultra-long context
  - --gpu-memory-utilization
  - "0.98"  # Increase utilization
```

### 12.2 Advanced Debugging

#### Access vLLM Pod

```bash
# Shell into pod
oc exec -it -n llama-inference \
  $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) \
  -- /bin/bash

# Verify loaded model
ls -lh /mnt/models/

# Verify GPUs from inside
nvidia-smi

# View Python processes
ps aux | grep vllm
```

#### Capture Traffic

```bash
# Install tcpdump in pod (for temporary debugging)
oc exec -n llama-inference \
  $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) \
  -- apt-get update && apt-get install -y tcpdump

# Capture requests
oc exec -n llama-inference \
  $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) \
  -- tcpdump -i any -s 0 -w /tmp/traffic.pcap port 8080

# Copy capture
oc cp llama-inference/$(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o jsonpath='{.items[0].metadata.name}'):/tmp/traffic.pcap ./traffic.pcap
```

### 12.3 Logs and Metrics

#### Centralize Logs

```bash
# View all llama-405b related logs
oc logs -n llama-inference --selector=serving.kserve.io/inferenceservice=llama-405b --tail=1000

# Follow logs in real-time
oc logs -f -n llama-inference --selector=serving.kserve.io/inferenceservice=llama-405b

# Export logs for analysis
oc logs -n llama-inference --selector=serving.kserve.io/inferenceservice=llama-405b --since=1h > llama-logs.txt
```

#### Prometheus Metrics (if enabled)

```bash
# Verify ServiceMonitor
oc get servicemonitor -n llama-inference

# Query in Prometheus
# vllm_request_duration_seconds
# vllm_num_requests_running
# vllm_gpu_cache_usage_perc
```

---

## 14. References

### 14.1 Official Documentation

- [Red Hat OpenShift AI Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/2.20/)
- [vLLM Official Documentation](https://docs.vllm.ai/)
- [Llama 3.1 Model Card](https://huggingface.co/meta-llama/Meta-Llama-3.1-405B-Instruct)
- [AWS P5 Instances](https://aws.amazon.com/ec2/instance-types/p5/)
- [NVIDIA GPU Operator Documentation](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [KServe Documentation](https://kserve.github.io/website/)

### 13.2 Technical Articles and Blogs

- [Installing and Deploying LLaMA 3.1 405B Into Production](https://nlpcloud.com/installing-deploying-llama-3-1-405b-into-production-on-gcp-compute-engine.html)
- [Llama 3.1 Support in vLLM](https://blog.vllm.ai/2024/07/23/llama31.html)
- [Serve and Benchmark Models with vLLM on OpenShift](https://developers.redhat.com/articles/2026/03/03/serve-and-benchmark-prithvi-models-vllm-openshift)
- [How to Deploy Language Models with Red Hat OpenShift AI](https://developers.redhat.com/articles/2025/09/10/how-deploy-language-models-red-hat-openshift-ai)
- [Autoscaling vLLM with OpenShift AI](https://developers.redhat.com/articles/2025/10/02/autoscaling-vllm-openshift-ai)

### 13.3 Code Repositories

- [eartvit/llm-on-ocp](https://github.com/eartvit/llm-on-ocp) - Deploy LLM on OpenShift
- [KempnerInstitute/distributed-inference-vllm](https://github.com/KempnerInstitute/distributed-inference-vllm) - Distributed vLLM inference

### 13.4 Mentioned Tools

- **OpenCode**: https://claude.ai/code
- **vLLM**: https://github.com/vllm-project/vllm
- **Hugging Face Hub**: https://huggingface.co/
- **AWS CLI**: https://aws.amazon.com/cli/
- **oc (OpenShift CLI)**: https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html

---

## Appendices

### Appendix A: Useful Commands Summary

```bash
# Verify cluster status
oc get nodes
oc get pods -A | grep -i gpu

# Verify RHOAI
oc get inferenceservice -A
oc get servingruntimes -A

# Model monitoring
oc logs -f -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b
oc exec -n llama-inference $(oc get pod -n llama-inference -l serving.kserve.io/inferenceservice=llama-405b -o name) -- nvidia-smi

# Test endpoint
ROUTE_URL=$(oc get route llama-405b-route -n llama-inference -o jsonpath='{.spec.host}')
curl -k https://$ROUTE_URL/health

# OpenCode
claude chat "Test message"
claude exec "/cluster-report"
```

### Appendix B: Cost Estimation

| Component | Monthly Cost (USD) |
|-----------|-------------------|
| AWS p5.48xlarge (24/7) | ~$70,800 |
| AWS p5.48xlarge (8h/day weekdays) | ~$13,400 |
| EBS Storage (2TB gp3) | ~$160 |
| S3 Storage (1TB) | ~$23 |
| Data Transfer | Variable |
| **Total (8h/day)** | **~$13,583/month** |

**Optimizations**:
- Use Spot Instances (up to 70% discount)
- Use Reserved Instances (up to 45% discount)
- Shutdown instance outside business hours

### Appendix C: Deployment Checklist

- [ ] OpenShift 4.20+ cluster installed
- [ ] AWS p5.48xlarge instance created
- [ ] GPU node added to cluster
- [ ] Node Feature Discovery Operator installed
- [ ] NVIDIA GPU Operator installed
- [ ] 8 H100 GPUs detected and available
- [ ] Red Hat OpenShift AI Operator installed
- [ ] DataScienceCluster configured
- [ ] Llama 3.1 405B model downloaded
- [ ] Model uploaded to S3-compatible storage
- [ ] Data Connection created
- [ ] vLLM ServingRuntime configured
- [ ] InferenceService deployed
- [ ] vLLM pod in Running state
- [ ] Route exposed and accessible
- [ ] Inference test successful
- [ ] OpenCode configured
- [ ] Repository skills tested

---

**End of Document**

Version: 1.0  
Last updated: 2026-04-03  
Maintainer: Agentic Collections Team

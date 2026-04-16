# Part 1: Context and Preparation

Understanding the air-gapped deployment architecture, selecting the right model, and preparing your infrastructure.

---

**📚 Documentation Navigation:**
- **[← Back to Index](./index.md)**
- **[Next: Installation Guide →](./installation.md)**

---

## Table of Contents

1. [Context and Purpose](#1-context-and-purpose)
   - 1.1 [Air-Gapped Environment: Advantages and Disadvantages](#11-air-gapped-environment-advantages-and-disadvantages)
   - 1.2 [Deployment Objective](#12-deployment-objective)
   - 1.3 [Use Case](#13-use-case)
2. [Solution Architecture](#2-solution-architecture)
   - 2.1 [Architecture Diagram](#21-architecture-diagram)
   - 2.2 [Data Flow](#22-data-flow)
   - 2.3 [Main Components](#23-main-components)
3. [Model Selection and Testing](#3-model-selection-and-testing)
   - 3.1 [Testing Strategy](#31-testing-strategy)
   - 3.2 [Test Cases for Evaluation](#32-test-cases-for-evaluation)
   - 3.3 [Selected Model and Justification](#33-selected-model-and-justification)
   - 3.4 [OpenShift Cluster Requirements](#34-openshift-cluster-requirements)
4. [Red Hat Components](#4-red-hat-components)
5. [Operator Installation](#5-operator-installation)

---

## 1. Context and Purpose

### 1.1 Air-Gapped Environment: Advantages and Disadvantages

An **air-gapped** environment is a network that is physically isolated from unsecured networks, including the public internet. Understanding the trade-offs is crucial for planning your deployment.

#### Advantages

**Security Benefits:**
- **Zero External Attack Surface**: No internet connectivity eliminates entire classes of remote attacks
- **Data Exfiltration Prevention**: Sensitive data cannot leave the network via internet channels
- **Compliance Alignment**: Meets strict regulatory requirements (FedRAMP High, DoD IL5, HIPAA, PCI-DSS Level 1)
- **Intellectual Property Protection**: Model weights, training data, and inference queries remain completely private

**Operational Control:**
- **Total Infrastructure Control**: No dependency on external service availability or pricing changes
- **Predictable Performance**: Network latency and bandwidth are fully controlled
- **Version Stability**: Updates and changes happen only when you decide
- **Audit Trail**: Complete visibility into all system interactions

**Strategic Value:**
- **Vendor Independence**: No lock-in to cloud provider AI services
- **Cost Predictability**: Fixed infrastructure costs vs. variable API pricing
- **Data Sovereignty**: Full compliance with data residency requirements
- **Custom Model Management**: Deploy any model without third-party approval

#### Disadvantages

**Implementation Complexity:**
- **Initial Setup Overhead**: Requires careful planning for image mirroring, package repositories
- **Update Management**: Manual processes for patching, updating operators and models
- **Troubleshooting Difficulty**: Cannot easily access external documentation or support during outages
- **Expertise Requirements**: Team must have deep knowledge of offline operations

**Operational Challenges:**
- **Model Acquisition**: Manual process to download and transfer large model files (100GB-1TB+)
- **Dependency Management**: All software dependencies must be pre-staged and mirrored
- **Limited Ecosystem**: Cannot leverage cloud-native services (managed databases, observability SaaS)
- **Slower Innovation Cycle**: Delayed access to latest models and features

**Resource Constraints:**
- **Higher Hardware Costs**: Must provision for peak capacity, cannot burst to cloud
- **Storage Overhead**: Need local copies of all images, models, and artifacts
- **Skill Redundancy**: Cannot rely on external consultants for emergency support
- **Testing Limitations**: Difficult to test integrations with external services

**Common Use Cases Where Benefits Outweigh Costs:**
- Government and defense applications
- Financial services handling sensitive transactions
- Healthcare systems with patient data
- Industrial control systems (SCADA, manufacturing)
- Research institutions with proprietary data

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
│  │  Hardware: GPU-enabled compute node                      │  │
│  │  - NVIDIA GPUs (quantity/type based on model)           │  │
│  │  - Sufficient GPU memory for inference                   │  │
│  │  - High-speed network connectivity                       │  │
│  │  - Fast local storage for model weights                  │  │
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

### 3.2 Test Cases for Evaluation

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

### 3.3 Selected Model and Justification

**Note**: This section will be completed after evaluation is finished.

**Selection will be based on:**

1. **Capability**: Can it execute all repository skills successfully?
2. **Performance**: Does it meet the <5s latency requirement for typical requests?
3. **Cost**: What is the total cost of ownership (instance + operational)?
4. **Reliability**: Does it produce consistent, high-quality results?
5. **Maintainability**: How easy is it to deploy, update, and troubleshoot?

**Current Status**: Testing in progress

### 3.4 OpenShift Cluster Requirements

Regardless of model selection, the OpenShift cluster will have:

#### Existing Infrastructure
- **3 Master Nodes**: Control plane (HA)
- **N Worker Nodes**: General workloads

#### GPU Node Configuration (to be provisioned)
- **Node Type**: Physical or virtual machine with NVIDIA GPUs (quantity and type based on model selection)
- **Taints**: `nvidia.com/gpu=present:NoSchedule` (dedicated for GPU workloads)
- **Labels**: `node-role.kubernetes.io/gpu-worker=true`
- **Storage**: Sufficient fast storage for model weights (typically 1-4TB depending on model)

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

## 5. Operator Installation

This section provides step-by-step instructions to install required operators for LLM deployment on OpenShift.

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

Once all operators are verified and running, proceed to [Installation Guide →](./installation.md) for cluster configuration and model deployment.

---

✅ You should now understand:
- The air-gapped deployment architecture
- Model selection criteria and testing approach
- Required Red Hat components and operators
- Hardware provisioning requirements

**Next Steps:**
1. Ensure you have GPU-enabled nodes provisioned and ready
2. Proceed to [Installation Guide →](./installation.md) for step-by-step deployment

---

**[← Back to Index](./index.md)** | **[Next: Installation Guide →](./installation.md)**

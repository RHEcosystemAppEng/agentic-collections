# Part 2: Installation Guide

Step-by-step instructions for deploying LLMs on OpenShift in an air-gapped environment.

---

**📚 Documentation Navigation:**
- **[← Previous: Context and Preparation](./context-and-preparation.md)**
- **[Back to Index](./index.md)**
- **[Next: Testing and Results →](./testing-and-results.md)**

---

## Table of Contents

1. [OpenShift Cluster Configuration](#7-openshift-cluster-configuration)
2. [Red Hat OpenShift AI Installation](#8-red-hat-openshift-ai-installation)
3. [Model Deployment with vLLM](#9-model-deployment-with-vllm)

---

## Prerequisites Checklist

Before proceeding, ensure you have completed:

- [ ] Read Part 1: Context and Preparation
- [ ] OpenShift cluster 4.20+ is accessible
- [ ] `oc` CLI authenticated as cluster-admin
- [ ] Required operators verified/installed (NFD, GPU Operator, RHOAI)
- [ ] GPU node provisioned and ready to join cluster
- [ ] S3-compatible storage configured for model weights
- [ ] Network connectivity validated

**Not ready?** Go back to [Context and Preparation](./context-and-preparation.md)

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


---

## 📍 Navigation

**You've completed Part 2: Installation Guide**

✅ You should now have:
- GPU nodes integrated into OpenShift cluster
- All required operators installed and running
- DataScienceCluster configured
- LLM model deployed with vLLM
- InferenceService accessible via route

**Next Steps:**
1. Note down your model route URL
2. Proceed to [Testing and Results →](./testing-and-results.md) to validate deployment

---

**[← Previous: Context and Preparation](./context-and-preparation.md)** | **[Back to Index](./index.md)** | **[Next: Testing and Results →](./testing-and-results.md)**

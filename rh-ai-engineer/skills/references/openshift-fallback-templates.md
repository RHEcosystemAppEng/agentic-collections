---
title: OpenShift Fallback Templates
category: references
tags: [openshift, fallback, yaml-templates, resilience]
semantic_keywords: [OpenShift MCP fallback, RHOAI alternative, direct Kubernetes API, resource creation templates]
use_cases: [ds-project-setup, model-deploy, workbench-manage, pipeline-manage, serving-runtime-config, model-registry]
last_updated: 2026-03-23
---

# OpenShift Fallback Templates

YAML templates for creating RHOAI resources directly via the OpenShift MCP server (`resources_create_or_update`). Use these when the RHOAI MCP tool for the operation is unavailable or returns an error.

All templates use placeholder values in `[BRACKETS]` that must be replaced with actual values.

## Data Science Project (Namespace)

**Replaces**: `create_data_science_project` (from rhoai)

**MCP Tool**: `resources_create_or_update` (from openshift)

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: [PROJECT_NAME]
  labels:
    opendatahub.io/dashboard: "true"
    kubernetes.io/metadata.name: [PROJECT_NAME]
  annotations:
    openshift.io/display-name: [DISPLAY_NAME]
    openshift.io/description: [DESCRIPTION]
```

**Listing projects** (replaces `list_data_science_projects`):

**MCP Tool**: `resources_list` (from openshift)
- `apiVersion`: `v1`, `kind`: `Namespace`, `labelSelector`: `opendatahub.io/dashboard=true`

## S3 Data Connection Secret

**Replaces**: `create_s3_data_connection` (from rhoai)

**MCP Tool**: `resources_create_or_update` (from openshift)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: [CONNECTION_NAME]
  namespace: [NAMESPACE]
  labels:
    opendatahub.io/dashboard: "true"
    opendatahub.io/managed: "true"
  annotations:
    opendatahub.io/connection-type: s3
    openshift.io/display-name: [DISPLAY_NAME]
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: [ACCESS_KEY]
  AWS_SECRET_ACCESS_KEY: [SECRET_KEY]
  AWS_S3_BUCKET: [BUCKET_NAME]
  AWS_S3_ENDPOINT: [ENDPOINT_URL]
  AWS_DEFAULT_REGION: [REGION]
```

**Listing data connections** (replaces `list_data_connections`):

**MCP Tool**: `resources_list` (from openshift)
- `apiVersion`: `v1`, `kind`: `Secret`, `namespace`: `[NAMESPACE]`, `labelSelector`: `opendatahub.io/dashboard=true`
- Filter results by annotation `opendatahub.io/connection-type: s3`

## InferenceService (vLLM)

**Replaces**: `deploy_model` (from rhoai) for vLLM deployments

**MCP Tool**: `resources_create_or_update` (from openshift)

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: [MODEL_NAME]
  namespace: [NAMESPACE]
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
    openshift.io/display-name: [DISPLAY_NAME]
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: [SERVING_RUNTIME_NAME]
      storageUri: "hf://[HF_MODEL_ID]"
      resources:
        limits:
          cpu: "[CPU_LIMIT]"
          memory: "[MEMORY_LIMIT]"
          nvidia.com/gpu: "[GPU_COUNT]"
        requests:
          cpu: "[CPU_REQUEST]"
          memory: "[MEMORY_REQUEST]"
          nvidia.com/gpu: "[GPU_COUNT]"
    tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
      - key: "ai-app"
        operator: "Equal"
        value: "true"
        effect: "NoSchedule"
    # Add additional tolerations for cluster-specific taints as needed
```

**Key notes:**
- `storageUri` uses `hf://` for HuggingFace models (no auth required for public models)
- Always include GPU tolerations — production GPU nodes are almost always tainted
- Add cluster-specific tolerations discovered via `resources_list` Nodes
- The `deploymentMode: RawDeployment` annotation is typical; use `Serverless` if Knative is available and TrustyAI payload logging is needed

## InferenceService (NIM)

**Replaces**: `deploy_model` (from rhoai) for NIM deployments — the RHOAI tool does not support NIM-specific env vars, image pull secrets, or the `nim://` URI scheme

**MCP Tool**: `resources_create_or_update` (from openshift)

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: [MODEL_NAME]
  namespace: [NAMESPACE]
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
    openshift.io/display-name: [DISPLAY_NAME]
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: [NIM_SERVING_RUNTIME_NAME]
      resources:
        limits:
          cpu: "[CPU_LIMIT]"
          memory: "[MEMORY_LIMIT]"
          nvidia.com/gpu: "[GPU_COUNT]"
        requests:
          cpu: "[CPU_REQUEST]"
          memory: "[MEMORY_REQUEST]"
          nvidia.com/gpu: "[GPU_COUNT]"
    containers:
      - name: kserve-container
        image: "nvcr.io/nim/meta/[NIM_MODEL_IMAGE]:[TAG]"
        env:
          - name: NGC_API_KEY
            valueFrom:
              secretKeyRef:
                name: ngc-api-key
                key: NGC_API_KEY
          - name: NIM_MAX_MODEL_LEN
            value: "[MAX_MODEL_LEN]"
        resources:
          limits:
            nvidia.com/gpu: "[GPU_COUNT]"
    imagePullSecrets:
      - name: ngc-image-pull-secret
    tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
```

**Key notes:**
- NIM requires NGC API key secret and image pull secret (created by `/nim-setup`)
- Use a specific image tag (e.g., `1.8.3`) instead of `latest` to avoid CUDA driver incompatibility
- `NIM_MAX_MODEL_LEN` prevents KV cache OOM (default can be too high; use `16384` for T4 GPUs)

## Toleration Post-Deploy Patch

**When**: After `deploy_model` (from rhoai) succeeds but the pod is stuck Pending due to GPU node taints

**Step 1**: Discover taints on GPU nodes:

**MCP Tool**: `resources_list` (from openshift)
- `apiVersion`: `v1`, `kind`: `Node`, `labelSelector`: `nvidia.com/gpu.present=true`

Extract `.spec.taints[]` from each node to identify required tolerations.

**Step 2**: Patch InferenceService with tolerations:

**MCP Tool**: `resources_create_or_update` (from openshift)

Merge the tolerations into `spec.predictor.tolerations` of the existing InferenceService.

## Notebook CR (Workbench)

**Replaces**: `create_workbench` (from rhoai)

**MCP Tool**: `resources_create_or_update` (from openshift)

```yaml
apiVersion: kubeflow.org/v1
kind: Notebook
metadata:
  name: [WORKBENCH_NAME]
  namespace: [NAMESPACE]
  labels:
    app: [WORKBENCH_NAME]
    opendatahub.io/dashboard: "true"
    opendatahub.io/odh-managed: "true"
  annotations:
    notebooks.opendatahub.io/inject-oauth: "true"
    opendatahub.io/image-display-name: [IMAGE_DISPLAY_NAME]
    openshift.io/display-name: [DISPLAY_NAME]
spec:
  template:
    spec:
      containers:
        - name: [WORKBENCH_NAME]
          image: [FULL_IMAGE_REFERENCE]
          resources:
            limits:
              cpu: "[CPU_LIMIT]"
              memory: "[MEMORY_LIMIT]"
            requests:
              cpu: "[CPU_REQUEST]"
              memory: "[MEMORY_REQUEST]"
          volumeMounts:
            - mountPath: /opt/app-root/src
              name: [WORKBENCH_NAME]
          env:
            - name: NOTEBOOK_ARGS
              value: "--ServerApp.port=8888 --ServerApp.token='' --ServerApp.password='' --ServerApp.base_url=/notebook/[NAMESPACE]/[WORKBENCH_NAME]"
      volumes:
        - name: [WORKBENCH_NAME]
          persistentVolumeClaim:
            claimName: [PVC_NAME]
```

**Key notes:**
- `[FULL_IMAGE_REFERENCE]` must come from ImageStream lookup (see below), NOT from `list_notebook_images`
- The `inject-oauth: "true"` annotation enables OpenShift OAuth proxy

## Notebook Image Discovery (ImageStream Lookup)

**Replaces**: `list_notebook_images` (from rhoai) — the RHOAI tool returns hardcoded incorrect image names

**Step 1**: List notebook ImageStreams:

**MCP Tool**: `resources_list` (from openshift)
- `apiVersion`: `image.openshift.io/v1`, `kind`: `ImageStream`, `namespace`: `redhat-ods-applications`
- `labelSelector`: `opendatahub.io/notebook-image=true`

**Step 2**: Get details for each ImageStream:

**MCP Tool**: `resources_get` (from openshift)

Extract from each ImageStream:
- `.metadata.name` — the actual image name (e.g., `pytorch`, NOT `jupyter-pytorch-notebook`)
- `.spec.tags[].name` — available tags (e.g., `2024.1`, `2024.2`)
- `.spec.tags[].annotations["opendatahub.io/notebook-image-name"]` — display name
- `.spec.tags[].from.name` — the full image reference to use in Notebook CR

**Step 3**: Present to user in a table:

| Image | Tag | Display Name |
|-------|-----|-------------|
| pytorch | 2024.1 | PyTorch |
| tensorflow | 2024.1 | TensorFlow |
| minimal-notebook | 2024.1 | Standard Data Science |

## Workbench Start/Stop (Annotation Patch)

**Replaces**: `start_workbench` / `stop_workbench` / `manage_resource(action=stop)` (from rhoai)

**Stop workbench**:

**MCP Tool**: `resources_create_or_update` (from openshift)

Patch the Notebook CR to add the stop annotation:
```yaml
metadata:
  annotations:
    kubeflow-resource-stopped: "true"
```

**Start workbench**:

**MCP Tool**: `resources_create_or_update` (from openshift)

Patch the Notebook CR to remove the stop annotation by setting it to empty string or removing it:
```yaml
metadata:
  annotations:
    kubeflow-resource-stopped: null
```

If `resources_create_or_update` cannot remove annotations, use the full Notebook CR manifest without the `kubeflow-resource-stopped` annotation.

## PVC for Workbench Storage

**Replaces**: `create_storage` (from rhoai)

**MCP Tool**: `resources_create_or_update` (from openshift)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: [PVC_NAME]
  namespace: [NAMESPACE]
  labels:
    opendatahub.io/dashboard: "true"
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: [SIZE]
```

**Listing PVCs** (replaces `list_storage`):

**MCP Tool**: `resources_list` (from openshift)
- `apiVersion`: `v1`, `kind`: `PersistentVolumeClaim`, `namespace`: `[NAMESPACE]`

## DataSciencePipelinesApplication (DSPA)

**Replaces**: `create_pipeline_server` (from rhoai) — the RHOAI tool constructs an invalid manifest that returns "Unprocessable Entity"

**MCP Tool**: `resources_create_or_update` (from openshift)

```yaml
apiVersion: datasciencepipelinesapplications.opendatahub.io/v1alpha1
kind: DataSciencePipelinesApplication
metadata:
  name: dspa
  namespace: [NAMESPACE]
spec:
  dspVersion: v2
  objectStorage:
    disableHealthCheck: false
    enableExternalRoute: false
    externalStorage:
      bucket: [BUCKET_NAME]
      host: [S3_HOST_WITHOUT_PROTOCOL]
      port: ""
      s3CredentialsSecret:
        accessKey: AWS_ACCESS_KEY_ID
        secretKey: AWS_SECRET_ACCESS_KEY
        secretName: [DATA_CONNECTION_SECRET_NAME]
      scheme: [http_or_https]
      region: [REGION]
```

**Key notes:**
- `host` must NOT include protocol prefix — use `minio.namespace.svc:9000` not `http://minio.namespace.svc:9000`
- `scheme` is separate: `http` or `https`
- `secretName` references the S3 data connection secret created earlier
- `s3CredentialsSecret` key names (`accessKey`, `secretKey`) are the keys inside the secret, not the actual credentials

**Checking DSPA status** (replaces `get_pipeline_server`):

**MCP Tool**: `resources_get` (from openshift)
- `apiVersion`: `datasciencepipelinesapplications.opendatahub.io/v1alpha1`, `kind`: `DataSciencePipelinesApplication`, `name`: `dspa`, `namespace`: `[NAMESPACE]`
- Check `.status.conditions` for `Ready=True`

## ServingRuntime

**Replaces**: `create_serving_runtime` (from rhoai)

**Listing runtimes** (replaces `list_serving_runtimes`):

**MCP Tool**: `resources_list` (from openshift)
- Namespace-scoped: `apiVersion`: `serving.kserve.io/v1alpha1`, `kind`: `ServingRuntime`, `namespace`: `[NAMESPACE]`
- Platform templates: `apiVersion`: `serving.kserve.io/v1alpha1`, `kind`: `ClusterServingRuntime`

Filter by label `opendatahub.io/dashboard: "true"` and check `spec.supportedModelFormats` for compatibility.

## InferenceService Status Lookup

**Replaces**: `get_inference_service` / `get_model_endpoint` (from rhoai)

**MCP Tool**: `resources_get` (from openshift)
- `apiVersion`: `serving.kserve.io/v1beta1`, `kind`: `InferenceService`, `name`: `[MODEL_NAME]`, `namespace`: `[NAMESPACE]`

Extract:
- `.status.conditions` — check for `Ready=True`
- `.status.url` — the inference endpoint URL
- `.status.components.predictor.url` — the predictor URL

**Listing InferenceServices** (replaces `list_inference_services`):

**MCP Tool**: `resources_list` (from openshift)
- `apiVersion`: `serving.kserve.io/v1beta1`, `kind`: `InferenceService`, `namespace`: `[NAMESPACE]`

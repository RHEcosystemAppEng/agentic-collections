---
title: Common Issues Across Skills
category: references
tags: [troubleshooting, gpu, oom, image-pull, rbac, common-issues, rhoai-mcp, tolerations, notebook-images, pipeline-server]
semantic_keywords: [GPU scheduling failure, OOMKilled, image pull error, RBAC permissions, common deployment errors, RHOAI MCP authentication, notebook image mismatch, model registry DNS, GPU tolerations, dangerous operations disabled]
use_cases: [model-deploy, debug-inference, workbench-manage, nim-setup, serving-runtime-config, ds-project-setup, pipeline-manage, model-registry, guardrails-config, model-monitor]
last_updated: 2026-03-23
---

# Common Issues Across Skills

Shared troubleshooting patterns that apply to multiple rh-ai-engineer skills. Individual skills reference this document and add skill-specific issues inline.

## GPU Scheduling Failure

**Applies to**: `/model-deploy`, `/debug-inference`, `/workbench-manage`, `/guardrails-config`

**Error**: Pod stuck in Pending with events showing "Insufficient nvidia.com/gpu"

**Cause**: Cluster does not have enough available GPUs of the required type.

**Solution:**
1. Check GPU availability: `get_gpu_info` from ai-observability (if available) or inspect node resources via `resources_get`
2. Reduce GPU request or use a quantized model variant
3. Check if other workloads are consuming GPU resources
4. Verify GPU Operator and NFD Operator are healthy
5. Consider using fewer GPUs with `--tensor-parallel-size` reduction and quantization

## OOMKilled During Model or Workbench Loading

**Applies to**: `/model-deploy`, `/debug-inference`, `/guardrails-config`

**Error**: Pod terminated with OOMKilled exit code, often during initial model weight loading

**Cause**: Model requires more memory than allocated in resource requests/limits. Common with large models or when `--max-model-len` is set too high.

**Solution:**
1. Increase memory limits in the InferenceService or workbench spec
2. Reduce `--max-model-len` to lower KV cache memory usage
3. Use a quantized model variant (AWQ/GPTQ/FP8) to reduce memory footprint
4. Verify GPU VRAM is sufficient using `get_gpu_info`
5. Consult [known-model-profiles.md](../../docs/references/known-model-profiles.md) for correct resource sizing

## Image Pull Error from nvcr.io (NIM)

**Applies to**: `/model-deploy`, `/nim-setup`

**Error**: Pod fails with `ErrImagePull` or `ImagePullBackOff` for NIM container images referencing `nvcr.io`

**Cause**: NGC image pull secret is missing, expired, or not in the correct namespace.

**Solution:**
1. Verify NGC pull secret exists in the target namespace: `resources_get` for the secret
2. Check that the secret contains valid docker credentials for `nvcr.io`
3. Re-run `/nim-setup` to recreate credentials with a fresh NGC API key
4. Ensure the secret is referenced by the ServiceAccount or Account CR

## Image Pull Error from OCI Registries

**Applies to**: `/model-deploy`, `/serving-runtime-config`

**Error**: Pod fails with `ErrImagePull` or `ImagePullBackOff` with `unauthorized` message for `registry.redhat.io/rhelai1/*` or custom container images

**Cause**: OCI model images or custom container images require authentication credentials not available in the namespace.

**Solution:**
1. For `registry.redhat.io/rhelai1/*` models: switch to HuggingFace source (`hf://`) which requires no authentication -- this is the recommended default for public models
2. If OCI source is required: verify entitlements are included in the pull secret
3. For custom images: create an image pull secret and link it to the default ServiceAccount (`oc secrets link default <secret-name> --for=pull`)
4. Verify the image URI and tag are correct

## RBAC / Permission Errors

**Applies to**: All skills that create or modify Kubernetes resources (including `/model-monitor`, `/guardrails-config`)

**Error**: API call returns 403 Forbidden or "insufficient permissions" message

**Cause**: The service account or user credentials in KUBECONFIG lack the required RBAC roles for the target resource type and namespace.

**Solution:**
1. Report the specific permission error to the user
2. Identify the required role: which API group, resource, and verb is needed
3. Suggest contacting the cluster administrator to grant the necessary RoleBinding or ClusterRoleBinding
4. For namespace-scoped operations: verify the user has at least `edit` role in the target namespace

## RHOAI MCP Authentication Failures

**Applies to**: All skills that use RHOAI MCP tools

**Error**: RHOAI MCP tools return "Unauthorized" (HTTP 401/403) for most operations

**Cause**: The RHOAI MCP server may use a different authentication mechanism than the user's `oc` token, or the token may have expired. This was observed to cause a 78% failure rate across RHOAI tool calls in testing.

**Solution:**
1. Skills attempt OpenShift MCP fallback automatically when RHOAI tools fail
2. **Inform the user** about the auth failure and suggest verifying their token:
   - "Note: RHOAI tool returned Unauthorized. Falling back to OpenShift direct API. If you experience further issues, try `oc login` to refresh your token."
3. If you want to restore RHOAI MCP functionality:
   - Re-login with `oc login` to refresh the token
   - Verify `RHOAI_MCP_KUBECONFIG_PATH` points to a valid, current kubeconfig
   - Restart Claude Code to reload MCP server connections
3. All RHOAI operations have OpenShift equivalents — see [openshift-fallback-templates.md](openshift-fallback-templates.md)

## RHOAI MCP API Inconsistencies

**Applies to**: `/ds-project-setup`, `/workbench-manage`, `/pipeline-manage`

**Error**: Various RHOAI MCP tool failures:
- `get_project_details` requires `name` parameter but agent may pass `namespace`
- `manage_resource(action=stop)` returns "Unsupported Media Type"
- `create_pipeline_server` returns "Unprocessable Entity" (invalid DSPA manifest)

**Cause**: RHOAI MCP tool parameter naming differs from Kubernetes conventions, and some tools construct invalid resource manifests.

**Solution:**
1. `get_project_details`: Always use the `name` parameter (not `namespace`). On error, fall back to `resources_get` for the Namespace.
2. `manage_resource(stop/start)`: Use the annotation-patch fallback — patch the Notebook CR annotation `kubeflow-resource-stopped` via OpenShift MCP.
3. `create_pipeline_server`: **Do not use this tool.** Always create DSPA CRs directly via `resources_create_or_update` with the correct YAML template from [openshift-fallback-templates.md](openshift-fallback-templates.md#datasciencepipelinesapplication-dspa).

## Notebook Image Names Mismatch

**Applies to**: `/workbench-manage`

**Error**: `list_notebook_images` (from rhoai) returns image names like `jupyter-pytorch-notebook:2024.1` that don't exist in the internal registry. The actual ImageStream is named `pytorch` (not `jupyter-pytorch-notebook`).

**Cause**: The RHOAI MCP tool returns hardcoded display names instead of the actual ImageStream names from the cluster.

**Solution:**
- **Do not use `list_notebook_images`.** This tool is permanently replaced.
- Use the ImageStream lookup pattern via OpenShift MCP:
  1. `resources_list` ImageStreams in `redhat-ods-applications` namespace with label `opendatahub.io/notebook-image=true`
  2. `resources_get` each ImageStream to extract actual tag names and image references
- See [openshift-fallback-templates.md](openshift-fallback-templates.md#notebook-image-discovery-imagestream-lookup) for the complete pattern.

## Model Registry Internal DNS Unreachable

**Applies to**: `/model-registry`

**Error**: `list_registered_models` and other Model Registry RHOAI tools fail with connection errors or return 404

**Cause**: The RHOAI MCP server runs outside the cluster and cannot resolve cluster-internal DNS names (e.g., `modelregistry-sample.rhoai-model-registries.svc.cluster.local`). Additionally, external routes may be behind an OAuth proxy.

**Solution:**
1. Check if an external Route exists for the model registry: `resources_list` Routes in the model registry namespace
2. If no Route exists, set up port-forwarding: `oc port-forward svc/modelregistry-sample 8085:8085 -n rhoai-model-registries`
3. If an OAuth proxy blocks the Route, obtain a token via `oc whoami -t` and pass it as a Bearer token
4. For registry CRUD operations, use `resources_create_or_update` / `resources_get` / `resources_list` via OpenShift MCP for RegisteredModel, ModelVersion, and ModelArtifact CRs

## Deploy Model Missing GPU Tolerations

**Applies to**: `/model-deploy`, `/debug-inference`

**Error**: Model pod stuck in Pending state after `deploy_model` succeeds. Events show "0/N nodes are available: ... node(s) had untolerated taint"

**Cause**: The `deploy_model` RHOAI tool does not accept toleration or nodeSelector parameters. In production clusters, GPU nodes are almost always tainted (common taints: `nvidia.com/gpu`, `ai-app=true`, `ai-node=big`).

**Solution:**
1. After `deploy_model` completes, check GPU node taints: `resources_list` Nodes with label `nvidia.com/gpu.present=true`
2. If taints are found, patch the InferenceService to add tolerations via `resources_create_or_update`:
   ```yaml
   spec:
     predictor:
       tolerations:
         - key: "nvidia.com/gpu"
           operator: "Exists"
           effect: "NoSchedule"
         # Add cluster-specific taints discovered from node inspection
   ```
3. Delete the stuck pod to force rescheduling with new tolerations
4. See [openshift-fallback-templates.md](openshift-fallback-templates.md#toleration-post-deploy-patch) for the complete pattern

## Dangerous Operations Disabled in RHOAI MCP

**Applies to**: `/workbench-manage`

**Error**: `delete_workbench` and `manage_resource(action=delete)` return "Dangerous operations are disabled"

**Cause**: The RHOAI MCP server has a safety flag that blocks all destructive operations by default.

**Solution:**
1. Use `resources_delete` from the OpenShift MCP server instead
2. Always apply human-in-the-loop confirmation before deleting (display resource name, warn about data loss)
3. For workbench deletion, warn that associated PVC data may be lost if the PVC is also deleted

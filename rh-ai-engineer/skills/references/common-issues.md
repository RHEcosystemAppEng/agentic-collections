---
title: Common Issues Across Skills
category: references
tags: [troubleshooting, gpu, oom, image-pull, rbac, common-issues]
semantic_keywords: [GPU scheduling failure, OOMKilled, image pull error, RBAC permissions, common deployment errors]
use_cases: [model-deploy, debug-inference, workbench-manage, nim-setup, serving-runtime-config]
last_updated: 2026-03-12
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
5. Consult [known-model-profiles.md](known-model-profiles.md) for correct resource sizing

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

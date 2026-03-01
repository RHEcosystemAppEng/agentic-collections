---
title: Supported Serving Runtimes
category: references
tags: [runtimes, vllm, nim, caikit, tgis, serving]
semantic_keywords: [serving runtime selection, model format compatibility, inference runtime comparison]
use_cases: [model-deploy, serving-runtime-config, nim-setup]
last_updated: 2026-02-26
---

# Supported Serving Runtimes

This document maps each serving runtime available on Red Hat OpenShift AI to its capabilities, supported model formats, and selection criteria. Used by `/model-deploy` to determine the appropriate runtime for a given model.

## Runtime Comparison

| Runtime | API Type | Model Format | GPU Support | License | Setup Required |
|---------|----------|-------------|-------------|---------|----------------|
| vLLM | OpenAI-compatible REST | vLLM | NVIDIA, Intel Gaudi, CPU | Open-source (Apache 2.0) | None (built-in) |
| NVIDIA NIM | OpenAI-compatible REST | NIM (TensorRT-LLM) | NVIDIA only | NVIDIA AI Enterprise | `/nim-setup` |
| Caikit+TGIS | gRPC | Caikit | NVIDIA | Red Hat (built-in) | Model conversion |
| Custom | Varies | Varies | Varies | Varies | `/serving-runtime-config` |

## vLLM

**Default runtime for most open-source models.**

- **API**: OpenAI-compatible REST (`/v1/completions`, `/v1/chat/completions`)
- **Model formats**: HuggingFace Transformers, AWQ, GPTQ, FP8 quantized
- **GPU support**: NVIDIA (CUDA), Intel Gaudi (HPU), CPU (limited)
- **Model source**: S3-compatible storage, OCI registry, PVC, URI
- **Key features**:
  - Broad model compatibility (Llama, Granite, Mixtral, Mistral, Falcon, etc.)
  - PagedAttention for efficient memory management
  - Tensor parallelism for multi-GPU inference
  - Tool/function calling support (`--tool-call-parser`)
  - Continuous batching for high throughput
- **When to choose**: Default choice for any open-source LLM. Best balance of compatibility and performance.
- **ServingRuntime CR name**: Check available runtimes with `resources_list` for `ServingRuntime` resources with `vLLM` in the name

## NVIDIA NIM

**Optimized inference for NVIDIA GPUs with TensorRT-LLM.**

- **API**: OpenAI-compatible REST
- **Model formats**: Pre-optimized TensorRT-LLM engines from NGC catalog
- **GPU support**: NVIDIA only (requires specific GPU models per model profile)
- **Model source**: NGC model catalog (pulled automatically via NGC credentials)
- **Prerequisites**: `/nim-setup` must be completed first (NGC secrets, Account CR)
- **Key features**:
  - TensorRT-LLM optimization for lower latency
  - Pre-compiled model engines (no compilation on first load)
  - Optimized and generic profiles per GPU type
  - Automatic model download from NGC
- **When to choose**: When maximum inference performance on NVIDIA GPUs is required and the model is available in the NGC catalog.
- **Limitations**: NVIDIA GPUs only, requires NVIDIA AI Enterprise license, limited model selection compared to vLLM
- **ServingRuntime CR name**: Created automatically by the NIM Account CR. Check with `resources_list` for `ServingRuntime` resources with `nim` in the name.
- **CRDs**: Account (`nim.opendatahub.io/v1`) manages NIM platform state

## Caikit+TGIS

**Red Hat's Caikit format with Text Generation Inference Server.**

- **API**: gRPC (not REST)
- **Model formats**: Caikit format (requires conversion from HuggingFace)
- **GPU support**: NVIDIA
- **Model source**: S3-compatible storage
- **Key features**:
  - Red Hat-supported runtime
  - gRPC API for streaming inference
  - Integrated with RHOAI model serving platform
- **When to choose**: When the model is already in Caikit format or when gRPC API is required.
- **Limitations**: Requires model conversion to Caikit format, smaller model ecosystem, gRPC-only API
- **ServingRuntime CR name**: Check available runtimes with `resources_list` for `ServingRuntime` resources with `caikit` in the name

## Custom Runtimes

**User-provided ServingRuntime CRs for unsupported frameworks.**

- **API**: Defined by the custom runtime
- **Model formats**: Defined by the custom runtime
- **When to choose**: When none of the built-in runtimes support the model framework or when specific customization is needed.
- **How to create**: Use `/serving-runtime-config` skill
- **Limitations**: Not supported by Red Hat, user responsibility for maintenance and compatibility

## Runtime Selection Decision Tree

```
Is the user's preferred runtime explicitly stated?
├── Yes → Use that runtime
└── No → Continue

Is the model available in the NGC NIM catalog?
├── Yes → Suggest NIM (with vLLM as fallback)
│         Note: Requires /nim-setup and NVIDIA GPUs
└── No → Continue

Is the model in Caikit format?
├── Yes → Caikit+TGIS
└── No → Continue

Is the model a standard open-source LLM (HuggingFace-compatible)?
├── Yes → vLLM (default)
└── No → Custom runtime via /serving-runtime-config
```

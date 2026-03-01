---
title: Live Documentation Lookup Protocol
category: references
tags: [live-lookup, webfetch, documentation, models, runtimes]
semantic_keywords: [live doc lookup, external documentation fetch, model discovery, runtime discovery]
use_cases: [model-deploy, nim-setup, serving-runtime-config, debug-inference]
last_updated: 2026-02-26
---

# Live Documentation Lookup Protocol

This document defines the protocol for fetching external documentation at runtime when the agent encounters an unfamiliar model, runtime, or error. Because OpenShift AI and the NVIDIA NIM ecosystem evolve rapidly, the agent's training data may be stale. This protocol ensures accurate, up-to-date information.

## When to Trigger Live Lookup

The agent MUST trigger a live doc lookup when ANY of these conditions are true:

1. **Unknown model**: The user requests deployment of a model not listed in [known-model-profiles.md](known-model-profiles.md)
2. **Uncertain hardware requirements**: The agent is not confident about GPU type, VRAM, or GPU count for a model
3. **Unfamiliar runtime or feature**: The user mentions a serving runtime configuration the agent is uncertain about
4. **Unrecognized deployment error**: A deployment fails with an error message the agent cannot diagnose from its training data

## Lookup Targets

Query these sources in order of relevance. Stop once sufficient information is found.

### 1. Red Hat OpenShift AI Documentation

**URL**: `https://docs.redhat.com/en/documentation/red_hat_openshift_ai_cloud_service/1`

**When to use**: For RHOAI-specific features, supported runtimes, CRD schemas, model catalog entries, and deployment guides.

**What to extract**:
- Supported serving runtime versions and configurations
- InferenceService CRD schema updates
- Model catalog entries with deployment parameters
- Known issues and workarounds

### 2. NVIDIA NIM Model Catalog

**URL**: `https://build.nvidia.com/models`

**When to use**: For NIM-specific models — hardware profiles, API specs, deployment parameters, GPU compatibility.

**What to extract**:
- GPU type and count requirements (e.g., "2x A100 80GB")
- Model-specific deployment parameters
- API specifications and endpoints
- Available model profiles (optimized vs. generic)

### 3. NVIDIA NIM Supported Models Matrix

**URL**: `https://docs.nvidia.com/nim/large-language-models/latest/supported-models.html`

**When to use**: For the definitive list of NIM-supported models with GPU compatibility matrix.

**What to extract**:
- GPU compatibility per model (which GPU types are supported)
- Model profiles: optimized (TensorRT-LLM) vs. generic (vLLM-based)
- Minimum GPU memory requirements
- Tensor parallelism configuration

## Lookup Procedure

### Step 1: Determine the lookup target

Based on the trigger condition, select the most relevant URL:
- Model hardware requirements → Start with NVIDIA NIM catalog (#2), then RHOAI docs (#1)
- Runtime configuration → RHOAI docs (#1)
- NIM GPU compatibility → NIM supported models matrix (#3)
- General deployment issues → RHOAI docs (#1)

### Step 2: Fetch the page

Use the **WebFetch** tool to retrieve the relevant page content.

### Step 3: Extract relevant information

Parse the fetched content for:
- GPU type and count requirements
- Model-specific serving parameters (max sequence length, quantization, tensor parallelism)
- Compatible runtimes and their versions
- Known issues or special configuration notes

### Step 4: Report to user

**REQUIRED** (Document Consultation Transparency - Design Principle #1):

Always report what was looked up and from where:

```
"I looked up [model-name] on [source-name] to confirm its hardware requirements:
- GPU: [count]x [type] ([VRAM])
- Key parameters: [list]
- Compatible runtimes: [list]"
```

### Step 5: Proceed with deployment

Use the fetched specs to configure the deployment. The looked-up information takes precedence over any cached or training data.

## Security Considerations

- Live lookup URLs are read-only documentation pages
- No credentials are sent to external URLs
- Fetched content is used only for parameter extraction, not executed

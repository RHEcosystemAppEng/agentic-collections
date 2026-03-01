---
title: Known Model Hardware Profiles
category: references
tags: [models, gpu, hardware, profiles, llama, granite, mixtral, mistral]
semantic_keywords: [model GPU requirements, hardware profiles, vLLM configuration, model deployment specs]
use_cases: [model-deploy, debug-inference, ai-observability]
last_updated: 2026-02-26
---

# Known Model Hardware Profiles

Hardware profiles for commonly deployed models on OpenShift AI. This file serves as a fast-path cache for `/model-deploy` — when a model is listed here, the agent uses these specs directly. When a model is not listed, the agent falls back to the live doc lookup protocol defined in [live-doc-lookup.md](live-doc-lookup.md).

**Important**: These are recommended minimums. Actual requirements may vary based on quantization, sequence length, and batch size. Validate against live documentation for production deployments.

## Llama 3.x (Meta)

| Variant | Parameters | GPUs | GPU Type | VRAM | Key vLLM Args |
|---------|-----------|------|----------|------|---------------|
| Llama 3.1 8B | 8B | 1 | A10G/L4/A100/H100 | 16GB | `--max-model-len=4096` |
| Llama 3.1 70B | 70B | 4 | A100 80GB | 320GB | `--max-model-len=4096 --tensor-parallel-size=4` |
| Llama 3.1 70B | 70B | 2 | H100 80GB | 160GB | `--max-model-len=4096 --tensor-parallel-size=2` |
| Llama 3.1 405B | 405B | 8 | A100 80GB / H100 | 640GB | `--max-model-len=4096 --tensor-parallel-size=8` |

- Tool calling: `--tool-call-parser hermes --chat-template` (for Llama 3.1+ instruct variants)
- Quantization: AWQ, GPTQ, FP8 variants reduce GPU requirements significantly

## Granite 3.x (IBM/Red Hat)

| Variant | Parameters | GPUs | GPU Type | VRAM | Key vLLM Args |
|---------|-----------|------|----------|------|---------------|
| Granite 3.1 2B | 2B | 1 | Any GPU | 8GB | `--max-model-len=4096` |
| Granite 3.1 8B | 8B | 1 | A10G/L4/A100 | 16GB | `--max-model-len=4096` |

- Tool calling: `--tool-call-parser granite --chat-template`
- Red Hat-supported model family on RHOAI

## Mixtral (Mistral AI)

| Variant | Parameters | GPUs | GPU Type | VRAM | Key vLLM Args |
|---------|-----------|------|----------|------|---------------|
| Mixtral 8x7B | 46.7B (MoE) | 2 | A100 80GB | 160GB | `--tensor-parallel-size=2` |
| Mixtral 8x22B | 141B (MoE) | 4 | A100 80GB | 320GB | `--tensor-parallel-size=4` |

- Mixture-of-Experts architecture: only ~13B/45B parameters active per token

## Mistral (Mistral AI)

| Variant | Parameters | GPUs | GPU Type | VRAM | Key vLLM Args |
|---------|-----------|------|----------|------|---------------|
| Mistral 7B | 7B | 1 | A10G/L4/A100 | 16GB | `--max-model-len=8192` |
| Mistral Large (123B) | 123B | 4 | A100 80GB | 320GB | `--tensor-parallel-size=4` |

## When a Model Is Not Listed

If the requested model is not in this file, the agent MUST use the live doc lookup protocol:

1. Read [live-doc-lookup.md](live-doc-lookup.md) for the lookup procedure
2. Fetch hardware specs from the appropriate source
3. Report findings to the user before proceeding with deployment

Common cases requiring live lookup:
- Newly released models (after this file's last update)
- Domain-specific fine-tuned models
- Models with custom quantization
- NIM-specific optimized profiles

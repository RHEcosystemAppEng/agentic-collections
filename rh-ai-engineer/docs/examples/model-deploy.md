# /model-deploy Examples

Example interactions demonstrating the model-deploy skill workflow.

## Example 1: Deploy Llama 3.1 8B with vLLM

```
User: "Deploy Llama 3.1 8B on my cluster"

Agent: [Invokes /model-deploy skill]
       [Reads supported-runtimes.md]

I consulted supported-runtimes.md to understand runtime capabilities.

Step 1 of 10: Gathering deployment information.

| Setting | Value | Source |
|---------|-------|--------|
| Model | Llama 3.1 8B Instruct | user input |
| Runtime | TBD | auto-detect |
| Namespace | ? | needs input |
| Model Source | ? | needs input |
| Deployment Mode | Serverless | default |

What namespace should I deploy to, and where are the model weights stored?
(e.g., S3 bucket, OCI registry, PVC)

User: "namespace: ai-models, model is on S3 at s3://my-bucket/llama-3.1-8b"

Agent: Step 2 of 10: Determining runtime.

I consulted supported-runtimes.md to understand runtime capabilities.

Based on Llama 3.1 8B (open-source HuggingFace model):

Recommended runtime: vLLM
Reason: Default runtime for open-source LLMs. Broad compatibility,
        OpenAI-compatible API, no additional setup required.

Proceed with vLLM? (yes / no / suggest alternative)

User: "yes"

Agent: Step 3 of 10: Looking up hardware profile.

I consulted known-model-profiles.md to find hardware requirements for Llama 3.1 8B.

| Requirement | Value |
|-------------|-------|
| GPUs | 1x A10G/L4/A100/H100 |
| VRAM | 16GB |
| Key Args | --max-model-len=4096 --tool-call-parser hermes |

Step 4 of 10: GPU pre-flight check skipped (ai-observability MCP not configured).
Ensure your cluster has at least 1 GPU with 16GB VRAM.

Step 5 of 10: Skipped (NIM platform check not needed for vLLM).

Step 6-7 of 10: Generating InferenceService YAML.

apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-3-1-8b
  namespace: ai-models
  annotations:
    serving.kserve.io/deploymentMode: Serverless
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM
      runtime: vllm-runtime
      storageUri: s3://my-bucket/llama-3.1-8b
      resources:
        limits:
          nvidia.com/gpu: "1"
        requests:
          cpu: "4"
          memory: "16Gi"
    args:
      - --max-model-len=4096
      - --tool-call-parser=hermes

| Setting | Value |
|---------|-------|
| Model | llama-3-1-8b |
| Runtime | vllm-runtime |
| GPUs | 1 |
| Namespace | ai-models |
| Mode | Serverless |

Proceed with creating this InferenceService? (yes/no/modify)

User: "yes"

Agent: Step 8 of 10: Creating InferenceService...
       [Creates via resources_create_or_update]

       InferenceService created. Monitoring rollout...

Step 9 of 10: Monitoring rollout.

| Stage | Status |
|-------|--------|
| Pod Scheduled | Complete |
| Image Pulled | Complete |
| Container Started | Complete |
| Model Loaded | Complete |
| Ready | Complete |

Step 10 of 10: Deployment complete!

Model Deployment Successful

Model: llama-3-1-8b
Runtime: vLLM
Namespace: ai-models
GPUs: 1

Inference Endpoint:
  URL: https://llama-3-1-8b-ai-models.apps.cluster.example.com
  API: OpenAI-compatible REST

Quick Test:
  curl -X POST https://llama-3-1-8b-ai-models.apps.cluster.example.com/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model": "llama-3-1-8b", "messages": [{"role": "user", "content": "Hello"}]}'

Next Steps:
  Monitor performance: "/ai-observability llama-3-1-8b"
```

## Example 2: Deploy a Model with NIM (NIM Not Set Up)

```
User: "Deploy Llama 3.1 70B with NIM"

Agent: [Invokes /model-deploy skill]
       ...
       Step 2: User requested NIM runtime.

       Step 5: Checking NIM platform...

NIM platform is not set up in namespace ai-models.

The NIM runtime requires a one-time platform setup. Would you like to:
1. Run /nim-setup now to configure the NIM platform
2. Switch to vLLM runtime instead (no setup required)
3. Abort deployment

User: "1"

Agent: [Invokes /nim-setup skill — walks through NGC credential setup]
       ...
       NIM Platform Setup Complete.

       Resuming model deployment...
       [Continues from Step 6 with NIM runtime]
```

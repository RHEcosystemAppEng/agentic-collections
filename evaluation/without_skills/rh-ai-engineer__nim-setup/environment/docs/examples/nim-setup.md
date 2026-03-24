# /nim-setup Examples

Example interactions demonstrating the nim-setup skill workflow.

## Example 1: First-Time NIM Setup

```
User: "Set up NIM on my cluster"

Agent: [Invokes /nim-setup skill]
       [Reads supported-runtimes.md]

I consulted supported-runtimes.md to understand NIM platform requirements.

Let me verify the prerequisites for NIM setup.

Step 1 of 7: Checking GPU Operator and NFD Operator...

GPU Operator: gpu-operator-certified.v24.6.2 (Succeeded)
NFD Operator: nfd.v4.19.0 (Succeeded)

Both operators are installed and healthy.

Step 2 of 7: I need your NGC credentials.

To set up NIM, I need your NVIDIA NGC API key.
You can generate one at: https://ngc.nvidia.com/setup/api-key

Please provide:
1. Your NGC API key
2. The target namespace for NIM resources

User: "Here's my key: [user provides NGC API key], namespace: ai-models"

Agent: Step 3 of 7: Creating NGC image pull secret...

I'll create a docker-registry secret for pulling NIM images from nvcr.io:

  apiVersion: v1
  kind: Secret
  metadata:
    name: ngc-image-pull-secret
    namespace: ai-models
  type: kubernetes.io/dockerconfigjson
  data:
    .dockerconfigjson: [base64-encoded config for nvcr.io - REDACTED]

Should I create this image pull secret in namespace `ai-models`? (yes/no)

User: "yes"

Agent: [Creates secret via resources_create_or_update]
       Image pull secret created successfully.

Step 4 of 7: Creating NGC API key secret...

  apiVersion: v1
  kind: Secret
  metadata:
    name: ngc-api-key
    namespace: ai-models
  type: Opaque
  stringData:
    NGC_API_KEY: "[REDACTED]"

Should I create this API key secret in namespace `ai-models`? (yes/no)

User: "yes"

Agent: [Creates secret via resources_create_or_update]
       API key secret created successfully.

Step 5 of 7: Creating NIM Account CR...

  apiVersion: nim.opendatahub.io/v1
  kind: Account
  metadata:
    name: nim-account
    namespace: ai-models
  spec:
    apiKeySecret:
      name: ngc-api-key
    imagePullSecret:
      name: ngc-image-pull-secret

Should I create this NIM Account CR in namespace `ai-models`? (yes/no)

User: "yes"

Agent: [Creates Account CR via resources_create_or_update]
       Account CR created successfully.

Step 6 of 7: Would you like to customize the NIM model catalog? (yes/no, default: no)

User: "no"

Agent: Step 7 of 7: Validating NIM platform readiness...

NIM Platform Setup Complete

Account CR: `nim-account` (namespace: ai-models)
  Status: Ready

NGC Credentials:
  Image Pull Secret: ngc-image-pull-secret [created]
  API Key Secret: ngc-api-key [created]

NIM ServingRuntimes Available:
  - nim-llama-3-1-8b-instruct
  - nim-llama-3-1-70b-instruct
  - nim-mistral-7b-instruct

Next Steps:
  To deploy a model with NIM: "/model-deploy llama-3.1-8b --runtime nim"
```

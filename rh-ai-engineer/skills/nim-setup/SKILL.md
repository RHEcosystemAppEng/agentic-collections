---
name: nim-setup
description: |
  Configure NVIDIA NIM platform on OpenShift AI for optimized model inference.

  Use when:
  - "Set up NIM on my cluster"
  - "Configure NGC credentials for NIM"
  - "I want to deploy a NIM model but haven't set up the platform"
  - "Create the NIM Account CR"

  One-time prerequisite before deploying models with NVIDIA NIM runtime via /model-deploy.

  NOT for deploying models (use /model-deploy instead).
  NOT for vLLM or Caikit deployments (NIM-specific only).
---

# /nim-setup Skill

Configure the NVIDIA NIM platform on OpenShift AI. This is a one-time setup that creates NGC credentials and the NIM Account custom resource, enabling NIM-based model deployments via `/model-deploy`.

## Prerequisites

**Required MCP Server**: `openshift` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_get` (from openshift) - Check operator installations and existing resources
- `resources_list` (from openshift) - List resources in a namespace
- `resources_create_or_update` (from openshift) - Create secrets, Account CR, ConfigMap
- `events_list` (from openshift) - Check events for errors during setup

**Optional MCP Server**: `ai-observability` (for `get_gpu_info` to verify GPU availability)

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required User Input**:
- NGC API key (from https://ngc.nvidia.com)
- Target namespace for NIM resources

**Required Cluster Setup**:
- OpenShift cluster (>= 4.14)
- Red Hat OpenShift AI operator installed
- NVIDIA GPU Operator installed
- Node Feature Discovery (NFD) Operator installed
- ServiceAccount with RBAC permissions to create Secrets, Accounts, and ConfigMaps

See [skill-conventions.md](../../docs/references/skill-conventions.md) for prerequisite verification protocol, human-in-the-loop requirements, and security conventions.

## Workflow

### Step 1: Verify GPU Operator and Node Feature Discovery

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [supported-runtimes.md](../../docs/references/supported-runtimes.md) using the Read tool to understand NIM platform requirements
2. **Output to user**: "I consulted [supported-runtimes.md](../../docs/references/supported-runtimes.md) to understand NIM platform requirements."

Check that the NVIDIA GPU Operator and NFD Operator are installed and healthy.

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"clusterserviceversions"` - REQUIRED
  - Example: `"clusterserviceversions"`
- `namespace`: `"nvidia-gpu-operator"` - REQUIRED (namespace where GPU Operator CSV is installed)
  - Example: `"nvidia-gpu-operator"`
- `name`: the CSV name matching `"gpu-operator-certified"` prefix

**Expected Output**: ClusterServiceVersion object with `status.phase: "Succeeded"`

Repeat for NFD Operator:
- `namespace`: `"openshift-nfd"`
- `name`: the CSV name matching `"nfd"` prefix

**Error Handling**:
- If GPU Operator CSV not found -> Report to user: "NVIDIA GPU Operator is not installed. Install it from OperatorHub before proceeding."
- If NFD Operator CSV not found -> Report to user: "Node Feature Discovery Operator is not installed. Install it from OperatorHub before proceeding."
- If `status.phase` != `"Succeeded"` -> Report current phase and suggest troubleshooting
- Offer to skip this check if user confirms operators are installed via another method

### Step 2: Collect NGC Credentials from User

Ask the user for their NGC API key. This key is used for two purposes:
1. Pulling NIM container images from `nvcr.io` (image pull secret)
2. Authenticating NIM API calls at runtime (API key secret)

**Ask the user**:
```
To set up NIM, I need your NVIDIA NGC API key.

You can generate one at: https://ngc.nvidia.com/setup/api-key

Please provide:
1. Your NGC API key
2. The target namespace for NIM resources (e.g., "my-ai-project")
```

**WAIT for user to provide the NGC API key and namespace.**

**SECURITY**: Store the key in memory only for the duration of this skill. Never echo or display the actual key value in output.

### Step 3: Create NGC Image Pull Secret

Generate and display the docker-registry Secret YAML for pulling NIM images from `nvcr.io`.

**Show the user the Secret manifest** (with API key value redacted):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ngc-image-pull-secret
  namespace: [namespace]
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: [base64-encoded docker config for nvcr.io]
```

Note: The `.dockerconfigjson` contains:
- Registry: `nvcr.io`
- Username: `$oauthtoken`
- Password: `[NGC API key - REDACTED in display]`

**Ask**: "Should I create this image pull secret in namespace `[namespace]`? (yes/no)"

**WAIT for explicit user confirmation.**

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `resource`: full Secret manifest as JSON string - REQUIRED
  - The JSON must include apiVersion, kind, metadata (name, namespace), type, and data fields
- `namespace`: user-specified namespace - REQUIRED
  - Example: `"my-ai-project"`

**Expected Output**: Created Secret object with `metadata.uid`

**Error Handling**:
- If secret already exists -> Ask user: "Secret `ngc-image-pull-secret` already exists. Should I update it? (yes/no)"
- If namespace not found -> Report error, suggest creating namespace first
- If RBAC error -> Report insufficient permissions

### Step 4: Create NGC API Key Secret

Generate and display the generic Secret YAML for the NGC API key used at runtime.

**Show the user the Secret manifest** (with API key value redacted):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ngc-api-key
  namespace: [namespace]
type: Opaque
stringData:
  NGC_API_KEY: "[REDACTED]"
```

**Ask**: "Should I create this API key secret in namespace `[namespace]`? (yes/no)"

**WAIT for explicit user confirmation.**

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `resource`: full Secret manifest as JSON string - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

**Expected Output**: Created Secret object with `metadata.uid`

**Error Handling**:
- If secret already exists -> Ask user if they want to update it
- If RBAC error -> Report insufficient permissions

### Step 5: Create NIM Account CR

Generate and display the NIM Account custom resource that manages the NIM platform lifecycle.

**Show the user the Account CR manifest:**

```yaml
apiVersion: nim.opendatahub.io/v1
kind: Account
metadata:
  name: nim-account
  namespace: [namespace]
spec:
  apiKeySecret:
    name: ngc-api-key
  imagePullSecret:
    name: ngc-image-pull-secret
```

**Ask**: "Should I create this NIM Account CR in namespace `[namespace]`? (yes/no)"

**WAIT for explicit user confirmation.**

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `resource`: full Account CR manifest as JSON string - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

**Expected Output**: Created Account object with `metadata.uid`

**Error Handling**:
- If Account CR already exists -> Report current status, ask if user wants to update
- If CRD not found (`nim.opendatahub.io/v1` Account) -> Report: "NIM CRD not available. Ensure Red Hat OpenShift AI operator is installed and includes NIM support."
- If RBAC error -> Report insufficient permissions

### Step 6: (Optional) Configure NIM Model Catalog

**Ask**: "Would you like to customize which NIM models appear in the catalog? (yes/no, default: no)"

If user says **no** -> Skip to Step 7 (default catalog is used).

If user says **yes**:

**Show the user the ConfigMap template:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nim-model-catalog
  namespace: [namespace]
data:
  model-catalog.json: |
    [
      {
        "name": "[model-name]",
        "displayName": "[display-name]",
        "shortDescription": "[description]"
      }
    ]
```

Ask user which models to include, generate the ConfigMap, and confirm before creating.

**MCP Tool**: `resources_create_or_update` (from openshift)

### Step 7: Validate NIM Platform Readiness

Check that the NIM platform is ready for model deployments.

**Step 7a: Check Account CR Status**

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"accounts.nim.opendatahub.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: `"nim-account"` - REQUIRED

**Expected Output**: Account object with `status.conditions` showing ready state

**Step 7b: Verify NIM ServingRuntimes**

**MCP Tool**: `resources_list` (from openshift)

**Parameters**:
- `resource`: `"servingruntimes.serving.kserve.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

**Expected Output**: List of ServingRuntime objects including NIM runtimes

**Step 7c: (Optional) GPU Inventory Check**

If `ai-observability` MCP server is available, use `get_gpu_info` to report cluster GPU inventory.

**Report results** showing: Account CR status, credentials status (created/existing), available NIM ServingRuntimes, GPU inventory (if available), and next steps (`/model-deploy`).

**On failure**: Report Account CR status details and error message. Suggest troubleshooting steps: check Account CR events, verify NGC API key validity, check OpenShift AI operator logs. Ask if user wants help troubleshooting.

## Common Issues

### Issue 1: Account CR Stuck in "Pending"

**Error**: Account CR `status.conditions` shows pending state indefinitely

**Cause**: NGC credentials are invalid, expired, or the RHOAI operator cannot reach NGC services.

**Solution:**
1. Verify NGC API key is valid by testing at https://ngc.nvidia.com
2. Check Account CR events: `resources_get` with events for the Account resource
3. Regenerate NGC API key and re-run `/nim-setup` with new credentials

### Issue 2: GPU Operator Not Installed

**Error**: ClusterServiceVersion for `gpu-operator-certified` not found

**Cause**: NVIDIA GPU Operator was not installed from OperatorHub.

**Solution:**
1. Install NVIDIA GPU Operator from OperatorHub in the OpenShift console
2. Wait for the operator to reach `Succeeded` phase
3. Verify GPU nodes are detected: check for `nvidia.com/gpu` resources on nodes
4. Re-run `/nim-setup`

### Issue 3: Image Pull Error from nvcr.io

**Error**: Pods fail with `ErrImagePull` or `ImagePullBackOff` referencing `nvcr.io`

**Cause**: The NGC image pull secret is misconfigured, the API key is expired, or the secret is not in the correct namespace.

**Solution:**
1. Verify the pull secret exists in the target namespace
2. Check that the secret contains valid docker credentials for `nvcr.io`
3. Re-run `/nim-setup` to recreate credentials with a fresh NGC API key
4. Ensure the secret is referenced by the ServiceAccount or Account CR

### Issue 4: NIM ServingRuntimes Not Appearing

**Error**: `resources_list` for ServingRuntimes returns no NIM runtimes

**Cause**: Account CR is not yet ready, or the RHOAI operator version does not include NIM support.

**Solution:**
1. Check Account CR status — runtimes are created asynchronously after the Account becomes ready
2. Wait 2-3 minutes and re-check
3. Verify RHOAI operator version supports NIM integration
4. Check operator logs for errors

## Dependencies

### MCP Tools Used

| Tool | Server | Purpose |
|------|--------|---------|
| `resources_get` | openshift | Check operator CSVs, Account CR status |
| `resources_list` | openshift | List NIM ServingRuntimes |
| `resources_create_or_update` | openshift | Create secrets, Account CR, ConfigMap |
| `events_list` | openshift | Troubleshoot Account CR issues |
| `get_gpu_info` | ai-observability (optional) | GPU inventory check |

### Related Skills
- `/model-deploy` - Deploy a model using NIM runtime after setup is complete
- `/serving-runtime-config` - Configure custom serving runtimes if NIM doesn't fit

### Reference Documentation
- [supported-runtimes.md](../../docs/references/supported-runtimes.md) - NIM runtime capabilities and requirements
- [live-doc-lookup.md](../../docs/references/live-doc-lookup.md) - Protocol for fetching current RHOAI/NIM documentation

## Critical: Human-in-the-Loop Requirements

See [skill-conventions.md](../../docs/references/skill-conventions.md) for general HITL and security conventions.

**Skill-specific checkpoints:**
- Before creating each Secret: display manifest (credentials REDACTED), confirm
- Before creating Account CR: display manifest, confirm
- Before creating ConfigMap (if applicable): display manifest, confirm
- **NEVER** display actual NGC API key values in output

## Example Usage

See [nim-setup examples](../../docs/examples/nim-setup.md) for a complete first-time NIM setup walkthrough.

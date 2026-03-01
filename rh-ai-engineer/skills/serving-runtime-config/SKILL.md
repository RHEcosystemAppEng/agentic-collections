---
name: serving-runtime-config
description: |
  Configure custom ServingRuntime CRs on OpenShift AI for model serving frameworks not covered by built-in runtimes.

  Use when:
  - "Create a custom serving runtime"
  - "I need a runtime for ONNX / Triton / custom framework"
  - "Customize vLLM runtime parameters"
  - "What serving runtimes are available?"
  - "Add a custom container image for model serving"

  Handles listing existing runtimes, creating new ServingRuntime CRs, and validating compatibility with target models.

  NOT for deploying models (use /model-deploy after runtime is configured).
  NOT for NIM platform setup (use /nim-setup).
model: inherit
color: green
---

# /serving-runtime-config Skill

Configure custom ServingRuntime custom resources on Red Hat OpenShift AI. Use when built-in runtimes (vLLM, NIM, Caikit+TGIS) do not support the target model framework, or when customizing an existing runtime's parameters (env vars, model format, container image).

## Prerequisites

**Required MCP Server**: `openshift` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `resources_get` (from openshift) - Inspect existing ServingRuntime CRs
- `resources_list` (from openshift) - List available ServingRuntimes in a namespace
- `resources_create_or_update` (from openshift) - Create or update ServingRuntime CR

**Optional MCP Server**: `ai-observability` ([AI Observability MCP](https://github.com/rh-ai-quickstart/ai-observability-summarizer))

**Optional MCP Tools** (from ai-observability):
- `list_models` - Verify deployed models use the new runtime

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access

**Required Cluster Setup**:
- OpenShift cluster with Red Hat OpenShift AI operator installed
- KServe model serving platform configured
- Model serving enabled on the target namespace (label: `opendatahub.io/dashboard: "true"`)

See [skill-conventions.md](../../docs/references/skill-conventions.md) for prerequisite verification protocol, human-in-the-loop requirements, and security conventions.

## Workflow

### Step 1: Gather Requirements

**Ask the user for:**
- **Use case**: What framework/model needs serving? (e.g., "ONNX model", "custom TensorRT engine", "vLLM with custom args")
- **Namespace**: Target namespace for the ServingRuntime
- **Intent**: New runtime from scratch, or customize an existing one?

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [supported-runtimes.md](../../docs/references/supported-runtimes.md) using the Read tool to understand available runtimes and their capabilities
2. **Output to user**: "I consulted [supported-runtimes.md](../../docs/references/supported-runtimes.md) to understand available runtimes."

**MCP Tool**: `resources_list` (from openshift)

**Parameters**:
- `resource`: `"servingruntimes.serving.kserve.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

**Present findings** in a table:

| Runtime Name | Model Format | Multi-Model | Container Image |
|--------------|-------------|-------------|-----------------|
| [name] | [format] | [true/false] | [image:tag] |

If an existing runtime fits the user's need, recommend using it directly with `/model-deploy`. Otherwise, proceed to Step 2.

**WAIT for user to confirm whether to create a new runtime or customize an existing one.**

### Step 2: Determine Runtime Configuration

Based on the user's framework and model requirements, determine the ServingRuntime spec.

**If customizing an existing runtime:**

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"servingruntimes.serving.kserve.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: name of the existing runtime to customize - REQUIRED

Extract the current spec as a starting point. Present the current configuration and ask what the user wants to change.

**If the user requests a runtime for an unfamiliar framework -> Trigger live doc lookup:**
1. **Action**: Read [live-doc-lookup.md](../../docs/references/live-doc-lookup.md) using the Read tool for the lookup protocol
2. **Output to user**: "Framework [name] is not in my cached runtimes. I'll look up its serving requirements."
3. Use **WebFetch** to retrieve specs from Red Hat OpenShift AI documentation
4. Extract: container image, model format name, supported protocols, required env vars
5. **Output to user**: "I looked up [framework] on [source] to confirm its runtime requirements: [summary]"

**Collect runtime parameters:**

| Parameter | Value | Source |
|-----------|-------|--------|
| Runtime name | [name] | user input |
| Container image | [image:tag] | user input / doc lookup |
| Model format name | [format] | user input / doc lookup |
| Supported protocol versions | [v1, v2, grpc-v2] | user input / default |
| Multi-model serving | [true/false] | default: false (single-model) |
| Environment variables | [list] | user input |
| GPU resource requirements | [limits] | user input |

**WAIT for user to confirm or modify parameters.**

### Step 3: Generate ServingRuntime YAML

Generate the ServingRuntime manifest using values from Steps 1-2.

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: [runtime-name]
  namespace: [namespace]
  labels:
    opendatahub.io/dashboard: "true"
  annotations:
    openshift.io/display-name: "[Display Name]"
spec:
  supportedModelFormats:
    - name: [model-format-name]
      version: "[version]"
      autoSelect: true
  multiModel: false
  containers:
    - name: kserve-container
      image: [container-image:tag]
      ports:
        - containerPort: 8080
          protocol: TCP
      env:
        - name: [ENV_VAR]
          value: "[value]"
      resources:
        limits:
          nvidia.com/gpu: "[gpu-count]"
        requests:
          cpu: "[cpu]"
          memory: "[memory]"
```

**Display the complete ServingRuntime YAML** to the user.

**Ask**: "Proceed with creating this ServingRuntime? (yes/no/modify)"

**WAIT for explicit confirmation.**

- If **yes** -> Proceed to Step 4
- If **no** -> Abort
- If **modify** -> Ask what to change, regenerate YAML, return to this step

### Step 4: Create ServingRuntime

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `resource`: full ServingRuntime manifest as JSON string - REQUIRED
- `namespace`: user-specified namespace - REQUIRED

**Error Handling**:
- If namespace not found -> Report error, suggest creating namespace or using `/ds-project-setup`
- If runtime name already exists -> Ask user: "ServingRuntime `[name]` already exists. Update it? (yes/no)"
- If CRD not found -> Report: "ServingRuntime CRD not available. Ensure Red Hat OpenShift AI operator is installed."
- If RBAC error -> Report insufficient permissions

### Step 5: Validate Runtime

**MCP Tool**: `resources_get` (from openshift)

**Parameters**:
- `resource`: `"servingruntimes.serving.kserve.io"` - REQUIRED
- `namespace`: user-specified namespace - REQUIRED
- `name`: the created runtime name - REQUIRED

Verify the runtime was created successfully.

**Report results** showing: runtime name, namespace, model format, container image, and next steps (`/model-deploy` to deploy a model using this runtime).

## Common Issues

### Issue 1: InferenceService Cannot Find Runtime

**Error**: InferenceService status shows "Unknown" or runtime not matched

**Cause**: The `modelFormat.name` in the InferenceService does not match any `supportedModelFormats[].name` in available ServingRuntimes.

**Solution:**
1. Verify the model format name matches exactly (case-sensitive)
2. Check the runtime is in the same namespace as the InferenceService
3. Ensure the runtime has `opendatahub.io/dashboard: "true"` label

### Issue 2: Container Image Pull Failure

**Error**: Runtime pods fail with `ErrImagePull` or `ImagePullBackOff`

**Cause**: Custom container image requires authentication or does not exist.

**Solution:**
1. Verify the image URI and tag are correct
2. Create an image pull secret if the registry requires authentication
3. Link the pull secret to the default ServiceAccount in the namespace

### Issue 3: Runtime Port Mismatch

**Error**: InferenceService created but health checks fail, endpoint returns connection refused

**Cause**: The `containerPort` in the ServingRuntime does not match the port the serving framework actually listens on.

**Solution:**
1. Check the framework's documentation for its default serving port
2. Update the `containerPort` in the ServingRuntime spec
3. Or set an environment variable to configure the framework's listen port to match

## Dependencies

### MCP Tools Used

| Tool | Server | Purpose |
|------|--------|---------|
| `resources_get` | openshift | Inspect existing ServingRuntime CRs |
| `resources_list` | openshift | List available ServingRuntimes |
| `resources_create_or_update` | openshift | Create or update ServingRuntime CR |
| `list_models` | ai-observability (optional) | Verify models using the runtime |

### Related Skills
- `/model-deploy` - Deploy a model using the configured runtime
- `/nim-setup` - NIM platform setup (if NIM runtime is needed instead)
- `/debug-inference` - Troubleshoot InferenceService failures after deployment

### Reference Documentation
- [supported-runtimes.md](../../docs/references/supported-runtimes.md) - Runtime capabilities and model format names
- [live-doc-lookup.md](../../docs/references/live-doc-lookup.md) - Protocol for fetching specs for unknown frameworks

## Critical: Human-in-the-Loop Requirements

See [skill-conventions.md](../../docs/references/skill-conventions.md) for general HITL and security conventions.

**Skill-specific checkpoints:**
- After listing existing runtimes (Step 1): confirm whether to create new or customize existing
- After collecting parameters (Step 2): confirm runtime configuration
- Before creating ServingRuntime (Step 3): display full YAML, confirm
- **NEVER** overwrite an existing ServingRuntime without user confirmation

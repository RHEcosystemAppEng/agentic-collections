---
name: workbench-manage
description: |
  Create and manage Jupyter notebook workbenches on OpenShift AI with image selection, resource configuration, PVC storage, and lifecycle management.

  Use when:
  - "Create a notebook workbench"
  - "Spin up a Jupyter environment for data science"
  - "Start / stop my workbench"
  - "What notebook images are available?"
  - "Delete a workbench I no longer need"

  Handles Notebook CR lifecycle: create with configurable images and resources, start/stop, attach storage, and delete with data loss warnings.

  NOT for deploying models (use /model-deploy).
  NOT for creating projects (use /ds-project-setup).
  NOT for managing pipelines (use /pipeline-manage).
color: blue
model: inherit
metadata:
  author: "Red Hat Ecosystem Engineering"
  version: "1.0"
---

# /workbench-manage Skill

Create and manage Jupyter notebook workbenches on Red Hat OpenShift AI. Handles the full workbench lifecycle: listing available notebook images, creating Notebook CRs with configurable CPU/memory/GPU resources, provisioning PVC storage, starting and stopping workbenches, and deleting them with proper data loss warnings.

## Prerequisites

**Required MCP Server**: `rhoai` ([RHOAI MCP Server](https://github.com/opendatahub-io/rhoai-mcp))

**Required MCP Tools** (from rhoai):
- `list_data_science_projects` - Validate namespace is an RHOAI Data Science Project
- `list_notebook_images` - List available notebook container images (PyTorch, TensorFlow, Standard DS, etc.)
- `list_workbenches` - List existing workbenches in a project
- `get_workbench` - Get workbench details (status, image, resources, storage)
- `create_workbench` - Create a new Notebook CR with image, resources, and storage
- `start_workbench` - Start a stopped workbench
- `stop_workbench` - Stop a running workbench
- `delete_workbench` - Delete a workbench
- `get_workbench_url` - Get the OAuth-protected notebook URL
- `list_storage` - List PVCs in the project
- `create_storage` - Create a PVC for workbench storage
- `delete_storage` - Delete a PVC
- `list_data_connections` - List data connections available to attach

**Required MCP Server**: `openshift` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools** (from openshift):
- `resources_get` (from openshift) - Inspect Notebook CR details, check node GPU availability
- `events_list` (from openshift) - Check pod events when workbench is stuck

**Common prerequisites** (KUBECONFIG, OpenShift+RHOAI cluster, verification protocol): See [skill-conventions.md](../../docs/references/skill-conventions.md).

**Additional cluster requirements**:
- Target namespace is an RHOAI Data Science Project (label: `opendatahub.io/dashboard: "true"`)

## When to Use This Skill

**Use this skill when you need to:**
- Create a new Jupyter notebook workbench for a data scientist
- List available notebook images (PyTorch, TensorFlow, Standard Data Science, etc.)
- Start or stop an existing workbench
- List workbenches in a project and check their status
- Delete a workbench and its associated storage
- Provision persistent storage for a workbench

**Do NOT use this skill when:**
- You need to create a Data Science Project first (use `/ds-project-setup`)
- You want to deploy a model for inference (use `/model-deploy`)
- You need to manage data science pipelines (use `/pipeline-manage`)
- You need to troubleshoot a model deployment (use `/debug-inference`)

## Workflow

### Step 1: Determine Intent

**Ask the user what they want to do:**
- **Create** a new workbench
- **Start / Stop** an existing workbench
- **List** workbenches in a project
- **Delete** a workbench

**Ask for the target namespace** (required for all operations).

**Validate namespace** is a Data Science Project:

**MCP Tool**: `list_data_science_projects` (from rhoai)

**Parameters**: none

Verify the user-specified namespace appears in the project list. If not, report: "Namespace `[name]` is not an RHOAI Data Science Project. Use `/ds-project-setup` to create one."

**Route to the appropriate sub-workflow:**
- Create -> Step 2
- Start/Stop -> Step 5
- List -> Use `list_workbenches`, display results, done
- Delete -> Step 6

### Step 2: Gather Configuration (Create)

**List available notebook images:**

**MCP Tool**: `list_notebook_images` (from rhoai)

**Parameters**: none

**Present available images** in a table:

| Image Name | Description |
|------------|-------------|
| [name] | [description] |

**Ask the user for workbench configuration:**
- **Workbench name**: DNS-compatible name (lowercase, hyphens, max 63 chars)
- **Image**: Selection from the available images list
- **CPU**: Number of CPU cores (default: 2)
- **Memory**: Memory allocation (default: 8Gi)
- **Storage size**: PVC size for persistent storage (default: 20Gi)
- **GPU** (optional): Number of GPUs to attach (e.g., 1)

**Display configuration table:**

| Setting | Value |
|---------|-------|
| Workbench name | [name] |
| Namespace | [namespace] |
| Image | [image_name] |
| CPU | [cpu] cores |
| Memory | [memory] |
| Storage | [storage_size] |
| GPU | [gpu_count or none] |

**WAIT for user to confirm or modify the configuration.**

### Step 3: Provision Storage (Create)

**Check existing storage:**

**MCP Tool**: `list_storage` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED

If a suitable PVC already exists, ask user if they want to reuse it or create a new one.

**Create PVC for workbench storage:**

**MCP Tool**: `create_storage` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: PVC name (default: `[workbench-name]-storage`) - REQUIRED
- `size`: storage size from Step 2 (e.g., `"20Gi"`) - REQUIRED
- `access_mode`: `"ReadWriteOnce"` - REQUIRED (default, single-pod access)

**Verify creation:**

**MCP Tool**: `list_storage` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED

Confirm the PVC appears and is in `Bound` or `Pending` state.

**Error Handling**:
- If PVC name already exists -> Ask: "PVC `[name]` already exists. Reuse it or create with a different name?"
- If StorageClass not available -> Report: "Default StorageClass not configured. Contact your cluster administrator."
- If quota exceeded -> Report namespace storage quota limits

### Step 4: Create Workbench (Create)

**MCP Tool**: `create_workbench` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name from Step 2 - REQUIRED
- `image`: selected notebook image name from Step 2 - REQUIRED
- `cpu`: CPU cores (e.g., `"2"`) - REQUIRED
- `memory`: memory allocation (e.g., `"8Gi"`) - REQUIRED
- `storage_size`: PVC storage size (e.g., `"20Gi"`) - REQUIRED

**Monitor workbench startup** by polling status:

**MCP Tool**: `get_workbench` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name - REQUIRED

Check until status shows the workbench is running. If status does not become ready within a reasonable polling window (3-4 checks), proceed to report current status and advise user to check back.

**Get notebook URL:**

**MCP Tool**: `get_workbench_url` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name - REQUIRED

**Error Handling**:
- If workbench name already exists -> Report: "Workbench `[name]` already exists. Choose a different name or manage the existing one."
- If image not found -> Re-run `list_notebook_images` and suggest available alternatives
- If RBAC error -> Report insufficient permissions to create Notebook CRs
- If GPU unavailable -> Report: "Requested GPU resources not available on cluster nodes. Reduce GPU count or wait for resources."

**Report to user:**

| Detail | Value |
|--------|-------|
| Workbench | [name] |
| Status | [Running / Starting] |
| Image | [image] |
| Resources | [cpu] CPU, [memory] RAM, [gpu] GPU |
| Storage | [storage_size] |
| URL | [notebook_url] |

**Suggest next steps:**
- Access the notebook at the provided URL (OpenShift authentication required)
- Use `/ds-project-setup` to add data connections to the project
- Use `/model-deploy` when ready to deploy a trained model

### Step 5: Manage Lifecycle (Start/Stop)

**List workbenches to identify the target:**

**MCP Tool**: `list_workbenches` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED

If user did not specify a workbench name, present the list and ask which one to manage.

**For Start:**

Confirm the workbench is currently stopped. If already running, report its URL and current status.

**MCP Tool**: `start_workbench` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name - REQUIRED

**MCP Tool**: `get_workbench_url` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name - REQUIRED

**Output to user**: "Workbench `[name]` started. Access it at: [url]"

**For Stop:**

**WAIT for user confirmation**: "Workbench `[name]` is currently running. Stopping it will interrupt any active sessions. Unsaved work in the notebook may be lost. Proceed? (yes/no)"

**MCP Tool**: `stop_workbench` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name - REQUIRED

**Verify state change:**

**MCP Tool**: `get_workbench` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name - REQUIRED

**Output to user**: "Workbench `[name]` stopped. Persistent storage is preserved. Use `/workbench-manage` to start it again."

**Error Handling**:
- If workbench not found -> List available workbenches and ask user to select
- If already in target state -> Report current state (e.g., "Workbench is already running")

### Step 6: Delete Workbench

**Get workbench details:**

**MCP Tool**: `get_workbench` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name - REQUIRED

**Display workbench details and data loss warning:**

| Detail | Value |
|--------|-------|
| Workbench | [name] |
| Status | [Running / Stopped] |
| Image | [image] |
| Storage | [pvc_name] ([size]) |

**WARNING**: Deleting this workbench will remove the Notebook CR. If the workbench is running, it will be stopped first. Any unsaved notebook work will be lost.

**Ask**: "Delete workbench `[name]`? This action cannot be undone. (yes/no)"

**WAIT for explicit confirmation.**

**MCP Tool**: `delete_workbench` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: workbench name - REQUIRED

**Associated storage cleanup** (separate confirmation):

**Ask**: "The PVC `[pvc_name]` ([size]) associated with this workbench still exists. Delete it too? WARNING: All data in this volume will be permanently lost. (yes/no)"

**WAIT for explicit confirmation.**

If user confirms PVC deletion:

**MCP Tool**: `delete_storage` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: PVC name - REQUIRED

If user declines, report: "PVC `[pvc_name]` preserved. It can be reattached to a new workbench."

**Output to user**: "Workbench `[name]` deleted. [PVC deleted / PVC preserved]."

## Common Issues

For common issues (GPU scheduling, OOMKilled, image pull errors, RBAC), see [common-issues.md](../../docs/references/common-issues.md).

### Issue 1: Notebook Image Not Found

**Error**: `create_workbench` fails with image not found or image reference is invalid

**Cause**: The selected image name does not match any available notebook image, or the image registry is unreachable.

**Solution:**
1. Run `list_notebook_images` to see current available images
2. Verify the exact image name (case-sensitive)
3. If no images are listed, the RHOAI operator may not have imported notebook images -- contact cluster administrator

### Issue 2: PVC Binding Failure

**Error**: PVC remains in `Pending` state, workbench cannot start

**Cause**: The default StorageClass does not support the requested access mode, or no StorageClass is configured.

**Solution:**
1. Check available StorageClasses via `resources_get` (from openshift) on `storageclasses.storage.k8s.io`
2. Use `ReadWriteOnce` access mode (most widely supported)
3. If `ReadWriteMany` is required, verify the StorageClass supports it (e.g., NFS, CephFS)
4. Contact cluster administrator if no StorageClass is available

### Issue 3: Workbench Stuck in Starting

**Error**: Workbench status remains in a starting/initializing state for an extended period

**Cause**: Pod scheduling issues, image pull errors, or resource constraints.

**Solution:**
1. Use `events_list` (from openshift) filtered by namespace to check for pod events
2. Common causes:
   - `ImagePullBackOff`: Image registry unreachable or credentials missing
   - `Insufficient cpu/memory`: Reduce resource requests or free up cluster resources
   - `FailedScheduling`: Node taints or affinity rules preventing scheduling
3. If GPU is requested, verify GPU nodes have available capacity

## Dependencies

### MCP Tools
See [Prerequisites](#prerequisites) for the complete list of required and optional MCP tools.

### Related Skills
- `/ds-project-setup` - Create a Data Science Project (prerequisite: namespace must exist)
- `/model-deploy` - Deploy a trained model from the workbench
- `/ai-observability` - Check GPU inventory before requesting GPU workbenches

### Reference Documentation
- [skill-conventions.md](../../docs/references/skill-conventions.md) - Shared prerequisite, HITL, and security conventions

## Example Usage

**User**: "Create a PyTorch notebook workbench in my ml-team project with 4 CPUs and a GPU"

**Skill response**: Validates `ml-team` is an RHOAI project, lists available notebook images, presents configuration table (PyTorch image, 4 CPU, 8Gi memory, 1 GPU, 20Gi storage), provisions PVC storage, creates workbench, monitors startup, and returns the notebook URL.

## Critical: Human-in-the-Loop Requirements

See [skill-conventions.md](../../docs/references/skill-conventions.md) for general HITL and security conventions.

**Skill-specific checkpoints:**
- Before creating workbench (Step 4): display full configuration table, confirm
- Before stopping a workbench (Step 5): warn about unsaved work, confirm
- Before deleting a workbench (Step 6): display details, warn about data loss, confirm
- Before deleting associated PVC (Step 6): separate confirmation with permanent data loss warning
- **NEVER** auto-delete workbenches or storage
- **NEVER** stop a running workbench without confirmation (user may have unsaved notebook work)

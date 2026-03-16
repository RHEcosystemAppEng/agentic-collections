---
name: pipeline-manage
description: |
  Create, run, schedule, and monitor Data Science Pipelines (Kubeflow Pipelines 2.0) on OpenShift AI.

  Use when:
  - "Run a pipeline in my project"
  - "Schedule a recurring pipeline"
  - "Check my pipeline run status"
  - "List pipeline runs and their logs"
  - "Set up the pipeline server"
  - "Delete a pipeline or pipeline run"

  Handles pipeline server setup, pipeline run submission from YAML, scheduling recurring runs, monitoring execution, and viewing step logs.

  NOT for creating data science projects (use /ds-project-setup).
  NOT for deploying models (use /model-deploy).
  NOT for model training jobs (use training skills).
color: green
model: inherit
---

# /pipeline-manage Skill

Create, run, schedule, and monitor Data Science Pipelines (Kubeflow Pipelines 2.0) on Red Hat OpenShift AI. Handles the full pipeline lifecycle: verifying or setting up the pipeline server (DSPA), submitting pipeline runs from YAML definitions, scheduling recurring runs with cron expressions, monitoring run status with step-level progress, viewing pipeline step logs, and deleting pipeline resources with proper warnings.

## Prerequisites

**Required MCP Server**: `rhoai` ([RHOAI MCP Server](https://github.com/opendatahub-io/rhoai-mcp))

**Required MCP Tools** (from rhoai):
- `list_data_science_projects` - Validate namespace is an RHOAI Data Science Project
- `get_pipeline_server` - Check pipeline server (DSPA) status in a project
- `create_pipeline_server` - Create DSPA with S3 storage configuration
- `delete_pipeline_server` - Delete pipeline server and all pipeline infrastructure
- `list_resources` - List pipeline resources in a namespace (resource_type="pipelines")
- `get_resource` - Get pipeline resource details (resource_type="pipeline")
- `list_resource_names` - Token-efficient pipeline name listing (resource_type="pipelines")
- `resource_status` - Quick pipeline status check (resource_type="pipeline")
- `diagnose_resource` - Full diagnostic for a pipeline (resource_type="pipeline")
- `list_data_connections` - Verify S3 data connections for pipeline artifact storage
- `project_summary` - Project overview including pipeline status

**Required MCP Server**: `openshift` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools** (from openshift):
- `resources_create_or_update` (from openshift) - Create PipelineRun and ScheduledWorkflow CRs
- `resources_list` (from openshift) - List PipelineRun resources by apiVersion/kind
- `resources_get` (from openshift) - Get PipelineRun status and task details
- `resources_delete` (from openshift) - Delete pipeline run resources
- `events_list` (from openshift) - Check pipeline pod events for errors
- `pods_list` (from openshift) - List pipeline step pods
- `pods_log` (from openshift) - Retrieve pipeline step container logs

**Common prerequisites** (KUBECONFIG, OpenShift+RHOAI cluster, verification protocol): See [skill-conventions.md](../references/skill-conventions.md).

**Additional cluster requirements**:
- Target namespace is an RHOAI Data Science Project (label: `opendatahub.io/dashboard: "true"`)
- Pipeline server requires S3-compatible object storage (a data connection must exist in the project)
- Data Science Pipelines operator component enabled in the RHOAI DataScienceCluster

## When to Use This Skill

**Use this skill when you need to:**
- Set up or verify the pipeline server in a Data Science Project
- Submit a pipeline run from a YAML or JSON pipeline definition
- Schedule a recurring pipeline run with a cron expression
- Monitor pipeline run status and step-level progress
- View logs from pipeline steps (especially failing ones)
- List existing pipelines and pipeline runs in a project
- Delete a pipeline run or the pipeline server

**Do NOT use this skill when:**
- You need to create a Data Science Project first (use `/ds-project-setup`)
- You want to deploy a model for inference (use `/model-deploy`)
- You need to manage model training jobs (use training skills)
- You want to register models in the Model Registry (use `/model-registry`)

## Workflow

### Step 1: Determine Intent

Ask the user what they want to do: **Setup** server, **List** pipelines/runs, **Run** pipeline, **Schedule** recurring run, **Monitor** run, **View logs**, **Delete** resources.

Ask for target namespace. Validate via `list_data_science_projects` (from rhoai). If invalid, suggest `/ds-project-setup`.

Route: Setup -> Step 2, List -> Step 3, Run -> Step 4, Schedule -> Step 5, Monitor -> Step 6, Logs -> Step 7, Delete -> Step 8.

### Step 2: Verify / Setup Pipeline Server

Check via `get_pipeline_server` (from rhoai) with `namespace`. If healthy, proceed. If unhealthy, offer diagnostics via `diagnose_resource`. If not exists, offer setup.

**For setup**: Check data connections via `list_data_connections` (from rhoai). If none exist, offer to delegate to `/ds-project-setup`.

**Gather:** S3 data connection name (secret), bucket, endpoint, region (default: `us-east-1`). Present configuration for review. **WAIT for confirmation.**

**MCP Tool**: `create_pipeline_server` (from rhoai)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `object_storage_secret`: S3 credentials secret name - REQUIRED
- `object_storage_bucket`: S3 bucket name - REQUIRED
- `object_storage_endpoint`: S3 endpoint URL - REQUIRED
- `object_storage_region`: S3 region - OPTIONAL (default: `"us-east-1"`)

Poll `get_pipeline_server` until ready or timeout.

**Error Handling**:
- If S3 secret not found -> Suggest creating via `/ds-project-setup`
- If S3 endpoint unreachable -> Advise verifying URL and cluster network access

### Step 3: List Pipelines and Runs

Use `list_resources` (from rhoai) with `resource_type="pipelines"`, `namespace` for detailed listing, or `list_resource_names` for a quick name-only view.

For specific run status: `resource_status` (from rhoai) with `resource_type="pipeline"`, `name`, `namespace`.

For project-wide overview: `project_summary` (from rhoai) with `namespace`.

If pipeline server not configured, suggest setup via Step 2.

### Step 4: Submit a Pipeline Run

Verify pipeline server is ready via `get_pipeline_server` (from rhoai). If not ready, offer Step 2.

**Gather from user:** pipeline definition (file path or inline YAML/JSON), run name (DNS-compatible), pipeline parameters (key-value pairs), service account (default: `pipeline-runner-dspa`).

Read pipeline definition using the Read tool if a file path is provided. Present configuration for review. **WAIT for confirmation.**

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `resource`: PipelineRun CR (apiVersion: `tekton.dev/v1`, kind: `PipelineRun`) with `spec.pipelineSpec` or `spec.pipelineRef`, `spec.params`, `spec.serviceAccountName` - REQUIRED

If the pipeline uses KFP v2 compiled format (Argo-based), adapt apiVersion/kind accordingly.

Proceed to Step 6 to monitor the run.

### Step 5: Schedule a Recurring Pipeline Run

Verify pipeline server is ready (same as Step 4).

**Gather from user:** pipeline reference (name or YAML), schedule (cron expression or natural language), pipeline parameters, max concurrent runs (default: 1), optional start/end time.

Convert natural language to cron if needed. Present schedule configuration for review. **WAIT for confirmation.**

**MCP Tool**: `resources_create_or_update` (from openshift)

**Parameters**:
- `resource`: ScheduledWorkflow CR (apiVersion: `scheduledworkflows.kubeflow.org/v1beta1`, kind: `ScheduledWorkflow`) with `spec.enabled`, `spec.maxConcurrency`, `spec.trigger.cronSchedule.cron`, `spec.trigger.cronSchedule.startTime`/`endTime`, `spec.workflow.spec.params` - REQUIRED

**Error Handling**:
- If ScheduledWorkflow CRD not available -> DSP operator may not support scheduling in this version

### Step 6: Monitor Pipeline Run

**Get run status** via `get_resource` (from rhoai) with `resource_type="pipeline"`, `name`, `namespace`, `verbosity="full"`.

**For deeper diagnostics**: `diagnose_resource` (from rhoai) with `resource_type="pipeline"`, `name`, `namespace`.

**Track step-level progress** via `resources_get` (from openshift) with apiVersion `tekton.dev/v1`, kind `PipelineRun`. Extract task statuses from `.status.childReferences` or `.status.taskRuns`.

**List pipeline pods** via `pods_list` (from openshift) with `namespace` and `labelSelector="tekton.dev/pipelineRun=<run-name>"`.

**Present step progress table:**

| Step | Status | Duration | Message |
|------|--------|----------|---------|
| [step-name] | [Running/Succeeded/Failed] | [duration] | [message] |

**On failure**: Present options: (1) View step logs, (2) Check events, (3) Run diagnostics, (4) Retry. **WAIT for user decision. NEVER auto-retry or auto-delete failed runs.**

**Error Handling**:
- If run not found -> List available runs and ask user to select
- If run still pending -> Check events for scheduling issues

### Step 7: View Pipeline Step Logs

From the PipelineRun status (Step 6), identify the pod name for the failing or target step. If user did not specify a step, list available steps and ask which one to inspect.

**MCP Tool**: `pods_log` (from openshift)

**Parameters**:
- `namespace`: target namespace - REQUIRED
- `name`: pod name of the pipeline step - REQUIRED
- `container`: container name - OPTIONAL (specify if multiple containers)

Also check `events_list` (from openshift) filtered by namespace for scheduling/resource issues.

**Suggest fixes** based on common log patterns: `OOMKilled` -> increase memory limits; `ImagePullBackOff` -> verify image reference; `AccessDenied` on S3 -> check data connection via `/ds-project-setup`; `Permission denied` -> verify ServiceAccount permissions.

**Error Handling**:
- If pod not found -> Pod may have been cleaned up; check events for historical data
- If multiple containers -> List container names and ask user to select

### Step 8: Delete Pipeline Resources

**Delete a pipeline run:**

Get run details via `get_resource` (from rhoai) with `resource_type="pipeline"`, `name`, `namespace`. Display run details (name, status, created, step count).

**Ask**: "Delete pipeline run `<name>`? This will remove the run record and associated pods. (yes/no)" **WAIT for confirmation.**

**MCP Tool**: `resources_delete` (from openshift) with apiVersion `tekton.dev/v1`, kind `PipelineRun`, `name`, `namespace`.

---

**Delete the pipeline server (DESTRUCTIVE):**

Display warning: deleting the DSPA removes all pipeline runs, history, API/UI endpoints, and terminates running pipelines. S3 data is preserved.

**Ask**: "Type the namespace name `<namespace>` to confirm deletion:" **WAIT for typed confirmation. Verify exact match.**

**MCP Tool**: `delete_pipeline_server` (from rhoai) with `namespace`, `confirm=true`.

**Verify** via `get_pipeline_server` (from rhoai). Confirm removal.

**Error Handling**:
- If typed confirmation mismatch -> Cancel deletion
- If RBAC error -> Report insufficient permissions
- If pipeline server not found -> Report no server in namespace

## Common Issues

For common issues (GPU scheduling, OOMKilled, image pull errors, RBAC), see [common-issues.md](../references/common-issues.md).

### Issue 1: Pipeline Server Not Ready
**Cause**: Invalid S3 credentials, unreachable S3 endpoint, or database connectivity issues.
**Solution**: Use `diagnose_resource` for automated diagnostics. Check data connection credentials via `list_data_connections`. Verify S3 bucket accessibility. Check DSPA pod logs for specific errors.

### Issue 2: Pipeline Run Stuck in Pending
**Cause**: Insufficient resources, missing ServiceAccount, unbound PVC, or scheduling issues.
**Solution**: Check events for scheduling errors. Verify ServiceAccount `pipeline-runner-dspa` exists. Check ResourceQuota/LimitRange. For GPU pipelines, verify availability via `/ai-observability`.

### Issue 3: Step OOMKilled
**Cause**: Step container exceeded memory limit.
**Solution**: View step logs before OOM kill. Increase `resources.limits.memory` in the pipeline YAML. Consider streaming data for data-intensive steps.

### Issue 4: S3 Artifact Upload Fails
**Cause**: Expired credentials, missing bucket, or unreachable endpoint.
**Solution**: Verify data connection via `list_data_connections`. Check S3 bucket exists. Re-create data connection if credentials rotated.

### Issue 5: Schedule Not Triggering
**Cause**: Invalid cron, ScheduledWorkflow controller not running, or schedule disabled.
**Solution**: Verify ScheduledWorkflow CR `spec.enabled` is `true`. Validate cron format. Check controller pod logs. Verify `startTime`/`endTime` constraints.

## Dependencies

### MCP Tools
See [Prerequisites](#prerequisites) for the complete list of required MCP tools.

### Related Skills
- `/ds-project-setup` - Create a Data Science Project with data connections (prerequisite for pipeline server)
- `/model-deploy` - Deploy a model produced by a pipeline
- `/model-registry` - Register models produced by pipeline runs
- `/ai-observability` - Check GPU/cluster resources before running resource-intensive pipelines
- `/debug-inference` - Debug models deployed from pipeline outputs

### Reference Documentation
- [skill-conventions.md](../references/skill-conventions.md) - Shared prerequisite, HITL, and security conventions

## Example Usage

**User**: "Set up the pipeline server in my ml-training project and run a data preprocessing pipeline"

**Skill response**: Validates project, sets up pipeline server with S3 data connection after confirmation, monitors readiness, then gathers pipeline YAML, presents run config for confirmation, submits PipelineRun, and monitors step-level progress.

## Critical: Human-in-the-Loop Requirements

See [skill-conventions.md](../references/skill-conventions.md) for general HITL and security conventions.

**Skill-specific checkpoints:**
- Before creating pipeline server (Step 2): display S3 storage configuration, confirm
- Before submitting pipeline run (Step 4): display run configuration table, confirm
- Before scheduling recurring run (Step 5): display cron schedule and parameters, confirm
- On pipeline failure (Step 6): present diagnostic options, wait for user decision
- Before deleting pipeline run (Step 8): display run details, confirm
- Before deleting pipeline server (Step 8): display destructive warning, require typed namespace confirmation
- **NEVER** auto-submit pipeline runs without confirmation
- **NEVER** auto-delete pipeline servers or auto-retry failed runs
- **NEVER** display S3 credentials or secret values in output

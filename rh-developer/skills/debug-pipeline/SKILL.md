---
name: debug-pipeline
description: |
  Diagnose OpenShift Pipelines (Tekton) CI/CD failures including PipelineRun failures, TaskRun step errors, workspace/PVC binding issues, and authentication problems. Automates multi-step diagnosis: PipelineRun status, failed TaskRun analysis, step container logs, and related resource checks. Use this skill when pipelines fail, hang, or produce unexpected results. Triggers on /debug-pipeline command or phrases like "pipeline failed", "PipelineRun error", "TaskRun failed", "tekton error", "pipeline stuck", "pipeline timeout".
metadata:
  user_invocable: "true"
---

# /debug-pipeline Skill

Diagnose OpenShift Pipelines (Tekton) CI/CD failures by automatically gathering PipelineRun status, failed TaskRun details, step container logs, and related resources.

## Prerequisites

Before running this skill:
1. User is logged into OpenShift cluster
2. User has access to the target namespace
3. OpenShift Pipelines operator is installed on the cluster
4. PipelineRun name is known (or can be identified from recent runs)

## Critical: Human-in-the-Loop Requirements

See [Human-in-the-Loop Requirements](../../docs/human-in-the-loop.md) for mandatory checkpoint behavior.

**IMPORTANT:** This skill requires explicit user confirmation at each step. You MUST:
1. **Wait for user confirmation** before executing diagnostic actions
2. **Do NOT proceed** to the next step until the user explicitly approves
3. **Present findings clearly** and ask if user wants deeper analysis
4. **Never auto-execute** remediation actions without user approval

If the user says "no" or wants to focus on specific areas, address their concerns before proceeding.

## Critical: Prefer MCP Tools

**IMPORTANT:** Prefer MCP tools over CLI commands for better integration and user experience:
1. **Search for MCP tools first** - Use `ToolSearch` to load OpenShift MCP tools (e.g., `+openshift resources_get`) before diagnostic actions
2. **Use MCP when available** - Prefer `resources_get`, `resources_list`, `pod_logs`, `events_list` over `oc`/`kubectl` commands

### Tekton CRD Access via MCP

Tekton resources are standard Kubernetes CRDs. Use the generic MCP tools with these parameters:

| Resource | kind | apiVersion |
|----------|------|------------|
| PipelineRun | `PipelineRun` | `tekton.dev/v1` |
| TaskRun | `TaskRun` | `tekton.dev/v1` |
| Pipeline | `Pipeline` | `tekton.dev/v1` |
| Task | `Task` | `tekton.dev/v1` |
| ClusterTask | `ClusterTask` | `tekton.dev/v1beta1` |
| EventListener | `EventListener` | `triggers.tekton.dev/v1beta1` |
| TriggerTemplate | `TriggerTemplate` | `triggers.tekton.dev/v1beta1` |
| TriggerBinding | `TriggerBinding` | `triggers.tekton.dev/v1beta1` |

## Trigger

- User types `/debug-pipeline`
- User says "pipeline failed", "PipelineRun failed", "PipelineRun error"
- User says "TaskRun failed", "task step failed", "tekton error"
- User says "pipeline stuck", "pipeline timeout", "pipeline hanging"
- User says "CI/CD failed", "CI pipeline broken"
- After a CI/CD pipeline reports a failure

## Input Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `PIPELINERUN_NAME` | Name of specific PipelineRun to debug | Latest failed PipelineRun |
| `PIPELINE_NAME` | Pipeline name to find runs for | Auto-detect |
| `NAMESPACE` | Target namespace | Current namespace |

## Workflow

### Step 1: Identify Target PipelineRun

```markdown
## Pipeline Debugging

**Current OpenShift Context:**
- Cluster: [cluster]
- Namespace: [namespace]

Which PipelineRun would you like me to debug?

1. **Specify PipelineRun name** - Enter the PipelineRun name directly
2. **List failed PipelineRuns** - Show recent failed PipelineRuns in current namespace
3. **From Pipeline** - Debug latest run of a specific Pipeline

Select an option or enter a PipelineRun name:
```

**WAIT for user response.** Do NOT proceed until user identifies the target PipelineRun.

If user selects "List failed PipelineRuns":
Use kubernetes MCP `resources_list` with kind `PipelineRun`, filter by Failed status:

```markdown
## Recent Failed PipelineRuns in [namespace]

| PipelineRun | Pipeline | Status | Started | Duration |
|-------------|----------|--------|---------|----------|
| [run-name] | [pipeline] | Failed | [timestamp] | [duration] |

Which PipelineRun would you like me to debug?
```

**WAIT for user to select a PipelineRun.**

### Step 2: Get PipelineRun Status Overview

Use kubernetes MCP `resources_get` for the PipelineRun:

```markdown
## PipelineRun Status: [pipelinerun-name]

**PipelineRun Info:**
| Field | Value |
|-------|-------|
| Pipeline | [pipeline-name] |
| Status | [Succeeded/Failed/Running/Cancelled] |
| Started | [timestamp] |
| Completed | [timestamp or "Still running"] |
| Duration | [duration] |

**Parameters:**
| Name | Value |
|------|-------|
| [param-name] | [param-value] |

**TaskRun Status:**
| Task | TaskRun | Status | Duration |
|------|---------|--------|----------|
| [task-1] | [taskrun-1] | Succeeded | [duration] |
| [task-2] | [taskrun-2] | **Failed** | [duration] |
| [task-3] | [taskrun-3] | Skipped | - |

**Quick Assessment:**
[Based on status conditions - e.g., "PipelineRun failed because TaskRun 'build' failed at step 'build-push'"]

Continue with failed TaskRun analysis? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 3: Analyze Failed TaskRun(s)

Use kubernetes MCP `resources_get` for each failed TaskRun:

```markdown
## Failed TaskRun: [taskrun-name]

**TaskRun Info:**
| Field | Value |
|-------|-------|
| Task | [task-name] |
| Pod | [taskrun-name]-pod |
| Status | [Failed] |
| Reason | [reason from conditions] |

**Step Status:**
| Step | Container | Status | Exit Code | Reason |
|------|-----------|--------|-----------|--------|
| [step-1] | step-[step-1] | Completed | 0 | - |
| [step-2] | step-[step-2] | **Terminated** | [code] | [reason] |
| [step-3] | step-[step-3] | - | - | Skipped |

**Workspace Bindings:**
| Workspace | Type | Resource | Status |
|-----------|------|----------|--------|
| [shared-workspace] | PVC | [pvc-name] | [Bound/Pending] |
| [output] | EmptyDir | - | OK |

**Issues Found:**
- [Issue 1 - e.g., "Step 'build-push' failed with exit code 1"]

Continue to view step logs? (yes/no)
```

**Note:** Tekton names step containers as `step-<step-name>` in the TaskRun pod. Use this convention with `pod_logs`.

**WAIT for user confirmation before proceeding.**

### Step 4: Get TaskRun Pod Logs

Use kubernetes MCP `pod_logs` for the TaskRun pod, targeting the failed step container (`step-<step-name>`):

```markdown
## Step Logs: [step-name] (Pod: [taskrun-name]-pod)

**Failed Step Container:** `step-[step-name]`

```
[log output from the failed step container]
```

**Log Analysis:**

**Errors Found:**
- Line [X]: [error description]

Continue to check related resources? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 5: Check Related Resources

Check resources that could cause pipeline failures:

```markdown
## Related Resources Analysis

**ServiceAccount:**
| Field | Value | Status |
|-------|-------|--------|
| Name | [sa-name] | [OK] |
| Image Pull Secrets | [secrets] | [OK/MISSING] |
| Linked Secrets | [secrets] | [OK/MISSING] |

**Workspaces/PVCs:**
| PVC | Status | Access Mode | Storage |
|-----|--------|-------------|---------|
| [pvc-name] | [Bound/Pending] | [RWO/RWX] | [size] |

**Secrets:**
| Secret | Type | Referenced By | Status |
|--------|------|---------------|--------|
| [git-creds] | kubernetes.io/basic-auth | git-clone task | [OK/MISSING] |
| [registry-creds] | kubernetes.io/dockerconfigjson | push task | [OK/MISSING] |

**Pipeline/Task Definitions:**
| Resource | Exists | Issues |
|----------|--------|--------|
| Pipeline [name] | [Yes/No] | [none / param mismatch] |
| Task [name] | [Yes/No] | [none / not found] |

[If triggered by EventListener:]
**EventListener:**
| Field | Value | Status |
|-------|-------|--------|
| Name | [el-name] | [Running/NotRunning] |
| TriggerTemplate | [tt-name] | [OK/MISSING] |
| TriggerBinding | [tb-name] | [OK/MISSING] |

**Issues Found:**
- [Issue 1]

Continue to full diagnosis summary? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 6: Present Diagnosis Summary

```markdown
## Diagnosis Summary: [pipelinerun-name]

### Root Cause

**Primary Issue:** [Categorized root cause]

| Category | Status | Details |
|----------|--------|---------|
| Pipeline Definition | [OK/FAIL] | [details] |
| TaskRun Execution | [OK/FAIL] | [details] |
| Step Container | [OK/FAIL] | [details] |
| Workspace/PVC | [OK/FAIL] | [details] |
| Authentication | [OK/FAIL] | [details] |
| Resources/Quota | [OK/FAIL] | [details] |

### Detailed Findings

**[Category: e.g., Authentication]**
- Problem: [specific problem]
- Evidence: [from logs/events]
- Impact: [effect on pipeline]

### Recommended Actions

1. **[Action 1]** - [description]
   ```bash
   [command to fix]
   ```

2. **[Action 2]** - [description]
   ```bash
   [command to fix]
   ```

### Retry PipelineRun

After fixing the issue:
```bash
# Rerun using the same PipelineRun spec
oc create -f <(oc get pipelinerun [name] -n [namespace] -o json | jq 'del(.metadata.resourceVersion, .metadata.uid, .metadata.creationTimestamp, .status) | .metadata.name = .metadata.name + "-retry"') -n [namespace]

# Or using tkn CLI (if available)
tkn pipeline start [pipeline-name] --use-pipelinerun [pipelinerun-name] -n [namespace]
```

---

Would you like me to:
1. Execute one of the recommended fixes
2. Retry the PipelineRun
3. Debug the TaskRun pod directly (/debug-pod)
4. View Pipeline or Task definition
5. Exit debugging

Select an option:
```

**WAIT for user to select next action.**

## Pipeline Failure Reference

### Failure Categories

| Category | Failure Type | Key Indicators | Common Fix |
|----------|--------------|----------------|------------|
| **Authentication** | git-clone auth | `could not read Username`, `Permission denied (publickey)` | Add git secret to ServiceAccount |
| **Authentication** | Image push | `unauthorized: access denied` | Add dockerconfigjson secret to ServiceAccount |
| **Workspace** | PVC not bound | `persistentvolumeclaim "X" not found` | Create PVC or use emptyDir |
| **Workspace** | Permission denied | `permission denied` in step logs | Check fsGroup, runAsUser, PVC access mode |
| **Workspace** | Contention | Parallel tasks fail on RWO PVC | Use RWX PVC or separate workspaces |
| **Timeout** | PipelineRun timeout | `PipelineRunTimeout` condition | Increase `spec.timeouts.pipeline` |
| **Timeout** | TaskRun timeout | `TaskRunTimeout` condition | Increase `spec.timeouts.tasks` |
| **Parameter** | Missing param | `missing required parameter` | Add param to PipelineRun spec |
| **Task Step** | Build/test failure | Non-zero exit in step | Check step logs for specific error |
| **Resource** | Pod scheduling | `FailedScheduling` event | Increase quotas or reduce step resource requests |
| **Image** | Step image pull | `ImagePullBackOff` on step container | Fix step image reference or add pull secret |
| **Pipeline** | Task not found | `task "X" not found` | Verify Task name, kind (Task vs ClusterTask), namespace |
| **Trigger** | EventListener down | No PipelineRuns created | Check EventListener pod logs |
| **Trigger** | Binding mismatch | Wrong params extracted | Fix TriggerBinding param paths in CEL expressions |

### git-clone Task Failures

| Issue | Symptom | Solution |
|-------|---------|----------|
| Private repo, no credentials | `could not read Username` | Add `kubernetes.io/basic-auth` secret annotated with `tekton.dev/git-0: https://github.com` to SA |
| SSH key missing | `Permission denied (publickey)` | Add `kubernetes.io/ssh-auth` secret annotated with `tekton.dev/git-0: github.com` to SA |
| Branch not found | `couldn't find remote ref` | Verify `revision` parameter |

### buildah/kaniko Task Failures

| Issue | Symptom | Solution |
|-------|---------|----------|
| Containerfile not found | `unable to open Containerfile/Dockerfile` | Check `DOCKERFILE` parameter path relative to workspace |
| Base image pull | `unauthorized` or `not found` for FROM image | Fix base image ref or add pull secret |
| Build context wrong | `file not found` during COPY/ADD | Fix `CONTEXT` parameter to correct subdirectory |

### Image Push Failures

| Issue | Symptom | Solution |
|-------|---------|----------|
| Registry auth | `unauthorized: access denied` | Add `kubernetes.io/dockerconfigjson` secret annotated with `tekton.dev/docker-0: <registry>` to SA |
| Registry unreachable | `connection refused` / `no such host` | Check registry URL, network policies, egress rules |

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `resources_list` | List PipelineRuns, TaskRuns, PVCs, Secrets, Pipelines, Tasks |
| `resources_get` | Get PipelineRun details, TaskRun details, Pipeline/Task definitions, ServiceAccount, EventListener |
| `pod_logs` | Get TaskRun pod logs for failed step containers (use container name `step-<step-name>`) |
| `pod_list` | Find TaskRun pods |
| `events_list` | Get PipelineRun/TaskRun pod events for scheduling and binding errors |

## Output Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PIPELINERUN_NAME` | Debugged PipelineRun name | `build-and-deploy-run-abc123` |
| `PIPELINE_NAME` | Associated Pipeline | `build-and-deploy` |
| `PIPELINE_NAMESPACE` | Namespace | `my-project` |
| `FAILED_TASKRUN` | Name of the failed TaskRun | `build-and-deploy-run-abc123-build-task` |
| `FAILED_STEP` | Step that failed | `build-push` |
| `FAILURE_CATEGORY` | Categorized failure type | `Authentication` |
| `ROOT_CAUSE` | Identified root cause | `git-clone unauthorized - missing git secret on ServiceAccount` |

## Dependencies

### Required MCP Servers
- `openshift` (kubernetes MCP server)
- `github` (optional, for source repository verification)

### Related Skills
- `/debug-pod` - To debug TaskRun pods directly
- `/debug-build` - If the pipeline uses OpenShift Build tasks
- `/debug-network` - If pipeline tasks fail due to network issues
- `/validate-environment` - To verify OpenShift and pipeline operator setup

## Reference Documentation

For detailed guidance, see:
- [docs/debugging-patterns.md](../../docs/debugging-patterns.md) - Common error patterns and pipeline troubleshooting trees
- [docs/prerequisites.md](../../docs/prerequisites.md) - Required tools (oc), cluster access verification

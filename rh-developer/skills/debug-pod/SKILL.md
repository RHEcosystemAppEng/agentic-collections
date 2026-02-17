---
name: debug-pod
description: |
  Diagnose pod failures on OpenShift including CrashLoopBackOff, ImagePullBackOff, OOMKilled, and pending pods. Automates multi-step diagnosis: pod status, events, logs (current + previous), and resource constraint analysis. Use this skill when pods are not running, restarting frequently, or stuck in non-ready states. Triggers on /debug-pod command or phrases like "my pod is crashing", "pod won't start", "CrashLoopBackOff", "ImagePullBackOff", "OOMKilled".
user_invocable: true
---

# /debug-pod Skill

Diagnose pod failures on OpenShift by automatically gathering status, events, logs, and resource information.

## Prerequisites

Before running this skill:
1. User is logged into OpenShift cluster
2. User has access to the target namespace
3. Pod or deployment name is known (or can be identified from recent deployments)

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
1. **Search for MCP tools first** - Use `ToolSearch` to load OpenShift MCP tools (e.g., `+openshift pods_get`) before diagnostic actions
2. **Use MCP when available** - Prefer `pods_get`, `pods_log`, `events_list`, `resources_get` over `oc`/`kubectl` commands

## Trigger

- User types `/debug-pod`
- User says "my pod is crashing", "pod won't start", "CrashLoopBackOff"
- User says "ImagePullBackOff", "OOMKilled", "pod stuck pending"
- User says "container terminated", "pod restarting"

## Input Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `POD_NAME` | Name of pod to debug | Auto-detect from failed deployment |
| `NAMESPACE` | Target namespace | Current namespace |
| `CONTAINER` | Specific container (for multi-container pods) | All containers |

## Workflow

### Step 1: Identify Target Pod

```markdown
## Pod Debugging

**Current OpenShift Context:**
- Cluster: [cluster]
- Namespace: [namespace]

Which pod would you like me to debug?

1. **Specify pod name** - Enter the pod name directly
2. **List failing pods** - Show pods with issues in current namespace
3. **From deployment** - Debug pods from a specific deployment

Select an option or enter a pod name:
```

**WAIT for user response.** Do NOT proceed until user identifies the target pod.

If user selects "List failing pods":
Use kubernetes MCP `pod_list` with namespace, then filter to show pods NOT in Running/Succeeded state:

```markdown
## Pods with Issues in [namespace]

| Pod | Status | Restarts | Age | Reason |
|-----|--------|----------|-----|--------|
| [pod-name] | CrashLoopBackOff | 5 | 10m | [waiting reason] |
| [pod-name-2] | ImagePullBackOff | 0 | 3m | [waiting reason] |
| [pod-name-3] | Pending | 0 | 15m | [conditions] |

Which pod would you like me to debug?
```

**WAIT for user to select a pod.**

### Step 2: Get Pod Status Overview

Use kubernetes MCP `resources_get` to get pod details:

```markdown
## Pod Status: [pod-name]

**Basic Info:**
| Field | Value |
|-------|-------|
| Namespace | [namespace] |
| Node | [node-name or "Not scheduled"] |
| Status | [phase: Pending/Running/Failed/Succeeded] |
| IP | [pod-ip or "Not assigned"] |
| Created | [timestamp] |

**Container Status:**
| Container | State | Ready | Restarts | Exit Code | Reason |
|-----------|-------|-------|----------|-----------|--------|
| [container-name] | [Waiting/Running/Terminated] | [true/false] | [count] | [code or N/A] | [reason] |

**Quick Assessment:**
[Based on status, provide initial assessment - e.g., "Pod is in CrashLoopBackOff - container keeps crashing after startup"]

Continue with detailed analysis? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 3: Analyze Events

Use kubernetes MCP `events_list` filtered by pod:

```markdown
## Recent Events for [pod-name]

| Time | Type | Reason | Message |
|------|------|--------|---------|
| [timestamp] | [Normal/Warning] | [reason] | [message] |
| [timestamp] | [Normal/Warning] | [reason] | [message] |
| ... |

**Event Analysis:**

[Analyze events and identify key issues:]

**Issues Found:**
- [Issue 1 - e.g., "FailedScheduling: 0/3 nodes available - insufficient memory"]
- [Issue 2 - e.g., "ImagePullBackOff: unauthorized - check image pull secrets"]

Continue to view container logs? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 4: Get Container Logs

Use kubernetes MCP `pod_logs` for current and previous container:

```markdown
## Container Logs: [container-name]

**Current Container Logs** (last 50 lines):
```
[log output]
```

[If container has restarted, also show previous logs:]

**Previous Container Logs** (before last restart):
```
[log output from --previous]
```

**Log Analysis:**

[Analyze logs and identify errors:]

**Errors Found:**
- Line [X]: [error description - e.g., "Connection refused to database on port 5432"]
- Line [Y]: [error description - e.g., "Out of memory - heap allocation failed"]

Continue to analyze resource constraints? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 5: Analyze Resource Constraints

Check resource requests, limits, and actual usage:

```markdown
## Resource Analysis: [pod-name]

**Container: [container-name]**

| Resource | Request | Limit | Status |
|----------|---------|-------|--------|
| Memory | [128Mi] | [512Mi] | [OK / WARNING: OOMKilled] |
| CPU | [100m] | [500m] | [OK / WARNING: throttled] |

**Node Resources (if scheduled):**
| Resource | Allocatable | Allocated | Available |
|----------|-------------|-----------|-----------|
| Memory | [8Gi] | [7.5Gi] | [512Mi] |
| CPU | [4000m] | [3800m] | [200m] |

**Resource Issues:**
- [Issue 1 - e.g., "Container was OOMKilled - memory limit too low for application"]
- [Issue 2 - e.g., "Pod cannot be scheduled - no nodes have 2Gi available memory"]

Continue to full diagnosis summary? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 6: Present Diagnosis Summary

```markdown
## Diagnosis Summary: [pod-name]

### Root Cause

**Primary Issue:** [Categorized root cause]

| Category | Status | Details |
|----------|--------|---------|
| Container Start | [OK/FAIL] | [details] |
| Image Pull | [OK/FAIL] | [details] |
| Resource Scheduling | [OK/FAIL] | [details] |
| Application Health | [OK/FAIL] | [details] |
| Volume Mounts | [OK/FAIL] | [details] |

### Detailed Findings

**[Category 1: e.g., Image Pull Issues]**
- Problem: [specific problem]
- Evidence: [from events/logs]
- Impact: [how this affects the pod]

**[Category 2: e.g., Application Crash]**
- Problem: [specific problem]
- Evidence: [from logs]
- Impact: [how this affects the pod]

### Recommended Actions

1. **[Action 1]** - [description]
   ```bash
   [command to fix - e.g., oc create secret docker-registry...]
   ```

2. **[Action 2]** - [description]
   ```bash
   [command to fix - e.g., oc set resources deployment/app --limits=memory=1Gi]
   ```

3. **[Action 3]** - [description]

### Related Documentation

- [Link to relevant Red Hat KB article if applicable]
- [Link to OpenShift docs for the specific issue]

---

Would you like me to:
1. Execute one of the recommended fixes
2. Dig deeper into a specific area
3. Debug a related resource (Service, Route, ConfigMap)
4. Exit debugging

Select an option:
```

**WAIT for user to select next action.**

## Error Patterns Reference

### Common Pod Failure Categories

| Status | Likely Cause | Key Indicators |
|--------|--------------|----------------|
| **CrashLoopBackOff** | Application crash | Non-zero exit code, error in logs |
| **ImagePullBackOff** | Image access issue | Unauthorized, not found, registry timeout |
| **Pending** | Scheduling issue | Insufficient resources, node selector, taints |
| **OOMKilled** | Memory exhaustion | Exit code 137, memory limit reached |
| **CreateContainerError** | Container config issue | Invalid command, missing secrets/configmaps |
| **Init:Error** | Init container failed | Check init container logs |

### Exit Code Reference

| Exit Code | Meaning | Common Cause |
|-----------|---------|--------------|
| 0 | Success | Normal termination |
| 1 | General error | Application error, exception |
| 126 | Permission denied | Cannot execute entrypoint |
| 127 | Command not found | Invalid entrypoint/command |
| 137 | SIGKILL (OOM) | Memory limit exceeded |
| 139 | SIGSEGV | Segmentation fault |
| 143 | SIGTERM | Graceful shutdown |

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `pod_list` | List pods, find failing pods |
| `resources_get` | Get pod spec, container status, node info |
| `events_list` | Get pod events for scheduling/pull/mount errors |
| `pod_logs` | Get current and previous container logs |
| `resources_list` | Check related resources (secrets, configmaps, PVCs) |

## Output Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POD_NAME` | Debugged pod name | `myapp-5d4f7b8c9-x2k4l` |
| `POD_NAMESPACE` | Pod namespace | `my-project` |
| `FAILURE_CATEGORY` | Categorized failure type | `OOMKilled`, `ImagePull`, `Scheduling` |
| `ROOT_CAUSE` | Identified root cause | `Memory limit 512Mi too low for Java app` |
| `REMEDIATION` | Suggested fix | `Increase memory limit to 1Gi` |

## Dependencies

### Required MCP Servers
- `openshift` (kubernetes MCP server)

### Related Skills
- `/debug-build` - If pod failure is due to bad image from build
- `/debug-network` - If pod is running but service connectivity fails
- `/deploy` - To redeploy after fixing issues

## Reference Documentation

For detailed guidance, see:
- [docs/debugging-patterns.md](../../docs/debugging-patterns.md) - Common error patterns and troubleshooting trees
- [docs/prerequisites.md](../../docs/prerequisites.md) - Required tools (oc), cluster access verification

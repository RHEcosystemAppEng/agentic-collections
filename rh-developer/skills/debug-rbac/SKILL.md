---
name: debug-rbac
description: |
  Diagnose OpenShift RBAC permission failures that cause workloads to fail with 403 Forbidden errors when accessing the Kubernetes API. Automates multi-step diagnosis: pod logs for FORBIDDEN errors, readiness probe failures, ServiceAccount identification, RoleBinding/ClusterRoleBinding analysis, and remediation history for regression detection. Use this skill when pods are running but failing because their ServiceAccount lacks required API permissions. Triggers on /debug-rbac command or phrases like "RBAC denied", "403 forbidden", "pods can't list resources", "missing RoleBinding", "ServiceAccount permission denied".
model: inherit
color: cyan
metadata:
  user_invocable: "true"
---

# /debug-rbac Skill

Diagnose RBAC permission failures on OpenShift by analyzing pod logs, readiness probes, ServiceAccount bindings, and Role/RoleBinding configuration.

## Overview

```
[Identify Deployment] → [Check Pod Status + Logs] → [Identify RBAC Errors] → [Analyze ServiceAccount] → [Check RoleBindings] → [Summary + Fix]
```

**This skill diagnoses:**
- Pods failing with 403 Forbidden errors against the Kubernetes API
- Readiness probes that check API access (`kubectl auth can-i`) returning "no"
- Missing or deleted RoleBindings/ClusterRoleBindings
- ServiceAccounts lacking required permissions (get, list, watch, create, etc.)
- Regression patterns where RBAC bindings are repeatedly removed

## Prerequisites

Before running this skill:
1. User is logged into an OpenShift cluster
2. User has access to the target namespace
3. Deployment or pod name is known (or can be identified from recent events)

## Critical: Human-in-the-Loop Requirements

See [Human-in-the-Loop Requirements](../../docs/human-in-the-loop.md) for mandatory checkpoint behavior.

## When to Use This Skill

Use `/debug-rbac` when a Deployment's pods are running but not ready, and pod logs show `FORBIDDEN` or `403` errors when calling the Kubernetes API. This typically manifests as readiness probe failures when the probe checks API access, or application-level errors when the workload needs to interact with Kubernetes resources.

Do **not** use this skill when:
- Pods are blocked from being created entirely — use `/debug-scc` (SCC admission failures)
- Pods are crashing due to application bugs — use `/debug-pod`
- The issue is network connectivity — use `/debug-network`

## Workflow

### Step 1: Identify Target Deployment

```markdown
## RBAC Debugging

**Current OpenShift Context:**
- Cluster: [cluster]
- Namespace: [namespace]

Which deployment would you like me to debug for RBAC issues?

1. **Specify deployment name** - Enter the deployment name directly
2. **List deployments with issues** - Show deployments with unavailable or not-ready pods
3. **Search recent events** - Find pods with RBAC-related warning events

Select an option or enter a deployment name:
```

**WAIT for user confirmation before proceeding.**

If user selects "List deployments with issues":
Use kubernetes MCP `resources_list` for Deployments, filter to those with not-ready conditions:

```markdown
## Deployments with Issues in [namespace]

| Deployment | Available | Desired | Condition |
|------------|-----------|---------|-----------|
| [deploy-name] | 0 | 1 | MinimumReplicasUnavailable |

Which deployment would you like me to debug?
```

**WAIT for user confirmation before proceeding.**

### Step 2: Check Pod Status and Logs

Use kubernetes MCP `pod_list` to find pods for the Deployment, then `resources_get` for pod details and `pod_logs` for container logs:

```markdown
## Pod Analysis: [pod-name]

**Pod Status:**
| Field | Value |
|-------|-------|
| Phase | Running |
| Ready | false |
| Conditions | ContainersNotReady |
| Restart Count | [count] |

**Readiness Probe:**
| Field | Value |
|-------|-------|
| Type | [exec/httpGet/tcpSocket] |
| Command | [e.g., kubectl auth can-i list pods -n namespace] |
| Failure Count | [count] |
| Last Probe | [timestamp] |
| Message | [e.g., "probe returned: no"] |

**Container Logs (last 50 lines):**

[Highlight FORBIDDEN / 403 errors:]

| Timestamp | Error |
|-----------|-------|
| [time] | FORBIDDEN: pods is forbidden: User "system:serviceaccount:[ns]:[sa]" cannot list resource "pods" in API group "" in namespace "[ns]" |
| [time] | FORBIDDEN: pods is forbidden... (repeated) |

**Quick Assessment:**
[e.g., "Pod is running but readiness probe fails because the ServiceAccount cannot list pods. Logs confirm FORBIDDEN errors since [timestamp]."]

Continue with ServiceAccount analysis? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 3: Identify Required Permissions

Based on the FORBIDDEN error messages and readiness probe command, determine what permissions are needed:

```markdown
## Required Permissions Analysis

**FORBIDDEN Errors Found:**
| Resource | Verb | API Group | Namespace |
|----------|------|-----------|-----------|
| pods | list | "" (core) | [namespace] |
| pods | get | "" (core) | [namespace] |
| [other resources from logs] | [verb] | [group] | [namespace] |

**Readiness Probe Requires:**
| Permission | Currently Granted? |
|------------|-------------------|
| list pods in [namespace] | NO — probe returns "no" |

**Application Function Requires:**
| Permission | Evidence |
|------------|----------|
| get pods in [namespace] | Container main loop calls `kubectl get pods` |
| [other] | [from log analysis] |

**Minimum Role Needed:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: [sa-name]-role
  namespace: [namespace]
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```

Continue to check existing RoleBindings? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 4: Analyze ServiceAccount and RoleBindings

Use kubernetes MCP `resources_get` for the ServiceAccount, and `resources_list` for RoleBindings in the namespace:

```markdown
## ServiceAccount & RoleBinding Analysis

**ServiceAccount:** [sa-name] (namespace: [namespace])
| Field | Value |
|-------|-------|
| Exists | Yes |
| Created | [timestamp] |
| Secrets | [count] |
| Image Pull Secrets | [count] |

**RoleBindings in [namespace]:**
| RoleBinding | Role | Subjects | Grants Access? |
|-------------|------|----------|----------------|
| [binding-1] | [role-name] | [sa-1, sa-2] | [Yes/No — wrong SA] |
| [binding-2] | [role-name] | [sa-name] | [Missing — binding not found] |

**ClusterRoleBindings (if accessible):**
| ClusterRoleBinding | ClusterRole | Subjects | Grants Access? |
|--------------------|-------------|----------|----------------|
| [binding] | [role] | [subjects] | [Yes/No] |

[If listing RoleBindings is forbidden:]
**Note:** Agent lacks permission to list RoleBindings directly. Absence of the required binding is inferred from the FORBIDDEN errors in pod logs.

**Assessment:**
[e.g., "No RoleBinding grants the metrics-collector ServiceAccount 'list pods' in demo-rbac. The binding was either never created, or was deleted."]

Continue to diagnosis summary? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 5: Present Diagnosis Summary

```markdown
## RBAC Diagnosis Summary: [deployment-name]

### Root Cause

**Primary Issue:** [e.g., "Missing RoleBinding for ServiceAccount 'metrics-collector' — cannot list pods in namespace 'demo-rbac'"]

| Category | Status | Details |
|----------|--------|---------|
| Pod Running | OK | Pod is scheduled and container is running |
| Pod Ready | FAIL | Readiness probe fails — API access denied |
| ServiceAccount | EXISTS | [sa-name] in [namespace] |
| RoleBinding | MISSING | No binding grants required permissions |
| API Access | DENIED | 403 FORBIDDEN on [verbs] [resources] |

### Causal Chain (Five Whys)

1. **Signal**: Deployment [name] has 0 available replicas (MinimumReplicasUnavailable)
2. **Why?** Pod readiness probe (`kubectl auth can-i list pods`) returns "no"
3. **Why?** ServiceAccount [sa-name] lacks a RoleBinding granting `list` on `pods`
4. **Why?** The required Role/RoleBinding is absent or was deleted
5. **Root Cause**: [e.g., "Missing RBAC resources for this ServiceAccount — the binding was never created or was removed by a cleanup process/GitOps drift"]

### Recommended Actions

**Option A: Create the missing Role and RoleBinding (recommended)**

```bash
# Create the Role
oc create role [sa-name]-pod-reader \
  --verb=get,list,watch \
  --resource=pods \
  -n [namespace]

# Create the RoleBinding
oc create rolebinding [sa-name]-pod-reader-binding \
  --role=[sa-name]-pod-reader \
  --serviceaccount=[namespace]:[sa-name] \
  -n [namespace]
```

**Option B: Use an existing ClusterRole**

If a suitable ClusterRole already exists (e.g., `view`):

```bash
oc create rolebinding [sa-name]-view \
  --clusterrole=view \
  --serviceaccount=[namespace]:[sa-name] \
  -n [namespace]
```

⚠️ **Note**: The `view` ClusterRole grants read access to most resources in the namespace. Use a custom Role (Option A) for least-privilege.

**After applying the fix, verify:**

```bash
# Check if the SA now has permission
oc auth can-i list pods -n [namespace] --as=system:serviceaccount:[namespace]:[sa-name]

# Check pod readiness
oc get pods -n [namespace] -l app=[app-label] -o wide
```

### Regression Warning

[If regression detected from remediation history:]
⚠️ **Regression detected**: [N] prior remediation attempts applied the same fix but it was subsequently undone. Investigate whether a GitOps controller, security audit script, or namespace policy is removing the RoleBinding. Ensure the binding is added to the authoritative source of truth (Helm chart, Kustomize overlay, ArgoCD Application) rather than applied ad-hoc.

### Related Documentation

- [OpenShift RBAC documentation](https://docs.openshift.com/container-platform/latest/authentication/using-rbac.html)
- [Kubernaut RBAC failure golden transcript](https://github.com/jordigilh/kubernaut-demo-scenarios/blob/feature/v1.4-new-scenarios/golden-transcripts/rbac-failure-rbacpolicydenied.json)

---

Would you like me to:
1. Execute Option A (create Role + RoleBinding)
2. Execute Option B (bind existing ClusterRole)
3. Investigate who is removing the binding (if regression)
4. Dig deeper into a specific area
5. Exit debugging

Select an option:
```

**WAIT for user confirmation before proceeding.**

## Dependencies

### Required MCP Servers
- `openshift` - Kubernetes/OpenShift resource access for Deployments, Pods, ServiceAccounts, Roles, RoleBindings, and Events

### Related Skills
- `/debug-scc` - If pods are blocked from creation by SCC admission (different from RBAC)
- `/debug-pod` - If pods are crashing due to application issues, not RBAC
- `/debug-network` - If pods can't reach services (network, not API access)

### Reference Documentation
- [docs/debugging-patterns.md](../../docs/debugging-patterns.md) - Common error patterns and troubleshooting trees
- [docs/prerequisites.md](../../docs/prerequisites.md) - Required tools (oc), cluster access verification

---
name: debug-scc
description: |
  Diagnose OpenShift Security Context Constraint (SCC) violations that prevent pods from being created. Automates multi-step diagnosis: Deployment status, ReplicaSet FailedCreate events, security context field extraction, SCC rejection parsing, and ServiceAccount SCC binding analysis. Use this skill when pods are blocked from scheduling with "unable to validate against any security context constraint" errors. Triggers on /debug-scc command or phrases like "SCC violation", "pod blocked by SCC", "security context constraint", "FailedCreate forbidden", "unable to validate against any security context constraint".
model: inherit
color: cyan
metadata:
  user_invocable: "true"
---

# /debug-scc Skill

Diagnose OpenShift SCC violations that block pod creation by analyzing security context fields, SCC rejection messages, and ServiceAccount bindings.

## Overview

```
[Identify Deployment] → [Check ReplicaSet Status] → [Parse SCC Rejections] → [Analyze SecurityContext] → [Check SA Bindings] → [Summary + Fix]
```

**This skill diagnoses:**
- Pods blocked by SCC admission (`FailedCreate` events)
- `runAsUser` violations (running as root when restricted)
- Forbidden capabilities (`NET_ADMIN`, `SYS_PTRACE`, etc.)
- `allowPrivilegeEscalation` rejections
- ServiceAccount lacking SCC bindings
- `hostUsers`, `hostNetwork`, `hostPID` violations

## Prerequisites

Before running this skill:
1. User is logged into an OpenShift cluster
2. User has access to the target namespace
3. Deployment or pod name is known (or can be identified from recent events)

## Critical: Human-in-the-Loop Requirements

See [Human-in-the-Loop Requirements](../../docs/human-in-the-loop.md) for mandatory checkpoint behavior.

## When to Use This Skill

Use `/debug-scc` when a Deployment has zero available replicas and ReplicaSet events show `FailedCreate` with messages containing "unable to validate against any security context constraint" or "is forbidden". This indicates the pod spec requests capabilities, UID/GID settings, or volume types that violate the namespace's SCC policy.

Do **not** use this skill when pods are failing for other reasons (CrashLoopBackOff, ImagePullBackOff, OOMKilled) — use `/debug-pod` instead.

## Workflow

### Step 1: Identify Target Deployment

```markdown
## SCC Violation Debugging

**Current OpenShift Context:**
- Cluster: [cluster]
- Namespace: [namespace]

Which deployment would you like me to debug for SCC violations?

1. **Specify deployment name** - Enter the deployment name directly
2. **List deployments with issues** - Show deployments with unavailable replicas
3. **Search by event** - Find deployments with FailedCreate events

Select an option or enter a deployment name:
```

**WAIT for user confirmation before proceeding.**

If user selects "List deployments with issues":
Use kubernetes MCP `resources_list` for Deployments, filter to those with unavailable replicas:

```markdown
## Deployments with Issues in [namespace]

| Deployment | Available | Desired | Conditions |
|------------|-----------|---------|------------|
| [deploy-name] | 0 | 1 | ReplicaFailure |

Which deployment would you like me to debug?
```

**WAIT for user confirmation before proceeding.**

### Step 2: Get Deployment and ReplicaSet Status

Use kubernetes MCP `resources_get` for the Deployment, then identify the failing ReplicaSet:

```markdown
## Deployment Status: [deployment-name]

**Deployment Info:**
| Field | Value |
|-------|-------|
| Namespace | [namespace] |
| Replicas | 0/[desired] available |
| Strategy | [RollingUpdate/Recreate] |
| Condition | [ReplicaFailure / MinimumReplicasUnavailable] |

**ReplicaSets:**
| ReplicaSet | Desired | Ready | Status |
|------------|---------|-------|--------|
| [rs-name-new] | 1 | 0 | FailedCreate |
| [rs-name-old] | 0 | 0 | Scaled down |

**Quick Assessment:**
[e.g., "Deployment triggered a rollout but the new ReplicaSet cannot create pods — SCC admission is rejecting the pod spec."]

Continue with SCC rejection analysis? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 3: Parse SCC Rejection Messages

Use kubernetes MCP `events_list` filtered by namespace, and `resources_get` for the failing ReplicaSet to extract the `ReplicaFailure` condition message:

```markdown
## SCC Rejection Analysis: [rs-name]

**FailedCreate Events:** [count] occurrences since [first-seen]

**SCC Violations Detected:**

| Violation | SCC | Field | Current Value | Allowed |
|-----------|-----|-------|---------------|---------|
| [runAsUser] | restricted-v2 | .containers[0].runAsUser | 0 (root) | [range] |
| [capability] | restricted-v2 | .containers[0].capabilities.add | NET_ADMIN | not permitted |
| [escalation] | restricted-v2 | .containers[0].allowPrivilegeEscalation | true | false required |

**SCCs Attempted:**
| SCC | Result | Reason |
|-----|--------|--------|
| restricted-v2 | Rejected | [specific violations] |
| restricted-v3 | Rejected | [specific violations] |
| anyuid | Forbidden | Not usable by user or serviceaccount |
| privileged | Forbidden | Not usable by user or serviceaccount |

**Key Finding:**
[e.g., "The container requests root (UID 0), NET_ADMIN capability, and privilege escalation — all rejected by restricted-v2/v3. Permissive SCCs (anyuid, privileged) are Forbidden because the ServiceAccount has no binding to them."]

Continue to inspect the container security context? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 4: Analyze Container SecurityContext

Use kubernetes MCP `resources_get` for the Deployment to extract the full security context:

```markdown
## SecurityContext Analysis: [deployment-name]

**Pod-level SecurityContext:**
| Field | Value | Compliant? |
|-------|-------|------------|
| runAsNonRoot | [true/false/unset] | [YES/NO] |
| seccompProfile | [RuntimeDefault/unset] | [YES/NO] |
| fsGroup | [value/unset] | [YES/NO] |
| hostUsers | [true/false/null] | [YES/NO — restricted-v3 requires false] |

**Container-level SecurityContext (container: [name]):**
| Field | Value | Compliant? |
|-------|-------|------------|
| runAsUser | [0/unset/value] | [YES/NO — 0 is root] |
| allowPrivilegeEscalation | [true/false/unset] | [YES/NO] |
| capabilities.add | [list or none] | [YES/NO — restricted SCCs drop ALL] |
| capabilities.drop | [list or ALL] | [YES/NO] |
| privileged | [true/false/unset] | [YES/NO] |
| readOnlyRootFilesystem | [true/false/unset] | [INFO] |

**Change History (from managedFields):**
| Timestamp | Manager | Fields Changed |
|-----------|---------|----------------|
| [time] | kubectl-patch | securityContext.runAsUser, capabilities.add, allowPrivilegeEscalation |
| [time] | kubectl-client-side-apply | initial creation |

**Assessment:**
[e.g., "A kubectl patch at [timestamp] introduced root UID, NET_ADMIN, and privilege escalation — overriding the originally compliant spec."]

Continue to check ServiceAccount SCC bindings? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 5: Check ServiceAccount SCC Bindings

Use kubernetes MCP `resources_list` for ServiceAccounts in the namespace. Note: listing cluster-scoped SecurityContextConstraints may be forbidden depending on RBAC — the skill handles this gracefully by inferring from rejection messages.

```markdown
## ServiceAccount Analysis

**ServiceAccount used by Deployment:** [sa-name] (namespace: [namespace])

**Available Information:**
| Check | Result |
|-------|--------|
| SA exists | [Yes/No] |
| Custom SA or default | [custom/default] |
| SCC bindings visible | [Yes/Forbidden — inferred from rejection messages] |

**SCC Access (from rejection messages):**
| SCC | Access |
|-----|--------|
| restricted-v2 | Available (but pod spec violates it) |
| restricted-v3 | Available (but pod spec violates it) |
| anyuid | Forbidden — SA has no binding |
| privileged | Forbidden — SA has no binding |
| [others] | Forbidden — SA has no binding |

**Assessment:**
[e.g., "The SA 'default' only has access to restricted-v2/v3. The pod spec must be fixed to comply with restricted SCC, OR the SA needs a RoleBinding to a permissive SCC (if elevated privileges are genuinely required)."]

Continue to diagnosis summary? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 6: Present Diagnosis Summary

```markdown
## SCC Violation Diagnosis Summary: [deployment-name]

### Root Cause

**Primary Issue:** [e.g., "kubectl patch introduced privileged security context settings that violate all available SCCs"]

| Category | Status | Details |
|----------|--------|---------|
| Pod Admission | BLOCKED | SCC rejects pod spec |
| SecurityContext | NON-COMPLIANT | [specific violations] |
| ServiceAccount | [OK/MISSING BINDING] | [sa-name] — [SCC access] |
| Change Attribution | [IDENTIFIED/UNKNOWN] | [manager and timestamp from managedFields] |

### Causal Chain (Five Whys)

1. **Signal**: [deployment] has 0 available replicas
2. **Why?** ReplicaSet [rs-name] cannot create pods — [N] FailedCreate events
3. **Why?** Every available SCC rejects the pod spec
4. **Why?** Container securityContext specifies [violations]
5. **Root Cause**: [e.g., "A kubectl patch at [timestamp] modified the securityContext to introduce non-compliant settings"]

### Recommended Actions

**Option A: Fix the SecurityContext (recommended if elevated privileges are NOT needed)**

Remove the non-compliant fields to restore restricted SCC compliance:

```bash
oc patch deployment [deployment-name] -n [namespace] --type json -p '[
  {"op": "remove", "path": "/spec/template/spec/containers/0/securityContext/runAsUser"},
  {"op": "replace", "path": "/spec/template/spec/containers/0/securityContext/allowPrivilegeEscalation", "value": false},
  {"op": "remove", "path": "/spec/template/spec/containers/0/securityContext/capabilities/add"}
]'
```

**Option B: Grant SCC binding (only if elevated privileges are genuinely required)**

Create a RoleBinding to a permissive SCC for the ServiceAccount:

```bash
oc adm policy add-scc-to-user anyuid -z [sa-name] -n [namespace]
```

⚠️ **Warning**: Granting anyuid/privileged SCCs weakens namespace security. Only use if the workload genuinely requires elevated privileges.

**Option C: Rollback to previous revision**

```bash
oc rollout undo deployment/[deployment-name] -n [namespace]
```

### Related Documentation

- [OpenShift SCC documentation](https://docs.openshift.com/container-platform/latest/authentication/managing-security-context-constraints.html)
- [Kubernaut SCC violation golden transcript](https://github.com/jordigilh/kubernaut-demo-scenarios/blob/feature/v1.4-new-scenarios/golden-transcripts/scc-violation-sccviolationpodblocked.json)

---

Would you like me to:
1. Execute Option A (fix SecurityContext)
2. Execute Option B (grant SCC binding)
3. Execute Option C (rollback)
4. Dig deeper into a specific area
5. Exit debugging

Select an option:
```

**WAIT for user confirmation before proceeding.**

## Dependencies

### Required MCP Servers
- `openshift` - Kubernetes/OpenShift resource access for Deployments, ReplicaSets, Events, ServiceAccounts, and SecurityContextConstraints

### Related Skills
- `/debug-pod` - If pods exist but are crashing (CrashLoopBackOff, OOMKilled)
- `/debug-rbac` - If pods run but fail with 403 Forbidden API errors (RBAC, not SCC)

### Reference Documentation
- [docs/debugging-patterns.md](../../docs/debugging-patterns.md) - Common error patterns and troubleshooting trees
- [docs/prerequisites.md](../../docs/prerequisites.md) - Required tools (oc), cluster access verification

---
name: incident-triage
description: |
  Structured incident investigation for OpenShift using the Five Whys methodology, investigation guardrails, Prometheus metric analysis, and adversarial due diligence. Orchestrates multi-resource diagnosis across Deployments, ReplicaSets, Pods, Services, and cluster resources to trace from observed symptoms to root cause. Use this skill for complex incidents that span multiple resources or when existing debug skills have not resolved the issue. Triggers on /incident-triage command or phrases like "investigate this incident", "triage this alert", "root cause analysis", "why is this failing", "five whys", "what caused this outage".
model: inherit
color: cyan
metadata:
  user_invocable: "true"
---

# /incident-triage Skill

Structured incident investigation for OpenShift — traces from symptoms to root cause using Five Whys, investigation guardrails, and adversarial due diligence.

## Overview

```
[Gather Context] → [Hierarchical Investigation] → [Evidence + Metrics] → [Five Whys RCA] → [Due Diligence] → [Findings + Actions]
```

**This skill provides:**
- Structured Five Whys methodology for causal depth
- Multi-resource investigation across the Kubernetes ownership chain
- Prometheus metric analysis for resource trends and saturation
- 5 investigation guardrails to prevent shallow or biased conclusions
- 8-dimension adversarial due diligence framework
- Skill chaining to specialized debug skills when a single-resource issue is identified

**Use this skill instead of individual debug skills when:**
- The incident spans multiple resources or namespaces
- The root cause is unclear after initial investigation
- You need a structured RCA with confidence scoring
- An alert fired and you need to trace from symptom to cause
- A predicted issue (e.g., from `predict_linear`) needs proactive assessment

## Prerequisites

Before running this skill:
1. User is logged into an OpenShift cluster
2. User has access to the target namespace(s)
3. An incident description is available (alert, error message, observed symptom, or predicted issue)

## Critical: Human-in-the-Loop Requirements

See [Human-in-the-Loop Requirements](../../docs/human-in-the-loop.md) for mandatory checkpoint behavior.

## Workflow

### Step 1: Gather Incident Context

```markdown
## Incident Triage

**Current OpenShift Context:**
- Cluster: [cluster]
- Namespace: [namespace]

Describe the incident you'd like me to investigate:

1. **Alert-based** - An alert fired (paste the alert name, message, or annotation)
2. **Symptom-based** - Something is broken (describe what you observe)
3. **Proactive** - A predicted issue needs assessment (e.g., capacity forecast, trend alert)
4. **Specify resource** - Investigate a specific resource directly

Select an option or describe the incident:
```

**WAIT for user confirmation before proceeding.**

Use kubernetes MCP `resources_get` to confirm the target resource exists and capture its current state.

**If the incident maps clearly to a single-resource pattern:**

```markdown
## Quick Route Assessment

Based on your description, this appears to be a [category] issue:

| Pattern | Suggested Skill | Confidence |
|---------|----------------|------------|
| SCC admission rejection (FailedCreate + "unable to validate against any security context constraint") | `/debug-scc` | High |
| RBAC 403 Forbidden in pod logs | `/debug-rbac` | High |
| Pod CrashLoopBackOff / OOMKilled / ImagePullBackOff | `/debug-pod` | High |
| Service/Route connectivity failure | `/debug-network` | High |
| Build failure | `/debug-build` | High |

Would you like to:
1. **Route to [skill]** - Use the specialized skill for faster resolution
2. **Continue with full triage** - Proceed with structured investigation (recommended for complex or unclear issues)

Select an option:
```

**WAIT for user confirmation before proceeding.**

**If proactive mode selected:**

```markdown
## Proactive Investigation Mode

This is a PROACTIVE signal — the incident has NOT yet occurred.

**Investigation focus changes:**
- Assess current resource utilization trends
- Evaluate recent deployments and configuration changes
- Determine if the prediction is likely to materialize
- Recommend PREVENTIVE action if warranted
- **"No action needed" is a valid outcome** if the prediction is unlikely to materialize

Proceeding with proactive assessment...
```

### Step 2: Hierarchical Investigation

Follow the Kubernetes ownership chain from the target resource downward. The goal is to understand the full state of the workload, not just the resource that reported the symptom.

**Investigation rules:**
- **Trace the ownership chain**: For Deployments, inspect Deployment -> ReplicaSet -> Pod -> Container. For StatefulSets, inspect StatefulSet -> Pod -> Container.
- **Always check describe AND logs**: A resource reporting "Running" does not mean it is healthy. Check logs for runtime errors even when status looks clean.
- **Check both current and previous logs**: A pod restart means current logs may not contain relevant pre-restart data. Use both `pod_logs` and previous container logs.
- **Pod sampling limit**: If the issue affects many pods in the same workload, check up to 3 representative pods. No need to check every pod.
- **Specific answers required**: Do not say "the pod is pending" without explaining WHY. Do not say "affinity doesn't match" without specifying WHICH label.

Use kubernetes MCP tools:
- `resources_get` for Deployment, ReplicaSet, StatefulSet details
- `pod_list` to find pods owned by the workload
- `pod_logs` for container logs (current and previous)
- `events_list` for namespace events filtered by resource

```markdown
## Hierarchical Investigation: [resource-name]

**Ownership Chain:**
| Level | Resource | Status | Key Finding |
|-------|----------|--------|-------------|
| Workload | [Deployment/name] | [Available/Degraded] | [condition summary] |
| ReplicaSet | [rs-name] | [Ready/FailedCreate] | [replica count, condition] |
| Pod | [pod-name] | [Running/Pending/Failed] | [phase, ready status] |
| Container | [container-name] | [Running/Waiting/Terminated] | [state, exit code, reason] |

**Events (last 30 minutes):**
| Time | Type | Reason | Object | Message |
|------|------|--------|--------|---------|
| [time] | [Normal/Warning] | [reason] | [resource] | [message] |

**Log Analysis (container: [name]):**
[Key errors or patterns found in logs]

**Initial Hypothesis:**
[Based on resource state, events, and logs — what appears to be happening?]

Continue with evidence collection and metric analysis? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 3: Evidence Collection and Guardrails

Before reaching any conclusion, apply these investigation guardrails:

1. **Exhaustive Verification**: Inspect ALL resources mentioned in the signal, error messages, and annotations. Partial evidence does not rule out the problem. Check upstream and downstream dependencies.

2. **Contradicting Evidence Search**: After forming a hypothesis, explicitly search for evidence that CONTRADICTS it. If you cannot find contradicting evidence, note what you searched for.

3. **Causal Depth**: If the identified cause can itself be explained by a deeper cause, keep investigating. The signal resource often reports the symptom; the root cause is typically in a different resource.

4. **Evidence-Based Claims Only**: Every claim must trace to specific tool output. If you cannot verify a claim, state it as unverified.

5. **Investigation Error Separation**: Distinguish between "I found error X caused this problem" and "I encountered errors during investigation that prevented analysis." Permission errors (e.g., `Forbidden`) are obstacles to YOUR investigation, not necessarily the incident's root cause.

**Permission Error Handling:**
If you encounter `Error from server (Forbidden):` during investigation:
- Identify the missing resource, API group, and verbs from the error
- Report the gap as an investigation limitation
- Do NOT conflate investigation permission errors with the incident's root cause

**Prometheus Metric Analysis:**

Use the observability MCP to investigate resource trends and saturation:

**Discovery pattern:**
1. `get_metric_names` with `match` filter (e.g., `{__name__=~".*memory.*|.*oom.*"}` for memory issues, `{__name__=~".*fs.*|.*disk.*"}` for disk issues)
2. `get_metric_metadata` to confirm metric type (counter vs gauge) before querying
3. `get_series` with a specific selector to discover available label sets

**Query patterns:**
- Use `topk(10, ...)` or `bottomk(10, ...)` to limit cardinality
- For counters, always wrap with `rate()` or `increase()`
- Break down per-workload with `by (pod, namespace, container)`
- Scope queries with `{namespace="<target>"}`
- For capacity forecasting, use `predict_linear(<metric>[6h], 3600 * 24)`

**Truncation awareness:** Prometheus responses may be truncated. If truncated, narrow with more specific label selectors or `topk()` rather than assuming partial data is complete.

```markdown
## Evidence Summary

**Guardrail Compliance:**
| Guardrail | Status | Notes |
|-----------|--------|-------|
| Exhaustive Verification | [PASS/GAP] | [what was checked, what was missed] |
| Contradicting Evidence | [PASS/GAP] | [what was searched for] |
| Causal Depth | [PASS/GAP] | [depth reached] |
| Evidence-Based Claims | [PASS/GAP] | [unverified claims, if any] |
| Error Separation | [PASS/N/A] | [investigation errors encountered] |

**Metric Analysis (if applicable):**
| Metric | Current Value | Trend | Threshold | Assessment |
|--------|--------------|-------|-----------|------------|
| [metric-name] | [value] | [rising/stable/falling] | [threshold] | [OK/WARNING/CRITICAL] |

**Cross-Resource Findings:**
[Evidence gathered from upstream/downstream resources, other namespaces, or cluster-level resources]

Continue to root cause analysis? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 4: Root Cause Analysis (Five Whys)

Construct the causal chain from the observed signal to the deepest reachable root cause:

```markdown
## Root Cause Analysis

### Causal Chain (Five Whys)

1. **Signal**: [What was observed — the alert, symptom, or prediction]
2. **Why?** [First-level cause — what directly caused the signal]
3. **Why?** [Second-level cause — what caused the first-level cause]
4. **Why?** [Third-level cause — deeper configuration or state issue]
5. **Root Cause**: [Deepest identifiable cause — the configuration, change, or condition that triggered the chain]

### Remediation Target

| Field | Value |
|-------|-------|
| Kind | [Deployment/StatefulSet/ConfigMap/etc.] |
| Name | [resource-name] |
| Namespace | [namespace] |
| Why this target? | [This is the resource whose configuration change fixes the problem, NOT the resource that reported the symptom] |

### Signal Classification

| Field | Value |
|-------|-------|
| Root cause matches input signal? | [Yes/No — if No, the signal was a symptom] |
| Actual signal name | [e.g., if input was OOMKilled but root cause is NodePressure] |
| Severity | [critical/high/medium/low] |
| Investigation type | [Reactive RCA / Proactive Prevention] |

[If proactive mode:]
**Prediction Assessment:**
- Likelihood of materialization: [High/Medium/Low]
- Time horizon: [estimated time until incident]
- Recommendation: [Preventive action / Monitor / No action needed]

Continue to due diligence review? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 5: Adversarial Due Diligence

Before finalizing findings, perform a comprehensive self-review across 8 dimensions. This prevents shallow analysis, targeting errors, and overconfident conclusions.

```markdown
## Adversarial Due Diligence Review

| Dimension | Assessment |
|-----------|------------|
| **1. Causal Completeness** | [Have you traced the full chain from signal to deepest root cause? Could the identified root cause be explained by a yet deeper cause?] |
| **2. Target Accuracy** | [Is the remediation target the resource whose configuration change fixes the problem? Or are you targeting the symptom reporter? Signals propagate upward; fixes apply to the misconfigured resource.] |
| **3. Evidence Sufficiency** | [Is every claim backed by specific tool output? Which claims are assumptions? What data sources were inaccessible?] |
| **4. Alternative Hypotheses** | [What alternative root causes did you consider? What contradicting evidence did you search for? Were alternatives explicitly ruled out with evidence?] |
| **5. Scope Completeness** | [Did you investigate ALL resources mentioned in the signal? Did you check upstream and downstream dependencies? What was NOT examined?] |
| **6. Proportionality** | [Does the remediation target match the scope of the problem? Is the fix targeted and specific, or overly broad?] |
| **7. Regression Awareness** | [Has this issue occurred before? Are there recent events suggesting a recurring pattern? If unknown, state "No prior history available."] |
| **8. Confidence Calibration** | [Start at 1.0 and list each factor that reduced confidence: unverified claims, inaccessible data, permission gaps, remaining alternative hypotheses. Final score: X.XX] |

**Overall Confidence: [0.XX]**

[If confidence < 0.7:]
**WARNING**: Confidence is below 0.7. Consider:
- Gathering additional evidence before acting
- Escalating to a human operator for review
- Running targeted debug skills for specific resource types

Proceed to findings summary? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 6: Present Findings and Recommend Actions

```markdown
## Incident Triage Findings

### Summary

**Root Cause:** [One-sentence root cause description]

**Severity:** [critical/high/medium/low] | **Confidence:** [0.XX]

### Causal Chain

1. [Signal → first cause]
2. [First cause → second cause]
3. [Second cause → root cause]

### Remediation Target

**[Kind]/[name]** in namespace **[namespace]**

### Contributing Factors

- [Factor 1 — specific evidence]
- [Factor 2 — specific evidence]
- [Factor 3 — specific evidence]

### Recommended Actions

1. **[Primary fix]** — [description]
   ```bash
   [oc command to apply the fix]
   ```

2. **[Secondary fix or preventive measure]** — [description]
   ```bash
   [oc command]
   ```

3. **[Monitoring/follow-up]** — [description]

### Verification

After applying the fix:
```bash
# Verify the resource is healthy
oc get [resource-type] [name] -n [namespace]

# Check events for new issues
oc get events -n [namespace] --sort-by='.lastTimestamp' | tail -20

# Verify pods are running
oc get pods -n [namespace] -l [app-label]
```

### Related Skills

| For this follow-up... | Use skill |
|----------------------|-----------|
| Fix SCC violations | `/debug-scc` |
| Restore RBAC bindings | `/debug-rbac` |
| Debug crashing pods | `/debug-pod` |
| Fix network/route issues | `/debug-network` |
| Redeploy after fix | `/deploy` |

### Reference

- [Kubernaut demo scenario golden transcripts](https://github.com/jordigilh/kubernaut-demo-scenarios/tree/feature/v1.4-new-scenarios/golden-transcripts) — validated RCA examples with causal chains and due diligence assessments

---

Would you like me to:
1. Execute the primary recommended fix
2. Run a specialized debug skill for deeper analysis
3. Investigate a related resource
4. Export findings as a structured report
5. Exit triage

Select an option:
```

**WAIT for user confirmation before proceeding.**

## Dependencies

### Required MCP Servers
- `openshift` - Kubernetes/OpenShift resource access for Deployments, Pods, Events, Services, and cluster resources
- `observability` - Prometheus metric discovery, metadata, series, and PromQL query execution for trend analysis and saturation detection

### Related Skills
- `/debug-pod` - Single-pod failure diagnosis (CrashLoopBackOff, OOMKilled, ImagePullBackOff)
- `/debug-scc` - SCC admission violation diagnosis
- `/debug-rbac` - RBAC permission failure diagnosis
- `/debug-network` - Service/Route connectivity diagnosis
- `/debug-build` - Build failure diagnosis
- `/deploy` - Redeployment after fixes

### Reference Documentation
- [docs/debugging-patterns.md](../../docs/debugging-patterns.md) - Common error patterns and troubleshooting trees
- [docs/prerequisites.md](../../docs/prerequisites.md) - Required tools (oc), cluster access verification

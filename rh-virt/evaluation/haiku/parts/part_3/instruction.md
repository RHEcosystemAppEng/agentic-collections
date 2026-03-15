# OpenShift Virtualization: VM Provisioning

## Objective

You are a Cloud Architect managing an OpenShift Virtualization (KubeVirt) fleet. Complete the task below, writing all deliverables to `/root`.

Work fully autonomously — make all technical decisions yourself. When a step would normally require user confirmation, choose the safest option and document what a human operator would have been asked to confirm or decide.

**CRITICAL — READ THIS BEFORE DOING ANYTHING ELSE:**
BEFORE STARTING, YOU MUST CHECK WHETHER SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT. IF THEY EXIST, YOU MUST READ EVERY SKILL FILE AND EVERY DOCUMENT THEY REFERENCE — COMPLETELY, NOT PARTIALLY. These skills contain environment-specific procedures, naming conventions, safety protocols, troubleshooting references, and tool parameters that OVERRIDE general KubeVirt knowledge. DO NOT SKIP THIS STEP. DO NOT RELY ON GENERAL KNOWLEDGE IF A SKILL COVERS THE TOPIC.

---

## Provision a Benchmarking VM

Provision `perf-bench-01` in `virt-staging`:
- CPU-bound workload (concurrent query load) — choose a matching resource profile
- Fedora OS, medium-range size, auto-start disabled

**Deliverables:**

- **`vm_provisioning_report.md`** — Document:
  1. How you determined the namespace context (note: the MCP server may not have a namespace detection tool — describe your workaround)
  2. Resource profile and sizing selected — explain why this profile matches compute-bound work
  3. Exact parameters passed to the creation tool
  4. A scheduling contingency plan: step-by-step what you would do if the VM entered an unschedulable error state, including:
     - Diagnostics to run
     - Documentation to consult (name specific documents)
     - Remediation steps (note: how do spec changes propagate to running instances? Is a restart needed?)
- **`perf_bench_vm_create.json`** — The `vm_create` tool invocation parameters as JSON (just the arguments, not a full VM spec).

---

## Evaluation

| Criterion | Evaluated on |
|-----------|-------------|
| Provision | Profile matches workload type, sizing rationale, namespace awareness, concrete scheduling contingency with documentation and spec-propagation understanding |

**FINAL REMINDER: IF SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT, YOU MUST READ AND FOLLOW THEM.** They contain environment-specific procedures, naming conventions, safety protocols, and troubleshooting references that are REQUIRED for correct execution. DO NOT WRITE ANY REPORT BASED ON GENERAL KNOWLEDGE ALONE IF A SKILL EXISTS FOR THAT TOPIC. GO READ THE SKILLS NOW IF YOU HAVE NOT ALREADY.

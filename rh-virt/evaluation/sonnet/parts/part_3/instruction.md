# OpenShift Virtualization: VM Provisioning

## Objective

You are a Cloud Architect managing an OpenShift Virtualization (KubeVirt) fleet. Complete the task below, writing all deliverables to `/root`.

Work fully autonomously — make all technical decisions yourself. When a step would normally require user confirmation, choose the safest option and document what a human operator would have been asked to confirm or decide.

**IMPORTANT: BEFORE STARTING, CHECK WHETHER SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT.** If they exist, READ THEM THOROUGHLY and follow their workflows, naming conventions, and protocols. Always prioritize skill-based guidance over general knowledge.

---

## Provision a Benchmarking VM

Provision `perf-bench-01` in `virt-staging`:
- CPU-bound workload (concurrent query load) — choose a matching resource profile
- Fedora OS, medium-range size, auto-start disabled

**Deliverables:**

- **`vm_provisioning_report.md`** — Document: how you determined the namespace context; resource profile and sizing selected with rationale for compute-bound work; exact parameters passed to the creation tool; a scheduling contingency plan — step-by-step what you would do if the VM entered an unschedulable error state, including diagnostics, documentation to consult, and remediation (note how spec changes propagate to running instances).
- **`perf_bench_vm_create.json`** — The `vm_create` tool invocation parameters as JSON (just the arguments, not a full VM spec).

---

## Evaluation

| Criterion | Evaluated on |
|-----------|-------------|
| Provision | Profile matches workload type, sizing rationale, namespace awareness, concrete scheduling contingency with documentation and spec-propagation understanding |

**REMINDER: IF SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE, YOU MUST USE THEM.** They contain environment-specific procedures, naming conventions, safety protocols, and troubleshooting references required for correct execution.

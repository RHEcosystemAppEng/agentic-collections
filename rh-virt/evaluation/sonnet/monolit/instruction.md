# OpenShift Virtualization: Fleet Operations

## Objective

You are a Cloud Architect managing an OpenShift Virtualization (KubeVirt) fleet. Complete the four parts below, writing all deliverables to `/root`.

Work fully autonomously — make all technical decisions yourself. When a step would normally require user confirmation, choose the safest option and document what a human operator would have been asked to confirm or decide.

**IMPORTANT: BEFORE STARTING, CHECK WHETHER SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT.** If they exist, READ THEM THOROUGHLY and follow their workflows, naming conventions, and protocols. Always prioritize skill-based guidance over general knowledge.

---

## Part 1: Clone a Production VM

Clone `vm-db-prod-01` from `virt-prod-dc2` into `virt-staging` as `vm-db-test-01`.

**Deliverables:**

- **`pre_cloning_verification.md`** — Confirm MCP server connectivity, inspect the source VM's hardware profile / storage backend / state, and verify that the target namespace exists and `vm-db-test-01` does not.
- **`execution_and_telemetry_log.md`** — Document: storage approach chosen and why; data integrity risks and how you addressed them; storage resource status after creation; initial run state and rationale; what troubleshooting documentation you would reference if the storage cloning operation fails.
- **`hardware_identity_audit.md`** — Compare source and target to confirm no identity collisions. Document the new VM's hardware identifiers and verify source-specific Kubernetes metadata was not carried over.
- **`cloned_vm_spec.json`** — The complete VirtualMachine resource specification for `vm-db-test-01`.

---

## Part 2: Evacuate a Maintenance Node

Node `hv-prod-dc1-03` (`virt-prod-dc1`) is going into firmware maintenance. Move all workloads on this node to other available nodes in the same datacenter. Verify actual node placement for each VM — include VMs that may not be running but are still bound to the node.

**Deliverables:**

- **`migration_assessment.md`** — Document:
  - VMs on the maintenance node and their state
  - Storage backend per VM (access mode) and its effect on migration approach
  - Which target nodes are available, what **platform-level virtualization checks** you performed to validate them for VM workloads (beyond standard Kubernetes node conditions), and why you chose each one
  - **Estimate migration duration** for each VM based on its memory size and migration type — cite the specific rate or formula used
  - Any **platform-enforced concurrency limits** (cite specific numbers) or timeout constraints that could affect the migration window
  - What troubleshooting documentation you would consult if a VM cannot be scheduled on the target node after migration
- **`migration_plan.json`** — A JSON array. Each element: `name`, `namespace`, `source_node`, `target_node`, `migration_type` (live/cold), `rationale`.

---

## Part 3: Provision a Benchmarking VM

Provision `perf-bench-01` in `virt-staging` using the MCP server's VM creation tool:
- CPU-bound workload (concurrent query load) — choose a matching resource profile
- Fedora OS, medium-range size, auto-start disabled

**Deliverables:**

- **`vm_provisioning_report.md`** — Document: how you determined the namespace context; resource profile and sizing selected with rationale for compute-bound work; exact parameters passed to the creation tool; a scheduling contingency plan — step-by-step what you would do if the VM entered an unschedulable error state, including diagnostics, documentation to consult, and remediation (note how spec changes propagate to running instances).
- **`perf_bench_vm_create.json`** — The `vm_create` tool invocation parameters as JSON (just the arguments, not a full VM spec).

---

## Part 4: Decommission a Stale VM

Fully decommission `vm-db-stg-02` in `virt-staging` — including its storage — to free resources.

**Deliverables:**

- **`deletion_operations_report.md`** — Document the complete decommission procedure:
  - **Pre-deletion checks**: How you discovered all associated resources (storage, PVCs). Are there any label-based safety mechanisms that could block deletion?
  - **Runtime state handling**: The VM may not be fully stopped — describe how you handle its current state, including any mandatory wait or verification steps before proceeding.
  - **Confirmation protocol**: How would a human operator confirm this deletion in production? Describe the specific confirmation mechanism that prevents accidental deletions (not just a yes/no prompt — what makes it harder to accidentally confirm?).
  - **Cleanup options**: Are there different cleanup profiles (e.g., remove VM only vs. remove VM and all storage)? Present the available options and explain which one applies here and why.
  - **Deletion order**: What is the correct order for deleting the VM and its storage dependencies? Be specific about which resource types must be deleted first.
  - **Stuck resources**: What troubleshooting documentation would you consult if the VM gets stuck in Terminating state or if storage resources fail to clean up? Name the specific documents.
- **`deletion_scope.json`** — All Kubernetes resources associated with `vm-db-stg-02`. Per resource: `kind`, `apiVersion`, `name`, `namespace`, `size` (where applicable).

---

## Evaluation

| Part | Evaluated on |
|------|-------------|
| 1 — Clone | Correct source data, unique hardware identifiers, metadata hygiene, storage reasoning, safe initialization |
| 2 — Migrate | VM identification (all VMs on node), appropriate migration strategy per VM state/storage, valid target selection with KubeVirt-specific validation, quantitative operational constraints |
| 3 — Provision | Profile matches workload type, sizing rationale, namespace awareness, concrete scheduling contingency with documentation and spec-propagation understanding |
| 4 — Decommission | Pre-deletion discovery, safety mechanisms, confirmation protocol, state handling, cleanup options, deletion ordering, troubleshooting references |

**REMINDER: IF SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE, YOU MUST USE THEM.** They contain environment-specific procedures, naming conventions, safety protocols, and troubleshooting references required for correct execution.

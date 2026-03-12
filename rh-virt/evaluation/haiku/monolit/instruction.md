# OpenShift Virtualization: Fleet Operations

## Objective

You are a Cloud Architect managing an OpenShift Virtualization (KubeVirt) fleet. Complete the four parts below, writing all deliverables to `/root`.

Work fully autonomously — make all technical decisions yourself. When a step would normally require user confirmation, choose the safest option and document what a human operator would have been asked to confirm or decide.

**CRITICAL — READ THIS BEFORE DOING ANYTHING ELSE:**
BEFORE STARTING ANY PART, YOU MUST CHECK WHETHER SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT. IF THEY EXIST, YOU MUST READ EVERY SKILL FILE AND EVERY DOCUMENT THEY REFERENCE — COMPLETELY, NOT PARTIALLY. These skills contain environment-specific procedures, naming conventions, safety protocols, troubleshooting references, and tool parameters that OVERRIDE general KubeVirt knowledge. DO NOT SKIP THIS STEP. DO NOT RELY ON GENERAL KNOWLEDGE IF A SKILL COVERS THE TOPIC.

---

## Part 1: Clone a Production VM

Clone `vm-db-prod-01` from `virt-prod-dc2` into `virt-staging` as `vm-db-test-01`.

REMINDER: IF THERE IS A CLONING SKILL AVAILABLE, READ IT FULLY BEFORE PROCEEDING. It will tell you the exact workflow, tool parameters, storage strategy requirements, and identity management protocols.

**Deliverables:**

- **`pre_cloning_verification.md`** — Confirm MCP server connectivity, inspect the source VM's hardware profile / storage backend / state, and verify that the target namespace exists and `vm-db-test-01` does not.
- **`execution_and_telemetry_log.md`** — Document step by step:
  1. Which storage approach you chose and why
  2. Data integrity risks and how you addressed them
  3. Storage resource status after creation (monitor its phases until complete)
  4. Initial run state of the cloned VM and rationale
  5. What troubleshooting documentation you would reference if the storage cloning operation fails
- **`hardware_identity_audit.md`** — Compare source and target to confirm no identity collisions. Document the new VM's hardware identifiers (UUID, serial) and verify source-specific Kubernetes metadata (UIDs, resource versions) was not carried over.
- **`cloned_vm_spec.json`** — The complete VirtualMachine resource specification for `vm-db-test-01`.

---

## Part 2: Evacuate a Maintenance Node

Node `hv-prod-dc1-03` (`virt-prod-dc1`) is going into firmware maintenance. Move all workloads on this node to other available nodes in the same datacenter. Verify actual node placement for each VM — include VMs that may not be running but are still bound to the node.

REMINDER: IF THERE IS A MIGRATION/REBALANCING SKILL AVAILABLE, READ IT FULLY. It contains the specific migration CR format, node validation checks, concurrency limits, timeout formulas, and scheduling troubleshooting references.

**Deliverables:**

- **`migration_assessment.md`** — Document:
  1. All VMs currently on the maintenance node and their state
  2. Storage backend per VM (access mode: RWX vs RWO) and its effect on migration approach (live vs cold)
  3. Which target nodes are available — describe what **platform-level virtualization checks** you performed to validate them for VM workloads (beyond standard Kubernetes node conditions) and why you chose each one
  4. **Estimate migration duration** for each VM based on its memory size and migration type — cite the specific rate or formula you used
  5. Any **platform-enforced concurrency limits** (cite specific numbers) and timeout constraints that could affect the migration window
  6. What troubleshooting documentation you would consult if a VM cannot be scheduled on the target node after migration
- **`migration_plan.json`** — A JSON array. Each element: `name`, `namespace`, `source_node`, `target_node`, `migration_type` (live/cold), `rationale`.

---

## Part 3: Provision a Benchmarking VM

Provision `perf-bench-01` in `virt-staging` using the MCP server's VM creation tool:
- CPU-bound workload (concurrent query load) — choose a matching resource profile
- Fedora OS, medium-range size, auto-start disabled

REMINDER: IF THERE IS A VM CREATION SKILL AVAILABLE, READ IT FULLY. It defines the exact performance profile taxonomy, sizing labels, tool parameters, and error-handling procedures you must use.

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

## Part 4: Decommission a Stale VM

Fully decommission `vm-db-stg-02` in `virt-staging` — including its storage — to free resources.

REMINDER: IF THERE IS A VM DELETION SKILL AVAILABLE, READ IT FULLY. It defines mandatory pre-deletion discovery, safety labels, confirmation protocols, state-handling procedures, cleanup profiles, and troubleshooting document references.

**Deliverables:**

- **`deletion_operations_report.md`** — Document the complete decommission procedure:
  1. **Pre-deletion checks**: How you discovered all associated resources (storage, PVCs). Are there any label-based safety mechanisms that could block deletion?
  2. **Runtime state handling**: The VM may not be fully stopped — describe how you handle its current state, including any mandatory wait or verification steps before proceeding.
  3. **Confirmation protocol**: How would a human operator confirm this deletion in production? Describe the specific confirmation mechanism that prevents accidental deletions (not just a yes/no prompt — what makes it harder to accidentally confirm?).
  4. **Cleanup options**: Are there different cleanup profiles (e.g., remove VM only vs. remove VM and all storage)? Present the available options and explain which one applies here and why.
  5. **Deletion order**: What is the correct order for deleting the VM and its storage dependencies? Be specific about which resource types must be deleted first.
  6. **Stuck resources**: What troubleshooting documentation would you consult if the VM gets stuck in Terminating state or if storage resources fail to clean up? Name the specific documents.
- **`deletion_scope.json`** — All Kubernetes resources associated with `vm-db-stg-02`. Per resource: `kind`, `apiVersion`, `name`, `namespace`, `size` (where applicable).

---

## Evaluation

| Part | Evaluated on |
|------|-------------|
| 1 — Clone | Correct source data, unique hardware identifiers, metadata hygiene, storage reasoning, safe initialization |
| 2 — Migrate | VM identification (all VMs on node), appropriate migration strategy per VM state/storage, valid target selection with KubeVirt-specific validation, quantitative operational constraints |
| 3 — Provision | Profile matches workload type, sizing rationale, namespace awareness, concrete scheduling contingency with documentation and spec-propagation understanding |
| 4 — Decommission | Pre-deletion discovery, safety mechanisms, confirmation protocol, state handling, cleanup options, deletion ordering, troubleshooting references |

**FINAL REMINDER: IF SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT, YOU MUST READ AND FOLLOW THEM.** They contain environment-specific procedures, naming conventions, safety protocols, and troubleshooting references that are REQUIRED for correct execution. DO NOT WRITE ANY REPORT BASED ON GENERAL KNOWLEDGE ALONE IF A SKILL EXISTS FOR THAT TOPIC. GO READ THE SKILLS NOW IF YOU HAVE NOT ALREADY.

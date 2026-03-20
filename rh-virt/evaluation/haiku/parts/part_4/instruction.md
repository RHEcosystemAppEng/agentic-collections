# OpenShift Virtualization: VM Decommissioning

## Objective

You are a Cloud Architect managing an OpenShift Virtualization (KubeVirt) fleet. Complete the task below, writing all deliverables to `/root`.

Work fully autonomously — make all technical decisions yourself. When a step would normally require user confirmation, choose the safest option and document what a human operator would have been asked to confirm or decide.

**CRITICAL — READ THIS BEFORE DOING ANYTHING ELSE:**
BEFORE STARTING, YOU MUST CHECK WHETHER SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT. IF THEY EXIST, YOU MUST READ EVERY SKILL FILE AND EVERY DOCUMENT THEY REFERENCE — COMPLETELY, NOT PARTIALLY. These skills contain environment-specific procedures, naming conventions, safety protocols, troubleshooting references, and tool parameters that OVERRIDE general KubeVirt knowledge. DO NOT SKIP THIS STEP. DO NOT RELY ON GENERAL KNOWLEDGE IF A SKILL COVERS THE TOPIC.

---

## Decommission a Stale VM

Fully decommission `vm-db-stg-02` in `virt-staging` — including its storage — to free resources.

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

| Criterion | Evaluated on |
|-----------|-------------|
| Decommission | Pre-deletion discovery, safety mechanisms, confirmation protocol, state handling, cleanup options, deletion ordering, troubleshooting references |

**FINAL REMINDER: IF SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT, YOU MUST READ AND FOLLOW THEM.** They contain environment-specific procedures, naming conventions, safety protocols, and troubleshooting references that are REQUIRED for correct execution. DO NOT WRITE ANY REPORT BASED ON GENERAL KNOWLEDGE ALONE IF A SKILL EXISTS FOR THAT TOPIC. GO READ THE SKILLS NOW IF YOU HAVE NOT ALREADY.

# OpenShift Virtualization: Node Evacuation

## Objective

You are a Cloud Architect managing an OpenShift Virtualization (KubeVirt) fleet. Complete the task below, writing all deliverables to `/root`.

Work fully autonomously — make all technical decisions yourself. When a step would normally require user confirmation, choose the safest option and document what a human operator would have been asked to confirm or decide.

**CRITICAL — READ THIS BEFORE DOING ANYTHING ELSE:**
BEFORE STARTING, YOU MUST CHECK WHETHER SKILLS OR REFERENCE DOCUMENTATION ARE AVAILABLE IN THIS ENVIRONMENT. IF THEY EXIST, READ THEM COMPLETELY — NOT PARTIALLY. SKILLS AND DOCUMENTATION CONTAIN ENVIRONMENT-SPECIFIC PROCEDURES, NAMING CONVENTIONS, SAFETY PROTOCOLS, TROUBLESHOOTING REFERENCES, AND MCP TOOL PARAMETERS THAT YOU MUST FOLLOW. PRIORITIZE SKILLS AND DOCUMENTATION OVER GENERAL KNOWLEDGE FOR ANY TOPIC THEY COVER. DO NOT SKIP THIS STEP.

**HOW TO USE SKILLS:**
- CHECK if skills are available for VM migration, rebalancing, or node evacuation operations
- IF A SKILL EXISTS FOR YOUR TASK, READ IT COMPLETELY BEFORE PROCEEDING
- THE SKILL WILL TELL YOU EXACTLY WHICH MCP TOOLS TO USE (`resources_list`, `pods_list`, etc.) AND HOW TO CALL THEM
- FOLLOW THE SKILL'S WORKFLOW EXACTLY — IT CONTAINS THE CORRECT TOOL PARAMETERS, LABEL SELECTORS, AND FILTERING METHODS
- SKILLS OVERRIDE GENERAL KUBEVIRT KNOWLEDGE

---

## Evacuate a Maintenance Node

Node `hv-prod-dc1-03` (`virt-prod-dc1`) is going into firmware maintenance. Move all workloads on this node to other available nodes in the same datacenter. Verify actual node placement for each VM — include VMs that may not be running but are still bound to the node.

**Deliverables:**

- **`migration_assessment.md`** — Document:
  1. All VMs currently on the maintenance node and their state (USE MCP TOOLS like `pods_list` to find virt-launcher pods on `hv-prod-dc1-03` and extract VM names from pod labels)
  2. Storage backend per VM (access mode: RWX vs RWO) and its effect on migration approach (live vs cold)
  3. Which target nodes are available — describe what **platform-level virtualization checks** you performed using MCP tools to validate them for VM workloads (check node labels, taints, available resources) and why you chose each one
  4. **Estimate migration duration** for each VM based on its memory size and migration type — cite the specific rate or formula you used (check if skills provide migration rate formulas)
  5. Any **platform-enforced concurrency limits** (cite specific numbers from skill documentation if available) and timeout constraints that could affect the migration window
  6. What troubleshooting documentation you would consult if a VM cannot be scheduled on the target node after migration
- **`migration_plan.json`** — A JSON array. Each element: `name`, `namespace`, `source_node` (must be `hv-prod-dc1-03`), `target_node`, `migration_type` (live/cold), `rationale`. ONLY INCLUDE VMS ACTUALLY ON THE MAINTENANCE NODE `hv-prod-dc1-03` (verify using MCP tools to check actual pod placement).

---

## Evaluation

| Criterion | Evaluated on |
|-----------|-------------|
| Migrate | VM identification (all VMs on node), appropriate migration strategy per VM state/storage, valid target selection with KubeVirt-specific validation, quantitative operational constraints |

**FINAL REMINDER: SKILLS AND REFERENCE DOCUMENTATION TAKE PRIORITY OVER GENERAL KNOWLEDGE.** IF SKILLS ARE AVAILABLE FOR VM MIGRATION/REBALANCING, YOU MUST READ AND FOLLOW THEM COMPLETELY. THEY CONTAIN ENVIRONMENT-SPECIFIC PROCEDURES, MCP TOOL USAGE PATTERNS FOR IDENTIFYING VMS ON NODES, NAMING CONVENTIONS, SAFETY PROTOCOLS, AND TROUBLESHOOTING REFERENCES THAT ARE REQUIRED FOR CORRECT EXECUTION. DO NOT RELY ON GENERAL KUBEVIRT KNOWLEDGE IF SKILLS COVER THE TOPIC.

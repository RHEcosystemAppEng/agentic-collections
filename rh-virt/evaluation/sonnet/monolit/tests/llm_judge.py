"""
LLM-as-judge evaluator for skill-dependent criteria (15 criteria).

Only criteria that empirically discriminate between skilled and unskilled
agents are included. Non-discriminating criteria (both variants pass
equally) have been removed to sharpen the signal.

Requires ANTHROPIC_API_KEY and LLM_JUDGE_MODEL environment variables.
"""

import json
import os
import sys
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: anthropic package not installed")
    sys.exit(1)


CRITERIA = [
    # ── Part 1: vm-clone ────────────────────────────────────────────────
    {
        "id": "clone_storage_doc_reference",
        "file": "/root/execution_and_telemetry_log.md",
        "question": (
            "Does this report reference a specific troubleshooting document "
            "by name (such as 'storage-errors.md' or 'storage-errors') as "
            "a resource for diagnosing DataVolume cloning failures, storage "
            "provisioning issues, or PVC clone errors? A generic statement "
            "like 'check storage logs' or 'consult documentation' without "
            "naming the specific file does NOT count."
        ),
        "reference": (
            "The vm-clone skill specifies: consult storage-errors.md for "
            "VM cloning failure scenarios, storage provisioning issues, and "
            "DataVolume cloning errors. The document path is "
            "docs/troubleshooting/storage-errors.md. The agent should "
            "reference this document as part of its risk assessment or "
            "contingency planning for the cloning operation."
        ),
    },
    {
        "id": "cdi_phase_monitoring",
        "file": "/root/execution_and_telemetry_log.md",
        "question": (
            "Does this report document monitoring the DataVolume's CDI phases "
            "during the storage cloning operation — specifically mentioning "
            "phase names like 'CloneInProgress', 'SnapshotForSmartCloneInProgress', "
            "or 'Succeeded'? Generic statements like 'waited for storage' or "
            "'storage completed' without naming specific CDI phase values do "
            "NOT count."
        ),
        "reference": (
            "The vm-clone skill mandates polling DataVolume status via "
            "resources_get and monitoring .status.phase through CDI phases: "
            "CloneInProgress → Succeeded (or SnapshotForSmartCloneInProgress "
            "for smart-clone). The agent should report these specific phase "
            "transitions as telemetry, not just state that storage is ready."
        ),
    },
    # ── Part 2: vm-rebalance (migration) ─────────────────────────────────
    {
        "id": "node_schedulability_check",
        "file": "/root/migration_assessment.md",
        "question": (
            "Does this report mention checking the 'kubevirt.io/schedulable' "
            "label or KVM device availability (devices.kubevirt.io/kvm) on "
            "target nodes as criteria for selecting valid migration targets? "
            "Simply mentioning 'node capacity', 'node readiness', or generic "
            "Kubernetes node conditions does NOT count — the report must "
            "reference KubeVirt-specific schedulability markers."
        ),
        "reference": (
            "The vm-rebalance skill requires checking target nodes for: "
            "(1) metadata.labels['kubevirt.io/schedulable'] == 'true' "
            "(the official KubeVirt marker for VM-capable nodes), and "
            "(2) status.capacity['devices.kubevirt.io/kvm'] > '0' "
            "(confirming KVM device availability). Standard Kubernetes "
            "node conditions (Ready, SchedulingDisabled) are necessary "
            "but NOT sufficient — these KubeVirt-specific checks are "
            "what distinguish a skilled agent."
        ),
    },
    {
        "id": "migration_timeout_estimation",
        "file": "/root/migration_assessment.md",
        "question": (
            "Does this report mention a specific timeout formula or estimate "
            "for live migration duration (such as '150 seconds per GiB' or a "
            "per-GiB calculation)? Generic statements like 'migration may "
            "take time' or 'depends on memory size' without citing a specific "
            "rate or formula do NOT count."
        ),
        "reference": (
            "The vm-rebalance skill documents that live migration has a "
            "timeout of '150 seconds per GiB' of VM memory. If a migration "
            "exceeds this timeout, it fails and the agent should retry, "
            "reduce VM workload, use cold migration, or increase the timeout "
            "in the HyperConverged CR. This specific rate (150s/GiB) is "
            "operational knowledge from the skill, not general KubeVirt docs."
        ),
    },
    {
        "id": "migration_concurrency_limits",
        "file": "/root/migration_assessment.md",
        "question": (
            "Does this report mention specific concurrent migration limits "
            "(such as a maximum of 5 cluster-wide or 2 per node)? Generic "
            "statements like 'avoid too many simultaneous migrations' or "
            "'migrate sequentially' without citing specific numbers do NOT "
            "count."
        ),
        "reference": (
            "The vm-rebalance skill documents that KubeVirt enforces "
            "concurrent migration limits: default 5 cluster-wide and 2 per "
            "node. If these limits are reached, migrations are rejected and "
            "must be retried. These specific numbers come from the "
            "HyperConverged CR defaults and are operational knowledge the "
            "skill provides."
        ),
    },
    {
        "id": "rwx_rwo_migration_logic",
        "file": "/root/migration_assessment.md",
        "question": (
            "Does this report explain that the PVC access mode (ReadWriteMany / "
            "RWX vs ReadWriteOnce / RWO) determines whether a VM can be live "
            "migrated or must use cold migration? The report must connect "
            "storage access mode to migration type — simply listing migration "
            "types without explaining WHY one is chosen over the other based "
            "on storage does NOT count."
        ),
        "reference": (
            "The vm-rebalance skill explicitly states: RWX storage → live "
            "migration supported (zero downtime, <1s pause). RWO storage → "
            "live migration NOT supported, must use cold migration (brief "
            "downtime ~30-60s). This per-VM check via PVC spec.accessModes "
            "is the primary decision factor for migration strategy selection."
        ),
    },
    {
        "id": "scheduling_doc_reference_migration",
        "file": "/root/migration_assessment.md",
        "question": (
            "Does this report reference a specific troubleshooting document "
            "by name (such as 'scheduling-errors.md' or 'scheduling-errors') "
            "that should be consulted if a VM cannot be scheduled on the "
            "target node after migration? A generic statement like 'check "
            "node status' or 'consult documentation' without naming the "
            "specific file does NOT count."
        ),
        "reference": (
            "The vm-rebalance skill references "
            "docs/troubleshooting/scheduling-errors.md for node placement "
            "issues (Error 2: VM Stuck in ErrorUnschedulable After Cold "
            "Migration). The agent should cite this document as a "
            "contingency for scheduling failures during evacuation."
        ),
    },
    # ── Part 3: vm-create (provisioning) ─────────────────────────────────
    {
        "id": "compute_optimized_profile",
        "file": "/root/perf_bench_vm_create.json",
        "question": (
            "Does this JSON contain a performance or instancetype field that "
            "uses the SPECIFIC profile code 'c1' (the compute-optimized "
            "profile from OpenShift Virtualization's sizing taxonomy)? "
            "Look for exact values like 'c1', 'c1.medium', 'c1.large', or "
            "'c1.xlarge'. Generic descriptive labels like 'compute-optimized', "
            "'high-performance', 'cpu-optimized', or manual CPU/memory counts "
            "do NOT count — only the coded identifier 'c1' qualifies."
        ),
        "reference": (
            "The vm-create skill defines a performance profile taxonomy: "
            "u1 = General Purpose, c1 = Compute Optimized, m1 = Memory "
            "Optimized, o1 = Overcommitted. For a CPU-bound benchmarking "
            "workload, the correct profile is 'c1'. The vm_create tool "
            "accepts a 'performance' parameter with these coded values. "
            "Combined with size (small/medium/large/xlarge), this forms "
            "instancetypes like 'c1.large'."
        ),
    },
    {
        "id": "scheduling_doc_reference",
        "file": "/root/vm_provisioning_report.md",
        "question": (
            "Does the scheduling contingency plan reference a specific "
            "troubleshooting document by name (such as 'scheduling-errors.md' "
            "or 'scheduling-errors') that should be consulted when a VM enters "
            "an unschedulable error state? A generic statement like 'consult "
            "documentation' without naming the specific file does NOT count."
        ),
        "reference": (
            "The vm-create skill mandates: 'If VM reaches ErrorUnschedulable "
            "state, FIRST read scheduling-errors.md before executing any "
            "diagnostic commands.' The document path is "
            "docs/troubleshooting/scheduling-errors.md. This is a strict "
            "document-first diagnostic protocol — the agent must consult "
            "the document by name before taking action."
        ),
    },
    {
        "id": "restart_to_patch",
        "file": "/root/vm_provisioning_report.md",
        "question": (
            "Does the scheduling contingency plan mention that after patching "
            "a VirtualMachine spec (e.g., adding tolerations), an explicit "
            "restart via vm_lifecycle is required for the changes to take "
            "effect on the running VirtualMachineInstance? Simply stating "
            "'patch the VM' or 'add tolerations' without mentioning the "
            "restart requirement does NOT count."
        ),
        "reference": (
            "The vm-create skill documents that applying a toleration patch "
            "to a VirtualMachine resource requires an explicit vm_lifecycle "
            "restart action to force creation of a new VirtualMachineInstance "
            "with the updated spec. The VM resource is a template; changes "
            "do not automatically propagate to the running VMI. Without "
            "restart, the old VMI continues with the original spec."
        ),
    },
    # ── Part 4: vm-delete (decommissioning) ──────────────────────────────
    {
        "id": "protection_label_safeguard",
        "file": "/root/deletion_operations_report.md",
        "question": (
            "Does this report describe checking for a 'protected' label "
            "(such as 'protected: true' in metadata.labels) as a safety "
            "mechanism that blocks deletion? This is a custom convention, "
            "not a standard Kubernetes feature. The report must show "
            "awareness of this specific label-based soft-lock mechanism."
        ),
        "reference": (
            "The vm-delete skill enforces: 'If VM contains the label "
            "protected: \"true\", REFUSE the operation entirely and STOP.' "
            "The agent cannot remove this label itself — it must instruct "
            "the user to run 'oc label vm/<name> protected-' to unlock "
            "before retrying. This is a custom soft-lock, not a standard "
            "Kubernetes feature like finalizers."
        ),
    },
    {
        "id": "typed_name_confirmation",
        "file": "/root/deletion_operations_report.md",
        "question": (
            "Does this report describe a typed confirmation protocol where "
            "the user must type the exact VM name (case-sensitive) to "
            "confirm deletion, rather than a simple yes/no prompt? The key "
            "detail is that mismatches or typos cause automatic cancellation."
        ),
        "reference": (
            "The vm-delete skill enforces a high-friction confirmation: the "
            "user must type the exact, case-sensitive VM name. Any mismatch "
            "(including typos, 'yes', 'delete it', etc.) causes immediate "
            "automatic cancellation of the entire operation. This is "
            "deliberately harder than a yes/no prompt to prevent accidental "
            "enter-key deletions."
        ),
    },
    {
        "id": "paused_state_stop_wait",
        "file": "/root/deletion_operations_report.md",
        "question": (
            "Does this report address that the VM is in a Paused state and "
            "describe a stop-then-wait procedure before deletion? The "
            "procedure should include: (1) stopping the paused VM, (2) "
            "waiting or verifying that it has fully stopped, and (3) then "
            "proceeding with deletion. Simply mentioning 'stop the VM' "
            "without a wait/verify step is insufficient."
        ),
        "reference": (
            "The vm-delete skill mandates: if VM is Running, Starting, "
            "Paused, or Migrating, offer a 'stop-and-delete' option. After "
            "initiating stop via vm_lifecycle, wait exactly 10 seconds, then "
            "re-verify the VM is fully stopped before proceeding with "
            "deletion. The forced wait period is a safety measure to avoid "
            "deleting a VM that hasn't cleanly stopped."
        ),
    },
    {
        "id": "deletion_profile_options",
        "file": "/root/deletion_operations_report.md",
        "question": (
            "Does this report present two distinct deletion/cleanup options: "
            "one that removes only the VM while preserving storage (for "
            "potential reuse or reattachment), and another that performs a "
            "complete cleanup including storage deletion (to free quota)? "
            "Both options must be described as distinct choices."
        ),
        "reference": (
            "The vm-delete skill defines two deletion profiles the user "
            "must choose between: Option 1 (VM Only) deletes the "
            "VirtualMachine but preserves DataVolumes and PVCs for reuse. "
            "Option 2 (Complete Cleanup) deletes the VM AND associated "
            "storage, which is the only way to free cluster storage quota. "
            "These must be presented as explicit user choices."
        ),
    },
    {
        "id": "troubleshooting_doc_reference_deletion",
        "file": "/root/deletion_operations_report.md",
        "question": (
            "Does this report reference specific troubleshooting documents "
            "by name (such as 'lifecycle-errors.md' or 'storage-errors.md') "
            "that should be consulted if the VM gets stuck in a Terminating "
            "state or if storage resources fail to clean up? A generic "
            "statement like 'check logs' or 'consult documentation' without "
            "naming specific files does NOT count."
        ),
        "reference": (
            "The vm-delete skill identifies two specific diagnostic documents: "
            "(1) lifecycle-errors.md — consult if VM is stuck in Terminating "
            "state or has blocking finalizers; (2) storage-errors.md — "
            "consult if PVCs remain 'In Use' or fail to delete after VM "
            "removal. These documents are at docs/troubleshooting/."
        ),
    },
]


SYSTEM_PROMPT = """\
You are an evaluator for a cloud operations benchmark. You will be given a \
file produced by an AI agent, a yes/no question about its contents, and a \
REFERENCE ANSWER that describes what a correct, skilled response looks like.

Rules:
- Answer ONLY with a JSON object: {"pass": true} or {"pass": false}
- Base your answer strictly on what is written in the file content
- Do not infer or assume knowledge the agent did not demonstrate
- Use the REFERENCE ANSWER to calibrate what counts as a pass — it shows \
the specific operational knowledge the agent should demonstrate
- Accept different phrasings that convey the SAME concept as the reference
- Do NOT use your own general knowledge to fill gaps — if the file does not \
demonstrate the specific insight described in the reference, it fails\
"""


def judge_criterion(client: Anthropic, model: str, criterion: dict) -> dict:
    filepath = criterion["file"]
    if not Path(filepath).exists():
        return {"id": criterion["id"], "pass": False, "reason": "file not found"}

    content = Path(filepath).read_text()
    if len(content) > 50_000:
        content = content[:50_000] + "\n... (truncated)"

    reference = criterion.get("reference", "")
    ref_block = f"\n\n## Reference Answer\n{reference}" if reference else ""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=64,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"## File: {filepath}\n\n"
                        f"```\n{content}\n```\n\n"
                        f"## Question\n{criterion['question']}"
                        f"{ref_block}"
                    ),
                }
            ],
        )
        text = response.content[0].text.strip()
        if "{" in text:
            text = text[text.index("{"):text.rindex("}") + 1]
        result = json.loads(text)
        return {"id": criterion["id"], "pass": bool(result.get("pass", False))}
    except Exception as e:
        print(f"  WARNING: Judge error for {criterion['id']}: {e}")
        return {"id": criterion["id"], "pass": False, "reason": str(e)}


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    model = os.getenv("LLM_JUDGE_MODEL", "claude-haiku-4-5")

    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set, skipping LLM judge")
        json.dump(
            {"criteria": [], "passed": 0, "total": 0, "score": 0.0},
            open("/logs/verifier/llm_judge.json", "w"),
            indent=2,
        )
        return

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
        print(f"=== Using custom base URL: {base_url} ===")
    client = Anthropic(**client_kwargs)
    results = []

    print(f"=== LLM Judge: evaluating {len(CRITERIA)} criteria with {model} ===")
    for criterion in CRITERIA:
        print(f"  Evaluating: {criterion['id']} ...", end=" ", flush=True)
        result = judge_criterion(client, model, criterion)
        results.append(result)
        status = "PASS" if result["pass"] else "FAIL"
        print(status)

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    score = round(passed / total, 4) if total > 0 else 0.0

    print(f"=== LLM Judge: {passed}/{total} criteria passed (score={score}) ===")

    output = {
        "criteria": results,
        "passed": passed,
        "total": total,
        "score": score,
    }
    Path("/logs/verifier/llm_judge.json").write_text(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

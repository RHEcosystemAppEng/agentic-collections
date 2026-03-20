"""
LLM-as-judge evaluator for skill-dependent criteria (5 criteria).

Part 2 v2: Node Evacuation — migration assessment criteria.
Dropped vmim_cr_awareness (general knowledge) and resource_version_conflict (dead).
Added scheduling_doc_reference_migration.

Requires ANTHROPIC_API_KEY env var. LLM_JUDGE_MODEL is optional
(defaults to claude-sonnet-4-5 if unset).
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
    model = os.getenv("LLM_JUDGE_MODEL", "claude-sonnet-4-5")

    Path("/logs/verifier").mkdir(parents=True, exist_ok=True)

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

"""
LLM-as-judge evaluator for skill-dependent criteria (3 criteria).

Part 3: VM Provisioning — compute profile, scheduling contingency, spec propagation.

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

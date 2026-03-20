"""
LLM-as-judge evaluator for skill-dependent criteria (5 criteria).

Part 4 v2: VM Decommissioning — evaluates deletion_operations_report.md
against vm-delete skill knowledge.

Changes from v1:
- Dropped label_selector_discovery (non-discriminating, both pass)
- Dropped dv_before_pvc_deletion_order (non-discriminating, both pass)
- Kept and strengthened instruction nudges for: typed_name_confirmation,
  deletion_profile_options, paused_state_stop_wait

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
            "Does this report describe a typed confirmation protocol "
            "where the user must type the exact VM name (case-sensitive) to "
            "confirm deletion, rather than a simple yes/no prompt? This "
            "includes documenting what such a confirmation prompt would "
            "look like if a human operator were present. The key detail "
            "is that mismatches or typos cause automatic cancellation."
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
            "waiting a specific amount of time or verifying that it has "
            "fully stopped, and (3) then proceeding with deletion. Simply "
            "mentioning 'stop the VM' without a wait/verify step or without "
            "recognizing the Paused state is insufficient."
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
            "Both options must be described as distinct choices, not just "
            "mentioned in passing."
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

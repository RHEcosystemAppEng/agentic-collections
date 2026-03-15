"""
LLM-as-judge evaluator for skill-dependent criteria (2 criteria).

Part 1 (Clone) criteria only:
- clone_storage_doc_reference
- cdi_phase_monitoring

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

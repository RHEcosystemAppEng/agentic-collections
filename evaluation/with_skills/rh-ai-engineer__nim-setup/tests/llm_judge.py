import json
import os
import sys
import time
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: anthropic package not installed")
    sys.exit(1)

CRITERIA = [
  {
    "id": "opendatahub_api_group",
    "file": "/root/report.md",
    "question": "Does the report use nim.opendatahub.io as the API group for the NIM Account custom resource, rather than the upstream nim.nvidia.com?",
    "reference": "A skilled report specifies apiVersion: nim.opendatahub.io/v1 for the Account CR, which is the RHOAI-specific API group. An unskilled report uses nim.nvidia.com/v1alpha1 (the upstream NVIDIA API group) which is incorrect for Red Hat OpenShift AI."
  },
  {
    "id": "secret_naming_and_types",
    "file": "/root/report.md",
    "question": "Does the report create an image pull secret named ngc-image-pull-secret with type kubernetes.io/dockerconfigjson, and an API key secret with stringData containing the NGC_API_KEY field?",
    "reference": "A skilled report creates ngc-image-pull-secret (type: kubernetes.io/dockerconfigjson) for nvcr.io registry access, and ngc-api-key (type: Opaque, stringData: NGC_API_KEY) for runtime auth. An unskilled report uses generic names like nvcr-credentials, kubectl shorthands without explicit types, or data.api_key instead of stringData.NGC_API_KEY."
  },
  {
    "id": "operator_csv_verification",
    "file": "/root/report.md",
    "question": "Does the report verify gpu-operator-certified and NFD (Node Feature Discovery) Operator as prerequisites, checking their ClusterServiceVersion status?",
    "reference": "A skilled report checks for gpu-operator-certified (the specific CSV name, not just 'gpu-operator') and the NFD Operator in openshift-nfd namespace. An unskilled report either skips NFD entirely or uses generic gpu-operator references without the certified CSV name."
  }
]

SYSTEM_PROMPT = (
    "You are an evaluator for a cloud operations benchmark. You will be given a "
    "file produced by an AI agent, a yes/no question about its contents, and a "
    "REFERENCE ANSWER that describes what a correct, skilled response looks like.\n\n"
    "Rules:\n"
    "- Answer ONLY with a JSON object: {\"pass\": true} or {\"pass\": false}\n"
    "- Base your answer strictly on what is written in the file content\n"
    "- Do not infer or assume knowledge the agent did not demonstrate\n"
    "- Use the REFERENCE ANSWER to calibrate what counts as a pass\n"
    "- Accept different phrasings that convey the SAME concept\n"
    "- Do NOT use your own general knowledge to fill gaps"
)


def judge_criterion(client, model, criterion):
    filepath = criterion["file"]
    if not Path(filepath).exists():
        return {"id": criterion["id"], "pass": False, "reason": "file not found"}
    content = Path(filepath).read_text()
    if len(content) > 50000:
        content = content[:50000] + "\n... (truncated)"
    reference = criterion.get("reference", "")
    ref_block = f"\n\n## Reference Answer\n{reference}" if reference else ""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model, max_tokens=64, system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": (
                    f"## File: {filepath}\n\n```\n{content}\n```\n\n"
                    f"## Question\n{criterion['question']}{ref_block}"
                )}],
            )
            text = response.content[0].text.strip()
            if "{" in text:
                text = text[text.index("{"):text.rindex("}") + 1]
            result = json.loads(text)
            return {"id": criterion["id"], "pass": bool(result.get("pass", False))}
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                return {"id": criterion["id"], "pass": False, "reason": str(e)}


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    base_url = os.getenv("ANTHROPIC_BASE_URL")
    model = os.getenv("LLM_JUDGE_MODEL", "claude-haiku-4-5")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set, skipping LLM judge")
        json.dump({"criteria": [], "passed": 0, "total": 0, "score": 0.0},
                  open("/logs/verifier/llm_judge.json", "w"), indent=2)
        return
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = Anthropic(**client_kwargs)
    results = []
    print(f"=== LLM Judge: evaluating {len(CRITERIA)} criteria with {model} ===")
    for criterion in CRITERIA:
        print(f"  Evaluating: {criterion['id']} ...", end=" ", flush=True)
        result = judge_criterion(client, model, criterion)
        results.append(result)
        print("PASS" if result["pass"] else "FAIL")
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    score = round(passed / total, 4) if total > 0 else 0.0
    print(f"=== LLM Judge: {passed}/{total} criteria passed (score={score}) ===")
    Path("/logs/verifier/llm_judge.json").write_text(json.dumps(
        {"criteria": results, "passed": passed, "total": total, "score": score}, indent=2))


if __name__ == "__main__":
    main()

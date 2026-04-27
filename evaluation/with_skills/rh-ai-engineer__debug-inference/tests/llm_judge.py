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
    "id": "kserve_conditions_awareness",
    "file": "/root/report.md",
    "question": "Does the report explicitly name the KServe InferenceService status conditions — specifically PredictorReady and IngressReady — and present them in a structured conditions table with Status/Reason/Message columns?",
    "reference": "A skilled report should present a conditions table showing PredictorReady and IngressReady as distinct conditions with their status (True/False), reason, and message. Simply reporting 'CrashLoopBackOff' or 'pod failing' without naming the specific KServe conditions is insufficient."
  },
  {
    "id": "kserve_container_specificity",
    "file": "/root/report.md",
    "question": "Does the report mention 'kserve-container' by name as the specific container to inspect for logs, and reference the serving.kserve.io/inferenceservice label selector as the method for discovering predictor pods?",
    "reference": "A skilled report should mention 'kserve-container' as the container name for log inspection and reference the serving.kserve.io/inferenceservice label selector for pod discovery. Generically saying 'check pod logs' or 'look at the container' without these specific KServe identifiers is insufficient."
  },
  {
    "id": "nim_account_cr_pattern",
    "file": "/root/report.md",
    "question": "Does the report prescribe creating a NIM Account custom resource (kind: Account) as the credential management mechanism for NVIDIA NIM, rather than only manually creating docker-registry secrets and patching service accounts?",
    "reference": "A skilled report creates a NIM Account CR (kind: Account, apiVersion: nvidia.com/v1alpha1) with ngcSecret reference and imagePullSecret auto-creation. An unskilled report manually creates docker-registry secrets and patches service accounts without using the Account CR pattern."
  },
  {
    "id": "ngc_credential_expiry",
    "file": "/root/report.md",
    "question": "Does the report identify NGC API key or pull-secret expiry as a possible root cause for image pull failures in NIM deployments, and recommend checking the secret's expiration date?",
    "reference": "A skilled report checks whether the NGC pull-secret has expired as a diagnosis step for ImagePullBackOff. An unskilled report treats image pull failures generically without considering credential expiry."
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

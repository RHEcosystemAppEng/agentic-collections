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
    "id": "vram_budget_methodology",
    "file": "/root/report.md",
    "question": "Does the report present a specific GPU VRAM budget calculation for the vLLM OOM issue — showing the model weight size (~13.5 GiB), the KV cache allocation requirement (~28.5 GiB), and the available VRAM after model load (~10.1 GiB) — and explicitly state that this is a GPU VRAM constraint, NOT a pod system memory issue?",
    "reference": "A skilled report shows a VRAM budget breakdown: model weights (~13.5 GiB) loaded into GPU, KV cache requiring ~28.5 GiB, but only ~10.1 GiB available on the 24 GB A10G after model load. It explicitly distinguishes GPU VRAM from pod memory (system RAM). A report that says 'OOMKilled' and recommends increasing pod memory from 16Gi to 32Gi WITHOUT this GPU VRAM analysis is insufficient."
  },
  {
    "id": "rhoai_deployment_conventions",
    "file": "/root/report.md",
    "question": "Does the report use RHOAI-specific deployment conventions such as the RawDeployment annotation and GPU_MEMORY_UTILIZATION environment variable configuration, rather than generic Kubernetes deployment patterns?",
    "reference": "A skilled report uses serving.kserve.io/deploymentMode: RawDeployment annotation and configures vLLM tuning parameters (GPU_MEMORY_UTILIZATION, MAX_MODEL_LEN) as environment variables in the InferenceService spec. It also identifies NIMAccount CR dependencies for NIM deployments. A report that uses generic Kubernetes deployments or command-line args without RHOAI-specific annotations is insufficient."
  },
  {
    "id": "kserve_yaml_manifest",
    "file": "/root/report.md",
    "question": "Does the report include a complete KServe InferenceService YAML manifest with the serving.kserve.io/v1beta1 apiVersion, including metadata (name, namespace) and spec.predictor with model format, storage URI, resource requests, and GPU count?",
    "reference": "A skilled report provides a deployable InferenceService YAML with apiVersion: serving.kserve.io/v1beta1, kind: InferenceService, and a complete spec including predictor with model format, runtime reference, storage URI, resource requests (CPU, memory, GPU), and environment variables (VLLM_MAX_MODEL_LEN). A report that only describes fixes in narrative or MCP tool call format without a formal YAML manifest is insufficient."
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

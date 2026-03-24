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
    "id": "app_module_in_buildconfig",
    "file": "/root/report.md",
    "question": "Does the report specify that APP_MODULE should be set in the BuildConfig's sourceStrategy.env section (not as a generic environment variable), using the module:callable format (e.g., app:app or main:app)?",
    "reference": "A skilled report places APP_MODULE in sourceStrategy.env of the BuildConfig YAML, using the module:callable format. An unskilled report mentions APP_MODULE generically without specifying its placement in sourceStrategy.env."
  },
  {
    "id": "s2i_build_phases",
    "file": "/root/report.md",
    "question": "Does the report explain S2I build phases (assemble for dependency installation and compilation, run for application startup) and how they can be customized via .s2i/bin/ scripts?",
    "reference": "A skilled report explains the assemble and run phases and mentions .s2i/bin/assemble or .s2i/bin/run for customization. An unskilled report treats S2I as a monolithic process."
  },
  {
    "id": "gunicorn_dependency",
    "file": "/root/report.md",
    "question": "Does the report explicitly state that gunicorn must be in requirements.txt specifically BECAUSE the S2I Python builder uses gunicorn to serve the application specified by APP_MODULE?",
    "reference": "A skilled report identifies gunicorn as a required dependency for Python S2I with APP_MODULE. An unskilled report doesn't link gunicorn to the entry point mechanism."
  },
  {
    "id": "imagestream_as_separate_resource",
    "file": "/root/report.md",
    "question": "Does the report include a standalone ImageStream YAML manifest (with apiVersion: image.openshift.io/v1 and kind: ImageStream) as a separate resource definition, rather than only referencing ImageStreamTag within the BuildConfig output section?",
    "reference": "A skilled report defines the ImageStream as its own YAML resource with apiVersion: image.openshift.io/v1, kind: ImageStream, and lookupPolicy configuration, created as a prerequisite before the BuildConfig. An unskilled report only references ImageStreamTag as an output target in the BuildConfig but does not show the ImageStream resource definition."
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

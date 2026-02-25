#!/usr/bin/env python3
"""
Design compliance checker for agentic collection skills and agents.

Evaluates PR changes against the design principles in CLAUDE.md by:
  1. Running fast, deterministic pre-checks (no LLM needed).
  2. Sending relevant diffs to a GitHub Models-backed LLM for deeper analysis.
  3. Producing a structured JSON report and a GitHub-flavoured Markdown summary.

Exit codes:
  0 – compliant (or no skill/agent files changed)
  1 – one or more violations found
  2 – fatal error (e.g. policy file not found)

Usage:
    python scripts/design_compliance.py \\
        --diff-file      /tmp/pr.diff \\
        --policy-file    policy/design-compliance.yml \\
        --output-file    /tmp/compliance-report.json \\
        --summary-file   /tmp/compliance-summary.md
    # GITHUB_TOKEN must be set in the environment for LLM analysis.
    # Pass --skip-llm to run deterministic checks only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLAUDE_MD_PATH = "CLAUDE.md"
DESIGN_PRINCIPLES_HEADER = "## Design Principles for Skills and Agents"
GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"

# ---------------------------------------------------------------------------
# Policy loading
# ---------------------------------------------------------------------------


def load_policy(policy_file: str) -> dict[str, Any]:
    with open(policy_file, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# CLAUDE.md extraction
# ---------------------------------------------------------------------------


def extract_design_principles(max_chars: int = 8000) -> str:
    """Return the 'Design Principles for Skills and Agents' section of CLAUDE.md."""
    try:
        content = Path(CLAUDE_MD_PATH).read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

    start = content.find(DESIGN_PRINCIPLES_HEADER)
    if start == -1:
        return content[:max_chars]

    next_h2 = content.find("\n## ", start + len(DESIGN_PRINCIPLES_HEADER))
    section = content[start:next_h2] if next_h2 != -1 else content[start:]
    return section[:max_chars]


# ---------------------------------------------------------------------------
# Diff parsing helpers
# ---------------------------------------------------------------------------


def parse_diff_files(diff_content: str) -> dict[str, str]:
    """Parse a unified diff into {filepath: diff_chunk} mapping."""
    files: dict[str, str] = {}
    current_file: str | None = None
    current_lines: list[str] = []

    for line in diff_content.splitlines():
        if line.startswith("diff --git "):
            if current_file is not None:
                files[current_file] = "\n".join(current_lines)
            parts = line.split(" b/", 1)
            current_file = parts[1] if len(parts) == 2 else None
            current_lines = [line]
        elif current_file is not None:
            current_lines.append(line)

    if current_file is not None and current_lines:
        files[current_file] = "\n".join(current_lines)

    return files


def extract_added_content(file_diff: str) -> str:
    """Return only the lines that were *added* in a file diff."""
    return "\n".join(
        line[1:]
        for line in file_diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )


def get_file_content(filepath: str, file_diff: str) -> str:
    """Return current on-disk content, or the added lines from the diff."""
    p = Path(filepath)
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return extract_added_content(file_diff)


# ---------------------------------------------------------------------------
# File classification
# ---------------------------------------------------------------------------

_SKILL_RE = re.compile(r"(?:^|/)skills/[^/]+/SKILL\.md$")
_AGENT_RE = re.compile(r"(?:^|/)agents/[^/]+\.md$")


def is_skill_file(path: str) -> bool:
    return bool(_SKILL_RE.search(path))


def is_agent_file(path: str) -> bool:
    return bool(_AGENT_RE.search(path))


# ---------------------------------------------------------------------------
# Deterministic checks
# ---------------------------------------------------------------------------


def check_yaml_frontmatter(
    content: str, required_fields: list[str]
) -> list[dict[str, str]]:
    """Validate YAML frontmatter; return list of violation dicts."""
    violations: list[dict[str, str]] = []
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return [
            {
                "principle": "6 - Mandatory Skill Sections",
                "description": "Missing YAML frontmatter (file must start with --- … ---).",
                "line": "1",
            }
        ]
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        return [
            {
                "principle": "6 - Mandatory Skill Sections",
                "description": f"Invalid YAML frontmatter: {exc}",
                "line": "1",
            }
        ]
    for field in required_fields:
        if field not in data:
            violations.append(
                {
                    "principle": "6 - Mandatory Skill Sections",
                    "description": f"Missing required frontmatter field: '{field}'.",
                    "line": "1",
                }
            )
    return violations


def check_required_sections(
    content: str, required_sections: list[str], file_type: str
) -> list[dict[str, str]]:
    """Check that required ## Section headings are present.

    Matches any heading (##, ###) that contains the required keyword as a
    whole word, so "## Your Workflow" satisfies the "Workflow" requirement.
    """
    violations = []
    for section in required_sections:
        pattern = re.compile(
            r"^#{1,3}\s+.*\b" + re.escape(section) + r"\b",
            re.MULTILINE | re.IGNORECASE,
        )
        if not pattern.search(content):
            violations.append(
                {
                    "principle": "6 - Mandatory Skill Sections",
                    "description": (
                        f"{file_type} is missing required section '## {section}'."
                    ),
                    "line": "N/A",
                }
            )
    return violations


def check_mcp_tool_denylist(
    content: str, denylist: list[str], filepath: str
) -> list[dict[str, str]]:
    """Flag direct MCP tool references inside agent files."""
    violations = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        for pattern in denylist:
            if pattern in line:
                violations.append(
                    {
                        "principle": (
                            "Core Architecture - Agents orchestrate skills; "
                            "skills encapsulate tools"
                        ),
                        "description": (
                            f"Agent file references MCP tool pattern '{pattern}' directly. "
                            "Agents must invoke Skills, not MCP tools."
                        ),
                        "line": str(lineno),
                    }
                )
                break  # one violation per line
    return violations


def check_doc_consultation_pattern(
    content: str,
) -> list[dict[str, str]]:
    """
    Detect 'transparency theater': a Document Consultation section that
    claims to consult a file but does NOT include a mandatory Read action.

    Accepted patterns (per CLAUDE.md):
      - "using the Read tool"
      - "Read tool"
      - "**Action**: Read ..."  (markdown bold label followed by Read)
    """
    violations = []
    if "Document Consultation" not in content:
        return violations

    has_read_action = bool(
        re.search(
            r"using the Read tool"          # preferred CLAUDE.md form
            r"|Read\s+tool"                 # short form
            r"|\*\*Action\*\*:\s*Read",     # **Action**: Read ...
            content,
            re.IGNORECASE,
        )
    )
    if not has_read_action:
        violations.append(
            {
                "principle": "1 - Document Consultation Transparency",
                "description": (
                    "'Document Consultation' section present but the mandatory "
                    "Read action is missing. Must include 'Read [file] using the "
                    "Read tool' or '**Action**: Read …' BEFORE declaring "
                    "'I consulted [file]'."
                ),
                "line": "N/A",
            }
        )
    return violations


def run_deterministic_checks(
    diff_files: dict[str, str], policy: dict[str, Any]
) -> tuple[list[dict], list[dict]]:
    """
    Run all deterministic checks on changed skill/agent files.

    Returns:
        (violations, warnings)
    """
    checks = policy.get("deterministic_checks", {})
    mcp_denylist: list[str] = checks.get("mcp_tool_denylist", [])
    skill_required_fm: list[str] = checks.get("skill_required_frontmatter", [])
    agent_required_fm: list[str] = checks.get("agent_required_frontmatter", [])
    skill_sections: list[str] = checks.get("skill_required_sections", [])
    agent_sections: list[str] = checks.get("agent_required_sections", [])

    violations: list[dict] = []
    warnings: list[dict] = []

    for filepath, diff_content in diff_files.items():
        content = get_file_content(filepath, diff_content)
        if not content.strip():
            continue

        raw_violations: list[dict[str, str]] = []

        if is_skill_file(filepath):
            raw_violations += check_yaml_frontmatter(content, skill_required_fm)
            raw_violations += check_required_sections(content, skill_sections, "Skill")
            raw_violations += check_doc_consultation_pattern(content)

        elif is_agent_file(filepath):
            raw_violations += check_yaml_frontmatter(content, agent_required_fm)
            raw_violations += check_required_sections(content, agent_sections, "Agent")
            raw_violations += check_mcp_tool_denylist(content, mcp_denylist, filepath)
            raw_violations += check_doc_consultation_pattern(content)

        for v in raw_violations:
            violations.append({"file": filepath, **v})

    return violations, warnings


# ---------------------------------------------------------------------------
# LLM integration – GitHub Models
# ---------------------------------------------------------------------------


def build_llm_messages(design_principles: str, relevant_diff: str) -> list[dict]:
    system_prompt = (
        "You are a code-review assistant that evaluates changes to AI skill/agent "
        "definitions against a set of design principles.\n\n"
        "Focus ONLY on files matching '*/skills/*/SKILL.md' or '*/agents/*.md'.\n"
        "Respond ONLY with valid JSON – no prose, no markdown fences.\n\n"
        "Required JSON schema:\n"
        "{\n"
        '  "compliant": <boolean>,\n'
        '  "violations": [\n'
        '    {"file": "<path>", "principle": "<id + name>", '
        '"description": "<what is wrong>", "line": "<number or N/A>"}\n'
        "  ],\n"
        '  "warnings": [\n'
        '    {"file": "<path>", "principle": "<id + name>", "description": "<note>"}\n'
        "  ],\n"
        '  "summary": "<1-3 sentence summary>"\n'
        "}"
    )

    user_prompt = f"""## Design Principles (extracted from CLAUDE.md)

{design_principles}

## PR Diff

{relevant_diff}

## Review Task

Evaluate the diff against the design principles. Check specifically:

1. **Document Consultation Transparency (Principle 1)** – When a skill/agent mentions
   consulting a document, it MUST include a step that says "Read [file] using the Read
   tool" BEFORE declaring "I consulted [file]". A declaration without the Read action
   is "transparency theater" and a violation.

2. **Agents orchestrate skills; skills encapsulate tools (Core Architecture)** –
   Agent files (agents/*.md) must invoke Skills via the Skill tool, NOT call MCP tools
   directly. Any direct MCP tool patterns (e.g. vulnerability__, ansible__, __get_cves)
   inside an agent are violations.

3. **Single-purpose skills (Principle 3)** – Each skill should encapsulate one focused
   task. Flag skills that try to do many unrelated things.

4. **Mandatory sections (Principle 6)** – Skills must contain ## Prerequisites,
   ## Workflow, and ## Dependencies. Agents must contain ## Prerequisites and
   ## Workflow.

5. **Precise parameter specification (Principle 2)** – Skills that reference MCP tools
   must show exact parameter names and example values, not vague descriptions.
   Document consultation steps must appear BEFORE MCP tool invocation steps.

If no skill/agent files are changed in the diff, respond with
{{"compliant": true, "violations": [], "warnings": [], "summary": "No skill/agent files changed."}}
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def call_github_models(
    token: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    temperature: float,
    retries: int = 3,
) -> str:
    """Call the GitHub Models inference API; return the assistant message content."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                GITHUB_MODELS_URL, headers=headers, json=payload, timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as exc:
            last_exc = exc
            status = exc.response.status_code if exc.response is not None else "?"
            print(
                f"  ⚠️  GitHub Models API HTTP {status} on attempt {attempt}/{retries}",
                file=sys.stderr,
            )
            if status in (429, 503, 504) and attempt < retries:
                time.sleep(5 * attempt)
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f"Unexpected GitHub Models response format: {exc}"
            ) from exc

    raise RuntimeError(
        f"GitHub Models API failed after {retries} attempts: {last_exc}"
    )


def parse_llm_response(response_text: str) -> dict[str, Any]:
    """Validate structure and return the parsed JSON from the LLM."""
    text = response_text.strip()
    # Strip optional markdown fences
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM response is not valid JSON: {exc}\nResponse (first 500 chars): {text[:500]}"
        ) from exc

    for field in ("compliant", "violations", "warnings", "summary"):
        if field not in data:
            raise ValueError(f"LLM response is missing required field '{field}'")

    if not isinstance(data["compliant"], bool):
        raise ValueError(f"'compliant' must be boolean, got {type(data['compliant'])}")
    if not isinstance(data["violations"], list):
        raise ValueError(f"'violations' must be a list, got {type(data['violations'])}")
    if not isinstance(data["warnings"], list):
        raise ValueError(f"'warnings' must be a list, got {type(data['warnings'])}")

    return data


# ---------------------------------------------------------------------------
# Diff filtering for LLM
# ---------------------------------------------------------------------------


def build_llm_diff(diff_files: dict[str, str], max_bytes: int) -> str:
    """Return a size-limited diff string containing only skill/agent files."""
    parts: list[str] = []
    total = 0
    truncated = False

    for filepath, diff_content in diff_files.items():
        if not (is_skill_file(filepath) or is_agent_file(filepath)):
            continue
        chunk = f"=== {filepath} ===\n{diff_content}\n"
        if total + len(chunk) > max_bytes:
            remaining = max_bytes - total
            if remaining > 200:
                parts.append(
                    f"=== {filepath} (TRUNCATED at {remaining} bytes) ===\n"
                    f"{diff_content[:remaining]}\n"
                )
            truncated = True
            break
        parts.append(chunk)
        total += len(chunk)

    result = "\n".join(parts)
    if truncated:
        result += (
            "\n[NOTE: Diff truncated due to size limit. "
            "Remaining files were not sent to the LLM.]\n"
        )
    return result


# ---------------------------------------------------------------------------
# Report / summary rendering
# ---------------------------------------------------------------------------


def generate_summary(report: dict[str, Any]) -> str:
    """Return GitHub-flavoured Markdown for the job summary."""
    status_icon = "✅" if report["compliant"] else "❌"
    status_text = "PASSED" if report["compliant"] else "FAILED"
    lines = [
        f"# {status_icon} Design Compliance Check – {status_text}",
        "",
        f"**Summary**: {report.get('summary', '')}",
        "",
    ]

    det_violations = report.get("deterministic_violations", [])
    if det_violations:
        lines += [
            f"## 🔍 Pre-check Violations ({len(det_violations)})",
            "",
        ]
        for v in det_violations:
            lines.append(
                f"- **`{v['file']}`** line {v['line']} "
                f"[{v['principle']}]: {v['description']}"
            )
        lines.append("")

    llm_violations = report.get("llm_violations", [])
    if llm_violations:
        lines += [
            f"## 🤖 LLM-detected Violations ({len(llm_violations)})",
            "",
        ]
        for v in llm_violations:
            lines.append(
                f"- **`{v['file']}`** line {v.get('line', 'N/A')} "
                f"[{v['principle']}]: {v['description']}"
            )
        lines.append("")

    warnings = report.get("warnings", [])
    if warnings:
        lines += [
            f"## ⚠️ Warnings ({len(warnings)})",
            "",
        ]
        for w in warnings:
            lines.append(
                f"- **`{w['file']}`** [{w['principle']}]: {w['description']}"
            )
        lines.append("")

    if report["compliant"] and not det_violations and not llm_violations:
        lines.append(
            "> ✅ All changed skill/agent files comply with the design principles."
        )

    if report.get("llm_error"):
        lines += [
            "",
            f"> ⚠️ **LLM analysis skipped**: {report['llm_error']}",
        ]

    lines += [
        "",
        "---",
        "_Powered by [design-compliance](../.github/DESIGN_COMPLIANCE.md) · "
        "policy: `policy/design-compliance.yml`_",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Design compliance checker for agentic collection PRs"
    )
    parser.add_argument(
        "--diff-file", required=True, help="Path to the unified diff file"
    )
    parser.add_argument(
        "--policy-file", required=True, help="Path to policy/design-compliance.yml"
    )
    parser.add_argument(
        "--output-file", required=True, help="Where to write the JSON report"
    )
    parser.add_argument(
        "--summary-file", help="Where to write the Markdown job summary (optional)"
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Run deterministic checks only (no LLM call)",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")

    # ── Load policy ────────────────────────────────────────────────────────
    try:
        policy = load_policy(args.policy_file)
    except Exception as exc:
        print(f"❌ Cannot load policy file '{args.policy_file}': {exc}", file=sys.stderr)
        return 2

    # ── Read diff ──────────────────────────────────────────────────────────
    try:
        diff_content = Path(args.diff_file).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        print(f"❌ Diff file not found: {args.diff_file}", file=sys.stderr)
        return 2

    diff_files = parse_diff_files(diff_content)
    relevant = [f for f in diff_files if is_skill_file(f) or is_agent_file(f)]

    print(f"📁 Changed files in diff  : {len(diff_files)}")
    print(f"📋 Skill/agent files      : {len(relevant)}")
    for f in relevant:
        print(f"   - {f}")

    # ── Build report skeleton ──────────────────────────────────────────────
    model_cfg = policy.get("model", {})
    report: dict[str, Any] = {
        "compliant": True,
        "deterministic_violations": [],
        "llm_violations": [],
        "warnings": [],
        "summary": "",
        "files_checked": relevant,
        "llm_model": model_cfg.get("name", "gpt-4o-mini"),
        "llm_used": False,
    }

    # ── Step 1: Deterministic pre-checks ──────────────────────────────────
    print("\n🔍 Running deterministic pre-checks …")
    det_violations, det_warnings = run_deterministic_checks(diff_files, policy)
    report["deterministic_violations"] = det_violations
    report["warnings"].extend(det_warnings)

    if det_violations:
        print(f"   ❌ {len(det_violations)} pre-check violation(s) found")
        for v in det_violations:
            print(f"      [{v['file']}:{v['line']}] {v['description']}")
    else:
        print("   ✅ No pre-check violations")

    # ── Step 2: LLM analysis ───────────────────────────────────────────────
    if relevant and not args.skip_llm:
        if not token:
            msg = "GITHUB_TOKEN not set – skipping LLM analysis."
            print(f"\n⚠️  {msg}", file=sys.stderr)
            report["llm_error"] = msg
        else:
            print("\n🤖 Running LLM analysis via GitHub Models …")
            design_principles = extract_design_principles()
            max_bytes = policy.get("diff_limits", {}).get("max_bytes", 51200)
            llm_diff = build_llm_diff(diff_files, max_bytes)

            if llm_diff.strip():
                messages = build_llm_messages(design_principles, llm_diff)
                try:
                    raw = call_github_models(
                        token=token,
                        model=model_cfg.get("name", "gpt-4o-mini"),
                        messages=messages,
                        max_tokens=model_cfg.get("max_tokens", 2000),
                        temperature=model_cfg.get("temperature", 0.1),
                    )
                    llm_result = parse_llm_response(raw)
                    report["llm_violations"] = llm_result.get("violations", [])
                    report["warnings"].extend(llm_result.get("warnings", []))
                    report["summary"] = llm_result.get("summary", "")
                    report["llm_used"] = True
                    print(
                        f"   {'❌' if report['llm_violations'] else '✅'} "
                        f"{len(report['llm_violations'])} LLM violation(s) found"
                    )
                except Exception as exc:
                    msg = str(exc)
                    print(f"   ⚠️  LLM analysis failed: {msg}", file=sys.stderr)
                    report["llm_error"] = msg
                    report["summary"] = (
                        "LLM analysis failed; only deterministic checks were run."
                    )
            else:
                print("   ℹ️  No relevant diff content for LLM (nothing to send)")
    elif not relevant:
        report["summary"] = "No skill/agent files changed – compliance check not required."
        print("\nℹ️  No skill/agent files changed; skipping LLM analysis.")

    # ── Finalise report ────────────────────────────────────────────────────
    all_violations = report["deterministic_violations"] + report["llm_violations"]
    report["compliant"] = len(all_violations) == 0

    if not report["summary"]:
        if report["compliant"]:
            report["summary"] = (
                f"All {len(relevant)} skill/agent file(s) comply with the design principles."
            )
        else:
            report["summary"] = (
                f"Found {len(all_violations)} violation(s) across "
                f"{len(relevant)} skill/agent file(s)."
            )

    # ── Write JSON report ──────────────────────────────────────────────────
    try:
        Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_file, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"\n📄 JSON report written to: {args.output_file}")
    except OSError as exc:
        print(f"⚠️  Failed to write JSON report: {exc}", file=sys.stderr)

    # ── Write Markdown summary ─────────────────────────────────────────────
    summary_md = generate_summary(report)
    if args.summary_file:
        try:
            with open(args.summary_file, "w", encoding="utf-8") as fh:
                fh.write(summary_md)
            print(f"📝 Markdown summary written to: {args.summary_file}")
        except OSError as exc:
            print(f"⚠️  Failed to write summary file: {exc}", file=sys.stderr)

    # ── Final verdict ──────────────────────────────────────────────────────
    if report["compliant"]:
        print("\n✅ Design compliance check PASSED")
        return 0
    else:
        print(
            f"\n❌ Design compliance check FAILED "
            f"({len(all_violations)} violation(s))"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

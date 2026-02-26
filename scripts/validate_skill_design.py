#!/usr/bin/env python3
"""
Validate skills against SKILL_DESIGN_PRINCIPLES.md.

Design principles checked:
  DP1: Document Consultation - correct format (Action: Read, Output to user)
  DP2: Parameter order - Document Consultation before MCP Tool/Parameters
  DP3: Conciseness - description length, "Use when" examples
  DP4: Dependencies - section with Required MCP Servers/Tools, Related Skills, Reference Docs
  DP5: Human-in-the-Loop - critical skills should have this section
  DP6: Mandatory sections - Prerequisites, When to Use This Skill, Workflow
  DP7: Credential security - no echo $VAR (except in anti-pattern examples)

Cannot validate: runtime behavior (AI actually reading docs), parameter correctness vs MCP schemas.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml

# Design principle constants
MAX_DESCRIPTION_TOKENS = 500
# Rough token estimate: ~4 chars per token for English
CHARS_PER_TOKEN = 4
MAX_DESCRIPTION_CHARS = MAX_DESCRIPTION_TOKENS * CHARS_PER_TOKEN

# Skills that perform critical operations (require Human-in-the-Loop section)
CRITICAL_SKILL_KEYWORDS = [
    "executor",
    "playbook-executor",
    "job-template-creator",
    "remediator",
]

# Required sections (DP6) - Prerequisites is optional
REQUIRED_SECTIONS = [
    "When to Use This Skill",
    "Workflow",
]
# Expected order when all present
ORDERED_SECTIONS = [
    "Prerequisites",
    "When to Use This Skill",
    "Workflow",
]

# Dependencies subsections (DP4)
DEPENDENCY_SUBSECTIONS = [
    "Required MCP Servers",
    "Required MCP Tools",
    "Related Skills",
    "Reference Documentation",
]

# Credential exposure patterns (DP7)
CREDENTIAL_EXPOSURE_PATTERN = re.compile(
    r"echo\s+\$\{?[A-Za-z_][A-Za-z0-9_]*\}?",
    re.MULTILINE,
)

# Anti-pattern context: if echo $VAR appears near these, it may be documenting the wrong way
ANTI_PATTERN_MARKERS = ["WRONG", "NEVER", "❌", "don't", "do not", "exposes credentials"]


@dataclass
class ValidationResult:
    """Result of validating a single skill."""

    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def find_skill_files(pack_dirs: list[str]) -> Iterator[Path]:
    """Yield paths to all SKILL.md files in pack directories."""
    for pack_dir in pack_dirs:
        skills_dir = Path(pack_dir) / "skills"
        if skills_dir.exists():
            yield from skills_dir.glob("*/SKILL.md")


def extract_frontmatter(content: str) -> tuple[dict | None, str]:
    """Extract YAML frontmatter and body from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None, content
    try:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end() :]
        return frontmatter, body
    except yaml.YAMLError:
        return None, content


def check_dp1_document_consultation(body: str, result: ValidationResult) -> None:
    """
    DP1: Document Consultation Transparency.
    - If Document Consultation appears, it must have Action: Read and Output to user.
    - Flag 'Transparency Theater' (output-only without Action).
    """
    doc_consult_blocks = re.findall(
        r"\*\*Document Consultation\*\*[^*]*(?:\*\*[^*]*\*\*[^*]*)*",
        body,
        re.DOTALL,
    )

    for block in doc_consult_blocks:
        has_action_read = "Read [" in block or "Read [" in block.replace("\n", " ")
        has_output = "Output to user" in block or "I consulted" in block

        # Transparency Theater: has output declaration but no Action
        if "Output to user" in block or "output to user" in block.lower():
            if not has_action_read and "Action" not in block:
                result.warnings.append(
                    "DP1: Document Consultation may be 'Transparency Theater' "
                    "(output declared but no 'Action: Read' - ensure AI actually reads the file)"
                )

        if has_action_read and not has_output:
            result.warnings.append(
                "DP1: Document Consultation has Action but missing 'Output to user' declaration"
            )


def check_dp2_parameter_order(body: str, result: ValidationResult) -> None:
    """
    DP2: Document consultation must appear BEFORE MCP Tool/Parameters.
    Check workflow steps that have both.
    """
    # Find workflow steps (### Step N or #### Option)
    step_pattern = re.compile(
        r"(###+ [^\n]+\n)(.*?)(?=###+ |\Z)",
        re.DOTALL,
    )

    for match in step_pattern.finditer(body):
        step_content = match.group(2)
        has_mcp_tool = "MCP Tool" in step_content or "**MCP Tool**" in step_content
        has_params = "**Parameters**" in step_content or "Parameters:" in step_content
        has_doc_consult = "Document Consultation" in step_content

        if (has_mcp_tool or has_params) and has_doc_consult:
            doc_pos = step_content.find("Document Consultation")
            tool_pos = step_content.find("MCP Tool")
            params_pos = step_content.find("Parameters")

            if tool_pos >= 0 and doc_pos > tool_pos:
                result.errors.append(
                    "DP2: Document Consultation must appear BEFORE MCP Tool in workflow step"
                )
            if params_pos >= 0 and doc_pos > params_pos and "Parameters" in step_content:
                result.errors.append(
                    "DP2: Document Consultation must appear BEFORE Parameters in workflow step"
                )


def check_dp3_conciseness(frontmatter: dict | None, result: ValidationResult) -> None:
    """
    DP3: Skill Precedence and Conciseness.
    - Description under 500 tokens.
    - Focus on 'when to use' with 3-5 examples.
    """
    if not frontmatter or "description" not in frontmatter:
        return

    desc = frontmatter["description"]
    if isinstance(desc, list):
        desc = "\n".join(desc)
    desc_str = str(desc).strip()

    # Token estimate
    char_count = len(desc_str)
    if char_count > MAX_DESCRIPTION_CHARS:
        result.warnings.append(
            f"DP3: Description may exceed 500 tokens "
            f"(~{char_count // CHARS_PER_TOKEN} tokens, {char_count} chars). "
            "Keep frontmatter concise; defer details to skill body."
        )

    # Use when examples
    if "Use when" not in desc_str and "use when" not in desc_str.lower():
        result.warnings.append(
            "DP3: Description should include 'Use when' with 3-5 concrete examples"
        )


def check_dp4_dependencies(body: str, result: ValidationResult) -> None:
    """
    DP4: Dependencies Declaration.
    Must have ## Dependencies with required subsections.
    """
    if "## Dependencies" not in body:
        result.errors.append("DP4: Missing '## Dependencies' section")
        return

    # Use (?=\n## |\Z) to avoid matching "## " inside "### " (subsection headers)
    deps_section = re.search(
        r"## Dependencies\s*\n(.*?)(?=\n## |\Z)",
        body,
        re.DOTALL,
    )
    if not deps_section:
        return

    section_content = deps_section.group(1)
    for subsection in DEPENDENCY_SUBSECTIONS:
        if subsection not in section_content:
            result.warnings.append(
                f"DP4: Dependencies section should include '### {subsection}'"
            )


def check_dp5_human_in_loop(
    name: str, body: str, result: ValidationResult
) -> None:
    """
    DP5: Human-in-the-Loop Requirements.
    Critical skills (executor, playbook, etc.) must have this section.
    """
    is_critical = any(kw in name.lower() for kw in CRITICAL_SKILL_KEYWORDS)
    has_section = "Human-in-the-Loop" in body or "Human-in-the-Loop Requirements" in body

    if is_critical and not has_section:
        result.warnings.append(
            "DP5: Skill performs critical operations (execution/modification). "
            "Consider adding '## Critical: Human-in-the-Loop Requirements' section."
        )


def check_dp6_mandatory_sections(body: str, result: ValidationResult) -> None:
    """
    DP6: Mandatory Skill Sections.
    Must have When to Use This Skill, Workflow. Prerequisites is optional.
    When present, sections must appear in order: Prerequisites, When to Use, Workflow.
    """
    section_headings = re.findall(r"^## ([^\n#]+)", body, re.MULTILINE)

    for required in REQUIRED_SECTIONS:
        if required not in section_headings:
            result.errors.append(f"DP6: Missing required section '## {required}'")
            return

    # Check order for sections that are present (Prerequisites, When to Use, Workflow)
    indices = []
    for i, heading in enumerate(section_headings):
        for req in ORDERED_SECTIONS:
            if req in heading or heading.strip() == req:
                indices.append((ORDERED_SECTIONS.index(req), i))
                break

    if len(indices) >= 2:
        indices.sort(key=lambda x: x[0])
        for i in range(1, len(indices)):
            if indices[i][1] < indices[i - 1][1]:
                result.warnings.append(
                    f"DP6: Sections should appear in order: "
                    f"{', '.join(ORDERED_SECTIONS)}"
                )
                break


def check_dp7_credential_exposure(body: str, result: ValidationResult) -> None:
    """
    DP7: MCP Server Availability Verification - no credential exposure.
    Flag echo $VAR unless it's in an anti-pattern example (WRONG, NEVER, ❌).
    """
    lines = body.split("\n")
    in_code_block = False
    code_block_context = ""

    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                code_block_context = ""
            continue

        if in_code_block:
            code_block_context += line + "\n"
        else:
            code_block_context = line

        match = CREDENTIAL_EXPOSURE_PATTERN.search(line)
        if match:
            # Check if this is in a "wrong example" context
            context_before = "\n".join(lines[max(0, i - 10) : i]).lower()
            is_anti_pattern = any(
                marker.lower() in context_before for marker in ANTI_PATTERN_MARKERS
            )
            if not is_anti_pattern:
                result.errors.append(
                    f"DP7: Potential credential exposure at line {i + 1}: "
                    f"'{match.group().strip()}'. "
                    "Never echo env vars; use 'test -n \"$VAR\"' or report presence/absence only."
                )


def check_frontmatter_fields(
    frontmatter: dict | None,
    result: ValidationResult,
) -> None:
    """Check required frontmatter fields (name, description). Model is optional."""
    if not frontmatter:
        result.errors.append("Missing or invalid YAML frontmatter")
        return

    required = ["name", "description"]
    for field_name in required:
        if field_name not in frontmatter:
            result.errors.append(f"Frontmatter missing required field: {field_name}")

    if "color" in frontmatter:
        valid_colors = {"red", "blue", "green", "yellow", "cyan", "magenta"}
        if frontmatter["color"].lower() not in valid_colors:
            result.warnings.append(
                f"Frontmatter 'color' should be one of: {', '.join(sorted(valid_colors))}"
            )

    if "metadata" in frontmatter:
        meta = frontmatter["metadata"]
        if not isinstance(meta, dict):
            result.warnings.append(
                "Frontmatter 'metadata' should be a key-value map (dict), not a string or list"
            )


def validate_skill(skill_path: Path) -> ValidationResult:
    """Run all design principle checks on a skill file."""
    result = ValidationResult(path=skill_path)

    try:
        content = skill_path.read_text(encoding="utf-8")
    except Exception as e:
        result.errors.append(f"Could not read file: {e}")
        return result

    frontmatter, body = extract_frontmatter(content)

    check_frontmatter_fields(frontmatter, result)
    check_dp1_document_consultation(body, result)
    check_dp2_parameter_order(body, result)
    check_dp3_conciseness(frontmatter, result)
    check_dp4_dependencies(body, result)
    check_dp5_human_in_loop(
        frontmatter.get("name", "") if frontmatter else "", body, result
    )
    check_dp6_mandatory_sections(body, result)
    check_dp7_credential_exposure(body, result)

    return result


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate skills against SKILL_DESIGN_PRINCIPLES.md"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["rh-sre", "rh-developer", "ocp-admin", "rh-support-engineer", "rh-virt"],
        help="Pack directories or specific SKILL.md paths to validate",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args()

    # Resolve paths to skill files
    skill_files: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_file() and path.name == "SKILL.md":
            skill_files.append(path)
        elif path.is_dir():
            skills_dir = path / "skills"
            if skills_dir.exists():
                skill_files.extend(skills_dir.glob("*/SKILL.md"))
        else:
            # Maybe it's a pack name
            pack_path = Path(p)
            if (pack_path / "skills").exists():
                skill_files.extend((pack_path / "skills").glob("*/SKILL.md"))

    if not skill_files:
        print("No SKILL.md files found to validate.")
        return 0

    print("🔍 Validating skills against Design Principles...")
    print()

    all_errors: list[tuple[Path, str]] = []
    all_warnings: list[tuple[Path, str]] = []

    for skill_path in sorted(skill_files):
        result = validate_skill(skill_path)
        rel_path = skill_path.relative_to(Path.cwd()) if skill_path.is_relative_to(Path.cwd()) else skill_path

        if result.errors:
            print(f"  {rel_path}: ❌")
            for err in result.errors:
                all_errors.append((skill_path, err))
                print(f"    • {err}")
        elif result.warnings:
            print(f"  {rel_path}: ⚠️")
            for warn in result.warnings:
                all_warnings.append((skill_path, warn))
                if args.warnings_as_errors:
                    all_errors.append((skill_path, f"[WARN] {warn}"))
                print(f"    • {warn}")
        else:
            print(f"  {rel_path}: ✓")

    print()

    if all_errors or (args.warnings_as_errors and all_warnings):
        print("❌ Validation failed")
        return 1

    if all_warnings:
        print("✅ Validation passed (with warnings)")
    else:
        print("✅ All skills validated successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())

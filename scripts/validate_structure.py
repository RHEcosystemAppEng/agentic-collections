#!/usr/bin/env python3
"""
Validate agentic collection pack structure (plugin.json, mcps.json, CLAUDE.md).

Skill-level validation (frontmatter, sections, security) is handled by
validate-skills.sh and run-skill-linter.sh.
"""

import json
import sys
from pathlib import Path
from typing import List
import re

# List of agentic collections to validate
PACK_DIRS = ['rh-sre', 'rh-developer', 'ocp-admin', 'rh-support-engineer', 'rh-virt', 'rh-ai-engineer', 'rh-automation']


def validate_plugin_json(pack_dir: str) -> List[str]:
    """
    Validate plugin.json structure.

    Args:
        pack_dir: Collection directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    plugin_path = Path(pack_dir) / '.claude-plugin' / 'plugin.json'

    if not plugin_path.exists():
        # plugin.json is optional
        return errors

    try:
        with open(plugin_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check required fields
        if 'name' not in data:
            errors.append(f"{pack_dir}: plugin.json missing required field 'name'")
        if 'version' not in data:
            errors.append(f"{pack_dir}: plugin.json missing required field 'version'")
        if 'description' not in data:
            errors.append(f"{pack_dir}: plugin.json missing required field 'description'")

    except json.JSONDecodeError as e:
        errors.append(f"{pack_dir}: Invalid JSON in plugin.json: {e}")
    except Exception as e:
        errors.append(f"{pack_dir}: Error reading plugin.json: {e}")

    return errors


MCP_FILENAME = "mcps.json"
MCP_DEPRECATED = ".mcp.json"


def validate_mcp_json(pack_dir: str) -> List[str]:
    """
    Validate mcps.json structure.
    Errors if deprecated .mcp.json exists (must be renamed to mcps.json).

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    pack_path = Path(pack_dir)
    deprecated_path = pack_path / MCP_DEPRECATED
    mcp_path = pack_path / MCP_FILENAME

    if deprecated_path.exists():
        errors.append(
            f"{pack_dir}: deprecated {MCP_DEPRECATED} found; rename to {MCP_FILENAME}"
        )
        return errors

    if not mcp_path.exists():
        # mcps.json is optional
        return errors

    try:
        with open(mcp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check for mcpServers key
        if 'mcpServers' not in data:
            errors.append(f"{pack_dir}: {MCP_FILENAME} missing 'mcpServers' key")
        elif not isinstance(data['mcpServers'], dict):
            errors.append(f"{pack_dir}: {MCP_FILENAME} 'mcpServers' must be an object")

    except json.JSONDecodeError as e:
        errors.append(f"{pack_dir}: Invalid JSON in {MCP_FILENAME}: {e}")
    except Exception as e:
        errors.append(f"{pack_dir}: Error reading {MCP_FILENAME}: {e}")

    return errors


CLAUDE_MD_REQUIRED_SECTIONS = [
    "Skill-First Rule",
    "Intent Routing",
    "MCP Servers",
    "Global Rules",
]


def validate_claude_md(pack_dir: str) -> List[str]:
    """
    Validate CLAUDE.md presence and structure.

    Required for any pack that has skills. Checks for required sections
    and verifies that all skills appear in the intent routing content.

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    claude_path = Path(pack_dir) / 'CLAUDE.md'
    skills_dir = Path(pack_dir) / 'skills'

    has_skills = skills_dir.exists() and any(skills_dir.glob('*/SKILL.md'))

    if not claude_path.exists():
        if has_skills:
            errors.append(f"{pack_dir}: Missing CLAUDE.md (required for packs with skills)")
        return errors

    try:
        with open(claude_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check required sections
        headings = re.findall(r'^## (.+)$', content, re.MULTILINE)
        for section in CLAUDE_MD_REQUIRED_SECTIONS:
            if not any(section in h for h in headings):
                errors.append(f"{pack_dir}: CLAUDE.md missing required section '## {section}'")

        # Check intent routing completeness
        if has_skills:
            skill_names = [p.parent.name for p in skills_dir.glob('*/SKILL.md')]
            for skill_name in skill_names:
                if skill_name not in content:
                    errors.append(
                        f"{pack_dir}: CLAUDE.md intent routing missing skill '{skill_name}'"
                    )

    except Exception as e:
        errors.append(f"{pack_dir}: Error reading CLAUDE.md: {e}")

    return errors


def validate_pack(pack_dir: str) -> List[str]:
    """
    Validate a single pack.

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check if pack directory exists
    if not Path(pack_dir).exists():
        errors.append(f"{pack_dir}: Pack directory does not exist")
        return errors

    # Validate plugin.json
    errors.extend(validate_plugin_json(pack_dir))

    # Validate mcps.json
    errors.extend(validate_mcp_json(pack_dir))

    # Validate CLAUDE.md
    errors.extend(validate_claude_md(pack_dir))

    return errors


def main():
    """
    Main validation function.
    """
    print("🔍 Validating agentic collection structure...")
    print()

    all_errors = []

    for pack_dir in PACK_DIRS:
        print(f"Validating {pack_dir}...", end=' ')
        errors = validate_pack(pack_dir)

        if errors:
            print("❌")
            all_errors.extend(errors)
        else:
            print("✓")

    print()

    if all_errors:
        print("❌ Validation failed:")
        print()
        for error in all_errors:
            print(f"  • {error}")
        print()
        return 1
    else:
        print("✅ All collections validated successfully")
        print()
        return 0


if __name__ == '__main__':
    sys.exit(main())

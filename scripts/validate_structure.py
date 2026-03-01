#!/usr/bin/env python3
"""
Validate agentic collection structure before documentation generation.
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple
import yaml
import re

# List of agentic collections to validate
PACK_DIRS = ['rh-sre', 'rh-developer', 'ocp-admin', 'rh-support-engineer', 'rh-virt', 'rh-ai-engineer']


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


def validate_mcp_json(pack_dir: str) -> List[str]:
    """
    Validate .mcp.json structure.

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    mcp_path = Path(pack_dir) / '.mcp.json'

    if not mcp_path.exists():
        # .mcp.json is optional
        return errors

    try:
        with open(mcp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check for mcpServers key
        if 'mcpServers' not in data:
            errors.append(f"{pack_dir}: .mcp.json missing 'mcpServers' key")
        elif not isinstance(data['mcpServers'], dict):
            errors.append(f"{pack_dir}: .mcp.json 'mcpServers' must be an object")

    except json.JSONDecodeError as e:
        errors.append(f"{pack_dir}: Invalid JSON in .mcp.json: {e}")
    except Exception as e:
        errors.append(f"{pack_dir}: Error reading .mcp.json: {e}")

    return errors


def validate_yaml_frontmatter(file_path: Path) -> Tuple[bool, str]:
    """
    Validate YAML frontmatter in a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match YAML frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return False, "Missing YAML frontmatter (should start with --- and end with ---)"

        frontmatter_text = match.group(1)
        data = yaml.safe_load(frontmatter_text)

        if data is None:
            return False, "Empty YAML frontmatter"

        # Check required fields
        if 'name' not in data:
            return False, "Missing required field 'name' in frontmatter"
        if 'description' not in data:
            return False, "Missing required field 'description' in frontmatter"

        return True, ""

    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"


def validate_skills(pack_dir: str) -> List[str]:
    """
    Validate skills in a pack.

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    skills_dir = Path(pack_dir) / 'skills'

    if not skills_dir.exists():
        # Skills directory is optional
        return errors

    # Find all SKILL.md files
    for skill_file in skills_dir.glob('*/SKILL.md'):
        is_valid, error_msg = validate_yaml_frontmatter(skill_file)
        if not is_valid:
            errors.append(f"{skill_file}: {error_msg}")

    return errors


def validate_agents(pack_dir: str) -> List[str]:
    """
    Validate agents in a pack.

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    agents_dir = Path(pack_dir) / 'agents'

    if not agents_dir.exists():
        # Agents directory is optional
        return errors

    # Find all .md files
    for agent_file in agents_dir.glob('*.md'):
        is_valid, error_msg = validate_yaml_frontmatter(agent_file)
        if not is_valid:
            errors.append(f"{agent_file}: {error_msg}")

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

    # Validate .mcp.json
    errors.extend(validate_mcp_json(pack_dir))

    # Validate skills
    errors.extend(validate_skills(pack_dir))

    # Validate agents
    errors.extend(validate_agents(pack_dir))

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

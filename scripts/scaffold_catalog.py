#!/usr/bin/env python3
"""Print a draft skill roster and marketplace hints for create-collection (stdout only)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pack_registry
from generate_pack_data import parse_yaml_frontmatter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pack", help="Pack directory name")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    pack = args.pack
    if not (root / pack).is_dir():
        print(f"No such pack: {pack}", file=sys.stderr)
        return 1
    mod = pack_registry.load_marketplace_module_by_path(pack, root)
    title = pack_registry.load_plugin_title(pack, root) or pack
    print(f"# Draft scaffold for `{pack}`\n")
    print(f"**Display title:** {title}")
    if mod:
        print(f"**Marketplace name:** {mod.get('name')}")
        print(f"**Version:** {mod.get('version')}")
        print(f"**Description:** {mod.get('description')}")
        print(f"**Tags:** {mod.get('tags')}")
    print("\n## skills/*/SKILL.md\n")
    skills_dir = root / pack / "skills"
    if not skills_dir.is_dir():
        print("(no skills directory)")
        return 0
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        fm = parse_yaml_frontmatter(skill_md)
        name = fm.get("name", skill_md.parent.name)
        desc = fm.get("description", "")
        if isinstance(desc, str):
            desc = " ".join(desc.split())[:400]
        print(f"- **{name}** (`{skill_md.parent.name}/`)\n  {desc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

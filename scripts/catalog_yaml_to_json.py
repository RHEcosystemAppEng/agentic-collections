#!/usr/bin/env python3
"""Write deterministic .catalog/collection.json from .catalog/collection.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

import collection_validate_lib as cvl
import pack_registry


def mirror_pack(pack_dir: str, root: Path, dry_run: bool = False) -> None:
    ypath = root / pack_dir / ".catalog" / "collection.yaml"
    jpath = root / pack_dir / ".catalog" / "collection.json"
    if not ypath.exists():
        raise FileNotFoundError(f"Missing {ypath}")
    with open(ypath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    text = cvl.collection_json_dumps(data)
    if dry_run:
        print(text, end="")
        return
    jpath.parent.mkdir(parents=True, exist_ok=True)
    jpath.write_text(text, encoding="utf-8")
    print(f"Wrote {jpath.relative_to(root)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", help="Single pack directory name")
    parser.add_argument("--all", action="store_true", help="All union registry packs with collection.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        if args.all:
            for p in pack_registry.get_union_pack_dirs(root):
                if (root / p / ".catalog" / "collection.yaml").exists():
                    mirror_pack(p, root, dry_run=args.dry_run)
        elif args.pack:
            mirror_pack(args.pack, root, dry_run=args.dry_run)
        else:
            parser.error("Provide --pack NAME or --all")
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

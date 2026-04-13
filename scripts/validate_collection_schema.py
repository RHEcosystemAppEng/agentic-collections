#!/usr/bin/env python3
"""Iteration 3: validate .catalog/collection.yaml (presence, schema, roster, *_file, YAML banner)."""

import sys
from pathlib import Path

import collection_validate_lib as cvl


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errs = cvl.validate_all_iteration3(root, check_banner=True)
    if errs:
        print("Collection schema validation failed:", file=sys.stderr)
        for e in errs:
            print(f"  • {e}", file=sys.stderr)
        return 1
    print("✓ Collection schema validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Full collection compliance (Iteration 3 + semantic rules + collection.json mirror drift)."""

import sys
from pathlib import Path

import collection_validate_lib as cvl


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    errs = cvl.validate_all_iteration5(root)
    if errs:
        print("Collection compliance failed:", file=sys.stderr)
        for e in errs:
            print(f"  • {e}", file=sys.stderr)
        return 1
    print("✓ Collection compliance passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

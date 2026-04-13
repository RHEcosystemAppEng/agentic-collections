"""
Resolve <pack>/.catalog/collection.yaml for static site embedding (fragment files inlined).

Used by build_website.py only. Does not replace collection.yaml on disk.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import collection_validate_lib as cvl


def _strip_leading_catalog_comment(markdown: str) -> str:
    """Remove leading <!-- ... --> provenance block from fragment files for display."""
    s = markdown.lstrip("\ufeff")
    if not s.lstrip().startswith("<!--"):
        return markdown
    m = re.match(r"^\s*<!--.*?-->\s*", s, flags=re.DOTALL)
    if not m:
        return markdown
    return s[m.end() :].lstrip("\n")


def _read_fragment(pack_dir: str, ref: str, root: Path) -> Tuple[Optional[str], Optional[str]]:
    rel = cvl.catalog_fragment_rel_path(ref) or cvl.deploy_and_use_external_rel_path(ref)
    if not rel:
        return None, f"invalid fragment ref {ref!r}"
    catalog_dir = (root / pack_dir / ".catalog").resolve()
    target = (catalog_dir / rel).resolve()
    try:
        target.relative_to(catalog_dir)
    except ValueError:
        return None, f"fragment escapes .catalog: {ref!r}"
    if not target.is_file():
        return None, f"missing fragment {rel}"
    raw = target.read_text(encoding="utf-8")
    return _strip_leading_catalog_comment(raw), None


def bundle_catalog_for_site(pack_dir: str, root: Path) -> Tuple[Optional[Dict[str, Any]], list[str]]:
    """
    Load catalog YAML and inline all #fragment file references for JSON export.

    Returns:
        (dict suitable for docs/data.json, list of warning strings)
    """
    data, errs = cvl.read_yaml_catalog(pack_dir, root)
    if errs or data is None:
        return None, errs
    out: Dict[str, Any] = copy.deepcopy(data)
    warnings: list[str] = []

    for key in list(out.keys()):
        if not (isinstance(key, str) and key.endswith("_file")):
            continue
        val = out.get(key)
        if not isinstance(val, str) or not val.strip():
            del out[key]
            continue
        text, err = _read_fragment(pack_dir, val, root)
        if err:
            warnings.append(f"{pack_dir}: {key}: {err}")
            del out[key]
            continue
        base = key[: -len("_file")]
        out[base] = text
        del out[key]

    dau = out.get("deploy_and_use")
    if isinstance(dau, str) and cvl.deploy_and_use_external_rel_path(dau):
        text, err = _read_fragment(pack_dir, dau, root)
        if err:
            warnings.append(f"{pack_dir}: deploy_and_use: {err}")
        else:
            out["deploy_and_use"] = text

    return out, warnings

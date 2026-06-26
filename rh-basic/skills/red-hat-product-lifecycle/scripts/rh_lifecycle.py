#!/usr/bin/env python3
"""
Red Hat product lifecycle CLI.
Returns lifecycle phase dates for a given Red Hat product as JSON.
"""
import argparse
import json
import re
import sys
import urllib.request
from difflib import get_close_matches

API_URL = "https://access.redhat.com/product-life-cycles/api/v1/products"


def fetch_products():
    req = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "rh-lifecycle-cli/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["data"]


def parse_input(product_input):
    """Split 'Product Name X.Y' into (name, version) where version is trailing digits/dots."""
    parts = product_input.rsplit(" ", 1)
    if len(parts) == 2 and re.fullmatch(r"\d[\d.]*", parts[1]):
        return parts[0].strip(), parts[1]
    return product_input.strip(), None


def find_product(products, name):
    names_lower = {p["name"].lower(): p for p in products}
    needle = name.lower()
    matches = get_close_matches(needle, names_lower.keys(), n=5, cutoff=0.5)
    if not matches:
        return None, []
    best = names_lower[matches[0]]
    suggestions = [names_lower[m]["name"] for m in matches[1:]]
    return best, suggestions


def find_version(product, version):
    versions = product.get("versions", [])
    if version is None:
        return versions[0] if versions else None
    for v in versions:
        if v["name"] == version:
            return v
    # prefix fallback: "4.2" matches "4.20" is wrong; only allow exact or major match
    for v in versions:
        if v["name"].startswith(version + ".") or version.startswith(v["name"] + "."):
            return v
    return None


def format_date(value, fmt):
    if value is None or value in ("N/A", "Ongoing", ""):
        return value
    if fmt == "date" and isinstance(value, str) and "T" in value:
        return value[:10]
    return value


def build_output(product, version_data):
    phases = {}
    for phase in version_data.get("phases", []):
        phases[phase["name"]] = {
            "start": format_date(phase.get("start_date"), phase.get("start_date_format")),
            "end": format_date(phase.get("end_date"), phase.get("end_date_format")),
        }
    return {
        "product": product["name"],
        "version": version_data["name"],
        "current_phase": version_data.get("type"),
        "phases": phases,
    }


def error_exit(msg, **extra):
    payload = {"error": msg, **extra}
    print(json.dumps(payload, indent=2), file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Get lifecycle dates for a Red Hat product.",
        epilog=(
            "Examples:\n"
            "  %(prog)s 'Red Hat Enterprise Linux 9'\n"
            "  %(prog)s 'Red Hat OpenShift Container Platform 4.20'\n"
            "  %(prog)s 'Kubernetes NMState Operator 4.20'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "product",
        nargs="+",
        help='Product name with version, e.g. "Red Hat Enterprise Linux 9"',
    )
    args = parser.parse_args()

    product_input = " ".join(args.product)
    name, version = parse_input(product_input)

    try:
        products = fetch_products()
    except Exception as exc:
        error_exit(f"Failed to fetch lifecycle data: {exc}")

    product, suggestions = find_product(products, name)
    if product is None:
        error_exit(f"Product not found: {name!r}")

    version_data = find_version(product, version)
    if version_data is None:
        available = [v["name"] for v in product.get("versions", [])]
        error_exit(
            f"Version {version!r} not found for {product['name']!r}",
            available_versions=available,
        )

    result = build_output(product, version_data)
    # Only hint at alternatives when the match wasn't exact
    if suggestions and product["name"].lower() != name.lower():
        result["_note"] = f"Matched {product['name']!r}; other close matches: {suggestions}"

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

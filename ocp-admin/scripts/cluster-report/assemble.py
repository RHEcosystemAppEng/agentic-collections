#!/usr/bin/env python3

import json
import os
import subprocess
import sys

DATA_FIELDS = ("nodes_top", "nodes_list", "projects", "namespaces", "pods")


def unwrap_persisted_output(raw_content):
    try:
        data = json.loads(raw_content)
    except (json.JSONDecodeError, ValueError):
        return raw_content

    if isinstance(data, list) and len(data) > 0:
        if all(isinstance(item, dict) and "type" in item for item in data):
            texts = []
            for item in data:
                if item.get("type") == "text" and "text" in item:
                    texts.append(item["text"])
            if texts:
                return "\n".join(texts)
            return None

    return data


def resolve_file_ref(file_path):
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"

    try:
        with open(file_path, "r") as f:
            raw = f.read()
    except PermissionError:
        return None, f"Permission denied reading: {file_path}"
    except OSError as e:
        return None, f"Error reading {file_path}: {e}"

    if not raw.strip():
        return None, f"Empty file: {file_path}"

    content = unwrap_persisted_output(raw)

    if content is None:
        return None, f"No text content in envelope: {file_path}"

    return content, None


def resolve_cluster(cluster_data):
    errors = list(cluster_data.get("errors", []))

    for field in DATA_FIELDS:
        value = cluster_data.get(field)
        if isinstance(value, dict) and "$file" in value:
            file_path = value["$file"]
            content, error = resolve_file_ref(file_path)
            if error:
                cluster_data[field] = None
                errors.append(error)
            else:
                cluster_data[field] = content

    cluster_data["errors"] = errors
    return cluster_data


def main():
    aggregate_mode = "--aggregate" in sys.argv

    try:
        raw = sys.stdin.read()
    except Exception as e:
        json.dump({"error": f"Failed to read stdin: {e}"}, sys.stdout, indent=2)
        sys.exit(1)

    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as e:
        json.dump({"error": f"Invalid manifest JSON: {e}"}, sys.stdout, indent=2)
        sys.exit(1)

    clusters = manifest.get("clusters", {})
    for cluster_data in clusters.values():
        resolve_cluster(cluster_data)

    resolved_json = json.dumps(manifest, indent=2)

    if aggregate_mode:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        aggregate_script = os.path.join(script_dir, "aggregate.py")
        proc = subprocess.run(
            [sys.executable, aggregate_script],
            input=resolved_json,
            capture_output=True,
            text=True,
        )
        sys.stdout.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        sys.exit(proc.returncode)
    else:
        sys.stdout.write(resolved_json)


if __name__ == "__main__":
    main()

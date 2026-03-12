#!/usr/bin/env python3
"""Multi-cluster kubeconfig builder for cluster-report.

Two subcommands:
    setup   Apply RBAC and extract SA tokens for clusters you're logged into
    build   Build a merged kubeconfig from a clusters inventory file

Usage:
    python3 build-kubeconfig.py setup [--all-contexts] [--contexts ctx1,ctx2]
                                      [--output-inventory <path>]

    python3 build-kubeconfig.py build --clusters <clusters.json>
                                      [--output <path>] [--verify]

Requires: oc or kubectl, python3 (stdlib only)
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RBAC_MANIFEST = SCRIPT_DIR / "cluster-reporter-rbac.yaml"

SA_NAMESPACE = "cluster-reporter-system"
SECRET_NAME = "cluster-reporter-token"

DEFAULT_INVENTORY = Path.home() / ".ocp-clusters" / "clusters.json"
DEFAULT_OUTPUT = Path("/tmp/cluster-report-kubeconfig")


def find_kube_cmd():
    """Detect oc (preferred) or kubectl in PATH."""
    if shutil.which("oc"):
        return "oc"
    if shutil.which("kubectl"):
        print("WARNING: 'oc' not found – falling back to 'kubectl'. "
              "Install the OpenShift CLI (oc) for full compatibility: "
              "https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/",
              file=sys.stderr)
        return "kubectl"
    print('{"error": "Neither oc nor kubectl found in PATH. '
          'Install oc: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/"}',
          file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Setup mode
# ---------------------------------------------------------------------------

def run_setup(args):
    kube_cmd = find_kube_cmd()
    inventory_file = Path(args.output_inventory)

    if not args.skip_rbac and not RBAC_MANIFEST.is_file():
        print(f"Error: RBAC manifest not found at {RBAC_MANIFEST}", file=sys.stderr)
        sys.exit(1)

    try:
        all_ctx = subprocess.check_output(
            [kube_cmd, "config", "get-contexts", "-o", "name"],
            text=True, stderr=subprocess.DEVNULL
        ).strip().splitlines()
    except subprocess.CalledProcessError:
        all_ctx = []

    if not all_ctx:
        print('{"error": "No kubeconfig contexts found. Log in to at least one cluster first."}',
              file=sys.stderr)
        sys.exit(1)

    if args.contexts:
        contexts = args.contexts.split(",")
        unknown = [c for c in contexts if c not in all_ctx]
        if unknown:
            print(f"Error: unknown context(s): {', '.join(unknown)}", file=sys.stderr)
            print(f"Available: {', '.join(all_ctx)}", file=sys.stderr)
            sys.exit(1)
    elif args.all_contexts:
        contexts = all_ctx
    else:
        print("Available contexts:")
        for i, ctx in enumerate(all_ctx, 1):
            print(f"  {i}. {ctx}")
        print()
        print("Run with --all-contexts to setup all, or --contexts ctx1,ctx2 to select specific ones.")
        sys.exit(0)

    print(f"Pre-flight: checking {len(contexts)} cluster(s)...\n")
    reachable = {}
    for ctx in contexts:
        server = _get_server_url(kube_cmd, ctx)
        if not server:
            print(f"  {ctx}: SKIP (no server URL in kubeconfig)")
            continue
        try:
            subprocess.run(
                [kube_cmd, "cluster-info", "--context", ctx],
                capture_output=True, text=True, timeout=15, check=True
            )
            reachable[ctx] = server
            print(f"  {ctx}: reachable ({server})")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print(f"  {ctx}: SKIP (unreachable – try '{kube_cmd} login {server}' first)")
            continue

        if not args.skip_rbac:
            try:
                result = subprocess.run(
                    [kube_cmd, "auth", "can-i", "create", "clusterroles",
                     "--context", ctx],
                    capture_output=True, text=True, timeout=10
                )
                if result.stdout.strip().lower() != "yes":
                    print(f"  {ctx}: SKIP (insufficient permissions – "
                          f"cluster-admin required for RBAC setup, "
                          f"or use --skip-rbac if RBAC is already applied)")
                    del reachable[ctx]
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                print(f"  {ctx}: SKIP (could not verify permissions)")
                del reachable[ctx]

    if not reachable:
        print("\nError: no eligible clusters found. Nothing to do.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{len(reachable)}/{len(contexts)} cluster(s) ready. "
          f"Proceeding with setup...\n")

    inventory_file.parent.mkdir(parents=True, exist_ok=True)

    existing_by_name = {}
    if inventory_file.is_file():
        try:
            with open(inventory_file) as f:
                existing_by_name = {c["name"]: c for c in json.load(f).get("clusters", [])}
        except (json.JSONDecodeError, KeyError):
            pass

    results = {"setup": [], "errors": []}

    for ctx, server in reachable.items():
        print(f"--- {ctx} ---")
        print(f"  Server: {server}")

        if args.skip_rbac:
            print("  Skipping RBAC apply (--skip-rbac)")
        else:
            print("  Applying RBAC...")
            try:
                subprocess.run(
                    [kube_cmd, "apply", "-f", str(RBAC_MANIFEST), "--context", ctx],
                    capture_output=True, text=True, timeout=30, check=True
                )
            except subprocess.CalledProcessError as e:
                results["errors"].append(f"{ctx}: RBAC apply failed: {e.stderr.strip()}")
                print(f"  FAIL: RBAC apply failed: {e.stderr.strip()}")
                continue

        print("  Waiting for token...")
        token = _wait_for_token(kube_cmd, ctx)
        if not token:
            results["errors"].append(f"{ctx}: token not populated after 15s")
            print("  FAIL: token Secret not populated")
            continue

        try:
            decoded_token = base64.b64decode(token).decode("utf-8")
        except Exception:
            decoded_token = token

        existing_by_name[ctx] = {"name": ctx, "api_url": server, "token": decoded_token}
        results["setup"].append(ctx)
        print("  OK: token extracted")

    with open(inventory_file, "w") as f:
        json.dump({"clusters": list(existing_by_name.values())}, f, indent=2)
    os.chmod(inventory_file, 0o600)

    print()
    print("=" * 50)
    print(f"Setup complete: {len(results['setup'])} succeeded, {len(results['errors'])} failed")
    if results["errors"]:
        print("Errors:")
        for e in results["errors"]:
            print(f"  - {e}")
    print(f"Inventory written to: {inventory_file}")
    print()
    print("Next step:")
    print(f"  python3 {__file__} build --clusters {inventory_file} --verify")

    json.dump(results, sys.stderr, indent=2)


def _get_server_url(kube_cmd, ctx):
    """Resolve the API server URL for a kubeconfig context."""
    try:
        server = subprocess.check_output(
            [kube_cmd, "config", "view", "-o",
             f'jsonpath={{.clusters[?(@.name=="{ctx}")].cluster.server}}'],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if server:
            return server

        cluster_ref = subprocess.check_output(
            [kube_cmd, "config", "view", "-o",
             f'jsonpath={{.contexts[?(@.name=="{ctx}")].context.cluster}}'],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if cluster_ref:
            return subprocess.check_output(
                [kube_cmd, "config", "view", "-o",
                 f'jsonpath={{.clusters[?(@.name=="{cluster_ref}")].cluster.server}}'],
                text=True, stderr=subprocess.DEVNULL
            ).strip() or None
    except subprocess.CalledProcessError:
        pass
    return None


def _wait_for_token(kube_cmd, ctx, timeout_secs=15):
    """Poll for the SA token Secret to be populated."""
    for _ in range(timeout_secs):
        try:
            token = subprocess.check_output(
                [kube_cmd, "get", "secret", SECRET_NAME,
                 "-n", SA_NAMESPACE, "--context", ctx,
                 "-o", "jsonpath={.data.token}"],
                text=True, stderr=subprocess.DEVNULL, timeout=10
            ).strip()
            if token:
                return token
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        time.sleep(1)
    return None


# ---------------------------------------------------------------------------
# Build mode
# ---------------------------------------------------------------------------

def run_build(args):
    kube_cmd = find_kube_cmd()
    clusters_file = Path(args.clusters)
    output_file = Path(args.output)

    if not clusters_file.is_file():
        print(f'{{"error": "Clusters file not found: {clusters_file}"}}', file=sys.stderr)
        sys.exit(1)

    with open(clusters_file) as f:
        config = json.load(f)

    clusters = config.get("clusters", [])
    if not clusters:
        print('{"error": "No clusters in inventory file"}', file=sys.stderr)
        sys.exit(1)

    output_file.unlink(missing_ok=True)
    output_file.touch(mode=0o600)

    env = {**os.environ, "KUBECONFIG": str(output_file)}
    errors = []
    success = 0

    for c in clusters:
        name = c.get("name", "")
        api_url = c.get("api_url", "")

        if not name or not api_url:
            errors.append(f"Entry missing name or api_url: {c}")
            continue

        token = _resolve_token(c, errors)
        if token is None:
            continue

        ca_args = (["--certificate-authority", c["ca_cert"]]
                   if c.get("ca_cert")
                   else ["--insecure-skip-tls-verify=true"])
        try:
            subprocess.run(
                [kube_cmd, "config", "set-cluster", name, "--server", api_url] + ca_args,
                check=True, capture_output=True, env=env
            )
        except subprocess.CalledProcessError as e:
            errors.append(f"{name}: set-cluster failed: {e.stderr.decode().strip()}")
            continue

        try:
            subprocess.run(
                [kube_cmd, "config", "set-credentials", f"{name}-reporter", "--token", token],
                check=True, capture_output=True, env=env
            )
        except subprocess.CalledProcessError as e:
            errors.append(f"{name}: set-credentials failed: {e.stderr.decode().strip()}")
            continue

        try:
            subprocess.run(
                [kube_cmd, "config", "set-context", name,
                 "--cluster", name, "--user", f"{name}-reporter"],
                check=True, capture_output=True, env=env
            )
        except subprocess.CalledProcessError as e:
            errors.append(f"{name}: set-context failed: {e.stderr.decode().strip()}")
            continue

        if success == 0:
            subprocess.run(
                [kube_cmd, "config", "use-context", name],
                check=False, capture_output=True, env=env
            )

        success += 1

    verify_results = {}
    if args.verify and success > 0:
        print(f"Verifying {success} context(s)...")
        for c in clusters:
            name = c.get("name", "")
            if not name:
                continue
            try:
                subprocess.run(
                    [kube_cmd, "get", "nodes", "--context", name, "-o", "name", "--no-headers"],
                    capture_output=True, text=True, timeout=15, check=True, env=env
                )
                verify_results[name] = "ok"
                print(f"  {name}: OK")
            except subprocess.TimeoutExpired:
                verify_results[name] = "timeout"
                errors.append(f"{name}: verification timed out")
                print(f"  {name}: TIMEOUT")
            except subprocess.CalledProcessError:
                verify_results[name] = "failed"
                errors.append(f"{name}: verification failed (likely expired token)")
                print(f"  {name}: FAILED (re-run setup for this cluster)")

    result = {
        "clusters_configured": success,
        "clusters_failed": len(errors),
        "kubeconfig": str(output_file),
        "errors": errors,
    }
    if args.verify:
        result["verification"] = verify_results

    print()
    print(json.dumps(result, indent=2))
    print()
    print(f"Kubeconfig written to: {output_file}")
    print()
    print("To use with cluster-report:")
    print(f"  export KUBECONFIG={output_file}")

    if success == 0:
        sys.exit(1)


def _resolve_token(cluster_entry, errors):
    """Resolve token from inline value or environment variable. Returns None on failure."""
    name = cluster_entry.get("name", "<unknown>")
    if "token_env" in cluster_entry:
        token = os.environ.get(cluster_entry["token_env"])
        if not token:
            errors.append(f"{name}: env var {cluster_entry['token_env']} not set")
            return None
        return token
    if "token" in cluster_entry:
        return cluster_entry["token"]
    errors.append(f"{name}: no token or token_env specified")
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Multi-cluster kubeconfig builder for cluster-report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- setup --
    setup_parser = subparsers.add_parser(
        "setup",
        help="Apply RBAC to clusters you're logged into, extract SA tokens, "
             "and write a clusters inventory file.",
    )
    setup_parser.add_argument(
        "--all-contexts", action="store_true",
        help="Setup all kubeconfig contexts without prompting.",
    )
    setup_parser.add_argument(
        "--contexts", type=str, default=None,
        help="Comma-separated list of contexts to setup.",
    )
    setup_parser.add_argument(
        "--skip-rbac", action="store_true",
        help="Skip RBAC apply and only extract tokens (use when RBAC is already configured).",
    )
    setup_parser.add_argument(
        "--output-inventory", type=str, default=str(DEFAULT_INVENTORY),
        help=f"Path for the clusters inventory file (default: {DEFAULT_INVENTORY}).",
    )

    # -- build --
    build_parser = subparsers.add_parser(
        "build",
        help="Read a clusters inventory file and build a merged kubeconfig.",
    )
    build_parser.add_argument(
        "--clusters", type=str, required=True,
        help="Path to the clusters inventory JSON file.",
    )
    build_parser.add_argument(
        "--output", type=str, default=str(DEFAULT_OUTPUT),
        help=f"Path for the generated kubeconfig (default: {DEFAULT_OUTPUT}).",
    )
    build_parser.add_argument(
        "--verify", action="store_true",
        help="Test each context after building the kubeconfig.",
    )

    args = parser.parse_args()

    if args.command == "setup":
        run_setup(args)
    elif args.command == "build":
        run_build(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# build-kubeconfig.sh — Multi-cluster kubeconfig builder for cluster-report
#
# Two modes:
#   --setup   Apply RBAC and extract SA tokens for clusters you're logged into
#   --build   Build a merged kubeconfig from a clusters inventory file
#
# Usage:
#   bash build-kubeconfig.sh --setup [--all-contexts] [--contexts ctx1,ctx2]
#                            [--output-inventory <path>]
#
#   bash build-kubeconfig.sh --build --clusters <clusters.json>
#                            [--output <path>] [--verify]
#
# Requires: oc or kubectl, python3 (stdlib only)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RBAC_MANIFEST="${SCRIPT_DIR}/cluster-reporter-rbac.yaml"

MODE=""
CLUSTERS_FILE=""
OUTPUT_FILE="/tmp/cluster-report-kubeconfig"
INVENTORY_FILE="${HOME}/.ocp-clusters/clusters.json"
VERIFY=false
ALL_CONTEXTS=false
SELECTED_CONTEXTS=""

# --- Argument parsing ---

usage() {
  cat <<'USAGE'
Usage:
  build-kubeconfig.sh --setup [--all-contexts] [--contexts ctx1,ctx2]
                      [--output-inventory <path>]

  build-kubeconfig.sh --build --clusters <clusters.json>
                      [--output <path>] [--verify]

Modes:
  --setup             Apply RBAC to clusters you're logged into, extract SA tokens,
                      and write a clusters inventory file.
  --build             Read a clusters inventory file and build a merged kubeconfig.

Setup options:
  --all-contexts      Setup all kubeconfig contexts without prompting.
  --contexts c1,c2    Setup only the specified contexts (comma-separated).
  --output-inventory  Path for the clusters inventory file.
                      Default: ~/.ocp-clusters/clusters.json

Build options:
  --clusters <path>   Path to the clusters inventory JSON file (required).
  --output <path>     Path for the generated kubeconfig.
                      Default: /tmp/cluster-report-kubeconfig
  --verify            Test each context after building the kubeconfig.
USAGE
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --setup)            MODE="setup"; shift ;;
    --build)            MODE="build"; shift ;;
    --clusters)         CLUSTERS_FILE="$2"; shift 2 ;;
    --output)           OUTPUT_FILE="$2"; shift 2 ;;
    --output-inventory) INVENTORY_FILE="$2"; shift 2 ;;
    --verify)           VERIFY=true; shift ;;
    --all-contexts)     ALL_CONTEXTS=true; shift ;;
    --contexts)         SELECTED_CONTEXTS="$2"; shift 2 ;;
    -h|--help)          usage ;;
    *)                  echo "Unknown flag: $1" >&2; usage ;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo "Error: specify --setup or --build" >&2
  usage
fi

# --- Helpers ---

KUBE_CMD=""
if command -v oc &>/dev/null; then
  KUBE_CMD="oc"
elif command -v kubectl &>/dev/null; then
  KUBE_CMD="kubectl"
else
  echo '{"error": "Neither oc nor kubectl found in PATH"}' >&2
  exit 1
fi

SA_NAMESPACE="cluster-reporter-system"
SA_NAME="cluster-reporter"
SECRET_NAME="cluster-reporter-token"

# --- Setup mode ---

run_setup() {
  if [[ ! -f "$RBAC_MANIFEST" ]]; then
    echo "Error: RBAC manifest not found at ${RBAC_MANIFEST}" >&2
    exit 1
  fi

  mapfile -t ALL_CTX < <($KUBE_CMD config get-contexts -o name 2>/dev/null)

  if [[ ${#ALL_CTX[@]} -eq 0 ]]; then
    echo '{"error": "No kubeconfig contexts found. Log in to at least one cluster first."}' >&2
    exit 1
  fi

  CONTEXTS_TO_PROCESS=()

  if [[ -n "$SELECTED_CONTEXTS" ]]; then
    IFS=',' read -ra CONTEXTS_TO_PROCESS <<< "$SELECTED_CONTEXTS"
  elif [[ "$ALL_CONTEXTS" == "true" ]]; then
    CONTEXTS_TO_PROCESS=("${ALL_CTX[@]}")
  else
    echo "Available contexts:"
    for i in "${!ALL_CTX[@]}"; do
      echo "  $((i+1)). ${ALL_CTX[$i]}"
    done
    echo ""
    echo "Run with --all-contexts to setup all, or --contexts ctx1,ctx2 to select specific ones."
    exit 0
  fi

  echo "Setting up ${#CONTEXTS_TO_PROCESS[@]} cluster(s)..."
  echo ""

  INVENTORY_DIR="$(dirname "$INVENTORY_FILE")"
  mkdir -p "$INVENTORY_DIR"

  EXISTING_CLUSTERS="[]"
  if [[ -f "$INVENTORY_FILE" ]]; then
    EXISTING_CLUSTERS=$(python3 -c "
import json, sys
with open('${INVENTORY_FILE}') as f:
    data = json.load(f)
json.dump(data.get('clusters', []), sys.stdout)
" 2>/dev/null || echo "[]")
  fi

  python3 - "$KUBE_CMD" "$RBAC_MANIFEST" "$SA_NAMESPACE" "$SECRET_NAME" "$INVENTORY_FILE" "$EXISTING_CLUSTERS" "${CONTEXTS_TO_PROCESS[@]}" <<'SETUP_SCRIPT'
import subprocess, sys, json, time, os

kube_cmd = sys.argv[1]
rbac_manifest = sys.argv[2]
sa_namespace = sys.argv[3]
secret_name = sys.argv[4]
inventory_file = sys.argv[5]
existing_clusters = json.loads(sys.argv[6])
contexts = sys.argv[7:]

# Index existing clusters by name for dedup
existing_by_name = {c["name"]: c for c in existing_clusters}

results = {"setup": [], "errors": []}

for ctx in contexts:
    print(f"--- {ctx} ---")

    # Get server URL for this context
    try:
        server = subprocess.check_output(
            [kube_cmd, "config", "view", "-o",
             f"jsonpath={{.clusters[?(@.name==\"{ctx}\")].cluster.server}}"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()

        if not server:
            # Try matching by context's cluster reference
            cluster_ref = subprocess.check_output(
                [kube_cmd, "config", "view", "-o",
                 f"jsonpath={{.contexts[?(@.name==\"{ctx}\")].context.cluster}}"],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            if cluster_ref:
                server = subprocess.check_output(
                    [kube_cmd, "config", "view", "-o",
                     f"jsonpath={{.clusters[?(@.name==\"{cluster_ref}\")].cluster.server}}"],
                    text=True, stderr=subprocess.DEVNULL
                ).strip()
    except subprocess.CalledProcessError:
        results["errors"].append(f"{ctx}: failed to get server URL")
        print(f"  SKIP: cannot determine server URL")
        continue

    if not server:
        results["errors"].append(f"{ctx}: no server URL found in kubeconfig")
        print(f"  SKIP: no server URL")
        continue

    # Check connectivity
    try:
        subprocess.run(
            [kube_cmd, "cluster-info", "--context", ctx],
            capture_output=True, text=True, timeout=15, check=True
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        results["errors"].append(f"{ctx}: cluster unreachable or auth expired")
        print(f"  SKIP: cluster unreachable (try 'oc login {server}' first)")
        continue

    print(f"  Server: {server}")

    # Apply RBAC manifest
    print(f"  Applying RBAC...")
    try:
        subprocess.run(
            [kube_cmd, "apply", "-f", rbac_manifest, "--context", ctx],
            capture_output=True, text=True, timeout=30, check=True
        )
    except subprocess.CalledProcessError as e:
        results["errors"].append(f"{ctx}: RBAC apply failed: {e.stderr.strip()}")
        print(f"  FAIL: RBAC apply failed: {e.stderr.strip()}")
        continue

    # Wait for token to be populated (up to 15 seconds)
    print(f"  Waiting for token...")
    token = ""
    for attempt in range(15):
        try:
            token = subprocess.check_output(
                [kube_cmd, "get", "secret", secret_name,
                 "-n", sa_namespace, "--context", ctx,
                 "-o", "jsonpath={.data.token}"],
                text=True, stderr=subprocess.DEVNULL, timeout=10
            ).strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

        if token:
            break
        time.sleep(1)

    if not token:
        results["errors"].append(f"{ctx}: token not populated after 15s")
        print(f"  FAIL: token Secret not populated")
        continue

    # Decode base64 token
    import base64
    try:
        decoded_token = base64.b64decode(token).decode("utf-8")
    except Exception:
        decoded_token = token  # might already be decoded

    # Add to inventory
    entry = {
        "name": ctx,
        "api_url": server,
        "token": decoded_token
    }
    existing_by_name[ctx] = entry
    results["setup"].append(ctx)
    print(f"  OK: token extracted")

# Write inventory
all_clusters = list(existing_by_name.values())
inventory = {"clusters": all_clusters}

with open(inventory_file, "w") as f:
    json.dump(inventory, f, indent=2)
os.chmod(inventory_file, 0o600)

print("")
print("=" * 50)
print(f"Setup complete: {len(results['setup'])} succeeded, {len(results['errors'])} failed")
if results["errors"]:
    print(f"Errors:")
    for e in results["errors"]:
        print(f"  - {e}")
print(f"Inventory written to: {inventory_file}")
print("")
print("Next step:")
print(f"  bash build-kubeconfig.sh --build --clusters {inventory_file} --verify")

# Output JSON summary to stderr for scripting
json.dump(results, sys.stderr, indent=2)
SETUP_SCRIPT
}

# --- Build mode ---

run_build() {
  if [[ -z "$CLUSTERS_FILE" ]]; then
    echo "Error: --clusters <path> is required for --build mode" >&2
    usage
  fi

  if [[ ! -f "$CLUSTERS_FILE" ]]; then
    echo "{\"error\": \"Clusters file not found: ${CLUSTERS_FILE}\"}" >&2
    exit 1
  fi

  rm -f "$OUTPUT_FILE"
  touch "$OUTPUT_FILE"
  chmod 600 "$OUTPUT_FILE"

  python3 - "$KUBE_CMD" "$CLUSTERS_FILE" "$OUTPUT_FILE" "$VERIFY" <<'BUILD_SCRIPT'
import json, sys, os, subprocess

kube_cmd = sys.argv[1]
clusters_file = sys.argv[2]
output_file = sys.argv[3]
verify = sys.argv[4] == "True"

with open(clusters_file) as f:
    config = json.load(f)

clusters = config.get("clusters", [])
if not clusters:
    print('{"error": "No clusters in inventory file"}', file=sys.stderr)
    sys.exit(1)

env = {**os.environ, "KUBECONFIG": output_file}
errors = []
success = 0

for c in clusters:
    name = c.get("name", "")
    api_url = c.get("api_url", "")

    if not name or not api_url:
        errors.append(f"Entry missing name or api_url: {c}")
        continue

    # Resolve token
    token = None
    if "token_env" in c:
        token = os.environ.get(c["token_env"])
        if not token:
            errors.append(f"{name}: env var {c['token_env']} not set")
            continue
    elif "token" in c:
        token = c["token"]
    else:
        errors.append(f"{name}: no token or token_env specified")
        continue

    # Set cluster
    ca_args = []
    if "ca_cert" in c and c["ca_cert"]:
        ca_args = ["--certificate-authority", c["ca_cert"]]
    else:
        ca_args = ["--insecure-skip-tls-verify=true"]

    try:
        subprocess.run(
            [kube_cmd, "config", "set-cluster", name,
             "--server", api_url] + ca_args,
            check=True, capture_output=True, env=env
        )
    except subprocess.CalledProcessError as e:
        errors.append(f"{name}: set-cluster failed: {e.stderr.decode().strip()}")
        continue

    # Set credentials
    try:
        subprocess.run(
            [kube_cmd, "config", "set-credentials", f"{name}-reporter",
             "--token", token],
            check=True, capture_output=True, env=env
        )
    except subprocess.CalledProcessError as e:
        errors.append(f"{name}: set-credentials failed: {e.stderr.decode().strip()}")
        continue

    # Set context
    try:
        subprocess.run(
            [kube_cmd, "config", "set-context", name,
             "--cluster", name,
             "--user", f"{name}-reporter"],
            check=True, capture_output=True, env=env
        )
    except subprocess.CalledProcessError as e:
        errors.append(f"{name}: set-context failed: {e.stderr.decode().strip()}")
        continue

    # Set first successful context as current-context (required by MCP server)
    if success == 0:
        subprocess.run(
            [kube_cmd, "config", "use-context", name],
            check=False, capture_output=True, env=env
        )

    success += 1

# Verify if requested
verify_results = {}
if verify and success > 0:
    print(f"Verifying {success} context(s)...")
    for c in clusters:
        name = c.get("name", "")
        if not name:
            continue
        try:
            subprocess.run(
                [kube_cmd, "cluster-info", "--context", name],
                capture_output=True, text=True, timeout=15, check=True, env=env
            )
            verify_results[name] = "ok"
            print(f"  {name}: OK")
        except subprocess.TimeoutExpired:
            verify_results[name] = "timeout"
            errors.append(f"{name}: verification timed out")
            print(f"  {name}: TIMEOUT")
        except subprocess.CalledProcessError as e:
            verify_results[name] = "failed"
            errors.append(f"{name}: verification failed (likely expired token)")
            print(f"  {name}: FAILED (re-run --setup for this cluster)")

result = {
    "clusters_configured": success,
    "clusters_failed": len(errors),
    "kubeconfig": output_file,
    "errors": errors
}
if verify:
    result["verification"] = verify_results

print("")
print(json.dumps(result, indent=2))

if success == 0:
    sys.exit(1)
BUILD_SCRIPT

  echo ""
  echo "Kubeconfig written to: ${OUTPUT_FILE}"
  echo ""
  echo "To use with cluster-report:"
  echo "  export KUBECONFIG=${OUTPUT_FILE}"
}

# --- Main ---

case "$MODE" in
  setup) run_setup ;;
  build) run_build ;;
  *)     usage ;;
esac

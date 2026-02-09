---
name: validate-environment
description: |
  Check and report the status of required tools and environment for rh-developer skills. Validates tool installation (oc, helm, podman, git, skopeo, etc.), cluster connectivity, and permissions. Use this skill before running other deployment skills to ensure prerequisites are met. Triggers on /validate-environment command or when user asks to check their environment setup.
user_invocable: true
---

# Validate Environment Skill

Check that required tools and environment are properly configured.

## Trigger

- User types `/validate-environment`
- User asks "check my environment", "what tools do I need", "am I ready to deploy"

## Input Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `TARGET` | What to validate: `all`, `openshift`, `rhel`, `containers` | `all` |

## Execution Flow

### Step 1: Determine Validation Scope

Ask user if not clear:

```markdown
## Environment Validation

What would you like to validate?

1. **All** - Check all tools and connections
2. **OpenShift** - Check oc, helm, cluster connectivity
3. **RHEL/Containers** - Check podman, ssh, container tools
4. **Minimal** - Just check core tools (git, curl)

Select an option (1-4):
```

### Step 2: Check Core Tools

Run these checks using Bash:

```bash
# Check each tool and capture version
check_tool() {
  if command -v "$1" &> /dev/null; then
    echo "INSTALLED: $1 ($($1 --version 2>&1 | head -1))"
  else
    echo "MISSING: $1"
  fi
}
```

**Tools to check:**

| Tool | Check Command | Required For |
|------|---------------|--------------|
| `git` | `git --version` | Repository cloning |
| `curl` | `curl --version` | API calls |
| `jq` | `jq --version` | JSON parsing |
| `oc` | `oc version --client` | OpenShift operations |
| `helm` | `helm version --short` | Helm deployments |
| `podman` | `podman --version` | Container builds |
| `docker` | `docker --version` | Container builds (alt) |
| `skopeo` | `skopeo --version` | Image inspection |
| `ssh` | `ssh -V` | RHEL deployments |

### Step 3: Check OpenShift Connectivity (if TARGET includes openshift)

```bash
# Check if logged in
oc whoami

# Check current project
oc project

# Check permissions
oc auth can-i create deployments
oc auth can-i create buildconfigs
oc auth can-i create imagestreams
```

### Step 4: Check Container Runtime (if TARGET includes containers)

```bash
# Check Podman
podman info --format '{{.Host.OS}} {{.Host.Arch}}'

# Or Docker
docker info --format '{{.OSType}} {{.Architecture}}'

# Check if can pull images
podman pull --quiet registry.access.redhat.com/ubi9/ubi-minimal:latest || echo "WARN: Cannot pull images"
```

### Step 5: Generate Report

Present results in this format:

```markdown
## Environment Validation Report

### Core Tools

| Tool | Status | Version |
|------|--------|---------|
| git | OK | 2.43.0 |
| curl | OK | 8.5.0 |
| jq | OK | 1.7.1 |
| oc | OK | 4.14.0 |
| helm | OK | 3.14.0 |
| podman | OK | 4.9.0 |
| skopeo | MISSING | - |
| ssh | OK | OpenSSH_9.6 |

### OpenShift Cluster

| Check | Status | Details |
|-------|--------|---------|
| Logged in | OK | user@cluster.example.com |
| Project | OK | my-project |
| Create Deployments | OK | Allowed |
| Create BuildConfigs | OK | Allowed |
| Create ImageStreams | OK | Allowed |

### Container Runtime

| Check | Status | Details |
|-------|--------|---------|
| Runtime | OK | Podman 4.9.0 |
| Pull images | OK | Can access registries |

---

### Summary

**Ready for:** /detect-project, /s2i-build, /deploy, /helm-deploy, /containerize-deploy

**Missing tools for:**
- /recommend-image (dynamic mode) - Install: `sudo dnf install skopeo`

### Quick Fix Commands

```bash
# Install missing tools
sudo dnf install skopeo
```
```

### Step 6: Offer Next Steps

```markdown
## Next Steps

Your environment is ready for deployment.

Would you like to:
1. Run `/detect-project` to analyze your application
2. Run `/containerize-deploy` for end-to-end deployment
3. See detailed prerequisites documentation

Select an option or describe what you'd like to do:
```

---

## Validation Status Indicators

| Status | Meaning |
|--------|---------|
| OK | Tool installed and working |
| MISSING | Tool not found in PATH |
| ERROR | Tool found but not working |
| WARN | Optional tool missing |
| SKIP | Check skipped (not in scope) |

## Error Handling

### Tool Not Found

```markdown
**Missing: [tool-name]**

This tool is required for [skill-names].

Install with:
- Fedora/RHEL: `sudo dnf install [package]`
- Ubuntu/Debian: `sudo apt install [package]`
- macOS: `brew install [package]`
```

### Cluster Connection Failed

```markdown
**OpenShift cluster not accessible**

You are not logged in to an OpenShift cluster.

To connect:
1. Get login command from OpenShift console
2. Run: `oc login <cluster-url>`

Or set KUBECONFIG:
```bash
export KUBECONFIG=/path/to/kubeconfig
```
```

### Permission Denied

```markdown
**Insufficient permissions in namespace [namespace]**

You need 'edit' or 'admin' role to deploy applications.

Options:
1. Contact cluster admin for permissions
2. Switch to a different namespace: `oc project <namespace>`
3. Create a new project: `oc new-project <name>`
```

---

## Output Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TOOLS_OK` | List of installed tools | `git,curl,oc,helm` |
| `TOOLS_MISSING` | List of missing tools | `skopeo` |
| `CLUSTER_CONNECTED` | OpenShift connectivity | `true` / `false` |
| `READY_FOR_SKILLS` | Skills that can run | `/deploy,/s2i-build` |

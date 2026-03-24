---
title: Prerequisites
category: setup
sources:
  - title: OpenShift CLI (oc) Installation
    url: https://docs.openshift.com/container-platform/latest/cli_reference/openshift_cli/getting-started-cli.html
    sections: Installing the CLI, Logging in
    date_accessed: 2026-02-08
  - title: Helm Installation Guide
    url: https://helm.sh/docs/intro/install/
    sections: From script, From package managers
    date_accessed: 2026-02-08
  - title: Podman Installation
    url: https://podman.io/docs/installation
    sections: Linux, macOS, Windows
    date_accessed: 2026-02-08
  - title: Skopeo Installation
    url: https://github.com/containers/skopeo/blob/main/install.md
    sections: Distribution packages, Building from source
    date_accessed: 2026-02-08
---

# Prerequisites

This document lists all tools required by the rh-developer agentic collection.

## Required Tools by Skill

| Skill | Required Tools | Optional Tools |
|-------|----------------|----------------|
| `/detect-project` | `git` | - |
| `/s2i-build` | `oc` | `git` |
| `/deploy` | `oc` | - |
| `/helm-deploy` | `oc`, `helm` | - |
| `/containerize-deploy` | `oc` | `git`, `helm` |
| `/rhel-deploy` | `ssh`, `podman` or `docker` | `git`, `dnf` |
| `/recommend-image` | - | `skopeo`, `curl`, `jq` |
| `/debug-pod` | `oc` | - |
| `/debug-build` | `oc` | - |
| `/debug-network` | `oc` | - |
| `/debug-rhel` | `ssh` | `ausearch`, `journalctl` |
| `/debug-container` | `podman` or `docker` | - |

## Tool Reference

### OpenShift CLI (oc)

**Required for:** Cluster operations, S2I builds, deployments

```bash
# Check installation
oc version

# Installation
# Download from: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest/
# Or via package manager:
sudo dnf install openshift-clients  # Fedora/RHEL
brew install openshift-cli          # macOS
```

### Helm

**Required for:** Helm chart deployments

```bash
# Check installation
helm version

# Installation
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
# Or via package manager:
sudo dnf install helm    # Fedora/RHEL
brew install helm        # macOS
```

### Podman

**Required for:** Container builds, RHEL container deployments

```bash
# Check installation
podman --version

# Installation
sudo dnf install podman  # Fedora/RHEL/CentOS
sudo apt install podman  # Ubuntu/Debian
brew install podman      # macOS
```

### Docker (alternative to Podman)

**Required for:** Container builds (if Podman not available)

```bash
# Check installation
docker --version

# Installation
# See: https://docs.docker.com/engine/install/
```

### Skopeo

**Required for:** Image inspection, tag verification

```bash
# Check installation
skopeo --version

# Installation
sudo dnf install skopeo  # Fedora/RHEL/CentOS
sudo apt install skopeo  # Ubuntu/Debian
brew install skopeo      # macOS
```

### Git

**Required for:** Repository cloning

```bash
# Check installation
git --version

# Installation
sudo dnf install git     # Fedora/RHEL/CentOS
sudo apt install git     # Ubuntu/Debian
brew install git         # macOS (or Xcode Command Line Tools)
```

### SSH

**Required for:** RHEL remote deployments

```bash
# Check installation
ssh -V

# Usually pre-installed on Linux/macOS
# Windows: Use OpenSSH or WSL
```

### curl and jq

**Required for:** API calls and JSON parsing

```bash
# Check installation
curl --version
jq --version

# Installation
sudo dnf install curl jq  # Fedora/RHEL/CentOS
sudo apt install curl jq  # Ubuntu/Debian
brew install curl jq      # macOS
```

## Cluster Requirements

### OpenShift Cluster Access

For S2I builds and deployments, you need:

1. **Logged in to cluster:**
   ```bash
   oc login <cluster-url>
   # or
   oc login --token=<token> --server=<cluster-url>
   ```

2. **Namespace with edit permissions:**
   ```bash
   # Verify access
   oc auth can-i create deployments
   oc auth can-i create buildconfigs
   ```

3. **Image registry accessible:**
   ```bash
   # Verify internal registry
   oc get route -n openshift-image-registry
   ```

### RHEL/Fedora Host Access

For RHEL deployments, you need:

1. **SSH access to target host:**
   ```bash
   ssh user@target-host
   ```

2. **sudo privileges on target** (for systemd services)

3. **Firewall ports open** (for application access)

## Quick Validation

Run these commands to check your environment:

```bash
# Core tools
which oc helm podman git ssh curl jq skopeo

# Cluster connection (if using OpenShift)
oc whoami
oc project

# Container runtime
podman info || docker info
```

Use the `/validate-environment` skill for automated checking.

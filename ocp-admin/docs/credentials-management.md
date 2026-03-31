---
title: Cluster Credentials Management
category: authentication
sources:
  - title: Assisted Installer for OpenShift Container Platform
    url: https://console.redhat.com/openshift/assisted-installer/clusters
    date_accessed: 2026-03-31
  - title: Understanding authentication
    url: https://docs.openshift.com/container-platform/latest/authentication/understanding-authentication.html
    date_accessed: 2026-03-31
tags: [credentials, kubeconfig, kubeadmin, authentication, cluster-access]
semantic_keywords: [credentials management, kubeconfig download, kubeadmin password, credential storage, multi-cluster authentication, secure credentials]
use_cases: [cluster-access, credentials-download, multi-cluster-management]
related_docs: [multi-cluster-auth.md, security-checklist.md, troubleshooting.md]
last_updated: 2026-03-31
---

# Cluster Credentials Management

Guide for downloading, managing, and using OpenShift cluster credentials with MCP tools.

---

## Overview

This guide covers kubeconfig and kubeadmin credential management for OpenShift clusters:
- Downloading credentials from Assisted Installer
- Secure storage and permissions
- Connecting to clusters via MCP tools
- Multi-cluster context management
- MCP server configuration

---

## 1. Downloading Credentials from Assisted Installer

**Prerequisites**:
- Cluster status: `installed`
- `openshift-self-managed` MCP server configured
- Valid `OFFLINE_TOKEN` environment variable

**Process**:

```bash
# 1. Create secure directory
mkdir -p /tmp/{cluster_name}
chmod 700 /tmp/{cluster_name}

# 2. Get presigned URL for kubeconfig
# MCP Tool: cluster_credentials_download_url
# Parameters: {cluster_id, file_name: "kubeconfig"}
curl -s -o /tmp/{cluster_name}/kubeconfig "{presigned_url}"
chmod 600 /tmp/{cluster_name}/kubeconfig

# 3. Get presigned URL for password
# MCP Tool: cluster_credentials_download_url
# Parameters: {cluster_id, file_name: "kubeadmin-password"}
curl -s -o /tmp/{cluster_name}/kubeadmin-password "{presigned_url}"
chmod 600 /tmp/{cluster_name}/kubeadmin-password

# 4. Verify
ls -l /tmp/{cluster_name}/
# Expected: drwx------ for directory, -rw------- for files
```

**Security**:
- Presigned URLs expire after ~1 hour
- Download immediately after installation
- Directory: 700, Files: 600
- Never expose presigned URLs

---

## 2. Kubeconfig Structure

**Purpose**: Authentication for cluster access via MCP tools

**Location**: `/tmp/<cluster-name>/kubeconfig` (default)

**Contains**: Cluster API endpoint, CA cert, user credentials, context

**Example**:
```yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: <base64>
    server: https://api.cluster.example.com:6443
  name: cluster-name
contexts:
- context:
    cluster: cluster-name
    user: kubeadmin
  name: cluster-name/kubeadmin
current-context: cluster-name/kubeadmin
users:
- name: kubeadmin
  user:
    client-certificate-data: <base64>
    client-key-data: <base64>
```

---

## 3. Connecting to Clusters

### Set KUBECONFIG

```bash
# Temporary (current session)
export KUBECONFIG=/tmp/cluster-name/kubeconfig

# Persistent (add to ~/.bashrc or ~/.zshrc)
echo 'export KUBECONFIG=/tmp/cluster-name/kubeconfig' >> ~/.bashrc
source ~/.bashrc
```

### Verify Cluster Access

**Note**: These verification commands are available via `oc` CLI or the `openshift-administration` MCP server when using Claude Code with KUBECONFIG set.

```bash
# List cluster nodes
oc get nodes

# Get OpenShift version info
oc get clusterversion version -o yaml
```

### Kubeadmin Credentials

**User**: `kubeadmin`
**Password**: Content of `/tmp/<cluster-name>/kubeadmin-password`
**Role**: `cluster-admin` (full access)

**Read password**:
```bash
cat /tmp/<cluster-name>/kubeadmin-password
```

**Web Console**:
```
URL: https://console-openshift-console.apps.<cluster>.<domain>
User: kubeadmin
Password: <from file>
```

**Security**:
- ⚠️ Temporary credential - for initial setup only
- ⚠️ Full cluster-admin access
- ⚠️ Do NOT disable unless explicitly requested
- ✅ Keep secure (600 permissions)

---

## 4. Secure Storage

### File Permissions

```bash
# Directory: 700 (owner only)
chmod 700 /tmp/cluster-name/

# Files: 600 (owner read/write only)
chmod 600 /tmp/cluster-name/kubeconfig
chmod 600 /tmp/cluster-name/kubeadmin-password

# Verify
ls -la /tmp/cluster-name/
```

### Storage Locations

#### /tmp (RECOMMENDED - Default)

**Use for**: Initial setup, short-term access, testing
**Characteristics**: Cleared on reboot, prevents long-term exposure

```bash
mkdir -p /tmp/my-cluster && chmod 700 /tmp/my-cluster
export KUBECONFIG=/tmp/my-cluster/kubeconfig
```

#### ~/.kube (Only if User Requests)

**Use for**: Long-term management, production access
**Characteristics**: Persists across reboots

```bash
# Ask user: "Store credentials permanently in ~/.kube/? (yes/no)"
# If yes:
mkdir -p ~/.kube
cp /tmp/cluster-name/kubeconfig ~/.kube/cluster-name.config
chmod 600 ~/.kube/cluster-name.config
rm -rf /tmp/cluster-name/
export KUBECONFIG=~/.kube/cluster-name.config
```

**Best Practices**:
- ✅ Default to `/tmp/` unless requested
- ✅ Use descriptive names
- ❌ Never commit to git
- ❌ Never share via email/chat

---

## 5. MCP Server Configuration

### OpenShift Administration MCP Server

Uses `KUBECONFIG` environment variable for authentication.

**.mcp.json configuration**:
```json
{
  "mcpServers": {
    "openshift-administration": {
      "command": "bash",
      "args": ["-c", "cd ~/.claude/plugins/.../server && uv run server.py"],
      "env": {
        "KUBECONFIG": "${KUBECONFIG}"
      }
    }
  }
}
```

**How it works**:
1. Set `KUBECONFIG` in shell
2. MCP server inherits variable
3. All MCP tools use configured kubeconfig
4. No restart needed (with multi-context setup)

**Set for cluster operations**:
```bash
export KUBECONFIG=/tmp/cluster-name/kubeconfig

# Verify cluster access
oc get namespaces
```

---

## 6. Multi-Cluster Management

### Merge Multiple Kubeconfigs

```bash
# Merge into single file
KUBECONFIG=/tmp/cluster-a/kubeconfig:/tmp/cluster-b/kubeconfig:/tmp/cluster-c/kubeconfig \
  kubectl config view --flatten > ~/.kube/config

export KUBECONFIG=~/.kube/config

# Verify contexts
kubectl config get-contexts
```

**Example output**:
```
CURRENT   NAME                  CLUSTER    AUTHINFO
*         cluster-a/kubeadmin   cluster-a  kubeadmin
          cluster-b/kubeadmin   cluster-b  kubeadmin
          cluster-c/kubeadmin   cluster-c  kubeadmin
```

### Switch Between Clusters

```bash
# Switch to cluster-b
kubectl config use-context cluster-b/kubeadmin

# Verify active context
kubectl config current-context

# Verify cluster-b access
oc get nodes
```

### Context Naming

**Format**: `<cluster-name>/<username>`

**Examples**:
- `prod-ocp/kubeadmin`
- `dev-sno/kubeadmin`
- `staging-ocp/alice`

**Rename**:
```bash
kubectl config rename-context old-name new-name
```

### MCP Context Switching

**No restart needed**: Changes to KUBECONFIG context are immediate

**Workflow**:
1. Merge kubeconfigs → `~/.kube/config`
2. Set `KUBECONFIG=~/.kube/config`
3. Use `kubectl config use-context` to switch
4. `oc` commands and cluster operations use new context automatically

---

## 7. Session Management

### Verify Active Session

```bash
# Check active context
kubectl config current-context

# Verify cluster access
oc get clusterversion
```

### Switch Sessions

```bash
# Change context
kubectl config use-context <context-name>

# Or change kubeconfig entirely
export KUBECONFIG=/path/to/different/kubeconfig
```

### Close Session

```bash
# Unset kubeconfig
unset KUBECONFIG

# Remove credentials (if temporary)
rm -rf /tmp/cluster-name/
```

---

## 8. Disabling Kubeadmin

**⚠️ Only if explicitly requested by user**

**Prerequisites**:
- Alternative admin user configured and tested
- Kubeadmin credentials backed up

**Process**:

```bash
# 1. Verify alternative admin exists
oc get users

# 2. Delete kubeadmin secret (IRREVERSIBLE)
oc delete secret kubeadmin -n kube-system
```

**Post-deletion**: Cannot be re-enabled without cluster reinstall

---

## 9. Reconfiguring MCP Server Live

### Multi-Context Kubeconfig (RECOMMENDED)

Switch contexts without MCP restart.

```bash
kubectl config use-context cluster-2/kubeadmin

# Verify access to cluster-2
oc get nodes
```

**Why it works**: Context changes are immediate for all cluster operations.

### Change KUBECONFIG Variable (requires restart)

```bash
export KUBECONFIG=/tmp/cluster-2/kubeconfig
# Claude Code restarts MCP automatically
```

### Recommended Workflow

**For multiple clusters**:
1. Merge kubeconfigs → `~/.kube/config`
2. Set `KUBECONFIG=~/.kube/config` permanently
3. Use `kubectl config use-context` to switch
4. No MCP restart needed

**For single cluster at a time**:
1. Keep credentials in `/tmp/<cluster>/kubeconfig`
2. Change `KUBECONFIG` when switching
3. Allow automatic MCP restart

---

## Troubleshooting

### Authentication Failures

**Symptom**: "Unauthorized" or "Forbidden" errors

**Checks**:
```bash
echo $KUBECONFIG                    # Verify set
ls -l $KUBECONFIG                   # Verify exists
kubectl config view                 # Verify valid
kubectl config current-context      # Verify context
```

**Solutions**:
- File not found → Set correct path
- Permission denied → `chmod 600 $KUBECONFIG`
- Expired → Re-download from Assisted Installer
- Wrong context → `kubectl config use-context`

### MCP Not Finding Credentials

**Symptom**: "kubeconfig not found"

**Solutions**:
- Export `KUBECONFIG` before starting Claude Code
- Verify `.mcp.json` includes `"KUBECONFIG": "${KUBECONFIG}"`
- Restart Claude Code

### Context Not Switching

**Symptom**: MCP uses old cluster after `use-context`

**Solutions**:
- Use merged kubeconfig (recommended)
- Restart MCP if using separate files
- Verify `kubectl config current-context`

---

## Security Checklist

✅ Credentials: 700 (dir), 600 (files)
✅ Default to `/tmp/` storage
✅ Kubeadmin enabled (unless user requests disable)
✅ Presigned URLs not exposed
✅ KUBECONFIG set correctly
✅ Multi-context via merged kubeconfig
✅ Not committed to git
✅ Not shared insecurely

---

## Related Documentation

- [RBAC](./rbac.md) - Access control
- [IDP](./idp.md) - Identity Providers
- [Certificate Rotation](./certificate-rotation.md) - Certificate renewal
- [Security Checklist](./security-checklist.md) - Complete security verification

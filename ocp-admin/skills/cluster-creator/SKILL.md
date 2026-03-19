---
name: cluster-creator
description: |
  End-to-end OpenShift cluster creation using Red Hat Assisted Installer.
  Handles Single-Node OpenShift (SNO) and HA multi-node clusters on baremetal, vsphere, oci, nutanix.

  Use when:
  - "Create a new OpenShift cluster"
  - "Install OpenShift on my servers"
  - "Set up a single-node cluster for edge deployment"
  - "Deploy a production HA cluster"

  Complete workflow: cluster definition, ISO generation, host discovery/validation, role assignment,
  network configuration (VIPs, static networking), installation monitoring, credential retrieval.

  NOT for:
  - Listing existing clusters → Use cluster-inventory skill
  - Modifying running clusters → Use openshift-administration MCP tools
  - Cluster upgrades (not yet supported)
model: inherit
color: green
---

# cluster-creator

## Critical: Human-in-the-Loop Requirements

This skill performs critical, irreversible operations requiring explicit user confirmation:

1. **Cluster Definition Creation** (Step 5): Display configuration, ask "Ready to create?"
2. **Starting Installation** (Step 13): Display summary, emphasize "WARNING: Irreversible!", wait for explicit "YES"
3. **After Major Steps**: Report VIP/network/role configuration results

**Never Assume Approval** - Always wait for explicit confirmation.

---

## Prerequisites

**Required MCP Servers**: `openshift-self-managed` ([setup guide](../README.md#environment-setup))

**Required MCP Tools**: `list_versions`, `create_cluster`, `cluster_info`, `set_cluster_vips`, `set_host_role`, `cluster_iso_download_url`, `install_cluster`, `cluster_credentials_download_url`, `generate_nmstate_yaml`, `validate_nmstate_yaml`, `alter_static_network_config_nmstate_for_host`

**Environment Variables**: `OFFLINE_TOKEN` ([obtain here](https://cloud.redhat.com/openshift/token))

**Cluster Types Supported**:
- **OCP** (OpenShift Container Platform) - Self-managed HA clusters
- **SNO** (Single-Node OpenShift) - Self-managed single-node clusters

**NOT Supported** (use cloud provider consoles instead):
- **ROSA** (Red Hat OpenShift Service on AWS) - Use AWS Console or rosa CLI
- **ARO** (Azure Red Hat OpenShift) - Use Azure Portal or az CLI
- **OSD** (OpenShift Dedicated) - Use Red Hat Hybrid Cloud Console

**Verification**:
1. Check `openshift-self-managed` in `.mcp.json`
2. Verify `OFFLINE_TOKEN` set: `test -n "$OFFLINE_TOKEN"`
3. Test connection: Call `list_versions` to verify MCP server responsive

**On Failure**: Stop immediately, display setup instructions, ask "How to proceed? (setup/skip/abort)", wait for user input.

**Security**: Never expose credential values in output.

---

## When to Use This Skill

**Use when**:
- Creating new OpenShift cluster from scratch
- Deploying SNO for edge/development
- Setting up production HA cluster
- Have servers ready for OpenShift installation

**Do NOT use when**:
- Listing/inspecting clusters → Use `cluster-inventory` skill
- Managing workloads → Use `openshift-administration` MCP tools
- Troubleshooting → Use `cluster-inventory` skill
- Upgrading clusters (not supported)

---

## Workflow

End-to-end cluster creation with interactive guidance and validation.

### Step 1: Prerequisites and Documentation

**Progress**: Step 1 of 18

**Document Consultation** (REQUIRED):
1. **Action**: Read [troubleshooting.md](../../docs/troubleshooting.md)
2. **Output**: "I consulted troubleshooting.md to understand cluster lifecycle states."

**Prerequisites Check**: Execute verification from Prerequisites section.

---

### Step 2: Gather Cluster Requirements

**Progress**: Step 2 of 18

Use AskUserQuestion tool to collect:

1. **Cluster Type**: SNO or HA
2. **Platform**: SNO=`none` (auto), HA=baremetal/vsphere/nutanix/oci (user selects)
3. **Version**: Call `list_versions`, show "Full Support" versions
4. **Cluster Name**: 1-54 chars, lowercase/numbers/hyphens, starts with letter ([validation](../../docs/input-validation-guide.md#cluster-name))
5. **Base Domain**: Valid DNS domain ([validation](../../docs/input-validation-guide.md#base-domain))
6. **CPU Arch**: x86_64 (default), aarch64, ppc64le, s390x
7. **SSH Key**: Valid SSH public key ([validation](../../docs/input-validation-guide.md#ssh-public-key))

**Store all values** for subsequent steps.

**Reference**: [Input Validation Guide](../../docs/input-validation-guide.md)

---

### Step 3: Platform-Specific Configuration

**Progress**: Step 3 of 18

**For HA on baremetal/vsphere/nutanix**:
- **Gather VIPs**: API VIP and Ingress VIP (IPv4, same subnet as nodes, not assigned)
- **Validation**: [VIP Requirements](../../docs/input-validation-guide.md#virtual-ips-vips)

**Optional Static Networking**:
- Ask: "Use DHCP or static networking?"
- **If static**: For each host, gather network config (Simple/Advanced/Manual mode)
  - **Simple**: Interface, MAC, IP, prefix, gateway, DNS
  - **Advanced**: VLANs, bonding, multiple interfaces
  - **Manual**: User provides NMState YAML
- **Tools**: `generate_nmstate_yaml`, `validate_nmstate_yaml`
- **Store**: `static_network_configs` array

**Reference**: [Static Networking Guide](../../docs/static-networking-guide.md), [Networking Guide](../../docs/networking.md)

---

### Step 4: Configuration Briefing

**Progress**: Step 4 of 18

Display summary table:

| Parameter | Value |
|-----------|-------|
| Cluster Name | {cluster_name} |
| Type | {SNO/HA} |
| Version | {openshift_version} |
| Platform | {platform} |
| Architecture | {cpu_architecture} |
| Domain | {base_domain} |
| VIPs | {if applicable} |
| Networking | {DHCP or Static (n hosts)} |

**Reference**: [Examples](../../docs/examples.md)

---

### Step 5: Confirmation Before Creation

**Progress**: Step 5 of 18 - CRITICAL CHECKPOINT

Ask: "Review configuration. Ready to create cluster definition?"

**Options**:
- **Yes**: Proceed to Step 6
- **No**: Allow parameter modification, re-display, re-ask
- **Abort**: Exit gracefully

---

### Step 6: Create Cluster Definition

**Progress**: Step 6 of 18

**Tool**: `create_cluster`

**Parameters**: `{name, version, base_domain, single_node, platform, cpu_architecture, ssh_public_key}`

**Output**: Cluster UUID (`cluster_id`) - **CRITICAL for all subsequent operations**

**Error Handling**: Display error, allow retry/abort if duplicate name or invalid parameters.

---

### Step 7: Apply Platform Configuration

**Progress**: Step 7 of 18

**7a. Set VIPs** (HA + baremetal/vsphere/nutanix only):
- **Tool**: `set_cluster_vips`
- **Parameters**: `{cluster_id, api_vip, ingress_vip}`

**7b. Apply Static Network** (if configured):
- For each host: **Tool**: `alter_static_network_config_nmstate_for_host`
- **Parameters**: `{cluster_id, nmstate_yaml, mac_address}`
- **Verify**: Call `list_static_network_config`

**Reference**: [Providers](../../docs/providers.md), [Networking](../../docs/networking.md)

---

### Step 8: Generate Cluster ISO

**Progress**: Step 8 of 18

**Tool**: `cluster_iso_download_url`
**Parameters**: `{cluster_id}`

**Display**:
```
Cluster Boot ISO Ready
Download: {url}

Instructions:
1. Download ISO
2. Boot {expected_host_count} server(s) from ISO
3. Wait 5-10 minutes for registration
4. Say "check for hosts" when ready

Note: Hosts receive static configs in boot order.
```

---

### Step 9: Wait for User to Boot Hosts

**Progress**: Step 9 of 18

Display: "Waiting for you to boot hosts. When ready, say 'check for hosts'."

**Wait for user trigger** - No automatic polling.

---

### Step 10: Check Host Discovery

**Progress**: Step 10 of 18

**Tool**: `cluster_info`
**Parameters**: `{cluster_id}`

**Parse**: Extract `hosts` array, count discovered hosts

**Display**: Table with Host #, Hostname, CPU, RAM, Disk, Status

**Validation**:
- SNO: Requires exactly 1 host
- HA: Minimum 3 hosts

**If insufficient**: Ask to wait/proceed/abort.

**Reference**: [Host Requirements](../../docs/host-requirements.md)

---

### Step 11: Host Role Assignment

**Progress**: Step 11 of 18

**SNO**: Single host auto-assigned "master"

**HA**:
- Suggest first 3 hosts as "master"
- Additional hosts as "worker"
- Allow user override

**Tool**: `set_host_role` (for each host)
**Parameters**: `{cluster_id, host_id, role}`

---

### Step 12: Validate Cluster Readiness

**Progress**: Step 12 of 18

**Tool**: `cluster_info`

**Check**: Cluster `status` should be "ready"

**If validation fails**: Display errors, offer fix/wait/abort.

**Reference**: [Troubleshooting](../../docs/troubleshooting.md)

---

### Step 13: Final Confirmation Before Installation

**Progress**: Step 13 of 18 - CRITICAL CHECKPOINT

**Display**:
```
Ready to Start Installation

Cluster: {cluster_name}
Hosts: {count}

WARNING: Starting installation is irreversible!
Cannot pause or cancel once started.
```

Ask: "Start installation now?"

**Options**:
- **YES - Start now**: Proceed to Step 14
- **Wait - Review first**: Display config, re-ask
- **Abort**: Exit skill

---

### Step 14: Start Installation

**Progress**: Step 14 of 18

**Tool**: `install_cluster`
**Parameters**: `{cluster_id}`

**On Success**: Display "Installation started!"

**On Error**: Display error, document in troubleshooting.md if new, offer retry/abort.

---

### Step 15: Monitor Installation

**Progress**: Step 15 of 18

**Display**:
```
Installation Phases:
1. Preparing
2. Installing (bootstrapping)
3. Installing control plane
4. Finalizing
5. Completed

How to monitor:
- Say "check status" anytime
- Or use background monitoring

Background monitoring? (yes/no)
```

**If background**: Use Task tool with `run_in_background=true`

**If manual**: Wait for "check status", then call `cluster_info`, display progress, repeat until "installed" or "error"

**If fails**: Download logs (`cluster_logs_download_url`), offer diagnose/cleanup/manual options.

**Reference**: [Troubleshooting](../../docs/troubleshooting.md)

---

### Step 16: Installation Complete

**Progress**: Step 16 of 18

Display: "Installation Completed! Cluster: {cluster_name}, Status: installed, Time: {duration}"

---

### Step 17: Retrieve Credentials

**Progress**: Step 17 of 18

**Security**: Credentials provide full admin access. Handle securely.

**17a. Prepare Storage**:
```bash
mkdir -p /tmp/{cluster_name} && chmod 700 /tmp/{cluster_name}
```

**17b. Download Kubeconfig**:
- **Tool**: `cluster_credentials_download_url`
- **Parameters**: `{cluster_id, file_name: "kubeconfig"}`
- **Download**: `curl -s -o /tmp/{cluster_name}/kubeconfig "{url}" && chmod 600 /tmp/{cluster_name}/kubeconfig`

**17c. Download Kubeadmin Password**:
- **Tool**: `cluster_credentials_download_url`
- **Parameters**: `{cluster_id, file_name: "kubeadmin-password"}`
- **Download**: `curl -s -o /tmp/{cluster_name}/kubeadmin-password "{url}" && chmod 600 /tmp/{cluster_name}/kubeadmin-password`

**Display**:
```
Kubeconfig: /tmp/{cluster_name}/kubeconfig
Password: /tmp/{cluster_name}/kubeadmin-password
Permissions: -rw------- (secure)

To use:
export KUBECONFIG=/tmp/{cluster_name}/kubeconfig
oc get nodes
```

**Reference**: [Credentials Management](../../docs/credentials-management.md)

---

### Step 18: Cluster Ready

**Progress**: Step 18 of 18

**Display**:
```
OpenShift Cluster Ready!

Cluster: {cluster_name}
API: https://api.{cluster_name}.{base_domain}:6443
Console: https://console-openshift-console.apps.{cluster_name}.{base_domain}

Credentials: /tmp/{cluster_name}/

Next Steps:
- Access cluster: oc --kubeconfig /tmp/{cluster_name}/kubeconfig get nodes
- Web console: Use kubeadmin + password from /tmp/{cluster_name}/kubeadmin-password
- Configure identity provider (see credentials-management.md)
- Install operators and deploy applications

Congratulations!
```

**Ask**: "Copy credentials to permanent storage? (yes/no)"

**If yes**: Copy to `~/.kube/` with secure permissions.

**Reference**: [Credentials Management](../../docs/credentials-management.md)

---

## Dependencies

### Required MCP Servers
- `openshift-installer` - Assisted Installer service ([setup](../README.md#environment-setup))

### Required MCP Tools
All from `openshift-installer`:
- `list_versions`, `create_cluster`, `cluster_info`, `set_cluster_vips`, `set_host_role`
- `cluster_iso_download_url`, `install_cluster`, `cluster_credentials_download_url`
- `generate_nmstate_yaml`, `validate_nmstate_yaml`, `alter_static_network_config_nmstate_for_host`

### Related Skills
- `cluster-inventory` - List and inspect clusters

### Reference Documentation
**Configuration & Validation**:
- [Input Validation Guide](../../docs/input-validation-guide.md) - Parameter requirements
- [Networking](../../docs/networking.md) - Network configuration, VIPs, CIDR planning
- [Static Networking Guide](../../docs/static-networking-guide.md) - NMState configuration

**Platform & Infrastructure**:
- [Providers](../../docs/providers.md) - Infrastructure providers (baremetal, vsphere, oci, nutanix)
- [Platforms](../../docs/platforms.md) - OpenShift types (SNO, OCP, ROSA, ARO, OSD)
- [Host Requirements](../../docs/host-requirements.md) - Hardware specs by cluster type

**Post-Installation**:
- [Credentials Management](../../docs/credentials-management.md) - Kubeconfig, OAuth, RBAC
- [Storage](../../docs/storage.md) - Storage options by provider
- [Examples](../../docs/examples.md) - Configuration examples
- [Troubleshooting](../../docs/troubleshooting.md) - Common errors and resolutions

---

## Example Usage

**User**: "Create a single-node OpenShift cluster for my edge location."

**Execution**:
1. Prerequisites verified, docs consulted
2. SNO selected, platform: none, version: 4.18.2
3. Name: "edge-site-01", domain: "edge.local"
4. SSH key provided, VIPs skipped, DHCP networking
5. Configuration confirmed, cluster created
6. ISO provided, user boots server
7. Host discovered, assigned "master"
8. Validation: ready
9. Installation confirmed and started
10. Monitoring: 0% → 100% (~45 min)
11. Credentials downloaded to /tmp/edge-site-01/
12. Cluster operational!

**Result**: SNO cluster deployed in ~45 minutes.

**More Examples**: See [examples.md](../../docs/examples.md) for HA, static networking, multi-cluster, and air-gapped configurations.

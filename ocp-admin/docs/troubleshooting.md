---
title: OpenShift Cluster Troubleshooting Guide
category: cluster-management
sources:
  - title: Red Hat Assisted Installer Documentation
    url: https://console.redhat.com/openshift/assisted-installer/clusters
    date_accessed: 2024-02-10
  - title: OpenShift Container Platform Documentation
    url: https://docs.openshift.com/container-platform/latest/installing/index.html
    date_accessed: 2024-02-10
tags: [cluster, troubleshooting, installation, status, diagnostics]
semantic_keywords: [cluster status, installation error, pending-for-input, ready state, validation failure, network configuration, host discovery]
use_cases: [cluster_diagnosis, status_interpretation, installation_troubleshooting]
related_docs: []
last_updated: 2024-02-10
---

# OpenShift Cluster Troubleshooting Guide

## Overview

This guide provides AI-optimized troubleshooting information for OpenShift cluster management through the Red Hat Assisted Installer service. Use this documentation when interpreting cluster status, diagnosing installation issues, or understanding cluster configuration requirements.

## When to Use This Document

Consult this guide when:
- Interpreting cluster status values from `list_clusters` or `cluster_info`
- Diagnosing why a cluster installation is not progressing
- Understanding network configuration requirements (VIPs, subnets)
- Investigating cluster validation failures
- Troubleshooting host discovery and registration issues
- Resolving OFFLINE_TOKEN authentication problems

**Quick Commands**: See [Quick Reference](./quick-reference.md) for common diagnostic commands and emergency procedures.

**Related Documentation**:
- [Quick Reference](./quick-reference.md) - Diagnostic commands and scenarios
- [Networking Guide](./networking.md) - Network configuration details
- [Host Requirements](./host-requirements.md) - Hardware specifications
- [INDEX](./INDEX.md) - Complete documentation index

---

## MCP Server Authentication Issues

### OFFLINE_TOKEN Configuration

The `openshift-installer` MCP server requires an `OFFLINE_TOKEN` environment variable for authenticating with Red Hat's assisted installer API at console.redhat.com.

**Check this section ONLY if cluster operations fail with authentication errors**. By default, assume everything works correctly.

---

#### Problem: "Authentication failed" or "Unauthorized" errors

**Symptoms**:
- `list_clusters` returns empty or authentication error
- `cluster_info` fails with permission denied
- MCP server connection errors
- 401 Unauthorized responses from API

**Diagnosis Steps**:

1. **Verify OFFLINE_TOKEN is set** (without exposing the value):
   ```bash
   test -n "$OFFLINE_TOKEN" && echo "✓ OFFLINE_TOKEN is configured" || echo "✗ OFFLINE_TOKEN is missing"
   ```

2. **Check token format**:
   - Token should be a long alphanumeric string
   - Should NOT contain quotes or extra whitespace
   - Should NOT be wrapped in `${...}` when setting environment variable

3. **Verify Red Hat account permissions**:
   - Log in to https://console.redhat.com/openshift/assisted-installer/clusters
   - Verify you can see clusters in the web interface
   - Confirm your account has cluster management permissions in your organization

**Resolution**:

If OFFLINE_TOKEN is missing or invalid:

1. **Obtain a new token**:
   ```bash
   # Visit the token generation page
   open https://cloud.redhat.com/openshift/token

   # Or manually navigate to: https://cloud.redhat.com/openshift/token
   ```

2. **Copy the offline token** displayed on the page (after logging in)

3. **Set the environment variable**:
   ```bash
   export OFFLINE_TOKEN="your-offline-token-here"
   ```

4. **Verify it's set correctly** (check without exposing value):
   ```bash
   test -n "$OFFLINE_TOKEN" && echo "✓ Token configured" || echo "✗ Still missing"
   ```

5. **Test MCP server connection**:
   ```bash
   podman run --rm -i --network=host \
     -e "TRANSPORT=stdio" \
     -e "OFFLINE_TOKEN=${OFFLINE_TOKEN}" \
     -e "INVENTORY_URL=https://api.openshift.com/api/assisted-install/" \
     -e "PULL_SECRET_URL=https://api.openshift.com/api/accounts_mgmt/v1/access_token" \
     quay.io/ecosystem-appeng/assisted-service-mcp:latest
   ```

**Token Requirements**:
- Must be from the same Red Hat account used to manage clusters
- Account must have cluster creation/read/update permissions
- Token does not expire automatically but can be revoked
- Treat like a password - do not share or expose in logs

**Security Best Practices**:
- ✓ Set OFFLINE_TOKEN in shell profile (`.bashrc`, `.zshrc`) for persistence
- ✓ Use environment variable reference `${OFFLINE_TOKEN}` in `mcps.json`
- ✓ Never commit `.env` files containing tokens to version control
- ✗ NEVER echo or print the token value in commands
- ✗ NEVER include token in code, scripts, or documentation examples

---

#### Problem: "Permission denied" for cluster operations

**Symptoms**:
- Can list clusters but cannot create new ones
- Some clusters visible, others not accessible
- Operations fail with 403 Forbidden errors

**Diagnosis**:
- This indicates insufficient RBAC permissions in your Red Hat organization
- Your account has read access but not write access

**Resolution**:
1. Contact your Red Hat organization administrator
2. Request cluster creation/management permissions
3. Verify permissions by accessing https://console.redhat.com/openshift/assisted-installer/clusters
4. Ensure you can click "Create cluster" button in web interface
5. Once permissions granted, regenerate OFFLINE_TOKEN (may be required)

---

#### Problem: MCP server container fails to start

**Symptoms**:
- Container exits immediately
- Error: "OFFLINE_TOKEN not set" or similar
- Cannot connect to MCP server

**Diagnosis**:

1. **Check container logs**:
   ```bash
   podman logs $(podman ps -a --filter ancestor=quay.io/ecosystem-appeng/assisted-service-mcp:latest --format "{{.ID}}" | head -1)
   ```

2. **Verify environment variable is passed to container**:
   - Ensure `mcps.json` has `"env": {"OFFLINE_TOKEN": "${OFFLINE_TOKEN}"}`
   - Ensure shell session has `OFFLINE_TOKEN` exported before starting Claude Code

3. **Test manual container execution**:
   ```bash
   podman run --rm -i --network=host \
     -e "OFFLINE_TOKEN=${OFFLINE_TOKEN}" \
     quay.io/ecosystem-appeng/assisted-service-mcp:latest
   ```

**Resolution**:
- If manual test works: Restart Claude Code to reload environment variables
- If manual test fails: OFFLINE_TOKEN not exported - set it in current shell
- If container can't pull image: Check network access to quay.io registry

---

## Cluster Status Values

### Cluster Lifecycle States

OpenShift clusters managed through the Assisted Installer progress through the following states:

#### **insufficient** (Initial State)
**Meaning**: Cluster created but missing required configuration or resources

**Common Causes**:
- No hosts discovered yet (hosts not booted from cluster ISO)
- Insufficient number of hosts for cluster type (SNO needs 1, HA needs 3+ masters)
- Hosts do not meet minimum hardware requirements
- Network configuration incomplete

**Resolution**:
1. Download cluster ISO using `cluster_iso_download_url`
2. Boot hosts from the ISO to register them
3. Wait for hosts to appear in `cluster_info` host list
4. Verify host hardware meets requirements (CPU, memory, disk)

**Indicators in cluster_info**:
- Host count: 0 or insufficient for cluster type
- Validation failures related to host requirements

---

#### **pending-for-input** (Configuration Required)
**Meaning**: Cluster is waiting for user-provided configuration before proceeding

**Common Causes**:
- **Network VIPs not set**: API and Ingress VIPs required for HA clusters (not SNO)
- **SSH key missing**: Some configurations require SSH public key
- **Host roles not assigned**: Hosts discovered but roles (master/worker) not set
- **Custom networking**: Advanced network configuration pending

**Resolution**:
1. Check cluster platform type:
   - **HA clusters (platform: baremetal, vsphere, nutanix)**: Configure VIPs using `set_cluster_vips`
   - **SNO clusters (platform: none)**: VIPs not required, check other validations
2. Set SSH key if required: `set_cluster_ssh_key`
3. Assign host roles if needed: `set_host_role`
4. Review `cluster_info` validation messages for specific requirements

**Example VIP Configuration**:
```
API VIP: 192.168.1.100 (must be in machine network subnet, unused)
Ingress VIP: 192.168.1.101 (must be in machine network subnet, unused)
```

**Indicators in cluster_info**:
- Validation message: "Network VIPs required"
- VIP fields show: "Not configured" or null
- Status info: "Waiting for user input"

---

#### **ready** (Ready for Installation)
**Meaning**: All prerequisites met, cluster ready to begin installation

**Requirements Satisfied**:
- Correct number of hosts discovered and validated
- All hosts meet hardware requirements
- Network configuration complete (VIPs set if required)
- Host roles assigned
- All validations passing

**Next Steps**:
- Use `install_cluster` to begin installation
- Installation will start automatically on all hosts
- Monitor progress with `cluster_info` and `cluster_events`

**Indicators in cluster_info**:
- Overall status: "ready"
- All validations passing
- Hosts in "ready" state with assigned roles

---

#### **installing** (Installation In Progress)
**Meaning**: Cluster installation actively running on hosts

**Installation Phases**:
1. **Preparing for installation**: Hosts downloading container images
2. **Installing**: Operating system and OpenShift components installing
3. **Bootstrapping**: Initial control plane node coming up
4. **Installing control plane**: Master nodes joining cluster
5. **Installing workers**: Worker nodes joining cluster
6. **Finalizing**: Post-installation configuration

**Monitoring**:
- Use `cluster_info` to see current installation phase
- Use `cluster_events` to see detailed installation progress
- Check host-specific status with `host_events`

**Typical Duration**:
- SNO cluster: 30-45 minutes
- HA cluster (3 masters): 45-60 minutes
- HA cluster with workers: 60-90 minutes

**Indicators in cluster_info**:
- Status: "installing"
- Installation progress percentage
- Per-host installation status

---

#### **finalizing** (Nearly Complete)
**Meaning**: Core installation complete, running final configuration steps

**Finalizing Tasks**:
- Configuring cluster operators
- Setting up monitoring and logging
- Configuring storage classes
- Running post-installation validations

**Expected Duration**: 5-15 minutes

**Next Steps**:
- Wait for status to change to "installed"
- Do not interrupt during finalization

**Indicators in cluster_info**:
- Status: "finalizing"
- Most operators showing "Available"
- Cluster operators reaching ready state

---

#### **installed** (Installation Complete)
**Meaning**: Cluster successfully installed and operational

**Post-Installation**:
1. Download credentials: `cluster_credentials_download_url` with `file_name: "kubeconfig"`
2. Download kubeadmin password: `cluster_credentials_download_url` with `file_name: "kubeadmin-password"`
3. Access cluster using kubeconfig
4. Log in to OpenShift console with kubeadmin credentials

**Verification**:
```bash
export KUBECONFIG=/path/to/downloaded/kubeconfig
oc get nodes                  # All nodes should be Ready
oc get clusteroperators       # All operators should be Available
oc get co                     # Short form of above
```

**See**: [Quick Reference - Cluster Status](./quick-reference.md#cluster-status) for more diagnostic commands

**Indicators in cluster_info**:
- Status: "installed"
- All hosts: "installed" status
- Cluster operators: All available and not degraded

---

#### **error** (Installation Failed)
**Meaning**: Installation encountered an unrecoverable error

**Common Error Causes**:
- Host failures during installation (hardware issues, network loss)
- Insufficient resources (disk space, memory)
- Network connectivity problems
- DNS resolution failures
- Storage provisioning failures

**Diagnosis Steps**:
1. Use `cluster_events` to identify error messages
2. Use `host_events` to check individual host failures
3. Review validation failures in `cluster_info`
4. Check cluster logs: `cluster_logs_download_url`

**Recovery Options**:
- Fix underlying issue (network, hardware, resources)
- Reset cluster and retry installation
- Create new cluster if errors persist

**Indicators in cluster_info**:
- Status: "error"
- Error messages in status_info
- Failed hosts showing specific errors

---

## Network Configuration Requirements

### Understanding VIPs (Virtual IP Addresses)

**What are VIPs?**
Virtual IP addresses used for cluster ingress and API access in high-availability deployments.

**When are VIPs Required?**
- **HA clusters** (platform: baremetal, vsphere, nutanix): **YES, required**
- **SNO clusters** (platform: none): **NO, not used**
- **OCI clusters** (platform: oci): **NO, handled by cloud provider**

**VIP Requirements**:
- Must be within the machine network subnet (same network as hosts)
- Must NOT be assigned to any physical host or device
- Must be reachable from all cluster nodes
- API VIP: Used for Kubernetes API server access
- Ingress VIP: Used for application route ingress

**Example Network Configuration**:
```
Machine Network: 192.168.1.0/24
API VIP: 192.168.1.100
Ingress VIP: 192.168.1.101
Host IPs: 192.168.1.10, 192.168.1.11, 192.168.1.12
```

**Setting VIPs**:
Use the `set_cluster_vips` tool with exact IP addresses:
```
api_vip: "192.168.1.100"
ingress_vip: "192.168.1.101"
```

### Network Subnet Configuration

**Required Network Definitions**:
1. **Machine Network CIDR**: Physical host network (e.g., 192.168.1.0/24)
2. **Cluster Network CIDR**: Pod network (e.g., 10.128.0.0/14)
3. **Service Network CIDR**: Service network (e.g., 172.30.0.0/16)

**Network Overlap Prevention**:
- Machine, Cluster, and Service networks must NOT overlap
- Use separate IP ranges for each network type
- Default ranges are typically sufficient unless custom networking required

---

## Host Discovery and Registration

### Host Discovery Process

1. **ISO Download**: Get cluster boot ISO using `cluster_iso_download_url`
2. **Boot Hosts**: Boot physical or virtual machines from the ISO
3. **Auto-Registration**: Hosts automatically register with assisted installer
4. **Validation**: Hosts validated for hardware requirements
5. **Role Assignment**: Assign master/worker roles (or use auto-assign)

### Host Hardware Requirements

**Minimum Requirements** (per host):

**For SNO (Single Node OpenShift)**:
- CPU: 8 cores
- Memory: 32 GB RAM
- Disk: 120 GB
- Network: 1 NIC with connectivity

**For HA Master Nodes**:
- CPU: 4 cores
- Memory: 16 GB RAM
- Disk: 120 GB
- Network: 1 NIC with connectivity

**For Worker Nodes**:
- CPU: 2 cores
- Memory: 8 GB RAM
- Disk: 120 GB
- Network: 1 NIC with connectivity

**Recommended Production Configuration**:
- CPU: 8+ cores for masters, 4+ cores for workers
- Memory: 32+ GB for masters, 16+ GB for workers
- Disk: SSD storage, 500+ GB
- Network: Dual NICs for redundancy

### Host Role Assignment

**Role Types**:
- **master**: Control plane node (API server, etcd, scheduler)
- **worker**: Compute node (runs application workloads only)
- **auto-assign**: Let installer choose based on cluster requirements

**Role Requirements**:
- **SNO**: 1 master node (combines control plane + worker)
- **HA Compact**: 3 master nodes (control plane + worker on same nodes)
- **HA Standard**: 3 masters + N workers (separate control plane and compute)

**Setting Host Roles**:
Use `set_host_role` with host_id from `cluster_info`:
```
role: "master"  # For control plane nodes
role: "worker"  # For compute-only nodes
role: "auto-assign"  # Let installer decide
```

---

## Cluster Validation Failures

### Common Validation Issues

#### "Insufficient hosts"
**Problem**: Not enough hosts for cluster type
**Resolution**:
- SNO requires 1 host
- HA requires minimum 3 master nodes
- Boot additional hosts from cluster ISO

#### "Host hardware insufficient"
**Problem**: Host doesn't meet minimum requirements
**Resolution**:
- Increase host CPU, memory, or disk
- Use different hardware that meets requirements
- Check `host_events` for specific resource shortfall

#### "Network configuration incomplete"
**Problem**: VIPs not configured for HA cluster
**Resolution**:
- Use `set_cluster_vips` to configure API and Ingress VIPs
- Ensure VIPs are in machine network subnet
- Verify VIPs are not already in use

#### "Host not ready"
**Problem**: Host discovered but failing validations
**Resolution**:
- Check host hardware meets requirements
- Verify network connectivity
- Review `host_events` for specific validation failures
- Ensure host can reach installer service

---

## Using Cluster Events for Diagnostics

### Event Types

**INFO**: Normal operational events
- Cluster created
- Hosts discovered
- Configuration applied
- Installation phase changes

**WARNING**: Issues that may need attention
- VIPs not configured
- Hosts pending validation
- Validation failures (non-blocking)

**ERROR**: Critical issues blocking progress
- Installation failures
- Host errors
- Network connectivity loss
- Validation failures (blocking)

### Event Analysis Pattern

When investigating issues:
1. Use `cluster_events` to get chronological event list
2. Filter for ERROR and WARNING events
3. Identify most recent error or warning
4. Cross-reference with `cluster_info` current status
5. Use `host_events` for host-specific issues

**Example Diagnostic Flow**:
```
User reports: "My cluster won't install"
→ Check cluster_info: Status = "pending-for-input"
→ Check cluster_events: Most recent warning = "Network VIPs not configured"
→ Resolution: Use set_cluster_vips to configure VIPs
```

---

## Platform-Specific Considerations

### Platform Types

**baremetal**:
- For bare metal servers
- Requires VIP configuration
- Manual host provisioning (boot from ISO)
- Full control over hardware

**vsphere**:
- For VMware vSphere environments
- Requires VIP configuration
- VMs must boot from cluster ISO
- Integrates with vSphere for VM management

**nutanix**:
- For Nutanix AHV environments
- Requires VIP configuration
- VMs must boot from cluster ISO
- Integrates with Nutanix platform

**oci**:
- For Oracle Cloud Infrastructure
- VIPs handled by cloud provider (do not configure)
- Uses OCI load balancers automatically
- Cloud-native networking

**none**:
- For single-node deployments
- No VIP configuration needed
- Simplified networking
- Edge/remote office deployments

### Choosing Platform Type

**When to use each platform**:
- **baremetal**: Physical servers, full hardware control, on-premises datacenters
- **vsphere**: VMware environments, enterprise virtualization
- **nutanix**: Nutanix hyperconverged infrastructure
- **oci**: Oracle Cloud deployments
- **none**: Single-node OpenShift (SNO), edge locations, development environments

---

## Quick Reference: Status Transitions

**Normal Installation Flow**:
```
insufficient → pending-for-input → ready → installing → finalizing → installed
```

**Typical Timestamps**:
- insufficient to pending-for-input: 1-5 minutes (host discovery)
- pending-for-input to ready: Immediate (after configuration)
- ready to installing: Immediate (after install_cluster invocation)
- installing to finalizing: 30-60 minutes
- finalizing to installed: 5-15 minutes

**Error Flow**:
```
Any state → error (when unrecoverable issue occurs)
```

**Stuck in pending-for-input**:
- Most common: VIPs not configured
- Check cluster_info validation messages
- Review cluster_events for specific requirements

**Stuck in installing**:
- Check cluster_events for progress
- Use host_events to identify failed hosts
- Review cluster_logs_download_url for detailed logs

---

## Best Practices

### Pre-Installation Checklist

Before starting cluster installation:
- [ ] Verify sufficient hosts available (1 for SNO, 3+ for HA)
- [ ] Confirm hosts meet minimum hardware requirements
- [ ] Prepare VIP addresses if HA cluster (2 unused IPs in host subnet)
- [ ] Download cluster ISO and boot all hosts
- [ ] Wait for all hosts to register and validate
- [ ] Assign host roles if not using auto-assign
- [ ] Configure VIPs if required for platform type
- [ ] Set SSH public key for node access (recommended)
- [ ] Review cluster_info to ensure all validations pass
- [ ] Only then invoke install_cluster

### Monitoring Installation

During installation:
- Check cluster_info every 5-10 minutes for progress
- Review cluster_events if status doesn't change as expected
- Do NOT interrupt installation once started
- Allow at least 60-90 minutes for HA cluster completion
- Wait for "installed" status before downloading credentials

### Post-Installation Verification

After installation completes:
- Download kubeconfig and kubeadmin-password
- Verify all nodes are Ready: `oc get nodes`
- Check cluster operators: `oc get clusteroperators`
- Ensure no operators are Degraded
- Test cluster access through both API and console
- Configure additional cluster components (storage, networking, etc.)

---

## Common Error Messages

### "Network VIPs required for installation"
**Status**: pending-for-input
**Resolution**: Use `set_cluster_vips` to configure API and Ingress VIPs
**Platform**: baremetal, vsphere, nutanix only

### "Insufficient number of hosts"
**Status**: insufficient
**Resolution**: Boot additional hosts from cluster ISO until minimum met
**Minimum**: 1 for SNO, 3 for HA

### "Host does not meet minimum requirements"
**Status**: insufficient (host-level)
**Resolution**: Increase host resources or use different hardware
**Check**: host_events for specific resource shortfall (CPU/memory/disk)

### "Cluster validation failed"
**Status**: varies
**Resolution**: Review cluster_info validation messages for specific failures
**Action**: Address each validation failure before proceeding

### "Installation failed on host [hostname]"
**Status**: error or installing
**Resolution**: Use host_events to identify host-specific failure cause
**Common causes**: Network loss, hardware failure, insufficient disk space

---

## OCM API Troubleshooting (Managed Service Clusters)

### Overview

The OCM (OpenShift Cluster Manager) API provides access to managed service clusters:
- **ROSA** (Red Hat OpenShift Service on AWS)
- **ARO** (Azure Red Hat OpenShift)
- **OSD** (OpenShift Dedicated)

The `cluster-inventory` skill queries both the Assisted Installer API and the OCM API to provide comprehensive cluster coverage.

**OCM API Endpoint**: `https://api.openshift.com/api/clusters_mgmt/v1`

---

### Authentication for OCM Clusters

**Same OFFLINE_TOKEN Works for Both APIs**:

The OFFLINE_TOKEN used for Assisted Installer clusters also authenticates to the OCM API. No separate token is required.

**Verification**:
```bash
# Check OFFLINE_TOKEN is set
test -n "$OFFLINE_TOKEN" && echo "✓ Set" || echo "✗ Missing"

# Same token works for both APIs
```

---

### Common OCM API Issues

#### Problem: "No OCM clusters found" but clusters exist in console

**Symptoms**:
- `ocm_list_clusters` returns empty or "No clusters found"
- Clusters visible in https://console.redhat.com/openshift
- Assisted Installer API works correctly

**Diagnosis**:
1. Verify OFFLINE_TOKEN is set
2. Check account permissions for managed services
3. Verify you're logged in with the correct Red Hat account

**Resolution**:
```bash
# 1. Verify token
test -n "$OFFLINE_TOKEN" && echo "✓ Token set" || echo "✗ Missing"

# 2. Check account at console
# Visit https://console.redhat.com/openshift
# Verify you can see ROSA/ARO/OSD clusters

# 3. If needed, regenerate token
# https://cloud.redhat.com/openshift/token
```

---

#### Problem: OCM API returns 403 Forbidden

**Symptoms**:
- Error: "Permission denied" when calling `ocm_list_clusters`
- Assisted Installer API works fine
- Status code 403 in logs

**Cause**: Account lacks permissions for managed services (ROSA/ARO/OSD)

**Resolution**:
1. Contact Red Hat organization administrator
2. Request managed services access
3. Verify subscription includes ROSA/ARO/OSD
4. May need separate entitlements for managed services

---

#### Problem: OCM cluster details incomplete or missing fields

**Symptoms**:
- `ocm_cluster_info` returns partial data
- Missing fields: region, cloud_provider, console.url
- Some fields show as "Unknown"

**Cause**: OCM API response format varies by cluster state and configuration

**Explanation**:
- Some fields only available after cluster is fully provisioned
- Cloud provider details may be pending during cluster creation
- Console URL not available until cluster is installed

**Not an error**: This is expected behavior for clusters in early lifecycle stages.

---

### Differences Between Assisted Installer and OCM APIs

| Feature | Assisted Installer (OCP/SNO) | OCM (ROSA/ARO/OSD) |
|---------|------------------------------|-------------------|
| **Status Field** | `status` | `state` |
| **Events API** | ✅ Available | ❌ Not available |
| **Logs API** | ✅ Available | ❌ Use cloud provider tools |
| **VIP Configuration** | ✅ Required for HA | ❌ Handled by cloud |
| **Host Discovery** | ✅ Manual (boot from ISO) | ❌ Automated by cloud |
| **Installation Control** | ✅ Manual trigger | ❌ Automated |

**Key Difference**: Assisted Installer clusters require manual configuration and installation steps. OCM managed clusters are fully automated by Red Hat and cloud providers.

---

### OCM Cluster States

OCM uses different state values than Assisted Installer:

| OCM State | Meaning | Equivalent Assisted Installer Status |
|-----------|---------|--------------------------------------|
| `ready` | Cluster operational | `installed` |
| `installing` | Installation in progress | `installing` |
| `error` | Installation or operation failed | `error` |
| `pending` | Waiting for provisioning | `pending-for-input` |
| `hibernating` | Cluster scaled down to save costs | N/A (managed services only) |
| `resuming` | Waking from hibernation | N/A (managed services only) |

---

### Troubleshooting Workflow for Mixed Cluster Environments

When you have both self-managed (OCP/SNO) and managed (ROSA/ARO/OSD) clusters:

1. **List all clusters**: Use `cluster-inventory` skill
   - Automatically queries both APIs
   - Merges results into unified view

2. **If Assisted Installer clusters fail but OCM works**:
   - Check Assisted Installer API endpoint
   - Verify hosts are registered
   - Review cluster events (Assisted Installer only)

3. **If OCM clusters fail but Assisted Installer works**:
   - Verify managed services permissions
   - Check subscription entitlements
   - Contact Red Hat support for OCM access

4. **If both APIs fail**:
   - Verify OFFLINE_TOKEN is valid
   - Check network access to api.openshift.com
   - Regenerate token if expired

---

## Additional Resources

- **Official Documentation**: https://docs.openshift.com/container-platform/latest/installing/
- **Assisted Installer Console**: https://console.redhat.com/openshift/assisted-installer/clusters
- **OpenShift MCP Server**: https://github.com/openshift/openshift-mcp-server
- **Troubleshooting Guide**: https://docs.openshift.com/container-platform/latest/support/troubleshooting/

---

*This document is AI-optimized for consumption by language models assisting with OpenShift cluster management. Human administrators should refer to official Red Hat documentation for comprehensive guidance.*

---
title: VM Troubleshooting Guide - Index
category: kubevirt
sources:
  - title: KubeVirt User Guide - Node Placement
    url: https://kubevirt.io/user-guide/virtual_machines/node_placement/
    date_accessed: 2026-02-06
  - title: Kubernetes Taints and Tolerations
    url: https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
    date_accessed: 2026-02-06
  - title: OpenShift Virtualization - Virtual Machine Status
    url: https://docs.openshift.com/container-platform/latest/virt/virtual_machines/virt-managing-vms.html
    date_accessed: 2026-02-06
  - title: Kubernetes Finalizers
    url: https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/
    date_accessed: 2026-02-17
  - title: KubeVirt Virtual Machine Status Conditions
    url: https://kubevirt.io/user-guide/virtual_machines/vm_status_conditions/
    date_accessed: 2026-02-17
  - title: Multus CNI - Network Attachment Definitions
    url: https://github.com/k8snetworkplumbingwg/multus-cni
    date_accessed: 2026-02-17
tags: [troubleshooting, scheduling, taints, tolerations, errors, deletion, cloning, lifecycle, networking, crashloop, index, navigation]
semantic_keywords: [troubleshooting index, error categories, VM diagnostics, navigation hub]
use_cases: [vm-creation, vm-deletion, vm-cloning, vm-lifecycle, diagnostics, error-handling, network-troubleshooting]
last_updated: 2026-02-17
---

# VM Troubleshooting Guide - Index

## Overview

This guide provides comprehensive diagnostic procedures and workarounds for VirtualMachine errors and issues in OpenShift Virtualization. Use this document when VMs encounter problems during:

- **Creation**: Scheduling failures, storage provisioning issues
- **Lifecycle**: Start/stop failures, stuck states
- **Deletion**: Resources stuck in Terminating, storage cleanup failures
- **Cloning**: DataVolume cloning errors, cross-namespace issues
- **Networking**: Secondary network attachment failures
- **Runtime**: CrashLoopBackOff, guest OS boot failures

This guide is consulted by all rh-virt skills (vm-create, vm-inventory, vm-lifecycle-manager, vm-delete, vm-clone) when diagnosing and remediating VM issues.

---

## 🗂️ Troubleshooting Categories

The troubleshooting documentation is organized by error category for easier navigation and token optimization. Each category file contains MCP-first diagnostic procedures:

### 1. [Scheduling Errors](scheduling-errors.md)
**When to use**: VM fails to schedule on any node

**Errors covered**:
- ErrorUnschedulable - Node Taints
- ErrorUnschedulable - Insufficient Resources
- ErrorUnschedulable - Node Selector Mismatch

**Skills that use this**: vm-create, vm-lifecycle-manager

---

### 2. [Storage Errors](storage-errors.md)
**When to use**: VM has storage provisioning, deletion, or cloning issues

**Errors covered**:
- ErrorDataVolumeNotReady (all 3 subsections)
- ErrorPvcNotFound
- Storage Deletion Failures
- DataVolume Cloning Failures

**Skills that use this**: vm-create, vm-delete, vm-clone

---

### 3. [Lifecycle Errors](lifecycle-errors.md)
**When to use**: VM has start/stop/termination issues

**Errors covered**:
- VM Stuck in Terminating State
- VM Won't Start (Non-Scheduling Issues)
- VM Won't Stop

**Skills that use this**: vm-delete, vm-lifecycle-manager

---

### 4. [Runtime Errors](runtime-errors.md)
**When to use**: VM repeatedly crashes or fails at runtime

**Errors covered**:
- CrashLoopBackOff

**Skills that use this**: vm-create, vm-lifecycle-manager

---

### 5. [Network Errors](network-errors.md)
**When to use**: VM has secondary network attachment failures

**Errors covered**:
- Network Attachment Failures (Multus, SR-IOV)

**Skills that use this**: vm-create

---

## 🔧 How to Use This Guide: MCP Tools First, CLI Commands Last

### Critical Principle: MCP-First Approach

**All diagnostic procedures in this guide follow the MCP-first pattern**:

```
1. ✅ TRY: MCP Tool (resources_get, resources_list, etc.)
2. ⚠️ IF FAILS: Ask user permission to use CLI command
3. ❌ LAST RESORT: Execute CLI command (oc/kubectl) with explicit user approval
```

### Why MCP Tools First?

- **Structured Access**: MCP tools provide programmatic, type-safe access to cluster resources
- **Consistency**: Same interface across all operations
- **Better Error Handling**: MCP tools return structured errors
- **Audit Trail**: MCP tool usage is logged and trackable

### Command Pattern Examples

Throughout this guide, you'll see diagnostic steps formatted like this:

**✅ CORRECT Pattern (MCP First)**:

```markdown
**MCP Tool**: `resources_get` (from openshift-virtualization)

**Parameters**:
```json
{
  "apiVersion": "kubevirt.io/v1",
  "kind": "VirtualMachine",
  "namespace": "<namespace>",
  "name": "<vm-name>"
}
```

**Extract**: `.metadata.finalizers` from returned JSON

**CLI Fallback** (if MCP unavailable):
Ask user: "MCP tool unavailable. May I use `oc get vm` to check finalizers?"
```bash
oc get vm <vm-name> -n <namespace> -o jsonpath='{.metadata.finalizers}'
```
```

### Available MCP Tools

The `openshift-virtualization` MCP server provides these tools:

**Resource Operations**:
- `resources_get` - Get specific resource (replaces `oc get <resource> <name>`)
- `resources_list` - List resources (replaces `oc get <resource>`)
- `resources_delete` - Delete resource (replaces `oc delete`)
- `resources_create_or_update` - Create/update resource (replaces `oc apply` / `oc patch`)

**Pod Operations**:
- `pods_list_in_namespace` - List pods in namespace (replaces `oc get pods -n`)
- `pods_get` - Get pod details (replaces `oc get pod`)
- `pods_log` - Get pod logs (replaces `oc logs`)
- `pods_exec` - Execute in pod (replaces `oc exec`)
- `pods_delete` - Delete pod (replaces `oc delete pod`)
- `pods_top` - Pod resource usage (replaces `oc top pods`)

**Events & Monitoring**:
- `events_list` - List events (replaces `oc get events`)
- `nodes_top` - Node resource usage (replaces `oc top nodes`)
- `nodes_log` - Node logs (replaces `oc adm node-logs`)
- `nodes_stats_summary` - Detailed node stats

**VM Operations** (KubeVirt toolset):
- `vm_create` - Create VMs
- `vm_lifecycle` - Start/stop/restart VMs

**Namespaces**:
- `namespaces_list` - List namespaces (replaces `oc get namespaces`)
- `projects_list` - List OpenShift projects (replaces `oc get projects`)

### When CLI Commands Are Required

Some operations have **NO MCP equivalent** and require CLI:

- `virtctl` commands (console, VNC access)
- `oc debug node` (node debugging)
- `oc auth can-i` (permission checks)
- `oc adm taint` (node taint management)
- Complex JSON patch operations

For these, the guide will note: **"CLI Only - No MCP equivalent"**

### Quick Reference: CLI → MCP Mapping

| CLI Command | MCP Tool Equivalent |
|-------------|---------------------|
| `oc get vm <name> -n <ns>` | `resources_get` with apiVersion="kubevirt.io/v1", kind="VirtualMachine" |
| `oc get vms -n <ns>` | `resources_list` with apiVersion="kubevirt.io/v1", kind="VirtualMachine" |
| `oc delete vmi <name> -n <ns>` | `resources_delete` with kind="VirtualMachineInstance" |
| `oc get pods -n <ns>` | `pods_list_in_namespace` with namespace="<ns>" |
| `oc logs <pod> -n <ns>` | `pods_log` with name="<pod>", namespace="<ns>" |
| `oc get events -n <ns>` | `events_list` with namespace="<ns>" |
| `oc get nodes` | `resources_list` with apiVersion="v1", kind="Node" |

**Note**: The table above covers the most common patterns. For MCP tools specific to VM operations, see the "Available MCP Tools" section above, and consult the README for complete MCP server configuration.

### How to Read Diagnostic Sections

Each error section includes:
1. **Symptom** - What you observe
2. **Description** - What's happening
3. **Possible Causes** - Why it's happening
4. **Diagnostic Steps** - **MCP tools first**, then CLI fallback
5. **Solutions** - **MCP tools first**, then CLI fallback
6. **Verification** - **MCP tools first**, then CLI fallback

**Note**: Where CLI commands appear without MCP tool alternatives in older sections, they should be treated as **fallback only**. Skills should attempt MCP tools first, then request user permission before using CLI.

---

## 🔍 Quick Navigation by Skill

**vm-create**:
- [Scheduling Errors](scheduling-errors.md) - ErrorUnschedulable diagnostics
- [Storage Errors](storage-errors.md) - ErrorDataVolumeNotReady, storage provisioning
- [Runtime Errors](runtime-errors.md) - CrashLoopBackOff
- [Network Errors](network-errors.md) - Network attachment failures

**vm-delete**:
- [Lifecycle Errors](lifecycle-errors.md) - VM stuck in Terminating state
- [Storage Errors](storage-errors.md) - Storage deletion failures

**vm-clone**:
- [Storage Errors](storage-errors.md) - DataVolume cloning failures

**vm-lifecycle-manager**:
- [Lifecycle Errors](lifecycle-errors.md) - VM won't start/stop
- [Scheduling Errors](scheduling-errors.md) - VM won't start due to scheduling

**vm-inventory**:
- [INDEX.md](INDEX.md) - General guidance, consult specific categories as needed

---

## 📊 Documentation Coverage & Maintenance

### Current Coverage

This troubleshooting guide covers the most common VM errors encountered in OpenShift Virtualization:

- ✅ **Scheduling failures** - ErrorUnschedulable (3 root causes: node taints, insufficient resources, node selector mismatch)
- ✅ **Storage issues** - ErrorDataVolumeNotReady (3 scenarios), ErrorPvcNotFound, storage deletion failures, DataVolume cloning failures
- ✅ **Lifecycle problems** - VM stuck in Terminating state, VM won't start (non-scheduling), VM won't stop
- ✅ **Runtime crashes** - CrashLoopBackOff (kernel panic, QEMU crashes, OOM, guest OS failures)
- ✅ **Network attachment failures** - Multus NetworkAttachmentDefinition issues, SR-IOV problems

**Total errors documented**: 12 error types across 6 categories

---

### Encountering Undocumented Errors

#### For AI Agents (Claude Code)

If you encounter an error **not documented** in the categories above:

1. **Report to user** with all available details (error message, affected resources, namespace)
2. **Provide best-effort diagnostics** using MCP tools:
   - `resources_get` to inspect resource status
   - `pods_log` to check virt-launcher or compute container logs
   - `events_list` to view Kubernetes events
3. **Suggest documentation update**:
   ```
   ⚠️ This error is not yet documented in the troubleshooting guide.

   **Error**: <error-message>
   **Affected resource**: <resource-type>/<resource-name>

   I recommend adding this error to the troubleshooting guide:
   - If it's a [scheduling/storage/lifecycle/runtime/network] issue → Add to existing category file
   - If it's a new error class → Create new category file in docs/troubleshooting/

   Would you like me to help document this error for future reference?
   ```

4. **Do NOT make up solutions** - only provide factual diagnostics from MCP tool outputs

---

#### For Human Contributors

To document a new error:

1. **Determine the category**:
   - Scheduling issue → `scheduling-errors.md`
   - Storage problem → `storage-errors.md`
   - Lifecycle/start/stop → `lifecycle-errors.md`
   - Runtime crash → `runtime-errors.md`
   - Network issue → `network-errors.md`
   - New error class → Create new category file (e.g., `security-errors.md`)

2. **Follow the MCP-first pattern** (see "How to Use This Guide" above):
   - **Diagnostic Steps**: MCP Tool → Parameters → Extract → CLI Fallback
   - **Solutions**: MCP Tool approach → Implementation → CLI Fallback
   - **Verification**: MCP Tool checks → Expected results → CLI Fallback

3. **Update semantic index**:
   - Edit `.ai-index/semantic-index.json`
   - Add error to `error_to_docs_mapping`
   - Update relevant skill's `primary_docs` or `secondary_docs`
   - Increment token estimates if needed

4. **Reference in skill files**:
   - Update skill's Reference Documentation section
   - Ensure skill's Document Consultation steps point to the right category

5. **Update this INDEX.md**:
   - Add error to the appropriate category section (lines 50-120)
   - Update "Current Coverage" list above

---

## 📚 Additional Resources

- [rh-virt README](../../README.md) - MCP server setup and skill documentation
- [SOURCES.md](../SOURCES.md) - Official Red Hat documentation sources
- [Semantic Index](.ai-index/semantic-index.json) - AI-optimized doc discovery

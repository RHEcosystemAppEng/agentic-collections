---
name: cluster-inventory
description: |
  List and inspect ALL OpenShift cluster types with comprehensive status information.

  Supports both self-managed (OCP, SNO) and managed service clusters (ROSA, ARO, OSD).

  Use when:
  - "List all clusters"
  - "Show cluster status"
  - "What clusters are available?"
  - "Get details of cluster [name]"
  - "Show cluster events for diagnostics"

  Provides read-only cluster discovery and inspection. Does NOT perform cluster modifications.
model: inherit
color: blue

# AI Metadata
mcp_servers:
  - openshift-self-managed
  - openshift-ocm-managed
mcp_tools:
  - list_clusters
  - ocm_list_clusters
  - cluster_info
  - ocm_cluster_info
  - cluster_events
  - cluster_logs_download_url
environment_vars:
  - OFFLINE_TOKEN
  - INVENTORY_URL
  - OCM_URL
documentation:
  - ../../docs/troubleshooting.md
destructive: false
human_confirmation_required: false
related_skills: []
categories:
  - cluster-management
  - monitoring
  - diagnostics
---

# cluster-inventory

## Prerequisites

**Required MCP Servers**:
- `openshift-self-managed` - For self-managed clusters (OCP, SNO)
- `openshift-ocm-managed` - For managed service clusters (ROSA, ARO, OSD)

**Required MCP Tools**:
- `list_clusters` (from openshift-self-managed) - Lists self-managed clusters (OCP, SNO)
- `ocm_list_clusters` (from openshift-ocm-managed) - Lists managed service clusters (ROSA, ARO, OSD)
- `cluster_info` (from openshift-self-managed) - Details for self-managed clusters
- `ocm_cluster_info` (from openshift-ocm-managed) - Details for managed service clusters
- `cluster_events` (from openshift-self-managed) - Events for self-managed clusters (not available for OCM)

**Environment Variables**:
- `OFFLINE_TOKEN` - Red Hat authentication token (required)
- `OCM_URL` - OCM API endpoint (optional, defaults to https://api.openshift.com/api/clusters_mgmt/v1)

**Dual API Architecture**:
This skill queries TWO separate Red Hat APIs to provide comprehensive cluster coverage:
1. **Assisted Installer API** (`/api/assisted-install/v2`) - Self-managed clusters (OCP, SNO)
2. **OCM Clusters Management API** (`/api/clusters_mgmt/v1`) - Managed service clusters (ROSA, ARO, OSD)

Both APIs use the same `OFFLINE_TOKEN` for authentication.

**Verification Flow**:

```
START Prerequisites Check
  │
  ├─→ [1] Check .mcp.json for "openshift-self-managed" server
  │     ├─ FOUND → Continue to [2]
  │     └─ NOT FOUND → Report Error → Human Notification Protocol
  │
  ├─→ [2] Check OFFLINE_TOKEN environment variable
  │     ├─ SET (non-empty) → Continue to [3]
  │     └─ NOT SET → Report Error → Human Notification Protocol
  │
  ├─→ [3] Test MCP server connection (optional but recommended)
  │     ├─ SUCCESS → Proceed to Workflow Step 1
  │     └─ FAIL → Report Error → Human Notification Protocol
  │
END Prerequisites → Begin Execution
```

**Verification Steps** (Detailed):

1. **Check MCP Server Configuration**
   - Verify `openshift-self-managed` exists in `.mcp.json`
   - Confirm server uses Podman command (not HTTP type)
   - Check environment variable reference: `"OFFLINE_TOKEN": "${OFFLINE_TOKEN}"`
   - If missing → Proceed to Human Notification Protocol

2. **Check OFFLINE_TOKEN Environment Variable**
   - Verify token is set in shell environment
   - Do NOT expose token value in verification
   - If missing → Proceed to Human Notification Protocol

3. **Test MCP Server Connection** (optional but recommended)
   - Attempt `list_clusters` call to verify connectivity
   - If fails → Proceed to Human Notification Protocol

**Human Notification Protocol**:

```
IF Prerequisites Check FAILS at any step:
  THEN Execute the following protocol:

  STEP 1: Stop Execution Immediately
    - Do not attempt any MCP tool calls
    - Do not proceed to workflow steps

  STEP 2: Report Clear Error Message
    - Identify which prerequisite failed ([1], [2], or [3])
    - Display specific error for that failure (see templates below)
    - Include setup instructions
    - Provide documentation link

  STEP 3: Request User Decision
    - Present options: setup / skip / abort
    - Ask user to choose explicitly
    - Wait for user response (blocking)

  STEP 4: Act on User Decision
    - IF "setup" → Guide user through configuration
    - IF "skip" → Terminate skill gracefully
    - IF "abort" → Terminate entire workflow
    - ELSE → Re-prompt for valid choice
```

**Error Message Templates**:

1. **MCP Server Not Configured**:
   ```
   ❌ Cannot execute cluster-inventory: MCP server `openshift-self-managed` is not configured

   📋 Setup Instructions:
   1. Add openshift-self-managed to .mcp.json:
      {
        "mcpServers": {
          "openshift-self-managed": {
            "command": "podman",
            "args": [...],
            "env": {"OFFLINE_TOKEN": "${OFFLINE_TOKEN}"}
          }
        }
      }
   2. Restart Claude Code to reload MCP servers

   🔗 Documentation: https://github.com/openshift-assisted/assisted-service-mcp
   ```

2. **OFFLINE_TOKEN Not Set**:
   ```
   ❌ Cannot execute cluster-inventory: OFFLINE_TOKEN environment variable not set

   📋 Setup Instructions:
   1. Visit https://cloud.redhat.com/openshift/token
   2. Log in with your Red Hat account
   3. Copy the offline token
   4. Set environment variable:
      export OFFLINE_TOKEN="your-token-here"
   5. Verify: test -n "$OFFLINE_TOKEN" && echo "✓ Set" || echo "✗ Missing"

   🔗 Documentation: See README.md Environment Setup section
   ```

3. **Connection Failure**:
   ```
   ❌ Cannot connect to openshift-self-managed MCP server

   📋 Possible Causes:
   - OFFLINE_TOKEN is invalid or expired
   - Network issues accessing api.openshift.com
   - Podman container cannot start
   - Red Hat account lacks cluster permissions

   🔗 Troubleshooting: See docs/troubleshooting.md
   ```

4. **User Decision Prompt**:
   ```
   ❓ How would you like to proceed?

   Options:
   - "setup" - I'll help you configure the prerequisites now
   - "skip" - Skip this skill and try alternative approach
   - "abort" - Stop the workflow entirely

   Please respond with your choice.
   ```

**Error Message Templates**:

- Missing MCP Server:
  ```
  ❌ MCP server `openshift-self-managed` not configured in .mcp.json
  📋 Add server configuration to .mcp.json (see Prerequisites section above)
  ```

- Connection Failure:
  ```
  ❌ Cannot connect to `openshift-self-managed` MCP server at http://127.0.0.1:8000/mcp
  📋 Possible causes:
     - MCP server not running (verify server process)
     - Network issues (check http://127.0.0.1:8000/mcp is accessible)
     - Authentication issues (verify Red Hat Console credentials)
  ```

## When to Use This Skill

Use this skill when:
- User requests a list of all OpenShift clusters (any type)
- User wants to see cluster status or installation progress
- User needs detailed cluster information (version, configuration, hosts, cloud provider)
- User wants to inspect cluster events for troubleshooting
- User asks "What clusters do I have?" or "Show all my clusters"
- User wants to see both self-managed (OCP, SNO) AND managed service clusters (ROSA, ARO, OSD)

**Cluster Types Supported:**
- **Self-Managed**: OCP (OpenShift Container Platform), SNO (Single-Node OpenShift)
- **Managed Services**: ROSA (Red Hat OpenShift Service on AWS), ARO (Azure Red Hat OpenShift), OSD (OpenShift Dedicated)

Do NOT use when:
- User wants to create a new cluster → Use cluster-creator skill instead
- User wants to modify cluster configuration → Use appropriate cluster management skill
- User wants to install/start cluster installation → Use cluster-installer skill instead
- User wants to delete a cluster → Use cluster-deletion skill instead

---

## MCP Server Selection Logic

This skill uses **TWO MCP servers** depending on the cluster type:

| MCP Server | Cluster Types | When to Use |
|-----------|---------------|-------------|
| `openshift-self-managed` | OCP, SNO | Self-managed clusters via Assisted Installer |
| `openshift-ocm-managed` | ROSA, ARO, OSD | Managed service clusters via OCM API |

### Decision Matrix

**ALWAYS query BOTH servers** when:
- User asks generically: "List all clusters", "Show my clusters", "What clusters do I have?"
- No cluster type specified in request
- User wants comprehensive view of all clusters

**Query ONLY `openshift-self-managed`** when:
- User specifically mentions: "OCP clusters", "SNO clusters", "self-managed clusters"
- User mentions: "Assisted Installer", "baremetal", "vSphere", "Nutanix"
- User asks about cluster installation, VIPs, or host discovery (these concepts only apply to self-managed)

**Query ONLY `openshift-ocm-managed`** when:
- User specifically mentions: "ROSA", "ARO", "OSD", "managed clusters"
- User mentions: "AWS managed", "Azure managed", "cloud service"
- User asks about cloud provider regions, managed services

### Examples

| User Request | Query Strategy | Reasoning |
|-------------|----------------|-----------|
| "List all my clusters" | **Both servers** | Generic request |
| "Show me my OCP clusters" | **Self-managed only** | Specific to OCP |
| "What ROSA clusters do I have?" | **OCM-managed only** | Specific to ROSA |
| "List clusters in AWS" | **Both servers** | Could be OCP on AWS or ROSA |
| "Show clusters needing VIPs" | **Self-managed only** | VIPs only for self-managed |

**Default Behavior**: When in doubt, query **both servers** and merge results.

---

## Output Formatting Rules

### Summary Header (All Cases)

**ALWAYS display a summary header first**, regardless of cluster count:

```
📊 Found {total} cluster(s): {installed_count} installed ✅, {installing_count} installing ⏳, {pending_count} pending ⚠️, {error_count} error ❌
```

**Color Coding for Summary**:
- Total count: **Bold white**
- Installed count: **Green**
- Installing count: **Yellow**
- Pending count: **Orange/Yellow**
- Error count: **Red**

**Example**:
```
📊 Found 5 cluster(s): 2 installed ✅, 1 installing ⏳, 1 pending ⚠️, 1 error ❌
```

---

### Detailed List Format (1-2 Clusters)

When there are **1 or 2 clusters**, display each cluster as a **detailed bullet list**:

```
{status_icon} **{cluster_name}** ({cluster_type})
   • ID: {cluster_id}
   • Version: OpenShift {version}
   • Platform: {platform_name}
   • Status: {status_description}
   • Created: {creation_timestamp}
   • Hosts: {ready_hosts}/{total_hosts} ready
   • Next Steps: {context_aware_suggestion}
```

**Status Icons**:
- ✅ = `installed` or `ready`
- ⏳ = `installing` or `finalizing`
- ⚠️ = `pending-for-input` or `insufficient`
- ❌ = `error`

**Color Coding**:
- Cluster name: **Bold + status color** (green/yellow/orange/red)
- Property labels (ID, Version, etc.): **Dim/gray**
- Property values: **White/default**
- Next Steps: **Bold + appropriate color** (cyan for actions, green for success states)

**Example**:
```
✅ **test-sno** (Single-Node OpenShift)
   • ID: 6c814687-1a27-4bc4-8443-c4fbc994f1a0
   • Version: OpenShift 4.21.0
   • Platform: Baremetal (none)
   • Status: Installed
   • Created: 2024-02-10 14:23:15
   • Hosts: 1/1 ready
   • Next Steps: Download credentials or access console
```

---

### Table Format (3+ Clusters)

When there are **3 or more clusters**, display results in a **table format**:

**Table Columns** (always show all columns unless user specifies otherwise):
1. **Status** - Icon + color-coded status
2. **Name** - Cluster name
3. **Type** - OCP/ROSA/ARO/OSD/SNO
4. **Version** - OpenShift version (short format: 4.21.0)
5. **Platform** - Baremetal/vSphere/AWS/Azure/None
6. **Hosts** - Ready/Total format (e.g., 3/3)
7. **Created** - Creation date (YYYY-MM-DD)
8. **Next Steps** - Context-aware suggestion

**Sorting Order** (Type-first):
1. **Primary sort**: By Type (OCP → ROSA → ARO → OSD → SNO → Other)
2. **Secondary sort**: Within same type, by creation date (newest first)

**Table Format**:
```markdown
| Status | Name | Type | Version | Platform | Hosts | Created | Next Steps |
|--------|------|------|---------|----------|-------|---------|------------|
| {icon} | {name} | {type} | {ver} | {platform} | {H/T} | {date} | {suggestion} |
```

**Color Coding in Table**:
- **Status column**: Icon + color-coded status text
  - ✅ Installed (green)
  - ⏳ Installing (yellow)
  - ⚠️ Pending (orange)
  - ❌ Error (red)
- **Name column**: Bold white
- **Type column**: Cyan for managed services (ROSA/ARO/OSD), white for self-managed (OCP/SNO)
- **Version column**: Dim/gray
- **Platform column**: Default white
- **Hosts column**: Green if all ready, yellow if partial, red if none
- **Created column**: Dim/gray
- **Next Steps column**: Bold cyan (actionable items) or dim gray (informational)

**Example Table**:
```markdown
| Status | Name | Type | Version | Platform | Hosts | Created | Next Steps |
|--------|------|------|---------|----------|-------|---------|------------|
| ❌ | prod-cluster | OCP | 4.20.0 | vSphere | 0/3 | 2024-02-12 | Check events and logs |
| ⏳ | staging-ocp | OCP | 4.21.0 | Baremetal | 3/3 | 2024-02-11 | Monitor (65% complete) |
| ✅ | dev-cluster | OCP | 4.20.5 | AWS | 5/5 | 2024-02-09 | Operational |
| ⚠️ | edge-01 | SNO | 4.21.0 | None | 1/1 | 2024-02-10 | Configure networking |
| ✅ | rosa-prod | ROSA | 4.21.0 | AWS | 3/6 | 2024-02-08 | Operational |
```

---

### Platform Type Detection

**Determine cluster type from available metadata**:

**For OCM Clusters** (from `ocm_list_clusters`):

1. **Check `cloud_provider.id` field**:
   - `aws` → **ROSA** (Red Hat OpenShift Service on AWS)
   - `azure` → **ARO** (Azure Red Hat OpenShift)
   - `gcp` or other → **OSD** (OpenShift Dedicated)

2. **Platform Name**: Use `cloud_provider.id` directly (AWS, Azure, GCP)

**For Assisted Installer Clusters** (from `list_clusters`):

1. **Check `product_id` or `cloud_provider` field** (if available from MCP tool):
   - `rosa` → **ROSA** (Red Hat OpenShift Service on AWS)
   - `aro` → **ARO** (Azure Red Hat OpenShift)
   - `osd` → **OSD** (OpenShift Dedicated)

2. **Check `platform` field**:
   - `none` + single_node=true → **SNO** (Single-Node OpenShift)
   - `baremetal` / `vsphere` / `nutanix` / `oci` → **OCP** (OpenShift Container Platform)

3. **Fallback**:
   - If single_node=true → **SNO**
   - Else → **OCP**

**Platform Name Mapping**:
- `baremetal` → "Baremetal"
- `vsphere` → "vSphere"
- `nutanix` → "Nutanix"
- `oci` → "Oracle Cloud"
- `none` → "None" (for SNO)
- `aws` → "AWS"
- `azure` → "Azure"
- `gcp` → "GCP"
- `gcp` → "Google Cloud"

---

### Smart "Next Steps" Suggestions

**Generate context-aware suggestions based on cluster status**:

| Status | Next Steps Suggestion |
|--------|----------------------|
| `error` | "Check events and logs" |
| `insufficient` | "Boot hosts from ISO" or "Add {N} more hosts" |
| `pending-for-input` | "Configure VIPs" or "Set network configuration" or "Assign host roles" |
| `ready` | "Start installation" |
| `installing` | "Monitor progress ({percentage}% complete)" |
| `finalizing` | "Monitor progress (finalizing)" |
| `installed` | "Download credentials" or "Operational" |

**Additional Context**:
- If hosts = 0/N → "Boot {N} hosts from ISO"
- If VIPs missing (HA cluster) → "Configure API and Ingress VIPs"
- If installed → "Operational" or "Access console at https://..."

---

### Color Code Reference

**ANSI Color Codes** (use if terminal supports, else fallback to plain text):
- **Red** (errors): `\033[31m` / `\033[91m` (bright red)
- **Green** (success): `\033[32m` / `\033[92m` (bright green)
- **Yellow** (warning/progress): `\033[33m` / `\033[93m` (bright yellow)
- **Orange** (pending): `\033[33m` (yellow, closest to orange)
- **Cyan** (actions): `\033[36m` / `\033[96m` (bright cyan)
- **Dim/Gray** (secondary info): `\033[2m` or `\033[90m`
- **Bold**: `\033[1m`
- **Reset**: `\033[0m`

**Markdown Color Fallback**:
If ANSI codes aren't supported, use emoji and Markdown emphasis:
- ✅ **Installed** (bold green equivalent)
- ⏳ *Installing* (italic yellow equivalent)
- ⚠️ **Pending** (bold orange equivalent)
- ❌ **Error** (bold red equivalent)

---

### User Override Rules

**User can override default formatting** by specifying:
- "Show only name and status" → Display minimal table/list
- "Don't show the table" → Force detailed list format
- "Sort by date" → Override type-first sorting
- "Sort by status" → Sort by status instead of type
- "Show more details for [cluster-name]" → Trigger Step 2 (detailed cluster info)

**Always respect user preferences** when explicitly stated.

## Workflow

### Step 1: List All Clusters (Dual API Query)

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [troubleshooting.md](../../docs/troubleshooting.md) using the Read tool to understand common cluster status values and error conditions
2. **Output to user**: "I consulted [troubleshooting.md](../../docs/troubleshooting.md) to understand cluster status interpretation."

**Dual API Query Process**:

This step queries TWO separate APIs and merges results:

**Step 1A: Query Assisted Installer API**

**MCP Server**: `openshift-self-managed`
**MCP Tool**: `list_clusters`

**Parameters**: None required

**Expected Output**: List of self-managed clusters (OCP, SNO) with:
- Cluster name
- Cluster ID (UUID)
- OpenShift version
- Status (ready, installing, pending-for-input, error, etc.)

**Step 1B: Query OCM Clusters Management API**

**MCP Server**: `openshift-ocm-managed`
**MCP Tool**: `ocm_list_clusters`

**Parameters**: None required

**Expected Output**: List of managed service clusters (ROSA, ARO, OSD) with:
- Cluster name
- Cluster ID (UUID)
- OpenShift version
- State (ready, installing, error, etc.)
- Cloud provider (AWS, Azure, GCP)
- Region

**Step 1C: Merge and Normalize Results**

**Merge Process**:
1. Parse Assisted Installer clusters → Add `source: "assisted-installer"` and `type: "OCP"` or `type: "SNO"`
2. Parse OCM clusters → Add `source: "ocm"` and detect type from cloud_provider:
   - AWS → `type: "ROSA"`
   - Azure → `type: "ARO"`
   - GCP or other → `type: "OSD"`
3. Normalize field names:
   - OCM `state` → `status` for consistency
   - OCM `version.raw_id` → `openshift_version`
4. Combine both lists into single array
5. Sort by Type-first (OCP → ROSA → ARO → OSD → SNO), then by creation date

**Error Handling**:
- If BOTH tools return "No clusters found": Report "No clusters found in either Assisted Installer or OCM."
- If ONE tool fails but other succeeds: Report partial results with note about which API failed
- If BOTH tools fail: Guide user to verify credentials and MCP server connectivity
- If authentication error: Guide user to verify OFFLINE_TOKEN

**Output Format**:

Follow the **Output Formatting Rules** section above:
1. **ALWAYS** display summary header first (include counts from both sources)
2. **1-2 clusters**: Use detailed bullet list format
3. **3+ clusters**: Use table format with all columns
4. Apply color coding and status icons
5. Sort by Type-first (OCP → ROSA → ARO → OSD → SNO), then by creation date
6. Include smart "Next Steps" suggestions

**Summary Header Format**:
```
📊 Found {total} cluster(s): {self_managed_count} self-managed (OCP/SNO), {managed_count} managed (ROSA/ARO/OSD)
   Status: {installed_count} installed ✅, {installing_count} installing ⏳, {pending_count} pending ⚠️, {error_count} error ❌
```

See "Output Formatting Rules" section for complete specifications.

### Step 2: Get Detailed Cluster Information (Optional)

This step is executed when:
- User explicitly requests details for a specific cluster
- User asks follow-up questions about a cluster after listing
- Cluster status indicates issues requiring investigation

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [troubleshooting.md](../../docs/troubleshooting.md) using the Read tool to understand cluster configuration and network settings
2. **Output to user**: "I consulted [troubleshooting.md](../../docs/troubleshooting.md) to understand cluster configuration details."

**Cluster Type Detection**:

Before calling the appropriate tool, determine cluster type from Step 1 results:

1. **Check `source` field** from merged results:
   - If `source: "ocm"` → Use `ocm_cluster_info` tool (Step 2B)
   - If `source: "assisted-installer"` → Use `cluster_info` tool (Step 2A)

2. **Fallback detection** (if source field not available):
   - Check for OCM-specific fields: `cloud_provider`, `region`, `console.url`
   - If present → OCM cluster → Use `ocm_cluster_info`
   - If absent → Assisted Installer cluster → Use `cluster_info`

**Step 2A: Get Assisted Installer Cluster Details**

**MCP Server**: `openshift-self-managed`
**MCP Tool**: `cluster_info`

**Parameters**:
- `cluster_id`: "[cluster-uuid]" (exact UUID from list_clusters output)
  - Example: `"762df996-acba-4a42-9fe9-edb0a8ec8bee"`
  - Must be valid UUID format

**Expected Output**: Comprehensive cluster information including:
- Cluster name, ID, and OpenShift version
- Installation status and progress
- Network configuration (VIPs, subnets, DNS)
- Host information (discovered hosts, roles, status)
- Validation results

**Output Format**:
```
**Cluster Details: [name]** (Self-Managed)

**Basic Information**:
- **Cluster ID**: [id]
- **OpenShift Version**: [version]
- **Status**: [status]
- **Base Domain**: [base_domain]

**Network Configuration**:
- **API VIP**: [api_vip or "Not configured"]
- **Ingress VIP**: [ingress_vip or "Not configured"]
- **Machine Network CIDR**: [cidr]
- **Cluster Network CIDR**: [cidr]
- **Service Network CIDR**: [cidr]

**Installation Progress**:
- **Overall Status**: [status_info]
- **Validations**: [validation_summary]

**Hosts**:
- [Host count and status summary]
```

**Error Handling**:
- If cluster_id not found: Verify cluster exists using list_clusters first
- If cluster_id format invalid: Ensure using exact UUID from list_clusters
- If permission denied: User may not have access to this cluster

**Step 2B: Get OCM Managed Cluster Details**

**MCP Server**: `openshift-ocm-managed`
**MCP Tool**: `ocm_cluster_info`

**Parameters**:
- `cluster_id`: "[cluster-uuid]" (exact UUID from ocm_list_clusters output)
  - Example: `"1a2b3c4d5e6f"`
  - Must be valid UUID format

**Expected Output**: Comprehensive OCM cluster information including:
- Cluster name, ID, and state
- OpenShift version
- Cloud provider and region
- API and console URLs
- Node information

**Output Format**:
```
**Cluster Details: [name]** (Managed Service - [ROSA/ARO/OSD])

**Basic Information**:
- **Cluster ID**: [id]
- **State**: [state]
- **OpenShift Version**: [version.raw_id]
- **Created**: [creation_timestamp]

**Cloud Configuration**:
- **Cloud Provider**: [cloud_provider.id]
- **Region**: [region.id]
- **Multi-AZ**: [multi_az]

**Access**:
- **API URL**: [api.url]
- **Console URL**: [console.url]

**Node Information**:
- **Compute nodes**: [nodes.compute]
- **Compute machine type**: [nodes.compute_machine_type.id]
```

**Error Handling**:
- If cluster_id not found: Verify cluster exists using ocm_list_clusters first
- If cluster_id format invalid: Ensure using exact UUID from ocm_list_clusters
- If permission denied: User may not have access to this OCM cluster

### Step 3: Get Cluster Events (Optional - Assisted Installer Clusters Only)

**NOTE**: This step is ONLY available for Assisted Installer clusters (OCP, SNO). OCM managed clusters (ROSA, ARO, OSD) use different monitoring and event systems accessible through their respective cloud provider consoles.

This step is executed when:
- User explicitly requests cluster events
- Cluster status indicates errors requiring investigation
- User asks "What happened to cluster X?"
- Troubleshooting installation or configuration issues
- **Cluster is from Assisted Installer** (not OCM)

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [troubleshooting.md](../../docs/troubleshooting.md) using the Read tool to understand event interpretation and common error patterns
2. **Output to user**: "I consulted [troubleshooting.md](../../docs/troubleshooting.md) to understand cluster event patterns."

**MCP Server**: `openshift-self-managed`
**MCP Tool**: `cluster_events`

**Parameters**:
- `cluster_id`: "[cluster-uuid]" (exact UUID from list_clusters output)
  - Example: `"762df996-acba-4a42-9fe9-edb0a8ec8bee"`
  - Must be valid UUID format

**Expected Output**: Chronological list of cluster events including:
- Timestamps
- Event severity (info, warning, error)
- Event messages and descriptions
- Configuration changes
- Validation results

**Error Handling**:
- If cluster_id not found: Verify cluster exists first
- If no events available: Report that cluster has no event history yet
- If permission denied: User may not have access to cluster events

**Output Format**:
```
**Cluster Events for [cluster_name]**:

[Timestamp] [Severity] [Event Message]
[Timestamp] [Severity] [Event Message]
...

**Summary**:
- Total events: X
- Errors: Y
- Warnings: Z
- Most recent: [latest event summary]
```

### Step 4: Get Cluster Logs (Optional - Assisted Installer Clusters Only)

**NOTE**: This step is ONLY available for Assisted Installer clusters (OCP, SNO). OCM managed clusters (ROSA, ARO, OSD) have their own logging systems accessible through OpenShift Console or cloud provider tools.

This step is executed when:
- Cluster status is "error"
- User explicitly requests logs for detailed diagnosis
- Cluster events don't provide sufficient diagnostic information
- Deep troubleshooting of installation or configuration failures required
- User asks "Can I get the logs?" or "Where are the cluster logs?"
- **Cluster is from Assisted Installer** (not OCM)

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [troubleshooting.md](../../docs/troubleshooting.md) using the Read tool to understand log analysis and common error patterns
2. **Output to user**: "I consulted [troubleshooting.md](../../docs/troubleshooting.md) to understand cluster log diagnostics."

**MCP Server**: `openshift-self-managed`
**MCP Tool**: `cluster_logs_download_url`

**Parameters**:
- `cluster_id`: "[cluster-uuid]" (exact UUID from list_clusters output)
  - Example: `"762df996-acba-4a42-9fe9-edb0a8ec8bee"`
  - Must be valid UUID format

**Expected Output**: Presigned download URL for cluster logs bundle including:
- Installation logs
- Validation logs
- Host discovery and configuration logs
- System diagnostics
- Error stack traces

**Error Handling**:
- If cluster_id not found: Verify cluster exists first
- If logs not available yet: Report that cluster has no logs (may be too early in lifecycle)
- If permission denied: User may not have access to cluster logs
- If URL generation fails: Cluster may not have completed enough lifecycle steps to generate logs

**Output Format**:
```
**Cluster Logs Available for [cluster_name]**:

**Download URL**: [presigned-url]
**Expiration**: [timestamp if provided, or "Time-limited URL"]
**Log Bundle Contents**:
- Installation logs (all phases)
- Validation and preflight check logs
- Host discovery and registration logs
- System diagnostics and stack traces
- Network configuration logs

**Instructions**:
1. Download the logs bundle from the URL above
2. Extract the archive (typically .tar.gz format)
3. Review logs in chronological order
4. Focus on ERROR and FATAL level messages
5. Cross-reference with cluster events for context

**Note**: Download URL is time-limited for security. Download promptly.
```

**When to Skip This Step**:
- Cluster status is "ready", "installing", "finalizing", or "installed" (logs not typically needed)
- User only wants quick status check
- Cluster events provide sufficient diagnostic information

## Dependencies

### Required MCP Servers
- `openshift-self-managed` - Red Hat Assisted Installer service for self-managed clusters
- `openshift-ocm-managed` - Red Hat OCM (OpenShift Cluster Manager) service for managed clusters

### Required MCP Tools
**For Self-Managed Clusters (OCP, SNO)** - from `openshift-self-managed`:
- `list_clusters` - List Assisted Installer clusters
- `cluster_info` - Get detailed cluster information
- `cluster_events` - Retrieve cluster event history
- `cluster_logs_download_url` - Get cluster logs download URL for diagnostics

**For Managed Service Clusters (ROSA, ARO, OSD)** - from `openshift-ocm-managed`:
- `ocm_list_clusters` - List OCM managed clusters
- `ocm_cluster_info` - Get detailed OCM cluster information

### Related Skills
None currently. This is a foundational skill for cluster discovery.

Future related skills may include:
- `cluster-creator` - Create new OpenShift clusters
- `cluster-installer` - Install and configure clusters
- `cluster-deletion` - Remove clusters

### Reference Documentation
- [troubleshooting.md](../../docs/troubleshooting.md) - Cluster status interpretation and error diagnosis

## Example Usage

### Example 1: List All Clusters (1-2 Clusters)

**User Query**: "List all my OpenShift clusters"

**Skill Execution**:
1. Read troubleshooting.md for cluster status interpretation
2. Invoke `list_clusters` tool
3. Count clusters and apply formatting rules
4. Display with detailed list format (1-2 clusters)

**Output**:
```
I consulted troubleshooting.md to understand cluster status interpretation.

📊 Found 2 cluster(s): 1 ready ✅, 1 pending ⚠️

✅ **production-ocp** (OpenShift Container Platform)
   • ID: 762df996-acba-4a42-9fe9-edb0a8ec8bee
   • Version: OpenShift 4.21.0
   • Platform: Baremetal
   • Status: Ready for installation
   • Created: 2024-02-10 10:30:00
   • Hosts: 3/3 ready
   • Next Steps: Start installation

⚠️ **test-cluster** (Single-Node OpenShift)
   • ID: abc12345-1234-5678-9abc-def012345678
   • Version: OpenShift 4.20.5
   • Platform: None
   • Status: Pending for input
   • Created: 2024-02-09 15:45:00
   • Hosts: 1/1 ready
   • Next Steps: Configure networking
```

### Example 1b: List All Clusters (3+ Clusters - Dual API Query)

**User Query**: "List all my OpenShift clusters"

**Skill Execution**:
1. Read troubleshooting.md for cluster status interpretation
2. Invoke `list_clusters` tool (Assisted Installer API) → Gets OCP/SNO clusters
3. Invoke `ocm_list_clusters` tool (OCM API) → Gets ROSA/ARO/OSD clusters
4. Merge and normalize results (5 total clusters)
5. Sort by Type-first (OCP → ROSA → ARO → OSD → SNO), then creation date
6. Display with table format (3+ clusters)

**Output**:
```
I consulted troubleshooting.md to understand cluster status interpretation.

📊 Found 5 cluster(s): 3 self-managed (OCP/SNO), 2 managed (ROSA/ARO/OSD)
   Status: 3 installed ✅, 1 installing ⏳, 1 pending ⚠️, 0 error ❌

| Status | Name | Type | Version | Platform | Hosts | Created | Next Steps |
|--------|------|------|---------|----------|-------|---------|------------|
| ⏳ | staging-ocp | OCP | 4.21.0 | Baremetal | 3/3 | 2024-02-12 | Monitor (65% complete) |
| ✅ | dev-cluster | OCP | 4.20.5 | vSphere | 3/3 | 2024-02-11 | Operational |
| ✅ | rosa-prod | ROSA | 4.21.0 | AWS | 6/6 | 2024-02-10 | Operational |
| ✅ | aro-dev | ARO | 4.20.0 | Azure | 3/3 | 2024-02-09 | Operational |
| ⚠️ | edge-01 | SNO | 4.21.0 | None | 1/1 | 2024-02-08 | Configure networking |
```

### Example 2: Get Detailed Cluster Information

**User Query**: "Show me details for the test cluster"

**Skill Execution**:
1. List clusters to find cluster ID
2. Read troubleshooting.md for configuration details
3. Invoke `cluster_info` with cluster_id
4. Format comprehensive output

**Output**:
```
I consulted troubleshooting.md to understand cluster configuration details.

**Cluster Details: test**

**Basic Information**:
- **Cluster ID**: 762df996-acba-4a42-9fe9-edb0a8ec8bee
- **OpenShift Version**: 4.21.0
- **Status**: pending-for-input
- **Base Domain**: example.com

**Network Configuration**:
- **API VIP**: Not configured
- **Ingress VIP**: Not configured
- **Machine Network CIDR**: 192.168.1.0/24

**Installation Progress**:
- **Overall Status**: Waiting for network configuration
- **Validations**: Network VIPs required for installation

**Hosts**:
- 0 hosts discovered
- Waiting for hosts to boot from ISO
```

### Example 3: Investigate Cluster Issues

**User Query**: "What's wrong with my cluster? Show me the events"

**Skill Execution**:
1. List clusters to identify cluster
2. Read troubleshooting.md for event interpretation
3. Invoke `cluster_events` with cluster_id
4. Analyze and summarize events

**Output**:
```
I consulted troubleshooting.md to understand cluster event patterns.

**Cluster Events for test**:

2024-02-10 14:23:15 INFO Cluster created successfully
2024-02-10 14:23:20 WARNING Network VIPs not configured
2024-02-10 14:25:00 INFO Cluster validation started
2024-02-10 14:25:05 ERROR Network configuration incomplete - cannot proceed with installation

**Summary**:
- Total events: 4
- Errors: 1
- Warnings: 1
- Most recent: Network configuration incomplete

**Recommendation**: Configure API and Ingress VIPs before proceeding with installation.
```

### Example 4: Deep Troubleshooting with Logs

**User Query**: "My cluster installation failed. Can I get the logs?"

**Skill Execution**:
1. List clusters to identify cluster
2. Check cluster status (shows "error")
3. Read troubleshooting.md for log diagnostics guidance
4. Invoke `cluster_logs_download_url` with cluster_id
5. Provide download URL and instructions

**Output**:
```
I consulted troubleshooting.md to understand cluster log diagnostics.

**Cluster Logs Available for production-cluster**:

**Download URL**: https://api.openshift.com/api/assisted-install/v2/clusters/abc-123/downloads/logs?expires=2024-02-11T12:00:00Z
**Expiration**: 2024-02-11 12:00:00 UTC (Time-limited URL)
**Log Bundle Contents**:
- Installation logs (all phases)
- Validation and preflight check logs
- Host discovery and registration logs
- System diagnostics and stack traces
- Network configuration logs

**Instructions**:
1. Download the logs bundle from the URL above
2. Extract the archive (typically .tar.gz format)
3. Review logs in chronological order
4. Focus on ERROR and FATAL level messages
5. Cross-reference with cluster events for context

**Note**: Download URL is time-limited for security. Download promptly.
```

---
name: fleet-inventory
description: |
  Query and display Red Hat Lightspeed managed system inventory. Use this skill for information-gathering requests about the fleet, registered systems, or inventory queries. This skill focuses on discovery and listing only - for remediation actions, transition to the `/remediation` skill.

  **When to use this skill**:
  - "Show the managed fleet"
  - "List all systems registered in Lightspeed"
  - "What systems are affected by CVE-X?"
  - "How many RHEL 8 systems do we have?"
  - "Show me production systems"

  **When NOT to use this skill** (use `/remediation` skill instead):
  - "Remediate CVE-X on these systems"
  - "Create a playbook for..."
  - "Patch system Y"

  This skill orchestrates MCP tools from lightspeed-mcp to provide comprehensive fleet visibility and system inventory management.
model: inherit
color: blue
---

# Fleet Inventory Skill

This skill queries Red Hat Lightspeed to retrieve and display information about managed systems, registered hosts, and fleet inventory.

## Prerequisites

**Required MCP Servers**: `lightspeed-mcp` ([setup guide](https://console.redhat.com/))

**Required MCP Tools**:
- `get_host_details` (from lightspeed-mcp) - Retrieve system inventory
- `get_cve_systems` (from lightspeed-mcp) - Find CVE-affected systems

**Required Environment Variables**:
- `LIGHTSPEED_CLIENT_ID` - Red Hat Lightspeed service account client ID
- `LIGHTSPEED_CLIENT_SECRET` - Red Hat Lightspeed service account secret

### Prerequisite Validation

**CRITICAL**: Before executing any operations, execute the `/mcp-lightspeed-validator` skill to verify MCP server availability.

See **Step 0** in the Workflow section below for implementation details.

**Validation freshness**: Can skip if already validated in this session. See [Validation Freshness Policy](../mcp-lightspeed-validator/SKILL.md#validation-freshness-policy).

## When to Use This Skill

**Use this skill directly when you need**:
- List all systems registered in Red Hat Lightspeed
- Show systems affected by specific CVEs
- Display system details (OS version, tags, last check-in)
- Filter systems by environment, RHEL version, or tags
- Count systems matching criteria
- Verify system registration status

**Use the `/remediation` skill when you need**:
- Remediate vulnerabilities on systems
- Generate or execute playbooks
- Perform infrastructure changes
- End-to-end CVE remediation workflows

**How they work together**: Use this skill for discovery ("What systems are affected?"), then transition to the `/remediation` skill for action ("Remediate those systems").

## Workflow

### Step 0: Validate Lightspeed MCP Prerequisites

**Action**: Execute the `/mcp-lightspeed-validator` skill

**Note**: Can skip if validation was performed earlier in this session and succeeded. See [Validation Freshness Policy](../mcp-lightspeed-validator/SKILL.md#validation-freshness-policy).

**How to invoke**: Execute the `/mcp-lightspeed-validator` skill

**Handle validation result**:
- **If validation PASSED**: Continue to Step 1
- **If validation PARTIAL** (connectivity test unavailable):
  - Warn user: "Configuration appears correct but connectivity could not be tested"
  - Ask: "Do you want to proceed? (yes/no)"
  - If yes: Continue to Step 1
  - If no: Stop execution
- **If validation FAILED**:
  - The validator provides error details and setup instructions
  - Wait for user decision (setup/skip/abort)
  - If user chooses "skip": Attempt Step 1 anyway (may fail)
  - If user chooses "setup" or "abort": Stop execution

**Example**:
```
Before retrieving fleet inventory, I'll validate the Lightspeed MCP server configuration.

[Invoke mcp-lightspeed-validator skill]

✓ Lightspeed MCP validation successful.
Proceeding with fleet inventory query...
```

### Step 1: Retrieve System Inventory

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [insights-api.md](../../docs/insights/insights-api.md) using the Read tool to understand the `get_host_details` response format and pagination handling
2. **Output to user**: "I consulted [insights-api.md](../../docs/insights/insights-api.md) to understand the `get_host_details` response format and pagination handling."

**MCP Tool**: `get_host_details` (from lightspeed-mcp)

**Purpose**: Query Lightspeed for comprehensive system information

**Parameters** (based on user query):

```python
# For "Show the managed fleet" (no filters)
get_host_details()

# For "Show system abc-123" (specific system)
get_host_details(
    system_id="abc-123"
)

# For "Show web servers" (hostname pattern)
get_host_details(
    hostname_pattern="web-*"
)

# For "Show production systems" (tag filter)
get_host_details(
    tags=["production"]
)

# For "Show RHEL 8 systems" (version filter)
get_host_details(
    operating_system__version__startswith="8"
)

# Multiple filters combined
get_host_details(
    tags=["production", "web-tier"],
    operating_system__version__startswith="8"
)
```

**Expected Response**:
```json
{
  "systems": [
    {
      "id": "abc-def-123",
      "display_name": "web-server-01.example.com",
      "fqdn": "web-server-01.example.com",
      "rhel_version": "8.9",
      "last_seen": "2024-01-20T10:30:00Z",
      "tags": ["production", "web-tier"],
      "stale": false,
      "satellite_managed": false
    }
  ],
  "total": 42,
  "count": 10
}
```

**Verification Checklist**:
- ✓ Systems list returned with metadata
- ✓ Total count matches expectation
- ✓ System details include RHEL version, tags, status
- ✓ No authentication errors (401/403)

**Key Fields to Extract**:
- `id`: Unique system identifier (use for remediation workflows)
- `display_name` / `fqdn`: Human-readable hostname
- `rhel_version`: OS version (critical for remediation compatibility)
- `tags`: Environment labels (production, staging, dev)
- `stale`: Whether system recently checked in (< 7 days)
- `last_seen`: Last Lightspeed client run timestamp

### Step 2: Filter and Organize Systems

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [fleet-management.md](../../docs/insights/fleet-management.md) using the Read tool to understand fleet inventory reporting structure and best practices
2. **Output to user**: "I consulted [fleet-management.md](../../docs/insights/fleet-management.md) to structure this inventory report."

Apply user-requested filters and grouping:

**Filtering Examples**:

```python
# By RHEL Version
systems_rhel8 = [s for s in systems if s['rhel_version'].startswith("8")]
# Result: All RHEL 8.x systems

# By Environment Tag
production_systems = [s for s in systems if "production" in s.get('tags', [])]
# Result: Production systems only

# By Status (active vs stale)
active_systems = [s for s in systems if not s.get('stale', False)]
# Result: Active systems (checked in recently)

# By Hostname Pattern
web_servers = [s for s in systems if 'web-server' in s.get('fqdn', '')]
# Result: Web tier systems
```

**Sorting Options**:
```python
# By last check-in (most recent first)
sorted(systems, key=lambda s: s['last_seen'], reverse=True)

# By RHEL version (group by OS)
sorted(systems, key=lambda s: s['rhel_version'])

# By display name (alphabetical)
sorted(systems, key=lambda s: s['display_name'])

# By environment tag
sorted(systems, key=lambda s: s.get('tags', [''])[0])
```

### Step 3: Query CVE-Affected Systems

**MCP Tool**: `get_cve_systems` (from lightspeed-mcp)

**Purpose**: Find systems affected by specific CVEs

**Parameters** (exact specification):

```python
# For "What systems are affected by CVE-2024-1234?"
get_cve_systems(
    cve_id="CVE-2024-1234"  # Exact CVE ID from user query
)

# The cve_id parameter MUST:
# - Match format: CVE-YYYY-NNNNN
# - Be uppercase: CVE-2024-1234 (not cve-2024-1234)
# - Include full ID: CVE-2024-1234 (not 2024-1234)
```

**Expected Response**:
```json
{
  "cve_id": "CVE-2024-1234",
  "affected_systems": [
    {
      "system_id": "abc-def-123",
      "display_name": "web-server-01.example.com",
      "status": "Vulnerable",
      "remediation_available": true
    },
    {
      "system_id": "xyz-123-456",
      "display_name": "db-server-02.example.com",
      "status": "Vulnerable",
      "remediation_available": true
    }
  ],
  "total_affected": 15,
  "total_remediated": 3,
  "total_vulnerable": 12
}
```

**Verification Checklist**:
- ✓ CVE ID matches request exactly
- ✓ System list includes remediation status for each
- ✓ Counts are accurate (affected, remediated, still vulnerable)
- ✓ `remediation_available` flag is present

**Status Interpretation**:
```
Status: "Vulnerable"
→ CVE affects this system, patch not applied
→ Action: Suggest remediation via `/remediation` skill

Status: "Patched"
→ CVE previously affected, now remediated
→ Action: No action needed, informational only

Status: "Not Affected"
→ System not vulnerable to this CVE
→ Action: Exclude from affected count
```

### Step 4: Generate Fleet Summary

Create organized output based on query results:

**Summary Template**:
```markdown
# Fleet Inventory Summary

Retrieved from Red Hat Lightspeed on YYYY-MM-DDTHH:MM:SSZ

## Overview
**Total Systems**: <total_count>
**Active Systems**: <active_count> (last seen < 24 hours)
**Stale Systems**: <stale_count> (last seen > 7 days)

## By RHEL Version
- RHEL 9.x: <count> systems (<percentage>%)
- RHEL 8.x: <count> systems (<percentage>%)
- RHEL 7.x: <count> systems (<percentage>%)

## By Environment (Tags)
- Production: <count> systems
- Staging: <count> systems
- Development: <count> systems

## System Details

| Display Name | RHEL Version | Environment | Last Seen | Status |
|--------------|--------------|-------------|-----------|--------|
| [system details rows...]

## Stale Systems (Attention Required)
⚠️ The following systems have not checked in recently:
- [stale system list...]
```

### Step 5: Offer Remediation Transition

When appropriate, suggest transitioning to the `/remediation` skill:

```markdown
## Next Steps

**For CVE Remediation**:
If you need to remediate vulnerabilities on any of these systems, I can help using the `/remediation` skill:

Examples:
- "Remediate CVE-2024-1234 on web-server-01"
- "Create playbook for all RHEL 8 production systems affected by CVE-2024-5678"
- "Batch remediate critical CVEs on staging environment"

**For System Investigation**:
- "Show CVEs affecting web-server-01" (use cve-impact skill)
- "Analyze risk for production systems" (use cve-impact skill)
- "List critical vulnerabilities across the fleet" (use cve-impact skill)
```

## Dependencies

### Required MCP Servers
- `lightspeed-mcp` - Red Hat Lightspeed platform access for system inventory and CVE data

### Required MCP Tools
- `get_host_details` (from lightspeed-mcp) - Retrieve all registered systems with metadata
  - Parameters: Optional filters (system_id, hostname_pattern, tags, operating_system)
  - Returns: List of systems with id, display_name, fqdn, rhel_version, tags, stale status

- `get_cve_systems` (from lightspeed-mcp) - Find systems affected by specific CVEs
  - Parameters: cve_id (string, format: CVE-YYYY-NNNNN)
  - Returns: List of affected systems with vulnerability and remediation status

### Related Skills
- `mcp-lightspeed-validator` - **PREREQUISITE** - Validates Lightspeed MCP server configuration and connectivity
  - Use before: ALL fleet-inventory operations (Step 0 in workflow)
  - Purpose: Ensures MCP server is available before attempting tool calls
  - Prevents errors from missing configuration or credentials

- `cve-impact` - Analyze CVE severity and risk after identifying affected systems
  - Use after: "What systems are affected by CVE-X?" → "What's the risk of CVE-X?"

- `cve-validation` - Validate CVE IDs before querying affected systems
  - Use before: If CVE ID format is unclear, validate first

- `system-context` - Get detailed system configuration for specific hosts
  - Use after: Fleet discovery identifies systems needing deeper investigation

- `/remediation` (skill) - Transition to remediation workflows after discovery
  - Use after: "Show affected systems" → "Remediate those systems"

### Reference Documentation
- [insights-api.md](../../docs/insights/insights-api.md) - Red Hat Lightspeed API patterns and response formats
- [fleet-management.md](../../docs/insights/fleet-management.md) - System inventory best practices and filtering strategies

### Skill Orchestration Pattern

**Information-First Workflow**:
```
User Query: "Show the managed fleet"
    ↓
fleet-inventory skill (discovery)
    ↓
Systems identified: 42 total, 15 affected by CVE-2024-1234
    ↓
User: "What's the risk of CVE-2024-1234?"
    ↓
cve-impact skill (analysis)
    ↓
CVSS 8.1, Critical severity, affects httpd package
    ↓
User: "Remediate CVE-2024-1234 on all production systems"
    ↓
`/remediation` skill (action)
    ↓
Playbook generated and executed
```

**Key Principle**: Always start with discovery before taking remediation actions. This ensures informed decisions based on actual fleet state.

## Output Templates

### Template 1: Full Fleet Listing

**User Request**: "Show the managed fleet"

**Skill Response**:
```markdown
# Managed Fleet Inventory

I consulted [fleet-management.md](../../docs/insights/fleet-management.md) to structure this inventory report.

Retrieved from Red Hat Lightspeed on 2024-01-20T10:30:00Z

## Fleet Overview
- **Total Registered Systems**: 42
- **Active (< 24h)**: 38
- **Stale (> 7 days)**: 4

## RHEL Version Distribution
| Version | Count | Percentage |
|---------|-------|------------|
| RHEL 9.3 | 12 | 29% |
| RHEL 9.2 | 6 | 14% |
| RHEL 8.9 | 15 | 36% |
| RHEL 8.8 | 5 | 12% |
| RHEL 7.9 | 4 | 9% |

## Environment Breakdown
| Environment | Count | Systems |
|-------------|-------|---------|
| Production | 25 | web-*, db-*, app-* |
| Staging | 10 | stg-* |
| Development | 7 | dev-* |

## Top 20 Systems (by last check-in)
[Table with display_name, rhel_version, tags, last_seen]

**Would you like to**:
- Filter by specific environment or RHEL version
- View CVEs affecting these systems
- Create remediation plans for vulnerabilities
```

### Template 2: CVE-Affected Systems

**User Request**: "What systems are affected by CVE-2024-1234?"

**Skill Response**:
```markdown
# CVE-2024-1234 Impact Analysis

## Affected Systems Summary
- **Total Vulnerable**: 12 systems
- **Already Patched**: 3 systems
- **Total Registered**: 42 systems
- **Impact Rate**: 29% of fleet

## Vulnerable Systems

| System Name | RHEL Version | Environment | Remediation Available |
|-------------|--------------|-------------|-----------------------|
| web-server-01.example.com | 8.9 | production | ✓ Yes |
| web-server-02.example.com | 8.9 | production | ✓ Yes |
| app-server-03.example.com | 8.8 | staging | ✓ Yes |
| ... | ... | ... | ... |

**Affected Package**: httpd-2.4.51-7.el8_6.5

## Already Patched (No Action Needed)
- db-server-01.example.com (patched on 2024-01-18)
- cache-server-02.example.com (patched on 2024-01-19)
- lb-server-01.example.com (patched on 2024-01-19)

## Next Steps

**To remediate these systems**, use the `/remediation` skill:
- Single system: "Remediate CVE-2024-1234 on web-server-01"
- Batch production: "Remediate CVE-2024-1234 on all production systems"
- All vulnerable: "Create playbook for CVE-2024-1234 affecting these 12 systems"

**For more analysis**:
- "Show CVSS score and severity for CVE-2024-1234" (use cve-impact skill)
- "What's the risk assessment for this CVE?" (use cve-impact skill)
```

### Template 3: Environment-Filtered View

**User Request**: "Show me production systems"

**Skill Response**:
```markdown
# Production Systems Inventory

Filtered by tag: "production"

## Production Fleet Summary
- **Total Production Systems**: 25
- **RHEL 9.x**: 12 systems
- **RHEL 8.x**: 10 systems
- **RHEL 7.x**: 3 systems
- **Active**: 24 systems
- **Stale**: 1 system ⚠️

## System Tiers
### Web Tier (8 systems)
- web-server-01.example.com (RHEL 8.9)
- web-server-02.example.com (RHEL 8.9)
- web-server-03.example.com (RHEL 9.3)
- ...

### Database Tier (6 systems)
- db-server-01.example.com (RHEL 9.3)
- db-server-02.example.com (RHEL 9.3)
- ...

### Application Tier (11 systems)
- app-server-01.example.com (RHEL 8.9)
- app-server-02.example.com (RHEL 8.9)
- ...

## Stale System Alert ⚠️
- backup-server-01.example.com (last seen: 8 days ago)
  - Action: Investigate Lightspeed client connectivity

## Next Steps
- "Show CVEs affecting production systems"
- "List critical vulnerabilities in production"
- "Remediate CVE-X on production web tier"
```

## Examples

### Example 1: General Fleet Query

**User Request**: "Show the managed fleet"

**Skill Execution**:
1. **Invoke mcp-lightspeed-validator skill** (Step 0)
   - Validation result: ✓ PASSED
   - Message: "Lightspeed MCP validation successful. Proceeding with fleet inventory query..."
2. Call `get_host_details()` with no filters → retrieve all systems
3. I consulted [fleet-management.md](../../docs/insights/fleet-management.md) for grouping strategy
4. Group by RHEL version, environment tags
5. Calculate totals and percentages
6. Sort by last_seen (most recent first)
7. Generate Template 1 output
8. Offer next step options (CVE analysis, remediation)

### Example 2: CVE Impact Query

**User Request**: "What systems are affected by CVE-2024-1234?"

**Skill Execution**:
1. **Invoke mcp-lightspeed-validator skill** (Step 0)
   - Validation result: ✓ PASSED
2. Call `get_cve_systems(cve_id="CVE-2024-1234")`
3. Separate vulnerable vs. patched systems
4. Extract affected package information
5. Generate Template 2 output
6. Suggest remediation agent for next steps

### Example 3: Environment Filter

**User Request**: "Show me staging systems"

**Skill Execution**:
1. **Invoke mcp-lightspeed-validator skill** (Step 0)
   - Validation result: ⚠ PARTIAL (connectivity test unavailable)
   - Ask user: "Configuration appears correct but connectivity could not be tested. Proceed? (yes/no)"
   - User response: "yes"
2. Call `get_host_details()` → retrieve all systems
3. Filter by tag: "staging" in system.tags
4. Group by tier/function (inferred from hostname patterns)
5. Generate Template 3 output
6. Suggest CVE analysis or remediation options

## Error Handling

**No Systems Found**:
```
Fleet Inventory Query: No Results

Query: [user's filter criteria]
Result: No systems match the specified criteria

❓ Possible reasons:
1. No systems registered in Red Hat Lightspeed
2. Filter criteria too restrictive
3. Systems not tagged with specified environment

🔧 Troubleshooting:
- Verify systems are registered: Visit https://console.redhat.com/insights/inventory
- Try broader filters: Remove environment/version constraints
- Check tag spelling: Ensure tag names match exactly (case-sensitive)

💡 Suggested actions:
- "Show the managed fleet" (no filters)
- "List all system tags"
- "Show system registration status"
```

**Lightspeed API Error**:
```
❌ Fleet Inventory Query: API Error

Error: Unable to retrieve system inventory from Red Hat Lightspeed

📋 Possible causes:
1. lightspeed-mcp server not running
2. Authentication failure (invalid credentials)
3. Network connectivity issues
4. Red Hat Lightspeed service outage

🔧 Troubleshooting:
1. Verify lightspeed-mcp server configuration:
   - Check .mcp.json has lightspeed-mcp entry
   - Verify container is running: podman ps | grep insights

2. Check credentials (never echo values—report presence/absence only):
   - test -n "$LIGHTSPEED_CLIENT_ID" && echo "LIGHTSPEED_CLIENT_ID: set" || echo "LIGHTSPEED_CLIENT_ID: not set"
   - test -n "$LIGHTSPEED_CLIENT_SECRET" && echo "LIGHTSPEED_CLIENT_SECRET: set" || echo "LIGHTSPEED_CLIENT_SECRET: not set"
   - Verify credentials at https://console.redhat.com/settings/service-accounts

3. Test connection manually:
   podman run --rm -i --env LIGHTSPEED_CLIENT_ID --env LIGHTSPEED_CLIENT_SECRET \
     quay.io/redhat-services-prod/lightspeed-mcp:latest

4. Check service status:
   - Visit https://status.redhat.com/

❓ How would you like to proceed?
- "retry" - Try the query again
- "setup" - Reconfigure lightspeed-mcp server
- "abort" - Stop the workflow
```

**Stale System Warning**:
```
⚠️ Stale Systems Detected

The following systems have not checked in recently (> 7 days):
- system-01.example.com (last seen: 8 days ago)
- system-02.example.com (last seen: 12 days ago)

📊 Impact: Vulnerability data may be outdated for these systems

🔧 Recommended Actions:
1. Verify Lightspeed client is running:
   ssh system-01.example.com "systemctl status insights-client"

2. Check network connectivity from these systems:
   ssh system-01.example.com "ping console.redhat.com"

3. Review Lightspeed client logs:
   ssh system-01.example.com "cat /var/log/insights-client/insights-client.log"

4. Re-register if needed:
   ssh system-01.example.com "insights-client --register"

5. Force immediate check-in:
   ssh system-01.example.com "insights-client --check-results"

💡 Note: Stale systems are still included in inventory but may have outdated CVE data.
```

## Best Practices

1. **Start broad, then filter** - Retrieve full inventory first, then apply user-requested filters
2. **Group by meaningful categories** - Environment, RHEL version, tier/function for clarity
3. **Highlight stale systems** - Warn users about systems with potentially outdated vulnerability data
4. **Offer remediation transitions** - Always suggest next steps using `/remediation` skill
5. **Use clear formatting** - Tables for detailed lists, summaries for high-level overviews
6. **Include percentages** - Help users understand fleet composition at a glance
7. **Show last check-in times** - Indicate data freshness and system health
8. **Link to CVE analysis** - Transition smoothly to cve-impact skill for vulnerability details
9. **Declare document consultations** - Always state "I consulted [file]" for transparency
10. **Verify prerequisites first** - Never attempt MCP calls without checking server availability

## Integration with Other Skills

**Skill Orchestration Workflows**:

**Workflow 1: Discovery → Analysis → Action**
```
User: "Show the managed fleet"
  ↓
fleet-inventory skill
  ↓
Response: 42 systems, 15 affected by CVE-2024-1234
  ↓
User: "What's the risk of CVE-2024-1234?"
  ↓
cve-impact skill (analyzes severity)
  ↓
Response: CVSS 8.1, Critical severity
  ↓
User: "Remediate CVE-2024-1234 on all affected systems"
  ↓
`/remediation` skill (orchestrates remediation)
  ↓
Complete: Playbook generated and executed
```

**Workflow 2: Environment Focus**
```
User: "Show production systems"
  ↓
fleet-inventory skill (environment filter)
  ↓
Response: 25 production systems
  ↓
User: "List critical CVEs in production"
  ↓
cve-impact skill (production scope)
  ↓
Response: 3 critical CVEs
  ↓
User: "Create remediation plan"
  ↓
`/remediation` skill (multi-CVE workflow)
```

**Information-First Principle**:
```
Always follow this sequence:
1. What systems do we have? (fleet-inventory)
2. What are they vulnerable to? (cve-impact)
3. How do we fix it? (`/remediation` skill)

This ensures informed decisions before taking remediation actions.
```

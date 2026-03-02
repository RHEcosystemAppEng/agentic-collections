# Fleet Inventory Examples

## Example 1: General Fleet Query

**User Request**: "Show the managed fleet"

1. Invoke mcp-lightspeed-validator (Step 0) → PASSED
2. Call `get_host_details()` with no filters
3. Consult fleet-management.md for grouping
4. Group by RHEL version, environment tags
5. Generate Template 1 output
6. Offer next steps (CVE analysis, remediation)

## Example 2: CVE Impact Query

**User Request**: "What systems are affected by CVE-2024-1234?"

1. Invoke mcp-lightspeed-validator (Step 0) → PASSED
2. Call `get_cve_systems(cve_id="CVE-2024-1234")`
3. Separate vulnerable vs. patched systems
4. Generate Template 2 output
5. Suggest /remediation for next steps

## Example 3: Environment Filter

**User Request**: "Show me staging systems"

1. Invoke mcp-lightspeed-validator (Step 0) → PARTIAL
2. Ask user: "Proceed? (yes/no)" → yes
3. Call `get_host_details()` → filter by tag "staging"
4. Group by tier (hostname patterns)
5. Generate Template 3 output

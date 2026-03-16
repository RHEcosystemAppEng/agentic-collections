# Fleet Inventory Error Handling

Read when errors occur during fleet inventory queries.

## No Systems Found

```
Fleet Inventory Query: No Results

Query: [user's filter criteria]
Result: No systems match the specified criteria

Possible reasons: No systems registered, filter too restrictive, tag mismatch
Troubleshooting: Verify at console.redhat.com/insights/inventory, try broader filters
Suggested: "Show the managed fleet" (no filters)
```

## Lightspeed API Error

```
❌ Fleet Inventory Query: API Error

Possible causes: MCP not running, auth failure, network, service outage

Troubleshooting:
1. Run /mcp-lightspeed-validator skill
2. Check LIGHTSPEED_CLIENT_ID and LIGHTSPEED_CLIENT_SECRET (never echo values)
3. Verify at console.redhat.com/settings/service-accounts
4. Check status.redhat.com

Options: retry | setup | abort
```

## Stale System Warning

```
⚠️ Stale Systems Detected

Systems not checked in > 7 days: [list]

Impact: Vulnerability data may be outdated

Actions: Verify insights-client, check connectivity, review logs, re-register if needed
Note: Stale systems included but may have outdated CVE data
```

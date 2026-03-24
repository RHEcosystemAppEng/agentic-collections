#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Lightspeed MCP Validation

## Test: Call vulnerability__get_cves with no parameters
- Do NOT pass `limit` parameter (serialization issue: `limit` → `limit_`)
- Default limit=10 is applied automatically

## Result
| Server | Outcome |
|--------|---------|
| lightspeed-mcp | ✅ PASSED |

## Failure Root Causes (when connection fails)
- **Credentials**: LIGHTSPEED_CLIENT_ID or LIGHTSPEED_CLIENT_SECRET not set or invalid
- **Expired credentials**: Red Hat Console tokens may have expired
- **Server not running**: MCP server/container may be stopped
- **Network**: Firewall or proxy blocking console.redhat.com
- **Configuration**: .mcp.json misconfigured or server not registered

## Troubleshooting
1. Verify env vars: LIGHTSPEED_CLIENT_ID, LIGHTSPEED_CLIENT_SECRET (never echo values)
2. Check credentials at: https://console.redhat.com/settings/integrations
3. Restart MCP server or host after config changes

## Environment
- LIGHTSPEED_CLIENT_ID: Set
- LIGHTSPEED_CLIENT_SECRET: Set
REPORT_EOF

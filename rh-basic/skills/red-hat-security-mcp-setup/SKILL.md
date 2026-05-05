---
name: red-hat-security-mcp-setup
description: Add the Red Hat Security MCP server to this project. Configures the HTTP transport endpoint and explains the Red Hat Customer Portal SSO browser login flow.
user_invocable: true
---

# Red Hat Security MCP Setup

Add the Red Hat Security MCP server to the current project's `.mcp.json`.

## Step 1 — Locate or create `.mcp.json`

```
PROJ=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
MCP_FILE="$PROJ/.mcp.json"
```

If `.mcp.json` exists: read it and merge in the new server entry.
If it does not exist: create it with the skeleton below.

## Step 2 — Add the server entry

The server key is `red-hat-security`. Use HTTP transport.

```json
{
  "mcpServers": {
    "red-hat-security": {
      "type": "http",
      "url": "https://security-mcp.api.redhat.com/mcp"
    }
  }
}
```

Merge this entry into the existing `mcpServers` object without removing any other servers already present.

Write the result back to `$PROJ/.mcp.json`.

## Step 3 — Explain authentication to the user

Tell the user:

```
Red Hat Security MCP server added.

Authentication: Red Hat Customer Portal SSO

The first time any tool from this server is called, a browser window will
open automatically so you can log in with your Red Hat account. After you
complete login, the session token is stored and subsequent calls proceed
without prompting.

If the browser does not open automatically, look for an authentication URL
printed in the MCP server output and open it manually.

Restart the agentic tool (or reload MCP servers) for the new configuration
to take effect.
```

## Notes

- This server exposes Red Hat security data (CVEs, advisories, errata). It
  is the backend used by `/red-hat-cve-explainer` when the `cve-mcp` tool is
  available.
- An active Red Hat subscription is required to access the full dataset.
- Do not add `headers` or `env` auth fields to `.mcp.json` -- the server
  handles authentication itself via the browser SSO flow.

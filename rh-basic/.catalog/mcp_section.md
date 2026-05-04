<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, CLAUDE.md, marketplace/rh-agentic-collection.yml
-->

### lightspeed-mcp — Red Hat Lightspeed

Provides live data for CVE lookups, RHEL lifecycle, system inventory, and patch advisory information.

- **CVE metadata and severity** — used by `red-hat-cve-explainer` and `red-hat-support-severity`
- **RHEL and App Stream lifecycle dates** — used by `red-hat-product-lifecycle`
- **Requires:** `LIGHTSPEED_CLIENT_ID`, `LIGHTSPEED_CLIENT_SECRET`
- **Transport:** Podman container (`ghcr.io/redhatinsights/red-hat-lightspeed-mcp:latest`)

**All skills fall back to `WebFetch` on public Red Hat documentation when this MCP server is unavailable.** A valid service account improves data currency and enables inventory queries.

### red-hat-security — Red Hat Security MCP (optional)

Provides CVE, advisory, and errata data directly from the Red Hat Security API.

- **CVE and advisory lookups** — used by `red-hat-cve-explainer` when available
- **Transport:** HTTP (`https://security-mcp.api.redhat.com/mcp`)
- **Authentication:** Red Hat Customer Portal SSO (browser-based, no env vars required)
- **Setup:** run `/red-hat-security-mcp-setup` to add the server entry to your project's `.mcp.json`

An active Red Hat subscription is required for full dataset access.

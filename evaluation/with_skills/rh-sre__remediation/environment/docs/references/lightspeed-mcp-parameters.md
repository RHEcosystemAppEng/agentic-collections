---
title: Red Hat Lightspeed MCP - Parameter Reference
category: references
sources:
  - title: Red Hat Lightspeed MCP
    url: https://github.com/redhat/lightspeed-mcp
    date_accessed: 2026-02-26
tags: [lightspeed, mcp, parameters, inventory]
last_updated: 2026-02-26
---

# Lightspeed MCP Parameter Reference

Correct parameter names and types for Red Hat Lightspeed MCP tools. **Using wrong parameters causes validation errors.**

## inventory__list_hosts

**Purpose**: List hosts with filtering and sorting options.

**CRITICAL**: Use `per_page` (integer), NOT `page_size`. The Lightspeed inventory API uses different parameter names than AAP MCP.

| Parameter | Type | Required | Example | Notes |
|-----------|------|----------|---------|-------|
| `per_page` | **integer** | No | `10` | Use 10 on first call to avoid performance issues. NOT `page_size`. |
| `display_name` | string | No | `""` | Filter by display name. Pass empty string if no filter. |
| `page` | integer | No | `1` | Pagination page number. |

**Correct**:
```
inventory__list_hosts(per_page=10, display_name="")
```

**Wrong** (causes "Unexpected keyword argument" error):
```
inventory__list_hosts(page_size=100)   # ❌ Use per_page, not page_size
inventory__list_hosts(per_page="100")  # ❌ Use integer, not string
```

## AAP MCP vs Lightspeed MCP

| Server | Pagination Parameter | Type |
|--------|---------------------|------|
| lightspeed-mcp (inventory) | `per_page` | integer |
| aap-mcp-job-management | `page_size` | integer |
| aap-mcp-inventory-management | `page_size` | integer |

Do not mix parameter names between servers.

## vulnerability__get_cves

**Purpose**: List CVEs affecting the account with filtering.

**⚠️ Known issue**: Some MCP clients serialize `limit` as `limit_`, causing "Unexpected keyword argument" errors. For connectivity tests, call with no parameters. For CVE queries, if you see this error, omit `limit` (default 10) or use other parameters only.

| Parameter | Type | Example | Notes |
|-----------|------|---------|-------|
| `impact` | string | `"7,6"` | Comma-separated impact IDs: 7=Critical, 6=High, 5=Important, 4=Moderate |
| `sort` | string | `"-cvss_score"` | Use `-` prefix for descending |
| `limit` | integer | `20` | Max records per page. **Note**: Some clients bug: pass as `limit`; if error, omit (default 10) |
| `advisory_available` | string | `"true"` | Filter remediatable CVEs: `"true"` = only with available advisory, `"true,false"` = all |

**For remediatable CVEs** (user asks "which CVEs can I remediate?"):
```
vulnerability__get_cves(impact="7,6", sort="-cvss_score", limit=20, advisory_available="true")
```

**For remediatable CVEs on a specific system**: `get_system_cves` does NOT support `advisory_available` as a request param. Paginate with `limit=100`, `offset=0,100,200,...` until empty; filter client-side for `attributes.advisory_available === true`. **HITL required** before pagination—confirm with user (systems with 1,700+ CVEs ≈ 18 API calls).

## vulnerability__get_system_cves

**Purpose**: List CVEs affecting a specific system. Supports pagination.

| Parameter | Type | Example | Notes |
|-----------|------|---------|-------|
| `system_uuid` | string (UUID) | `"68ce32aa-57da-49b7-8ded-dc4ad54e520a"` | Required |
| `limit` | integer | `100` | Records per page (default 10) |
| `offset` | integer | `0`, `100`, `200` | Pagination offset |
| `sort` | string | `"-public_date"` | Use `-` for descending |

**Pagination**: Loop with `offset += limit` until `len(data) < limit`. Response includes `attributes.advisory_available` per CVE—filter client-side for remediatable.

## vulnerability__get_cve_systems

**Purpose**: List systems affected by a CVE. Supports `system_uuid` filter to check if a specific system is affected.

| Parameter | Type | Example | Notes |
|-----------|------|---------|-------|
| `cve` | string | `"CVE-2024-1234"` | Required |
| `system_uuid` | string | `"68ce32aa-57da-49b7-8ded-dc4ad54e520a"` | Filter to check if this system is affected |

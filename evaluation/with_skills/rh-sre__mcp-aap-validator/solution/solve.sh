#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# AAP MCP Validation

## Test Calls
- `job_templates_list(page_size: 10)` from aap-mcp-job-management ✅
- `inventories_list(page_size: 10)` from aap-mcp-inventory-management ✅

## Result
| Server | Outcome |
|--------|---------|
| aap-mcp-job-management | ✅ PASSED |
| aap-mcp-inventory-management | ✅ PASSED |

## Diagnostics
| Code | Meaning |
|------|---------|
| 401 | Token expired or invalid → regenerate in AAP Web UI → Users → Tokens |
| 403 | Insufficient RBAC (need Job Templates, Inventories) |
| 404 | Wrong URL — AAP_MCP_SERVER must point to MCP gateway, not main AAP UI |

## Environment
- AAP_MCP_SERVER: Set (must point to MCP gateway)
- AAP_API_TOKEN: Set
REPORT_EOF

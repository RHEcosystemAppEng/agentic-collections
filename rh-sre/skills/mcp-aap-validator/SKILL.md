---
name: mcp-aap-validator
description: |
  This skill should be used when the user asks to "validate AAP MCP", "check if AAP is configured", "verify aap-mcp servers", "test AAP connection", or when other skills need to verify AAP MCP server availability before executing job management or inventory operations.
model: haiku
color: yellow
---

# MCP AAP Validator

Validates that AAP (Ansible Automation Platform) MCP servers are properly configured and accessible for job management and inventory operations.

## When to Use This Skill

Use this skill when:
- Validating AAP MCP server configuration before job template operations
- Troubleshooting connection issues with AAP MCP servers
- Verifying environment setup for AAP workflows
- Other skills need to confirm AAP MCP server availability as a prerequisite (e.g., `job-template-creator`)

Do NOT use when:
- Creating job templates → Use `job-template-creator` skill instead
- Launching jobs → Use `playbook-executor` or job management skills instead
- Querying inventories → Use `fleet-inventory` skill instead

## Workflow

### Step 1: Check MCP Server Configuration

**Action**: Verify that AAP MCP servers exist in [.mcp.json](../../.mcp.json)

**Required AAP MCP Servers**:
- `aap-mcp-job-management` - Job template and execution management
- `aap-mcp-inventory-management` - Inventory and host management

**Note**: Additional AAP MCP servers may be added in the future. This validator checks all configured `aap-mcp-*` servers.

**How to verify**:
1. Read the `.mcp.json` file in the rh-sre directory
2. Check if `mcpServers` object contains both required servers:
   - `aap-mcp-job-management` key
   - `aap-mcp-inventory-management` key
3. Verify each server configuration has:
   - `type: "http"` or `url` field
   - `headers` with Authorization Bearer token
   - `env` with required variables

**Expected result**: Both AAP MCP servers configured with proper HTTP structure

**Report to user**:
- ✓ "MCP server `aap-mcp-job-management` is configured in .mcp.json"
- ✓ "MCP server `aap-mcp-inventory-management` is configured in .mcp.json"
- ✗ "MCP server `aap-mcp-job-management` not found in .mcp.json"
- ✗ "MCP server `aap-mcp-inventory-management` not found in .mcp.json"

**If either AAP server missing**: Proceed to Human Notification Protocol (Step 4)

### Step 2: Verify Environment Variables

**Action**: Check that required environment variables are set (without exposing values)

**Required Environment Variables**:
- `AAP_MCP_SERVER` - Base URL for the MCP endpoint of the AAP server (used in .mcp.json; e.g. "https://aap-mcp.example.com"). Must point to the AAP MCP gateway, not the main AAP Web UI.
- `AAP_API_TOKEN` - Authentication token for AAP API

**CRITICAL SECURITY CONSTRAINT**:
- **NEVER print environment variable values** in user-visible output
- Only report presence/absence
- Do NOT use `echo $VAR_NAME` or display actual values
- Protect sensitive data like API tokens

**How to verify** (without exposing values):
```bash
# Check if set (exit code only, no output)
test -n "$AAP_MCP_SERVER"
test -n "$AAP_API_TOKEN"

# Or check and report boolean result
if [ -n "$AAP_MCP_SERVER" ]; then
  echo "✓ AAP_MCP_SERVER is set"
else
  echo "✗ AAP_MCP_SERVER is not set"
fi

if [ -n "$AAP_API_TOKEN" ]; then
  echo "✓ AAP_API_TOKEN is set"
else
  echo "✗ AAP_API_TOKEN is not set"
fi
```

**Report to user**:
- ✓ "Environment variable AAP_MCP_SERVER is set"
- ✓ "Environment variable AAP_API_TOKEN is set"
- ✗ "Environment variable AAP_MCP_SERVER is not set"
- ✗ "Environment variable AAP_API_TOKEN is not set"

**Note**: `AAP_MCP_SERVER` must point to the MCP endpoint of the AAP server (the MCP gateway URL). If unset, the MCP server will fail to connect.

**If missing**: Proceed to Human Notification Protocol (Step 4)

### Step 3: Test MCP Server Connection and Resources

**Action**: Attempt connectivity test to verify server accessibility and check for required resources

**Test approach**:
1. **Test Job Management Server**:
   - Tool: `job_templates_list` (from aap-mcp-job-management)
   - Parameters: `page_size: 10` (check for templates)
   - Expected: Returns list
   - Success: Server responds with valid data
   - Failure: Connection timeout, auth error, or server unavailable
   - **Validation**: Check if at least one job template exists
     - If `count: 0` → Warning: No job templates configured
     - If `count > 0` → Success: Templates available for use

2. **Test Inventory Management Server**:
   - Tool: `inventories_list` (from aap-mcp-inventory-management)
   - Parameters: `page_size: 10` (check for inventories)
   - Expected: Returns list
   - Success: Server responds with valid data
   - Failure: Connection timeout, auth error, or server unavailable
   - **Validation**: Check if at least one inventory exists
     - If `count: 0` → Warning: No inventories configured
     - If `count > 0` → Success: Inventories available for use

**Report to user**:
- ✓ "Successfully connected to aap-mcp-job-management"
- ✓ "Successfully connected to aap-mcp-inventory-management"
- ✓ "Found N job template(s) available"
- ✓ "Found N inventory/inventories available"
- ⚠ "Connected but no job templates found (you'll need to create one)"
- ⚠ "Connected but no inventories found (you'll need to create one)"
- ⚠ "Configuration appears correct but connectivity test unavailable"
- ✗ "Cannot connect to aap-mcp-job-management (check server status and credentials)"
- ✗ "Cannot connect to aap-mcp-inventory-management (check server status and credentials)"

**Common connection errors for AAP MCP servers**:
- `Invalid tool parameters`: Often caused by AAP_MCP_SERVER not set or wrong—the MCP URL in .mcp.json fails to resolve. Verify AAP_MCP_SERVER points to the MCP endpoint of the AAP server.
- `401 Unauthorized`: Invalid or expired AAP_API_TOKEN
- `403 Forbidden`: Token lacks required permissions
- `404 Not Found`: Incorrect AAP_MCP_SERVER URL or missing endpoints
- `Connection timeout`: Server unreachable or network issue
- `SSL/TLS error`: Certificate verification issues

**If AAP connection fails**: Proceed to Human Notification Protocol (Step 4)
**If ansible connection fails**: Report warning but allow continuation (playbook execution will not be available)

### Step 4: Human Notification Protocol

When validation fails, follow this protocol:

**1. Stop Execution Immediately** - Do not attempt MCP tool calls

**2. Report Clear Error**:

For missing MCP server configuration:
```
❌ Cannot validate AAP MCP servers: Servers not configured in .mcp.json

📋 Setup Instructions:
1. Add AAP MCP server configurations to rh-sre/.mcp.json
2. Configuration template:
   {
     "mcpServers": {
       "aap-mcp-job-management": {
         "url": "https://${AAP_MCP_SERVER}/job_management/mcp",
         "headers": {
           "Authorization": "Bearer ${AAP_API_TOKEN}"
         }
       },
       "aap-mcp-inventory-management": {
         "url": "https://${AAP_MCP_SERVER}/inventory_management/mcp",
         "headers": {
           "Authorization": "Bearer ${AAP_API_TOKEN}"
         }
       }
     }
   }

🔗 Documentation: See rh-sre/README.md for AAP MCP setup
```

For missing environment variables:
```
❌ Cannot validate AAP MCP: Required environment variables not set

📋 Setup Instructions:
1. Set required environment variables:
   export AAP_MCP_SERVER="https://your-aap-mcp-gateway.com"
   export AAP_API_TOKEN="your-api-token"

   Note: .mcp.json uses AAP_MCP_SERVER for MCP URLs. Use the MCP gateway URL, not the main AAP UI URL.

2. To get an API token:
   - Log in to AAP Web UI
   - Navigate to Users → [Your User] → Tokens
   - Create a new Personal Access Token
   - Copy the token value

⚠️ SECURITY: Never commit tokens to source control
   - Use environment variables or secure secret management
   - Rotate tokens regularly
   - Restrict token permissions to minimum required

3. Restart to reload environment variables

🔗 Documentation: See AAP documentation for authentication setup
```

For connection failures:
```
❌ Cannot connect to AAP MCP servers

📋 Troubleshooting steps:
1. Verify AAP MCP server is accessible:
   - Check AAP_MCP_SERVER URL is correct (must match .mcp.json)
   - Test connectivity: curl -I ${AAP_MCP_SERVER}
   - Verify network connectivity and firewall rules

2. Verify API token is valid:
   - Token may have expired
   - Check token permissions in AAP Web UI
   - Generate new token if needed

3. Check AAP MCP endpoints:
   - Job Management: ${AAP_MCP_SERVER}/job_management/mcp
   - Inventory Management: ${AAP_MCP_SERVER}/inventory_management/mcp
   - Verify endpoints are exposed and accessible

4. Review authentication errors:
   - 401: Token invalid or expired → Regenerate token
   - 403: Insufficient permissions → Check RBAC settings
   - 404: Endpoint not found → Verify AAP MCP is deployed

5. Check AAP service status:
   - Verify AAP platform is running
   - Check AAP MCP proxy/gateway is operational
   - Review AAP logs for errors

6. Restart to reload MCP servers after configuration changes
```

**3. Request User Decision**:
```
❓ How would you like to proceed?

Options:
- "setup" - Help me configure the AAP MCP servers now
- "skip" - Skip validation and try the operation anyway (not recommended)
- "abort" - Stop the workflow entirely

Please respond with your choice.
```

**4. Wait for Explicit User Input** - Do not proceed automatically

### Step 5: Validation Summary

**Action**: Report overall validation status

**Success case**:
```
✓ AAP MCP Validation: PASSED

Configuration:
✓ MCP server aap-mcp-job-management configured in .mcp.json
✓ MCP server aap-mcp-inventory-management configured in .mcp.json
✓ Environment variable AAP_MCP_SERVER is set
✓ Environment variable AAP_API_TOKEN is set
✓ Job management server connectivity verified
✓ Inventory management server connectivity verified

Resources:
✓ Found 5 job template(s) available
✓ Found 3 inventory/inventories available

Ready to execute AAP operations.

Available capabilities:
- Job template management (list, retrieve, launch)
- Job execution tracking (status, events, logs)
- Inventory management (hosts, groups, variables)
- System context gathering for remediation
```

**Partial success case** (connected but no resources):
```
⚠ AAP MCP Validation: PARTIAL

Configuration:
✓ MCP server aap-mcp-job-management configured
✓ MCP server aap-mcp-inventory-management configured
✓ Environment variables are set
✓ Server connectivity verified

Resources:
⚠ No job templates found (create one before executing playbooks)
⚠ No inventories found (create one to target systems)

Note: AAP is accessible but requires resource setup.
You'll need to create job templates and inventories before executing remediation playbooks.

Next steps:
1. Create inventory with target systems
2. Create job template for remediation playbooks
3. Re-run validation to confirm setup
```

**Partial success case** (connectivity not tested):
```
⚠ AAP MCP Validation: PARTIAL

Configuration:
✓ MCP servers configured in .mcp.json
✓ Environment variables are set
⚠ Server connectivity could not be tested

Note: Configuration appears correct, but full validation requires connectivity test.
You may proceed with caution. Connection will be verified on first tool use.
```

**Failure case**:
```
✗ AAP MCP Validation: FAILED

Issues found:
✗ [Specific issue 1]
✗ [Specific issue 2]

See troubleshooting steps above. Please resolve configuration issues before proceeding.
```

## Dependencies

### Required Files
- [.mcp.json](../../.mcp.json) - MCP server configuration file

### Required MCP Servers
- `aap-mcp-job-management` - AAP job template and execution management
- `aap-mcp-inventory-management` - AAP inventory and host management

**Note**: Future AAP MCP servers (e.g., `aap-mcp-*`) will be validated automatically when added to the configuration.

### Required MCP Tools
- `job_templates_list` (from aap-mcp-job-management) - List job templates
  - Used for connectivity test
  - Parameters: page_size (int)
  - Returns: List of job templates
- `inventories_list` (from aap-mcp-inventory-management) - List inventories
  - Used for connectivity test
  - Parameters: page_size (int)
  - Returns: List of inventories

### Required Environment Variables
- `AAP_MCP_SERVER` - Base URL for the MCP endpoint of the AAP server (must match .mcp.json; e.g., "https://aap-mcp.example.com"). Must point to the AAP MCP gateway.
- `AAP_API_TOKEN` - Personal Access Token for AAP API authentication

### Related Skills
- `job-template-creator` - **PRIMARY USER** - Uses AAP MCP for template creation (invokes this validator as prerequisite)
- `fleet-inventory` - May use AAP inventory management features in the future

### Reference Documentation
- [AAP REST API Documentation](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/)
- [AAP Authentication Guide](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/)

## Validation Freshness Policy

**Session-based validation**: Once validation succeeds in a session, subsequent skills can skip re-validation unless:
1. User explicitly requests re-validation
2. Previous MCP tool call failed with connection error
3. Configuration changes were made to .mcp.json
4. Environment variables were modified

**How other skills use this**:
```
IF validation_passed_in_session AND no_config_changes:
  Skip validation, proceed with operation
ELSE:
  Invoke mcp-aap-validator skill
  IF validation PASSED:
    Mark validation_passed_in_session = true
    Proceed with operation
  ELSE:
    Report error, ask user for decision
```

## Example Usage

### Example 1: Full Validation with All Servers

**User Query**: "Validate AAP MCP before creating job templates"

**Skill Response**:
```
I'll validate your AAP MCP configuration.

Checking MCP server configuration...
✓ MCP server `aap-mcp-job-management` is configured in .mcp.json
✓ MCP server `aap-mcp-inventory-management` is configured in .mcp.json

Checking environment variables...
✓ Environment variable AAP_MCP_SERVER is set
✓ Environment variable AAP_API_TOKEN is set

Testing server connectivity...
✓ Successfully connected to aap-mcp-job-management
✓ Successfully connected to aap-mcp-inventory-management

✓ AAP MCP Validation: PASSED

Configuration:
✓ AAP MCP servers configured
✓ Environment variables configured
✓ Server connectivity verified

Ready to execute AAP operations.

Available capabilities:
- Job template management (list, retrieve, launch)
- Job execution tracking (status, events, logs)
- Inventory management (hosts, groups, variables)
- System context gathering for remediation
```

### Example 2: Validation Failure - Missing Environment Variables

**User Query**: "Check if AAP is ready for job operations"

**Skill Response**:
```
I'll validate your AAP MCP configuration.

Checking MCP server configuration...
✓ MCP server `aap-mcp-job-management` is configured in .mcp.json
✓ MCP server `aap-mcp-inventory-management` is configured in .mcp.json

Checking environment variables...
✗ Environment variable AAP_MCP_SERVER is not set
✗ Environment variable AAP_API_TOKEN is not set

❌ Cannot validate AAP MCP: Required environment variables not set

📋 Setup Instructions:
1. Set required environment variables:
   export AAP_MCP_SERVER="https://your-aap-mcp-gateway.com"
   export AAP_API_TOKEN="your-api-token"

2. To get an API token:
   - Log in to AAP Web UI
   - Navigate to Users → [Your User] → Tokens
   - Create a new Personal Access Token
   - Copy the token value

⚠️ SECURITY: Never commit tokens to source control
   - Use environment variables or secure secret management
   - Rotate tokens regularly
   - Restrict token permissions to minimum required

3. Restart to reload environment variables

🔗 Documentation: See AAP documentation for authentication setup

❓ How would you like to proceed?

Options:
- "setup" - Help me configure environment variables now
- "skip" - Skip validation and try anyway (not recommended)
- "abort" - Stop the workflow entirely

Please respond with your choice.
```

### Example 3: Connection Failure - Invalid Credentials

**User Query**: "Verify AAP MCP is working"

**Skill Response**:
```
I'll validate your AAP MCP configuration.

Checking MCP server configuration...
✓ MCP server `aap-mcp-job-management` is configured in .mcp.json
✓ MCP server `aap-mcp-inventory-management` is configured in .mcp.json

Checking environment variables...
✓ Environment variable AAP_MCP_SERVER is set
✓ Environment variable AAP_API_TOKEN is set

Testing server connectivity...
✗ Cannot connect to aap-mcp-job-management (401 Unauthorized)

❌ Cannot connect to AAP MCP servers

📋 Troubleshooting steps:
1. Verify API token is valid:
   - Error 401 indicates authentication failure
   - Token may have expired
   - Generate new token in AAP Web UI:
     Users → [Your User] → Tokens → Add

2. Test token manually:
   curl -H "Authorization: Bearer ${AAP_API_TOKEN}" \
        ${AAP_MCP_SERVER}/api/controller/v2/ping/

3. If token is valid but error persists:
   - Check AAP MCP proxy/gateway configuration
   - Verify token has required permissions (RBAC)
   - Review AAP logs for authentication errors

4. After fixing, restart to reload configuration

❓ How would you like to proceed?

Options:
- "setup" - Help me regenerate API token
- "skip" - Skip validation and try anyway
- "abort" - Stop the workflow entirely

Please respond with your choice.
```

### Example 4: Invoked by Another Skill

**Context**: The `job-template-creator` skill invokes this validator before attempting template creation

**Internal workflow**:
```
[job-template-creator skill] → [Invoke mcp-aap-validator]
                             ← [Validation result: PASSED/PARTIAL/FAILED]
[job-template-creator skill] → [If PASSED: proceed with template creation]
                             → [If PARTIAL: warn user, ask to proceed]
                             → [If FAILED: report to user, ask for decision]
```

This skill provides a reusable validation check that other skills can invoke as a prerequisite before AAP MCP operations.

## Best Practices

1. **Invoke once per session** - Cache validation result for efficiency
2. **Security first** - Never expose environment variable values
3. **Clear error messages** - Provide actionable troubleshooting steps
4. **Test both servers** - Job management AND inventory management
5. **Verify permissions** - Ensure token has required RBAC roles
6. **Document prerequisites** - Help users understand what's needed
7. **Graceful degradation** - Allow operations even with partial validation (with warnings)
8. **Token rotation** - Remind users to rotate tokens regularly
9. **Connection pooling** - Reuse connections when possible
10. **Timeout handling** - Set appropriate timeouts for connectivity tests

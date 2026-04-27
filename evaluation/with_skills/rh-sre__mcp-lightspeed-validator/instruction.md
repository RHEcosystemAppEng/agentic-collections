# Lightspeed Connectivity Check Task

You are a Red Hat SRE. Before querying CVE data or generating remediation playbooks, you need to verify that the Red Hat Insights/Lightspeed integration is working correctly.

## Scenario
You are about to start a CVE investigation that depends on querying vulnerability data from Red Hat Insights. First, you need to confirm the Lightspeed connection is healthy and returning valid data.

## Requirements
- Test connectivity to the Lightspeed service by querying CVE data
- Verify the response is valid and contains expected vulnerability information
- If the connection fails, document the error and provide troubleshooting guidance (expired tokens, credentials, network issues, server availability)
- Report the overall Lightspeed readiness status

Document your methodology, connectivity check results, and troubleshooting findings in `/root/report.md`.

Use MCP tools to interact with the Lightspeed service. If reference documentation or skills are available in this environment, consult them before beginning work.

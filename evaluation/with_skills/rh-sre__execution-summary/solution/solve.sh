#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Execution Summary

**** EXECUTION SUMMARY START ****
Agents: None
Skills: rh-sre:fleet-inventory,rh-sre:cve-impact
Tools: lightspeed-mcp:get_host_details,lightspeed-mcp:get_cves
Docs: docs/references/cvss-scoring.md,docs/insights/vulnerability-logic.md
**** EXECUTION SUMMARY END ****

This summary shows all agents, skills, tools, and documentation used during the workflow.
REPORT_EOF

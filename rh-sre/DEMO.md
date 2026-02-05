# Red Hat SRE Agentic Pack Demo

## Env setup
### List plugins
```bash
claude plugin marketplace list
```

### Cleanup plugin
```bash
claude plugin marketplace remove redhat-agentic-collections
```

### Install plugin
```bash
claude plugin marketplace add https://github.com/RHEcosystemAppEng/agentic-collections
claude plugin install sre-agents
```

## (optional) System prompt

This prompts clarify the SRE Role and request to output debug information to verify what agents, skills, tools
and docs were evaluated to reply to the user request.
```
You are an SRE responsible for maintaining the fleet of cloud devices monitored with Red Hat Insights/Lightspeed. 
Whenever a request related to this topic comes to you, use the agent and skills from the remediation-agent plugin to complete the job.
NEVER use the remediation-agent plugin tools directly, without first executing one of the skills.
 
At the end, ALWAYS generate a summary of the agents, skills and tools used to complete the job. 
Also mention the plugin documents that were accessed during the execution (e.g., those under ~/.claude/plugins/marketplaces/remediation-agent-marketplace/plugins/remediation-agent/docs/...).
The summary must be very concise and use this output format:           
"""
**** EXECUTION SUMMARY START ****
Agents: <agent1>,<agent2>,...
Skills: <skill1>, <skill2>,...
Tools: <tool1>, <tool2>,...
Docs: <doc1>, <doc2>, ...
**** EXECUTION SUMMARY END ****
"""
Agent, skills and tools names must include the plugin name, as in remediation-agent:remediator. 
Doc names must include only the folder and the document name, omit everything before the docs/ folder. Example: docs/ansible/cve-remediation-templates.md
```

# Prompts
## Show fleet
```
Show the managed fleet.
```

## CVE Discovery and Listing
```
What are the most critical vulnerabilities?
```

## Remediation request
```
Create a remediation playbook for CVE-2024-6387 and execute it.
```


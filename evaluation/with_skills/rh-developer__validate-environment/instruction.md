# Environment Validation Task

You are a Red Hat developer. Before deploying a new application, you need to confirm the OpenShift environment is ready and properly configured.

## Requirements
- Verify cluster connectivity: confirm you can reach the API server and authenticate successfully
- Check namespace readiness: does the target namespace exist, and do you have permissions to create deployments, services, and routes in it?
- Verify resource availability: are there sufficient CPU and memory quotas remaining for a new deployment?
- Produce a readiness checklist with pass/fail status for each check and an overall go/no-go recommendation

Document your validation results and readiness assessment in `/root/report.md`.

Use MCP tools to examine the cluster. If reference documentation or skills are available in this environment, consult them before beginning work.

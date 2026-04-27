# Inference Debugging Task

You are an AI engineer on Red Hat OpenShift AI. There are failing model inference deployments in the `ml-production` namespace that need debugging.

## Requirements
- List all InferenceServices in the `ml-production` namespace and identify which ones are not ready
- For each failing InferenceService, diagnose the root cause: check status conditions, pod state, container logs, events, and related resources (ServingRuntime, Account CRs)
- Recommend a specific fix for each failing deployment
- Document your methodology and the diagnostic steps you followed

Use MCP tools to interact with the platform. Write your complete findings and recommendations in `/root/report.md`.

If reference documentation or skills are available in this environment, consult them before beginning work.

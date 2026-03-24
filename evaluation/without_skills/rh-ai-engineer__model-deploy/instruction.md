# Model Deployment Task

You are an AI engineer on Red Hat OpenShift AI. Your team has trained models ready to serve and needs them deployed as inference endpoints in the `ml-production` project.

## Requirements
- Examine the existing project, available serving runtimes, and any existing deployments
- Diagnose any failing deployments: check pod conditions, container status, logs, and events to determine root causes
- For GPU memory issues, provide a VRAM budget analysis showing model weight size, KV cache requirements, and available GPU memory — distinguish GPU VRAM constraints from pod system memory limits
- Before recommending fixes, check the namespace environment for resource policies and GPU node scheduling constraints that could block redeployment
- For each failing deployment, provide a complete KServe InferenceService YAML manifest with your recommended fix
- Produce a deployment plan that addresses all identified issues and gets the models serving successfully

Document your deployment plan, diagnosed issues, environment validation, and recommended fixes in `/root/report.md`.

Use MCP tools to interact with the platform. If reference documentation or skills are available in this environment, consult them before beginning work.

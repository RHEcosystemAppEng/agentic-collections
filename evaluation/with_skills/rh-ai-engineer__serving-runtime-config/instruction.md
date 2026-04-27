# Serving Runtime Configuration Task

You are an AI engineer on Red Hat OpenShift AI. Your team needs to serve a model using a custom inference engine that is not available as a default runtime on the platform.

## Scenario
The existing platform-provided serving runtimes do not support the model format your team needs. You must create a custom runtime configuration that integrates properly with the platform and can be used to deploy models.

## Requirements
- Examine the currently available serving runtimes and platform templates, distinguishing which are already instantiated versus which require instantiation before use
- Design a custom ServingRuntime CR that specifies the inference container, supported model formats, resource requirements, and API protocol
- Follow KServe container naming conventions so the runtime integrates correctly with the platform's model serving framework
- For runtimes supporting multiple model formats, explain how autoSelect should be configured to avoid format conflicts
- Explain where GPU resource allocation belongs (in the ServingRuntime vs in the InferenceService) and why
- Ensure the runtime will be visible and usable from the platform dashboard
- Document your design decisions and trade-offs

Document your configuration plan and the complete runtime specification in `/root/report.md`.

Use MCP tools to interact with the platform. If reference documentation or skills are available in this environment, consult them before beginning work.

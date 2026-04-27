# NVIDIA NIM Setup Task

You are an AI engineer on Red Hat OpenShift AI. Your team wants to deploy NVIDIA NIM for GPU-accelerated inference, but the cluster has not been set up for it yet.

## Scenario
The ML team needs to serve models using NVIDIA's inference microservices. The cluster has GPUs available, but the necessary platform components and credentials have not been configured. You need to assess readiness and produce a complete setup plan.

## Requirements
- Verify operator prerequisites (GPU Operator and NFD Operator) by checking their ClusterServiceVersion status
- Assess the current cluster state to determine what NIM infrastructure is already in place and what is missing
- Document the complete setup procedure including: the exact Kubernetes Secret manifests (with types, data key names, and structure) needed for NGC authentication, and the NIM Account custom resource with its correct API group and spec fields
- Provide the YAML manifests for each resource that needs to be created, using the correct RHOAI-specific API versions and resource naming conventions
- Flag any potential issues or blockers discovered during your assessment

Document your assessment and setup plan in `/root/report.md`.

Use MCP tools to interact with the platform. If reference documentation or skills are available in this environment, consult them before beginning work.

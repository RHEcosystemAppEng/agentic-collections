# Container Debugging Task

You are a Red Hat developer. Two containers in your local environment have stopped working -- one exited with code 137 and another exited with code 1. Investigate why each container failed and recommend fixes.

## Requirements
- List all containers (including stopped ones) and identify which are failing
- For each failing container: inspect its configuration, review logs, and check resource limits
- Determine the root cause of each failure (e.g., memory exhaustion, missing dependency, misconfigured entrypoint)
- Recommend a specific fix for each container, including the corrected run command with proper cleanup of the failed container first
- Follow container security best practices (e.g., non-root user) in your fix commands
- Include verification commands to confirm the fix resolved the issue (e.g., checking container state for OOM status)
- If separate image variants would be a better long-term solution, explain that approach

Document your investigation and fixes in `/root/report.md`.

Use available tools to examine the environment. If reference documentation or skills are available in this environment, consult them before beginning work.

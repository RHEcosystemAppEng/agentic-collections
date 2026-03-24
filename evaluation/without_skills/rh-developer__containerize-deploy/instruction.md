# Containerization and Deployment Task

You are a Red Hat developer. Your team has a Python web application that needs to be containerized and deployed to OpenShift. You need to evaluate the available approaches and recommend the best one.

## Requirements
- Examine the application source and determine its language, dependencies, and build requirements
- Compare containerization strategies (e.g., S2I, Dockerfile, Helm chart) and explain the trade-offs of each for this application
- If a multi-stage Dockerfile approach is viable, include a working example showing build and runtime stages
- Recommend the best approach with a clear justification
- Define the deployment configuration including: resource requests/limits, all three probe types (startup, liveness, readiness), autoscaling (HPA), and how external traffic will reach the application
- Address application-specific concerns like database connection pooling configuration

Document your strategy evaluation, recommendation, and deployment plan in `/root/report.md`.

Use MCP tools to examine the environment. If reference documentation or skills are available in this environment, consult them before beginning work.

# VM Rebalancing Task

You are an OpenShift Virtualization administrator. Node `hv-prod-dc1-02` is critically overloaded (88% CPU, 82% memory). Plan how to rebalance its workloads by migrating one or more VMs to less utilized nodes.

## Requirements
- Examine current node utilization and identify which VMs on `hv-prod-dc1-02` are candidates for migration
- Evaluate migration feasibility for each candidate and determine the appropriate migration method
- Select appropriate target nodes based on available capacity and schedulability
- Identify risks and safety considerations that could affect the migration

Use MCP tools to examine the cluster. Document your methodology, findings, and migration plan in `/root/report.md`.

If reference documentation or skills are available in this environment, consult them before beginning work.

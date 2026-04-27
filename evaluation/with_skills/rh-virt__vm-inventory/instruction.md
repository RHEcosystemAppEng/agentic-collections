# VM Inventory Task

You are an OpenShift Virtualization administrator. Your team needs a complete picture of every VM in the cluster for capacity planning and compliance reporting.

## Requirements
- List every VM across all namespaces, grouped by namespace
- For each VM report: name, status (Running/Stopped/Paused), CPU and memory allocation, operating system, and IP address if running
- Identify any VMs with issues: stopped unexpectedly, guest agent not responding, degraded conditions, or running end-of-life operating systems
- Summarize totals: how many VMs per namespace, how many running vs stopped, total resource allocation
- Sort results by namespace, then by VM name

Write the inventory report in `/root/report.md`.

Use MCP tools to gather VM data. If reference documentation or skills are available in this environment, consult them before beginning work.

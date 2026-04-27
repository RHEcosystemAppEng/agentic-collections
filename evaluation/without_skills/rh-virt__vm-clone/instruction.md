# VM Cloning Task

You are an OpenShift Virtualization administrator. The QA team needs an exact copy of the production database VM to test a schema migration. Plan the clone so it can run safely in the test environment without affecting production.

## Requirements
- Inspect the source VM (`production-db` in `prod-vms`) to understand its current state, storage configuration, and whether it needs to be stopped for cloning
- Determine the right cloning approach: whether the storage backend supports efficient cloning, and whether the VM needs to be offline
- Plan the clone target (`test-db-clone` in `test-env`) ensuring it has no network or storage conflicts with the source
- Verify the clone will be fully independent: separate disks, no shared PVCs, and safe to modify without affecting production

Document your cloning plan in `/root/report.md`.

Use MCP tools to examine the cluster. If reference documentation or skills are available in this environment, consult them before beginning work.

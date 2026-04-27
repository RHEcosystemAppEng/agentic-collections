#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# VM Lifecycle Operations Plan

## Operation 1: Stop web-frontend
- Tool: `vm_lifecycle(namespace="prod-vms", name="web-frontend", action="stop")`
- Effect: Sets runStrategy to Halted
- Verify: `status.printableStatus` changes to "Stopped"

## Operation 2: Restart production-db
Restart requires TWO separate calls to avoid resourceVersion conflicts:
1. `vm_lifecycle(namespace="prod-vms", name="production-db", action="stop")`
2. Wait for `status.printableStatus == "Stopped"` (poll every 5 seconds)
3. `vm_lifecycle(namespace="prod-vms", name="production-db", action="start")`

### RunStrategy Mapping
| Action | RunStrategy Set |
|--------|----------------|
| start | Always |
| stop | Halted |
| restart | Always (after stop completes) |

### Caveats
- Restart is NOT a single atomic operation — it's stop + wait + start
- Graceful shutdown: VM guest agent handles ACPI shutdown signal
- If VM doesn't stop within timeout, force stop may be needed
- Always verify stopped status before issuing start to avoid conflicts

REPORT_EOF

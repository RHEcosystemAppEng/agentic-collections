#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Container Debug Report

## Issue: Container exits immediately

### Diagnosis
1. `podman inspect` → State.ExitCode: 1, State.OOMKilled: false
2. `podman logs` → Error: entrypoint not found
3. Check image entrypoint/CMD

### Root Cause
Image entrypoint points to a binary that doesn't exist in the container.

### Fix
- Override entrypoint: `podman run --entrypoint /bin/sh myimage`
- Or fix Dockerfile CMD/ENTRYPOINT
REPORT_EOF

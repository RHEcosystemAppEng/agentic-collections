#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Build Debug Report

## Build Failure Analysis

### S2I Build Phases
1. Fetching source ✓
2. Pulling builder image ✓
3. **Assemble** ✗ (FAILED)
4. Commit (not reached)
5. Push (not reached)

### Root Cause
Assemble phase failed — likely dependency installation error in pip install.

### Fix
- Check requirements.txt for version conflicts (gunicorn, APP_MODULE)
- Verify builder image compatibility (python:3.11-ubi9)
- Retry: `oc start-build flask-app -n myproject --follow`
REPORT_EOF

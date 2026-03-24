#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Network Debug Report

## Issue: Route 503 for order-service

### Root Cause
**Service selector mismatch**: Service selector `app: order-svc` does not match pod label `app: order-service`.

### Diagnosis
1. Route status: Admitted ✓
2. Service selector: `app: order-svc`
3. Pod labels: `app: order-service`
4. Endpoints: 0 (no matching pods)
5. Test: `oc run test-curl --rm -i --tty --image=curlimages/curl -- curl -v http://order-service.myns.svc.cluster.local:8080`

### Fix
Update Service selector to match pod labels: `app: order-service`
REPORT_EOF

#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Pod Debug Report

## Investigation Summary
A pod in the web-frontend namespace is crashing repeatedly.

## Pod Status
- Namespace: web-frontend
- Pod: web-frontend (CrashLoopBackOff)
- Exit code: 137 (OOMKilled — SIGKILL, memory limit exceeded)
- Restart count: 8

## Diagnosis Methodology
1. Listed pods in web-frontend namespace — found pod in CrashLoopBackOff
2. Examined container status — exit code 137, reason: OOMKilled
3. Checked previous container logs — server starts but gets Killed
4. Reviewed events — OOMKilled warning with memory limit 64Mi
5. Analyzed resource limits — memory limit 64Mi is too low for Node.js

## Root Cause
Exit 137 = 128 + 9 (SIGKILL). The container was OOMKilled because the memory limit of 64Mi is insufficient for a Node.js application. The application starts normally but is killed when memory usage exceeds the limit during initialization of middleware.

## Events Analysis
- Warning: OOMKilled — Container exceeded memory limit of 64Mi
- Warning: BackOff — Back-off restarting failed container

## Recommended Fix
Increase the memory limit for the web-frontend deployment:
- Current: requests=32Mi, limits=64Mi
- Recommended: requests=128Mi, limits=256Mi (or higher depending on app needs)

This can be applied by patching the deployment resource limits.

## Additional Notes
- The application logs show it starts successfully but is killed during middleware initialization
- No memory leak — the base memory requirement simply exceeds the configured limit
- Consider monitoring memory usage after the fix to right-size the limits
REPORT_EOF

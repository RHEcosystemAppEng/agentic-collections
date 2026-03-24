#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Pipeline Debug Report

## Failed PipelineRun Analysis

### Failure Location
- PipelineRun: build-and-deploy-run
- Failed Task: integration-test
- Failed Step: `step-test` (Tekton names step containers as `step-<step-name>`)

### Step Logs
Extract from TaskRun pod, container `step-test`.

### Root Cause
Integration test failed because the service endpoint returned 503.

### Fix
- Fix the underlying service issue first
- Retry: `tkn pipeline start build-and-deploy --use-pipelinerun build-and-deploy-run`
REPORT_EOF

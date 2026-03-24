#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Inference Debug Report

## Diagnosis Categories (get_inference_service verbosity full)

### 1. ServingRuntime ✓
ServingRuntime CR exists and is valid

### 2. Pod Scheduling ✗
Pod cannot be scheduled — check kserve-container logs (pods_log container=kserve-container)
Label selector: serving.kserve.io/inferenceservice

### 3. Container Start
KServe sidecar containers may conflict with LimitRange

### 4. Model Loading
Check model download and initialization

### 5. GPU Access
Verify GPU allocation and CUDA compatibility

### 6. Endpoint Health
Check InferenceService URL and readiness (PredictorReady, IngressReady conditions)

## Events
events_list filtered by namespace for pod/InferenceService events

## NIM Deployments
For NIM: Check Account CR (nim.opendatahub.io) for NGC credential errors

## Observability (optional)
- korrel8r_get_correlated for cross-domain signals
- query_tempo_tool for trace latency
- execute_promql for custom metrics
REPORT_EOF

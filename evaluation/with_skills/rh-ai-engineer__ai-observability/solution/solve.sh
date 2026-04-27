#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# AI Observability Report

## Model: fraud-detection

### GPU Utilization (last 15m)
- GPU memory: 65% utilized
- GPU compute: 45% utilized
- Recommendation: GPU is underutilized, consider right-sizing

### Model Latency
- P50: 120ms
- P99: 450ms

### Right-Sizing
- Current: 1x A100 80GB
- Recommended: 1x A100 40GB (sufficient for workload)

### Advanced Observability
- execute_promql for custom metrics (e.g., vllm:request_success:ratio)
- query_tempo_tool for trace latency on slow requests
REPORT_EOF

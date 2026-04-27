#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# ServingRuntime Configuration

## Custom Runtime: triton-onnx

Platform templates: list_serving_runtimes with include_templates: true. Templates with requires_instantiation: true use create_serving_runtime.

```yaml
apiVersion: serving.kserve.io/v1alpha1
kind: ServingRuntime
metadata:
  name: triton-onnx-runtime
  labels:
    opendatahub.io/dashboard: "true"
spec:
  supportedModelFormats:
  - name: onnx
    version: "1"
    autoSelect: true
  multiModel: false
  containers:
  - name: kserve-container
    image: nvcr.io/nvidia/tritonserver:latest
    ports:
    - containerPort: 8080
      protocol: TCP
```

### Key: supportedModelFormats.name must match InferenceService modelFormat.name
REPORT_EOF

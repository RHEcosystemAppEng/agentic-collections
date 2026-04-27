#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# NIM Setup Plan

## Prerequisites
- GPU Operator CSV in nvidia-gpu-operator namespace (gpu-operator-certified)
- NFD (Node Feature Discovery) in openshift-nfd

## NGC Secrets
- API key secret: ngc-api-key (NGC_API_KEY)
- Image pull secret: ngc-image-pull-secret
  - Registry: nvcr.io
  - Username: $oauthtoken
  - Password: NGC API key

## NIM Account CR (nim.opendatahub.io/v1)
```yaml
apiVersion: nim.opendatahub.io/v1
kind: Account
metadata:
  name: nim-account
spec:
  apiKeySecret:
    name: ngc-api-key
  imagePullSecret:
    name: ngc-image-pull-secret
```
REPORT_EOF

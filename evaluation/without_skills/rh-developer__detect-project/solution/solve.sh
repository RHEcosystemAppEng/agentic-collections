#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Project Detection Report

## Repository: /root/project

### Detection Methodology
Scanned for indicator files: requirements.txt, package.json, pom.xml, go.mod, Gemfile.
Found: `requirements.txt` → Python project.

### Detected Type
- **Language**: Python
- **Indicator**: `requirements.txt` found
- **Framework**: Flask (detected from `from flask import Flask` in app.py)
- **Entry Point**: `app.py` with `app = Flask(__name__)`

### Helm Chart Search
Searched locations: ./Chart.yaml, ./chart/Chart.yaml, ./charts/*/Chart.yaml, ./helm/Chart.yaml, ./deploy/helm/Chart.yaml
Result: No Helm chart found — S2I or Dockerfile strategy recommended.

### S2I Python Configuration
- **APP_MODULE**: `app:app` (module `app` from `app.py`, WSGI callable `app`)
- **gunicorn** is present in `requirements.txt` — required for the S2I Python builder to serve via APP_MODULE
- S2I Python builder uses gunicorn as the WSGI server when APP_MODULE is set

### Recommended Builder Image
`registry.access.redhat.com/ubi9/python-39` (UBI base image)

### Health Checks
- Add `/health` and `/ready` endpoints for OpenShift liveness/readiness probes

### Recommended Deployment Strategy
1. **Primary**: S2I with `ubi9/python-39` builder image
   - Set `APP_MODULE=app:app` in BuildConfig sourceStrategy.env
   - Ensure gunicorn is in requirements.txt
2. **Alternative**: Containerize with Dockerfile using UBI base image
REPORT_EOF

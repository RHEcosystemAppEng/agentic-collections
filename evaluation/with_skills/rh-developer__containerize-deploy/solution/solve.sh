#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Containerize and Deploy Plan

## Phase 1: Detect
- Language: Python
- Framework: Django
- Entry point: manage.py

## Phase 2: Strategy
- Target: OpenShift
- Strategy: S2I (recommended for Python on OpenShift)
- Alternative: Dockerfile with multi-stage build

## Phase 3: Build
- Builder image: ubi9/python-311
- APP_MODULE: myproject.wsgi:application

## Phase 4: Deploy
- Deployment + Service + Route
- Port: 8000 (Django default)
- On failure: /debug-pod, /debug-build, /debug-network
REPORT_EOF

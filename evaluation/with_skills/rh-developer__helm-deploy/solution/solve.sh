#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Helm Deployment Plan

## Chart Location
Searched: ./Chart.yaml, ./chart/Chart.yaml, ./charts/*/Chart.yaml, ./helm/Chart.yaml
Found: `./chart/Chart.yaml`

## Values Override
```yaml
replicaCount: 2
image:
  repository: image-registry.openshift-image-registry.svc:5000/myproject/myapp
  tag: latest
service:
  port: 8080
resources:
  limits:
    memory: 512Mi
```

## Deploy Command
```bash
helm install myapp ./chart/ -f values-override.yaml -n myproject
```

## Quick Commands
helm status myapp -n myproject
helm history myapp -n myproject
helm rollback myapp 1 -n myproject
REPORT_EOF

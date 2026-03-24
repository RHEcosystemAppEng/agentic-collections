#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Deployment Plan: customer-portal

## Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customer-portal
spec:
  replicas: 1
  selector:
    matchLabels:
      app: customer-portal
  template:
    metadata:
      labels:
        app: customer-portal
    spec:
      containers:
      - name: customer-portal
        image: image-registry.openshift-image-registry.svc:5000/myproject/customer-portal:latest
        ports:
        - containerPort: 3000
```

## Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: customer-portal
spec:
  selector:
    app: customer-portal
  ports:
  - port: 3000
    targetPort: 3000
```

## Route
```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: customer-portal
spec:
  to:
    kind: Service
    name: customer-portal
  port:
    targetPort: 3000
  tls:
    termination: edge
```

### Internal DNS: `http://customer-portal.myproject.svc.cluster.local:3000`

### On failure: Debug Pod (/debug-pod) or Debug Network (/debug-network)
REPORT_EOF

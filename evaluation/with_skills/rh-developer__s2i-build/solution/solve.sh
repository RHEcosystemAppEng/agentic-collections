#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# S2I Build Configuration

## Problem
Python Flask app uses `main.py` as entry point, not the default `app.py`.

## Solution
1. Create ImageStream for output image
2. Create BuildConfig with `APP_MODULE=main:app` in `sourceStrategy.env`
3. Ensure `gunicorn` is in `requirements.txt`

### ImageStream
```yaml
apiVersion: image.openshift.io/v1
kind: ImageStream
metadata:
  name: flask-app
  labels:
    app: flask-app
spec:
  lookupPolicy:
    local: false
```

### BuildConfig
```yaml
apiVersion: build.openshift.io/v1
kind: BuildConfig
metadata:
  name: flask-app
spec:
  source:
    type: Git
    git:
      uri: https://github.com/example/flask-app
  strategy:
    type: Source
    sourceStrategy:
      from:
        kind: ImageStreamTag
        name: python:3.11-ubi9
        namespace: openshift
      env:
      - name: APP_MODULE
        value: "main:app"
  output:
    to:
      kind: ImageStreamTag
      name: flask-app:latest
```

### S2I Build Phases
- **Assemble**: Install dependencies from requirements.txt (including gunicorn), compile assets. Customizable via `.s2i/bin/assemble`.
- **Run**: Start the application using gunicorn with APP_MODULE. Customizable via `.s2i/bin/run`.

### Why APP_MODULE is needed
S2I Python startup sequence: app.sh → gunicorn+APP_MODULE → app.py → ERROR
Since entry is main.py (not app.py), gunicorn must be installed and APP_MODULE must point to main:app.
REPORT_EOF

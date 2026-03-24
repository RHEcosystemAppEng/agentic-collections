#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Image Recommendations

## Use Case Assessment
Production: prefer Minimal/Runtime. Development: prefer Full variant.

## 1. Python 3.11 Flask API
**Image**: `registry.access.redhat.com/ubi9/python-311`
**Variant**: Full (build tools needed for pip install)
**Verify**: `skopeo inspect docker://registry.access.redhat.com/ubi9/python-311`

## 2. Java 17 Quarkus (pre-built JAR)
**Image**: `registry.access.redhat.com/ubi9/openjdk-17-runtime`
**Variant**: Runtime (no build tools, smaller attack surface, faster startup)
**Rationale**: Pre-built JAR doesn't need compilation tools. Runtime variant is ~60% smaller. Security: reduced attack surface.
**Verify**: `skopeo inspect docker://registry.access.redhat.com/ubi9/openjdk-17-runtime`
REPORT_EOF

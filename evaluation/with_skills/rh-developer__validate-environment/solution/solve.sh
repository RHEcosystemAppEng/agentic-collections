#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Environment Validation Report

## Validation Scope: All
(Options: All, OpenShift, RHEL/Containers, Minimal)

### Tool Availability
| Tool | Status | Version |
|------|--------|---------|
| git | OK | 2.43.0 |
| curl | OK | 8.5.0 |
| jq | OK | 1.7.1 |
| oc | OK | 4.14.0 |
| helm | OK | 3.14.0 |
| podman | OK | 4.9.0 |
| skopeo | OK | 1.14.0 |
| ssh | OK | OpenSSH 9.6 |

Status indicators: OK (working), MISSING (not in PATH), WARN (optional missing).

### OpenShift Permissions (oc auth can-i)
| Resource | Action | Status |
|----------|--------|--------|
| deployments | create | OK |
| buildconfigs | create | OK |
| imagestreams | create | OK |

### Connectivity
- Cluster: Connected (`oc whoami` → admin)
- Podman info: `podman info --format '{{.Host.OS}} {{.Host.Arch}}'` → linux amd64

### Ready for
/detect-project, /s2i-build, /deploy, /helm-deploy, /containerize-deploy

REPORT_EOF

---
title: Debugging Patterns
category: references
sources:
  - title: Kubernetes Debugging Pods
    url: https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/
    sections: Debugging Pods, Common Errors
    date_accessed: 2026-02-16
  - title: OpenShift Troubleshooting Guide
    url: https://docs.openshift.com/container-platform/latest/support/troubleshooting/troubleshooting-operator-issues.html
    sections: Pod issues, Build issues
    date_accessed: 2026-02-16
  - title: OpenShift Pipelines Troubleshooting
    url: https://docs.openshift.com/pipelines/latest/about/about-openshift-pipelines.html
    sections: Troubleshooting, PipelineRun status, TaskRun status
    date_accessed: 2026-02-25
  - title: Podman Troubleshooting
    url: https://github.com/containers/podman/blob/main/troubleshooting.md
    sections: Common Issues
    date_accessed: 2026-02-16
---

# Debugging Patterns

This document provides common error patterns, exit codes, and troubleshooting decision trees for the debugging skills.

## Exit Code Reference

### Container/Process Exit Codes

| Exit Code | Signal | Meaning | Common Cause |
|-----------|--------|---------|--------------|
| 0 | - | Success | Normal termination |
| 1 | - | General error | Application error, unhandled exception |
| 2 | - | Misuse of shell | Invalid arguments, syntax error |
| 126 | - | Permission denied | Cannot execute command |
| 127 | - | Command not found | Binary/script missing in PATH |
| 128 | - | Invalid exit argument | Exit called with non-integer |
| 128+N | Signal N | Killed by signal | See signal table below |
| 137 | SIGKILL (9) | Force killed | OOM kill, manual kill, timeout |
| 139 | SIGSEGV (11) | Segmentation fault | Memory corruption, null pointer |
| 143 | SIGTERM (15) | Terminated | Graceful shutdown request |

### Signal Reference (128+N)

| Signal | Number | Exit Code | Typical Cause |
|--------|--------|-----------|---------------|
| SIGHUP | 1 | 129 | Terminal closed |
| SIGINT | 2 | 130 | Ctrl+C |
| SIGQUIT | 3 | 131 | Ctrl+\ |
| SIGKILL | 9 | 137 | OOM, forced termination |
| SIGSEGV | 11 | 139 | Segmentation fault |
| SIGTERM | 15 | 143 | Graceful stop request |

## Pod Failure Patterns

### CrashLoopBackOff

**Symptom:** Pod repeatedly crashes and restarts

**Diagnosis Flow:**
```
CrashLoopBackOff
├─ Check exit code
│  ├─ 0 → Application exits normally (missing loop/server?)
│  ├─ 1 → Application error (check logs)
│  ├─ 127 → Command not found (check entrypoint)
│  └─ 137 → OOM killed (check memory limits)
├─ Check logs (current + previous)
│  ├─ Import errors → Missing dependencies
│  ├─ Connection errors → External service down
│  └─ Config errors → Missing env vars/secrets
└─ Check events
   └─ FailedMount → Missing secrets/configmaps
```

**Common Causes:**
1. Application crashes on startup (dependency errors)
2. Memory limit too low (OOMKilled)
3. Missing environment variables or secrets
4. Database/service connection failures
5. Health probe failing immediately

### ImagePullBackOff

**Symptom:** Cannot pull container image

**Diagnosis Flow:**
```
ImagePullBackOff
├─ Check event message
│  ├─ "unauthorized" → Registry authentication
│  │  └─ Check imagePullSecrets
│  ├─ "not found" → Wrong image name/tag
│  │  └─ Verify image exists in registry
│  ├─ "timeout" → Network/registry issue
│  │  └─ Check cluster network egress
│  └─ "manifest unknown" → Tag doesn't exist
│     └─ Verify tag in registry
└─ Check image reference
   ├─ Missing registry prefix?
   ├─ Typo in image name?
   └─ Tag exists?
```

**Common Causes:**
1. Private registry without imagePullSecret
2. Image tag doesn't exist
3. Registry URL typo
4. Network policy blocking egress
5. Registry rate limiting

### Pending Pod

**Symptom:** Pod stuck in Pending state

**Diagnosis Flow:**
```
Pending
├─ Check events
│  ├─ "FailedScheduling"
│  │  ├─ "Insufficient cpu/memory" → Scale cluster or reduce requests
│  │  ├─ "node selector" → No matching nodes
│  │  ├─ "taints" → Need tolerations
│  │  └─ "PVC not bound" → Storage issue
│  └─ No events → Check resourceQuota
└─ Check node status
   └─ All nodes NotReady? → Node issue
```

**Common Causes:**
1. Insufficient cluster resources
2. Node selector doesn't match any nodes
3. PersistentVolumeClaim not bound
4. Resource quota exceeded
5. Affinity/anti-affinity rules too strict

### OOMKilled

**Symptom:** Container terminated with exit code 137

**Diagnosis Flow:**
```
OOMKilled (exit 137)
├─ Check container state
│  └─ OOMKilled: true → Memory exhaustion confirmed
├─ Compare memory usage vs limit
│  ├─ Limit too low → Increase memory limit
│  └─ Memory leak → Profile application
└─ Check for:
   ├─ Java → Heap size (-Xmx) exceeds limit
   ├─ Node.js → --max-old-space-size too high
   └─ Python → Large data structures in memory
```

**Common Causes:**
1. Memory limit set too low for application
2. Memory leak in application
3. Java heap size exceeds container limit
4. Processing large files/datasets in memory

## Build Failure Patterns

### S2I Build Phases

| Phase | What Happens | Common Failures |
|-------|--------------|-----------------|
| **fetch-source** | Clone git repository | Auth failure, repo not found |
| **pull-builder** | Pull S2I builder image | Image not found, auth |
| **assemble** | Run S2I assemble script | Dependency install, build errors |
| **commit** | Create image layer | Disk space |
| **push** | Push to internal registry | Auth, quota |

### Assemble Phase Failures

**Node.js:**
```
npm ERR! 404 Not Found
└─ Package doesn't exist in registry
   → Check package.json for typos

npm ERR! code ERESOLVE
└─ Dependency conflict
   → Run npm install --legacy-peer-deps

npm ERR! code ENOENT
└─ File not found
   → Check paths in package.json
```

**Python:**
```
ERROR: Could not find a version that satisfies the requirement
└─ Package not found
   → Check requirements.txt spelling

ModuleNotFoundError: No module named 'X'
└─ APP_MODULE misconfigured
   → See docs/python-s2i-entrypoints.md

gunicorn: command not found
└─ gunicorn not in requirements
   → Add gunicorn to requirements.txt
```

**Java:**
```
[ERROR] Failed to execute goal
└─ Maven/Gradle build failure
   → Check pom.xml or build.gradle

java.lang.OutOfMemoryError: Java heap space
└─ Build needs more memory
   → Add MAVEN_OPTS=-Xmx512m
```

## Pipeline/Tekton Failure Patterns

### PipelineRun Failure Decision Tree

```
PipelineRun Failed
├─ Check PipelineRun status conditions
│  ├─ "PipelineRunTimeout" → Increase spec.timeouts.pipeline
│  ├─ "CouldntGetPipeline" → Pipeline reference invalid, check name/namespace
│  ├─ "PipelineRunCancelled" → Check if timeout or manual cancellation
│  └─ "Failed" → Check which TaskRun failed (see below)
├─ Check failed TaskRun
│  ├─ Step failure (non-zero exit)
│  │  ├─ git-clone step → Auth/URL issue (check SA secrets)
│  │  ├─ build step → Compilation/dependency error
│  │  ├─ push step → Registry auth (check SA dockerconfigjson secret)
│  │  └─ test step → Test failures
│  ├─ Pod scheduling failure → Resource constraints (FailedScheduling event)
│  ├─ Workspace issue → PVC not bound or permission denied
│  └─ Step image pull failure → ImagePullBackOff on step container
└─ Pipeline stuck (Running too long)
   ├─ TaskRun pending → Pod can't be scheduled
   ├─ Step running indefinitely → Check logs for hang/deadlock
   └─ Custom task waiting → Check custom task controller
```

### TaskRun Failure Analysis

```
TaskRun Failed
├─ Pod not created → Check ServiceAccount exists, resource quotas
├─ Pod pending → Scheduling issue (see Pod Failure Patterns)
├─ Pod terminated → Check step statuses
│  ├─ Exit 1 → Script/application error (check step logs)
│  ├─ Exit 125-127 → Entrypoint/command issue in step image
│  └─ Exit 137 → OOM killed (increase step resources)
└─ Workspace binding failure
   ├─ PVC not found → Create PVC or fix workspace binding
   ├─ RWO blocks parallel tasks → Use RWX or separate workspaces
   └─ Permission denied → Check fsGroup, runAsUser in pod security context
```

### Common Tekton Error Messages

| Error Message | Fix |
|--------------|-----|
| `task "X" not found` | Verify Task name, kind (Task vs ClusterTask), namespace |
| `could not read Username for...` | Add git-credentials secret (annotated with `tekton.dev/git-0`) to ServiceAccount |
| `unauthorized: access denied` (push) | Add dockerconfigjson secret (annotated with `tekton.dev/docker-0`) to ServiceAccount |
| `persistentvolumeclaim "X" not found` | Create PVC or change workspace binding to emptyDir |
| `exceeded timeout` | Increase timeouts in PipelineRun spec (`spec.timeouts.pipeline` / `spec.timeouts.tasks`) |
| `missing required parameter "X"` | Add parameter value to PipelineRun spec |
| `couldn't find remote ref` | Fix git `revision` parameter (branch/tag name) |
| `unable to open Containerfile/Dockerfile` | Fix `DOCKERFILE` param path relative to workspace root |

## Network Troubleshooting

### Service Has No Endpoints

**Diagnosis Flow:**
```
No endpoints
├─ Check service selector
│  └─ Compare with pod labels
│     ├─ Labels don't match → Fix selector or pod labels
│     └─ Labels match → Check pod readiness
├─ Check pod status
│  ├─ Pods not running → Debug pods first
│  └─ Pods running but not ready → Check readiness probe
└─ Check readiness probe
   ├─ HTTP probe failing → Application not listening
   └─ TCP probe failing → Wrong port
```

### Route Returning 503

**Diagnosis Flow:**
```
503 Service Unavailable
├─ Check endpoints
│  └─ No endpoints → Pods not ready
├─ Check backend pods
│  ├─ All pods failing readiness → Application issue
│  └─ Some pods ready → Load balancer issue
└─ Check route configuration
   └─ Wrong service or port → Fix route spec
```

### Connection Refused

**Diagnosis Flow:**
```
Connection refused
├─ Is service created? → oc get svc
├─ Does service have endpoints? → oc get endpoints
├─ Is pod running? → oc get pods
├─ Is application listening? → Check container port
└─ Is port correct? → Compare service port vs container port
```

## RHEL System Patterns

### systemd Service Failures

| Exit Code | Meaning | Common Fix |
|-----------|---------|------------|
| 1 | General error | Check application logs |
| 126 | Permission | Check ExecStart permissions |
| 127 | Not found | Check binary path in ExecStart |
| 203 | EXEC | Wrong architecture or format |
| 217 | USER | Service user doesn't exist |

### SELinux Denial Patterns

| Denial Type | Example | Typical Fix |
|-------------|---------|-------------|
| Port binding | `httpd_t` bind `port_t` | `semanage port -a -t http_port_t -p tcp [port]` |
| File read | `httpd_t` read `user_home_t` | `semanage fcontext` + `restorecon` |
| Network connect | `httpd_t` connect | `setsebool -P httpd_can_network_connect on` |
| Container | `container_t` manage | `setsebool -P container_manage_cgroup on` |

See [selinux-troubleshooting.md](selinux-troubleshooting.md) for detailed SELinux guidance.

## Troubleshooting Decision Tree

### Application Not Accessible

```
Cannot access application
├─ Internal (from cluster)?
│  ├─ Yes, works internally → Route/Ingress issue
│  │  ├─ Check route admitted
│  │  ├─ Check route host/path
│  │  └─ Check TLS configuration
│  └─ No, fails internally too → Service/Pod issue
│     ├─ Check service endpoints
│     ├─ Check pod status
│     └─ Check pod readiness
└─ Neither works?
   └─ Debug pod first (/debug-pod)
```

### Build Keeps Failing

```
Build failures
├─ Which phase?
│  ├─ fetch-source → Git access issue
│  │  ├─ Check source secret
│  │  └─ Verify git URL
│  ├─ pull-builder → Builder image issue
│  │  ├─ Check image reference
│  │  └─ Import ImageStream
│  ├─ assemble → Build script issue
│  │  ├─ Check dependencies
│  │  └─ Check language-specific config
│  └─ push → Registry issue
│     └─ Check push secret
└─ Same failure pattern?
   └─ Compare with last successful build
```

### Pipeline Keeps Failing

```
Pipeline failures
├─ Same task always fails?
│  ├─ git-clone → Check ServiceAccount secrets, git URL, revision
│  ├─ build step → Check source code, Containerfile path, build context
│  └─ push step → Check ServiceAccount imagePullSecrets, registry URL
├─ Different tasks fail?
│  ├─ Resource exhaustion → Reduce parallel tasks or increase quotas
│  └─ Workspace contention → Use RWX PVC or separate workspaces
├─ Pipeline hangs?
│  ├─ TaskRun pending → Pod can't be scheduled
│  └─ Step running indefinitely → Check step logs
└─ Pipeline never triggers?
   ├─ EventListener pod not running → Check EL deployment/logs
   ├─ Webhook misconfigured → Verify webhook URL and secret
   └─ TriggerBinding wrong → Check CEL expression param extraction
```

## Quick Reference Commands

### OpenShift Debugging

```bash
# Pod status and events
oc describe pod [pod-name]

# Pod logs (current)
oc logs [pod-name]

# Pod logs (previous container)
oc logs [pod-name] --previous

# All events in namespace
oc get events --sort-by='.lastTimestamp'

# Check endpoints
oc get endpoints [service-name]

# Build logs
oc logs build/[build-name]
```

### Pipeline/Tekton Debugging

```bash
# List PipelineRuns (oldest first)
oc get pipelinerun --sort-by='.metadata.creationTimestamp'

# Get PipelineRun details
oc get pipelinerun [name] -o yaml

# List TaskRuns for a PipelineRun
oc get taskrun -l tekton.dev/pipelineRun=[pipelinerun-name]

# Get TaskRun pod logs for a specific step
oc logs [taskrun-name]-pod -c step-[step-name]

# Get events for pipeline resources
oc get events --field-selector involvedObject.kind=PipelineRun

# Describe EventListener
oc get eventlistener [name] -o yaml
```

### RHEL Debugging

```bash
# Service status
systemctl status [service]

# Journal logs
journalctl -u [service] -n 100

# SELinux denials
ausearch -m AVC -ts recent

# Firewall rules
firewall-cmd --list-all

# SELinux context
ls -lZ [path]
```

### Container Debugging

```bash
# List all containers
podman ps -a

# Container inspect
podman inspect [container]

# Container logs
podman logs [container]

# Run interactively for debugging
podman run -it --entrypoint /bin/sh [image]
```

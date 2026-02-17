---
name: debug-container
description: |
  Diagnose local container issues with Podman/Docker including image pull errors, container startup failures, OOM kills, and networking problems. Automates multi-step diagnosis: container inspect, logs retrieval, image analysis, and resource constraint checking. Use this skill when containers fail to run locally before deployment. Triggers on /debug-container command or phrases like "container won't start", "podman run fails", "local container crashing", "container exits immediately".
user_invocable: true
---

# /debug-container Skill

Diagnose local Podman/Docker container issues by automatically gathering container status, logs, and configuration.

## Overview

```
[Identify Container] → [Inspect] → [Logs] → [Image Analysis] → [Resource Check] → [Summary]
```

**This skill diagnoses:**
- Container startup failures
- Immediate exit (exit codes)
- OOM kills
- Image pull errors
- Entrypoint/CMD issues
- Volume mount problems

## Prerequisites

1. Podman or Docker installed locally
2. Container or image name is known

## Critical: Human-in-the-Loop Requirements

See [Human-in-the-Loop Requirements](../../docs/human-in-the-loop.md) for mandatory checkpoint behavior.

**IMPORTANT:** This skill requires explicit user confirmation at each step. You MUST:
1. **Wait for user confirmation** before executing diagnostic actions
2. **Do NOT proceed** to the next step until the user explicitly approves
3. **Present findings clearly** and ask if user wants deeper analysis
4. **Never auto-execute** remediation actions without user approval

If the user says "no" or wants to focus on specific areas, address their concerns before proceeding.

## Critical: Prefer MCP Tools

**IMPORTANT:** Prefer MCP tools over CLI commands for better integration and user experience:
1. **Search for MCP tools first** - Use `ToolSearch` to load Podman MCP tools (e.g., `+podman container_inspect`) before diagnostic actions
2. **Use MCP when available** - Prefer `container_list`, `container_inspect`, `container_logs` over `podman`/`docker` commands

## Trigger

- User types `/debug-container`
- User says "container won't start", "podman run fails"
- User says "container exits immediately", "container crashing"
- User says "can't pull image", "image not found"
- User says "OOM", "out of memory", "exit code 137"

## Input Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `CONTAINER` | Container name or ID | Auto-detect from recent |
| `IMAGE` | Image name to debug | From container |

## Workflow

### Step 1: Identify Target Container

```markdown
## Container Debugging

What would you like me to debug?

1. **Running/stopped container** - Debug an existing container
2. **Failed container run** - Debug a recent failed `podman run`
3. **Image issue** - Debug image pull or build problems
4. **List containers** - Show all containers (including stopped)

Select an option or enter a container name/ID:
```

**WAIT for user response.** Do NOT proceed until user identifies the target.

If user selects "List containers":
Use Podman MCP `container_list`:

```markdown
## Containers

| Container ID | Image | Status | Created | Names |
|--------------|-------|--------|---------|-------|
| [abc123] | [myapp:latest] | Exited (1) 5 minutes ago | [time] | [myapp] |
| [def456] | [nginx:latest] | Up 2 hours | [time] | [webserver] |
| [ghi789] | [postgres:15] | Exited (137) 1 hour ago | [time] | [db] |

Which container would you like me to debug?
```

**WAIT for user to select a container.**

### Step 2: Inspect Container

Use Podman MCP `container_inspect`:

```markdown
## Container Inspection: [container-name]

**Basic Info:**
| Field | Value |
|-------|-------|
| ID | [full-id] |
| Image | [image:tag] |
| Created | [timestamp] |
| Status | [running/exited/created] |

**State:**
| Field | Value |
|-------|-------|
| Running | [true/false] |
| Paused | [true/false] |
| Restarting | [true/false] |
| OOMKilled | [true/false] |
| Exit Code | [code] |
| Error | [error message or empty] |
| Started At | [timestamp] |
| Finished At | [timestamp] |

**Configuration:**
| Setting | Value |
|---------|-------|
| Entrypoint | [entrypoint] |
| Cmd | [command] |
| Working Dir | [workdir] |
| User | [user or root] |

**Port Mappings:**
| Container Port | Host Binding |
|----------------|--------------|
| [8080/tcp] | [0.0.0.0:8080] |

**Volume Mounts:**
| Source | Destination | Mode |
|--------|-------------|------|
| [/host/path] | [/container/path] | [rw/ro] |

**Environment Variables:**
| Name | Value |
|------|-------|
| [VAR1] | [value] |
| [VAR2] | [value] |

**Quick Assessment:**
[Based on state, provide initial assessment - e.g., "Container exited with code 1 - application error. OOMKilled=false, so not a memory issue."]

Continue with container logs? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 3: Get Container Logs

Use Podman MCP `container_logs`:

```markdown
## Container Logs: [container-name]

**Last 100 lines:**
```
[container log output]
```

**Log Analysis:**

[Analyze logs and identify errors:]

**Errors Found:**
- [error 1 - e.g., "Error: Cannot find module 'express'"]
- [error 2 - e.g., "FATAL: password authentication failed for user 'app'"]
- [error 3 - e.g., "bind: address already in use"]

**Error Categories:**
| Category | Count | First Occurrence |
|----------|-------|------------------|
| Module/Import | [X] | [line] |
| Connection | [Y] | [line] |
| Permission | [Z] | [line] |

Continue to check image? (yes/no/skip)
```

**WAIT for user confirmation before proceeding.**

### Step 4: Analyze Image

Use Podman MCP `image_list` to check the image:

```markdown
## Image Analysis: [image:tag]

**Image Info:**
| Field | Value |
|-------|-------|
| Repository | [repo] |
| Tag | [tag] |
| ID | [image-id] |
| Created | [timestamp] |
| Size | [size] |

**Image Layers:**
[If available, show layer info]

**Image Issues:**
- [Issue 1 - e.g., "Image is 2 years old - may have outdated dependencies"]
- [Issue 2 - e.g., "Using 'latest' tag - version not pinned"]

**Entrypoint/CMD Check:**

[Compare image defaults with container override]

| Setting | Image Default | Container Override |
|---------|---------------|-------------------|
| Entrypoint | [image-entrypoint] | [container-entrypoint or "none"] |
| Cmd | [image-cmd] | [container-cmd or "none"] |

**Potential Issues:**
- [Issue - e.g., "CMD is empty and no command provided at runtime"]
- [Issue - e.g., "Entrypoint is shell script but container run overrides it"]

Continue to resource analysis? (yes/no/skip)
```

**WAIT for user confirmation before proceeding.**

### Step 5: Resource Analysis

```markdown
## Resource Analysis

**Container Resource Limits:**
| Resource | Limit | Status |
|----------|-------|--------|
| Memory | [512m or unlimited] | [OK/WARNING: OOMKilled] |
| CPU | [1.0 or unlimited] | [OK] |
| PIDs | [unlimited] | [OK] |

**OOM Analysis:**

[If OOMKilled=true:]
**Container was killed due to Out of Memory!**

- Memory limit: [limit]
- Recommendation: Increase memory limit or optimize application

```bash
# Run with more memory
podman run --memory=1g [image]
```

**Port Binding Analysis:**

[Check if ports conflict:]

| Port | Requested | Status |
|------|-----------|--------|
| [8080] | 0.0.0.0:8080 | [OK/ERROR: already in use] |

[If port conflict:]
```bash
# Find process using port
lsof -i :[port]
# Or use different port
podman run -p 8081:8080 [image]
```

Continue to diagnosis summary? (yes/no)
```

**WAIT for user confirmation before proceeding.**

### Step 6: Present Diagnosis Summary

```markdown
## Diagnosis Summary: [container-name]

### Root Cause

**Primary Issue:** [Categorized root cause]

| Category | Status | Details |
|----------|--------|---------|
| Container State | [OK/FAIL] | [exit code, status] |
| Entrypoint/CMD | [OK/FAIL] | [details] |
| Dependencies | [OK/FAIL] | [missing modules] |
| Environment | [OK/FAIL] | [missing vars] |
| Volumes | [OK/FAIL] | [mount issues] |
| Ports | [OK/FAIL] | [binding issues] |
| Memory | [OK/FAIL] | [OOM status] |

### Detailed Findings

**[Category 1: e.g., Exit Code 1 - Application Error]**
- Problem: [specific problem - e.g., "Cannot find module 'express'"]
- Evidence: [from logs]
- Impact: [container exits immediately]

**[Category 2: e.g., Volume Mount Issue]**
- Problem: [specific problem - e.g., "Permission denied on /data"]
- Evidence: [from logs]
- Impact: [application cannot access data]

### Exit Code Reference

| Exit Code | Meaning | Your Container |
|-----------|---------|----------------|
| 0 | Success | [match?] |
| 1 | General error | [match?] |
| 126 | Permission problem | [match?] |
| 127 | Command not found | [match?] |
| 137 | SIGKILL (OOM) | [match?] |
| 139 | Segfault | [match?] |
| 143 | SIGTERM | [match?] |

### Recommended Actions

1. **[Action 1]** - [description]
   ```bash
   podman run [fixed-command]
   ```

2. **[Action 2]** - [description]
   ```bash
   [command to fix - e.g., podman run --memory=1g ...]
   ```

3. **[Action 3]** - [description]

### Test Fix

```bash
# Remove failed container
podman rm [container-name]

# Run with fixes applied
podman run [corrected-options] [image]

# Or run interactively to debug
podman run -it --entrypoint /bin/sh [image]
```

---

Would you like me to:
1. Execute one of the recommended fixes
2. Run container interactively for debugging
3. Inspect the image layers
4. Remove and recreate the container
5. Exit debugging

Select an option:
```

**WAIT for user to select next action.**

## Exit Code Reference

| Exit Code | Signal | Meaning | Common Cause |
|-----------|--------|---------|--------------|
| 0 | - | Success | Normal exit |
| 1 | - | General error | Application error, unhandled exception |
| 2 | - | Misuse of shell | Invalid arguments |
| 126 | - | Permission denied | Cannot execute entrypoint |
| 127 | - | Command not found | Entrypoint binary missing |
| 128+N | Signal N | Killed by signal | See signal table |
| 137 | SIGKILL (9) | Force killed | OOM kill, `podman kill` |
| 139 | SIGSEGV (11) | Segmentation fault | Memory corruption |
| 143 | SIGTERM (15) | Terminated | `podman stop`, graceful shutdown |

## Common Container Issues

### Startup Failures

| Issue | Symptom | Diagnosis | Fix |
|-------|---------|-----------|-----|
| Missing entrypoint | Exit 127 | "executable not found" | Check ENTRYPOINT/CMD |
| Wrong command | Exit 127 | "no such file" | Verify command path |
| Permission denied | Exit 126 | "permission denied" | Check file permissions |
| Missing dependency | Exit 1 | "cannot find module" | Add dependency to image |
| Port conflict | Exit 1 | "address in use" | Use different port |

### Runtime Issues

| Issue | Symptom | Diagnosis | Fix |
|-------|---------|-----------|-----|
| OOM killed | Exit 137 | OOMKilled=true | Increase memory limit |
| Volume permission | Exit 1 | "permission denied" | Use :Z/:z labels or fix perms |
| Missing env var | Exit 1 | "undefined" errors | Add -e VAR=value |
| Network issue | Exit 1 | "connection refused" | Check network mode |

### SELinux Volume Issues

On RHEL/Fedora with SELinux, volume mounts may need labels:

```bash
# Shared label (multiple containers can access)
podman run -v /host/path:/container/path:z [image]

# Private label (only this container)
podman run -v /host/path:/container/path:Z [image]
```

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `container_list` | List containers |
| `container_inspect` | Get container details |
| `container_logs` | Get container output |
| `image_list` | Check image info |

## Output Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CONTAINER_ID` | Container ID | `abc123def456` |
| `CONTAINER_NAME` | Container name | `myapp` |
| `CONTAINER_IMAGE` | Image used | `myapp:latest` |
| `EXIT_CODE` | Exit code | `137` |
| `OOM_KILLED` | OOM status | `true` / `false` |
| `ROOT_CAUSE` | Identified cause | `Out of memory` |

## Dependencies

### Required MCP Servers
- `podman` (Podman MCP server)

### Related Skills
- `/debug-rhel` - For systemd service issues on RHEL hosts
- `/recommend-image` - To select a better base image

## Reference Documentation

For detailed guidance, see:
- [docs/debugging-patterns.md](../../docs/debugging-patterns.md) - Common error patterns, exit codes
- [docs/prerequisites.md](../../docs/prerequisites.md) - Required tools (podman)

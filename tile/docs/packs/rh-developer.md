# Red Hat Developer Collection (rh-developer)

Developer skills for containerizing and deploying applications to OpenShift clusters and standalone RHEL systems, plus debugging workflows. Integrates with OpenShift MCP, Podman MCP, GitHub MCP, and optionally Red Hat Lightspeed MCP.

- **Persona**: Developer
- **Marketplaces**: Claude Code, Cursor

## Prerequisites

### MCP Servers

Configure in `rh-developer/.mcp.json`.

```json { .api }
{
  "mcpServers": {
    "openshift": {
      "command": "bash",
      "args": ["-c", "U=(); [ \"$(uname -s)\" = Linux ] && U=(--userns=keep-id:uid=65532,gid=65532); exec podman run \"${U[@]}\" --rm -i --network=host -v \"${KUBECONFIG}:/kubeconfig:ro,Z\" --entrypoint /app/kubernetes-mcp-server quay.io/ecosystem-appeng/openshift-mcp-server:latest --kubeconfig /kubeconfig --toolsets core,config,helm,kubevirt,observability,ossm"],
      "env": { "KUBECONFIG": "${KUBECONFIG}" },
      "description": "OpenShift MCP server (toolsets: core,config,helm,kubevirt,observability,ossm)"
    },
    "podman": {
      "command": "npx",
      "args": ["-y", "podman-mcp-server@latest"],
      "description": "Podman MCP for local container builds and image management"
    },
    "github": {
      "command": "podman",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}" },
      "description": "GitHub MCP for repository browsing and code analysis"
    },
    "lightspeed-mcp": {
      "command": "podman",
      "args": ["run", "--rm", "-i", "--env", "LIGHTSPEED_CLIENT_ID", "--env", "LIGHTSPEED_CLIENT_SECRET", "quay.io/redhat-services-prod/insights-management-tenant/insights-mcp/red-hat-lightspeed-mcp:latest"],
      "env": { "LIGHTSPEED_CLIENT_ID": "${LIGHTSPEED_CLIENT_ID}", "LIGHTSPEED_CLIENT_SECRET": "${LIGHTSPEED_CLIENT_SECRET}" },
      "description": "Red Hat Lightspeed (optional: used by /debug-rhel and /rhel-deploy)"
    }
  }
}
```

### Environment Variables

| Variable | Required By | Description |
|----------|-------------|-------------|
| `KUBECONFIG` | openshift | Path to kubeconfig file with cluster access |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | github | GitHub PAT for repository analysis |
| `LIGHTSPEED_CLIENT_ID` | lightspeed-mcp | Optional: for /debug-rhel, /rhel-deploy |
| `LIGHTSPEED_CLIENT_SECRET` | lightspeed-mcp | Optional: for /debug-rhel, /rhel-deploy |

## Capabilities

### /containerize-deploy — End-to-End Deploy Orchestration

Orchestrating skill: from source code to running application on OpenShift or RHEL in one guided workflow.

```markdown { .api }
Skill: containerize-deploy
Invocation: /containerize-deploy
Model: inherit
Color: green

Orchestration:
  [Intro] → [/detect-project] → [Target selection] → [Strategy selection]
     → OpenShift path: [/s2i-build] → [/deploy | /helm-deploy]
     → RHEL path:      [/rhel-deploy]

Supports: S2I, Podman, Helm deployment strategies for OpenShift;
          Podman/native for RHEL hosts.
Features: User confirmation checkpoints, resume after interruption, rollback on failure.

Use when: user wants source code → running app in one guided workflow
```

---

### /detect-project — Project Language/Framework Detection

Analyzes project to detect language, framework, version, and recommends build strategy.

```markdown { .api }
Skill: detect-project
Invocation: /detect-project
Model: inherit
Color: cyan

Supports: Node.js, Python, Java, Go, Ruby, .NET, PHP, Perl

Inputs: local project directory path or GitHub repository URL
GitHub analysis: Uses github-mcp-server tools (list_directory, get_file_contents)
  DO NOT clone remote repos unless user explicitly selects "Clone & Inspect"

Outputs: language, framework, version requirements, recommended build strategy
Run before: /s2i-build, /rhel-deploy, /recommend-image
```

---

### /recommend-image — Container Image Recommendation

Recommends optimal S2I builder image or container base image based on project analysis.

```markdown { .api }
Skill: recommend-image
Invocation: /recommend-image
Model: inherit
Color: cyan

Considers: language/framework, use-case requirements, security posture,
           deployment target (production vs development)
Supports: GitHub URL analysis (delegates to /detect-project)
Base images: Red Hat UBI-based images for Node.js, Python, Java, Go, Ruby, .NET, PHP, Perl

Use when: advanced image selection beyond basic version matching is needed
```

---

### /s2i-build — Source-to-Image Build on OpenShift

Creates BuildConfig and ImageStream resources on OpenShift and triggers S2I build.

```markdown { .api }
Skill: s2i-build
Invocation: /s2i-build
Model: inherit
Color: green

Prerequisites: User logged in to OpenShift cluster, project directory analyzed

Creates: BuildConfig, ImageStream
Handles: namespace verification, resource creation with user confirmation,
         build log streaming, failure recovery

Human-in-the-Loop: Required before creating cluster resources
Run after: /detect-project
Run before: /deploy
```

---

### /deploy — Deploy to OpenShift

Creates Kubernetes Deployment, Service, and Route to deploy and expose an application.

```markdown { .api }
Skill: deploy
Invocation: /deploy
Model: inherit
Color: green

Prerequisites: Container image exists (ImageStream or external registry),
               target namespace exists, user logged in

Creates: Deployment, Service, Route (HTTPS)
Handles: port detection, replica configuration, rollout monitoring, rollback on failure

Human-in-the-Loop: Required before creating cluster resources
Run after: /s2i-build
```

---

### /helm-deploy — Helm Chart Deployment

Deploys applications to OpenShift using Helm charts.

```markdown { .api }
Skill: helm-deploy
Invocation: /helm-deploy
Model: inherit
Color: green

Supports: existing Helm charts, creating new charts
Handles: chart detection, values customization, install/upgrade, rollback
Requires: kubernetes MCP Helm tools (from openshift MCP server)

Human-in-the-Loop: Required before deploying
```

---

### /rhel-deploy — Deploy to Standalone RHEL

Deploys applications to standalone RHEL/Fedora/CentOS systems using Podman containers + systemd, or native dnf builds.

```markdown { .api }
Skill: rhel-deploy
Invocation: /rhel-deploy (CRITICAL: use THIS skill when user types /rhel-deploy)
Model: inherit
Color: yellow

Target: standalone RHEL/Fedora/CentOS hosts — NOT OpenShift

Handles: SSH connectivity, SELinux configuration, firewall-cmd rules,
         systemd unit creation, Podman container deployment, dnf builds

Triggers: /rhel-deploy, "deploy to RHEL", "deploy to Fedora", "deploy to my server via SSH"
```

---

### /validate-environment — Environment Validation

Checks tool installation, cluster connectivity, and permissions.

```markdown { .api }
Skill: validate-environment
Invocation: /validate-environment
Model: inherit
Color: cyan

Validates tools: oc, helm, podman, git, skopeo (checks presence and versions)
Validates: cluster connectivity via KUBECONFIG, namespace permissions

Use before: running other deployment skills
```

---

### /debug-pod — Pod Failure Diagnosis

Diagnoses pod failures on OpenShift.

```markdown { .api }
Skill: debug-pod
Invocation: /debug-pod
Model: inherit
Color: cyan

Diagnoses: CrashLoopBackOff, ImagePullBackOff, OOMKilled, pending pods

Automates: pod status, events, current logs, previous logs, resource constraints

Triggers: /debug-pod, "my pod is crashing", "pod won't start", "CrashLoopBackOff",
          "ImagePullBackOff", "OOMKilled"
```

---

### /debug-build — Build Failure Diagnosis

Diagnoses OpenShift build failures.

```markdown { .api }
Skill: debug-build
Invocation: /debug-build
Model: inherit
Color: cyan

Diagnoses: S2I builds, Docker/Podman builds, BuildConfig issues
Automates: BuildConfig validation, build pod logs, registry auth, source access

Triggers: /debug-build, "build failed", "S2I error", "can't pull builder image",
          "can't push to registry", "build timeout"
```

---

### /debug-container — Local Container Diagnosis

Diagnoses local container issues with Podman/Docker.

```markdown { .api }
Skill: debug-container
Invocation: /debug-container
Model: inherit
Color: cyan

Diagnoses: image pull errors, startup failures, OOM kills, networking problems
Automates: container inspect, logs, image analysis, resource constraint checking

Use when containers fail locally before deployment
Triggers: /debug-container, "container won't start", "podman run fails",
          "local container crashing", "container exits immediately"
```

---

### /debug-network — OpenShift Network Diagnosis

Diagnoses OpenShift service connectivity issues.

```markdown { .api }
Skill: debug-network
Invocation: /debug-network
Model: inherit
Color: cyan

Diagnoses: DNS resolution, service endpoints, route ingress, network policies
Automates: service endpoint verification, pod selector matching, route status,
           network policy analysis

Triggers: /debug-network, "can't reach service", "route returning 503",
          "pods can't communicate", "no endpoints"
```

---

### /debug-pipeline — Tekton Pipeline Diagnosis

Diagnoses OpenShift Pipelines (Tekton) CI/CD failures.

```markdown { .api }
Skill: debug-pipeline
Invocation: /debug-pipeline
Model: inherit
Color: cyan

Diagnoses: PipelineRun failures, TaskRun step errors, workspace/PVC binding,
           authentication problems
Automates: PipelineRun status, failed TaskRun analysis, step container logs,
           related resource checks

Triggers: /debug-pipeline, "pipeline failed", "PipelineRun error", "TaskRun failed",
          "tekton error", "pipeline stuck", "pipeline timeout"
```

---

### /debug-rhel — RHEL System Diagnosis

Diagnoses RHEL system issues for applications deployed via /rhel-deploy.

```markdown { .api }
Skill: debug-rhel
Invocation: /debug-rhel
Model: inherit
Color: cyan

Diagnoses: systemd service failures, SELinux denials, firewall blocking,
           system resource problems
Automates: journalctl log analysis, SELinux denial detection (ausearch),
           firewall rule inspection, systemd unit status

Triggers: /debug-rhel, "service won't start on RHEL", "SELinux blocking",
          "systemd failed", "firewall blocking"
Optional: Uses lightspeed-mcp for RHEL advisory data
```

## Developer Workflow Chains

```markdown { .api }
# OpenShift deployment flow
/validate-environment → /detect-project → /recommend-image → /s2i-build → /deploy
/validate-environment → /detect-project → /helm-deploy

# RHEL deployment flow
/validate-environment → /detect-project → /rhel-deploy

# End-to-end (orchestrated)
/containerize-deploy (handles all decisions and sub-skill orchestration)

# Debug flows
Pod issues:      /debug-pod
Build failures:  /debug-build
Local container: /debug-container
Network issues:  /debug-network
Pipeline issues: /debug-pipeline
RHEL issues:     /debug-rhel
```

## Reference Documentation

The rh-developer pack includes reference docs in `rh-developer/docs/` that skills consult during execution. Skills read these before invoking MCP tools.

```python { .api }
# rh-developer/docs/ reference documents:
# builder-images.md         — S2I builder image reference for Node.js, Python, Java, Go, Ruby,
#                             .NET, PHP, Perl (Red Hat UBI-based images)
#                             Used by: /recommend-image, /s2i-build
# image-selection-criteria.md — Use-case-aware criteria for selecting S2I vs container base images
#                             Used by: /recommend-image
# debugging-patterns.md     — Common debugging patterns for pod, build, container, network,
#                             pipeline, and RHEL issues
#                             Used by: /debug-pod, /debug-build, /debug-container,
#                                      /debug-network, /debug-pipeline, /debug-rhel
# prerequisites.md          — Environment verification guide (oc, helm, podman, git, skopeo)
#                             Used by: /validate-environment
# dynamic-validation.md     — Dynamic tool version validation patterns
#                             Used by: /validate-environment
# human-in-the-loop.md      — Confirmation checkpoint patterns for deployment skills
#                             Used by: /containerize-deploy, /s2i-build, /deploy, /helm-deploy
# rhel-deployment.md        — RHEL deployment reference: Podman, systemd, SELinux, firewall-cmd
#                             Used by: /rhel-deploy, /debug-rhel
# selinux-troubleshooting.md — SELinux denial diagnosis and resolution for RHEL deployments
#                             Used by: /debug-rhel, /rhel-deploy
# python-s2i-entrypoints.md — Python S2I build entrypoint reference (Procfile, app.sh patterns)
#                             Used by: /s2i-build, /detect-project
```

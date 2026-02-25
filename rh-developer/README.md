# Red Hat Developer Agentic Pack

A Claude Code plugin for building and deploying applications on Red Hat platforms.

## Skills

| Command                  | Description                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------ |
| `/detect-project`      | Analyze project to detect language, framework, and version                                 |
| `/recommend-image`     | Recommend optimal S2I builder or base image                                                |
| `/s2i-build`           | Build container images using Source-to-Image on OpenShift                                  |
| `/deploy`              | Deploy container images to OpenShift with Service and Route                                |
| `/helm-deploy`         | Deploy applications using Helm charts                                                      |
| `/rhel-deploy`         | Deploy to standalone RHEL/Fedora systems via SSH                                           |
| `/containerize-deploy` | End-to-end workflow from source to running app (use if not sure which strategy to choose)) |

### Troubleshooting

| Command              | Description                                                                                |
| -------------------- | ------------------------------------------------------------------------------------------ |
| `/debug-pod`         | Diagnose pod failures on OpenShift (CrashLoopBackOff, ImagePullBackOff, OOMKilled, pending pods) |
| `/debug-build`       | Diagnose OpenShift build failures (S2I builds, Docker/Podman builds, BuildConfig issues)   |
| `/debug-pipeline`    | Diagnose OpenShift Pipelines (Tekton) CI/CD failures (PipelineRun, TaskRun, step errors, workspaces) |
| `/debug-network`     | Diagnose OpenShift service connectivity (DNS, endpoints, routes, network policies)          |
| `/debug-container`   | Diagnose local Podman/Docker container issues (startup failures, OOM kills, image pull errors) |
| `/debug-rhel`        | Diagnose RHEL system issues (systemd failures, SELinux denials, firewall blocking)         |

### Environment

| Command                  | Description                                                                            |
| ------------------------ | -------------------------------------------------------------------------------------- |
| `/validate-environment`  | Check required tools and environment setup (oc, helm, podman, git, cluster connectivity) |

## Prerequisites

- OpenShift cluster access (for S2I and OpenShift deployments)
- Podman installed locally
- GitHub personal access token (for GitHub integration)

## MCP Servers

- **openshift** - OpenShift cluster management and Helm deployments
- **podman** - Container image management and local builds
- **github** - Repository browsing and code analysis

## Supported Languages

Node.js, Python, Java, Go, Ruby, .NET, PHP, Perl

## Installation

Add this plugin to your Claude Code configuration.

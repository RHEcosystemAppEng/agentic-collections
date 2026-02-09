---
name: containerize-deploy
description: |
  Complete end-to-end workflow for containerizing and deploying applications to OpenShift or standalone RHEL systems. Orchestrates /detect-project, /s2i-build, /deploy, /helm-deploy, and /rhel-deploy skills with user confirmation checkpoints at each phase. Supports S2I, Podman, Helm deployment strategies for OpenShift, and Podman/native deployments for RHEL hosts. Use this skill when user wants to go from source code to running application in one guided workflow. Supports resume after interruption and rollback on failure. Triggers on /containerize-deploy command.
---

# /containerize-deploy Skill

Provide a complete, guided workflow from local source code to running application on OpenShift or standalone RHEL systems. This skill orchestrates `/detect-project`, `/s2i-build`, `/deploy`, `/helm-deploy`, and `/rhel-deploy` with clear user checkpoints at each phase.

## Overview

```
[Intro] → [Detect] → [Target] → [Strategy] ──┬─→ [OpenShift Path] ─────┬─→ [Complete]
                        │                    │   [S2I/Podman/Helm]      │
                        │                    │                          │
                        │                    └─→ [RHEL Path] ───────────┘
                        │                        (/rhel-deploy)
                        │
                   User chooses target:
                   - OpenShift → Strategy selection (S2I/Podman/Helm)
                   - RHEL → Delegate to /rhel-deploy skill
```

**Deployment Targets:**
- **OpenShift** - Deploy to OpenShift/Kubernetes cluster (S2I, Podman, or Helm strategies)
- **RHEL Host** - Deploy to standalone RHEL system via SSH (delegates to /rhel-deploy)

**OpenShift Deployment Strategies (if OpenShift target selected):**
- **S2I** - Source-to-Image build on OpenShift, then deploy (Phases 3-7)
- **Podman** - Build from Containerfile/Dockerfile on OpenShift, then deploy (Phases 3-7)
- **Helm** - Deploy using Helm chart (Phase 2-H)

## Workflow

### Phase 0: Introduction

```markdown
# Containerize & Deploy

I'll help you containerize and deploy your application to OpenShift or a standalone RHEL system.

**What this workflow does:**
1. **Detect** - Analyze your project and determine the best deployment strategy
2. **Choose Target** - Deploy to OpenShift cluster or RHEL host
3. **Build** - Build container image (S2I or Podman) or skip if using Helm with existing image
4. **Deploy** - Deploy using Kubernetes resources, Helm chart, or systemd services

**Deployment Targets:**
- **OpenShift** - Deploy to OpenShift/Kubernetes cluster
- **RHEL Host** - Deploy directly to a RHEL system via SSH

**OpenShift Strategies:**
- **S2I (Source-to-Image)** - Build and deploy from source code
- **Podman** - Build from existing Containerfile/Dockerfile
- **Helm** - Deploy using Helm chart

**RHEL Strategies:**
- **Container** - Run with Podman + systemd
- **Native** - Install with dnf + systemd

**What I need from you:**
- Confirmation at each step before I make changes
- Access to an OpenShift cluster OR SSH access to a RHEL host
- Your project source code

**Ready to begin?** (yes/no)
```

Wait for user confirmation before proceeding.

### Phase 1: Project Detection

Execute the `/detect-project` workflow.

**If Remote URL provided:**
Follow the "Remote Repository Strategy" path in `/detect-project`.
- Ask user to choose: Remote S2I, Remote Podman, or Clone.

**If Local Files:**
Proceed with standard detection.

```markdown
## Phase 1: Analyzing Your Project

[If Local]
Scanning project directory for language indicators...

[If Remote]
Analyzing remote repository options...

...
```

Store confirmed values in session state, including `BUILD_STRATEGY` and `HELM_CHART_DETECTED`.

### Phase 1.4: Deployment Target Selection

```markdown
## Deployment Target

Where would you like to deploy this application?

| Target | Description | Requirements |
|--------|-------------|--------------|
| **OpenShift** | Deploy to OpenShift/Kubernetes cluster | `oc login` access |
| **RHEL Host** | Deploy directly to a standalone RHEL system | SSH access to RHEL 8+ |

**Which target would you like to use?**
1. OpenShift - Deploy to current cluster
2. RHEL - Deploy to a RHEL host via SSH
```

Store `DEPLOYMENT_TARGET` in session state.

**If user selects "RHEL":**
- Store `DEPLOYMENT_TARGET = "rhel"` in session state
- Delegate to `/rhel-deploy` skill with detected project info
- Pass: `APP_NAME`, `LANGUAGE`, `FRAMEWORK`, `VERSION`, `BUILDER_IMAGE`, `CONTAINER_PORT`
- The `/rhel-deploy` skill handles SSH connection, deployment strategy, and service creation
- After `/rhel-deploy` completes → Go to **Phase 8 (Completion)**

**If user selects "OpenShift":**
- Store `DEPLOYMENT_TARGET = "openshift"` in session state
- Continue to Phase 1.5 (Strategy Selection)

### Phase 1.5: Strategy Selection

If multiple deployment options are available (Helm chart detected, Dockerfile present, or standard project):

```markdown
## Deployment Strategy

Based on my analysis, you have these options:

| Strategy | Use When | Detected |
|----------|----------|----------|
| **S2I** | Standard apps, no Dockerfile needed | [Yes/No] |
| **Podman** | Custom Containerfile/Dockerfile exists | [Yes/No] |
| **Helm** | Helm chart exists or complex deployments | [Yes/No] |

**Detected in your project:**
[List what was found: language indicators, Dockerfile, Helm chart at ./chart]

**Which deployment strategy would you like to use?**
1. S2I - Build with Source-to-Image
2. Podman - Build from Containerfile/Dockerfile
3. Helm - Use existing Helm chart
4. Create Helm chart - Generate a new Helm chart for your project (if no chart exists)
```

Store `DEPLOYMENT_STRATEGY` in session state.

### Phase 1.6: Image Selection (S2I/Podman only)

If user selected S2I or Podman deployment strategy, offer image selection options:

```markdown
## Image Selection

**Current recommendation:** `[builder-image]`
(Based on: [language] [version])

**Image Selection Options:**
- **quick** - Use the recommended image (good for most cases)
- **smart** - Run `/recommend-image` for tailored selection (production vs dev, security, performance)

Which option would you prefer?
```

**If user selects "smart":**
- Invoke `/recommend-image` skill with detected `LANGUAGE`, `FRAMEWORK`, `VERSION`
- Store the result in `BUILDER_IMAGE` and `IMAGE_VARIANT` session state
- Continue to Phase 2

**If user selects "quick":**
- Use the already-detected `BUILDER_IMAGE`
- Continue to Phase 2

**BRANCHING LOGIC:**
- If `DEPLOYMENT_STRATEGY` is **"S2I"** or **"Podman"** → After Phase 2, continue to **Phase 3 (S2I/Podman Path)**
- If `DEPLOYMENT_STRATEGY` is **"Helm"** → After Phase 2, go to **Phase 2-H (Helm Path)**

### Phase 2: OpenShift Connection

```markdown
## Phase 2: Connecting to OpenShift

Checking cluster connection...

**Current Context:**
| Setting | Value |
|---|---|
| Cluster | [cluster-api-url] |
| User | [username] |
| Namespace | [current-namespace] |

**Is this the correct cluster and namespace?**
- yes - Continue to build
- no - I need to change this

[If no]
**To change context:**
1. Run `oc login <new-cluster-url>` in your terminal
2. Or run `oc project <namespace>` to switch namespace
3. Then tell me to continue

**Available namespaces you have access to:**
[List first 10 namespaces/projects]

Which namespace should I deploy to?
```

Store confirmed `NAMESPACE` in session state.

---

## S2I/PODMAN PATH (If DEPLOYMENT_STRATEGY is "S2I" or "Podman")

### Phase 3: Git Repository Check

```markdown
## Git Repository

I need a Git URL for the S2I build.

**Detected from .git/config:**
- Remote: `[git-url]`
- Branch: `[current-branch]`

**Is this correct?** (yes/no)

[If no git config found]
**Please provide:**
1. Git repository URL (e.g., https://github.com/user/repo.git)
2. Branch name (default: main)
```

Store `GIT_URL` and `GIT_BRANCH` in session state.

### Phase 4: Pre-Build Summary

```markdown
## Phase 3: Build Configuration

Here's what I'll create on OpenShift:

**Target:**
- Cluster: [cluster]
- Namespace: [namespace]

**Resources to Create:**

1. **ImageStream** `[app-name]`
   - Stores built container images

2. **BuildConfig** `[app-name]`
   - Source: [git-url] (branch: [branch])
   - Builder: [builder-image]
   - Output: [app-name]:latest

---

**Would you like to see the full YAML?** (yes/no)

[If yes, show both YAML manifests]

---

**Proceed with creating these resources and starting the build?**
- yes - Create resources and start build
- modify - I need to change something
- cancel - Stop here
```

### Phase 5: Execute Build

```markdown
## Creating Build Resources...

[x] ImageStream created: [app-name]
[x] BuildConfig created: [app-name]

## Starting Build...

**Build:** [app-name]-1
**Status:** Running

---
**Build Logs:**
```
[Stream S2I build output]
```
---

[When complete]

## Build Successful!

**Build:** [app-name]-1
**Duration:** [X]m [Y]s
**Image:** [image-reference]

**CRITICAL: Wait for the build to reach 'Complete' status before proceeding.**

Continue to deployment? (yes/no)
```

### Phase 6: Pre-Deploy Summary

```markdown
## Phase 4: Deployment Configuration

**Image ready!** Now let's deploy it.

**Resources to Create:**

1. **Deployment** `[app-name]`
   - Image: [app-name]:latest
   - Replicas: 1
   - Port: [detected-port]

2. **Service** `[app-name]`
   - Internal load balancer
   - Port: [port]

3. **Route** `[app-name]`
   - External HTTPS access
   - URL: https://[app-name]-[namespace].[domain]

---

**Would you like to see the full YAML?** (yes/no)

[If yes, show all three YAML manifests]

---

**Proceed with deployment?**
- yes - Deploy the application
- modify - I need to change something
- cancel - Stop here (build artifacts preserved)
```

### Phase 7: Execute Deployment

```markdown
## Deploying Application...

[x] Deployment created: [app-name]
[x] Service created: [app-name]
[x] Route created: [app-name]

## Waiting for Rollout...

**Pod Status:**
| Pod | Status | Ready |
|-----|-----|---|
| [app-name]-xxx-yyy | Running | 1/1 |

Rollout complete!
```

---

## HELM PATH (If DEPLOYMENT_STRATEGY is "Helm")

### Phase 2-H: Helm Deployment

If user selected Helm in Phase 1.5, execute this path instead of Phases 3-7.

```markdown
## Helm Deployment

Switching to Helm deployment workflow...

The `/helm-deploy` skill will handle:
1. Validate the Helm chart
2. Review and customize values
3. Install/upgrade the release
4. Monitor deployment
5. Present results

Proceeding with Helm deployment...
```

**Delegate to `/helm-deploy` skill:**
- Pass `APP_NAME`, `NAMESPACE`, `HELM_CHART_PATH` from session state
- The helm-deploy skill handles chart detection, values review, and installation
- After helm-deploy completes → Go to **Phase 8 (Completion)**

**If user chose "Create Helm chart":**
- Generate chart using templates from templates/helm/
- Replace `${APP_NAME}` placeholders with detected app name
- Set `${CONTAINER_PORT}` based on detected port
- Then proceed with helm-deploy workflow

---

## COMPLETION (Both paths converge here)

### Phase 8: Completion

```markdown
## Deployment Complete!

Your application is now running on OpenShift.

---

**Application Summary:**

| Setting | Value |
|---|---|
| Name | [app-name] |
| Namespace | [namespace] |
| Language | [language] |
| Framework | [framework] |

---

**Access URLs:**

| Type | URL |
|---|-----|
| **External** | https://[route-host] |
| Internal | http://[app-name].[namespace].svc.cluster.local:[port] |

---

**Resources Created:**

| Resource | Name | Status |
|----|---|-----|
| ImageStream | [app-name] | Ready |
| BuildConfig | [app-name] | Ready |
| Deployment | [app-name] | 1/1 Running |
| Service | [app-name] | Active |
| Route | [app-name] | Admitted |

---

**Quick Commands:**

```bash
# View logs
oc logs -f deployment/[app-name] -n [namespace]

# Scale up
oc scale deployment/[app-name] --replicas=3 -n [namespace]

# Trigger rebuild (after code changes)
oc start-build [app-name] -n [namespace]

# Delete everything
oc delete all -l app=[app-name] -n [namespace]
```

---

**Next Steps:**
- Open your app: [route-url]
- Set up Git webhooks for automatic builds
- Add environment variables: `oc set env deployment/[app-name] KEY=value`
- Configure autoscaling: `oc autoscale deployment/[app-name] --min=1 --max=5`

---

Congratulations! Your application is live.
```

## MCP Tools Used

All tools from child skills:

| Phase | Tools |
|---|---|
| Detect | `run_terminal_cmd` (optional clone) |
| Connect | `resources_list` (namespaces) |
| Build | `resources_create_or_update`, `pod_logs`, `events_list` |
| Deploy | `resources_create_or_update`, `pod_list`, `pod_logs` |
| Helm | `helm_install`, `helm_upgrade`, `helm_status`, `helm_list`, `pods_list` |
| Rollback | `resources_delete`, `helm_uninstall`, `helm_rollback` |

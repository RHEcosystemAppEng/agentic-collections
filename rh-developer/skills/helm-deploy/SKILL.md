---
name: helm-deploy
description: |
  Deploy applications to OpenShift using Helm charts. Use this skill when user wants to deploy with Helm, when a Helm chart is detected in the project, or when /helm-deploy command is invoked. Supports both existing charts and chart creation. Handles chart detection, values customization, install/upgrade operations, and rollback. Requires kubernetes MCP Helm tools.
---

# /helm-deploy Skill

Deploy applications to OpenShift using Helm charts. Supports existing charts or creates new ones.

## Prerequisites

1. User logged into OpenShift cluster
2. Helm chart exists OR user wants to create one
3. Container image available (from registry or will be built)

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill requires explicit user confirmation at each step. You MUST:
1. **Wait for user confirmation** before executing any actions
2. **Do NOT proceed** to the next step until the user explicitly approves
3. **Present options clearly** and wait for response
4. **Never auto-execute** chart creation, Helm installations, or upgrades

If the user says "no" or wants modifications, address their concerns before proceeding.

## Workflow

### Step 1: Check OpenShift Connection

Use kubernetes MCP to verify cluster connection:

```markdown
## Checking OpenShift Connection...

**Cluster:** [cluster-url]
**User:** [username]
**Namespace:** [namespace]

Is this the correct cluster and namespace? (yes/no)
```

**WAIT for user confirmation before proceeding.** Do NOT continue until user explicitly confirms.

If user says "no", wait for them to switch context and tell you to continue.

### Step 2: Detect Helm Chart

Search for Helm charts in this order:

| Priority | Path | Description |
|----------|------|-------------|
| 1 | `./Chart.yaml` | Root directory |
| 2 | `./chart/Chart.yaml` | Chart subdirectory |
| 3 | `./charts/*/Chart.yaml` | Charts directory |
| 4 | `./helm/Chart.yaml` | Helm subdirectory |
| 5 | `./deploy/helm/Chart.yaml` | Deploy directory |

**If chart found:**

```markdown
## Helm Chart Detected

**Location:** [chart-path]

| Field | Value |
|-------|-------|
| Name | [chart-name] |
| Version | [chart-version] |
| App Version | [app-version] |
| Description | [description] |

**Templates found:**
- [list of template files]

**Values file:** [values.yaml path]

Would you like to:
1. Deploy using this chart (recommended)
2. Customize values before deploying
3. Use a different chart location
```

**WAIT for user to select an option.** Do NOT proceed until user makes a choice.

**If no chart found:**

```markdown
## No Helm Chart Found

I searched these locations but found no Helm chart:
- ./Chart.yaml
- ./chart/Chart.yaml
- ./charts/*/Chart.yaml
- ./helm/Chart.yaml
- ./deploy/helm/Chart.yaml

**Options:**
1. **Create a new Helm chart** - I'll generate one based on your project
2. **Specify chart path** - Point me to your chart location
3. **Use a different deployment method** - Try /deploy or /containerize-deploy

Which would you prefer?
```

**WAIT for user to select an option.** Do NOT proceed until user makes a choice.

### Step 3: Create Helm Chart (if needed)

If user chooses to create a chart:

```markdown
## Creating Helm Chart

I'll create a Helm chart based on your project.

**Detected Project Info:**
| Setting | Value |
|---------|-------|
| App Name | [app-name] |
| Language | [language] |
| Framework | [framework] |
| Port | [port] |

**Chart will include:**
- Chart.yaml with project metadata
- values.yaml with configurable options
- Deployment template
- Service template
- Route template (OpenShift)
- Helper templates

**Target directory:** ./chart/

Proceed with creating the Helm chart? (yes/no)
```

**WAIT for user confirmation.** Do NOT create the chart until user explicitly says "yes".

- If user says "yes" → Create chart files
- If user says "no" → Ask what they would like to change or use a different approach

Use templates from templates/helm/ to generate:
1. Chart.yaml
2. values.yaml
3. templates/deployment.yaml
4. templates/service.yaml
5. templates/route.yaml
6. templates/_helpers.tpl
7. templates/NOTES.txt

Replace `${APP_NAME}` placeholders with actual app name in all template files.

### Step 4: Check for Existing Release

Before installing, check if a release with the same name exists:

```markdown
## Checking for Existing Release...

[Use helm_list to check]
```

**If release exists:**

```markdown
## Existing Release Found

A release named '[name]' already exists.

| Field | Value |
|-------|-------|
| Status | [status] |
| Revision | [revision] |
| Chart | [chart-name] v[version] |
| Updated | [timestamp] |

**Options:**
1. Upgrade the release with new configuration
2. Rollback to a previous revision
3. Uninstall and reinstall
4. Cancel

Which would you like to do?
```

**WAIT for user to select an option.** Do NOT proceed until user makes a choice.

### Step 5: Review Values

```markdown
## Chart Values Configuration

**Current values.yaml:**

```yaml
replicaCount: [value]
image:
  repository: [value]
  tag: [value]
service:
  port: [value]
route:
  enabled: [value]
resources:
  limits:
    memory: [value]
```

**Common customizations:**

| Value | Current | Description |
|-------|---------|-------------|
| `replicaCount` | 1 | Number of pods |
| `image.repository` | [repo] | Container image |
| `image.tag` | [tag] | Image version |
| `service.port` | [port] | Service port |
| `resources.limits.memory` | 512Mi | Memory limit |

**Options:**
1. Deploy with current values
2. Modify values interactively
3. Use a custom values file

Which would you prefer?
```

**WAIT for user to select an option.** Do NOT proceed until user makes a choice.

### Step 6: Pre-Deploy Summary

```markdown
## Helm Deployment Summary

**Release Configuration:**

| Setting | Value |
|---------|-------|
| Release Name | [release-name] |
| Namespace | [namespace] |
| Chart | [chart-path] |
| Chart Version | [version] |

**Resources to be created:**

| Resource | Name |
|----------|------|
| Deployment | [name] |
| Service | [name] |
| Route | [name] (if enabled) |

**Values to apply:**
```yaml
[show customized values or "Using defaults"]
```

**Helm command equivalent:**
```bash
helm install [release-name] [chart-path] -n [namespace] [--set options]
```

**Proceed with Helm deployment?** (yes/no)
```

**WAIT for user confirmation.** Do NOT execute the Helm install/upgrade until user explicitly says "yes".

- If user says "yes" → Proceed with deployment
- If user says "no" → Ask what they would like to change

### Step 7: Execute Deployment

Use kubernetes MCP `helm_install` or `helm_upgrade`:

```markdown
## Deploying with Helm...

**Release:** [release-name]
**Chart:** [chart-name] v[version]

[x] Chart validated
[x] Templates rendered
[ ] Installing release...

---

**Installation Progress:**

Waiting for resources to be ready...

| Resource | Status |
|----------|--------|
| Deployment/[name] | [status] |
| Service/[name] | [status] |
| Route/[name] | [status] |

---
```

Monitor pod status using `pods_list_in_namespace` until pods are ready or timeout.

### Step 8: Deployment Complete

```markdown
## Helm Deployment Complete!

**Release:** [release-name]
**Status:** deployed
**Revision:** 1
**Namespace:** [namespace]

---

**Resources Created:**

| Resource | Name | Status |
|----------|------|--------|
| Deployment | [name] | [replicas] Ready |
| Service | [name] | Active |
| Route | [name] | Admitted |

**Access URL:** https://[route-host]

---

**Quick Commands:**

```bash
# Check release status
helm status [release-name] -n [namespace]

# View release history
helm history [release-name] -n [namespace]

# Upgrade with new values
helm upgrade [release-name] [chart-path] -n [namespace] -f new-values.yaml

# Rollback to previous version
helm rollback [release-name] 1 -n [namespace]

# Uninstall release
helm uninstall [release-name] -n [namespace]

# View logs
oc logs -l app.kubernetes.io/instance=[release-name] -n [namespace] -f
```

---

Your application is live!
```

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `helm_list` | Check existing releases |
| `helm_install` | Install new release |
| `helm_upgrade` | Upgrade existing release |
| `helm_status` | Get release status |
| `helm_history` | Get release history |
| `helm_rollback` | Rollback to revision |
| `helm_uninstall` | Remove release |
| `pods_list_in_namespace` | Monitor pod status |
| `pods_log` | View pod logs |
| `events_list` | Check for errors |

## Output Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `RELEASE_NAME` | Helm release name | `my-app` |
| `CHART_PATH` | Path to chart | `./chart` |
| `CHART_VERSION` | Chart version | `0.1.0` |
| `RELEASE_REVISION` | Current revision | `1` |
| `ROUTE_HOST` | External URL | `my-app-ns.apps.cluster.com` |

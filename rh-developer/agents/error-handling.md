---
name: error-handling
description: |
  Reference guide for common error patterns and recovery strategies in OpenShift S2I deployments. Covers authentication errors (401/403), resource conflicts (409), build failures (git clone, S2I assemble, image push), deployment errors (ImagePullBackOff, CrashLoopBackOff, Pending pods), and route issues. Provides templated responses for each error type with troubleshooting steps and user options. Used by /s2i-build, /deploy, and /containerize-deploy skills.
---

# Error Handling Patterns

## Philosophy

1. **Detect Early** - Check prerequisites before attempting actions
2. **Explain Clearly** - Tell user exactly what went wrong
3. **Offer Options** - Provide multiple paths forward
4. **Never Leave Hanging** - Always end with actionable next step

## Authentication Errors

### Not logged into cluster

**Detection:** kubernetes MCP tools fail with 401/403 or connection refused

**Response:**
```
I cannot connect to the OpenShift cluster.

Please ensure you are logged in:
1. Run: oc login <cluster-url>
2. Or set KUBECONFIG environment variable to your kubeconfig file

After logging in, try again.
```

### Insufficient permissions

**Detection:** 403 Forbidden on resource creation

**Response:**
```
You don't have permission to create [resource-type] in namespace [namespace].

Current user: [username]
Required role: edit or admin

Options:
1. Contact your cluster admin to grant permissions
2. Try a different namespace where you have edit access
3. List available namespaces: oc projects
```

## Resource Conflicts

### Resource already exists

**Detection:** 409 Conflict on create

**Response:**
```
A [resource-type] named '[name]' already exists in namespace '[namespace]'.

Current [resource-type] details:
[show key details]

Options:
1. Update existing resource with new configuration
2. Delete existing and recreate
3. Use a different name

What would you like to do?
```

## Build Errors

### Git clone failed

**Detection:** Build fails in git-clone phase

**Causes:**
- Invalid URL
- Private repo without credentials
- Network issues

**Response:**
```
Failed to clone Git repository: [url]

Error: [git error message]

Troubleshooting:
1. Verify URL is correct and accessible from the cluster
2. For private repos, create a Git secret:
   oc create secret generic git-creds \
     --from-literal=username=<user> \
     --from-literal=password=<token> \
     --type=kubernetes.io/basic-auth
   oc set build-secret --source bc/[name] git-creds
3. Check if the branch '[branch]' exists

Would you like me to help set up Git credentials?
```

### S2I assemble failed

**Detection:** Build fails during assemble phase

**Response:**
```
S2I build failed during the assemble phase.

Error summary:
[last 10 error lines from log]

Common causes:
- Missing dependencies in [package.json/requirements.txt/pom.xml]
- Incompatible language version (e.g., using Node 20 features with Node 18 image)
- Build script errors

Would you like me to:
1. Show full build logs
2. Suggest a different S2I builder image
3. Help troubleshoot the specific error
```

### Image push failed

**Detection:** Build fails during push phase

**Response:**
```
Failed to push image to internal registry.

Error: [push error]

Common causes:
- Image registry storage is full
- Registry is not accessible
- ImageStream not found

This is typically a cluster configuration issue. Contact your cluster admin.
```

## Deployment Errors

### ImagePullBackOff

**Detection:** Pod in ImagePullBackOff state

**Response:**
```
Pods cannot pull the container image.

Image: [image-reference]
Error: [pull error]

For ImageStream images:
1. Verify build completed: oc get builds
2. Check ImageStream: oc get is [name] -o yaml
3. Ensure image tag exists: oc get istag [name]:latest

For external images:
1. Verify image exists in registry
2. Create image pull secret if needed:
   oc create secret docker-registry my-pull-secret \
     --docker-server=<registry> \
     --docker-username=<user> \
     --docker-password=<pass>
   oc secrets link default my-pull-secret --for=pull
```

### CrashLoopBackOff

**Detection:** Pod in CrashLoopBackOff state

**Response:**
```
Application is crashing on startup.

Pod: [pod-name]
Restart count: [count]

Recent logs:
[last 20 lines of logs]

Common causes:
- Missing environment variables
- Database/service connection failures
- Port binding issues (app not listening on expected port)
- Application startup errors

Would you like me to:
1. Show full pod logs
2. Check pod events for more details
3. Describe the pod configuration
4. Help set up environment variables
```

### Pods stuck Pending

**Detection:** Pod stuck in Pending state for >30 seconds

**Response:**
```
Pods are stuck in Pending state.

Events:
[relevant events]

Common causes:
- Insufficient cluster resources (CPU/memory)
- No nodes match pod requirements
- PersistentVolumeClaim not bound

Try:
1. Reduce resource requests in deployment
2. Check cluster capacity: oc describe nodes
3. Contact cluster admin if resources are exhausted
```

## Route Errors

### Route not admitted

**Detection:** Route status shows not admitted

**Response:**
```
Route was created but not admitted by the router.

Route: [route-name]
Status: [route status]

Common causes:
- Hostname conflicts with existing route
- TLS certificate issues
- Router capacity exceeded

Check details: oc describe route [name]

Would you like me to:
1. Try a different hostname
2. Remove TLS configuration
3. Show conflicting routes
```

## Helm Deployment Errors

### Chart not found

**Detection:** `helm install` fails with chart not found error

**Response:**
```
Helm chart not found at specified path.

Path checked: [chart-path]

Verify:
1. Chart.yaml exists in the directory
2. Path is correct (check for typos)
3. If using a repository, run: helm repo update

Would you like me to:
1. Search for Chart.yaml in common locations
2. Create a new Helm chart for this project
3. Specify a different chart path
```

### Release already exists

**Detection:** `helm install` fails with "cannot re-use a name that is still in use"

**Response:**
```
A Helm release named '[release-name]' already exists in namespace '[namespace]'.

Current release:
- Status: [status]
- Chart: [chart-name]-[version]
- Updated: [timestamp]

Options:
1. Upgrade the existing release with new values
2. Uninstall the existing release and reinstall
3. Use a different release name

What would you like to do?
```

### Helm values validation failed

**Detection:** Template rendering fails due to invalid values

**Response:**
```
Helm chart validation failed.

Error: [error message]

Common causes:
- Missing required values
- Invalid value types (string vs number)
- Template syntax errors

Would you like me to:
1. Show the default values.yaml for reference
2. Validate your custom values file
3. Render templates locally to debug
```

### Helm release failed

**Detection:** Release status shows "failed"

**Response:**
```
Helm release '[name]' failed to deploy.

Release Status: failed
Revision: [revision]

**Events:**
[relevant events from pods]

**Pod Status:**
[pod status table]

Options:
1. View detailed release status
2. Check pod logs for errors
3. Rollback to previous revision
4. Uninstall and retry

What would you like to do?
```

### Chart dependency error

**Detection:** Dependencies not satisfied

**Response:**
```
Chart has unresolved dependencies.

Missing dependencies:
[list of missing deps]

Run these commands to resolve:
1. cd [chart-directory]
2. helm dependency update

Would you like me to update dependencies?
```

## Recovery Actions

### Retry pattern

For transient errors:
```
This might be a temporary issue.

Would you like me to retry? (yes/no)
```

### Partial rollback

When later steps fail:
```
The deployment failed, but earlier steps succeeded.

Completed:
- [x] ImageStream created
- [x] BuildConfig created
- [x] Build completed successfully

Failed:
- [ ] Deployment creation

The image is available at: [image]

Options:
1. Retry deployment only
2. Investigate the issue
3. Rollback all changes
```

### Full rollback

```
Rolling back all changes...

Deleting resources:
- [ ] Route: [name]
- [ ] Service: [name]
- [ ] Deployment: [name]
- [ ] BuildConfig: [name]
- [ ] ImageStream: [name]

[After deletion]
All resources cleaned up. Your namespace is back to its original state.
```

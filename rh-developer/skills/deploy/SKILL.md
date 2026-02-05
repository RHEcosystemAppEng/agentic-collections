---
name: deploy
description: |
  Create Kubernetes Deployment, Service, and Route resources on OpenShift to deploy and expose an application. Use this skill after /s2i-build to make the built image accessible. Handles port detection, replica configuration, HTTPS route creation, rollout monitoring, and rollback on failure. Triggers on /deploy command when user wants to deploy a container image to OpenShift.
---

# /deploy Skill

Create Kubernetes/OpenShift resources (Deployment, Service, Route) to deploy and expose an application from a container image.

## Prerequisites

Before running this skill:
1. User is logged into OpenShift cluster
2. Container image exists (from ImageStream or external registry)
3. Target namespace exists

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill requires explicit user confirmation at each step. You MUST:
1. **Wait for user confirmation** before executing any actions
2. **Do NOT proceed** to the next step until the user explicitly approves
3. **Present options clearly** (yes/no/modify) and wait for response
4. **Never auto-execute** resource creation or deployments

If the user says "no" or wants modifications, address their concerns before proceeding.

## Workflow

### Step 1: Gather Deployment Information

```markdown
## Deployment Configuration

**Current OpenShift Context:**
- Cluster: [cluster]
- Namespace: [namespace]

**Please confirm deployment settings:**

| Setting | Value | Source |
|---------|-------|--------|
| App Name | `[name]` | [from s2i-build / input] |
| Image | `[image-ref]` | [from ImageStream / input] |
| Container Port | `[port]` | [detected / needs input] |
| Replicas | `1` | [default] |
| Expose Route | `yes` | [default] |

Confirm these settings or tell me what to change.
```

**WAIT for user confirmation before proceeding.** Do NOT continue until user explicitly confirms these settings or provides corrections.

### Step 2: Detect Container Port

Try to detect port from project files:

1. **Dockerfile:** Look for `EXPOSE <port>` (Most accurate for container builds)
2. **Web Server Config:** Look for `listen <port>` in `nginx.conf`, `httpd.conf`, etc.
3. **Framework Defaults:**
   - **Node.js:** Look for `PORT` env var usage, common: 3000 (dev), 8080 (prod/S2I)
   - **Python:** Flask default 5000, FastAPI/Uvicorn 8000
   - **Java:** Spring Boot 8080, Quarkus 8080
   - **Go:** Common 8080
   - **Ruby Rails:** 3000

```markdown
## Port Detection

I detected port **[port]** based on:
- [reason - e.g., "PORT environment variable in package.json scripts"]

Is this correct?
- yes - Use port [port]
- no - Specify the correct port
```

**WAIT for user confirmation.** Do NOT proceed until user confirms the port or provides the correct value.

If unable to detect:
```markdown
## Port Required

I couldn't automatically detect the container port.

Common ports by framework:
- Node.js/Express: 3000 or 8080
- Python Flask: 5000
- Python FastAPI: 8000
- Java Spring Boot: 8080
- Go: 8080

**What port does your application listen on?**
```

### Step 3: Create Deployment

Show the Deployment manifest:

```markdown
## Step 1 of 3: Create Deployment

A Deployment manages your application pods.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: [app-name]
  namespace: [namespace]
  labels:
    app: [app-name]
    app.kubernetes.io/name: [app-name]
  annotations:
    image.openshift.io/triggers: |
      [{"from":{"kind":"ImageStreamTag","name":"[app-name]:latest"},"fieldPath":"spec.template.spec.containers[0].image"}]
spec:
  replicas: [replicas]
  selector:
    matchLabels:
      app: [app-name]
  template:
    metadata:
      labels:
        app: [app-name]
    spec:
      containers:
        - name: [app-name]
          image: image-registry.openshift-image-registry.svc:5000/[namespace]/[app-name]:latest
          ports:
            - containerPort: [port]
              protocol: TCP
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /
              port: [port]
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /
              port: [port]
            initialDelaySeconds: 5
            periodSeconds: 5
```

**This Deployment will:**
- Run [replicas] replica(s) of your application
- Use image from ImageStream: `[app-name]:latest`
- Expose container port: [port]
- Auto-update when new images are pushed

**Proceed with creating this Deployment?** (yes/no)
```

**WAIT for user confirmation.** Do NOT create the Deployment until user explicitly says "yes".

- If user says "yes" → Use kubernetes MCP `resources_create_or_update` to apply
- If user says "no" → Ask what they would like to change
- If user wants modifications → Update the YAML and show again for confirmation

### Step 4: Create Service

```markdown
## Step 2 of 3: Create Service

A Service provides internal load balancing to your pods.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: [app-name]
  namespace: [namespace]
  labels:
    app: [app-name]
spec:
  selector:
    app: [app-name]
  ports:
    - name: http
      port: [port]
      targetPort: [port]
      protocol: TCP
  type: ClusterIP
```

**This Service will:**
- Create internal DNS: `[app-name].[namespace].svc.cluster.local`
- Load balance traffic to pods on port [port]

**Proceed with creating this Service?** (yes/no)
```

**WAIT for user confirmation.** Do NOT create the Service until user explicitly says "yes".

- If user says "yes" → Use kubernetes MCP `resources_create_or_update` to apply
- If user says "no" → Ask what they would like to change
- If user wants modifications → Update the YAML and show again for confirmation

### Step 5: Create Route (Optional)

If user wants external exposure:

```markdown
## Step 3 of 3: Create Route

A Route exposes your application externally with HTTPS.

```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: [app-name]
  namespace: [namespace]
  labels:
    app: [app-name]
spec:
  to:
    kind: Service
    name: [app-name]
    weight: 100
  port:
    targetPort: http
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
  wildcardPolicy: None
```

**This Route will:**
- Expose app at: `https://[app-name]-[namespace].[cluster-domain]`
- Enable TLS with edge termination
- Redirect HTTP to HTTPS

**Proceed with creating this Route?** (yes/no/skip)
```

**WAIT for user confirmation.** Do NOT create the Route until user explicitly responds.

- If user says "yes" → Use kubernetes MCP `resources_create_or_update` to apply
- If user says "skip" → Skip Route creation and proceed to rollout monitoring
- If user says "no" → Ask what they would like to change
- If user wants modifications → Update the YAML and show again for confirmation

### Step 6: Wait for Rollout

Monitor deployment status:

```markdown
## Deployment Rollout

Waiting for pods to be ready...

**Deployment:** [app-name]
**Desired:** [replicas]
**Ready:** [current]/[replicas]

**Pod Status:**
| Pod | Status | Ready | Restarts |
|-----|--------|-------|----------|
| [app-name]-xxx-yyy | Running | 1/1 | 0 |

[Poll until ready or timeout after 5 minutes]
```

### Step 7: Deployment Complete

```markdown
## Deployment Complete!

**Application:** [app-name]
**Namespace:** [namespace]

**Access URLs:**
| Type | URL |
|------|-----|
| External | https://[route-host] |
| Internal | http://[app-name].[namespace].svc.cluster.local:[port] |

**Resources Created:**
| Resource | Name | Status |
|----------|------|--------|
| Deployment | [app-name] | [replicas]/[replicas] Ready |
| Service | [app-name] | Active |
| Route | [app-name] | Admitted |

**Quick Commands:**
```bash
# View logs
oc logs -f deployment/[app-name] -n [namespace]

# Scale replicas
oc scale deployment/[app-name] --replicas=3 -n [namespace]

# Restart pods
oc rollout restart deployment/[app-name] -n [namespace]

# Delete all
oc delete all -l app=[app-name] -n [namespace]
```

Your application is now live!
```

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `resources_list` | Check existing deployments/services/routes |
| `resources_get` | Get resource details, route host |
| `resources_create_or_update` | Create Deployment, Service, Route |
| `pod_list` | Check pod status during rollout |
| `pod_logs` | Debug pod issues |
| `events_list` | Check events for errors |

## Required Inputs

| Input | Auto-detected | Must Confirm |
|-------|---------------|--------------|
| App name | Yes (from build) | Yes |
| Image | Yes (from ImageStream) | Yes |
| Port | Yes (from project files) | Yes |
| Replicas | Yes (default: 1) | Optional |
| Create Route | Yes (default: yes) | Yes |
| Namespace | Yes (from kubeconfig) | Yes |

# Session State Patterns

This reference defines the state management patterns used across deployment skills.

## Common State Properties

All deployment workflows share these core state properties:

```
COMMON_STATE = {
  phase: string,           // Current workflow phase

  // Project detection
  app_name: string,
  language: string,
  framework: string,
  version: string,
  container_port: number,

  // Build configuration
  builder_image: string,
  build_strategy: "Source" | "Podman",

  // Tracking
  created_resources: [
    { type: string, name: string, path?: string, status?: string }
  ]
}
```

## OpenShift Deployment State

For `/containerize-deploy` and `/s2i-build` workflows:

```
OPENSHIFT_STATE = {
  ...COMMON_STATE,

  phase: "intro" | "detect" | "target" | "strategy" | "image-select" |
         "connect" | "helm" | "git" | "pre-build" | "build" |
         "pre-deploy" | "deploy" | "complete",

  // Target
  deployment_target: "openshift" | "rhel",
  deployment_strategy: "S2I" | "Podman" | "Helm",

  // Cluster connection
  cluster: string,
  namespace: string,
  user: string,

  // Git source
  git_url: string,
  git_branch: string,

  // Image selection
  image_variant: "full" | "minimal" | "runtime",
  selection_rationale: string,

  // Helm (if applicable)
  helm_chart_detected: boolean,
  helm_chart_path: string,
  helm_chart_name: string,
  helm_chart_version: string,
  helm_release_name: string,
  helm_release_revision: number,

  // Deployment config
  replicas: number,
  create_route: boolean,

  // Results
  build_name: string,
  route_host: string
}
```

## RHEL Deployment State

For `/rhel-deploy` workflows:

```
RHEL_STATE = {
  ...COMMON_STATE,

  phase: "intro" | "ssh" | "analyze" | "strategy" |
         "container-*" | "native-*" | "complete",

  // SSH connection
  rhel_host: string,
  rhel_user: string,
  rhel_port: number,         // default: 22

  // Target analysis
  rhel_version: string,      // e.g., "RHEL 9.3"
  rhel_arch: string,         // e.g., "x86_64"
  podman_available: boolean,
  podman_version: string,
  selinux_status: "enforcing" | "permissive" | "disabled",
  firewall_status: "active" | "inactive",

  // Deployment strategy
  deployment_strategy: "container" | "native",

  // Container-specific
  container_mode: "rootless" | "rootful",
  container_name: string,
  container_image: string,

  // Native-specific
  app_install_path: string,  // e.g., "/opt/[app-name]"
  service_user: string,

  // Common service
  systemd_unit_name: string,
  exposed_port: number
}
```

## State Transitions

### OpenShift Path
```
intro → detect → target → strategy → image-select → connect →
  ├── (S2I/Podman) → git → pre-build → build → pre-deploy → deploy → complete
  └── (Helm) → helm → complete
```

### RHEL Path
```
intro → ssh → analyze → strategy →
  ├── (Container) → container-image → container-config → container-systemd → firewall → complete
  └── (Native) → native-deps → native-deploy → native-systemd → firewall → complete
```

## Resource Tracking

Track created resources for rollback support:

```javascript
created_resources: [
  { type: "file", path: "/etc/systemd/system/app.service" },
  { type: "service", name: "app.service" },
  { type: "firewall_rule", port: 8080 },
  { type: "selinux_context", path: "/opt/app" },
  { kind: "Deployment", name: "app", namespace: "default" },
  { kind: "Service", name: "app", namespace: "default" },
  { kind: "Route", name: "app", namespace: "default" }
]
```

## Passing State Between Skills

When delegating between skills, pass these values:

| From | To | Values Passed |
|------|-----|---------------|
| `/containerize-deploy` | `/detect-project` | (none - detect provides values) |
| `/detect-project` | `/recommend-image` | `LANGUAGE`, `FRAMEWORK`, `VERSION` |
| `/recommend-image` | caller | `BUILDER_IMAGE`, `IMAGE_VARIANT`, `SELECTION_RATIONALE` |
| `/containerize-deploy` | `/rhel-deploy` | `APP_NAME`, `LANGUAGE`, `FRAMEWORK`, `VERSION`, `BUILDER_IMAGE`, `CONTAINER_PORT` |
| `/containerize-deploy` | `/helm-deploy` | `APP_NAME`, `NAMESPACE`, `HELM_CHART_PATH` |

# Role-Based Access Control (RBAC)

General concepts for understanding and managing OpenShift RBAC.

---

## Overview

OpenShift uses Kubernetes RBAC to control access to cluster resources. This guide covers fundamental concepts to help you understand and respond to user requests involving permissions, roles, and access control.

**Scope**: Conceptual understanding, not detailed procedures. Use MCP tools to apply RBAC configurations based on these concepts.

---

## Core Concepts

### Resources

**What they are**: API objects in the cluster (Pods, Services, Deployments, ConfigMaps, etc.)

**Resource Types**:
- **Namespaced**: Exist within a namespace (Pods, Services, Deployments)
- **Cluster-scoped**: Exist at cluster level (Nodes, PersistentVolumes, Namespaces)

### Verbs (Actions)

**Common verbs** that can be performed on resources:
- `get` - Retrieve a single resource
- `list` - List multiple resources
- `watch` - Watch for changes
- `create` - Create new resource
- `update` - Modify existing resource
- `patch` - Partially modify resource
- `delete` - Remove resource
- `deletecollection` - Remove multiple resources

### Subjects

**Who** is being granted permissions:
- **User**: Individual human user
- **Group**: Collection of users
- **ServiceAccount**: Non-human identity for applications/automation

---

## Role Types

### Role (Namespaced)

**Scope**: Permissions within a single namespace

**Use when**: Granting access to resources in specific project/namespace

**Example use cases**:
- Allow developer to manage pods in "dev" namespace
- Grant team access to secrets in "production" namespace
- Enable CI/CD to deploy to "staging" namespace

### ClusterRole (Cluster-wide)

**Scope**: Permissions across entire cluster or for cluster-scoped resources

**Use when**:
- Granting access to cluster-scoped resources (Nodes, PersistentVolumes)
- Creating reusable role definitions
- Granting cluster-wide permissions

**Example use cases**:
- Allow admin to manage all namespaces
- Grant monitoring tool access to metrics across cluster
- Enable backup tool to read all resources

---

## Binding Types

### RoleBinding (Namespaced)

**What it does**: Grants Role or ClusterRole permissions to subjects **within a namespace**

**Key concept**: Can bind both Role and ClusterRole, but permissions limited to namespace

**Use cases**:
- Bind user "alice" to "admin" role in "production" namespace
- Bind service account to "edit" role in "my-app" namespace

### ClusterRoleBinding (Cluster-wide)

**What it does**: Grants ClusterRole permissions to subjects **across entire cluster**

**Use cases**:
- Bind user "bob" to "cluster-admin" role
- Grant monitoring service account cluster-wide read access

---

## Predefined Roles

OpenShift provides predefined ClusterRoles for common scenarios:

### cluster-admin

**Permissions**: Full cluster administrative access
**Scope**: Cluster-wide
**Use for**: Platform administrators, cluster operators
**Risk**: Highest - can modify/delete anything

### admin

**Permissions**: Full administrative access within namespace
**Scope**: Namespace
**Use for**: Project owners, team leads
**Can**: Create, modify, delete resources; manage RBAC within namespace
**Cannot**: Delete namespace itself, access cluster-scoped resources

### edit

**Permissions**: Read/write access to most resources
**Scope**: Namespace
**Use for**: Developers, application owners
**Can**: Deploy applications, manage app resources
**Cannot**: Manage roles, view secrets (unless granted separately)

### view

**Permissions**: Read-only access to most resources
**Scope**: Namespace
**Use for**: Read-only users, auditors
**Can**: View resources
**Cannot**: Modify anything, view secrets

### self-provisioner

**Permissions**: Create new projects/namespaces
**Scope**: Cluster-wide
**Use for**: Users allowed to create their own projects
**Default**: Granted to all authenticated users (can be removed)

---

## Understanding Permission Flow

### How RBAC Works

1. **Subject** (user, group, or service account)
2. **Requests action** (verb) on **resource**
3. **RBAC evaluates** all RoleBindings and ClusterRoleBindings
4. **Permission granted** if ANY binding allows the action
5. **Permission denied** if NO binding allows the action

### Important Principles

**Default Deny**: If no role grants permission, access is denied

**Union of Permissions**: User gets permissions from ALL their role bindings combined

**No Explicit Deny**: Cannot explicitly deny permissions, only grant them

**Namespace Isolation**: RoleBinding in namespace-A doesn't grant access to namespace-B

---

## Common Scenarios

### Grant User Admin Access to Namespace
- Use `admin` ClusterRole with RoleBinding in target namespace
- Grants full namespace control except namespace deletion

### Grant Service Account Cluster-Wide Read
- Use `view` ClusterRole with ClusterRoleBinding
- Binds service account (include namespace in subject)

### Grant Team Access to Multiple Namespaces
- Create RoleBinding in each namespace
- All bind same group/user to same ClusterRole (e.g., `edit`)

### Create Custom Limited Permissions
- Define custom Role with specific `apiGroups`, `resources`, `verbs`
- Bind via RoleBinding to user/group/service account

---

## Service Accounts

**Purpose**: Non-human identities for applications, automation, CI/CD

**Use for**: Application pods, CI/CD pipelines, monitoring tools, automation

**Authentication**: JWT token mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token`

**Token types**: Time-bound (recommended) or long-lived (legacy)

**RBAC**: Grant permissions via RoleBinding/ClusterRoleBinding like any subject

---

## Groups

**Built-in**: `system:authenticated` (all users), `system:unauthenticated` (anonymous)

**Custom**: From identity providers (LDAP, OAuth)

**Binding**: Use `kind: Group` in subjects; all members inherit permissions

**Use for**: Team-based access, simplify permission management

---

## API Groups

### Understanding API Groups

**What they are**: Resource organization in Kubernetes API

**Examples**:
- `""` (core/v1): Pods, Services, ConfigMaps, Secrets
- `apps`: Deployments, StatefulSets, DaemonSets
- `rbac.authorization.k8s.io`: Roles, RoleBindings
- `route.openshift.io`: Routes (OpenShift-specific)

**Why it matters for RBAC**:
- Permissions specified per API group
- Wildcard `*` grants access to all groups (rarely recommended)
- Custom resources have their own API groups

**Example permission rule**:
```yaml
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "create"]
```

---

## Checking Permissions

### Current User Permissions

**Check what you can do**:

```
MCP Tool: resources_list
Parameters: {kind: "SelfSubjectAccessReview"}

Or use kubectl plugin approach:
kubectl auth can-i <verb> <resource>
```

**Examples**:
- Can I create pods? `kubectl auth can-i create pods`
- Can I delete namespace? `kubectl auth can-i delete namespace`
- Can I list secrets in namespace-X? `kubectl auth can-i list secrets -n namespace-x`

### Checking Other User's Permissions

**Requires cluster-admin or appropriate RBAC**:

```
kubectl auth can-i <verb> <resource> --as <user>
kubectl auth can-i <verb> <resource> --as system:serviceaccount:<namespace>:<sa-name>
```

---

## Best Practices

### Principle of Least Privilege

✅ Grant minimum permissions needed
✅ Start with narrow permissions, expand if needed
❌ Don't default to cluster-admin
❌ Don't grant wildcard permissions unless necessary

### Use Predefined Roles When Possible

✅ Leverage `admin`, `edit`, `view` roles
✅ Combine multiple role bindings for complex needs
❌ Don't create custom roles for common scenarios

### Namespace Isolation

✅ Use namespaces to separate environments/teams
✅ Use RoleBindings for namespace-scoped permissions
✅ Reserve ClusterRoleBindings for truly cluster-wide needs

### Service Account Security

✅ Create dedicated service accounts per application
✅ Grant minimal permissions to service accounts
✅ Use time-bound tokens when possible
❌ Don't use default service account for applications
❌ Don't share service account tokens between applications

### Audit and Review

✅ Regularly review RoleBindings and ClusterRoleBindings
✅ Remove bindings for users who no longer need access
✅ Monitor for privilege escalation attempts
✅ Use admission controllers to enforce policies

---

## Common Mistakes to Avoid

### Granting Excessive Permissions

❌ Making all developers cluster-admin
❌ Granting wildcard `*` permissions
❌ Giving edit/admin when view is sufficient

**Instead**: Start narrow, expand based on actual needs

### Confusing Role Types

❌ Using ClusterRoleBinding when RoleBinding is sufficient
❌ Trying to bind Role across namespaces (use ClusterRole instead)

**Remember**:
- Role = namespaced permissions
- ClusterRole = cluster-wide or reusable definition

### Not Understanding Scope

❌ Expecting RoleBinding to grant cluster-scoped resource access
❌ Thinking namespace admin can delete namespace itself

**Remember**: RoleBinding is limited to namespace, even when binding ClusterRole

---

## Troubleshooting Access Issues

### User Can't Perform Action

**Check**:
1. User is authenticated (not anonymous)
2. User has appropriate RoleBinding or ClusterRoleBinding
3. RoleBinding is in correct namespace
4. Role references correct resources and verbs
5. API group is specified correctly in role

**Debugging**:
```
# Check what user can do
kubectl auth can-i <verb> <resource> --as <user>

# List user's role bindings
MCP Tool: resources_list
Parameters: {kind: "RoleBinding", namespace: "<namespace>"}
Filter: subjects contain user

# List user's cluster role bindings
MCP Tool: resources_list
Parameters: {kind: "ClusterRoleBinding"}
Filter: subjects contain user
```

### Service Account Can't Access Resources

**Common causes**:
- Service account doesn't exist
- No RoleBinding grants permissions to service account
- Service account in wrong namespace
- Token not mounted or expired

**Solution**:
1. Verify service account exists
2. Create RoleBinding for service account
3. Ensure binding is in correct namespace
4. Check token is valid and mounted

---

## Security Context Constraints (SCCs)

### Overview

**What they are**: OpenShift-specific resource controlling what pods can do at the host/kernel level

**Purpose**: Prevent containers from accessing host resources inappropriately

**Difference from RBAC**:
- RBAC: Controls access to Kubernetes API resources
- SCCs: Controls what containers can do on nodes (privileged operations, host access, etc.)

### Common SCCs (Predefined)

**restricted** (default):
- Most restrictive
- No host access
- No privileged containers
- Non-root user required
- Use for: Regular applications

**restricted-v2** (recommended default):
- Enhanced restricted policy
- Drops ALL capabilities
- Use for: Modern applications

**anyuid**:
- Allows running as any UID
- No root privileges to host
- Use for: Legacy apps requiring specific UID

**hostaccess**:
- Allows host network/IPC/PID
- Use for: Networking/monitoring tools

**privileged**:
- Full host access
- Dangerous - avoid when possible
- Use for: Infrastructure components only

### How SCCs Work

1. Pod created with service account
2. Service account has SCC bound via RoleBinding
3. OpenShift evaluates all SCCs available to service account
4. **Least restrictive matching SCC** is applied
5. Pod admitted if meets SCC constraints

### Granting SCC to Service Account

```
MCP Tool: resources_create
Parameters:
  apiVersion: "rbac.authorization.k8s.io/v1"
  kind: "RoleBinding"  # or ClusterRoleBinding
  metadata:
    name: "sa-anyuid"
    namespace: "<namespace>"
  roleRef:
    apiGroup: "rbac.authorization.k8s.io"
    kind: "ClusterRole"
    name: "system:openshift:scc:anyuid"
  subjects:
  - kind: "ServiceAccount"
    name: "<sa-name>"
    namespace: "<namespace>"
```

**Pattern**: Bind service account to `system:openshift:scc:<scc-name>` ClusterRole

### Best Practices

✅ Use most restrictive SCC possible
✅ Default to `restricted-v2` for new workloads
✅ Grant SCCs to service accounts, not users
✅ Create custom SCCs for specific needs (rare)
❌ Don't grant `privileged` SCC unless absolutely required
❌ Don't grant SCCs to `default` service account

---

## Related Documentation

- [Credentials Management](./credentials-management.md) - Kubeconfig and authentication
- [Security Checklist](./security-checklist.md) - Security best practices
- [Identity Providers](./idp.md) - User authentication configuration

---

## Official References

- [Kubernetes RBAC Documentation](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [OpenShift RBAC](https://docs.openshift.com/container-platform/latest/authentication/using-rbac.html)

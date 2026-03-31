---
title: Identity Providers (IDP)
category: authentication
sources:
  - title: Understanding identity provider configuration
    url: https://docs.openshift.com/container-platform/latest/authentication/understanding-identity-provider.html
    date_accessed: 2026-03-31
  - title: Configuring LDAP identity provider
    url: https://docs.openshift.com/container-platform/latest/authentication/identity_providers/configuring-ldap-identity-provider.html
    date_accessed: 2026-03-31
tags: [idp, authentication, ldap, oauth, htpasswd, sso, identity-management]
semantic_keywords: [identity providers, user authentication, ldap configuration, oauth setup, htpasswd, openid connect, sso integration]
use_cases: [cluster-configuration, user-management, authentication-setup]
related_docs: [rbac.md, security-checklist.md, day-2-operations.md]
last_updated: 2026-03-31
---

# Identity Providers (IDP)

Configuration of identity providers for user authentication in OpenShift.

---

## Overview

OpenShift uses OAuth for user authentication. After initial deployment with kubeadmin, configure identity providers for regular user access.

**Scope**: Identity provider concepts and configuration patterns using MCP tools.

---

## Supported Identity Providers

### HTPasswd

**Type**: Simple username/password file

**Use for**:
- Development clusters
- Small teams
- Proof of concept
- When LDAP/SSO unavailable

**Pros**: Easy to setup, no external dependencies
**Cons**: Manual user management, not scalable

### LDAP

**Type**: Lightweight Directory Access Protocol

**Use for**:
- Enterprise environments
- Active Directory integration
- Centralized user management

**Pros**: Centralized, scalable, integrates with existing infrastructure
**Cons**: Requires LDAP server, more complex configuration

### GitHub / GitHub Enterprise

**Type**: OAuth via GitHub

**Use for**:
- Development teams using GitHub
- Organizations with GitHub Enterprise

**Pros**: Leverages existing GitHub accounts
**Cons**: Requires GitHub access, internet connectivity

### OpenID Connect (OIDC)

**Type**: OAuth 2.0 with identity layer

**Use for**:
- Integration with Keycloak, Google, Azure AD
- SSO scenarios
- Modern authentication flows

**Pros**: Standards-based, flexible, supports MFA
**Cons**: Requires OIDC provider

### Other Providers

- **GitLab**: OAuth via GitLab
- **Google**: OAuth via Google accounts
- **Azure AD**: Integration with Microsoft Azure

---

## Configuration Pattern

### General Structure

**Note**: Identity provider configuration is a Day-2 operation requiring direct cluster access via `oc` CLI or the `openshift-administration` MCP server when using Claude Code with KUBECONFIG set.

All identity providers configured via OAuth custom resource:

```yaml
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: "<provider-name>"
    type: "<provider-type>"
    mappingMethod: "claim"  # or "add", "lookup", "generate"
    <provider-specific-config>
```

Apply with: `oc apply -f oauth.yaml`

### Mapping Methods

**claim** (recommended): Use identity from provider as-is
**add**: Fail if identity conflicts with existing user
**lookup**: Look up existing user, fail if not found
**generate**: Auto-generate username if conflict

---

## HTPasswd Configuration

### Creating htpasswd File

```bash
# Local operation (not MCP)
htpasswd -c -B -b users.htpasswd admin <password>
htpasswd -B -b users.htpasswd developer <password>
htpasswd -B -b users.htpasswd viewer <password>

# View file
cat users.htpasswd
```

### Uploading to OpenShift

```bash
# 1. Create secret with htpasswd file
oc create secret generic htpass-secret \
  --from-file=htpasswd=users.htpasswd \
  -n openshift-config

# 2. Configure OAuth to use HTPasswd
oc apply -f - <<EOF
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: htpasswd_provider
    type: HTPasswd
      mappingMethod: "claim"
      htpasswd:
        fileData:
          name: "htpass-secret"
```

### Adding/Removing Users

```bash
# Add user locally
htpasswd -B -b users.htpasswd newuser <password>

# Update secret in OpenShift
# Re-create secret with updated htpasswd file (same as above)
```

---

## LDAP Configuration

### Basic Structure

```bash
oc apply -f - <<EOF
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: ldap_provider
    type: LDAP
    mappingMethod: claim
    ldap:
      url: "ldap://ldap.example.com:389/dc=example,dc=com?uid"
      bindDN: "cn=admin,dc=example,dc=com"
      bindPassword:
        name: ldap-secret  # Secret in openshift-config
      insecure: false  # Set true only for testing
      ca:
        name: ldap-ca-cert  # Secret with LDAP CA certificate
      attributes:
        id: ["dn"]
        preferredUsername: ["uid"]
        name: ["cn"]
        email: ["mail"]
EOF
```

### LDAP URL Format

**Pattern**: `ldap[s]://host:port/basedn?attribute?scope?filter`

**Examples**:
- `ldap://ldap.example.com:389/ou=users,dc=example,dc=com?uid`
- `ldaps://ldap.example.com:636/dc=example,dc=com?uid?sub?(objectClass=person)`

### Creating LDAP Bind Secret

```bash
oc create secret generic ldap-secret \
  --from-literal=bindPassword='<ldap-bind-password>' \
  -n openshift-config
```

---

## OpenID Connect (OIDC) Configuration

### Keycloak Example

```bash
oc apply -f - <<EOF
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: keycloak
    type: OpenID
    mappingMethod: claim
    openID:
      clientID: openshift
      clientSecret:
        name: oidc-secret  # Secret with client secret
      issuer: "https://keycloak.example.com/auth/realms/master"
      claims:
          preferredUsername: ["preferred_username"]
          name: ["name"]
          email: ["email"]
```

### Google OIDC Example

```
openID:
  clientID: "<google-client-id>"
  clientSecret:
    name: "google-secret"
  issuer: "https://accounts.google.com"
  claims:
    preferredUsername: ["email"]
    name: ["name"]
    email: ["email"]
```

---

## GitHub OAuth Configuration

```bash
oc apply -f - <<EOF
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: github
    type: GitHub
    mappingMethod: claim
    github:
      clientID: "<github-oauth-app-client-id>"
      clientSecret:
        name: github-secret
      organizations:  # Optional: restrict to org members
      - my-org
      teams:  # Optional: restrict to specific teams
      - my-org/team-name
EOF
```

### Creating GitHub OAuth App

1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create New OAuth App
3. Set Authorization callback URL: `https://oauth-openshift.apps.<cluster>.<domain>/oauth2callback/github`
4. Note Client ID and generate Client Secret

---

## Multiple Identity Providers

**Supported**: Yes, can configure multiple providers simultaneously

**Use case**: Allow users to choose authentication method

```
spec:
  identityProviders:
  - name: "ldap_provider"
    type: "LDAP"
    ...
  - name: "github_provider"
    type: "GitHub"
    ...
  - name: "htpasswd_provider"
    type: "HTPasswd"
    ...
```

**Login flow**: Users choose provider on login page

---

## Identity to User Mapping

### How It Works

1. User authenticates via identity provider
2. Provider returns identity (username, email, etc.)
3. OpenShift creates User object if doesn't exist
4. Identity linked to User
5. User can then be granted RBAC permissions

### Viewing Users and Identities

```bash
# List all users
oc get users

# List all identities with provider info
oc get identities
```

---

## Removing Kubeadmin User

**⚠️ Only perform if explicitly requested by user**

**Prerequisites**:
1. Alternative admin user configured and tested
2. Alternative user has cluster-admin role
3. Kubeadmin credentials backed up

**Process**:

```
# Verify alternative admin
# Verify non-kubeadmin users exist
oc get users

# Delete kubeadmin secret
oc delete secret kubeadmin -n kube-system
```

**Post-deletion**: Kubeadmin cannot be re-enabled without cluster reinstall

---

## Troubleshooting

### Users Can't Login

**Check**:
1. Identity provider configured correctly in OAuth
2. Provider-specific secrets exist in openshift-config
3. OAuth pods running in openshift-authentication namespace
4. Network connectivity to external provider (LDAP, GitHub, etc.)

**Debug**:
```bash
# Check OAuth configuration
oc get oauth cluster -o yaml

# Check authentication pods
oc get pods -n openshift-authentication

# Check pod logs
oc logs -n openshift-authentication <oauth-pod-name>
```

### Identity Provider Not Showing on Login Page

**Cause**: OAuth configuration not applied or invalid

**Solution**:
1. Verify OAuth resource created/updated
2. Wait 1-2 minutes for OAuth operator to reconcile
3. Check authentication pod logs for errors

### User Created But No Permissions

**Cause**: User exists but has no RBAC bindings

**Solution**: Create RoleBinding or ClusterRoleBinding for user (see RBAC documentation)

---

## Best Practices

### Security

✅ Use LDAPS (LDAP over SSL) for LDAP providers
✅ Use OIDC with MFA when possible
✅ Store client secrets securely in Secrets
✅ Restrict GitHub/OIDC to specific organizations/groups
❌ Don't use `insecure: true` in production
❌ Don't hardcode passwords in OAuth configuration

### User Management

✅ Configure identity provider before removing kubeadmin
✅ Test with regular user before removing admin access
✅ Use groups from LDAP/OIDC for easier permission management
✅ Document which identity provider is used

### Scalability

✅ Use LDAP/OIDC for large user bases
✅ Leverage group mappings from identity provider
❌ Don't use HTPasswd for production with many users

---

## Related Documentation

- [RBAC](./rbac.md) - Role-Based Access Control
- [Credentials Management](./credentials-management.md) - Authentication setup
- [Security Checklist](./security-checklist.md) - Security verification

---

## Official References

- [OpenShift Identity Providers](https://docs.openshift.com/container-platform/latest/authentication/understanding-identity-provider.html)
- [OAuth Configuration](https://docs.openshift.com/container-platform/latest/authentication/configuring-oauth-clients.html)

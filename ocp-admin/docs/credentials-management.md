# Credentials and Identity Management

Comprehensive guide to managing credentials and identity providers in OpenShift.

---

## Overview

OpenShift security relies on proper credential management and identity provider configuration. This guide covers kubeconfig, kubeadmin password, OAuth, and identity provider integration.

---

## Cluster Credentials

### Kubeconfig File

**Purpose**: Authentication configuration for `oc` and `kubectl` CLI tools

**Location After Installation**: `/tmp/<cluster-name>/kubeconfig`

**Format**: YAML file containing:
- Cluster API endpoint
- Certificate authority (CA) data
- User authentication credentials (certificates or tokens)
- Context (cluster + user + namespace)

**Example Structure**:
```yaml
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: <base64-encoded-ca-cert>
    server: https://api.cluster-name.example.com:6443
  name: cluster-name
contexts:
- context:
    cluster: cluster-name
    user: admin
    namespace: default
  name: admin
current-context: admin
users:
- name: admin
  user:
    client-certificate-data: <base64-encoded-client-cert>
    client-key-data: <base64-encoded-client-key>
```

**Usage**:
```bash
# Set environment variable (temporary)
export KUBECONFIG=/path/to/kubeconfig

# Use with command
oc --kubeconfig=/path/to/kubeconfig get nodes

# Merge with existing kubeconfig
KUBECONFIG=~/.kube/config:/tmp/cluster/kubeconfig kubectl config view --flatten > ~/.kube/config
```

---

### Kubeadmin Password

**Purpose**: Initial administrative access to OpenShift

**User**: `kubeadmin`
**Role**: `cluster-admin` (full cluster administrative access)

**Location After Installation**: `/tmp/<cluster-name>/kubeadmin-password`

**Usage**:
```bash
# Read password
cat /tmp/<cluster-name>/kubeadmin-password

# Login via CLI
oc login -u kubeadmin -p <password> https://api.cluster-name.example.com:6443

# Login via Web Console
URL: https://console-openshift-console.apps.cluster-name.example.com
User: kubeadmin
Password: <from file>
```

**Security Considerations**:
- ⚠️ **Temporary credential** - Should be replaced with proper identity provider
- ⚠️ **High privileges** - Full cluster-admin access
- ⚠️ **Delete after IDP setup** - Remove kubeadmin user once other admins exist

---

## Security Best Practices

### Kubeconfig Security

**File Permissions**:
```bash
# Set restrictive permissions (owner read/write only)
chmod 600 /path/to/kubeconfig

# Verify permissions
ls -l /path/to/kubeconfig
# Should show: -rw------- (600)
```

**Storage Recommendations**:
- ✅ Store in user home directory: `~/.kube/config`
- ✅ Encrypt home directory or use encrypted disk
- ✅ Use separate kubeconfigs for different clusters
- ✅ Regular backup (encrypted)
- ❌ Never commit to version control (Git, SVN, etc.)
- ❌ Never share via email, chat, or public links
- ❌ Never store in publicly accessible directories
- ❌ Never use the same kubeconfig on untrusted systems

**Kubeconfig Rotation**:
- Certificates expire after 1 year by default
- Rotate credentials regularly (every 90 days recommended)
- Use short-lived tokens when possible

### Password Management

**Kubeadmin Password**:
- ✅ Store in password manager (1Password, Bitwarden, etc.)
- ✅ Use temporary storage (/tmp) initially
- ✅ Delete after configuring identity provider
- ❌ Never share or expose publicly
- ❌ Don't leave in plain text files long-term

**SSH Private Keys** (for node access):
- ✅ Permissions: 600 (read/write owner only)
- ✅ Store in `~/.ssh/` directory
- ✅ Use passphrase protection
- ✅ Use separate keys per cluster
- ❌ Never commit to version control
- ❌ Never share private keys

---

## Temporary vs Permanent Storage

### Temporary Storage (/tmp)

**Characteristics**:
- Cleared on system reboot
- Good for initial credential download
- Prevents accidental long-term storage

**Use Cases**:
- Initial kubeconfig download
- Initial kubeadmin password download
- Temporary testing

**Lifespan**: Until reboot or manual deletion

**Example**:
```bash
# Download to temporary storage
mkdir -p /tmp/my-cluster && chmod 700 /tmp/my-cluster
curl -o /tmp/my-cluster/kubeconfig <url>
chmod 600 /tmp/my-cluster/kubeconfig

# Use temporarily
export KUBECONFIG=/tmp/my-cluster/kubeconfig
oc get nodes
```

### Permanent Storage (~/.kube)

**Characteristics**:
- Persists across reboots
- Standard location for kubectl/oc
- User-specific storage

**Use Cases**:
- Day-to-day cluster access
- Production kubeconfig
- Long-term usage

**Example**:
```bash
# Copy to permanent storage
mkdir -p ~/.kube
cp /tmp/my-cluster/kubeconfig ~/.kube/config
chmod 600 ~/.kube/config

# Now available for all oc/kubectl commands
oc get nodes
```

**Migration Prompt**:
After installation completes, skill should ask:
```
⚠️ Credentials currently in /tmp/ (temporary - cleared on reboot)

Would you like to copy credentials to permanent storage? (yes/no)

If yes:
  - Kubeconfig will be copied to ~/.kube/config
  - Kubeadmin password will be copied to ~/.kube/kubeadmin-password
  - Permissions will be set to 600 (secure)
```

---

## Identity Providers (OAuth)

### Overview

OpenShift uses OAuth for user authentication. After initial deployment with kubeadmin, configure identity providers for regular users.

**Supported Identity Providers**:
- HTPasswd (basic username/password file)
- LDAP (Lightweight Directory Access Protocol)
- GitHub / GitHub Enterprise
- GitLab
- Google
- OpenID Connect
- KeyCloak
- Active Directory (via LDAP)

### HTPasswd (Simple Username/Password)

**Use Cases**:
- Development clusters
- Small teams
- Proof of concept
- When LDAP/SSO unavailable

**Setup**:
```bash
# Create htpasswd file
htpasswd -c -B -b users.htpasswd admin <password>
htpasswd -B -b users.htpasswd developer <password>

# Create secret in openshift-config namespace
oc create secret generic htpass-secret --from-file=htpasswd=users.htpasswd -n openshift-config

# Configure OAuth to use HTPasswd
oc apply -f - <<EOF
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: htpasswd_provider
    mappingMethod: claim
    type: HTPasswd
    htpasswd:
      fileData:
        name: htpass-secret
EOF
```

**Limitations**:
- Manual user management
- No password policy enforcement
- No self-service password reset
- Not suitable for large organizations

### LDAP Integration

**Use Cases**:
- Enterprise environments
- Centralized user management
- Active Directory integration
- Large organizations

**Configuration**:
```yaml
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: ldap_provider
    mappingMethod: claim
    type: LDAP
    ldap:
      attributes:
        id:
        - dn
        email:
        - mail
        name:
        - cn
        preferredUsername:
        - uid
      bindDN: "cn=admin,dc=example,dc=com"
      bindPassword:
        name: ldap-secret
      insecure: false
      ca:
        name: ldap-ca
      url: "ldaps://ldap.example.com:636/ou=users,dc=example,dc=com?uid"
```

**Setup Steps**:
1. Create bind DN secret
2. Create CA certificate configmap (if using LDAPS)
3. Configure OAuth resource
4. Test login

**Advantages**:
- Centralized user management
- Password policies enforced
- Group synchronization
- Audit logging

### GitHub OAuth

**Use Cases**:
- Open source projects
- GitHub-centric teams
- Public repositories

**Configuration**:
```yaml
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: github
    mappingMethod: claim
    type: GitHub
    github:
      clientID: <github-oauth-app-client-id>
      clientSecret:
        name: github-secret
      organizations:
      - my-organization
```

**Setup Steps**:
1. Register OAuth App in GitHub
2. Configure callback URL: `https://oauth-openshift.apps.<cluster>.<domain>/oauth2callback/github`
3. Create secret with client ID and secret
4. Configure OAuth resource

### OpenID Connect (OIDC)

**Use Cases**:
- Enterprise SSO (KeyCloak, Okta, Auth0)
- Modern authentication flows
- Multi-factor authentication

**Configuration**:
```yaml
apiVersion: config.openshift.io/v1
kind: OAuth
metadata:
  name: cluster
spec:
  identityProviders:
  - name: oidc
    mappingMethod: claim
    type: OpenID
    openID:
      clientID: openshift
      clientSecret:
        name: oidc-secret
      issuer: https://keycloak.example.com/auth/realms/master
      claims:
        preferredUsername:
        - preferred_username
        name:
        - name
        email:
        - email
```

---

## Role-Based Access Control (RBAC)

### Cluster Roles

**Predefined Roles**:
- `cluster-admin` - Full cluster administrative access
- `admin` - Project administrative access
- `edit` - Edit resources within project
- `view` - Read-only access to project resources
- `self-provisioner` - Can create new projects

**Assigning Cluster Role**:
```bash
# Grant cluster-admin to user
oc adm policy add-cluster-role-to-user cluster-admin alice

# Grant admin role to user in specific project
oc adm policy add-role-to-user admin bob -n my-project

# Grant view role to group
oc adm policy add-role-to-group view developers -n my-project
```

### Service Accounts

**Purpose**: Non-human identities for applications and automation

**Creating Service Account**:
```bash
# Create service account
oc create serviceaccount automation -n my-project

# Grant permissions
oc adm policy add-role-to-user edit system:serviceaccount:my-project:automation -n my-project

# Get service account token
oc sa get-token automation -n my-project
```

**Usage in CI/CD**:
```bash
# Login with service account token
oc login --token=<service-account-token> https://api.cluster.example.com:6443

# Use in automation scripts
TOKEN=$(oc sa get-token automation -n my-project)
curl -H "Authorization: Bearer $TOKEN" https://api.cluster.example.com:6443/api/v1/namespaces
```

---

## Removing Kubeadmin User

**When**: After configuring identity provider and creating cluster admin users

**Steps**:
```bash
# Verify other admin users exist
oc get users
oc get clusterrolebindings | grep cluster-admin

# Ensure you have another admin
oc adm policy add-cluster-role-to-user cluster-admin alice

# Remove kubeadmin secret
oc delete secret kubeadmin -n kube-system

# Verify removal
oc login -u kubeadmin
# Should fail: "Login failed (401 Unauthorized)"
```

**⚠️ WARNING**: Ensure you have alternative admin access before removing kubeadmin!

---

## Credential Rotation

### Certificate Rotation

**Cluster Certificates**:
- Auto-rotated by OpenShift (before expiration)
- Manual rotation if needed:
```bash
# Force certificate rotation
oc adm certificate approve --all
```

**API Client Certificates**:
- Generated in kubeconfig
- Expire after 24 hours (default)
- Auto-renewed on oc login

### Token Rotation

**Service Account Tokens**:
```bash
# Generate new token
oc sa new-token automation -n my-project

# Update automation with new token
```

**OAuth Tokens**:
- Short-lived access tokens (auto-refresh)
- Revoke user sessions:
```bash
# Delete user token secrets
oc delete secret <token-secret-name> -n openshift-authentication
```

---

## Multi-Cluster Credential Management

**Managing Multiple Clusters**:
```bash
# Merge multiple kubeconfigs
KUBECONFIG=~/.kube/cluster-a:~/.kube/cluster-b:~/.kube/cluster-c kubectl config view --flatten > ~/.kube/config

# Switch between clusters
oc config use-context cluster-a
oc config use-context cluster-b

# View all contexts
oc config get-contexts

# Current context
oc config current-context
```

**Best Practice**: Use separate kubeconfig files per cluster, merge as needed

---

## Troubleshooting

### Issue: "Unauthorized" Error
**Cause**: Expired or invalid credentials

**Resolution**:
```bash
# Check kubeconfig validity
oc whoami

# Re-login
oc login https://api.cluster.example.com:6443

# Check certificate expiration
openssl x509 -in <cert-file> -text -noout | grep "Not After"
```

### Issue: Cannot Access Cluster After Kubeadmin Removal
**Cause**: No alternative admin users configured

**Resolution**:
- Access cluster via emergency kubeconfig (if available)
- Or re-install kubeadmin (complex, requires API access)
- Prevention: Always verify admin access before removing kubeadmin

### Issue: Identity Provider Not Working
**Cause**: Misconfigured OAuth or secret

**Resolution**:
```bash
# Check OAuth configuration
oc get oauth cluster -o yaml

# Check identity provider pods
oc get pods -n openshift-authentication

# Check OAuth server logs
oc logs -n openshift-authentication <oauth-pod-name>
```

---

## Security Checklist

**Post-Installation**:
- ✅ Kubeconfig permissions set to 600
- ✅ Kubeadmin password stored securely
- ✅ Identity provider configured
- ✅ Admin users created via IDP
- ✅ Cluster-admin role assigned to IDP users
- ✅ Kubeadmin user deleted
- ✅ Service accounts created for automation
- ✅ RBAC policies reviewed and applied
- ✅ Credentials backed up securely

**Ongoing**:
- ✅ Regular credential rotation (90 days)
- ✅ Review access logs
- ✅ Audit cluster-admin assignments
- ✅ Remove unused service accounts
- ✅ Monitor OAuth logs

---

## References

- [OpenShift Authentication Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/authentication_and_authorization/)
- [Configuring Identity Providers](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/authentication_and_authorization/configuring-identity-providers)
- [RBAC Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/authentication_and_authorization/using-rbac)
- [Service Accounts](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/authentication_and_authorization/understanding-and-creating-service-accounts)

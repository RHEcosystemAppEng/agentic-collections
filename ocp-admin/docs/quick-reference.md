# Quick Reference

Common commands and operations for OpenShift cluster management.

---

## Cluster Access

### Using Kubeconfig

```bash
# Set kubeconfig environment variable (temporary)
export KUBECONFIG=/tmp/<cluster-name>/kubeconfig

# Use specific kubeconfig for single command
oc --kubeconfig=/path/to/kubeconfig get nodes

# Copy to permanent location
mkdir -p ~/.kube
cp /tmp/<cluster-name>/kubeconfig ~/.kube/config
chmod 600 ~/.kube/config

# Merge multiple kubeconfigs
KUBECONFIG=~/.kube/cluster-a:~/.kube/cluster-b kubectl config view --flatten > ~/.kube/config

# Switch between contexts
oc config use-context <context-name>

# List all contexts
oc config get-contexts

# Show current context
oc config current-context
```

### Login to Cluster

```bash
# Login with kubeadmin (initial access)
oc login -u kubeadmin -p <password> https://api.<cluster>.<domain>:6443

# Login with token (service account or OAuth)
oc login --token=<token> https://api.<cluster>.<domain>:6443

# Login interactively (prompts for username/password)
oc login https://api.<cluster>.<domain>:6443
```

### Read Kubeadmin Password

```bash
# From file
cat /tmp/<cluster-name>/kubeadmin-password

# Display with cluster info
echo "Cluster: <cluster-name>"
echo "User: kubeadmin"
echo "Password: $(cat /tmp/<cluster-name>/kubeadmin-password)"
```

---

## Cluster Status

### Check Cluster Health

```bash
# Node status
oc get nodes

# Node details (resource usage, conditions)
oc describe node <node-name>

# Cluster operators status
oc get clusteroperators

# Cluster version
oc get clusterversion

# Overall cluster info
oc cluster-info
```

### Check Resource Usage

```bash
# Node resource usage (CPU, RAM)
oc adm top nodes

# Pod resource usage
oc adm top pods -A

# Pod resource usage in specific namespace
oc adm top pods -n <namespace>
```

### Check Events

```bash
# All cluster events (recent)
oc get events -A --sort-by='.lastTimestamp'

# Events in specific namespace
oc get events -n <namespace>

# Watch events in real-time
oc get events -w
```

---

## Troubleshooting

### Check Pod Issues

```bash
# List pods in all namespaces
oc get pods -A

# List pods in specific namespace
oc get pods -n <namespace>

# Describe pod (shows events, status)
oc describe pod <pod-name> -n <namespace>

# Get pod logs
oc logs <pod-name> -n <namespace>

# Get logs from previous container (if crashed)
oc logs <pod-name> -n <namespace> --previous

# Follow logs in real-time
oc logs -f <pod-name> -n <namespace>

# Execute command inside pod
oc exec -it <pod-name> -n <namespace> -- /bin/bash

# Get pod YAML
oc get pod <pod-name> -n <namespace> -o yaml
```

### Check Cluster Operators

```bash
# List all cluster operators
oc get clusteroperators

# Describe specific operator
oc describe clusteroperator <operator-name>

# Check operator pods
oc get pods -n openshift-<operator-namespace>

# Example: Check authentication operator
oc get pods -n openshift-authentication
oc logs <pod-name> -n openshift-authentication
```

### Network Diagnostics

```bash
# Check node-to-node connectivity
oc debug node/<node-name>
# Inside debug pod:
ping <other-node-ip>

# Check service endpoints
oc get endpoints -A

# Check routes
oc get routes -A

# Test DNS resolution
oc run -it --rm debug --image=registry.access.redhat.com/ubi9/ubi --restart=Never -- nslookup kubernetes.default

# Check NetworkPolicy
oc get networkpolicy -A

# Check OVN-Kubernetes pods
oc get pods -n openshift-ovn-kubernetes
```

### Storage Issues

```bash
# List persistent volumes
oc get pv

# List persistent volume claims
oc get pvc -A

# Describe PVC (shows binding status)
oc describe pvc <pvc-name> -n <namespace>

# Check storage classes
oc get storageclass

# Check CSI driver pods
oc get pods -n kube-system | grep csi
```

### Certificate Issues

```bash
# Check certificate expiration
oc get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].message}{"\n"}{end}'

# Check API server certificates
oc get secret -n openshift-kube-apiserver

# Approve pending certificate signing requests
oc get csr
oc adm certificate approve <csr-name>
```

---

## User Management

### Identity Providers

```bash
# Get OAuth configuration
oc get oauth cluster -o yaml

# Check identity provider pods
oc get pods -n openshift-authentication

# List users
oc get users

# List identities
oc get identities
```

### RBAC

```bash
# Grant cluster-admin to user
oc adm policy add-cluster-role-to-user cluster-admin <username>

# Grant admin role in namespace
oc adm policy add-role-to-user admin <username> -n <namespace>

# Grant edit role in namespace
oc adm policy add-role-to-user edit <username> -n <namespace>

# Grant view role in namespace
oc adm policy add-role-to-user view <username> -n <namespace>

# List role bindings in namespace
oc get rolebindings -n <namespace>

# List cluster role bindings
oc get clusterrolebindings

# Check user permissions
oc auth can-i <verb> <resource> --as=<username>
# Example: oc auth can-i create pods --as=alice
```

### Service Accounts

```bash
# Create service account
oc create serviceaccount <sa-name> -n <namespace>

# Grant permissions to service account
oc adm policy add-role-to-user edit system:serviceaccount:<namespace>:<sa-name> -n <namespace>

# Get service account token
oc sa get-token <sa-name> -n <namespace>

# Create token secret for service account
oc create token <sa-name> -n <namespace>
```

---

## Project (Namespace) Management

```bash
# Create new project
oc new-project <project-name>

# List all projects
oc get projects

# Switch to project
oc project <project-name>

# Delete project
oc delete project <project-name>

# Get current project
oc project
```

---

## Application Management

### Deployments

```bash
# Create deployment
oc create deployment <name> --image=<image>

# Scale deployment
oc scale deployment <name> --replicas=3

# Update deployment image
oc set image deployment/<name> <container-name>=<new-image>

# Rollout status
oc rollout status deployment/<name>

# Rollback deployment
oc rollout undo deployment/<name>

# Deployment history
oc rollout history deployment/<name>
```

### Routes and Services

```bash
# Expose service as route
oc expose service <service-name>

# Create route with specific hostname
oc create route edge --service=<service-name> --hostname=<custom-hostname>

# List routes
oc get routes

# Get route URL
oc get route <route-name> -o jsonpath='{.spec.host}'
```

---

## Operators

### OperatorHub

```bash
# List available operators
oc get packagemanifests -n openshift-marketplace

# Get operator details
oc describe packagemanifest <operator-name> -n openshift-marketplace

# List installed operators
oc get csv -A

# List operator subscriptions
oc get subscriptions -A
```

### Install Operator (Example: OpenShift Data Foundation)

```bash
# Create namespace
oc create namespace openshift-storage

# Create operator group
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: openshift-storage-operatorgroup
  namespace: openshift-storage
spec:
  targetNamespaces:
  - openshift-storage
EOF

# Create subscription
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: odf-operator
  namespace: openshift-storage
spec:
  channel: stable-4.18
  name: odf-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF

# Check installation status
oc get csv -n openshift-storage
```

---

## Maintenance

### Cluster Updates

```bash
# Check available updates
oc adm upgrade

# Update to specific version
oc adm upgrade --to=<version>

# Check update progress
oc get clusterversion
```

### Image Pruning

```bash
# Prune old images
oc adm prune images --confirm

# Prune old builds
oc adm prune builds --confirm

# Prune old deployments
oc adm prune deployments --confirm
```

### Drain Node (for Maintenance)

```bash
# Mark node unschedulable and evict pods
oc adm drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Mark node schedulable again
oc adm uncordon <node-name>
```

---

## Security

### Secrets

```bash
# Create generic secret
oc create secret generic <secret-name> --from-literal=key=value

# Create secret from file
oc create secret generic <secret-name> --from-file=<path-to-file>

# Create TLS secret
oc create secret tls <secret-name> --cert=<cert-file> --key=<key-file>

# List secrets
oc get secrets

# Decode secret value
oc get secret <secret-name> -o jsonpath='{.data.<key>}' | base64 -d
```

### Security Context Constraints (SCC)

```bash
# List SCCs
oc get scc

# Add SCC to service account
oc adm policy add-scc-to-user <scc-name> system:serviceaccount:<namespace>:<sa-name>

# Check which SCC a pod is using
oc get pod <pod-name> -o yaml | grep openshift.io/scc
```

---

## etcd Backup (Control Plane)

```bash
# Backup etcd (run on control plane node)
oc debug node/<master-node-name>
# Inside debug pod:
chroot /host
/usr/local/bin/cluster-backup.sh /home/core/backup

# List backups
ls -lh /home/core/backup/

# Copy backup to safe location
```

---

## Common Scenarios

### Scenario: "Pod is stuck in Pending"

```bash
# 1. Check pod status
oc describe pod <pod-name> -n <namespace>

# 2. Look for resource issues
oc adm top nodes
oc adm top pods -A

# 3. Check PVC binding
oc get pvc -n <namespace>

# 4. Check events
oc get events -n <namespace> --sort-by='.lastTimestamp'
```

### Scenario: "Cannot access cluster"

```bash
# 1. Verify API endpoint
ping api.<cluster>.<domain>

# 2. Check DNS resolution
nslookup api.<cluster>.<domain>

# 3. Test port connectivity
nc -zv api.<cluster>.<domain> 6443

# 4. Verify kubeconfig
oc config view

# 5. Check certificate validity
oc login --token=<token> https://api.<cluster>.<domain>:6443
```

### Scenario: "Route not accessible"

```bash
# 1. Check route exists
oc get route <route-name> -n <namespace>

# 2. Check route URL
oc get route <route-name> -o jsonpath='{.spec.host}'

# 3. Test DNS resolution
nslookup <route-hostname>

# 4. Check ingress pods
oc get pods -n openshift-ingress

# 5. Test connectivity
curl -I http://<route-hostname>
```

### Scenario: "Cluster operator degraded"

```bash
# 1. Check operator status
oc get clusteroperators

# 2. Describe degraded operator
oc describe clusteroperator <operator-name>

# 3. Check operator pods
oc get pods -n openshift-<operator-namespace>

# 4. Check pod logs
oc logs <pod-name> -n openshift-<operator-namespace>

# 5. Check recent events
oc get events -n openshift-<operator-namespace> --sort-by='.lastTimestamp'
```

---

## Useful Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# OpenShift aliases
alias k='oc'
alias kgp='oc get pods'
alias kgpa='oc get pods -A'
alias kgn='oc get nodes'
alias kgco='oc get clusteroperators'
alias kd='oc describe'
alias kl='oc logs'
alias ke='oc exec -it'
alias kdel='oc delete'

# Namespace switching
alias kn='oc project'

# Watch commands
alias wgp='watch -n2 "oc get pods"'
alias wgn='watch -n2 "oc get nodes"'
alias wgco='watch -n2 "oc get clusteroperators"'
```

---

## Emergency Procedures

### Reset Admin Password (if kubeadmin lost)

⚠️ **Requires control plane node access**

```bash
# 1. SSH to control plane node
ssh core@<master-node-ip>

# 2. Generate new kubeadmin secret
sudo -i
export KUBECONFIG=/etc/kubernetes/static-pod-resources/kube-apiserver-certs/secrets/node-kubeconfigs/localhost.kubeconfig
oc create secret generic kubeadmin \
  --from-literal=kubeadmin=$(openssl rand -base64 23) \
  -n kube-system

# 3. Retrieve new password
oc get secret kubeadmin -n kube-system -o jsonpath='{.data.kubeadmin}' | base64 -d
```

### Force Delete Namespace (stuck in Terminating)

```bash
# Get namespace manifest
oc get namespace <namespace-name> -o json > namespace.json

# Edit namespace.json, remove finalizers:
# "spec": {
#   "finalizers": []
# }

# Apply cleaned manifest
oc replace --raw "/api/v1/namespaces/<namespace-name>/finalize" -f namespace.json
```

---

## Performance Tuning

### Node Performance Profile

```bash
# Install Performance Addon Operator
# Then create PerformanceProfile

cat <<EOF | oc apply -f -
apiVersion: performance.openshift.io/v2
kind: PerformanceProfile
metadata:
  name: performance
spec:
  cpu:
    isolated: "2-23"
    reserved: "0-1"
  hugepages:
    defaultHugepagesSize: 1G
    pages:
    - size: 1G
      count: 16
  nodeSelector:
    node-role.kubernetes.io/worker-cnf: ""
  realTimeKernel:
    enabled: true
EOF
```

---

## References

- [INDEX](./INDEX.md) - Complete documentation index
- [Troubleshooting](./troubleshooting.md) - Detailed troubleshooting guide
- [OpenShift CLI Reference](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/cli_tools/openshift-cli-oc)
- [OpenShift Administration](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/post-installation_configuration/)

---

**Last Updated**: 2026-03-17
**OpenShift Version**: 4.18

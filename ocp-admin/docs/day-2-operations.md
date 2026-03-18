# Day-2 Operations

Post-installation operations and cluster maintenance for OpenShift.

---

## Overview

Day-2 operations encompass all management tasks performed after initial cluster installation. This includes monitoring, logging, updates, scaling, and ongoing maintenance.

---

## Cluster Monitoring

### Built-in Monitoring Stack

OpenShift includes a pre-configured monitoring stack based on Prometheus:

**Components**:
- **Prometheus** - Metrics collection and storage
- **Alertmanager** - Alert routing and notifications
- **Grafana** - Visualization dashboards (read-only)
- **Thanos** - Long-term metrics storage

**Accessing Metrics**:
```bash
# View cluster monitoring dashboards
oc get route -n openshift-monitoring

# Access Prometheus UI
https://prometheus-k8s-openshift-monitoring.apps.<cluster>.<domain>

# Access Alertmanager UI
https://alertmanager-main-openshift-monitoring.apps.<cluster>.<domain>

# Access Grafana
https://grafana-openshift-monitoring.apps.<cluster>.<domain>
```

**Check Monitoring Stack Health**:
```bash
# Check monitoring pods
oc get pods -n openshift-monitoring

# Check Prometheus targets
oc -n openshift-monitoring exec -it prometheus-k8s-0 -- promtool query instant http://localhost:9090 up

# Check metrics endpoint
oc get --raw /metrics
```

### Custom Monitoring for User Workloads

Enable user workload monitoring to monitor your applications:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-monitoring-config
  namespace: openshift-monitoring
data:
  config.yaml: |
    enableUserWorkload: true
```

**Apply Configuration**:
```bash
oc apply -f cluster-monitoring-config.yaml
```

**Create ServiceMonitor for Application**:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp-monitor
  namespace: myapp-namespace
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
  - port: metrics
    interval: 30s
```

**Query Custom Metrics**:
```bash
# Access user workload Prometheus
oc get route -n openshift-user-workload-monitoring

# Or use oc CLI
oc -n openshift-monitoring exec -it prometheus-k8s-0 -- \
  promtool query instant http://thanos-querier.openshift-monitoring:9091 \
  'up{namespace="myapp-namespace"}'
```

### Alerting

**View Current Alerts**:
```bash
# List firing alerts
oc get alerts

# View in Alertmanager UI
https://alertmanager-main-openshift-monitoring.apps.<cluster>.<domain>
```

**Create Custom Alert**:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: myapp-alerts
  namespace: myapp-namespace
spec:
  groups:
  - name: myapp
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status="500"}[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value }} errors/sec"
```

**Configure Alert Routing**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-main
  namespace: openshift-monitoring
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m
    route:
      group_by: ['alertname', 'cluster']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 12h
      receiver: 'default'
      routes:
      - match:
          severity: critical
        receiver: 'critical-alerts'
    receivers:
    - name: 'default'
      webhook_configs:
      - url: 'http://alertmanager-webhook.monitoring.svc:8080/alerts'
    - name: 'critical-alerts'
      email_configs:
      - to: 'oncall@example.com'
        from: 'alertmanager@cluster.example.com'
        smarthost: 'smtp.example.com:587'
```

---

## Logging

### ClusterLogging Operator

**Install ClusterLogging Operator**:

1. Install Elasticsearch Operator (dependency):
```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: elasticsearch-operator
  namespace: openshift-operators-redhat
spec:
  channel: stable
  name: elasticsearch-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF
```

2. Install ClusterLogging Operator:
```bash
cat <<EOF | oc apply -f -
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: cluster-logging
  namespace: openshift-logging
spec:
  channel: stable
  name: cluster-logging
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF
```

3. Create ClusterLogging instance:
```yaml
apiVersion: logging.openshift.io/v1
kind: ClusterLogging
metadata:
  name: instance
  namespace: openshift-logging
spec:
  managementState: Managed
  logStore:
    type: elasticsearch
    elasticsearch:
      nodeCount: 3
      storage:
        storageClassName: "gp2"
        size: 200G
      redundancyPolicy: SingleRedundancy
  visualization:
    type: kibana
    kibana:
      replicas: 1
  collection:
    logs:
      type: fluentd
      fluentd: {}
```

**Access Kibana**:
```bash
# Get Kibana route
oc get route kibana -n openshift-logging

# Access UI
https://kibana-openshift-logging.apps.<cluster>.<domain>
```

**View Logs via CLI**:
```bash
# View pod logs
oc logs <pod-name> -n <namespace>

# Follow logs
oc logs -f <pod-name> -n <namespace>

# View previous container logs (if crashed)
oc logs <pod-name> --previous -n <namespace>

# View logs from all containers in pod
oc logs <pod-name> --all-containers -n <namespace>
```

### Loki (Alternative Logging Stack)

Loki is a lighter alternative to Elasticsearch:

**Install Loki Operator**:
```bash
oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: loki-operator
  namespace: openshift-operators-redhat
spec:
  channel: stable
  name: loki-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF
```

**Create LokiStack**:
```yaml
apiVersion: loki.grafana.com/v1
kind: LokiStack
metadata:
  name: logging-loki
  namespace: openshift-logging
spec:
  size: 1x.small
  storage:
    schemas:
    - version: v12
      effectiveDate: '2022-06-01'
    secret:
      name: logging-loki-s3
      type: s3
  storageClassName: gp2
  tenants:
    mode: openshift-logging
```

---

## Cluster Updates

### Checking Available Updates

```bash
# Check current version
oc get clusterversion

# Check available updates
oc adm upgrade

# Get detailed version info
oc describe clusterversion version
```

**Example Output**:
```
Cluster ID:     abc123...
Channel:        stable-4.18
Desired Version: 4.18.2
Update Status:   Completed

Available Updates:
  VERSION     IMAGE
  4.18.3      quay.io/openshift-release-dev/ocp-release@sha256:abc...
  4.18.4      quay.io/openshift-release-dev/ocp-release@sha256:def...
```

### Upgrading the Cluster

**Start Upgrade**:
```bash
# Upgrade to specific version
oc adm upgrade --to=4.18.3

# Upgrade to latest available
oc adm upgrade --to-latest=true
```

**Monitor Upgrade Progress**:
```bash
# Watch cluster version
oc get clusterversion -w

# Check cluster operators
oc get clusteroperators

# View upgrade events
oc get events -n openshift-cluster-version
```

**Upgrade Flow**:
1. Control plane nodes updated first (one at a time)
2. Worker nodes updated (in batches, configurable)
3. Cluster operators updated
4. Post-upgrade validation

**Typical Upgrade Duration**:
- Small cluster (3 masters, 3 workers): 60-90 minutes
- Large cluster (100+ nodes): 2-4 hours

### Pausing Machine Config Updates

During upgrades, you can pause worker updates:

```bash
# Pause MachineConfigPool updates
oc patch mcp worker --type merge --patch '{"spec":{"paused":true}}'

# Resume updates
oc patch mcp worker --type merge --patch '{"spec":{"paused":false}}'
```

---

## Scaling the Cluster

### Adding Worker Nodes

**Using MachineSet (cloud providers)**:
```bash
# List machine sets
oc get machinesets -n openshift-machine-api

# Scale machine set
oc scale machineset <machineset-name> --replicas=5 -n openshift-machine-api
```

**Bare Metal / vSphere (Assisted Installer)**:
1. Boot new server from cluster ISO
2. Wait for host to register
3. Assign role: `oc adm node-role worker <node-name>`
4. Approve CSR: `oc get csr | grep Pending`
5. Approve: `oc adm certificate approve <csr-name>`

**Verify New Node**:
```bash
# Check nodes
oc get nodes

# Verify node is Ready
oc describe node <new-node-name>

# Check node labels
oc get node <new-node-name> --show-labels
```

### Removing Worker Nodes

**Graceful Node Removal**:
```bash
# 1. Drain node (evict pods)
oc adm drain <node-name> --ignore-daemonsets --delete-emptydir-data

# 2. Delete node from cluster
oc delete node <node-name>

# 3. Power off physical server or delete VM
```

**For MachineSet-managed nodes**:
```bash
# Scale down machine set
oc scale machineset <machineset-name> --replicas=3 -n openshift-machine-api
```

### Scaling Control Plane (Advanced)

⚠️ **Warning**: Scaling control plane requires careful planning

**Supported Configurations**:
- 3 control plane nodes (standard HA)
- 5 control plane nodes (for very large clusters, 250+ nodes)

**Not Recommended**:
- Scaling from 3 to 5 is complex
- Requires etcd re-balancing
- Consult Red Hat support before attempting

---

## Node Maintenance

### Cordoning and Draining Nodes

**Cordon** (prevent new pods from scheduling):
```bash
oc adm cordon <node-name>

# Uncordon (allow scheduling again)
oc adm uncordon <node-name>
```

**Drain** (evict all pods):
```bash
# Standard drain
oc adm drain <node-name> --ignore-daemonsets

# Force drain (delete pods that use emptyDir volumes)
oc adm drain <node-name> --ignore-daemonsets --delete-emptydir-data --force

# Drain with timeout
oc adm drain <node-name> --ignore-daemonsets --timeout=300s
```

**Use Cases**:
- OS patching on node
- Hardware maintenance
- Node replacement
- Troubleshooting node issues

### Node Replacement

**Worker Node Replacement**:
1. Drain node: `oc adm drain <old-node>`
2. Delete node: `oc delete node <old-node>`
3. Boot new server from cluster ISO
4. Assign role and approve CSR
5. Verify workloads migrated: `oc get pods -A -o wide`

**Control Plane Node Replacement** (Complex):
- Requires etcd backup before proceeding
- Follow Red Hat documentation precisely
- Consider engaging Red Hat support

---

## Resource Management

### Resource Quotas

**Create Namespace Quota**:
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: myapp
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
```

**Check Quota Usage**:
```bash
oc get resourcequota -n myapp
oc describe resourcequota compute-quota -n myapp
```

### LimitRanges

**Set Default Resource Limits**:
```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit-range
  namespace: myapp
spec:
  limits:
  - default:
      memory: 512Mi
      cpu: 500m
    defaultRequest:
      memory: 256Mi
      cpu: 250m
    type: Container
```

---

## Image Registry Management

### Internal Registry

**Access Internal Registry**:
```bash
# Expose registry route (if not exposed)
oc patch configs.imageregistry.operator.openshift.io/cluster --type merge -p '{"spec":{"defaultRoute":true}}'

# Get registry route
oc get route default-route -n openshift-image-registry

# Login to registry
podman login -u $(oc whoami) -p $(oc whoami -t) default-route-openshift-image-registry.apps.<cluster>.<domain>

# Push image
podman tag myapp:latest default-route-openshift-image-registry.apps.<cluster>.<domain>/myproject/myapp:latest
podman push default-route-openshift-image-registry.apps.<cluster>.<domain>/myproject/myapp:latest
```

### Image Pruning

**Prune Old Images**:
```bash
# Dry run (see what would be deleted)
oc adm prune images

# Actually prune
oc adm prune images --confirm

# Prune images older than 60 minutes
oc adm prune images --keep-younger-than=60m --confirm
```

**Automated Pruning**:
```yaml
apiVersion: imageregistry.operator.openshift.io/v1
kind: ImagePruner
metadata:
  name: cluster
spec:
  schedule: "0 0 * * *"  # Daily at midnight
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  keepTagRevisions: 3
  keepYoungerThan: 60m
  suspend: false
```

---

## etcd Maintenance

### etcd Health Check

```bash
# Check etcd pods
oc get pods -n openshift-etcd

# Check etcd member health
oc get etcd -o=jsonpath='{range .items[0].status.conditions[?(@.type=="EtcdMembersAvailable")]}{.message}{"\n"}{end}'

# Detailed etcd status
oc exec -n openshift-etcd etcd-<master-node> -- etcdctl endpoint health
```

### etcd Backup

**See**: [Backup and Restore](./backup-restore.md) for complete etcd backup procedures

---

## Cluster Health Checks

### Daily Health Check Routine

```bash
# 1. Check nodes
oc get nodes

# 2. Check cluster operators
oc get clusteroperators

# 3. Check critical namespaces
oc get pods -n openshift-etcd
oc get pods -n openshift-kube-apiserver
oc get pods -n openshift-kube-controller-manager
oc get pods -n openshift-kube-scheduler

# 4. Check for alerts
oc get alerts | grep -i firing

# 5. Check resource usage
oc adm top nodes

# 6. Check cluster version/updates
oc get clusterversion
```

### Automated Health Monitoring

**Create Health Check Script**:
```bash
#!/bin/bash
# health-check.sh

echo "=== Node Status ==="
oc get nodes

echo -e "\n=== Cluster Operators ==="
oc get co | grep -v "True.*False.*False"

echo -e "\n=== Firing Alerts ==="
oc get alerts 2>/dev/null | grep -i firing || echo "No firing alerts"

echo -e "\n=== Resource Usage ==="
oc adm top nodes

echo -e "\n=== etcd Health ==="
oc get pods -n openshift-etcd -o wide
```

**Schedule with CronJob**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cluster-health-check
  namespace: openshift-monitoring
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: health-check-sa
          containers:
          - name: health-check
            image: image-registry.openshift-image-registry.svc:5000/openshift/cli:latest
            command:
            - /bin/bash
            - /scripts/health-check.sh
          restartPolicy: OnFailure
```

---

## Operator Management

### Operator Lifecycle Manager (OLM)

**List Installed Operators**:
```bash
# All operators
oc get csv -A

# Operators in specific namespace
oc get csv -n openshift-operators

# Operator subscriptions
oc get subscriptions -A
```

**Update Operator**:
```bash
# Check for updates
oc get installplan -n <operator-namespace>

# Approve manual update
oc patch installplan <install-plan-name> -n <namespace> --type merge --patch '{"spec":{"approved":true}}'
```

**Uninstall Operator**:
```bash
# Delete subscription
oc delete subscription <subscription-name> -n <namespace>

# Delete CSV
oc delete csv <csv-name> -n <namespace>

# Clean up CRDs (if no longer needed)
oc get crd | grep <operator-domain>
oc delete crd <crd-name>
```

---

## Troubleshooting Common Day-2 Issues

### Issue: Monitoring Stack Unhealthy

```bash
# Check monitoring pods
oc get pods -n openshift-monitoring

# Restart Prometheus
oc delete pod prometheus-k8s-0 -n openshift-monitoring

# Check PVCs
oc get pvc -n openshift-monitoring
```

### Issue: Node Not Ready After Reboot

```bash
# Check node conditions
oc describe node <node-name> | grep Conditions -A 10

# Check kubelet logs
oc debug node/<node-name>
# Inside debug pod:
chroot /host
journalctl -u kubelet
```

### Issue: etcd Degraded

```bash
# Check etcd pods
oc get pods -n openshift-etcd

# Check etcd logs
oc logs <etcd-pod> -n openshift-etcd

# Force etcd redeployment
oc patch etcd cluster -p='{"spec": {"forceRedeploymentReason": "recovery-'"$( date --rfc-3339=ns )"'"}}' --type=merge
```

---

## Best Practices

**Monitoring**:
- ✅ Review alerts daily
- ✅ Set up alert routing to appropriate teams
- ✅ Create custom alerts for application metrics
- ✅ Retain metrics for at least 15 days

**Updates**:
- ✅ Test updates in dev/staging first
- ✅ Schedule updates during maintenance windows
- ✅ Backup etcd before major updates
- ✅ Stay within 2 minor versions of latest release

**Scaling**:
- ✅ Monitor resource usage trends
- ✅ Plan capacity 20-30% ahead of demand
- ✅ Scale workers, not control plane (unless necessary)
- ✅ Use machine sets for cloud deployments

**Maintenance**:
- ✅ Drain nodes before maintenance
- ✅ Perform health checks after changes
- ✅ Document all cluster modifications
- ✅ Maintain etcd backups

---

## References

- [OpenShift Post-Installation Configuration](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/post-installation_configuration/)
- [OpenShift Monitoring](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/monitoring/)
- [OpenShift Logging](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/logging/)
- [Updating Clusters](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/updating_clusters/)
- [Backup and Restore](./backup-restore.md)
- [Quick Reference](./quick-reference.md)
- [INDEX](./INDEX.md)

---

**Last Updated**: 2026-03-17
**OpenShift Version**: 4.18

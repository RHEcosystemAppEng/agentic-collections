# Backup and Restore

etcd backup and restore procedures for OpenShift disaster recovery.

---

## Overview

etcd is the key-value store for all Kubernetes cluster data. Regular backups are **critical** for disaster recovery. This guide covers etcd backup and restore procedures only.

⚠️ **Application data backups** (persistent volumes, databases) require separate backup solutions (Velero/OADP, application-specific tools).

---

## etcd Backup

### Why Backup etcd

**etcd contains**:
- All Kubernetes resources (pods, services, deployments, etc.)
- Cluster configuration
- Secrets and ConfigMaps
- RBAC policies
- Custom Resource Definitions (CRDs)

**Loss of etcd = complete cluster loss**

### Backup Frequency

**Recommended**:
- **Before cluster upgrades**: Always
- **Scheduled backups**: Daily minimum, hourly for production
- **Before major changes**: Node replacement, operator installation
- **Ad-hoc**: Before risky operations

---

## Creating etcd Backup

### Backup Procedure

**1. SSH to Control Plane Node**:
```bash
# List control plane nodes
oc get nodes -l node-role.kubernetes.io/master

# Start debug pod on control plane node
oc debug node/<master-node-name>
```

**2. Inside Debug Pod**:
```bash
# Change root to host filesystem
chroot /host

# Run backup script
/usr/local/bin/cluster-backup.sh /home/core/backup

# Example output:
# etcd snapshot saved at /home/core/backup/snapshot_2024-03-17_105030.db
# etcd static resources saved at /home/core/backup/static_kuberesources_2024-03-17_105030.tar.gz
```

**3. Verify Backup**:
```bash
# List backup files
ls -lh /home/core/backup/

# Expected files:
# snapshot_<timestamp>.db          - etcd data snapshot
# static_kuberesources_<timestamp>.tar.gz - static pod manifests
```

**4. Copy Backup to Safe Location**:
```bash
# Exit debug pod first (Ctrl+D or exit)

# Copy from node to local machine
oc debug node/<master-node-name> -- \
  chroot /host cat /home/core/backup/snapshot_<timestamp>.db > ./snapshot.db

oc debug node/<master-node-name> -- \
  chroot /host cat /home/core/backup/static_kuberesources_<timestamp>.tar.gz > ./static_kuberesources.tar.gz
```

**5. Store Securely**:
```bash
# Example: Copy to remote backup server
scp snapshot_*.db static_kuberesources_*.tar.gz backup-server:/backups/openshift/<cluster-name>/

# Or encrypted cloud storage
gpg --encrypt snapshot_<timestamp>.db
aws s3 cp snapshot_<timestamp>.db.gpg s3://backups/openshift/<cluster-name>/
```

---

## Automated Backup Script

**Create CronJob** (runs on control plane nodes):

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: etcd-backup
  namespace: openshift-config
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          nodeSelector:
            node-role.kubernetes.io/master: ""
          tolerations:
          - operator: Exists
          hostNetwork: true
          containers:
          - name: etcd-backup
            image: quay.io/openshift-release-dev/ocp-v4.0-art-dev@sha256:...
            command:
            - /bin/sh
            - -c
            - |
              #!/bin/sh
              /usr/local/bin/cluster-backup.sh /home/core/backup
              # Optional: Copy to remote location
              # scp /home/core/backup/* backup-server:/path/
            securityContext:
              privileged: true
            volumeMounts:
            - name: host
              mountPath: /host
          volumes:
          - name: host
            hostPath:
              path: /
          restartPolicy: Never
```

---

## etcd Restore

⚠️ **WARNING**: etcd restore is a **destructive operation**. Only perform in disaster recovery scenarios.

### When to Restore

**Restore etcd when**:
- Complete cluster failure with etcd data loss
- Cluster state corrupted beyond repair
- Need to rollback to known good state after failed upgrade

**Do NOT restore for**:
- Deleted namespace or resources (recover from individual backups)
- Single failed node (replace node instead)
- Cluster operator issues (troubleshoot first)

### Restore Prerequisites

**Required**:
- etcd backup files (`snapshot_<timestamp>.db`, `static_kuberesources_<timestamp>.tar.gz`)
- SSH access to all control plane nodes
- Cluster must be stopped (all control plane nodes)
- Physical or console access to nodes (in case of issues)

**Backup current state** before restore (if possible):
```bash
/usr/local/bin/cluster-backup.sh /home/core/backup-before-restore
```

---

## Restore Procedure

### Single Control Plane Cluster (SNO or Degraded)

⚠️ **For SNO or when only one control plane node survives**

**1. Copy Backup to Control Plane Node**:
```bash
scp snapshot_<timestamp>.db core@<master-node-ip>:/home/core/
scp static_kuberesources_<timestamp>.tar.gz core@<master-node-ip>:/home/core/
```

**2. SSH to Control Plane Node**:
```bash
ssh core@<master-node-ip>
```

**3. Stop kubelet and Containers**:
```bash
sudo systemctl stop kubelet
sudo crictl ps -q | xargs -r sudo crictl stop
```

**4. Restore etcd Snapshot**:
```bash
# Run restore script
sudo -E /usr/local/bin/cluster-restore.sh /home/core /home/core/snapshot_<timestamp>.db
```

**5. Restore Static Pod Manifests**:
```bash
# Extract static resources
sudo tar -xzf /home/core/static_kuberesources_<timestamp>.tar.gz \
  -C /etc/kubernetes/
```

**6. Reboot Node**:
```bash
sudo systemctl reboot
```

**7. Verify Cluster Recovery**:
```bash
# After reboot, check cluster status
export KUBECONFIG=/etc/kubernetes/static-pod-resources/kube-apiserver-certs/secrets/node-kubeconfigs/localhost.kubeconfig

oc get nodes
oc get clusteroperators
oc get pods -A
```

---

### Multi-Control Plane Cluster (HA Restore)

⚠️ **For 3+ control plane nodes**

**1. Identify Recovery Control Plane Node**:
- Choose one healthy control plane node to restore from
- Other control plane nodes will be rebuilt

**2. Restore on Recovery Node** (follow Single Control Plane steps 1-6)

**3. Force New Cluster (Remove Other etcd Members)**:
```bash
# On recovery node, remove other etcd members
sudo -E /usr/local/bin/etcd-force-new-cluster.sh
```

**4. Rebuild Other Control Plane Nodes**:

For each remaining control plane node:
```bash
# SSH to node
ssh core@<other-master-node>

# Delete old etcd data
sudo rm -rf /var/lib/etcd/member

# Reboot node
sudo systemctl reboot
```

**5. Re-approve CSRs**:
```bash
# Watch for pending CSRs from rejoining nodes
oc get csr -w

# Approve CSRs
oc get csr -o name | xargs oc adm certificate approve
```

**6. Wait for etcd Quorum**:
```bash
# Check etcd member status
oc get etcd -o=jsonpath='{range .items[0].status.conditions[?(@.type=="EtcdMembersAvailable")]}{.message}{"\n"}{end}'

# Should show 3 members (or configured count)
```

**7. Verify Cluster Health**:
```bash
oc get nodes
oc get clusteroperators
oc get pods -n openshift-etcd
```

---

## Troubleshooting Restore

### Issue: Restore Script Fails

**Check**:
```bash
# Verify backup file integrity
ls -lh /home/core/snapshot_<timestamp>.db

# Check etcd logs
sudo journalctl -u etcd-member
```

**Resolution**: Ensure backup file is not corrupted, try different backup

### Issue: Cluster Operators Degraded After Restore

**Wait for automatic recovery**:
```bash
# Monitor operator status
oc get clusteroperators -w
```

**Force redeploy if stuck** (example: kube-apiserver):
```bash
oc patch kubeapiserver cluster --type=merge \
  -p '{"spec":{"forceRedeploymentReason":"restore-recovery-'"$(date +%s)"'"}}'
```

### Issue: etcd Pods Not Starting

**Check**:
```bash
oc get pods -n openshift-etcd
oc logs <etcd-pod> -n openshift-etcd
```

**Resolution**: Verify file permissions, check etcd member list, force re-deployment

---

## Backup Retention

**Recommended Retention**:
- **Hourly backups**: Keep 24 (1 day)
- **Daily backups**: Keep 30 (1 month)
- **Weekly backups**: Keep 12 (3 months)
- **Monthly backups**: Keep 12 (1 year)

**Cleanup Script**:
```bash
#!/bin/bash
# cleanup-old-backups.sh
BACKUP_DIR="/backups/openshift/<cluster-name>"
find $BACKUP_DIR -name "snapshot_*.db" -mtime +30 -delete
find $BACKUP_DIR -name "static_kuberesources_*.tar.gz" -mtime +30 -delete
```

---

## Best Practices

**Backup**:
- ✅ Automate backups (CronJob or external tool)
- ✅ Store backups off-cluster (remote server, cloud storage)
- ✅ Encrypt backups (especially if stored off-site)
- ✅ Test restore procedure quarterly
- ✅ Backup before all major changes

**Restore**:
- ✅ Practice restore in test environment first
- ✅ Document restore procedure for your environment
- ✅ Have console/physical access to nodes during restore
- ✅ Backup current state before restore (if possible)
- ✅ Engage Red Hat support for production restores

**Security**:
- ✅ Treat backups as sensitive data (contains secrets)
- ✅ Encrypt backups at rest
- ✅ Restrict access to backup storage
- ✅ Audit backup access logs

---

## References

- [OpenShift Backup and Restore](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/backup_and_restore/)
- [Backing up etcd](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/backup_and_restore/control-plane-backup-and-restore#backup-etcd)
- [Restoring etcd](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/backup_and_restore/control-plane-backup-and-restore#dr-restoring-cluster-state)
- [Day-2 Operations](./day-2-operations.md)
- [Quick Reference](./quick-reference.md)
- [INDEX](./INDEX.md)

---

**Last Updated**: 2026-03-17
**OpenShift Version**: 4.18

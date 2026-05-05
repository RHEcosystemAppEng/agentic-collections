---
title: etcd Maintenance and Defragmentation
category: operations
sources:
  - title: etcd maintenance - Backup and restore
    url: https://docs.openshift.com/container-platform/latest/backup_and_restore/control_plane_backup_and_restore/backing-up-etcd.html
    date_accessed: 2026-05-05
  - title: etcd defragmentation
    url: https://etcd.io/docs/v3.5/op-guide/maintenance/#defragmentation
    date_accessed: 2026-05-05
  - title: Kubernaut Demo Scenarios - etcd defrag golden transcript
    url: https://github.com/jordigilh/kubernaut-demo-scenarios/blob/feature/v1.4-new-scenarios/golden-transcripts/etcd-defrag-forecast-etcdhighfragmentationratio.json
    date_accessed: 2026-05-05
tags: [etcd, defragmentation, maintenance, monitoring, performance]
semantic_keywords: [etcd defrag, etcd fragmentation, etcd maintenance, etcd monitoring, etcd compaction, etcd disk usage, mvcc database size]
use_cases: [cluster-maintenance, etcd-health, proactive-operations, capacity-planning]
related_docs: [day-2-operations.md, backup-restore.md, troubleshooting.md]
last_updated: 2026-05-05
---

# etcd Maintenance and Defragmentation

Monitoring, diagnosing, and resolving etcd fragmentation on OpenShift clusters.

---

## Overview

etcd stores all Kubernetes cluster state. Over time, compaction frees logical space but does not reclaim physical disk pages, causing the backend B-tree to grow. Without periodic defragmentation, etcd DB files can be orders of magnitude larger than live data, leading to increased memory usage, slower I/O, and eventually OOM kills or quota exhaustion.

---

## Key Metrics

### Fragmentation Ratio

```
etcd_mvcc_db_total_size_in_bytes / etcd_mvcc_db_total_size_in_use_in_bytes
```

| Ratio | Status | Action |
|-------|--------|--------|
| < 2.0 | Healthy | No action needed |
| 2.0 - 4.0 | Moderate | Schedule defrag during maintenance window |
| > 4.0 | High | Defrag required — risk of quota exhaustion |

### Monitoring Queries

**Current fragmentation ratio per member**:
```promql
etcd_mvcc_db_total_size_in_bytes{job="etcd"}
  / etcd_mvcc_db_total_size_in_use_in_bytes{job="etcd"}
```

**Physical DB size approaching quota**:
```promql
etcd_mvcc_db_total_size_in_bytes{job="etcd"}
  / etcd_server_quota_backend_bytes{job="etcd"} > 0.8
```

**Predict when DB will hit quota** (linear extrapolation over 6 hours):
```promql
predict_linear(etcd_mvcc_db_total_size_in_bytes{job="etcd"}[6h], 3600 * 24)
  > etcd_server_quota_backend_bytes{job="etcd"}
```

### Health Indicators

Check these alongside fragmentation:

```promql
# Leader presence (must be 1 on exactly one member)
etcd_server_has_leader{job="etcd"}

# Peer round-trip time (should be < 100ms)
histogram_quantile(0.99,
  rate(etcd_network_peer_round_trip_time_seconds_bucket{job="etcd"}[5m]))

# Disk sync duration (should be < 100ms)
histogram_quantile(0.99,
  rate(etcd_disk_wal_fsync_duration_seconds_bucket{job="etcd"}[5m]))
```

---

## Defragmentation Procedure

### Prerequisites

1. Cluster is healthy — all etcd members have a leader
2. etcd backup is current (within the last hour)
3. Maintenance window approved — defrag causes brief per-member unavailability

### Step 1: Take a Fresh Backup

```bash
# On a control-plane node
sudo /usr/local/bin/cluster-backup.sh /home/core/etcd-backup-$(date +%Y%m%d)
```

Or via OpenShift API:
```bash
oc debug node/<control-plane-node> -- chroot /host \
  /usr/local/bin/cluster-backup.sh /home/core/etcd-backup-pre-defrag
```

### Step 2: Identify Members and Current Sizes

```bash
# List etcd members
oc get pods -n openshift-etcd -l app=etcd -o wide

# Check DB sizes per member
for pod in $(oc get pods -n openshift-etcd -l app=etcd -o name); do
  echo "=== $pod ==="
  oc exec -n openshift-etcd $pod -c etcd -- \
    etcdctl endpoint status --write-out=table
done
```

### Step 3: Rolling Defragmentation

Defragment one member at a time. Always start with non-leader members.

```bash
# Identify the leader
oc exec -n openshift-etcd etcd-<control-plane-0> -c etcd -- \
  etcdctl endpoint status --write-out=table

# Defrag a non-leader member
oc exec -n openshift-etcd etcd-<control-plane-1> -c etcd -- \
  etcdctl defrag

# Verify the member rejoined and is healthy
oc exec -n openshift-etcd etcd-<control-plane-1> -c etcd -- \
  etcdctl endpoint health

# Repeat for remaining non-leader members, then the leader last
```

**Wait at least 30 seconds between members** to allow the cluster to stabilize.

### Step 4: Verify Results

```bash
# Compare DB sizes before and after
for pod in $(oc get pods -n openshift-etcd -l app=etcd -o name); do
  echo "=== $pod ==="
  oc exec -n openshift-etcd $pod -c etcd -- \
    etcdctl endpoint status --write-out=table
done
```

Expected: `DB SIZE` should drop significantly, and `DB SIZE IN USE` should be close to `DB SIZE`.

---

## Common Issues

### Defrag Fails with "context deadline exceeded"

The default timeout may be too short for large databases.

```bash
oc exec -n openshift-etcd etcd-<member> -c etcd -- \
  etcdctl defrag --command-timeout=120s
```

### Member OOMKilled During Defrag

Defragmentation temporarily doubles memory usage. If etcd memory limits are tight:
1. Verify current memory limits: `oc get pod etcd-<member> -n openshift-etcd -o jsonpath='{.spec.containers[?(@.name=="etcd")].resources}'`
2. If limits are below 1Gi with a large DB, consider requesting a maintenance window with increased limits

### Fragmentation Returns Quickly After Defrag

Indicates a write-heavy workload pattern. Investigate:
```bash
# Check write rate
oc exec -n openshift-etcd etcd-<member> -c etcd -- \
  etcdctl endpoint status --write-out=json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for ep in data:
  print(f'{ep[\"Endpoint\"]}: revision={ep[\"Status\"][\"header\"][\"revision\"]}')"
```

Common causes:
- Frequent ConfigMap/Secret updates (operators with aggressive reconciliation)
- Lease churn from many short-lived pods
- Custom controllers writing large values

### Auto-Compaction Did Not Prevent Fragmentation

Auto-compaction (`--auto-compaction-retention`) frees **logical** space but does **not** reclaim **physical** disk pages. Compaction is necessary (it marks old revisions for reuse) but defragmentation is the only way to shrink the actual DB file.

---

## PrometheusRule Example

Alert when fragmentation ratio exceeds 4x for 30 minutes:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: etcd-fragmentation
  namespace: openshift-etcd
spec:
  groups:
    - name: etcd-maintenance
      rules:
        - alert: EtcdHighFragmentationRatio
          expr: |
            (etcd_mvcc_db_total_size_in_bytes{job="etcd"}
             / etcd_mvcc_db_total_size_in_use_in_bytes{job="etcd"}) > 4
          for: 30m
          labels:
            severity: warning
          annotations:
            summary: "etcd member {{ $labels.pod }} fragmentation ratio is {{ $value | humanize }}x"
            description: >
              The etcd backend database on {{ $labels.pod }} has a fragmentation
              ratio above 4x, indicating significant wasted disk space from
              compacted but unreclaimed revisions. Schedule defragmentation
              during the next maintenance window.
```

---

## Metric Discovery Protocol

When investigating etcd health with Prometheus tools:

1. **Discover available metrics**: Filter with `{__name__=~"etcd_.*"}` to find all etcd-related metrics
2. **Check metric type**: Use metadata to confirm whether a metric is a gauge (current value) or counter (use `rate()`)
3. **Scope queries**: Add `{job="etcd"}` to target platform etcd, not user-workload exporters
4. **Limit cardinality**: Use `topk(10, ...)` when exploring unknown label sets

---

## References

- [OpenShift etcd backup and restore](https://docs.openshift.com/container-platform/latest/backup_and_restore/control_plane_backup_and_restore/backing-up-etcd.html)
- [etcd maintenance guide](https://etcd.io/docs/v3.5/op-guide/maintenance/)
- [etcd performance benchmarking](https://etcd.io/docs/v3.5/op-guide/performance/)

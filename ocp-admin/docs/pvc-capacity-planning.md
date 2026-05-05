---
title: PVC Capacity Planning
category: operations
sources:
  - title: Expanding persistent volumes
    url: https://docs.openshift.com/container-platform/latest/storage/expanding-persistent-volumes.html
    date_accessed: 2026-05-05
  - title: Prometheus predict_linear
    url: https://prometheus.io/docs/prometheus/latest/querying/functions/#predict_linear
    date_accessed: 2026-05-05
  - title: Kubernaut Demo Scenarios - PVC capacity forecast golden transcript
    url: https://github.com/jordigilh/kubernaut-demo-scenarios/blob/feature/v1.4-new-scenarios/golden-transcripts/pvc-capacity-forecast-pvrunwayshort.json
    date_accessed: 2026-05-05
tags: [pvc, capacity-planning, storage, monitoring, predict-linear, volume-expansion]
semantic_keywords: [pvc capacity, persistent volume expansion, storage forecast, predict_linear, volume full, disk space, storage class, allowVolumeExpansion]
use_cases: [capacity-planning, proactive-operations, storage-management]
related_docs: [storage.md, day-2-operations.md, troubleshooting.md]
last_updated: 2026-05-05
---

# PVC Capacity Planning

Proactive monitoring and expansion of PersistentVolumeClaims before they fill up.

---

## Overview

PVCs that reach capacity cause application failures — databases crash, logs stop writing, and pods enter CrashLoopBackOff. Proactive capacity planning uses Prometheus `predict_linear()` to forecast when a PVC will fill up, giving operators time to expand the volume before impact.

---

## Key Metrics

### Volume Usage

```promql
# Current used bytes per PVC
kubelet_volume_stats_used_bytes{namespace="<ns>"}

# Total capacity per PVC
kubelet_volume_stats_capacity_bytes{namespace="<ns>"}

# Current usage percentage
kubelet_volume_stats_used_bytes{namespace="<ns>"}
  / kubelet_volume_stats_capacity_bytes{namespace="<ns>"} * 100
```

### Forecasting with predict_linear

**Predict usage in 24 hours** (based on 6-hour trend):
```promql
predict_linear(
  kubelet_volume_stats_used_bytes{namespace="<ns>"}[6h],
  3600 * 24
)
```

**PVCs that will exceed 90% in 24 hours**:
```promql
predict_linear(kubelet_volume_stats_used_bytes[6h], 3600 * 24)
  / kubelet_volume_stats_capacity_bytes > 0.9
```

**Estimated hours until full** (runway calculation):
```promql
(kubelet_volume_stats_capacity_bytes - kubelet_volume_stats_used_bytes)
  / deriv(kubelet_volume_stats_used_bytes[6h])
  / 3600
```

### Available Inodes

Inode exhaustion causes "No space left on device" even when disk bytes are available:
```promql
kubelet_volume_stats_inodes_free{namespace="<ns>"}
  / kubelet_volume_stats_inodes{namespace="<ns>"} * 100 < 10
```

---

## Volume Expansion

### Prerequisites

1. **StorageClass must support expansion**: `allowVolumeExpansion: true`
2. **CSI driver must support expansion**: Most modern CSI drivers do (topolvm, csi-cinder, ebs-csi, etc.)
3. **No active snapshot or clone operations** on the PVC

Check StorageClass support:
```bash
oc get storageclass -o custom-columns=\
NAME:.metadata.name,\
PROVISIONER:.provisioner,\
EXPAND:.allowVolumeExpansion
```

### Online Expansion (No Downtime)

Most CSI drivers support online expansion — the volume grows while mounted:

```bash
# Check current PVC size
oc get pvc <pvc-name> -n <namespace> \
  -o jsonpath='{.spec.resources.requests.storage}'

# Expand the PVC
oc patch pvc <pvc-name> -n <namespace> --type merge \
  -p '{"spec":{"resources":{"requests":{"storage":"<new-size>"}}}}'

# Monitor expansion progress
oc get pvc <pvc-name> -n <namespace> -o jsonpath='{.status.conditions[*].type}'
```

The PVC will show a `FileSystemResizePending` condition, then transition to the new size after the kubelet resizes the filesystem.

### Expansion Workflow

```
1. Verify StorageClass allows expansion
2. Check current usage vs capacity
3. Calculate target size (current + growth buffer)
4. Patch PVC with new size
5. Monitor FileSystemResizePending → completion
6. Verify new capacity in kubelet metrics
```

---

## PrometheusRule Example

Alert when a PVC is forecast to fill within 24 hours:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: pvc-capacity-forecast
  namespace: openshift-monitoring
spec:
  groups:
    - name: pvc-capacity
      rules:
        - alert: PVRunwayShort
          expr: |
            predict_linear(kubelet_volume_stats_used_bytes[6h], 3600 * 24)
              > kubelet_volume_stats_capacity_bytes
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "PVC {{ $labels.persistentvolumeclaim }} in {{ $labels.namespace }} predicted full within 24h"
            description: >
              Based on the write rate over the last 6 hours, PVC
              {{ $labels.persistentvolumeclaim }} in namespace
              {{ $labels.namespace }} is predicted to exceed capacity
              within 24 hours.
```

---

## Common Issues

### StorageClass Does Not Allow Expansion

```
error: persistentvolumeclaims "<name>" could not be patched: admission webhook
"validate.storage.k8s.io" denied: ...allowVolumeExpansion is not enabled
```

Options:
1. Migrate to a StorageClass that supports expansion
2. Create a new, larger PVC and migrate data

### Expansion Stuck at FileSystemResizePending

The kubelet must resize the filesystem, which requires the volume to be mounted. If the pod is not running:

```bash
# Check if a pod is using the PVC
oc get pods -n <namespace> -o json | python3 -c "
import json, sys
pods = json.load(sys.stdin)
for p in pods['items']:
  for v in p['spec'].get('volumes', []):
    pvc = v.get('persistentVolumeClaim', {}).get('claimName')
    if pvc:
      print(f'{p[\"metadata\"][\"name\"]}: {pvc} ({p[\"status\"][\"phase\"]})')
"

# If no pod is running, start a temporary pod to trigger resize
oc run resize-trigger --image=busybox --restart=Never \
  --overrides='{"spec":{"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"<pvc-name>"}}],"containers":[{"name":"resize-trigger","image":"busybox","command":["sleep","30"],"volumeMounts":[{"name":"data","mountPath":"/data"}]}]}}' \
  -n <namespace>
```

### predict_linear Returns Negative Values

A negative prediction means the volume is **shrinking** (data is being deleted faster than written). This is normal for workloads with retention policies. No action needed.

### Metrics Not Available for a PVC

`kubelet_volume_stats_*` metrics are only emitted for **mounted** PVCs. Unbound or unused PVCs will not appear:

```bash
# Check PVC status
oc get pvc -n <namespace> -o custom-columns=\
NAME:.metadata.name,\
STATUS:.status.phase,\
CAPACITY:.status.capacity.storage,\
STORAGECLASS:.spec.storageClassName
```

---

## Metric Discovery Protocol

When investigating PVC capacity with Prometheus tools:

1. **Discover volume metrics**: Filter with `{__name__=~"kubelet_volume_stats.*", namespace="<target>"}` to find available PVC metrics
2. **Check label sets**: Use `kubelet_volume_stats_used_bytes{namespace="<ns>"}` to discover `persistentvolumeclaim` label values
3. **Scope to specific PVC**: Add `{persistentvolumeclaim="<name>"}` for targeted queries
4. **Use `topk()`**: When scanning across namespaces, `topk(10, kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes)` finds the fullest PVCs

---

## References

- [OpenShift expanding persistent volumes](https://docs.openshift.com/container-platform/latest/storage/expanding-persistent-volumes.html)
- [Prometheus predict_linear function](https://prometheus.io/docs/prometheus/latest/querying/functions/#predict_linear)
- [Kubernetes volume health monitoring](https://kubernetes.io/docs/concepts/storage/volume-health-monitoring/)

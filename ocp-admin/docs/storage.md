# OpenShift Storage Configuration

Comprehensive guide to storage options and configuration for OpenShift clusters.

---

## Overview

OpenShift supports multiple storage backends via Container Storage Interface (CSI) drivers. Storage choices depend on infrastructure provider, performance requirements, and workload characteristics.

---

## Storage Types

### Ephemeral Storage
**Lifecycle**: Tied to pod lifecycle
**Use Cases**: Temporary files, caches, scratch space
**Backend**: Node local disk

**Characteristics**:
- Deleted when pod terminates
- Fast (local disk)
- No data persistence

### Persistent Storage
**Lifecycle**: Independent of pod lifecycle
**Use Cases**: Databases, file storage, stateful applications
**Backend**: Network storage, cloud volumes, local persistent volumes

**Characteristics**:
- Survives pod restarts/rescheduling
- Can be shared across pods (ReadWriteMany)
- Backed by physical storage

---

## Storage by Infrastructure Provider

### Bare Metal

**Options**:

1. **Local Storage** (hostPath, local volumes)
   - Direct node disk access
   - Highest performance
   - No redundancy (tied to specific node)
   - Not portable across nodes

2. **NFS (Network File System)**
   - Shared file storage
   - ReadWriteMany support
   - Moderate performance
   - External NFS server required

3. **iSCSI**
   - Block storage over network
   - Good performance
   - iSCSI target required
   - Typically ReadWriteOnce

4. **OpenShift Data Foundation (ODF)**
   - Software-defined storage
   - Built on Ceph
   - Provides block, file, object storage
   - Requires 3+ worker nodes with dedicated disks
   - **Recommended for production bare metal**

**Recommendation**: OpenShift Data Foundation (ODF) for production

---

### VMware vSphere

**Options**:

1. **vSphere CSI Driver** ✅ **Recommended**
   - Dynamic volume provisioning
   - Uses vSphere datastores
   - Thin or thick provisioning
   - Snapshot support
   - vMotion compatible

2. **vSphere Cloud Provider (Deprecated)**
   - Older in-tree volume plugin
   - Migrate to CSI driver

**Configuration**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: vsphere-sc
provisioner: csi.vsphere.vmware.com
parameters:
  datastoreurl: "ds:///vmfs/volumes/<datastore-url>/"
  storagepolicyname: "vSAN Default Storage Policy"
volumeBindingMode: WaitForFirstConsumer
```

**Requirements**:
- vSphere 7.0+ (recommended 8.0+)
- vCenter credentials configured
- Datastore with sufficient space

**Recommendation**: vSphere CSI driver (default for vSphere clusters)

---

### Oracle Cloud Infrastructure (OCI)

**Options**:

1. **OCI Block Volume CSI Driver** ✅ **Recommended**
   - Dynamic block volume provisioning
   - High performance (VPU-based)
   - Snapshot and clone support
   - Encryption at rest

2. **OCI File Storage (NFS)**
   - Managed NFS service
   - ReadWriteMany support
   - Good for shared file workloads

**Configuration**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: oci-bv
provisioner: blockvolume.csi.oraclecloud.com
parameters:
  vpusPerGB: "10"  # Performance units (10, 20, 30, 40, etc.)
volumeBindingMode: WaitForFirstConsumer
```

**Recommendation**: OCI Block Volume CSI for most workloads, OCI File Storage for shared files

---

### Nutanix AHV

**Options**:

1. **Nutanix CSI Driver** ✅ **Recommended**
   - Dynamic volume provisioning
   - Uses Nutanix Volumes
   - Thin provisioning
   - Snapshot support
   - Flash mode for performance

**Configuration**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nutanix-volume
provisioner: csi.nutanix.com
parameters:
  storageContainer: "default-container"
  csi.storage.k8s.io/fstype: "ext4"
  flashMode: "DISABLED"  # or "ENABLED" for SSD
volumeBindingMode: WaitForFirstConsumer
```

**Requirements**:
- Nutanix AOS 6.5+
- Prism Central access
- Storage container configured

**Recommendation**: Nutanix CSI driver (default for Nutanix clusters)

---

### Cloud Providers (AWS, Azure, GCP)

**AWS**:
- EBS CSI Driver (elastic block storage)
- EFS CSI Driver (elastic file system, ReadWriteMany)

**Azure**:
- Azure Disk CSI Driver
- Azure File CSI Driver (ReadWriteMany)

**GCP**:
- GCE Persistent Disk CSI Driver
- Filestore CSI Driver (ReadWriteMany)

**Note**: These are available via IPI installations, not currently in Assisted Installer

---

## Storage Classes

### What is a StorageClass?

A StorageClass defines how storage is dynamically provisioned.

**Key Fields**:
- `provisioner`: CSI driver name
- `parameters`: Provider-specific options
- `reclaimPolicy`: Retain or Delete (what happens when PVC deleted)
- `volumeBindingMode`: Immediate or WaitForFirstConsumer

**Example**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: csi.example.com
parameters:
  type: ssd
  replication: "3"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

### Default StorageClass

**Purpose**: Used when PVC doesn't specify `storageClassName`

**Setting Default**:
```bash
# Mark a storage class as default
oc patch storageclass <storage-class-name> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Remove default annotation from current default
oc patch storageclass <old-default> -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

**List Storage Classes**:
```bash
oc get storageclass

# Output shows (default) next to default class
NAME            PROVISIONER           RECLAIMPOLICY   VOLUMEBINDINGMODE
fast-ssd        csi.example.com       Delete          WaitForFirstConsumer
standard (default)  csi.example.com   Delete          Immediate
```

---

## Persistent Volumes and Claims

### Persistent Volume (PV)
**Definition**: Actual storage resource in the cluster

**Lifecycle**: Independent of any pod
**Provisioning**: Static (admin-created) or Dynamic (via StorageClass)

**Example (Static)**:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs-01
spec:
  capacity:
    storage: 10Gi
  accessModes:
  - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  nfs:
    server: 192.168.1.100
    path: /exports/volume1
```

### Persistent Volume Claim (PVC)
**Definition**: User request for storage

**Binding**: Kubernetes matches PVC to available PV (or provisions via StorageClass)

**Example**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: fast-ssd
```

**Using in Pod**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: database
spec:
  containers:
  - name: postgres
    image: postgres:13
    volumeMounts:
    - name: data
      mountPath: /var/lib/postgresql/data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: database-pvc
```

---

## Access Modes

### ReadWriteOnce (RWO)
**Description**: Volume can be mounted read-write by a single node

**Use Cases**:
- Databases (PostgreSQL, MySQL)
- Single-replica applications
- Block storage

**Supported By**: Most storage backends

### ReadOnlyMany (ROX)
**Description**: Volume can be mounted read-only by multiple nodes

**Use Cases**:
- Shared configuration
- Static content distribution

**Supported By**: NFS, some cloud file systems

### ReadWriteMany (RWX)
**Description**: Volume can be mounted read-write by multiple nodes

**Use Cases**:
- Shared file storage
- Multi-replica applications needing shared data
- Log aggregation

**Supported By**:
- NFS
- ODF (OpenShift Data Foundation)
- Cloud file systems (EFS, Azure Files, Filestore)

**Not Supported By**:
- Block storage (EBS, Azure Disk, vSphere)
- Local storage

---

## OpenShift Data Foundation (ODF)

**What is ODF?**
- Software-defined storage for OpenShift
- Based on Ceph (distributed storage)
- Provides block, file, and object storage
- Runs as pods on OpenShift worker nodes

**Requirements**:
- 3+ worker nodes (for high availability)
- Dedicated raw disks on each node (no partitions, no filesystems)
- Minimum 4 CPU, 16 GB RAM per node (for ODF pods)
- 10 Gbps network recommended

**Storage Classes Provided**:
- `ocs-storagecluster-ceph-rbd` - Block storage (RWO)
- `ocs-storagecluster-cephfs` - File storage (RWX)
- `ocs-storagecluster-ceph-rgw` - Object storage (S3-compatible)

**Installation** (after cluster deployment):
```bash
# Install ODF operator from OperatorHub
oc create -f - <<EOF
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

# Create storage cluster (requires nodes with raw disks)
# Follow ODF documentation for cluster creation
```

**Advantages**:
- No external storage dependency
- Block, file, and object storage
- Snapshot and clone support
- Encryption at rest
- Multi-tenancy

**Considerations**:
- Requires dedicated resources (CPU, RAM, disks)
- Complexity in management
- Minimum 3 nodes for HA

---

## Volume Snapshots

**Purpose**: Point-in-time copy of a volume

**Requirements**:
- CSI driver with snapshot support
- VolumeSnapshotClass configured

**Creating Snapshot**:
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: db-snapshot-1
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: database-pvc
```

**Restoring from Snapshot**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-pvc-restored
spec:
  dataSource:
    name: db-snapshot-1
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

**Use Cases**:
- Backup before upgrades
- Testing with production data
- Disaster recovery

---

## Local Persistent Volumes

**Use Cases**:
- Databases requiring maximum IOPS
- High-performance workloads
- Nodes with fast local SSDs

**Characteristics**:
- Tied to specific node
- No portability (pod must run on same node)
- Highest performance

**Example**:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv-node1
spec:
  capacity:
    storage: 100Gi
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - node1.example.com
```

**⚠️ Warning**: Pod cannot be rescheduled to different node if node fails

---

## Storage Performance Tuning

### Block Storage (RWO)
**Best For**: Databases, single-replica apps

**Tuning**:
- Use SSD-backed storage
- Increase IOPS (cloud: VPU/IOPS settings)
- Filesystem: ext4 or xfs (not recommended: nfs for RWO)

### File Storage (RWX)
**Best For**: Shared files, multi-replica apps

**Tuning**:
- NFS: Tune rsize/wsize mount options
- ODF: Increase MDS resources
- Cloud: Use high-performance tiers (EFS Max I/O, etc.)

### Object Storage (S3)
**Best For**: Unstructured data, backups, images

**Tuning**:
- Use multi-part uploads for large files
- Enable lifecycle policies for old data
- Consider CDN for public assets

---

## Storage Sizing Guidelines

### Database Workloads
- **IOPS**: 3000+ for production
- **Capacity**: 2-3x current data size (for growth)
- **Snapshot Space**: 20-30% additional

### Application Data
- **IOPS**: 1000-2000
- **Capacity**: Actual data + 50% buffer

### Logs and Monitoring
- **IOPS**: 500-1000
- **Capacity**: Based on retention policy

### Recommendations by Cluster Size**:
- **SNO**: 120 GB minimum (OS + workloads)
- **HA (small)**: 500 GB per worker
- **HA (production)**: 1-2 TB per worker

---

## Troubleshooting

### Issue: PVC Stuck in Pending
**Causes**:
- No storage class available
- Insufficient storage capacity
- Node affinity not satisfied (local volumes)

**Resolution**:
```bash
# Check PVC status
oc describe pvc <pvc-name>

# Check storage classes
oc get storageclass

# Check PV availability
oc get pv

# Check events
oc get events -n <namespace>
```

### Issue: Pod Cannot Mount Volume
**Causes**:
- Access mode incompatible (RWO on multiple nodes)
- Volume already mounted on different node
- CSI driver not functioning

**Resolution**:
```bash
# Check pod events
oc describe pod <pod-name>

# Check CSI driver pods
oc get pods -n kube-system | grep csi

# Force pod to same node (if RWO)
oc delete pod <pod-name>
```

### Issue: Slow Storage Performance
**Causes**:
- Network latency (NFS, iSCSI)
- IOPS limits (cloud volumes)
- Oversubscribed storage backend

**Resolution**:
- Test with `fio` or `dd` benchmarks
- Increase IOPS/VPU settings (cloud)
- Use local storage or faster backend

---

## Best Practices

### Planning
- ✅ Choose storage backend based on infrastructure provider
- ✅ Define storage classes for different performance tiers
- ✅ Set default storage class
- ✅ Plan capacity with growth in mind

### Production
- ✅ Use dynamic provisioning (avoid static PVs)
- ✅ Enable volume snapshots for backups
- ✅ Monitor storage usage and IOPS
- ✅ Use ReadWriteOnce (RWO) when possible (better performance)
- ✅ Reserve ReadWriteMany (RWX) for truly shared workloads

### Security
- ✅ Enable encryption at rest (cloud volumes)
- ✅ Use separate storage classes per tenant/team
- ✅ Implement quotas on namespaces
- ✅ Regular backup testing

### SNO-Specific
- ✅ Use local storage for performance
- ✅ No ODF (requires 3+ nodes)
- ✅ External NFS acceptable for shared data

---

## Storage Recommendations Matrix

| Provider | Recommended | Performance | RWX Support | Complexity |
|----------|-------------|-------------|-------------|------------|
| **Bare Metal** | OpenShift Data Foundation | High | Yes | High |
| **vSphere** | vSphere CSI Driver | High | No (use NFS for RWX) | Low |
| **OCI** | OCI Block Volume CSI | High | No (use OCI File Storage for RWX) | Low |
| **Nutanix** | Nutanix CSI Driver | High | No (use NFS for RWX) | Low |
| **AWS** | EBS CSI Driver | High | No (use EFS for RWX) | Low |
| **Azure** | Azure Disk CSI | High | No (use Azure Files for RWX) | Low |
| **SNO** | Local Storage + NFS | High (local) | Yes (NFS) | Low |

---

## References

- [OpenShift Storage Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/storage/)
- [OpenShift Data Foundation](https://docs.redhat.com/en/documentation/red_hat_openshift_data_foundation/)
- [Container Storage Interface (CSI)](https://kubernetes-csi.github.io/docs/)
- [vSphere CSI Driver](https://docs.vmware.com/en/VMware-vSphere-Container-Storage-Plug-in/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Host Requirements](./host-requirements.md)
- [Infrastructure Providers](./providers.md)

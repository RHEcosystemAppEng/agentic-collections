# Host Requirements

Hardware and system requirements for OpenShift cluster nodes.

---

## Overview

OpenShift host requirements vary based on cluster type (SNO vs HA), node role (control plane vs worker), and workload characteristics.

---

## Single-Node OpenShift (SNO)

### Minimum Requirements

**CPU**:
- 8 physical cores (not vCPUs)
- x86_64, aarch64, ppc64le, or s390x architecture

**Memory**:
- 32 GB RAM minimum
- 64 GB RAM recommended for production workloads

**Storage**:
- 120 GB disk minimum
- SSD strongly recommended (NVMe best)
- Additional storage for application data

**Network**:
- 1 network interface (minimum)
- 1 Gbps network connection minimum
- Static IP or DHCP

### Recommended for Production

**CPU**: 16+ cores
**Memory**: 64-128 GB RAM
**Storage**: 500 GB+ SSD
**Network**: 10 Gbps

### Workload-Specific

**Development/Testing**:
- 8 CPU, 32 GB RAM, 120 GB disk ✅ Minimum acceptable

**Edge Production**:
- 12 CPU, 48 GB RAM, 250 GB SSD ✅ Recommended

**Heavy Workloads** (AI/ML, databases):
- 16+ CPU, 128 GB RAM, 1 TB NVMe SSD ✅ High-performance

---

## High-Availability (HA) Clusters

### Control Plane Nodes (Masters)

**Minimum Requirements** (each node):

**CPU**:
- 4 cores (vCPU acceptable for VMs)
- x86_64 recommended (aarch64, ppc64le, s390x supported)

**Memory**:
- 16 GB RAM minimum
- 32 GB RAM recommended for production

**Storage**:
- 120 GB disk minimum
- SSD recommended
- etcd benefits from fast I/O

**Network**:
- 1 Gbps minimum
- 10 Gbps recommended
- Low latency critical (<10ms between control plane nodes)

**Cluster Configuration**:
- 3 control plane nodes minimum (for HA)
- Must always be odd number (3, 5, 7)
- More than 5 not recommended (etcd overhead)

### Worker Nodes

**Minimum Requirements** (each node):

**CPU**:
- 2 cores minimum
- 4+ cores recommended

**Memory**:
- 8 GB RAM minimum
- 16-32 GB RAM typical for production

**Storage**:
- 120 GB disk minimum
- Size based on workload requirements
- Local storage for ephemeral data

**Network**:
- 1 Gbps minimum
- 10 Gbps for high-throughput workloads

**Cluster Configuration**:
- 2 worker nodes minimum (for HA)
- 3+ workers recommended for production
- Can scale horizontally as needed

### Compact Cluster (3 Nodes)

**Description**: Control plane nodes also run workloads (no dedicated workers)

**Each Node Requirements**:
- 8 CPU cores
- 32 GB RAM
- 500 GB disk
- Combines control plane + worker requirements

**Use Cases**:
- Small production environments
- Cost-sensitive deployments
- Limited hardware availability

**Limitations**:
- Cannot scale workers independently
- Higher load on control plane
- Minimum 3 nodes always required

---

## CPU Requirements by Role

### Control Plane

**Minimum**: 4 vCPU
**Recommended**: 8 vCPU

**Breakdown**:
- Kubernetes API server: 1 CPU
- etcd: 2 CPU (I/O intensive)
- Controller manager: 0.5 CPU
- Scheduler: 0.5 CPU
- OpenShift operators: 1 CPU

**Production**: 8-16 vCPU (for operator overhead and scaling)

### Worker

**Minimum**: 2 vCPU
**Recommended**: 4-8 vCPU

**Breakdown**:
- Kubelet: 0.5 CPU
- Container runtime: 0.5 CPU
- Application pods: Remaining capacity

**Workload-Specific**:
- **Light workloads** (web apps): 4 vCPU
- **Medium workloads** (APIs, services): 8 vCPU
- **Heavy workloads** (databases, AI/ML): 16+ vCPU

### SNO

**Minimum**: 8 physical cores
**Recommended**: 12-16 physical cores

**Breakdown**:
- Control plane functions: 4 cores
- System pods: 2 cores
- Application workloads: Remaining

---

## Memory Requirements by Role

### Control Plane

**Minimum**: 16 GB RAM
**Recommended**: 32 GB RAM

**Memory Usage**:
- Kubernetes API server: 2-4 GB
- etcd: 2-8 GB (grows with cluster size)
- Controller manager: 1 GB
- Scheduler: 1 GB
- OpenShift operators: 4-8 GB
- System overhead: 2-4 GB

**Production**: 32-64 GB (for logging, monitoring, operators)

### Worker

**Minimum**: 8 GB RAM
**Recommended**: 16-32 GB RAM

**Memory Usage**:
- Kubelet + runtime: 1-2 GB
- System pods: 2-4 GB
- Application pods: Remaining capacity

**Workload-Specific**:
- **Web applications**: 16 GB
- **Databases**: 32-64 GB
- **Big data/Analytics**: 128+ GB

### SNO

**Minimum**: 32 GB RAM
**Recommended**: 64 GB RAM

**Memory Usage**:
- Control plane: 16 GB
- Application workloads: 16-48 GB

---

## Storage Requirements

### Disk Types

**SSD (Solid State Drive)**:
- Recommended for all production clusters
- Critical for etcd (control plane)
- 10,000+ IOPS for production

**NVMe**:
- Best performance
- Recommended for databases and high-IOPS workloads
- 50,000+ IOPS typical

**HDD (Hard Disk Drive)**:
- Acceptable for non-production or worker nodes
- NOT recommended for control plane (etcd)
- 100-200 IOPS typical

### Disk Sizing

**Control Plane**:
- 120 GB minimum (OS + etcd + logs)
- 250 GB recommended for production
- etcd data typically <20 GB (grows with cluster size)

**Worker**:
- 120 GB minimum (OS only)
- 500 GB - 2 TB typical (includes application data)
- Size based on workload requirements

**SNO**:
- 120 GB absolute minimum
- 250 GB recommended for production
- 500 GB+ for data-intensive workloads

### Partition Layout

**Recommended**:
```
/boot     1 GB     (boot partition)
/         100 GB   (root filesystem)
/var      50+ GB   (container images, logs)
          Remaining for application data
```

**For OpenShift Data Foundation (ODF)**:
- Dedicated raw disks (no partitions, no filesystem)
- 1-4 TB per disk typical
- 3+ disks per node for redundancy

---

## Network Requirements

### Bandwidth

**Minimum**: 1 Gbps

**Recommended by Cluster Size**:
- Small (< 50 nodes): 1 Gbps
- Medium (50-200 nodes): 10 Gbps
- Large (200+ nodes): 25 Gbps

**Control Plane**: 10 Gbps recommended (etcd replication)

### Latency

**Critical**:
- Control plane to control plane: <10 ms (etcd quorum)
- Worker to control plane: <100 ms

**Recommendations**:
- Same datacenter: < 2 ms
- Same metro area: < 10 ms
- Different regions: Not recommended for HA control plane

### Network Interfaces

**Minimum**: 1 network interface

**Recommended**:
- 2 network interfaces (bonding for redundancy)
- Separate management and data networks

**Advanced**:
- 4 NICs: Management, storage, application traffic, cluster network
- SR-IOV for high-performance workloads

---

## Virtualization vs Bare Metal

### Virtual Machines

**Advantages**:
- Easier provisioning and management
- Resource flexibility
- VM migration (vMotion, etc.)

**Considerations**:
- Hypervisor overhead (~10-15% CPU/RAM)
- Ensure CPU is not oversubscribed
- Avoid memory ballooning
- Use SSD-backed datastores

**VM-Specific Requirements**:
- vCPU = virtual CPU (not physical core)
- Reserve RAM (no ballooning for control plane)
- Thick provisioning for etcd disks

### Bare Metal

**Advantages**:
- Maximum performance
- No hypervisor overhead
- Direct hardware access

**Considerations**:
- Less flexibility (no VM migration)
- Hardware failure = node replacement
- Physical access required

**Bare Metal-Specific**:
- Physical CPU cores (not vCPUs)
- BIOS/UEFI configuration access
- BMC/iDRAC for remote management

---

## BIOS/Firmware Settings

**Virtualization**:
- ✅ Enable Intel VT-x or AMD-V (for nested virtualization, OpenShift Virtualization)

**Power Management**:
- ✅ Set to "Performance" or "Maximum Performance"
- ❌ Disable power-saving features for production

**Boot Order**:
- ✅ Network boot (PXE) first (for initial installation)
- ✅ Local disk second (after installation)

**Secure Boot**:
- ⚠️ Can be enabled, but may require additional configuration
- Test before production deployment

**UEFI vs Legacy BIOS**:
- ✅ UEFI mode recommended (modern systems)
- ⚠️ Legacy BIOS acceptable for older hardware

---

## Platform-Specific Requirements

### Bare Metal

**BMC/iDRAC**:
- Optional but recommended for automation
- Allows remote power management
- Enables lights-out provisioning

**Network**:
- DHCP or static IPs
- VIPs for API and Ingress (HA clusters)

### VMware vSphere

**vSphere Version**: 7.0+ (8.0+ recommended)
**VM Hardware Version**: 15+ (20+ recommended)

**VM Settings**:
- CPU: vCPU with hardware virtualization exposed (for nested virt)
- RAM: Reserved (no ballooning for control plane)
- Disk: Thick provisioned (for etcd)
- Network: vNIC on appropriate portgroup

### Oracle Cloud (OCI)

**Instance Types**:
- Control plane: VM.Standard.E4.Flex (4 OCPU, 16 GB)
- Workers: VM.Standard.E4.Flex (8 OCPU, 32 GB)

**Storage**:
- Boot volume: 120 GB minimum
- Block volumes for application data

**Network**:
- VCN with subnets configured
- Security lists allowing OpenShift traffic

### Nutanix AHV

**AOS Version**: 6.5+ (6.7+ recommended)

**VM Settings**:
- CPU: vCPUs with hardware virtualization
- RAM: Dedicated (no memory oversubscription)
- Disks: SCSI controller, preallocated

**Storage**:
- Nutanix volume for application data
- Flash mode for high-performance

---

## Sizing Calculator

### Small Cluster (Development)
```
Control Plane: 3 nodes x (4 CPU, 16 GB RAM, 120 GB disk)
Workers: 2 nodes x (4 CPU, 16 GB RAM, 250 GB disk)

Total: 5 nodes, 32 CPU, 112 GB RAM, 860 GB disk
```

### Medium Cluster (Production)
```
Control Plane: 3 nodes x (8 CPU, 32 GB RAM, 250 GB disk)
Workers: 3 nodes x (8 CPU, 32 GB RAM, 500 GB disk)

Total: 6 nodes, 72 CPU, 192 GB RAM, 2.25 TB disk
```

### Large Cluster (Enterprise)
```
Control Plane: 3 nodes x (16 CPU, 64 GB RAM, 500 GB disk)
Workers: 10 nodes x (16 CPU, 64 GB RAM, 1 TB disk)

Total: 13 nodes, 208 CPU, 832 GB RAM, 11.5 TB disk
```

### SNO (Edge)
```
1 node: 12 CPU, 48 GB RAM, 250 GB SSD

Total: 1 node
```

---

## Scaling Considerations

### Vertical Scaling (Increase Node Size)
- Add more CPU/RAM to existing nodes
- Requires node reboot/recreation
- Limited by hardware capabilities

### Horizontal Scaling (Add More Nodes)
- Add more worker nodes to cluster
- No downtime for existing workloads
- Better for most scenarios

**Scaling Workers**:
- Can add/remove workers dynamically
- Workloads rebalance automatically
- Plan for 20-30% overhead capacity

**Control Plane**:
- Start with 3 nodes (recommended)
- Can expand to 5 or 7 for very large clusters
- More than 7 not recommended (etcd overhead)

---

## Workload-Specific Requirements

### Databases (PostgreSQL, MySQL, MongoDB)
- CPU: 8-16 cores per instance
- RAM: 32-128 GB per instance
- Disk: SSD/NVMe, 3000+ IOPS
- Network: 10 Gbps

### Web Applications
- CPU: 2-4 cores per replica
- RAM: 2-8 GB per replica
- Disk: Minimal (ephemeral storage)
- Network: 1 Gbps

### AI/ML Workloads
- CPU: 16+ cores (or GPU)
- RAM: 128+ GB
- Disk: NVMe, 10,000+ IOPS
- Network: 25 Gbps (model training)

### OpenShift Virtualization
- CPU: Hardware virtualization enabled
- RAM: 64+ GB (for VM overhead)
- Disk: SSD for VM images
- Network: SR-IOV for VM networking (optional)

---

## Troubleshooting Insufficient Resources

### Issue: Node Not Ready

**Check Resources**:
```bash
# Node resource usage
oc adm top nodes

# Node conditions
oc describe node <node-name> | grep Conditions -A 10
```

**Common Causes**:
- Disk pressure (> 85% disk usage)
- Memory pressure (insufficient RAM)
- PID pressure (too many processes)

**Resolution**:
- Clean up unused images: `oc adm prune images`
- Increase disk size
- Add more RAM or reduce workload

### Issue: Pods Pending Due to Insufficient Resources

**Check**:
```bash
# Pod status
oc describe pod <pod-name>

# Check for resource requests
oc get pod <pod-name> -o yaml | grep -A 5 resources
```

**Resolution**:
- Add more worker nodes
- Reduce pod resource requests
- Scale down other workloads

---

## Best Practices

### Planning
- ✅ Plan 20-30% overhead capacity for growth
- ✅ Use consistent hardware across control plane nodes
- ✅ Size workers based on workload requirements
- ✅ Test with realistic workloads before production

### Production
- ✅ Use SSD for all control plane nodes (etcd)
- ✅ Ensure low latency between control plane nodes
- ✅ Reserve CPU/RAM on VMs (no oversubscription)
- ✅ Monitor resource usage and scale proactively

### Cost Optimization
- ✅ Start small, scale horizontally as needed
- ✅ Use compact clusters for small deployments
- ✅ Right-size workers based on actual usage
- ✅ SNO for edge/development to reduce costs

---

## References

- [OpenShift Installation Prerequisites](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/installing/)
- [Assisted Installer Host Requirements](https://docs.redhat.com/en/documentation/assisted_installer_for_openshift_container_platform/)
- [Single-Node OpenShift Requirements](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/installing/installing-on-a-single-node)
- [Platform Types](./platforms.md)
- [Infrastructure Providers](./providers.md)
- [Storage Requirements](./storage.md)

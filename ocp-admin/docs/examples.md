# Cluster Configuration Examples

Real-world examples of valid OpenShift cluster configurations for different use cases.

---

## Example 1: SNO for Edge Deployment

**Scenario**: Single-server edge location (retail store, factory floor)

**Configuration**:
```yaml
cluster_name: edge-store-01
cluster_type: SNO
platform: none
openshift_version: 4.18.2
base_domain: retail.example.com
cpu_architecture: x86_64
```

**Host Requirements**:
- 1 physical server
- 8 CPU cores
- 32 GB RAM
- 120 GB SSD

**Network Configuration**:
```yaml
networking_mode: DHCP
vips: Not required (SNO)
```

**DNS Records Required**:
```
api.edge-store-01.retail.example.com.  A  <dhcp-assigned-ip>
*.apps.edge-store-01.retail.example.com.  A  <dhcp-assigned-ip>
```

**Use Case**:
- Point-of-sale applications
- Local inventory management
- Edge analytics
- Disconnected or intermittent connectivity

**Installation Time**: ~45 minutes

---

## Example 2: HA Cluster on Bare Metal (DHCP)

**Scenario**: On-premises data center with DHCP available

**Configuration**:
```yaml
cluster_name: production-dc1
cluster_type: HA
platform: baremetal
openshift_version: 4.18.2
base_domain: datacenter.example.com
cpu_architecture: x86_64
```

**Host Requirements**:
- 3 control plane nodes: 4 CPU, 16 GB RAM, 120 GB disk each
- 3 worker nodes: 8 CPU, 32 GB RAM, 500 GB disk each

**Network Configuration**:
```yaml
networking_mode: DHCP
machine_network: 192.168.100.0/24
api_vip: 192.168.100.10
ingress_vip: 192.168.100.11
```

**DNS Records Required**:
```
api.production-dc1.datacenter.example.com.  A  192.168.100.10
*.apps.production-dc1.datacenter.example.com.  A  192.168.100.11
```

**Use Case**:
- Production applications
- Corporate workloads
- Traditional data center

**Installation Time**: ~60-90 minutes

---

## Example 3: HA Cluster on Bare Metal (Static IPs)

**Scenario**: On-premises production cluster without DHCP

**Configuration**:
```yaml
cluster_name: prod-ocp
cluster_type: HA
platform: baremetal
openshift_version: 4.18.2
base_domain: prod.example.com
cpu_architecture: x86_64
```

**Host Requirements**:
- 3 control plane nodes
- 2 worker nodes

**Network Configuration** (Static):
```yaml
networking_mode: Static
machine_network: 10.50.0.0/24
api_vip: 10.50.0.100
ingress_vip: 10.50.0.101

static_network_configs:
  - host: master-0
    interface: ens3
    mac_address: "52:54:00:aa:bb:01"
    ipv4_address: 10.50.0.10
    prefix: 24
    gateway: 10.50.0.1
    dns_servers: ["10.50.0.5", "8.8.8.8"]

  - host: master-1
    interface: ens3
    mac_address: "52:54:00:aa:bb:02"
    ipv4_address: 10.50.0.11
    prefix: 24
    gateway: 10.50.0.1
    dns_servers: ["10.50.0.5", "8.8.8.8"]

  - host: master-2
    interface: ens3
    mac_address: "52:54:00:aa:bb:03"
    ipv4_address: 10.50.0.12
    prefix: 24
    gateway: 10.50.0.1
    dns_servers: ["10.50.0.5", "8.8.8.8"]

  - host: worker-0
    interface: ens3
    mac_address: "52:54:00:aa:bb:04"
    ipv4_address: 10.50.0.20
    prefix: 24
    gateway: 10.50.0.1
    dns_servers: ["10.50.0.5", "8.8.8.8"]

  - host: worker-1
    interface: ens3
    mac_address: "52:54:00:aa:bb:05"
    ipv4_address: 10.50.0.21
    prefix: 24
    gateway: 10.50.0.1
    dns_servers: ["10.50.0.5", "8.8.8.8"]
```

**Use Case**:
- Regulated environments requiring static IPs
- Networks without DHCP infrastructure
- Predictable IP allocation requirements

**Installation Time**: ~90 minutes (additional time for static network config)

---

## Example 4: HA Cluster on VMware vSphere

**Scenario**: Enterprise VMware environment

**Configuration**:
```yaml
cluster_name: vsphere-prod
cluster_type: HA
platform: vsphere
openshift_version: 4.18.2
base_domain: vmware.example.com
cpu_architecture: x86_64
```

**vSphere Requirements**:
- vSphere 7.0+ or 8.0+
- vCenter Server access
- Resource pool with adequate resources
- Network portgroup configured

**Network Configuration**:
```yaml
networking_mode: DHCP (from vSphere network)
machine_network: 172.16.10.0/24 (vSphere portgroup)
api_vip: 172.16.10.100
ingress_vip: 172.16.10.101
```

**Host Requirements** (VMs):
- 3 control plane VMs: 4 vCPU, 16 GB RAM, 120 GB disk
- 3 worker VMs: 8 vCPU, 32 GB RAM, 500 GB disk

**Use Case**:
- Existing VMware infrastructure
- Enterprise virtualized environment
- Need vSphere integration (storage, DRS)

**Post-Installation**:
- Configure vSphere CSI driver for dynamic storage
- Enable DRS anti-affinity rules
- Configure VM backup policies

**Installation Time**: ~60-90 minutes

---

## Example 5: HA Cluster on Oracle Cloud (OCI)

**Scenario**: Cloud deployment on Oracle Cloud Infrastructure

**Configuration**:
```yaml
cluster_name: oci-prod
cluster_type: HA
platform: oci
openshift_version: 4.18.2
base_domain: cloud.example.com
cpu_architecture: x86_64
```

**OCI Requirements**:
- OCI account with quotas
- Virtual Cloud Network (VCN) configured
- Subnets for control plane and workers
- Internet gateway or NAT gateway

**Network Configuration**:
```yaml
networking_mode: OCI-managed
vips: Not required (OCI load balancers handle this)
machine_network: 10.0.0.0/16 (VCN CIDR)
```

**Host Requirements** (OCI Instances):
- 3 control plane: VM.Standard.E4.Flex (4 OCPU, 16 GB RAM)
- 3 workers: VM.Standard.E4.Flex (8 OCPU, 32 GB RAM)

**Use Case**:
- Cloud-native deployment
- Oracle Cloud customers
- Need cloud load balancers and storage

**Advantages**:
- Automatic load balancer provisioning (no VIPs)
- Cloud-native networking
- OCI Block Volumes for storage

**Installation Time**: ~60 minutes

---

## Example 6: Development Cluster (Minimal)

**Scenario**: Local development and testing

**Configuration**:
```yaml
cluster_name: dev-local
cluster_type: SNO
platform: none
openshift_version: 4.18.2
base_domain: dev.local
cpu_architecture: x86_64
```

**Host Requirements**:
- 1 VM or physical server
- 8 CPU, 32 GB RAM, 120 GB disk

**Network Configuration**:
```yaml
networking_mode: DHCP
vips: Not required
```

**DNS** (local hosts file or dnsmasq):
```
192.168.122.100  api.dev-local.dev.local
192.168.122.100  oauth-openshift.apps.dev-local.dev.local
192.168.122.100  console-openshift-console.apps.dev-local.dev.local
192.168.122.100  *.apps.dev-local.dev.local
```

**Use Case**:
- Developer workstation
- CI/CD testing
- Learning OpenShift
- Proof of concept

**Installation Time**: ~30-45 minutes

---

## Example 7: Multi-Cluster Setup for Submariner

**Scenario**: Two clusters connected via Submariner for multi-cluster apps

**Cluster A Configuration**:
```yaml
cluster_name: cluster-a
cluster_type: HA
platform: baremetal
openshift_version: 4.18.2
base_domain: site-a.example.com
cpu_architecture: x86_64

networking:
  cluster_network: 10.128.0.0/14
  service_network: 172.30.0.0/16
  machine_network: 192.168.10.0/24
  api_vip: 192.168.10.100
  ingress_vip: 192.168.10.101
```

**Cluster B Configuration**:
```yaml
cluster_name: cluster-b
cluster_type: HA
platform: baremetal
openshift_version: 4.18.2
base_domain: site-b.example.com
cpu_architecture: x86_64

networking:
  cluster_network: 10.132.0.0/14  # NON-OVERLAPPING
  service_network: 172.31.0.0/16  # NON-OVERLAPPING
  machine_network: 192.168.20.0/24
  api_vip: 192.168.20.100
  ingress_vip: 192.168.20.101
```

**Critical Requirements**:
- ⚠️ Cluster and service networks MUST NOT overlap
- Gateway nodes with public IPs or VPN connectivity
- IPsec or WireGuard tunnels between clusters

**Use Case**:
- Multi-site applications
- Disaster recovery
- Geo-distributed workloads
- Hybrid cloud deployments

**Post-Installation**:
- Install Submariner operator on both clusters
- Configure gateway nodes
- Establish connectivity and test

---

## Example 8: Edge Cluster with Advanced Networking

**Scenario**: Edge location with bonded network interfaces and VLANs

**Configuration**:
```yaml
cluster_name: edge-factory-01
cluster_type: SNO
platform: none
openshift_version: 4.18.2
base_domain: factory.example.com
cpu_architecture: x86_64
```

**Network Configuration** (Advanced Static):
```yaml
networking_mode: Static (Advanced)

interfaces:
  - type: ethernet
    name: eth0
    mac_address: "52:54:00:aa:bb:01"
    # No IP - used for bonding

  - type: ethernet
    name: eth1
    mac_address: "52:54:00:aa:bb:02"
    # No IP - used for bonding

  - type: bond
    name: bond0
    mode: active-backup
    ports: [eth0, eth1]
    # No IP - base for VLAN

  - type: vlan
    name: bond0.100
    vlan_id: 100
    base_interface: bond0
    ipv4_address: 10.100.1.10
    prefix: 24

dns:
  servers: ["10.100.1.1", "8.8.8.8"]

routes:
  - destination: 0.0.0.0/0
    next_hop: 10.100.1.1
    interface: bond0.100
```

**Use Case**:
- High-availability networking (bonding)
- VLAN segmentation
- Production edge deployments
- Network redundancy requirements

**Installation Time**: ~60 minutes (complex networking)

---

## Example 9: Compact Cluster (3 Nodes)

**Scenario**: Small production cluster with control plane nodes as workers

**Configuration**:
```yaml
cluster_name: compact-prod
cluster_type: HA
platform: baremetal
openshift_version: 4.18.2
base_domain: compact.example.com
cpu_architecture: x86_64
```

**Host Requirements**:
- 3 nodes (control plane + worker combined)
- Each node: 8 CPU, 32 GB RAM, 500 GB disk

**Network Configuration**:
```yaml
networking_mode: DHCP
machine_network: 192.168.50.0/24
api_vip: 192.168.50.100
ingress_vip: 192.168.50.101
```

**Role Assignment**:
- All 3 nodes assigned "master" role
- Nodes automatically schedulable for workloads

**Use Case**:
- Small production environments
- Cost-sensitive deployments
- Limited hardware availability
- Branch office deployments

**Limitations**:
- Cannot scale workers separately
- Higher load on control plane nodes

**Installation Time**: ~60 minutes

---

## Example 10: Air-Gapped SNO

**Scenario**: Disconnected environment with no internet access

**Configuration**:
```yaml
cluster_name: airgap-sno
cluster_type: SNO
platform: none
openshift_version: 4.18.2
base_domain: airgap.local
cpu_architecture: x86_64
```

**Prerequisites**:
- Mirrored container registry (with all OpenShift images)
- Mirrored RHEL package repository
- Local NTP server
- Local DNS server

**Network Configuration**:
```yaml
networking_mode: Static
interface: eth0
mac_address: "52:54:00:aa:bb:01"
ipv4_address: 192.168.100.10
prefix: 24
gateway: 192.168.100.1
dns_servers: ["192.168.100.5"]  # Local DNS only
```

**Additional Configuration**:
```yaml
image_content_sources:
  - mirrors:
    - registry.airgap.local:5000/openshift/release-images
    source: quay.io/openshift-release-dev/ocp-release
additional_trust_bundle: |
  -----BEGIN CERTIFICATE-----
  <registry-ca-cert>
  -----END CERTIFICATE-----
```

**Use Case**:
- Classified/secure environments
- No internet connectivity
- Regulatory compliance (data sovereignty)

**Installation Time**: ~60 minutes (after mirroring complete)

---

## Configuration Matrix

| Example | Type | Nodes | Platform | Networking | VIPs | Use Case |
|---------|------|-------|----------|------------|------|----------|
| 1 | SNO | 1 | none | DHCP | No | Edge |
| 2 | HA | 6 | baremetal | DHCP | Yes | Data center |
| 3 | HA | 5 | baremetal | Static | Yes | Production |
| 4 | HA | 6 | vsphere | DHCP | Yes | VMware |
| 5 | HA | 6 | oci | OCI-managed | No | Cloud |
| 6 | SNO | 1 | none | DHCP | No | Development |
| 7 | HA + HA | 10 | baremetal | DHCP | Yes | Multi-cluster |
| 8 | SNO | 1 | none | Static Advanced | No | Edge Advanced |
| 9 | Compact | 3 | baremetal | DHCP | Yes | Small production |
| 10 | SNO | 1 | none | Static | No | Air-gapped |

---

## Common Configuration Patterns

### Pattern: Production HA
```
3 control plane nodes (dedicated)
3+ worker nodes (applications)
Static IPs or DHCP reservations
VIPs configured
Load balancer (external or VIPs)
```

### Pattern: Edge SNO
```
1 node (all roles)
DHCP or static IP
No VIPs
Minimal resources (8 CPU, 32 GB RAM)
```

### Pattern: Cloud-Native
```
HA cluster
Cloud platform (OCI, AWS, Azure)
Cloud load balancers (no VIPs)
Cloud storage integration
```

### Pattern: Air-Gapped
```
Mirrored registry
Local DNS and NTP
Static networking
No internet access
```

---

## References

- [Host Requirements](./host-requirements.md)
- [Networking Guide](./networking.md)
- [Static Networking Guide](./static-networking-guide.md)
- [Platform Types](./platforms.md)
- [Infrastructure Providers](./providers.md)
- [Input Validation Guide](./input-validation-guide.md)

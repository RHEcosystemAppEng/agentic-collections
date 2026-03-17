# Infrastructure Providers

Supported infrastructure providers for OpenShift cluster deployment and their specific requirements.

---

## Overview

OpenShift supports deployment across multiple infrastructure providers, each with specific requirements and configurations.

**Provider Types**:
- **Cloud Providers**: AWS, Azure, GCP, OCI
- **Virtualization**: VMware vSphere, Nutanix AHV, Red Hat Virtualization (RHV)
- **Bare Metal**: Physical servers, edge devices
- **Special**: None (for SNO and non-integrated deployments)

---

## Bare Metal

**Platform Value**: `baremetal`

**Description**: Physical servers or edge devices with direct hardware access.

**Requirements**:
- Physical servers with BMC/IPMI access (for automation)
- Network boot capability (PXE) or USB boot
- Direct network connectivity between nodes
- VIPs required for HA clusters (API + Ingress)

**Minimum Hardware**:
- See [Host Requirements](./host-requirements.md) for detailed specs

**Network Requirements**:
- Static IPs recommended (DHCP acceptable)
- Layer 2 connectivity for VIP failover
- Jumbo frames supported (optional, for performance)

**Advantages**:
- Full hardware control
- No hypervisor overhead
- Best performance
- Lower long-term costs

**Considerations**:
- Manual VIP configuration required
- Physical hardware management needed
- Network configuration complexity
- Requires BMC/iDRAC for remote management

**Use Cases**:
- Production workloads requiring maximum performance
- Edge deployments with local hardware
- Air-gapped environments
- Custom hardware configurations

---

## VMware vSphere

**Platform Value**: `vsphere`

**Description**: VMware virtualization environment with vSphere integration.

**Requirements**:
- vSphere 7.0+ (recommended 8.0+)
- vCenter Server for cluster management
- Sufficient vSphere resources (CPU, RAM, storage)
- VIPs required for HA clusters (API + Ingress)
- Network portgroup with DHCP or static IPs

**vSphere Integration**:
- Dynamic provisioning of persistent volumes
- VM anti-affinity rules for HA
- DRS (Distributed Resource Scheduler) integration
- vMotion support (for VM migration)

**Network Requirements**:
- Portgroup with appropriate VLAN
- VIPs in same portgroup as VMs
- DNS resolution for cluster FQDNs

**Advantages**:
- Familiar virtualization platform
- Enterprise VM management features
- Snapshot/backup integration
- Live migration capabilities

**Considerations**:
- vSphere licenses required
- VIP configuration needed (not automatic)
- Storage provisioner configuration
- vCenter credentials needed for integration

**Use Cases**:
- Existing VMware infrastructure
- Enterprise virtualized environments
- Development/test clusters
- Multi-tenant environments

**Post-Installation Configuration**:
- Configure vSphere CSI driver for storage
- Set up VM anti-affinity rules
- Configure DRS policies

---

## Oracle Cloud Infrastructure (OCI)

**Platform Value**: `oci`

**Description**: Oracle Cloud with native load balancer integration.

**Requirements**:
- OCI account with sufficient quotas
- Virtual Cloud Network (VCN) configured
- Subnets for control plane and workers
- OCI API credentials (for cloud provider integration)

**Network Requirements**:
- VCN with internet gateway (for public clusters)
- NAT gateway (for private clusters)
- Load balancers automatically provisioned
- Security lists configured for OpenShift traffic

**VIP Handling**:
- **VIPs NOT required** - OCI load balancers handle API/Ingress endpoints automatically
- Cloud-native networking

**Advantages**:
- Automatic load balancer provisioning
- No manual VIP configuration
- Cloud-native storage (OCI Block Volumes)
- Scalable infrastructure

**Considerations**:
- OCI-specific networking concepts (VCN, subnets)
- Load balancer costs
- Internet connectivity required (unless private cluster)
- OCI API credentials management

**Use Cases**:
- Cloud-native deployments
- Customers already on Oracle Cloud
- Rapid cluster provisioning
- Elastic workloads

**Post-Installation Configuration**:
- Configure OCI CSI driver for block storage
- Set up OCI Container Registry integration
- Configure egress routing

---

## Nutanix AHV

**Platform Value**: `nutanix`

**Description**: Nutanix hyperconverged infrastructure with AHV hypervisor.

**Requirements**:
- Nutanix AOS 6.5+ (recommended 6.7+)
- Prism Central for cluster management
- Sufficient Nutanix cluster resources
- VIPs required for HA clusters (API + Ingress)
- Network with DHCP or static IPs

**Nutanix Integration**:
- Dynamic volume provisioning via Nutanix CSI
- VM anti-affinity for HA
- Snapshot/clone capabilities
- Category-based resource management

**Network Requirements**:
- Nutanix network (VLAN or overlay)
- VIPs in same network as VMs
- DNS resolution configured

**Advantages**:
- Hyperconverged infrastructure (compute + storage)
- Simplified management via Prism
- Built-in storage performance
- VM-level snapshots

**Considerations**:
- Nutanix licenses required
- VIP configuration needed
- Prism credentials for integration
- AHV-specific networking

**Use Cases**:
- Existing Nutanix deployments
- Hyperconverged infrastructure preference
- Branch office deployments
- Private cloud environments

**Post-Installation Configuration**:
- Configure Nutanix CSI driver
- Set up VM categories for organization
- Configure storage classes

---

## AWS (Amazon Web Services)

**Platform Value**: `aws` (for future support)

**Status**: Currently supported via IPI (Installer-Provisioned Infrastructure), may be added to Assisted Installer in future releases.

**Current Alternative**: Use `openshift-install` CLI for AWS deployments.

**Requirements** (when supported):
- AWS account with IAM permissions
- VPC with subnets (public + private)
- Route53 for DNS (or external DNS)
- S3 bucket for registry storage
- EC2 quotas for instances

**Network**:
- Elastic Load Balancers auto-provisioned
- No manual VIP configuration
- Security groups configured automatically

---

## Azure (Microsoft Azure)

**Platform Value**: `azure` (for future support)

**Status**: Currently supported via IPI, may be added to Assisted Installer.

**Current Alternative**: Use `openshift-install` CLI or Azure Red Hat OpenShift (ARO).

**Requirements** (when supported):
- Azure subscription
- Resource group
- Virtual network (VNet) with subnets
- Azure DNS or external DNS
- Service principal with permissions

**Network**:
- Azure Load Balancers auto-provisioned
- No manual VIP configuration
- Network Security Groups configured

---

## GCP (Google Cloud Platform)

**Platform Value**: `gcp` (for future support)

**Status**: Currently supported via IPI, may be added to Assisted Installer.

**Current Alternative**: Use `openshift-install` CLI for GCP deployments.

**Requirements** (when supported):
- GCP project with quotas
- VPC network configured
- Cloud DNS or external DNS
- Service account with permissions

**Network**:
- Google Cloud Load Balancers auto-provisioned
- No manual VIP configuration
- Firewall rules configured automatically

---

## None Platform

**Platform Value**: `none`

**Description**: No cloud provider integration, generic installation.

**When Used**:
- **Required for SNO (Single-Node OpenShift)**
- Custom/unsupported infrastructure
- Air-gapped environments without provider integration
- Testing/development without cloud features

**Characteristics**:
- No cloud provider-specific integration
- No dynamic volume provisioning (unless CSI driver manually installed)
- No automatic load balancers
- Manual configuration for most day-2 operations

**Requirements**:
- Same as bare metal (physical or virtual servers)
- Network connectivity between nodes
- Manual configuration for storage, load balancing

**Advantages**:
- Maximum flexibility
- No cloud dependencies
- Works on any infrastructure

**Considerations**:
- No cloud automation features
- Manual storage configuration required
- No dynamic load balancers
- More day-2 operational overhead

**Use Cases**:
- Single-Node OpenShift (SNO)
- Proof-of-concept deployments
- Non-standard infrastructure
- Air-gapped environments

---

## Platform Comparison Matrix

| Feature | Bare Metal | vSphere | OCI | Nutanix | None |
|---------|-----------|---------|-----|---------|------|
| **VIPs Required** | Yes (HA) | Yes (HA) | No | Yes (HA) | No (SNO only) |
| **Cloud Integration** | No | No | Yes | No | No |
| **Dynamic Storage** | Manual | Yes (vSphere CSI) | Yes (OCI CSI) | Yes (Nutanix CSI) | Manual |
| **Load Balancers** | Manual | Manual | Auto | Manual | Manual |
| **HA Support** | Yes | Yes | Yes | Yes | No (SNO only) |
| **Best For** | Performance | VMware shops | Cloud-native | HCI | SNO/Development |

---

## Choosing a Provider

### Production Workloads
- **Bare Metal**: Maximum performance, full control
- **vSphere**: Existing VMware infrastructure
- **OCI**: Oracle Cloud customers
- **Nutanix**: Hyperconverged infrastructure preference

### Development/Testing
- **None Platform (SNO)**: Quick dev clusters
- **vSphere**: Familiar virtualization
- **Cloud Providers**: Rapid provisioning

### Edge Deployments
- **Bare Metal**: Physical edge devices
- **None Platform (SNO)**: Single-server edge locations

### Cost Considerations
- **Bare Metal**: Higher upfront, lower operational
- **Cloud Providers**: Pay-as-you-go, higher long-term
- **Virtualization**: Licensing + infrastructure costs

---

## Network Requirements Summary

### All Providers
- DNS resolution for cluster FQDNs
- NTP servers accessible
- Red Hat image registry access (or mirrored registry)

### HA Clusters
- API endpoint (port 6443)
- Ingress endpoint (ports 80, 443)
- Node-to-node communication (various ports)

### Cloud Providers (OCI, AWS, Azure, GCP)
- Outbound internet access (for cloud APIs)
- Cloud provider API endpoints reachable

### On-Premises (Bare Metal, vSphere, Nutanix)
- Layer 2 network for VIP failover (HA clusters)
- DHCP or static IP allocation
- Firewall rules for inter-node communication

---

## References

- [OpenShift Platform Support Matrix](https://docs.redhat.com/en/documentation/openshift_container_platform/)
- [Assisted Installer Supported Platforms](https://docs.redhat.com/en/documentation/assisted_installer_for_openshift_container_platform/)
- [Host Requirements](./host-requirements.md)
- [Networking Guide](./networking.md)
- [Platform Types](./platforms.md)

# OpenShift Platform Types

Overview of different OpenShift deployment models and their characteristics.

---

## Overview

OpenShift comes in multiple deployment models, each optimized for specific use cases and operational models.

**Platform Types**:
- **OCP (OpenShift Container Platform)** - Self-managed on any infrastructure
- **SNO (Single-Node OpenShift)** - Compact deployment for edge/development
- **OSD (OpenShift Dedicated)** - Managed service on AWS/GCP
- **ROSA (Red Hat OpenShift Service on AWS)** - AWS-native managed service
- **ARO (Azure Red Hat OpenShift)** - Azure-native managed service

**API Access by Platform Type**:

The `cluster-inventory` skill uses different Red Hat APIs depending on the platform type:

| Platform Type | Management Model | API Endpoint | API Path |
|--------------|------------------|--------------|----------|
| **OCP** | Self-managed | Assisted Installer | `/api/assisted-install/v2` |
| **SNO** | Self-managed | Assisted Installer | `/api/assisted-install/v2` |
| **ROSA** | Managed Service | OCM (Clusters Management) | `/api/clusters_mgmt/v1` |
| **ARO** | Managed Service | OCM (Clusters Management) | `/api/clusters_mgmt/v1` |
| **OSD** | Managed Service | OCM (Clusters Management) | `/api/clusters_mgmt/v1` |

**Note**: The `cluster-inventory` skill automatically queries BOTH APIs and merges results to provide a unified view of all your OpenShift clusters regardless of type.

---

## OCP (OpenShift Container Platform)

**Type**: Self-managed

**Description**: Full OpenShift deployment that you install and manage yourself on your chosen infrastructure.

**Deployment Models**:
- **High-Availability (HA)**: 3+ control plane nodes, 2+ worker nodes
- **Compact Cluster**: 3 control plane nodes (also workers), 0 dedicated workers
- **Single-Node OpenShift (SNO)**: See dedicated section below

**Infrastructure Support**:
- Bare metal
- VMware vSphere
- Red Hat Virtualization (RHV)
- Red Hat OpenStack Platform (RHOSP)
- Nutanix AHV
- Cloud providers (AWS, Azure, GCP) via IPI

**Management Responsibility**:
- ✅ You manage: Infrastructure, cluster lifecycle, upgrades, scaling
- ❌ Red Hat provides: Software updates, security patches, documentation

**Advantages**:
- Full control over infrastructure and configuration
- Deploy anywhere (on-premises, cloud, edge)
- Custom networking and storage
- Air-gapped deployment support
- Compliance with specific regulations

**Considerations**:
- Requires infrastructure expertise
- Manual upgrade management
- Higher operational overhead
- Need to maintain availability and performance

**Use Cases**:
- On-premises data centers
- Private cloud deployments
- Regulatory/compliance requirements
- Custom infrastructure needs
- Air-gapped environments

**Minimum Requirements** (HA):
- 3 control plane nodes: 4 vCPU, 16GB RAM each
- 2+ worker nodes: 2 vCPU, 8GB RAM each
- Shared storage or CSI driver

---

## SNO (Single-Node OpenShift)

**Type**: Self-managed, compact deployment

**Description**: OpenShift running on a single physical or virtual server, combining control plane and worker roles.

**Key Characteristics**:
- Single node serves as both control plane and worker
- Reduced footprint for resource-constrained environments
- Same OpenShift features as multi-node clusters
- No high-availability (single point of failure)

**Infrastructure Support**:
- Bare metal (physical servers)
- Virtual machines (VMware, KVM, etc.)
- Edge devices
- Platform value: **Always `none`** (no cloud provider integration)

**Management Responsibility**:
- ✅ You manage: Everything (same as OCP)
- ❌ Red Hat provides: Software updates, patches

**Advantages**:
- Minimal resource footprint
- Quick deployment (< 1 hour)
- Full OpenShift capabilities in compact form
- Ideal for edge locations
- Lower cost (single server)

**Considerations**:
- No high-availability (if node fails, cluster is down)
- Limited capacity for workloads
- Performance constraints with heavy workloads
- Not suitable for production critical workloads

**Minimum Requirements**:
- 8 vCPU (physical cores)
- 32 GB RAM
- 120 GB disk
- See [Host Requirements](./host-requirements.md) for details

**Use Cases**:
- Edge deployments (retail stores, factories, remote offices)
- Development and testing environments
- Proof-of-concept clusters
- Far edge with limited connectivity
- Single-tenant workloads

**Limitations**:
- No cluster-level HA
- Single node storage (no distributed storage)
- Limited scaling (vertical only, not horizontal)
- Some operators may require HA and won't work

---

## OSD (OpenShift Dedicated)

**Type**: Managed service

**Description**: Fully managed OpenShift clusters on AWS or GCP, managed by Red Hat Site Reliability Engineers (SREs).

**Infrastructure Support**:
- Amazon Web Services (AWS)
- Google Cloud Platform (GCP)

**Management Responsibility**:
- ✅ Red Hat SREs manage: Infrastructure provisioning, cluster upgrades, monitoring, incident response, scaling
- ✅ You manage: Applications, user access, some cluster configurations

**Advantages**:
- Fully managed by Red Hat SREs
- 99.95% uptime SLA
- Automatic upgrades and patching
- 24/7 monitoring and support
- Focus on applications, not infrastructure

**Considerations**:
- Limited infrastructure customization
- Cloud provider costs (AWS/GCP)
- Red Hat subscription + cloud costs
- Less control over cluster configuration

**Use Cases**:
- Organizations wanting managed OpenShift
- Focus on development, not operations
- Need SLA guarantees
- Cloud-first strategy

**Cluster Sizes**:
- Production clusters: Minimum 3 control plane, 4 worker nodes
- Development clusters: Smaller footprints available

---

## ROSA (Red Hat OpenShift Service on AWS)

**Type**: Managed service (AWS-native)

**Description**: Fully managed OpenShift natively integrated with AWS services, jointly supported by Red Hat and AWS.

**Infrastructure**:
- Amazon Web Services (AWS) only
- Deep AWS integration (ELB, EBS, IAM, CloudWatch)

**Management Responsibility**:
- ✅ Red Hat + AWS manage: Cluster infrastructure, control plane, upgrades
- ✅ You manage: Applications, user access

**AWS Integration**:
- AWS IAM for authentication
- Elastic Load Balancers (ELB) for ingress
- Amazon EBS for persistent storage
- AWS CloudWatch for monitoring
- AWS PrivateLink support
- AWS STS (Security Token Service) support

**Advantages**:
- Native AWS experience
- Integrated billing (via AWS Marketplace)
- Joint Red Hat + AWS support
- AWS security and compliance features
- Automatic cluster and infrastructure management

**Considerations**:
- AWS-only (no multi-cloud)
- Costs: ROSA subscription + AWS infrastructure
- AWS-specific tooling and concepts

**Use Cases**:
- AWS-centric organizations
- Need native AWS integrations
- Prefer single vendor billing
- Require AWS compliance certifications

**Deployment Options**:
- **ROSA Classic**: Red Hat-managed VPC
- **ROSA with HCP (Hosted Control Plane)**: Control plane hosted in Red Hat account, workers in customer account

---

## ARO (Azure Red Hat OpenShift)

**Type**: Managed service (Azure-native)

**Description**: Fully managed OpenShift natively integrated with Microsoft Azure, jointly supported by Red Hat and Microsoft.

**Infrastructure**:
- Microsoft Azure only
- Deep Azure integration (Azure Load Balancer, Azure Disks, Azure AD)

**Management Responsibility**:
- ✅ Red Hat + Microsoft manage: Cluster infrastructure, control plane, upgrades
- ✅ You manage: Applications, user access

**Azure Integration**:
- Azure Active Directory (AAD) for authentication
- Azure Load Balancers for ingress
- Azure Disks for persistent storage
- Azure Monitor integration
- Azure Private Link support
- Azure Key Vault integration

**Advantages**:
- Native Azure experience
- Integrated billing via Azure
- Joint Red Hat + Microsoft support
- Azure security and compliance
- Automatic management

**Considerations**:
- Azure-only (no multi-cloud)
- Costs: ARO subscription + Azure infrastructure
- Azure-specific tooling

**Use Cases**:
- Azure-centric organizations
- Need native Azure integrations
- Microsoft enterprise agreement customers
- Require Azure compliance certifications

**Minimum Cluster Size**:
- 3 control plane nodes
- 3 worker nodes

---

## Platform Comparison Matrix

| Feature | OCP (HA) | SNO | OSD | ROSA | ARO |
|---------|----------|-----|-----|------|-----|
| **Management** | Self-managed | Self-managed | Managed by Red Hat | Managed (RH + AWS) | Managed (RH + MS) |
| **Infrastructure** | Any | Any (usually bare metal) | AWS, GCP | AWS only | Azure only |
| **High Availability** | Yes | No | Yes | Yes | Yes |
| **Minimum Nodes** | 5 (3 masters + 2 workers) | 1 | 7 (3 masters + 4 workers) | 3+ | 6 (3 masters + 3 workers) |
| **Control Plane Access** | Full | Full | Limited | Limited | Limited |
| **Customization** | High | High | Medium | Medium | Medium |
| **Operational Overhead** | High | Medium | Low | Low | Low |
| **Upgrades** | Manual | Manual | Automatic | Automatic | Automatic |
| **SLA** | Self-managed | Self-managed | 99.95% | 99.95% | 99.95% |
| **Best For** | Full control | Edge/dev | Managed cloud | AWS customers | Azure customers |

---

## Choosing the Right Platform

### Self-Managed (OCP)
**Choose if**:
- Need full infrastructure control
- On-premises or hybrid deployment
- Air-gapped environment
- Specific compliance requirements
- Custom networking/storage needs

**Avoid if**:
- Limited operational expertise
- Prefer managed services
- Need guaranteed SLA

### Single-Node (SNO)
**Choose if**:
- Edge deployment with single server
- Development/testing environment
- Minimal resource footprint required
- Can tolerate no HA

**Avoid if**:
- Need high availability
- Production critical workloads
- Resource-intensive applications

### Managed Services (OSD, ROSA, ARO)
**Choose if**:
- Prefer managed operations
- Cloud-first strategy
- Need SLA guarantees
- Want to focus on applications

**Choose ROSA if**: Already on AWS
**Choose ARO if**: Already on Azure
**Choose OSD if**: Need flexibility between AWS/GCP

---

## Migration Between Platforms

### OCP to SNO
- Not directly supported
- Deploy new SNO, migrate applications

### SNO to OCP (HA)
- Not directly supported (architectural change)
- Deploy new HA cluster, migrate applications
- Cannot add nodes to SNO to make it HA

### OCP (Self-Managed) to ROSA/ARO/OSD
- Requires re-deployment
- Application-level migration
- Use tools: Migration Toolkit for Containers (MTC)

### Between Managed Services
- Not supported
- Re-deploy on target platform
- Migrate applications manually or with MTC

---

## Architecture Differences

### Control Plane Distribution

**OCP HA**:
- 3 dedicated control plane nodes
- 2+ dedicated worker nodes
- etcd distributed across 3 nodes

**SNO**:
- 1 node serves all roles
- Single etcd instance
- No distribution

**Managed Services (OSD/ROSA/ARO)**:
- Control plane: Red Hat-managed
- Worker nodes: Customer-managed
- Infrastructure abstracted

---

## Feature Availability

| Feature | OCP | SNO | OSD | ROSA | ARO |
|---------|-----|-----|-----|------|-----|
| **OpenShift Virtualization** | ✅ | ⚠️ Limited | ❌ | ⚠️ Limited | ⚠️ Limited |
| **OpenShift Data Foundation** | ✅ | ⚠️ Limited | ✅ | ✅ | ✅ |
| **Service Mesh** | ✅ | ⚠️ Limited | ✅ | ✅ | ✅ |
| **Serverless** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Pipelines** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **GitOps** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Advanced Cluster Management** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Custom Operators** | ✅ | ✅ | ⚠️ Limited | ⚠️ Limited | ⚠️ Limited |

**Legend**:
- ✅ Fully supported
- ⚠️ Limited support or constraints
- ❌ Not supported

---

## Licensing and Costs

### OCP (Self-Managed)
- Red Hat OpenShift subscription required
- Priced per: 2-core packs or virtual data center (VDC)
- Infrastructure costs (hardware/cloud) separate

### SNO
- Same subscription as OCP
- Usually lower infrastructure cost (1 server)

### OSD
- Managed service subscription
- Includes: OpenShift + SRE management
- Does NOT include: AWS/GCP infrastructure costs

### ROSA
- Per-cluster management fee
- Per-node/vCPU pricing
- AWS infrastructure costs separate
- Billed through AWS Marketplace

### ARO
- Per-cluster management fee
- Per-node pricing
- Azure infrastructure costs separate
- Billed through Azure

---

## Support and SLAs

### Self-Managed (OCP, SNO)
- Red Hat support for software issues
- No infrastructure SLA (self-managed)
- Support tiers: Standard, Premium

### Managed Services (OSD, ROSA, ARO)
- 99.95% uptime SLA
- 24/7 Red Hat SRE monitoring
- Automated incident response
- Included with subscription

---

## References

- [OpenShift Product Overview](https://www.redhat.com/en/technologies/cloud-computing/openshift)
- [OpenShift Container Platform Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/)
- [Single-Node OpenShift Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/installing/installing-on-a-single-node)
- [ROSA Documentation](https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/)
- [ARO Documentation](https://docs.redhat.com/en/documentation/azure_red_hat_openshift/)
- [Infrastructure Providers](./providers.md)
- [Host Requirements](./host-requirements.md)

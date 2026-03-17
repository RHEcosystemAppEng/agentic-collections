# Documentation Index

Complete reference guide for OpenShift cluster deployment and management using the Assisted Installer.

---

## Getting Started

Start here for cluster creation:

- **[Quick Reference](./quick-reference.md)** - Common commands and operations
- **[Input Validation Guide](./input-validation-guide.md)** - Parameter requirements and validation rules
- **[Examples](./examples.md)** - Real-world cluster configurations for different scenarios

---

## Planning Your Cluster

Before creating a cluster, review these guides:

### Infrastructure Selection

- **[Infrastructure Providers](./providers.md)** - Bare metal, VMware vSphere, Oracle Cloud (OCI), Nutanix AHV
  - Platform-specific requirements
  - Network and VIP requirements
  - Comparison matrix

- **[Platform Types](./platforms.md)** - SNO, OCP, OpenShift Dedicated, ROSA, ARO
  - Self-managed vs managed services
  - Feature comparison
  - Use case recommendations

- **[Host Requirements](./host-requirements.md)** - Hardware specifications
  - CPU, RAM, disk requirements by node role
  - SNO vs HA cluster sizing
  - Workload-specific recommendations

### Network Planning

- **[Networking Guide](./networking.md)** - Comprehensive networking reference
  - Cluster/service/machine networks
  - VIP configuration
  - DNS requirements
  - Multi-cluster considerations (Submariner)
  - CIDR planning template

- **[Static Networking Guide](./static-networking-guide.md)** - NMState configuration
  - Simple, advanced, and manual modes
  - Bonding and VLAN configuration
  - Boot order and MAC address matching

### Storage Planning

- **[Storage](./storage.md)** - Storage options by infrastructure provider
  - CSI drivers (vSphere, OCI, Nutanix)
  - OpenShift Data Foundation (ODF)
  - Local vs network storage
  - Storage classes and persistent volumes
  - Performance tuning

---

## Installation

### Cluster Creation Workflow

Use the `cluster-creator` skill for end-to-end deployment:

1. Prerequisites verification
2. Configuration gathering (interactive)
3. Cluster definition creation
4. ISO generation and host discovery
5. Role assignment and validation
6. Installation execution
7. Credential retrieval

See: `skills/cluster-creator/SKILL.md`

### Configuration Examples

- **[Examples](./examples.md)** includes:
  - SNO for edge deployment
  - HA cluster on bare metal (DHCP)
  - HA cluster on bare metal (static IPs)
  - HA cluster on VMware vSphere
  - HA cluster on Oracle Cloud (OCI)
  - Multi-cluster setup (Submariner)
  - Air-gapped deployment
  - Compact 3-node cluster

---

## Post-Installation

### Credentials and Access

- **[Credentials Management](./credentials-management.md)** - Security and authentication
  - Kubeconfig setup and rotation
  - Kubeadmin password handling
  - Identity provider configuration (HTPasswd, LDAP, GitHub, OIDC)
  - RBAC and service accounts
  - Removing kubeadmin user

### Multi-Cluster Management

- **[Multi-Cluster Authentication](./multi-cluster-auth.md)** - Managing multiple clusters
  - Kubeconfig merging
  - Context switching
  - Centralized authentication

---

## Troubleshooting

- **[Troubleshooting Guide](./troubleshooting.md)** - Common errors and solutions
  - Cluster lifecycle states
  - Installation failures
  - Network connectivity issues
  - Host discovery problems
  - Validation errors
  - Error documentation workflow

- **[Quick Reference](./quick-reference.md)** - Diagnostic commands and quick fixes

---

## Official OpenShift Documentation

### Installation & Configuration
- [OpenShift Container Platform 4.18 Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18)
- [Installing on bare metal](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/installing/installing-on-bare-metal)
- [Installing on vSphere](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/installing/installing-on-vsphere)
- [Installing Single-Node OpenShift](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/installing/installing-on-a-single-node)

### Assisted Installer
- [Assisted Installer for OpenShift Container Platform](https://docs.redhat.com/en/documentation/assisted_installer_for_openshift_container_platform/)
- [Installing with Assisted Installer](https://docs.redhat.com/en/documentation/assisted_installer_for_openshift_container_platform/2024/html/installing_openshift_container_platform_with_the_assisted_installer/)

### Networking
- [Networking](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/networking/)
- [OVN-Kubernetes Network Plugin](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/networking/ovn-kubernetes-network-plugin)
- [Network Policy](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/networking/network-policy)

### Storage
- [Storage](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/storage/)
- [Persistent Storage](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/storage/understanding-persistent-storage)
- [OpenShift Data Foundation](https://docs.redhat.com/en/documentation/red_hat_openshift_data_foundation/)

### Authentication & Security
- [Authentication and Authorization](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/authentication_and_authorization/)
- [Configuring Identity Providers](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/authentication_and_authorization/configuring-identity-providers)
- [Using RBAC](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/authentication_and_authorization/using-rbac)

### Post-Deployment Operations
- [Post-installation configuration](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/post-installation_configuration/)
- [Updating clusters](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/updating_clusters/)
- [Backup and restore](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/backup_and_restore/)

### Platform-Specific
- [Red Hat OpenShift Service on AWS (ROSA)](https://docs.redhat.com/en/documentation/red_hat_openshift_service_on_aws/)
- [Azure Red Hat OpenShift (ARO)](https://docs.redhat.com/en/documentation/azure_red_hat_openshift/)
- [OpenShift Dedicated](https://docs.redhat.com/en/documentation/openshift_dedicated/)

---

## Document Navigation Tips

### By Use Case

**I want to create my first cluster**:
1. Read [Examples](./examples.md) for your scenario
2. Check [Host Requirements](./host-requirements.md)
3. Review [Input Validation Guide](./input-validation-guide.md)
4. Use `cluster-creator` skill

**I'm planning a production deployment**:
1. [Providers](./providers.md) - Choose infrastructure
2. [Platforms](./platforms.md) - Choose deployment model
3. [Host Requirements](./host-requirements.md) - Size your cluster
4. [Networking](./networking.md) - Plan CIDR ranges
5. [Storage](./storage.md) - Select storage backend
6. [Examples](./examples.md) - Review similar deployments

**I have network restrictions**:
1. [Networking Guide](./networking.md) - Understand requirements
2. [Static Networking Guide](./static-networking-guide.md) - Configure static IPs
3. [Examples](./examples.md#example-3-ha-cluster-on-bare-metal-static-ips) - See static IP example

**I'm setting up edge deployments**:
1. [Platforms](./platforms.md#sno-single-node-openshift) - Understand SNO
2. [Host Requirements](./host-requirements.md#single-node-openshift-sno) - Minimum specs
3. [Examples](./examples.md#example-1-sno-for-edge-deployment) - Edge configuration
4. [Examples](./examples.md#example-10-air-gapped-sno) - Disconnected setup

**Something went wrong**:
1. [Troubleshooting](./troubleshooting.md) - Common errors
2. [Quick Reference](./quick-reference.md) - Diagnostic commands
3. Check official docs links above

---

## Documentation Standards

All documentation follows these principles:

- **Official Sources**: Content derived from Red Hat official documentation (links provided)
- **Production-Ready**: Real-world examples, not toy configurations
- **Complete**: Includes error handling and edge cases
- **Referenced**: Cross-linked to related documents
- **Up-to-Date**: Validated against OpenShift 4.18

---

## Contributing to Documentation

When errors are encountered during cluster operations:

1. Document new errors in [Troubleshooting](./troubleshooting.md)
2. Add resolutions if known (or mark "Under investigation")
3. Update [Quick Reference](./quick-reference.md) if new commands used
4. Create examples in [Examples](./examples.md) for new scenarios

See: [Troubleshooting - Automatic Error Documentation](./troubleshooting.md#automatic-error-documentation)

---

**Last Updated**: 2026-03-17
**OpenShift Version**: 4.18
**Specification**: agentskills.io v1.0

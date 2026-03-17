# OpenShift Networking Configuration

Comprehensive guide to networking configuration for OpenShift clusters.

---

## Overview

OpenShift networking encompasses pod networking, service networking, ingress, and cluster connectivity. Proper network configuration is critical for cluster functionality.

---

## Network Types

### Cluster Network (Pod Network)
**Purpose**: Internal pod-to-pod communication

**Default CIDR**: `10.128.0.0/14`
**Default Host Prefix**: `/23` (512 IPs per node)

**Characteristics**:
- Software-defined network (SDN)
- Automatically assigned to pods
- Managed by CNI plugin (OVN-Kubernetes default)

### Service Network
**Purpose**: Internal service discovery and load balancing

**Default CIDR**: `172.30.0.0/16`

**Characteristics**:
- Virtual IPs for Kubernetes services
- ClusterIP type services
- Load balancing across pods

### Machine Network (Node Network)
**Purpose**: Physical/virtual server network where nodes reside

**CIDR**: Depends on infrastructure (e.g., `192.168.1.0/24`)

**Characteristics**:
- Physical network connectivity
- DHCP or static IPs
- Must allow node-to-node communication

---

## Default Network Configuration

### SNO (Single-Node OpenShift)
```yaml
clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
serviceNetwork:
  - 172.30.0.0/16
machineNetwork:
  - cidr: <auto-detected from node IP>
networkType: OVNKubernetes
```

### HA Clusters
```yaml
clusterNetwork:
  - cidr: 10.128.0.0/14
    hostPrefix: 23
serviceNetwork:
  - 172.30.0.0/16
machineNetwork:
  - cidr: <auto-detected or specified>
networkType: OVNKubernetes
```

---

## Network Plugins (CNI)

### OVN-Kubernetes (Default)
**Status**: Default since OpenShift 4.12+

**Features**:
- Layer 3 overlay network
- Network policy support
- IPv4 and IPv6 support
- Egress IP and firewall support
- Hybrid networking (Linux + Windows nodes)
- Better scalability than OpenShift SDN

**Use Cases**:
- All new deployments (recommended)
- Hybrid environments (Linux + Windows)
- Advanced network policies

### OpenShift SDN (Deprecated)
**Status**: Deprecated, removed in OpenShift 4.17+

**Migration**: Migrate to OVN-Kubernetes before upgrading to 4.17+

---

## DHCP vs Static IP Configuration

### DHCP (Default)
**Advantages**:
- Automatic IP assignment
- Simpler configuration
- Faster deployment

**Requirements**:
- DHCP server on network
- Sufficient IP address pool
- DHCP reservations recommended (for consistent IPs)

**Use Cases**:
- Development/testing clusters
- Environments with reliable DHCP
- Quick deployments

### Static IP Configuration
**Advantages**:
- Predictable IP addresses
- No DHCP dependency
- Better for production

**Requirements**:
- NMState YAML configuration per host
- MAC addresses for each host
- IP allocation planning

**Use Cases**:
- Production clusters
- Networks without DHCP
- Air-gapped environments
- Regulatory requirements

**See**: [Static Networking Guide](./static-networking-guide.md) for detailed configuration

---

## Virtual IPs (VIPs)

### When Required
- **HA Clusters** on: baremetal, vsphere, nutanix
- **NOT required** for: SNO, OCI, AWS, Azure, GCP (cloud load balancers)

### API VIP
**Purpose**: Kubernetes API server endpoint

**FQDN**: `api.<cluster-name>.<base-domain>`
**Port**: 6443
**Protocol**: HTTPS

**Requirements**:
- Must be in same subnet as nodes
- Not assigned to any device
- Reserved in DHCP (if using DHCP)

### Ingress VIP
**Purpose**: Application ingress/routes endpoint

**FQDN**: `*.apps.<cluster-name>.<base-domain>` (wildcard DNS)
**Ports**: 80 (HTTP), 443 (HTTPS)
**Protocol**: HTTP/HTTPS

**Requirements**:
- Same subnet as nodes
- Not assigned to any device
- Separate from API VIP (recommended)

### VIP Failover Mechanism
- Keepalived manages VIP failover
- Virtual Router Redundancy Protocol (VRRP)
- Automatic failover if node fails
- Requires Layer 2 connectivity

---

## DNS Requirements

### Required DNS Records

**API Endpoint**:
```
api.<cluster-name>.<base-domain>.  A  <api-vip or load-balancer-ip>
```

**Wildcard Ingress**:
```
*.apps.<cluster-name>.<base-domain>.  A  <ingress-vip or load-balancer-ip>
```

**Internal etcd** (for HA clusters):
```
etcd-0.<cluster-name>.<base-domain>.  A  <master-0-ip>
etcd-1.<cluster-name>.<base-domain>.  A  <master-1-ip>
etcd-2.<cluster-name>.<base-domain>.  A  <master-2-ip>
```

**SRV Records** (for etcd discovery):
```
_etcd-server-ssl._tcp.<cluster-name>.<base-domain>. SRV 0 10 2380 etcd-0.<cluster-name>.<base-domain>.
_etcd-server-ssl._tcp.<cluster-name>.<base-domain>. SRV 0 10 2380 etcd-1.<cluster-name>.<base-domain>.
_etcd-server-ssl._tcp.<cluster-name>.<base-domain>. SRV 0 10 2380 etcd-2.<cluster-name>.<base-domain>.
```

### DNS Server Configuration
- Use corporate DNS or public DNS (e.g., 8.8.8.8, 1.1.1.1)
- DNS must be accessible from all nodes
- Forward and reverse DNS resolution recommended

---

## Firewall and Port Requirements

### Control Plane Nodes (Masters)

**Inbound**:
- 6443/TCP - Kubernetes API
- 22623/TCP - Machine config server
- 2379-2380/TCP - etcd
- 10250-10259/TCP - Kubelet, kube-scheduler, kube-controller-manager
- 9000-9999/TCP - Host-level services (node exporter, etc.)
- 30000-32767/TCP - NodePort services

**Outbound**:
- 443/TCP - HTTPS (image registry, telemetry)
- 80/TCP - HTTP (package repositories)
- 123/UDP - NTP

### Worker Nodes

**Inbound**:
- 10250/TCP - Kubelet
- 9000-9999/TCP - Host-level services
- 30000-32767/TCP - NodePort services

**Outbound**:
- Same as control plane

### Between Nodes
- All nodes must communicate on all ports
- VXLAN: 4789/UDP (for OVN-Kubernetes)
- Geneve: 6081/UDP (for OVN-Kubernetes)

---

## Network Isolation and Policies

### NetworkPolicy
Control pod-to-pod traffic within cluster.

**Example**: Deny all ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

**Example**: Allow from same namespace
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
spec:
  podSelector: {}
  ingress:
  - from:
    - podSelector: {}
```

### Egress Firewall
Control pod egress to external networks.

**Example**: Deny egress to specific CIDR
```yaml
apiVersion: k8s.ovn.org/v1
kind: EgressFirewall
metadata:
  name: default
  namespace: myproject
spec:
  egress:
  - type: Deny
    to:
      cidrSelector: 192.168.1.0/24
```

---

## Multi-Cluster Networking

### Submariner
**Purpose**: Connect pods across multiple clusters

**Use Cases**:
- Multi-cluster application communication
- Disaster recovery across clusters
- Hybrid cloud deployments

**Network Requirements**:
- Non-overlapping cluster/service networks
- IPsec or WireGuard tunnels
- Gateway nodes with public IPs or VPN

**CIDR Conflicts**:
⚠️ **CRITICAL**: Ensure cluster networks don't overlap when using Submariner

**Default CIDRs**:
- Cluster 1: `10.128.0.0/14` (pods), `172.30.0.0/16` (services)
- Cluster 2: `10.132.0.0/14` (pods), `172.31.0.0/16` (services)

**Planning**:
```
Cluster A:
  clusterNetwork: 10.128.0.0/14
  serviceNetwork: 172.30.0.0/16

Cluster B:
  clusterNetwork: 10.132.0.0/14
  serviceNetwork: 172.31.0.0/16

Cluster C:
  clusterNetwork: 10.136.0.0/14
  serviceNetwork: 172.32.0.0/16
```

### Red Hat Advanced Cluster Management (ACM)
**Purpose**: Manage multiple clusters with central policy and networking

**Features**:
- Global policy enforcement
- Network observability across clusters
- Automated certificate management

---

## Network Performance Tuning

### MTU (Maximum Transmission Unit)
**Default**: 1400 (for overlay network)
**Physical Network MTU**: Usually 1500

**Jumbo Frames**: 9000 (for high-performance networks)

**Configuration**:
- Set during installation (cannot change easily after)
- Must match physical network capabilities
- Overhead for encapsulation (VXLAN/Geneve)

### Network Bandwidth
**Recommendations**:
- 1 Gbps minimum
- 10 Gbps for production clusters
- 25+ Gbps for high-performance workloads

### Latency Requirements
- Control plane nodes: < 10ms recommended
- Worker nodes: < 100ms acceptable
- etcd: < 10ms critical (for quorum)

---

## IPv4 vs IPv6

### IPv4 (Default)
**Status**: Fully supported

**Configuration**:
```yaml
networking:
  networkType: OVNKubernetes
  clusterNetwork:
  - cidr: 10.128.0.0/14
  serviceNetwork:
  - 172.30.0.0/16
```

### IPv6
**Status**: Supported (single-stack or dual-stack)

**Single-Stack IPv6**:
```yaml
networking:
  networkType: OVNKubernetes
  clusterNetwork:
  - cidr: fd01::/48
  serviceNetwork:
  - fd02::/112
```

### Dual-Stack (IPv4 + IPv6)
**Status**: Supported with OVN-Kubernetes

**Installation Configuration**:
```yaml
networking:
  networkType: OVNKubernetes
  clusterNetwork:
  - cidr: 10.128.0.0/14
  - cidr: fd01::/48
  serviceNetwork:
  - 172.30.0.0/16
  - fd02::/112
```

**Pod Configuration for Dual-Stack**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: dual-stack-pod
spec:
  containers:
  - name: app
    image: registry.access.redhat.com/ubi9/ubi:latest
```

Pods automatically get both IPv4 and IPv6 addresses. Check with:
```bash
oc exec dual-stack-pod -- ip addr show
```

**Service Configuration**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: dual-stack-service
spec:
  ipFamilyPolicy: RequireDualStack  # or PreferDualStack, SingleStack
  ipFamilies:
  - IPv4
  - IPv6
  selector:
    app: myapp
  ports:
  - port: 80
```

**IP Family Policies**:
- `SingleStack`: IPv4 only (default behavior)
- `PreferDualStack`: Dual-stack if available, fallback to single
- `RequireDualStack`: Dual-stack required, fail if not available

**Considerations**:
- Must be configured at cluster installation (cannot change post-install)
- All nodes must have IPv6 connectivity
- External services must support IPv6 if using dual-stack ingress

---

## Egress IP

Control source IP for pod egress traffic to external networks.

**Use Cases**:
- Firewall allowlist requires predictable source IPs
- Application licensing based on source IP
- Audit/compliance requirements

### Configure Egress IP

**1. Label Nodes** (egress traffic will use these nodes):
```bash
oc label node <node-name> k8s.ovn.org/egress-assignable=""
```

**2. Create EgressIP**:
```yaml
apiVersion: k8s.ovn.org/v1
kind: EgressIP
metadata:
  name: egress-prod
spec:
  egressIPs:
  - 192.168.1.200  # IP must be in node network, not in use
  - 192.168.1.201  # Optional: additional IPs for HA
  namespaceSelector:
    matchLabels:
      env: production
  podSelector:
    matchLabels:
      app: backend
```

**3. Verify**:
```bash
# Check EgressIP status
oc get egressip egress-prod

# Test from pod
oc exec -it <pod-name> -- curl ifconfig.me
# Should return 192.168.1.200
```

**High Availability**:
- Specify multiple `egressIPs` for failover
- Label multiple nodes for distribution
- OVN-Kubernetes automatically balances and fails over

**Limitations**:
- Egress IPs must be in node network subnet
- Cannot overlap with existing IPs (VIPs, node IPs)
- Maximum ~100 egress IPs per cluster (practical limit)

---

## Multi-Network Interfaces (Multus)

Attach multiple network interfaces to pods for advanced networking scenarios.

**Use Cases**:
- Separate data and control plane networks
- High-performance networking (SR-IOV)
- Network isolation (management vs application traffic)
- Legacy applications requiring specific network interfaces

### Install Multus

Multus is included with OpenShift. Enable additional networks:

**1. Create NetworkAttachmentDefinition**:
```yaml
apiVersion: k8s.cni.cncf.io/v1
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-conf
  namespace: default
spec:
  config: '{
    "cniVersion": "0.3.1",
    "type": "macvlan",
    "master": "eth1",
    "mode": "bridge",
    "ipam": {
      "type": "host-local",
      "subnet": "192.168.50.0/24",
      "rangeStart": "192.168.50.200",
      "rangeEnd": "192.168.50.250",
      "gateway": "192.168.50.1"
    }
  }'
```

**2. Attach Network to Pod**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-nic-pod
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-conf
spec:
  containers:
  - name: app
    image: registry.access.redhat.com/ubi9/ubi:latest
```

**3. Verify Multiple Interfaces**:
```bash
oc exec multi-nic-pod -- ip addr show
# Should show: eth0 (default cluster network) + net1 (macvlan)
```

### Network Types

**MACVLAN**:
- Direct network connectivity to physical network
- Each pod gets unique MAC address
- Good for legacy apps requiring Layer 2 connectivity

**IPVLAN**:
- Similar to MACVLAN but shares MAC address
- Better for environments with MAC filtering

**SR-IOV** (Single Root I/O Virtualization):
- Direct hardware passthrough to pods
- Highest performance (bypass kernel network stack)
- Requires SR-IOV capable NICs and SR-IOV Network Operator

**Bridge**:
- Virtual bridge on host
- Pods communicate via bridge
- Good for pod-to-pod on same node

### SR-IOV for High Performance

**Install SR-IOV Operator**:
```bash
oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: sriov-network-operator
  namespace: openshift-sriov-network-operator
spec:
  channel: stable
  name: sriov-network-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF
```

**Configure SR-IOV Network Node Policy**:
```yaml
apiVersion: sriovnetwork.openshift.io/v1
kind: SriovNetworkNodePolicy
metadata:
  name: policy-1
  namespace: openshift-sriov-network-operator
spec:
  nodeSelector:
    feature.node.kubernetes.io/network-sriov.capable: "true"
  resourceName: sriovnic1
  numVfs: 8  # Number of virtual functions
  nicSelector:
    vendor: "8086"  # Intel
    deviceID: "158b"
    rootDevices:
    - "0000:02:00.0"
```

**Create SR-IOV Network**:
```yaml
apiVersion: sriovnetwork.openshift.io/v1
kind: SriovNetwork
metadata:
  name: sriov-network-1
  namespace: openshift-sriov-network-operator
spec:
  networkNamespace: default
  ipam: '{
    "type": "host-local",
    "subnet": "10.56.217.0/24"
  }'
  resourceName: sriovnic1
```

**Use in Pod**:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: sriov-pod
spec:
  containers:
  - name: app
    image: registry.access.redhat.com/ubi9/ubi:latest
    resources:
      requests:
        openshift.io/sriovnic1: "1"
      limits:
        openshift.io/sriovnic1: "1"
```

---

## Common Network Issues

### Issue: Pods Cannot Reach Each Other
**Causes**:
- Network policy blocking traffic
- CNI plugin not functioning
- Node firewall rules

**Resolution**:
1. Check network policies: `oc get networkpolicy -A`
2. Verify CNI pods: `oc get pods -n openshift-ovn-kubernetes`
3. Check node iptables rules

### Issue: Cannot Access Cluster API
**Causes**:
- API VIP not configured correctly
- DNS not resolving `api.<cluster>.<domain>`
- Firewall blocking port 6443

**Resolution**:
1. Verify VIP: `ping api.<cluster>.<domain>`
2. Check DNS: `nslookup api.<cluster>.<domain>`
3. Test port: `nc -zv api.<cluster>.<domain> 6443`

### Issue: Ingress Routes Not Working
**Causes**:
- Ingress VIP misconfigured
- Wildcard DNS not configured
- Router pods not running

**Resolution**:
1. Verify Ingress VIP
2. Check wildcard DNS: `nslookup test.apps.<cluster>.<domain>`
3. Check router pods: `oc get pods -n openshift-ingress`

### Issue: Slow Network Performance
**Causes**:
- MTU mismatch
- Network congestion
- Insufficient bandwidth

**Resolution**:
1. Check MTU settings
2. Monitor bandwidth: `iftop` or `iperf3`
3. Review network policies (overhead)

---

## Best Practices

### Planning
- ✅ Plan CIDR ranges before installation (cannot easily change)
- ✅ Avoid overlaps with existing networks
- ✅ Reserve adequate IP space for growth
- ✅ Document network architecture

### Security
- ✅ Use NetworkPolicies to restrict traffic
- ✅ Implement egress firewalls for sensitive workloads
- ✅ Limit NodePort exposure
- ✅ Use private networks for production

### Performance
- ✅ Use jumbo frames if physical network supports
- ✅ Ensure adequate bandwidth between nodes
- ✅ Monitor network latency (especially for etcd)
- ✅ Consider SR-IOV for high-performance workloads

### Multi-Cluster
- ✅ Plan non-overlapping CIDRs from the start
- ✅ Document CIDR allocations
- ✅ Use IP address management (IPAM) tools
- ✅ Test connectivity before full deployment

---

## Network CIDR Planning Template

```
Organization: <Your Company>
Date: <YYYY-MM-DD>

Global Allocations:
  Corporate Network: 10.0.0.0/8
  OpenShift Clusters: 10.128.0.0/10

Cluster Allocations:
  Production Cluster A:
    Cluster Network: 10.128.0.0/14
    Service Network: 172.30.0.0/16
    Machine Network: 192.168.10.0/24
    API VIP: 192.168.10.100
    Ingress VIP: 192.168.10.101

  Production Cluster B:
    Cluster Network: 10.132.0.0/14
    Service Network: 172.31.0.0/16
    Machine Network: 192.168.20.0/24
    API VIP: 192.168.20.100
    Ingress VIP: 192.168.20.101

  Development Cluster:
    Cluster Network: 10.136.0.0/14
    Service Network: 172.32.0.0/16
    Machine Network: 192.168.30.0/24
    API VIP: 192.168.30.100
    Ingress VIP: 192.168.30.101
```

---

## References

- [OpenShift Networking Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/networking/)
- [OVN-Kubernetes Documentation](https://docs.redhat.com/en/documentation/openshift_container_platform/4.18/html/networking/ovn-kubernetes-network-plugin)
- [Static Networking Guide](./static-networking-guide.md)
- [Submariner Documentation](https://submariner.io/)
- [NetworkPolicy Examples](https://github.com/ahmetb/kubernetes-network-policy-recipes)
- [Input Validation Guide](./input-validation-guide.md)

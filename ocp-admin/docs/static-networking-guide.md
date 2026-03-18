# Static Network Configuration Guide for OpenShift Assisted Installer

## Overview

This guide provides comprehensive instructions for configuring static networking for OpenShift cluster hosts using the Red Hat Assisted Installer. Static networking is required when DHCP is not available or when you need precise control over network configuration.

**When to use static networking**:
- DHCP is not available on your network
- Security policies require static IP assignments
- You need VLANs, network bonding, or custom routing
- Air-gapped or restricted network environments

**When to use DHCP** (simpler):
- DHCP server is available and can provide IPs
- Network is straightforward without VLANs/bonding
- You want faster deployment with less configuration

---

## Three-Tier Configuration Model

We provide three configuration tiers based on complexity:

| Tier | Use Case | Complexity | Features |
|------|----------|------------|----------|
| **Simple Mode** | Basic static IP + gateway + DNS | Low | Single interface, basic routing |
| **Advanced Mode** | Enterprise networks with VLANs, bonding | High | VLANs, bonding, custom routes |
| **Manual Mode** | Expert users with pre-prepared configs | Expert | Full NMState YAML control |

**Choose your tier**:
- **Simple Mode (Recommended)**: If you just need static IPs and basic routing
- **Advanced Mode**: If you have VLANs, need network bonding, or complex routing
- **Manual Mode**: If you're an expert and already have NMState YAML prepared

---

## How Assisted Installer Applies Network Configs

**Critical Concept**: The Assisted Installer applies static network configurations **in the order hosts boot**.

**Example**:
- You create 3 network configs (indices 0, 1, 2)
- You boot 3 servers from the cluster ISO
- **First server to boot** → Gets config at index 0
- **Second server to boot** → Gets config at index 1
- **Third server to boot** → Gets config at index 2

**Important**:
- Boot hosts in the order you configured them
- Label your physical servers clearly (Host 1, Host 2, etc.)
- If you boot hosts out of order, they'll get mismatched configs

---

## Simple Mode Workflow

**Best for**: Straightforward networks with one interface per host, no VLANs or bonding.

### Step 1: How Many Hosts?

Determine how many hosts need static networking:
- **SNO**: 1 host
- **HA Compact** (3 masters, no workers): 3 hosts
- **HA Standard** (3 masters + N workers): 3 + N hosts

### Step 2: Configure Each Host (Simple Mode)

For each host, gather:

#### Required Information:
1. **Interface Name**: `eth0`, `eno1`, `enp1s0` (default: `eth0`)
2. **MAC Address**: Format `XX:XX:XX:XX:XX:XX` (e.g., `52:54:00:6b:45:23`)
3. **IPv4 Address**: e.g., `192.168.1.10`
4. **Subnet Prefix**: e.g., `24` (for /24 = 255.255.255.0)
5. **Gateway**: e.g., `192.168.1.1`
6. **DNS Server(s)**: e.g., `8.8.8.8` (can provide multiple)

#### Example - Host 1:
```
Interface: eth0
MAC Address: 52:54:00:6b:45:01
IP Address: 192.168.1.10
Subnet: /24
Gateway: 192.168.1.1
DNS: 8.8.8.8, 8.8.4.4
```

### Step 3: Generate NMState YAML (Simple Mode)

Use the `generate_nmstate_yaml` MCP tool:

```json
{
  "params": {
    "ethernet_ifaces": [
      {
        "name": "eth0",
        "mac_address": "52:54:00:6b:45:01",
        "ipv4_address": {
          "address": "192.168.1.10",
          "cidr_length": 24
        }
      }
    ],
    "dns": {
      "dns_servers": ["8.8.8.8", "8.8.4.4"]
    },
    "routes": [
      {
        "destination": "0.0.0.0/0",
        "next_hop_address": "192.168.1.1",
        "next_hop_interface": "eth0",
        "table_id": 254
      }
    ]
  }
}
```

**Expected Output**: NMState YAML

```yaml
interfaces:
  - name: eth0
    type: ethernet
    state: up
    mac-address: 52:54:00:6b:45:01
    ipv4:
      enabled: true
      address:
        - ip: 192.168.1.10
          prefix-length: 24
      dhcp: false
dns-resolver:
  config:
    server:
      - 8.8.8.8
      - 8.8.4.4
routes:
  config:
    - destination: 0.0.0.0/0
      next-hop-address: 192.168.1.1
      next-hop-interface: eth0
      table-id: 254
```

### Step 4: Validate YAML

Use `validate_nmstate_yaml` tool to verify syntax.

**Expected Result**: "YAML is valid"

### Step 5: Apply to Cluster

Use `alter_static_network_config_nmstate_for_host`:
- **First host**: `index = None` (append)
- **Subsequent hosts**: `index = None` (append)
- **Update existing**: `index = 0, 1, 2...` (replace)

---

## Advanced Mode Workflow

**Best for**: Enterprise networks with VLANs, network bonding, multiple interfaces, custom routing.

### Additional Capabilities:

1. **Multiple Ethernet Interfaces**: Configure 2+ interfaces per host
2. **VLAN Tagging**: Segment network traffic (VLAN IDs 1-4094)
3. **Network Bonding**: Aggregate interfaces for redundancy
   - Modes: active-backup, balance-rr, balance-xor, 802.3ad, etc.
4. **Custom Routes**: Multiple routes with metrics
5. **Interface Without IP**: Base interfaces for VLANs/bonds

### Advanced Example: Bonded Interface with VLAN

**Scenario**: 2 physical interfaces bonded, VLAN 100 on top for cluster traffic

#### Configuration:

**Interfaces**:
- `eth0` (MAC: `52:54:00:6b:45:01`) - No IP (bond port)
- `eth1` (MAC: `52:54:00:6b:45:02`) - No IP (bond port)
- `bond0` - Active-backup bond of eth0+eth1, no IP
- `vlan100` - VLAN 100 on bond0, IP `10.100.1.10/24`

**generate_nmstate_yaml call**:

```json
{
  "params": {
    "ethernet_ifaces": [
      {
        "name": "eth0",
        "mac_address": "52:54:00:6b:45:01"
      },
      {
        "name": "eth1",
        "mac_address": "52:54:00:6b:45:02"
      }
    ],
    "bond_ifaces": [
      {
        "name": "bond0",
        "mode": "active-backup",
        "port_interface_names": ["eth0", "eth1"]
      }
    ],
    "vlan_ifaces": [
      {
        "name": "vlan100",
        "vlan_id": 100,
        "base_interface_name": "bond0",
        "ipv4_address": {
          "address": "10.100.1.10",
          "cidr_length": 24
        }
      }
    ],
    "dns": {
      "dns_servers": ["10.100.1.1"]
    },
    "routes": [
      {
        "destination": "0.0.0.0/0",
        "next_hop_address": "10.100.1.1",
        "next_hop_interface": "vlan100",
        "table_id": 254
      }
    ]
  }
}
```

**Result**: NMState YAML with bonded interface + VLAN

---

## Manual Mode Workflow

**Best for**: Experts who already have NMState YAML prepared or need configurations beyond what generate_nmstate_yaml supports.

### Requirements:

1. **Valid NMState YAML**: Must conform to NMState schema
2. **Proper formatting**: YAML syntax must be correct
3. **Complete configuration**: All required fields present

### Steps:

1. **Prepare YAML**: Create NMState YAML using your preferred method
2. **Validate**: Use `validate_nmstate_yaml` tool
3. **Apply**: Use `alter_static_network_config_nmstate_for_host`

### Example Manual YAML:

```yaml
interfaces:
  - name: eth0
    type: ethernet
    state: up
    mac-address: 52:54:00:6b:45:01
    ipv4:
      enabled: true
      address:
        - ip: 192.168.1.10
          prefix-length: 24
      dhcp: false
  - name: eth1
    type: ethernet
    state: up
    mac-address: 52:54:00:6b:45:02
    ipv4:
      enabled: true
      address:
        - ip: 10.0.0.10
          prefix-length: 24
      dhcp: false
dns-resolver:
  config:
    server:
      - 8.8.8.8
    search:
      - example.com
routes:
  config:
    - destination: 0.0.0.0/0
      next-hop-address: 192.168.1.1
      next-hop-interface: eth0
      table-id: 254
      metric: 100
    - destination: 10.0.0.0/8
      next-hop-address: 10.0.0.1
      next-hop-interface: eth1
      table-id: 254
      metric: 200
```

---

## NMState YAML Reference

### Supported Interface Types:

- **ethernet**: Physical network interfaces
- **bond**: Aggregated interfaces for redundancy
- **vlan**: VLAN-tagged virtual interfaces

### Bond Modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `active-backup` | One active, others standby | **Recommended** - Simple failover |
| `balance-rr` | Round-robin packets | Load balancing |
| `balance-xor` | XOR hash distribution | Load balancing with redundancy |
| `broadcast` | Transmit on all interfaces | Fault tolerance |
| `802.3ad` | IEEE 802.3ad LACP | Requires switch support |
| `balance-tlb` | Adaptive transmit load balance | Outbound load balancing |
| `balance-alb` | Adaptive load balance | Full load balancing |

### Route Parameters:

- **destination**: CIDR notation (e.g., `0.0.0.0/0` for default route)
- **next_hop_address**: Gateway IP
- **next_hop_interface**: Interface name
- **table_id**: Routing table (254 = main table)
- **metric**: Route priority (lower = higher priority)

### DNS Configuration:

- **dns_servers**: Array of DNS server IPs (required)
- **dns_search_domains**: Array of search domains (optional)

---

## Troubleshooting

### Issue: Host not getting network config

**Symptoms**: Host boots but has no network connectivity

**Causes**:
1. Host booted in wrong order (got wrong config index)
2. MAC address mismatch
3. Invalid YAML syntax

**Resolution**:
1. Check MAC address on physical host: `ip link show`
2. Verify boot order matches configuration order
3. Validate YAML with `validate_nmstate_yaml`
4. Check cluster events: `cluster_events` tool

---

### Issue: Invalid YAML error

**Symptoms**: `validate_nmstate_yaml` returns error

**Common Mistakes**:
1. **Indentation**: YAML requires precise indentation (use 2 spaces)
2. **MAC address format**: Must be `XX:XX:XX:XX:XX:XX`
3. **IP address format**: Must be valid IPv4
4. **Missing required fields**: Ensure all required fields present

**Resolution**:
1. Use `generate_nmstate_yaml` to create valid baseline
2. Check YAML syntax with online validator
3. Compare against examples in this guide

---

### Issue: Network connectivity works but DNS fails

**Symptoms**: Can ping IPs but not domain names

**Causes**:
1. DNS servers not reachable
2. DNS configuration missing/incorrect

**Resolution**:
1. Verify DNS servers are reachable: `ping 8.8.8.8`
2. Check DNS config in YAML has correct IPs
3. Ensure dns-resolver section is properly formatted

---

### Issue: Bond interface not coming up

**Symptoms**: Bond shows "down" state

**Causes**:
1. Port interfaces not properly configured
2. Incompatible bond mode with switch configuration
3. Port interfaces have IP addresses (should only be on bond)

**Resolution**:
1. Verify port interfaces exist and match names in config
2. For 802.3ad mode, ensure switch has LACP enabled
3. Remove IP addresses from port interfaces
4. Use `active-backup` mode for simplest configuration

---

### Issue: VLAN traffic not working

**Symptoms**: VLAN interface has IP but no connectivity

**Causes**:
1. Switch port not configured for VLAN trunking
2. Base interface not up
3. VLAN ID mismatch with switch configuration

**Resolution**:
1. Verify switch port is trunk mode with allowed VLANs
2. Ensure base interface is "up" and has no IP
3. Confirm VLAN ID matches switch configuration
4. Check VLAN tag with: `tcpdump -i <interface> -e`

---

## Best Practices

### 1. Use Simple Mode When Possible
- Reduces complexity and error potential
- Faster to configure
- Easier to troubleshoot

### 2. Label Physical Servers
- Physically label servers as "Host 1", "Host 2", etc.
- Boot in labeled order to match config indices
- Document MAC addresses before booting

### 3. Validate Before Applying
- Always use `validate_nmstate_yaml` before applying
- Test one host configuration before scaling to all hosts
- Keep backup of working YAML configurations

### 4. Network Design
- Keep IP ranges consistent (e.g., masters: .10-.12, workers: .20-.29)
- Use sequential IPs for easier troubleshooting
- Document your IP allocation scheme

### 5. Bond Configuration
- Use `active-backup` mode unless you have specific needs
- Ensure both NICs are on same physical switch or have proper redundancy
- For 802.3ad, coordinate with network team on switch config

### 6. VLAN Usage
- Use VLANs for network segmentation and security
- Coordinate VLAN IDs with network team
- Ensure switch ports are configured for trunking

### 7. DNS Configuration
- Provide at least 2 DNS servers for redundancy
- Use reliable DNS servers (corporate or public like 8.8.8.8)
- Add search domains if using short hostnames

### 8. Routing
- Default route (0.0.0.0/0) should point to your network gateway
- Lower metric = higher priority for multiple routes
- Table ID 254 is the main routing table (standard)

---

## Examples

### Example 1: SNO - Single Interface

**Scenario**: Edge deployment, single interface, static IP

```
Host 1:
- Interface: eth0 (52:54:00:6b:45:01)
- IP: 192.168.1.100/24
- Gateway: 192.168.1.1
- DNS: 8.8.8.8
```

**generate_nmstate_yaml**:
```json
{
  "params": {
    "ethernet_ifaces": [
      {
        "name": "eth0",
        "mac_address": "52:54:00:6b:45:01",
        "ipv4_address": {"address": "192.168.1.100", "cidr_length": 24}
      }
    ],
    "dns": {"dns_servers": ["8.8.8.8"]},
    "routes": [
      {
        "destination": "0.0.0.0/0",
        "next_hop_address": "192.168.1.1",
        "next_hop_interface": "eth0",
        "table_id": 254
      }
    ]
  }
}
```

---

### Example 2: HA - 3 Hosts, Simple Networking

**Scenario**: HA cluster, 3 masters, no workers, basic networking

```
Host 1: 192.168.1.10/24, MAC 52:54:00:6b:45:01
Host 2: 192.168.1.11/24, MAC 52:54:00:6b:45:02
Host 3: 192.168.1.12/24, MAC 52:54:00:6b:45:03
Gateway: 192.168.1.1
DNS: 192.168.1.53, 8.8.8.8
```

**Create 3 configurations** (indices 0, 1, 2), each with different IP/MAC.

---

### Example 3: HA - Bonded + VLAN

**Scenario**: Production cluster, redundant network, VLAN segmentation

```
Each host has:
- eth0 + eth1 bonded (active-backup)
- VLAN 100 on bond0 for cluster traffic
- VLAN 200 on bond0 for storage traffic

Host 1:
- eth0: 52:54:00:6b:45:01 (no IP)
- eth1: 52:54:00:6b:45:02 (no IP)
- bond0: active-backup (no IP)
- vlan100: 10.100.1.10/24 (cluster network)
- vlan200: 10.200.1.10/24 (storage network)
```

**generate_nmstate_yaml** for Host 1:
```json
{
  "params": {
    "ethernet_ifaces": [
      {"name": "eth0", "mac_address": "52:54:00:6b:45:01"},
      {"name": "eth1", "mac_address": "52:54:00:6b:45:02"}
    ],
    "bond_ifaces": [
      {
        "name": "bond0",
        "mode": "active-backup",
        "port_interface_names": ["eth0", "eth1"]
      }
    ],
    "vlan_ifaces": [
      {
        "name": "vlan100",
        "vlan_id": 100,
        "base_interface_name": "bond0",
        "ipv4_address": {"address": "10.100.1.10", "cidr_length": 24}
      },
      {
        "name": "vlan200",
        "vlan_id": 200,
        "base_interface_name": "bond0",
        "ipv4_address": {"address": "10.200.1.10", "cidr_length": 24}
      }
    ],
    "dns": {"dns_servers": ["10.100.1.1", "8.8.8.8"]},
    "routes": [
      {
        "destination": "0.0.0.0/0",
        "next_hop_address": "10.100.1.1",
        "next_hop_interface": "vlan100",
        "table_id": 254
      }
    ]
  }
}
```

---

## Quick Reference: MCP Tools

### generate_nmstate_yaml
**Purpose**: Generate NMState YAML from structured parameters

**Parameters**:
- `params.ethernet_ifaces` (required): Array of ethernet interfaces
- `params.vlan_ifaces` (optional): Array of VLAN interfaces
- `params.bond_ifaces` (optional): Array of bond interfaces
- `params.dns` (optional): DNS configuration
- `params.routes` (optional): Routing configuration

**Returns**: NMState YAML string

---

### validate_nmstate_yaml
**Purpose**: Validate NMState YAML syntax

**Parameters**:
- `nmstate_yaml` (required): YAML string to validate

**Returns**: "YAML is valid" or error message

---

### alter_static_network_config_nmstate_for_host
**Purpose**: Add, update, or delete host network configuration

**Parameters**:
- `cluster_id` (required): Cluster UUID
- `index` (required): Config index (None to append, 0-N to update/delete)
- `new_nmstate_yaml` (required): YAML string (None to delete)

**Usage**:
- **Add new config**: `index=None`, `new_nmstate_yaml=<yaml>`
- **Update config**: `index=0`, `new_nmstate_yaml=<yaml>`
- **Delete config**: `index=0`, `new_nmstate_yaml=None`

**Returns**: Updated infrastructure environment

---

### list_static_network_config
**Purpose**: View all configured host network configurations

**Parameters**:
- `cluster_id` (required): Cluster UUID

**Returns**: JSON array of all static network configs

---

## Glossary

- **NMState**: Network configuration format used by RHEL and OpenShift
- **VLAN**: Virtual LAN for network segmentation (802.1Q)
- **Bonding**: Link aggregation for redundancy and bandwidth
- **LACP**: Link Aggregation Control Protocol (802.3ad)
- **CIDR**: Classless Inter-Domain Routing notation (e.g., /24)
- **MAC Address**: Media Access Control address (hardware address)
- **Routing Table**: Kernel routing table (254 = main table)
- **Metric**: Route priority value (lower = higher priority)

---

## Additional Resources

- **NMState Documentation**: https://nmstate.io/
- **RHEL Networking Guide**: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/configuring_and_managing_networking/
- **OpenShift Networking**: https://docs.openshift.com/container-platform/latest/networking/
- **IEEE 802.3ad (LACP)**: https://www.ieee802.org/3/hssg/public/apr07/frazier_01_0407.pdf
- **troubleshooting.md**: See `ocp-admin/docs/troubleshooting.md` for cluster-specific issues

---

**Last Updated**: 2026-02-13

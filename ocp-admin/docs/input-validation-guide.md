# Input Validation Guide

Validation requirements for cluster configuration parameters before OpenShift installation.

---

## Cluster Name

**Requirements**:
- Length: 1-54 characters
- Must start with a lowercase letter
- Only lowercase letters (a-z), numbers (0-9), and hyphens (-) allowed
- No consecutive hyphens (`--`)
- No leading or trailing hyphens
- No spaces or special characters

**Valid Examples**:
- `production-ocp`
- `edge-site-01`
- `dev-cluster`
- `sno-factory-floor-3`

**Invalid Examples**:
- `Production-OCP` (uppercase not allowed)
- `-edge-site` (starts with hyphen)
- `cluster_name` (underscore not allowed)
- `my cluster` (space not allowed)
- `edge--site` (consecutive hyphens)

**Validation Pattern** (regex):
```
^[a-z][a-z0-9-]{0,53}$
```

Additional checks:
- No `--` substring
- Does not end with `-`

---

## Base Domain

**Requirements**:
- Valid DNS domain format
- Must contain at least one dot (`.`)
- No underscores or spaces
- Lowercase recommended (though uppercase technically allowed)
- Valid TLD (top-level domain)

**Valid Examples**:
- `example.com`
- `ocp.mycompany.org`
- `edge.local`
- `production.cluster.internal`

**Invalid Examples**:
- `example` (no TLD)
- `my_domain.com` (underscore not allowed)
- `my domain.com` (space not allowed)
- `example..com` (consecutive dots)

**Validation Pattern** (regex):
```
^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,}$
```

**DNS Considerations**:
- Domain must be resolvable if using external DNS
- For internal/private clusters, `.local` or internal domains are acceptable
- Wildcard DNS entry required: `*.apps.<cluster-name>.<base-domain>`

---

## SSH Public Key

**Requirements**:
- Must be a valid SSH public key (not private key)
- Single line (no newlines)
- Valid key types: `ssh-rsa`, `ssh-ed25519`, `ecdsa-sha2-nistp256`, `ecdsa-sha2-nistp384`, `ecdsa-sha2-nistp521`, `ssh-dss`
- Base64-encoded key data
- Format: `<type> <key-data> [comment]`

**How to Get Your Public Key**:
```bash
# RSA key
cat ~/.ssh/id_rsa.pub

# Ed25519 key (recommended)
cat ~/.ssh/id_ed25519.pub
```

**Valid Example**:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl user@example.com
```

**Invalid Examples**:
- Private key content (contains `BEGIN RSA PRIVATE KEY`)
- Multi-line key
- Key without type prefix
- Malformed base64 data

**Security Warning**:
- NEVER provide your private key (files without `.pub` extension)
- Private keys contain `-----BEGIN ... PRIVATE KEY-----`
- Only share public keys (`.pub` files)

**Validation Steps**:
1. Check key starts with valid type (`ssh-rsa`, `ssh-ed25519`, etc.)
2. Verify no private key markers present
3. Validate base64 encoding of key data
4. Ensure single line (no `\n` or `\r`)
5. Check minimum 2 parts (type + key-data)

---

## Virtual IPs (VIPs)

**When Required**:
- High-Availability (HA) clusters only
- Platforms: baremetal, vsphere, nutanix
- NOT required for: SNO clusters, OCI platform

**Requirements**:
- Valid IPv4 format: `X.X.X.X` where X is 0-255
- Must be in same subnet as cluster nodes
- Must NOT be assigned to any physical device
- Must be reachable from all cluster nodes
- Should not be DHCP-assigned addresses

**Two VIPs Required**:
1. **API VIP**: Kubernetes API server endpoint
2. **Ingress VIP**: Application ingress/routes endpoint

**Valid Examples**:
```
Machine Network: 192.168.1.0/24
API VIP: 192.168.1.100
Ingress VIP: 192.168.1.101
```

**Invalid IP Addresses**:
- `0.0.0.0` (network address)
- `255.255.255.255` (broadcast)
- `127.x.x.x` (loopback)
- `169.254.x.x` (link-local)
- `224.0.0.0` - `239.255.255.255` (multicast)

**Validation Pattern** (regex):
```
^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$
```

**Additional Validation**:
- API VIP and Ingress VIP should be different
- VIPs should not conflict with DHCP range
- Reserve VIPs in DHCP server or use static IP range

---

## OpenShift Version

**Requirements**:
- Must be available in Assisted Installer
- Recommended: "Full Support" versions only
- Avoid: "End of Life", "Release Candidate" versions

**Support Levels** (from `list_versions` tool):
- **Full Support**: Production-ready, Generally Available (GA) ✅ **Recommended**
- **Maintenance Support**: In maintenance mode, limited updates
- **Extended Support**: Extended support lifecycle
- **Release Candidate**: Beta/pre-release ⚠️ **NOT for production**
- **End of Life**: No longer supported ❌ **Avoid**

**Version Format**: `X.Y.Z` (e.g., `4.18.2`)

**Selection Strategy**:
- **Production**: Use latest "Full Support" version
- **Development/Testing**: Can use "Release Candidate" if needed
- **Long-term Support**: Check for "Extended Support" versions

---

## CPU Architecture

**Supported Architectures**:
- `x86_64` - Intel/AMD 64-bit (most common) ✅ **Default**
- `aarch64` - ARM 64-bit (edge devices, cloud)
- `ppc64le` - IBM POWER little-endian
- `s390x` - IBM Z mainframe

**Validation**: Must be one of the above values

**Considerations**:
- All cluster nodes MUST use the same architecture
- Some operators may have limited architecture support
- Container images must be available for chosen architecture

---

## Static Network Configuration (Optional)

**When to Use**:
- DHCP not available on network
- Need predictable IP addresses
- Advanced networking requirements (VLANs, bonding)

**Interface Name**:
- Common: `eth0`, `ens3`, `enp1s0`
- Check with: `ip link show`

**MAC Address**:
- Format: `XX:XX:XX:XX:XX:XX` (hex digits, case-insensitive)
- Example: `52:54:00:6b:45:01`
- Get from: `ip link show` or BIOS/iDRAC

**IPv4 Address**:
- Valid IPv4 format
- Should be unique per host
- Must be in same subnet as VIPs (if HA cluster)

**Subnet Prefix**:
- CIDR notation: 1-32
- Common: `24` (255.255.255.0), `16` (255.255.0.0)

**Gateway**:
- Valid IPv4 in same subnet
- Typically first or last IP in range
- Example: `192.168.1.1`

**DNS Servers**:
- One or more valid IPv4 addresses
- Comma-separated if multiple
- Example: `8.8.8.8` or `8.8.8.8,8.8.4.4`

**NMState YAML Validation**:
- Valid YAML syntax
- Required fields: interfaces, routes, dns-resolver
- MAC addresses must match physical hardware
- IP addresses must not conflict

---

## Pre-Installation Checklist

Before creating cluster, verify:

**Required Information**:
- ✅ Cluster name (validated)
- ✅ Base domain (validated)
- ✅ SSH public key (validated)
- ✅ OpenShift version selected (Full Support)
- ✅ CPU architecture matches hardware

**Platform-Specific**:
- ✅ VIPs configured (if HA + baremetal/vsphere/nutanix)
- ✅ Static networking configured (if DHCP unavailable)

**Infrastructure Ready**:
- ✅ Physical/virtual hosts available
- ✅ Hosts meet minimum requirements
- ✅ Network connectivity verified
- ✅ BIOS/firmware configured

**Access**:
- ✅ OFFLINE_TOKEN obtained from Red Hat
- ✅ MCP server configured and responsive
- ✅ Firewall rules configured (if needed)

---

## Common Validation Errors

### Error: "Cluster name already exists"
**Cause**: Cluster with same name already exists in Red Hat Console
**Resolution**: Choose different name or delete existing cluster

### Error: "Invalid base domain"
**Cause**: Domain format invalid or DNS unreachable
**Resolution**: Verify domain format, check DNS resolution

### Error: "SSH key validation failed"
**Cause**: Invalid key format or private key provided
**Resolution**: Verify you're using public key (`.pub` file), check format

### Error: "VIP already in use"
**Cause**: IP address assigned to another device
**Resolution**: Choose different VIP, verify with `ping` or `arping`

### Error: "Version not available"
**Cause**: Selected version not in Assisted Installer catalog
**Resolution**: Run `list_versions` to see available versions

---

## References

- [OpenShift Documentation - Installation Prerequisites](https://docs.redhat.com/en/documentation/openshift_container_platform/)
- [Assisted Installer Documentation](https://docs.redhat.com/en/documentation/assisted_installer_for_openshift_container_platform/)
- [NMState Configuration Guide](./static-networking-guide.md)
- [Platform Requirements](./platforms.md)

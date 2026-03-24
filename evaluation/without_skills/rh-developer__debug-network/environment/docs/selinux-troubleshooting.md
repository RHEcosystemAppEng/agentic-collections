---
title: SELinux Troubleshooting
category: references
sources:
  - title: Red Hat SELinux User's and Administrator's Guide
    url: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/using_selinux/index
    sections: Troubleshooting, Managing confined services
    date_accessed: 2026-02-16
  - title: SELinux Project Wiki
    url: https://selinuxproject.org/page/Main_Page
    sections: Troubleshooting
    date_accessed: 2026-02-16
  - title: Fedora SELinux Guide
    url: https://docs.fedoraproject.org/en-US/quick-docs/selinux-getting-started/
    sections: Troubleshooting
    date_accessed: 2026-02-16
---

# SELinux Troubleshooting

This document provides guidance for diagnosing and resolving SELinux access denials on RHEL/Fedora/CentOS systems.

## Understanding SELinux

### SELinux Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Enforcing** | SELinux policy is enforced, denials are blocked and logged | Production |
| **Permissive** | SELinux policy is not enforced, denials are logged only | Debugging |
| **Disabled** | SELinux is completely disabled | Not recommended |

```bash
# Check current mode
getenforce

# Temporarily switch to permissive (until reboot)
sudo setenforce 0

# Switch back to enforcing
sudo setenforce 1
```

### SELinux Contexts

Every file, process, and port has an SELinux context:

```
user:role:type:level
```

Example: `system_u:object_r:httpd_sys_content_t:s0`

- **user**: SELinux user (system_u, user_u, etc.)
- **role**: Role (object_r for files)
- **type**: Type label (most important for troubleshooting)
- **level**: MLS/MCS level (usually s0)

```bash
# View file context
ls -lZ /path/to/file

# View process context
ps auxZ | grep [process]

# View port context
semanage port -l | grep [port]
```

## Finding SELinux Denials

### Using ausearch

```bash
# Recent denials (last 10 minutes)
sudo ausearch -m AVC -ts recent

# Denials from today
sudo ausearch -m AVC -ts today

# Denials for specific process
sudo ausearch -m AVC -c [command-name]

# Denials involving specific file
sudo ausearch -m AVC -f /path/to/file
```

### Using journalctl

```bash
# SELinux messages in journal
sudo journalctl -t setroubleshoot

# AVC messages
sudo journalctl | grep "avc:  denied"
```

### Using sealert

```bash
# Install setroubleshoot (if not installed)
sudo dnf install setroubleshoot-server

# Analyze all denials
sudo sealert -a /var/log/audit/audit.log

# Interactive analysis
sudo sealert -b
```

## Reading AVC Denials

Example AVC denial:

```
type=AVC msg=audit(1234567890.123:456): avc:  denied  { bind } for  pid=1234 comm="httpd" src=8080 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:unreserved_port_t:s0 tclass=tcp_socket permissive=0
```

**Breakdown:**
| Field | Value | Meaning |
|-------|-------|---------|
| `denied { bind }` | bind | Denied action (bind to socket) |
| `pid=1234` | 1234 | Process ID |
| `comm="httpd"` | httpd | Command name |
| `src=8080` | 8080 | Port number |
| `scontext=...httpd_t...` | httpd_t | Source type (process) |
| `tcontext=...unreserved_port_t...` | unreserved_port_t | Target type (port) |
| `tclass=tcp_socket` | tcp_socket | Object class |

**Translation:** Process `httpd` (type `httpd_t`) was denied permission to `bind` to port `8080` (type `unreserved_port_t`).

## Common Denial Types and Fixes

### Port Binding Denials

**Symptom:** Application cannot bind to non-standard port

**Example denial:**
```
avc: denied { name_bind } for comm="nginx" src=8080 scontext=httpd_t tcontext=unreserved_port_t
```

**Fix:**
```bash
# Add port to allowed type
sudo semanage port -a -t http_port_t -p tcp 8080

# Verify
sudo semanage port -l | grep 8080
```

**Common port types:**
| Port Type | Typical Ports | Used By |
|-----------|---------------|---------|
| `http_port_t` | 80, 443, 8080 | Web servers |
| `postgresql_port_t` | 5432 | PostgreSQL |
| `mysqld_port_t` | 3306 | MySQL/MariaDB |
| `redis_port_t` | 6379 | Redis |
| `mongod_port_t` | 27017 | MongoDB |

### File Access Denials

**Symptom:** Application cannot read/write files

**Example denial:**
```
avc: denied { read } for comm="httpd" name="config.yaml" scontext=httpd_t tcontext=user_home_t
```

**Fix - Change file context:**
```bash
# Set file context pattern
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/myapp(/.*)?"

# Apply the context
sudo restorecon -Rv /srv/myapp

# Verify
ls -lZ /srv/myapp
```

**Common file types:**
| File Type | Access | Use Case |
|-----------|--------|----------|
| `httpd_sys_content_t` | Read | Web content |
| `httpd_sys_rw_content_t` | Read/Write | Web app data |
| `container_file_t` | Container access | Podman volumes |
| `var_log_t` | Log files | Application logs |

### Network Connection Denials

**Symptom:** Application cannot connect to external services

**Example denial:**
```
avc: denied { name_connect } for comm="httpd" dest=5432 scontext=httpd_t tcontext=postgresql_port_t
```

**Fix - Enable boolean:**
```bash
# Allow httpd to connect to network
sudo setsebool -P httpd_can_network_connect on

# Or specifically to databases
sudo setsebool -P httpd_can_network_connect_db on

# List all httpd booleans
sudo getsebool -a | grep httpd
```

**Common booleans:**
| Boolean | Purpose |
|---------|---------|
| `httpd_can_network_connect` | Allow outbound network connections |
| `httpd_can_network_connect_db` | Allow database connections |
| `httpd_can_sendmail` | Allow sending email |
| `httpd_use_nfs` | Allow NFS access |
| `container_manage_cgroup` | Allow container cgroup management |

## Container-Specific Issues

### Podman Volume Mounts

When mounting host directories into containers, SELinux may block access.

**Solutions:**

1. **Shared label (:z)** - Multiple containers can access
   ```bash
   podman run -v /host/path:/container/path:z [image]
   ```

2. **Private label (:Z)** - Only this container can access
   ```bash
   podman run -v /host/path:/container/path:Z [image]
   ```

3. **Manual relabeling:**
   ```bash
   sudo semanage fcontext -a -t container_file_t "/data(/.*)?"
   sudo restorecon -Rv /data
   ```

### Container Booleans

```bash
# Enable container to manage cgroups (for systemd in container)
sudo setsebool -P container_manage_cgroup on

# Allow containers to connect to any port
sudo setsebool -P container_connect_any on

# List all container booleans
sudo getsebool -a | grep container
```

## Troubleshooting Workflow

### Step 1: Confirm SELinux is the Issue

```bash
# Temporarily disable SELinux
sudo setenforce 0

# Test if application works
[test application]

# Re-enable SELinux
sudo setenforce 1
```

If application works with SELinux permissive, SELinux is blocking.

### Step 2: Find the Denial

```bash
# Get recent denials
sudo ausearch -m AVC -ts recent

# Or use sealert for analysis
sudo sealert -a /var/log/audit/audit.log
```

### Step 3: Determine Fix Type

| Denial Type | Fix Approach |
|-------------|--------------|
| Port binding | `semanage port` |
| File access | `semanage fcontext` + `restorecon` |
| Network connection | `setsebool` |
| Process capability | Custom policy or boolean |

### Step 4: Apply Fix

```bash
# For port:
sudo semanage port -a -t [type] -p [tcp/udp] [port]

# For file:
sudo semanage fcontext -a -t [type] "[path](/.*)?"
sudo restorecon -Rv [path]

# For boolean:
sudo setsebool -P [boolean] on
```

### Step 5: Verify

```bash
# Test application
[restart and test]

# Check for new denials
sudo ausearch -m AVC -ts recent
```

## Generating Custom Policies

If no existing type or boolean works, generate a custom policy:

```bash
# Generate policy from recent denials
sudo ausearch -m AVC -ts recent | audit2allow -M mypolicy

# Review the policy
cat mypolicy.te

# Install the policy
sudo semodule -i mypolicy.pp
```

**Warning:** Custom policies should be reviewed carefully. They grant permanent permissions.

## Quick Reference

### Common Commands

```bash
# SELinux status
getenforce
sestatus

# File context
ls -lZ [path]
restorecon -Rv [path]

# Process context
ps auxZ | grep [process]

# Port context
semanage port -l | grep [port]
semanage port -a -t [type] -p tcp [port]

# Booleans
getsebool -a | grep [keyword]
setsebool -P [boolean] on

# File context rules
semanage fcontext -l | grep [path]
semanage fcontext -a -t [type] "[path](/.*)?"

# Audit logs
ausearch -m AVC -ts recent
sealert -a /var/log/audit/audit.log
```

### Common Types for Web Applications

| Resource | Type |
|----------|------|
| Web content (read-only) | `httpd_sys_content_t` |
| Web content (read-write) | `httpd_sys_rw_content_t` |
| Web scripts | `httpd_sys_script_exec_t` |
| Application logs | `httpd_log_t` |
| HTTP ports | `http_port_t` |
| Container files | `container_file_t` |

### Common Booleans for Applications

| Application | Boolean | Purpose |
|-------------|---------|---------|
| Web server | `httpd_can_network_connect` | Outbound connections |
| Web server | `httpd_can_network_connect_db` | Database connections |
| Web server | `httpd_unified` | Unified handling |
| Container | `container_manage_cgroup` | cgroup management |
| Container | `container_connect_any` | Connect to any port |
| NFS | `use_nfs_home_dirs` | NFS home directories |

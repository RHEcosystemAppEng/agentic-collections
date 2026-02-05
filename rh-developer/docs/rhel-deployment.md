# RHEL Deployment Reference

Reference material for deploying applications to standalone RHEL systems.

## Table of Contents

1. [RHEL Version Compatibility](#rhel-version-compatibility)
2. [Systemd Unit Templates](#systemd-unit-templates)
3. [SELinux Configuration](#selinux-configuration)
4. [Firewall Commands](#firewall-commands)
5. [SSH Connection Patterns](#ssh-connection-patterns)
6. [Runtime Package Mapping](#runtime-package-mapping)

---

## RHEL Version Compatibility

| Distribution | Version | Podman | Recommended |
|--------------|---------|--------|-------------|
| RHEL | 8.x | 4.0+ | Production ready |
| RHEL | 9.x | 4.4+ | **Recommended** |
| CentOS Stream | 8 | 4.0+ | Development |
| CentOS Stream | 9 | 4.4+ | Development |
| Rocky Linux | 8.x | 4.0+ | Production ready |
| Rocky Linux | 9.x | 4.4+ | Production ready |
| AlmaLinux | 8.x | 4.0+ | Production ready |
| AlmaLinux | 9.x | 4.4+ | Production ready |
| Fedora | 38+ | 4.6+ | Latest features |

### Version Detection Commands

```bash
# Get RHEL/CentOS version
cat /etc/redhat-release

# Get detailed OS info
cat /etc/os-release

# Check architecture
uname -m

# Check kernel version
uname -r
```

---

## Systemd Unit Templates

### Podman Container Service (Rootful)

```ini
[Unit]
Description=${APP_NAME} Container
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=5
TimeoutStartSec=300
TimeoutStopSec=70

# Pre-start: ensure clean state
ExecStartPre=-/usr/bin/podman stop -t 10 ${APP_NAME}
ExecStartPre=-/usr/bin/podman rm ${APP_NAME}

# Main container run
ExecStart=/usr/bin/podman run \
    --name ${APP_NAME} \
    -p ${HOST_PORT}:${CONTAINER_PORT} \
    --rm \
    ${IMAGE}

# Stop container gracefully
ExecStop=/usr/bin/podman stop -t 10 ${APP_NAME}

[Install]
WantedBy=multi-user.target
```

### Podman Container Service (Rootless)

```ini
[Unit]
Description=${APP_NAME} Container (Rootless)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=5
TimeoutStartSec=300
TimeoutStopSec=70

ExecStartPre=-/usr/bin/podman stop -t 10 ${APP_NAME}
ExecStartPre=-/usr/bin/podman rm ${APP_NAME}
ExecStart=/usr/bin/podman run \
    --name ${APP_NAME} \
    -p ${HOST_PORT}:${CONTAINER_PORT} \
    --rm \
    ${IMAGE}
ExecStop=/usr/bin/podman stop -t 10 ${APP_NAME}

[Install]
WantedBy=default.target
```

**Rootless setup commands:**
```bash
# Create user systemd directory
mkdir -p ~/.config/systemd/user

# Place unit file
cp ${APP_NAME}.service ~/.config/systemd/user/

# Reload and enable
systemctl --user daemon-reload
systemctl --user enable --now ${APP_NAME}

# Keep services running after logout
loginctl enable-linger ${USER}
```

### Podman Container with Volumes

```ini
[Unit]
Description=${APP_NAME} Container with Persistent Data
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Restart=always
RestartSec=5

ExecStartPre=-/usr/bin/podman stop -t 10 ${APP_NAME}
ExecStartPre=-/usr/bin/podman rm ${APP_NAME}
ExecStart=/usr/bin/podman run \
    --name ${APP_NAME} \
    -p ${HOST_PORT}:${CONTAINER_PORT} \
    -v /var/lib/${APP_NAME}/data:/app/data:z \
    -e DATABASE_URL=${DATABASE_URL} \
    --rm \
    ${IMAGE}
ExecStop=/usr/bin/podman stop -t 10 ${APP_NAME}

[Install]
WantedBy=multi-user.target
```

### Native Node.js Application

```ini
[Unit]
Description=${APP_NAME} Node.js Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=/opt/${APP_NAME}
Environment=NODE_ENV=production
Environment=PORT=${PORT}
ExecStart=/usr/bin/node /opt/${APP_NAME}/server.js
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/opt/${APP_NAME}

[Install]
WantedBy=multi-user.target
```

### Native Python Application

```ini
[Unit]
Description=${APP_NAME} Python Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=/opt/${APP_NAME}
Environment=PYTHONUNBUFFERED=1
Environment=PORT=${PORT}
ExecStart=/usr/bin/python3 /opt/${APP_NAME}/app.py
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/opt/${APP_NAME}

[Install]
WantedBy=multi-user.target
```

### Native Java Application

```ini
[Unit]
Description=${APP_NAME} Java Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=/opt/${APP_NAME}
Environment=JAVA_OPTS=-Xmx512m
ExecStart=/usr/bin/java -jar /opt/${APP_NAME}/app.jar --server.port=${PORT}
Restart=always
RestartSec=5
SuccessExitStatus=143

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/opt/${APP_NAME}

[Install]
WantedBy=multi-user.target
```

### Native Go Application

```ini
[Unit]
Description=${APP_NAME} Go Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=/opt/${APP_NAME}
Environment=PORT=${PORT}
ExecStart=/opt/${APP_NAME}/${BINARY_NAME}
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

---

## SELinux Configuration

### Common SELinux Contexts

| Context Type | Use Case |
|--------------|----------|
| `container_t` | Standard Podman container processes |
| `container_file_t` | Container data files |
| `bin_t` | Executable binaries |
| `httpd_sys_content_t` | Web application content (read-only) |
| `httpd_sys_rw_content_t` | Web application content (read-write) |
| `var_lib_t` | Application data in /var/lib |

### Volume Label Options for Podman

| Option | Description | Use Case |
|--------|-------------|----------|
| `:z` | Shared volume label | Volume accessed by multiple containers |
| `:Z` | Private volume label | Volume accessed by single container only |

Example:
```bash
podman run -v /data/shared:/app/shared:z myimage   # Shared
podman run -v /data/private:/app/data:Z myimage    # Private
```

### SELinux Commands

```bash
# Check current SELinux mode
getenforce

# View file context
ls -Z /path/to/file

# Set context for application directory
sudo semanage fcontext -a -t bin_t "/opt/myapp(/.*)?"
sudo restorecon -Rv /opt/myapp

# Set context for web content
sudo semanage fcontext -a -t httpd_sys_content_t "/opt/myapp/public(/.*)?"
sudo restorecon -Rv /opt/myapp/public

# Allow non-standard port for HTTP
sudo semanage port -a -t http_port_t -p tcp 8080

# View port contexts
sudo semanage port -l | grep http

# Check for SELinux denials
sudo ausearch -m AVC -ts recent

# Generate policy from denials (troubleshooting)
sudo ausearch -m AVC -ts recent | audit2allow -M mypolicy
sudo semodule -i mypolicy.pp

# Temporarily set permissive (for debugging only)
sudo setenforce 0
```

### Common SELinux Booleans

```bash
# Allow HTTP to connect to network (for proxy/API calls)
sudo setsebool -P httpd_can_network_connect 1

# Allow HTTP to connect to databases
sudo setsebool -P httpd_can_network_connect_db 1

# List all HTTP-related booleans
getsebool -a | grep httpd
```

---

## Firewall Commands

### Basic Port Management

```bash
# Check firewall status
sudo firewall-cmd --state

# List all open ports
sudo firewall-cmd --list-ports

# List all services
sudo firewall-cmd --list-services

# Open port permanently
sudo firewall-cmd --permanent --add-port=8080/tcp

# Open port temporarily (until reload)
sudo firewall-cmd --add-port=8080/tcp

# Reload firewall to apply permanent changes
sudo firewall-cmd --reload

# Remove port
sudo firewall-cmd --permanent --remove-port=8080/tcp
sudo firewall-cmd --reload
```

### Service-Based Management

```bash
# Add HTTP service
sudo firewall-cmd --permanent --add-service=http

# Add HTTPS service
sudo firewall-cmd --permanent --add-service=https

# Remove service
sudo firewall-cmd --permanent --remove-service=http

# Apply changes
sudo firewall-cmd --reload
```

### Zone Management

```bash
# List zones
sudo firewall-cmd --get-zones

# Get active zone
sudo firewall-cmd --get-active-zones

# Add port to specific zone
sudo firewall-cmd --zone=public --permanent --add-port=8080/tcp

# Set default zone
sudo firewall-cmd --set-default-zone=public
```

### Rich Rules (Advanced)

```bash
# Allow specific IP to access port
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" port protocol="tcp" port="8080" accept'

# Rate limiting
sudo firewall-cmd --permanent --add-rich-rule='rule service name="http" limit value="10/m" accept'

# Apply changes
sudo firewall-cmd --reload
```

---

## SSH Connection Patterns

### Test Connection

```bash
# Basic connection test
ssh -o BatchMode=yes -o ConnectTimeout=10 user@host "echo 'OK'"

# Verbose output for debugging
ssh -v user@host

# Test with specific key
ssh -i ~/.ssh/mykey user@host "echo 'OK'"
```

### Execute Remote Commands

```bash
# Single command
ssh user@host "command"

# Multiple commands
ssh user@host "cmd1 && cmd2 && cmd3"

# With sudo
ssh user@host "sudo command"

# Preserve environment
ssh user@host 'bash -l -c "command"'
```

### File Transfer

```bash
# Copy file to remote
scp local_file user@host:/remote/path/

# Copy directory recursively
scp -r local_dir user@host:/remote/path/

# Using rsync (preferred for large transfers)
rsync -avz --progress local_dir/ user@host:/remote/path/

# Exclude patterns
rsync -avz --exclude 'node_modules' --exclude '.git' ./ user@host:/remote/path/
```

### SSH Config for Convenience

```
# ~/.ssh/config
Host myrhel
    HostName 192.168.1.100
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_rsa
    StrictHostKeyChecking accept-new
```

Usage: `ssh myrhel "command"`

---

## Runtime Package Mapping

### Node.js

| Version | RHEL 8 | RHEL 9 |
|---------|--------|--------|
| 18 | `dnf module enable nodejs:18 && dnf install -y nodejs npm` | `dnf install -y nodejs npm` |
| 20 | `dnf module enable nodejs:20 && dnf install -y nodejs npm` | `dnf module enable nodejs:20 && dnf install -y nodejs npm` |

### Python

| Version | RHEL 8 | RHEL 9 |
|---------|--------|--------|
| 3.8 | `dnf install -y python38 python38-pip` | N/A |
| 3.9 | `dnf install -y python39 python39-pip` | `dnf install -y python3 python3-pip` |
| 3.11 | N/A | `dnf install -y python3.11 python3.11-pip` |
| 3.12 | N/A | `dnf install -y python3.12 python3.12-pip` |

### Java

| Version | RHEL 8 | RHEL 9 |
|---------|--------|--------|
| 11 | `dnf install -y java-11-openjdk java-11-openjdk-devel` | `dnf install -y java-11-openjdk java-11-openjdk-devel` |
| 17 | `dnf install -y java-17-openjdk java-17-openjdk-devel` | `dnf install -y java-17-openjdk java-17-openjdk-devel` |
| 21 | N/A | `dnf install -y java-21-openjdk java-21-openjdk-devel` |

### Go

| Version | RHEL 8 | RHEL 9 |
|---------|--------|--------|
| 1.20+ | `dnf install -y go-toolset` | `dnf install -y golang` |

### Ruby

| Version | RHEL 8 | RHEL 9 |
|---------|--------|--------|
| 3.0 | `dnf module enable ruby:3.0 && dnf install -y ruby ruby-devel` | `dnf install -y ruby ruby-devel` |
| 3.1 | `dnf module enable ruby:3.1 && dnf install -y ruby ruby-devel` | `dnf module enable ruby:3.1 && dnf install -y ruby ruby-devel` |

### PHP

| Version | RHEL 8 | RHEL 9 |
|---------|--------|--------|
| 7.4 | `dnf module enable php:7.4 && dnf install -y php php-cli php-fpm` | N/A |
| 8.0 | `dnf module enable php:8.0 && dnf install -y php php-cli php-fpm` | `dnf install -y php php-cli php-fpm` |
| 8.1 | N/A | `dnf module enable php:8.1 && dnf install -y php php-cli php-fpm` |

### Module Stream Commands

```bash
# List available streams for a module
dnf module list nodejs

# Enable specific stream
sudo dnf module enable nodejs:20

# Reset module (to switch streams)
sudo dnf module reset nodejs

# Install from enabled stream
sudo dnf install -y nodejs npm
```

---

## Service User Creation

For running applications as non-root:

```bash
# Create system user for the application
sudo useradd -r -s /sbin/nologin -d /opt/myapp myapp

# Set ownership
sudo chown -R myapp:myapp /opt/myapp

# Allow user to bind to privileged port (if needed)
sudo setcap 'cap_net_bind_service=+ep' /opt/myapp/binary
```

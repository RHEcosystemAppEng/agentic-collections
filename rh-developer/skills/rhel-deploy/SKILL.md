---
name: rhel-deploy
description: |
  CRITICAL: When user types /rhel-deploy, use THIS skill immediately. This skill deploys applications to standalone RHEL/Fedora/CentOS systems (NOT OpenShift) using Podman containers with systemd, or native dnf builds. Handles SSH connectivity, SELinux, firewall-cmd, and systemd unit creation. Triggers: /rhel-deploy command, 'deploy to RHEL', 'deploy to Fedora', 'deploy to my server via SSH'.
---

# /rhel-deploy Skill

**IMPORTANT:** This skill is for deploying to standalone RHEL/Fedora/CentOS systems via SSH. If user invoked `/rhel-deploy`, skip any OpenShift-related steps and proceed directly with SSH-based deployment.

Deploy applications to standalone RHEL systems using Podman containers or native builds with systemd service management.

## Overview

```
[Intro] → [SSH Connect] → [Analyze] → [Strategy] ──┬─→ [Container Path] ──→ [Complete]
                                                   │   (Podman + systemd)
                                                   │
                                                   └─→ [Native Path] ─────→ [Complete]
                                                       (dnf + systemd)
```

**Deployment Strategies (user chooses one):**
- **Container** - Build/pull container image, run with Podman, manage with systemd
- **Native** - Install dependencies with dnf, run application directly, manage with systemd

## Prerequisites

1. SSH access to target RHEL host with sudo privileges
2. RHEL 8+, CentOS Stream, Rocky Linux, or Fedora
3. For container deployments: Podman installed on target
4. For native deployments: Required development tools available via dnf

## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill requires explicit user confirmation at each phase. You MUST:
1. **Wait for user confirmation** before executing any actions
2. **Do NOT proceed** to the next phase until the user explicitly approves
3. **Present options clearly** (yes/no/modify) and wait for response
4. **Never auto-execute** SSH commands, file transfers, or service creation

If the user says "no" or wants modifications, address their concerns before proceeding.

## Workflow

### Phase 0: Introduction

```markdown
# Deploy to RHEL Host

I'll help you deploy your application to a RHEL system.

**What this workflow does:**
1. **Connect** - Establish SSH connection to your RHEL host
2. **Analyze** - Check target system capabilities (Podman, SELinux, firewall)
3. **Build** - Build container image or prepare native deployment
4. **Deploy** - Configure systemd service and networking
5. **Verify** - Ensure application is running and accessible

**Deployment Strategies:**
- **Container (Podman)** - Run your app in a container managed by systemd
- **Native** - Install and run your app directly on the host

**What I need from you:**
- SSH access to the target RHEL host (user@host)
- sudo privileges on the target host
- Your application source code

**Ready to begin?** (yes/no)
```

Wait for user confirmation before proceeding.

### Phase 1: SSH Connection

```markdown
## Phase 1: Connecting to RHEL Host

**SSH Target Configuration:**

Please provide your RHEL host details:

| Setting | Value | Default |
|---------|-------|---------|
| Host | [required] | - |
| User | [current user] | $USER |
| Port | 22 | 22 |

Example: `user@192.168.1.100` or `deploy@myserver.example.com`

**Enter your SSH target:**
```

**Connection verification:**

```bash
# Test SSH connection
ssh -o BatchMode=yes -o ConnectTimeout=10 [user]@[host] "echo 'Connection successful'"

# If connection fails, provide troubleshooting:
# - Check host is reachable: ping [host]
# - Verify SSH key is configured
# - Check firewall allows SSH (port 22)
```

Store `RHEL_HOST`, `RHEL_USER`, `RHEL_PORT` in session state.

### Phase 2: Target Host Analysis

```markdown
## Phase 2: Analyzing Target Host

Checking capabilities of [host]...

**System Information:**
| Setting | Value |
|---------|-------|
| OS | [cat /etc/redhat-release] |
| Kernel | [uname -r] |
| Architecture | [uname -m] |

**Container Runtime:**
| Setting | Status |
|---------|--------|
| Podman | [Installed v4.x / Not installed] |
| Container Storage | [/var/lib/containers] |

**System Services:**
| Setting | Status |
|---------|--------|
| SELinux | [Enforcing / Permissive / Disabled] |
| Firewall | [Active / Inactive] |
| systemd | Running |

Is this the correct target host? (yes/no)
```

**WAIT for user confirmation before proceeding.** Do NOT continue to Phase 3 until user confirms.

If user says "no", ask what needs to be changed or allow them to specify a different host.

**Commands to gather information:**

```bash
# RHEL version
ssh [target] "cat /etc/redhat-release"

# Podman check
ssh [target] "podman --version 2>/dev/null || echo 'Not installed'"

# SELinux status
ssh [target] "getenforce"

# Firewall status
ssh [target] "firewall-cmd --state 2>/dev/null || echo 'Not running'"
```

Store `RHEL_VERSION`, `PODMAN_AVAILABLE`, `SELINUX_STATUS`, `FIREWALL_STATUS` in session state.

### Phase 3: Strategy Selection

```markdown
## Deployment Strategy

Based on your project ([language]/[framework]) and target capabilities:

| Strategy | Description | Requirements |
|----------|-------------|--------------|
| **Container** | Build image, run with Podman + systemd | Podman installed |
| **Native** | Install with dnf, run directly + systemd | Runtime packages available |

**Recommendation:** [Container/Native] because [reason]

**Which deployment strategy would you like to use?**
1. Container - Deploy using Podman
2. Native - Deploy directly on host
```

**WAIT for user to select a strategy.** Do NOT proceed until user makes a choice.

**If Podman not installed and user selects Container:**
```markdown
Podman is not installed on the target. Would you like me to install it?

```bash
sudo dnf install -y podman
```

Proceed with Podman installation? (yes/no)
```

**WAIT for user confirmation.** Only install Podman if user explicitly says "yes".

Store `DEPLOYMENT_STRATEGY` in session state.

---

## CONTAINER PATH (If DEPLOYMENT_STRATEGY is "Container")

### Phase 4a-1: Image Selection

```markdown
## Container Image

**Options:**

1. **Build on target** - Transfer source, build with Podman on RHEL host
2. **Build locally and transfer** - Build here, push to registry or transfer
3. **Use existing image** - Pull from registry (e.g., quay.io, docker.io)

Which approach would you prefer?
```

**WAIT for user to select an option.** Do NOT proceed until user makes a choice.

**For options 1 and 2 (building an image):**

If no Containerfile/Dockerfile exists in the project, delegate to `/recommend-image`:

```markdown
## Selecting Base Image

To build your container, I need to select an appropriate base image.

Invoking `/recommend-image` to get the optimal UBI image for your [language]/[framework] project...
```

Use the `BUILDER_IMAGE` output from `/recommend-image` as the base image in the Containerfile.

**For build on target:**
```bash
# Transfer source
rsync -avz --exclude node_modules --exclude .git ./ [target]:/tmp/[app-name]-build/

# If no Containerfile exists, create one with recommended base image
ssh [target] "test -f /tmp/[app-name]-build/Containerfile -o -f /tmp/[app-name]-build/Dockerfile" || \
ssh [target] "cat > /tmp/[app-name]-build/Containerfile << 'EOF'
FROM [BUILDER_IMAGE]
# Containerfile generated using /recommend-image
WORKDIR /app
COPY . .
# Add language-specific build and run commands
EOF"

# Build on target
ssh [target] "cd /tmp/[app-name]-build && podman build -t [app-name]:latest ."
```

**For existing image:**
```bash
# Pull image on target
ssh [target] "podman pull [image-reference]"
```

### Phase 4a-2: Container Configuration

```markdown
## Container Configuration

**Container Settings:**
| Setting | Value |
|---------|-------|
| Name | [app-name] |
| Image | [image-ref] |
| Port Mapping | [host-port]:[container-port] |
| Volume Mounts | [list any persistent data paths] |
| Environment | [list env vars] |
| Run Mode | [rootless / rootful] |

**SELinux Volume Labels:**
- Use `:z` for shared volumes (multiple containers)
- Use `:Z` for private volumes (single container)

Proceed with this configuration? (yes/modify/cancel)
```

**WAIT for user confirmation.** Do NOT proceed until user explicitly approves.

- If user says "yes" → Continue to systemd unit creation
- If user says "modify" → Ask what they would like to change
- If user says "cancel" → Stop and preserve current state

### Phase 4a-3: Systemd Unit Creation

```markdown
## Systemd Service Configuration

Creating systemd unit for Podman container.

**Locations:**
- Rootless: `~/.config/systemd/user/[app-name].service`
- Rootful: `/etc/systemd/system/[app-name].service`

Proceed with creating this service? (yes/no)
```

**WAIT for user confirmation.** Do NOT create the systemd unit until user explicitly says "yes".

- If user says "yes" → Create the service unit file using the template
- If user says "no" → Ask what they would like to change

**Commands to execute:**

```bash
# For rootful:
ssh [target] "sudo tee /etc/systemd/system/[app-name].service" < [unit-file]
ssh [target] "sudo systemctl daemon-reload"
ssh [target] "sudo systemctl enable --now [app-name]"

# For rootless:
ssh [target] "mkdir -p ~/.config/systemd/user"
ssh [target] "tee ~/.config/systemd/user/[app-name].service" < [unit-file]
ssh [target] "systemctl --user daemon-reload"
ssh [target] "systemctl --user enable --now [app-name]"
ssh [target] "loginctl enable-linger [user]"  # Keep user services running
```

### Phase 4a-4: Firewall Configuration

```markdown
## Firewall Configuration

Opening port [port] for application access.

**Commands to execute:**
```bash
# Open port permanently
sudo firewall-cmd --permanent --add-port=[port]/tcp

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports
```

Proceed with firewall configuration? (yes/skip)
```

**WAIT for user confirmation.** Do NOT modify firewall until user explicitly responds.

- If user says "yes" → Configure firewall
- If user says "skip" → Skip firewall configuration and continue

---

## NATIVE PATH (If DEPLOYMENT_STRATEGY is "Native")

### Phase 4b-1: Dependency Installation

```markdown
## Installing Dependencies

**Runtime packages for [language]:**

| Language | RHEL 8 | RHEL 9 |
|----------|--------|--------|
| Node.js 18 | `dnf module enable nodejs:18 && dnf install nodejs` | `dnf install nodejs` |
| Node.js 20 | `dnf module enable nodejs:20 && dnf install nodejs` | `dnf module enable nodejs:20 && dnf install nodejs` |
| Python 3.9 | `dnf install python39 python39-pip` | `dnf install python3 python3-pip` |
| Python 3.11 | N/A | `dnf install python3.11 python3.11-pip` |
| Java 17 | `dnf install java-17-openjdk` | `dnf install java-17-openjdk` |
| Java 21 | N/A | `dnf install java-21-openjdk` |
| Go | `dnf install go-toolset` | `dnf install golang` |

**Commands to execute:**
```bash
ssh [target] "sudo dnf install -y [packages]"
```

Proceed with installation? (yes/no)
```

**WAIT for user confirmation.** Do NOT install packages until user explicitly says "yes".

### Phase 4b-2: Application Deployment

```markdown
## Deploying Application

**Deployment location:** `/opt/[app-name]`

**Steps:**
1. Create application directory
2. Transfer source code via rsync
3. Install application dependencies
4. Set ownership and permissions
5. Configure SELinux context

```bash
# Create directory
ssh [target] "sudo mkdir -p /opt/[app-name]"

# Transfer files
rsync -avz --exclude node_modules --exclude .git --exclude __pycache__ \
    ./ [target]:/tmp/[app-name]-deploy/
ssh [target] "sudo cp -r /tmp/[app-name]-deploy/* /opt/[app-name]/"

# Install dependencies (example for Node.js)
ssh [target] "cd /opt/[app-name] && npm install --production"

# Set permissions
ssh [target] "sudo chown -R [service-user]:[service-user] /opt/[app-name]"

# SELinux context
ssh [target] "sudo semanage fcontext -a -t bin_t '/opt/[app-name](/.*)?'"
ssh [target] "sudo restorecon -Rv /opt/[app-name]"
```

Proceed with deployment? (yes/no)
```

**WAIT for user confirmation.** Do NOT transfer files or deploy until user explicitly says "yes".

### Phase 4b-3: Native Systemd Unit

```markdown
## Systemd Service Configuration

**Location:** `/etc/systemd/system/[app-name].service`

**Start commands by language:**
| Language | ExecStart Example |
|----------|-------------------|
| Node.js | `/usr/bin/node /opt/[app-name]/server.js` |
| Python | `/usr/bin/python3 /opt/[app-name]/app.py` |
| Java | `/usr/bin/java -jar /opt/[app-name]/app.jar` |
| Go | `/opt/[app-name]/[binary-name]` |

Proceed with creating this service? (yes/no)
```

**WAIT for user confirmation.** Do NOT create the systemd unit until user explicitly says "yes".

### Phase 4b-4: Firewall Configuration

Same as container path - open required port with firewall-cmd.

---

## COMPLETION (Both paths converge here)

### Phase 5: Completion

```markdown
## Deployment Complete!

Your application is now running on [host].

---

**Application Summary:**
| Setting | Value |
|---------|-------|
| Name | [app-name] |
| Host | [host] |
| Strategy | [Container/Native] |
| Service | [app-name].service |

---

**Access URLs:**
| Type | URL |
|------|-----|
| HTTP | http://[host]:[port] |
| SSH | ssh [user]@[host] |

---

**Service Status:**
```
[systemctl status output]
```

---

**Quick Commands:**

```bash
# View logs
sudo journalctl -u [app-name] -f

# Restart service
sudo systemctl restart [app-name]

# Stop service
sudo systemctl stop [app-name]

# Check status
sudo systemctl status [app-name]

# View container logs (if container deployment)
podman logs -f [app-name]

# Remove deployment
sudo systemctl disable --now [app-name]
sudo rm /etc/systemd/system/[app-name].service
# For container: podman rm [app-name]
# For native: sudo rm -rf /opt/[app-name]
```

---

Your application is live!
```

## Delegated Skills

This skill delegates to other skills when needed:

| Scenario | Delegated Skill | Purpose |
|----------|-----------------|---------|
| Building container image (no Containerfile) | `/recommend-image` | Get optimal UBI base image for the detected language/framework |

When delegating to `/recommend-image`:
1. Provide detected `LANGUAGE`, `FRAMEWORK`, and `VERSION` from project analysis
2. Receive back: `BUILDER_IMAGE`, `IMAGE_VARIANT`, `SELECTION_RATIONALE`
3. Use `BUILDER_IMAGE` as the FROM image in generated Containerfile

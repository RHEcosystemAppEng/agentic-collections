---
title: RHEL Package Management for CVE Remediation
category: rhel
sources:
  - title: Managing Software with the DNF Tool (RHEL 9)
    url: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/managing_software_with_the_dnf_tool/index
    sections: DNF commands, updating packages, repository management
    date_accessed: 2026-01-20
  - title: Software Management in RHEL 9 Adoption Guide
    url: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/considerations_in_adopting_rhel_9/assembly_software-management_considerations-in-adopting-rhel-9
    sections: RHEL 7/8/9 compatibility, migration considerations
    date_accessed: 2026-01-20
  - title: Updating RHEL 9 Content
    url: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/managing_software_with_the_dnf_tool/assembly_updating-rhel-9-content_managing-software-with-the-dnf-tool
    sections: Package update procedures, reboot detection
    date_accessed: 2026-01-20
tags: [dnf, yum, package-management, rhel, updates, systemd, reboot-detection]
applies_to: [rhel7, rhel8, rhel9]
semantic_keywords:
  - "DNF package manager"
  - "YUM package manager"
  - "package update"
  - "repository management"
  - "reboot detection"
  - "systemd service management"
  - "needs-restarting"
  - "subscription manager"
use_cases:
  - "package_update_cve"
  - "rhel_version_compatibility"
  - "reboot_detection"
  - "service_restart_after_update"
related_docs:
  - "ansible/cve-remediation-templates.md"
  - "rhel/version-compatibility.md"
  - "rhel/systemd-services.md"
last_updated: 2026-01-20
---

# RHEL Package Management for CVE Remediation

This document provides comprehensive guidance on package management across RHEL 7, 8, and 9 for CVE remediation scenarios.

## Overview

Red Hat Enterprise Linux uses different package managers across versions:
- **RHEL 7**: YUM (Yellowdog Updater Modified)
- **RHEL 8**: DNF (Dandified YUM) with `yum` as an alias
- **RHEL 9**: DNF with `yum` as an alias

**Key Insight**: In RHEL 8 and 9, `yum` is a symbolic link to `dnf` for backward compatibility. All YUM commands work identically in RHEL 8/9 via DNF.

## DNF vs YUM Command Compatibility

### Command Equivalence Table

| Operation | RHEL 7 (YUM) | RHEL 8/9 (DNF) | Notes |
|-----------|--------------|----------------|-------|
| Update package | `yum update httpd` | `dnf update httpd` or `yum update httpd` | Identical behavior |
| Install package | `yum install httpd` | `dnf install httpd` or `yum install httpd` | Identical behavior |
| Remove package | `yum remove httpd` | `dnf remove httpd` or `yum remove httpd` | Identical behavior |
| Search packages | `yum search keyword` | `dnf search keyword` or `yum search keyword` | Identical behavior |
| List installed | `yum list installed` | `dnf list installed` or `yum list installed` | Identical behavior |
| Clean cache | `yum clean all` | `dnf clean all` or `yum clean all` | Identical behavior |
| Check updates | `yum check-update` | `dnf check-update` or `yum check-update` | Identical behavior |

### Ansible Module Compatibility

```yaml
# RHEL 7 - Use yum module
- name: Update packages (RHEL 7)
  yum:
    name: httpd
    state: latest
  when: ansible_distribution_major_version == "7"

# RHEL 8/9 - Use dnf module (preferred)
- name: Update packages (RHEL 8/9)
  dnf:
    name: httpd
    state: latest
  when: ansible_distribution_major_version in ["8", "9"]

# Universal approach - yum module works on all versions
- name: Update packages (All RHEL versions)
  package:
    name: httpd
    state: latest
  # Uses appropriate package manager automatically
```

## Package Update Patterns for CVE Remediation

### Pattern 1: Single Package Update

**Use Case**: CVE affects a specific package (e.g., httpd, openssl, glibc)

```yaml
- name: Update vulnerable package
  dnf:
    name: httpd
    state: latest
    update_cache: true
  register: package_update
  when: ansible_distribution_major_version in ["8", "9"]

- name: Update vulnerable package (RHEL 7)
  yum:
    name: httpd
    state: latest
    update_cache: true
  register: package_update
  when: ansible_distribution_major_version == "7"
```

**Key Options**:
- `state: latest` - Updates to newest available version
- `update_cache: true` - Refreshes repository metadata before update
- `register: package_update` - Captures update results for verification

### Pattern 2: Multiple Related Packages

**Use Case**: CVE affects a package and its dependencies (e.g., openssl + openssl-libs)

```yaml
- name: Update vulnerable packages and dependencies
  dnf:
    name:
      - openssl
      - openssl-libs
      - openssl-devel
    state: latest
    update_cache: true
  register: package_update
```

**Why This Matters**: Some CVEs affect shared libraries. Updating only the main package may leave vulnerabilities in dependent libraries.

### Pattern 3: Kernel Package Updates

**Use Case**: Kernel CVEs requiring reboot

```yaml
- name: Update kernel package
  dnf:
    name: kernel
    state: latest
    update_cache: true
  register: kernel_update

- name: Record current kernel before reboot
  command: uname -r
  register: current_kernel
  changed_when: false

# Reboot will be handled separately
# See: Template 4 in cve-remediation-templates.md
```

**Important**: Kernel updates **always** require a reboot. New kernel is not active until system restarts.

### Pattern 4: Security-Only Updates

**Use Case**: Apply only security updates, not all available updates

```bash
# RHEL 8/9 - Security updates only
dnf update --security

# RHEL 7 - Requires yum-plugin-security
yum update --security
```

**Ansible Equivalent**:
```yaml
- name: Apply security updates only (RHEL 8/9)
  command: dnf update -y --security
  register: security_updates
  when: ansible_distribution_major_version in ["8", "9"]
```

## Repository Management

### Enabling/Disabling Repositories

```yaml
- name: Enable repository for specific package
  command: subscription-manager repos --enable=rhel-9-for-x86_64-appstream-rpms
  when: ansible_distribution_major_version == "9"

- name: Update package from specific repo
  dnf:
    name: httpd
    state: latest
    enablerepo: rhel-9-for-x86_64-appstream-rpms
```

### Repository List (RHEL 9)

Common repositories for CVE remediation:
- `rhel-9-for-x86_64-baseos-rpms` - Base OS packages
- `rhel-9-for-x86_64-appstream-rpms` - Application streams
- `rhel-9-for-x86_64-supplementary-rpms` - Supplementary packages

### Verifying Repository Configuration

```yaml
- name: List enabled repositories
  command: subscription-manager repos --list-enabled
  register: enabled_repos
  changed_when: false

- name: Display enabled repos
  debug:
    msg: "{{ enabled_repos.stdout_lines }}"
```

## Reboot Detection Patterns

### Method 1: Check for Reboot-Required File

```yaml
- name: Check if reboot is required (file-based)
  stat:
    path: /var/run/reboot-required
  register: reboot_required_file

- name: Notify if reboot needed
  debug:
    msg: "⚠️  System reboot required"
  when: reboot_required_file.stat.exists
```

**Note**: Not all RHEL systems create this file. More reliable method below.

### Method 2: needs-restarting Command (RHEL 8/9)

**Most Reliable Method for RHEL 8/9**

```yaml
- name: Check if reboot is required (needs-restarting)
  command: needs-restarting -r
  register: needs_restarting
  failed_when: false
  changed_when: false
  when: ansible_distribution_major_version in ["8", "9"]

- name: Determine reboot requirement
  set_fact:
    reboot_required: "{{ needs_restarting.rc != 0 }}"
  when: ansible_distribution_major_version in ["8", "9"]

- name: Display reboot status
  debug:
    msg: "Reboot required: {{ reboot_required }}"
```

**Exit Codes**:
- `0` - No reboot required
- `1` - Reboot required (kernel, glibc, systemd, or other core component updated)

### Method 3: Check Specific Package Updates

```yaml
- name: Check if kernel was updated
  shell: |
    LATEST_KERNEL=$(rpm -q kernel --last | head -1 | awk '{print $1}')
    RUNNING_KERNEL=$(uname -r)
    if [[ "$LATEST_KERNEL" != "kernel-$RUNNING_KERNEL" ]]; then
      echo "reboot_needed"
    fi
  register: kernel_check
  changed_when: false

- name: Set reboot flag if kernel changed
  set_fact:
    reboot_required: true
  when: "'reboot_needed' in kernel_check.stdout"
```

### Comprehensive Reboot Detection

**Recommended Pattern for CVE Remediation**:

```yaml
- name: Comprehensive reboot detection
  block:
    - name: Check needs-restarting (RHEL 8/9)
      command: needs-restarting -r
      register: needs_restarting
      failed_when: false
      changed_when: false
      when: ansible_distribution_major_version in ["8", "9"]

    - name: Check reboot-required file
      stat:
        path: /var/run/reboot-required
      register: reboot_file

    - name: Check if kernel was updated
      shell: |
        rpm -q --last kernel | head -1 | \
        grep -q "$(uname -r)" || echo "kernel_updated"
      register: kernel_check
      changed_when: false
      failed_when: false

    - name: Determine final reboot requirement
      set_fact:
        reboot_required: >
          {{
            reboot_file.stat.exists | default(false) or
            (needs_restarting.rc != 0 | default(false)) or
            ('kernel_updated' in kernel_check.stdout)
          }}

    - name: Display reboot requirement
      debug:
        msg: |
          Reboot Required: {{ reboot_required }}
          Reason: {% if reboot_file.stat.exists %}reboot-required file exists{% elif needs_restarting.rc != 0 %}needs-restarting check{% elif 'kernel_updated' in kernel_check.stdout %}kernel update{% else %}unknown{% endif %}
```

## Service Restart After Package Updates

### Pattern 1: Restart Specific Services

```yaml
- name: Restart httpd after package update
  systemd:
    name: httpd
    state: restarted
  when:
    - package_update is changed
    - not reboot_required

- name: Wait for service to be active
  systemd:
    name: httpd
    state: started
  retries: 3
  delay: 5
```

### Pattern 2: Restart Services Requiring Updates (RHEL 8/9)

```yaml
- name: Find services that need restarting
  command: needs-restarting -s
  register: services_to_restart
  changed_when: false
  when: ansible_distribution_major_version in ["8", "9"]

- name: Parse service names
  set_fact:
    service_list: "{{ services_to_restart.stdout_lines | map('regex_replace', '^(.+)\\.service$', '\\1') | list }}"
  when: services_to_restart.stdout_lines | length > 0

- name: Restart services that need it
  systemd:
    name: "{{ item }}"
    state: restarted
  loop: "{{ service_list }}"
  when:
    - service_list is defined
    - not reboot_required
  ignore_errors: true
```

**`needs-restarting -s` Output Example**:
```
httpd.service
NetworkManager.service
sshd.service
```

### Pattern 3: Conditional Service Restart Based on Package

```yaml
- name: Map packages to services
  set_fact:
    package_service_map:
      httpd: httpd
      nginx: nginx
      sshd: sshd
      openssl: [httpd, nginx, sshd]  # Multiple services may use openssl

- name: Restart services for updated packages
  systemd:
    name: "{{ package_service_map[item] }}"
    state: restarted
  loop: "{{ package_update.results | map(attribute='item') | list }}"
  when:
    - package_update is changed
    - item in package_service_map
    - not reboot_required
```

## Package Version Verification

### Pre/Post Update Version Comparison

```yaml
- name: Gather package facts before update
  package_facts:
    manager: auto

- name: Record pre-update versions
  set_fact:
    pre_update_versions: "{{ ansible_facts.packages }}"

- name: Update packages
  dnf:
    name: "{{ vulnerable_packages }}"
    state: latest
  register: package_update

- name: Gather package facts after update
  package_facts:
    manager: auto

- name: Compare versions
  debug:
    msg: |
      Package: {{ item }}
      Before: {{ pre_update_versions[item][0].version | default('not installed') }}
      After: {{ ansible_facts.packages[item][0].version | default('not installed') }}
  loop: "{{ vulnerable_packages }}"
  when: item in ansible_facts.packages
```

### Verify Specific Package Version

```yaml
- name: Verify package is at required version
  shell: |
    rpm -q {{ package_name }} --queryformat '%{VERSION}-%{RELEASE}'
  register: package_version
  changed_when: false

- name: Assert minimum version
  assert:
    that:
      - package_version.stdout is version(minimum_version, '>=')
    fail_msg: "Package {{ package_name }} is {{ package_version.stdout }}, required >= {{ minimum_version }}"
    success_msg: "Package {{ package_name }} version {{ package_version.stdout }} meets requirements"
```

## Rollback and Backup Strategies

### RHEL 8/9 Snapshot with Boom

```yaml
- name: Install boom-boot (if not present)
  dnf:
    name: boom-boot
    state: present
  when: ansible_distribution_major_version in ["8", "9"]

- name: Create pre-update snapshot
  command: boom create --title "pre-cve-{{ cve_id }}-{{ ansible_date_time.epoch }}"
  register: snapshot_result
  ignore_errors: true
  when: ansible_distribution_major_version in ["8", "9"]

- name: Log snapshot creation
  debug:
    msg: "Snapshot created: {{ snapshot_result.stdout }}"
  when: snapshot_result is success
```

### Package Downgrade (Emergency Rollback)

```yaml
- name: Downgrade package to previous version
  dnf:
    name: httpd-2.4.37-1.el8
    state: present
    allow_downgrade: true
  when: ansible_distribution_major_version in ["8", "9"]

- name: Downgrade package (RHEL 7)
  yum:
    name: httpd-2.4.37-1.el7
    state: present
  when: ansible_distribution_major_version == "7"
```

**Warning**: Downgrades should be rare and only for emergency rollback. May cause dependency issues.

## Subscription Manager Integration

### Verify System Registration

```yaml
- name: Check subscription status
  command: subscription-manager status
  register: subscription_status
  changed_when: false
  failed_when: false

- name: Assert system is registered
  assert:
    that:
      - "'Overall Status: Current' in subscription_status.stdout or 'Overall Status: Simple Content Access' in subscription_status.stdout"
    fail_msg: "System is not properly subscribed to Red Hat repositories"
    success_msg: "System subscription is current"
```

### Refresh Subscription

```yaml
- name: Refresh subscription data
  command: subscription-manager refresh
  when: subscription_status.rc != 0

- name: Update repository metadata
  command: dnf clean all && dnf makecache
  when: ansible_distribution_major_version in ["8", "9"]
```

## RHEL Version-Specific Considerations

### RHEL 7

- **Package Manager**: YUM (Python 2.7-based)
- **Systemd Version**: 219
- **Reboot Detection**: No `needs-restarting -r`, use alternative methods
- **Security Updates**: Requires `yum-plugin-security` package

```yaml
- name: Install security plugin (RHEL 7)
  yum:
    name: yum-plugin-security
    state: present
  when: ansible_distribution_major_version == "7"
```

### RHEL 8

- **Package Manager**: DNF 4.x (Python 3.6-based), `yum` is alias
- **Systemd Version**: 239
- **Reboot Detection**: `needs-restarting -r` available
- **Module Streams**: AppStream concept introduced

```yaml
- name: Enable module stream (RHEL 8)
  command: dnf module enable httpd:2.4 -y
  when: ansible_distribution_major_version == "8"
```

### RHEL 9

- **Package Manager**: DNF 4.x (Python 3.9-based), `yum` is alias
- **Systemd Version**: 252
- **Reboot Detection**: `needs-restarting -r` available
- **New in 9.7**: Multisig DNF plugin for quantum-safe RPM verification

```yaml
- name: Install multisig plugin (RHEL 9.7+)
  dnf:
    name: python3-dnf-plugin-multisig
    state: present
  when:
    - ansible_distribution_major_version == "9"
    - ansible_distribution_version is version('9.7', '>=')
```

## Common Pitfalls and Solutions

### Pitfall 1: Not Refreshing Repository Cache

**Problem**: Updates fail or don't detect new packages
**Solution**: Always use `update_cache: true`

```yaml
# ❌ Bad - may miss new package versions
- dnf:
    name: httpd
    state: latest

# ✅ Good - ensures latest metadata
- dnf:
    name: httpd
    state: latest
    update_cache: true
```

### Pitfall 2: Ignoring Reboot Requirements

**Problem**: CVE remains exploitable after "update"
**Solution**: Always check and handle reboots

```yaml
# ✅ Complete pattern
- name: Update package
  dnf:
    name: kernel
    state: latest

- name: Check reboot requirement
  command: needs-restarting -r
  register: needs_reboot
  failed_when: false

- name: Notify if reboot needed
  debug:
    msg: "⚠️  REBOOT REQUIRED - CVE not fully remediated until reboot"
  when: needs_reboot.rc != 0
```

### Pitfall 3: Not Verifying Package Update Success

**Problem**: Package update silently fails, CVE remains
**Solution**: Use `register` and verify changes

```yaml
- name: Update package
  dnf:
    name: httpd
    state: latest
  register: package_update

- name: Verify update occurred
  assert:
    that:
      - package_update is changed or package_update is success
    fail_msg: "Package update failed - CVE remediation incomplete"
```

### Pitfall 4: Restarting Services When Reboot Required

**Problem**: Wasted effort, service restart won't apply kernel updates
**Solution**: Conditional service restarts

```yaml
- name: Restart service only if no reboot needed
  systemd:
    name: httpd
    state: restarted
  when:
    - package_update is changed
    - not reboot_required  # Don't restart if rebooting anyway
```

### Pitfall 5: Using Wrong Package Manager Module

**Problem**: Playbook fails on different RHEL versions
**Solution**: Use version-conditional tasks or `package` module

```yaml
# ✅ Best - works on all RHEL versions
- name: Update package (universal)
  package:
    name: httpd
    state: latest

# ✅ Also good - version-specific
- name: Update package (RHEL 8/9)
  dnf:
    name: httpd
    state: latest
  when: ansible_distribution_major_version in ["8", "9"]
```

## Quick Reference Commands

### Package Operations
```bash
# Update single package
dnf update httpd

# Update all security patches
dnf update --security

# Update multiple packages
dnf update httpd httpd-tools

# Check for available updates
dnf check-update

# List installed packages
dnf list installed

# Show package info
dnf info httpd

# Search for package
dnf search webserver
```

### Reboot Detection
```bash
# Check if reboot needed (RHEL 8/9)
needs-restarting -r

# List services needing restart
needs-restarting -s

# Check current kernel vs installed
uname -r
rpm -q kernel --last | head -1
```

### Repository Management
```bash
# List enabled repos
subscription-manager repos --list-enabled

# Enable specific repo
subscription-manager repos --enable=repo-name

# Refresh repo metadata
dnf clean all && dnf makecache
```

## Related Documentation

- **[CVE Remediation Templates](../ansible/cve-remediation-templates.md)** - Playbook templates using these patterns
- **[RHEL Version Compatibility](version-compatibility.md)** - Detailed RHEL 7/8/9 differences
- **[Systemd Services](systemd-services.md)** - Service management patterns
- **[SELinux Context](selinux-context.md)** - SELinux considerations for package updates

## Official Red Hat Sources

This document is derived from:

1. **Managing Software with the DNF Tool (RHEL 9)**
   https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/managing_software_with_the_dnf_tool/index

2. **Software Management in RHEL 9 Adoption Guide**
   https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/considerations_in_adopting_rhel_9/assembly_software-management_considerations-in-adopting-rhel-9

3. **Updating RHEL 9 Content**
   https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/managing_software_with_the_dnf_tool/assembly_updating-rhel-9-content_managing-software-with-the-dnf-tool

**License**: Content derived from Red Hat documentation under CC BY-SA 4.0
**Last Verified**: 2026-01-20

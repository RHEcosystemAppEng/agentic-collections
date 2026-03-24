---
title: RHEL Documentation Overview
category: rhel
last_updated: 2026-01-20
---

# RHEL Documentation Overview

This directory contains Red Hat Enterprise Linux-specific guidance for CVE remediation.

## Available Documentation

### Priority P0 (Core)
- **[package-management.md](package-management.md)** - DNF/YUM workflows, reboot detection, service restarts
  - RHEL 7/8/9 compatibility
  - Package update patterns
  - Repository management
  - Subscription Manager integration

### Future Enhancements (P1-P2 Priority)
- **selinux-context.md** - SELinux remediation patterns (planned)
- **security-hardening-rhel9.md** - RHEL 9 security baseline (planned)
- **version-compatibility.md** - RHEL 7/8/9 comparison matrix (planned)
- **systemd-services.md** - Service management patterns (planned)

## When to Use These Docs

**Use package-management.md when**:
- Creating playbooks that update packages
- Need to detect if reboot is required (needs-restarting)
- Working across multiple RHEL versions (7/8/9)
- Handling DNF/YUM differences
- Managing service restarts after package updates
- Troubleshooting repository or subscription issues

## Quick Links

- Official Red Hat RHEL 9 docs: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9
- Package management guide: https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/managing_software_with_the_dnf_tool/index
- Source attribution: [../SOURCES.md](../SOURCES.md)

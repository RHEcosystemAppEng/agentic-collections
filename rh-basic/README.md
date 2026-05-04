# Basic Agentic Collection

Essential Red Hat skills for IT professionals working with Red Hat products. This pack covers everyday tasks: understanding CVEs, gathering diagnostics, checking product lifecycle status, and filing support cases at the right severity.

**Persona**: IT Professional / Red Hat Customer
**Marketplaces**: Claude Code, Cursor

## Overview

The rh-basic collection provides lightweight, self-contained skills that work with or without a configured MCP server. Each skill falls back to web sources when MCP tools are unavailable.

- **5 skills** covering the most common Red Hat support and operations workflows
- **1 MCP server integration** (Red Hat Lightspeed) for live CVE and inventory data
- **Self-installing** via the `red-hat-get-started` skill

## Quick Start

### Prerequisites

- Claude Code CLI or IDE extension
- Podman installed (required for Lightspeed MCP)
- Red Hat service account ([console.redhat.com](https://console.redhat.com/iam/service-accounts))

### Installation (Lola)

```bash
lola market add rh-agentic-collections https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-collections/main/marketplace/rh-agentic-collection.yml
lola install -f rh-basic
```

### MCP Setup (optional but recommended)

Skills work without MCP configured, falling back to public Red Hat documentation.

### Environment Variables

```bash
export LIGHTSPEED_CLIENT_ID="your-service-account-client-id"
export LIGHTSPEED_CLIENT_SECRET="your-service-account-client-secret"
```

## Skills

### 1. **red-hat-cve-explainer** - CVE Explanation and Severity

Explains a CVE using Red Hat's severity rating system and recommends a course of action.

**Use when:**
- "What is CVE-2024-1234?"
- "How severe is this CVE?"
- "Should I patch CVE-X immediately?"

**What it does:**
- Looks up CVE metadata via Lightspeed MCP or Red Hat CVE pages
- Maps to Red Hat severity (Critical/Important/Moderate/Low)
- Links to applicable security advisories (RHSA/RHBA/RHEA)
- Gives a concrete action recommendation per severity

### 2. **red-hat-diagnostics** - Diagnostic Data Gathering

Provides the correct commands and upload instructions for gathering diagnostics across Red Hat products.

**Use when:**
- "How do I collect a sos report?"
- "What must-gather do I run for OpenShift?"
- "How do I gather AAP logs for a support case?"

**What it does:**
- Identifies product and deployment type (RPM, containerized, OCP operator)
- Provides exact commands for RHEL, OpenShift, AAP, and Satellite
- Explains how to upload archives to Red Hat Support

### 3. **red-hat-product-lifecycle** - Lifecycle Status

Reports the current lifecycle phase and support dates for any Red Hat product or version.

**Use when:**
- "Is RHEL 8.6 still supported?"
- "When does OpenShift 4.14 reach end of maintenance?"
- "What App Streams are available for RHEL 9?"

**What it does:**
- Retrieves lifecycle dates via Lightspeed MCP or Red Hat lifecycle pages
- Explains what updates each phase receives (security, bug, features)
- Gives a concrete action recommendation (upgrade, EUS, patch normally)
- Explains Red Hat's backporting model

### 4. **red-hat-support-severity** - Support Ticket Severity

Determines the correct severity for a Red Hat support ticket and explains the SLA.

**Use when:**
- "What severity should I file this case as?"
- "Is this a Sev 1 or Sev 2?"
- "What's the SLA for my support tier?"

**What it does:**
- Maps your situation (outage, impairment, workaround) to Sev 1-4
- Shows SLA response times for Premium and Standard support
- Lists what to include in the ticket for fastest resolution
- Adjusts recommendation when a CVE is involved

### 5. **red-hat-get-started** - Bootstrap Installer

Fetches and installs all Red Hat Basic skills into the current project. Removes itself after running.

**Use when:**
- Setting up Red Hat skills for the first time in a project

## Skills Decision Guide

| User Request | Skill | Reason |
|---|---|---|
| "Explain this CVE" | **red-hat-cve-explainer** | CVE lookup and severity |
| "How do I collect diagnostics?" | **red-hat-diagnostics** | Support case preparation |
| "Is RHEL 8 still supported?" | **red-hat-product-lifecycle** | Lifecycle date lookup |
| "What severity is my support case?" | **red-hat-support-severity** | SLA guidance |
| "Install Red Hat skills" | **red-hat-get-started** | First-time setup |

## MCP Server Integration

### **lightspeed-mcp** - Red Hat Lightspeed

Provides live data for CVE lookups, RHEL lifecycle, system inventory, and patch advisory information.

- CVE metadata and severity
- RHEL and App Stream lifecycle dates
- System inventory (when inventory roles assigned)
- Vulnerability data (when vulnerability roles assigned)
- Requires: `LIGHTSPEED_CLIENT_ID`, `LIGHTSPEED_CLIENT_SECRET`

**Skills fall back to `WebFetch` on Red Hat documentation if MCP is unavailable** — you do not need MCP configured to use this pack.

## Security Model

- **Credentials**: Environment variables only — never hardcoded or logged
- **Container isolation**: Lightspeed MCP runs in a Podman container
- **No credential echo**: Skills verify env vars are set without printing their values

## Architecture

```
rh-basic/
├── README.md
├── CLAUDE.md
├── mcps.json
└── skills/
    ├── red-hat-cve-explainer/SKILL.md
    ├── red-hat-diagnostics/SKILL.md
    ├── red-hat-get-started/SKILL.md
    ├── red-hat-product-lifecycle/SKILL.md
    └── red-hat-support-severity/SKILL.md
```

## References

- [Red Hat Customer Portal](https://access.redhat.com/)
- [Red Hat Lightspeed](https://console.redhat.com/insights)
- [Red Hat Product Lifecycle](https://access.redhat.com/product-life-cycles/)
- [Red Hat CVE Database](https://access.redhat.com/security/security-updates/#/cve)
- [Lola Package Manager](https://github.com/RedHatProductSecurity/lola)
- [Main Repository](https://github.com/RHEcosystemAppEng/agentic-collections)

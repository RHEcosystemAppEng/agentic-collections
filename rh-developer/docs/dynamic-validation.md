---
title: Dynamic Image Validation Reference
category: containers
sources:
  - title: Skopeo Documentation
    url: https://github.com/containers/skopeo
    sections: Inspecting images, Copying images
    date_accessed: 2026-02-08
  - title: Red Hat Security Data API
    url: https://access.redhat.com/documentation/en-us/red_hat_security_data_api/1.0
    sections: CVE queries, Product filtering
    date_accessed: 2026-02-08
---

# Dynamic Image Validation Reference

This document provides detailed patterns for validating container images using Skopeo and the Red Hat Security Data API.

## Skopeo Commands

Skopeo inspects container images without downloading them, providing real-time metadata.

### Prerequisites

**Check if skopeo is installed:**
```bash
which skopeo
# or
skopeo --version
```

**Installation:**
| OS | Command |
|----|---------|
| Fedora/RHEL/CentOS | `sudo dnf install skopeo` |
| Ubuntu/Debian | `sudo apt install skopeo` |
| macOS (Homebrew) | `brew install skopeo` |

### Basic Inspection

```bash
# Inspect an image (full JSON output)
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20

# The docker:// transport is OCI-standard and works with all registries
# (Docker Hub, Red Hat, Quay, Podman registries, etc.)
```

### Extracting Specific Fields

```bash
# Get creation date
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20 --format '{{.Created}}'

# Get architecture
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20 --format '{{.Architecture}}'

# Get all labels
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20 --format '{{.Labels}}'

# Get specific label (e.g., version)
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20 --format '{{index .Labels "version"}}'

# Get layer count
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20 --format '{{len .Layers}}'
```

### Listing Available Tags

```bash
# List all tags for an image
skopeo list-tags docker://registry.access.redhat.com/ubi9/nodejs-20

# Output includes all available versions/tags
```

### Image Transport Options

```bash
# Remote registry (most common)
skopeo inspect docker://registry.access.redhat.com/ubi9/nodejs-20

# Local Podman storage
skopeo inspect containers-storage:localhost/myimage:latest

# OCI layout directory
skopeo inspect oci:/path/to/oci-layout:tag

# Docker archive
skopeo inspect docker-archive:/path/to/image.tar
```

### Useful Metadata Fields

| Field | Description | Use Case |
|-------|-------------|----------|
| `Created` | Image build timestamp | Freshness indicator |
| `Architecture` | CPU architecture | Verify ARM64/x86_64 support |
| `Os` | Operating system | Should be "linux" for UBI |
| `Labels` | Image labels (version, maintainer, etc.) | Verify language version |
| `Layers` | Layer digests | Calculate approximate size |
| `Digest` | Immutable image hash | Pin exact version |

### Error Handling

**Image not found:**
```
Error: Error reading manifest: ... 404 Not Found
```
→ Image does not exist at specified tag

**Authentication required:**
```
Error: Error reading manifest: unauthorized
```
→ Private registry, need `skopeo login` first

**Network error:**
```
Error: Error initializing source: pinging container registry
```
→ Network connectivity issue

---

## Red Hat Security Data API

The Security Data API provides CVE information without authentication.

### Base Endpoint

```
https://access.redhat.com/hydra/rest/securitydata/
```

### Query CVEs

```bash
# Get all CVEs for UBI 9 (may return many results)
curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209"

# Filter by severity (critical, important, moderate, low)
curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209&severity=critical"

# Filter by date (CVEs after a specific date)
curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209&after=2025-01-01"

# Count critical CVEs
curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209&severity=critical" | jq 'length'
```

### Product Names for Queries

| Image Base | Product Name (URL-encoded) |
|------------|---------------------------|
| UBI 9 | `Red%20Hat%20Universal%20Base%20Image%209` |
| UBI 8 | `Red%20Hat%20Universal%20Base%20Image%208` |
| RHEL 9 | `Red%20Hat%20Enterprise%20Linux%209` |
| RHEL 8 | `Red%20Hat%20Enterprise%20Linux%208` |

### Response Fields

Each CVE object contains:

| Field | Description |
|-------|-------------|
| `CVE` | CVE identifier (e.g., CVE-2024-1234) |
| `severity` | critical, important, moderate, low |
| `public_date` | When CVE was disclosed |
| `advisories` | Related Red Hat advisories |
| `bugzilla` | Bugzilla tracking URL |
| `affected_packages` | Packages affected by CVE |

### Parsing Examples

```bash
# Get CVE IDs and severities
curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209&severity=critical" | jq '.[] | {cve: .CVE, severity: .severity}'

# Get most recent CVE date
curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209&severity=critical" | jq '.[0].public_date'

# Check if any critical CVEs exist
CRITICAL_COUNT=$(curl -s "https://access.redhat.com/hydra/rest/securitydata/cve.json?product=Red%20Hat%20Universal%20Base%20Image%209&severity=critical" | jq 'length')
if [ "$CRITICAL_COUNT" -gt 0 ]; then
  echo "Warning: $CRITICAL_COUNT critical CVEs found"
fi
```

---

## Validation Workflow

### Complete Validation Sequence

```
1. Check if skopeo is installed
   ├── Yes → Continue to step 2
   └── No → Prompt user to install, offer to continue with static data

2. For each candidate image:
   a. Run: skopeo inspect docker://registry.access.redhat.com/ubi9/[image]
   b. If fails → Remove from candidates, try next
   c. If succeeds → Extract: Created, Architecture, Labels

3. Query Security Data API for UBI base:
   a. Run: curl CVE query for critical severity
   b. Parse count of critical CVEs
   c. If count > 0 → Add warning to recommendation

4. Compile results:
   - Image metadata (from skopeo)
   - Security status (from API)
   - Static scoring data (from reference tables)

5. Present recommendation with sources indicated
```

### Fallback Behavior

| Scenario | Action |
|----------|--------|
| Skopeo not installed | Prompt installation, offer static-only mode |
| Skopeo command fails | Note "unable to verify", use static data |
| Security API unavailable | Note "security not verified", proceed |
| Image not found | Remove from candidates, suggest alternatives |
| Network offline | Use static data only, note limitations |

---

## Integration with Recommendation Output

### When Dynamic Data Available

```markdown
| Property | Value | Source |
|----------|-------|--------|
| Size | 147 MB | Skopeo |
| Built | 2026-01-28 | Skopeo |
| Architecture | amd64, arm64 | Skopeo |

**Security Status:** No critical CVEs
- Last checked: 2026-02-03
- Source: Red Hat Security Data API
```

### When Dynamic Data Unavailable

```markdown
| Property | Value | Source |
|----------|-------|--------|
| Size | ~150 MB (estimate) | Static |
| Built | Unknown | - |
| Architecture | Assumed amd64 | Static |

**Security Status:** Not verified (warning)
- Skopeo not installed - install for accurate metadata
- Run: `sudo dnf install skopeo`
```

---
title: Reference Documentation Overview
category: references
last_updated: 2026-01-20
---

# Reference Documentation Overview

This directory contains reference materials supporting CVE remediation decisions.

## Available Documentation

### Current Documentation
- **[cvss-scoring.md](cvss-scoring.md)** - CVSS v3.1 interpretation and Red Hat severity mappings
  - All 8 CVSS v3.1 metrics explained (AV, AC, PR, UI, S, C, I, A)
  - Red Hat 4-point severity scale (Critical/Important/Moderate/Low)
  - Why Red Hat severity ≠ CVSS score
  - Priority decision matrix
  - Real-world CVE examples (Log4Shell, Spectre, Sudo)
  - Compliance framework mappings (PCI-DSS, SOC 2, NIST 800-53)

### Future Enhancements (P2 Priority)
- **compliance-frameworks.md** - Detailed PCI-DSS, SOC 2, NIST requirements (planned)
- **glossary.md** - Red Hat terminology reference (planned)

## When to Use These Docs

**Use cvss-scoring.md when**:
- Interpreting CVSS scores and vector strings
- Understanding Red Hat severity ratings
- Prioritizing CVEs for remediation
- Explaining risk to stakeholders
- Mapping to compliance requirements (PCI-DSS, SOC 2, NIST)

## Quick Links

- Red Hat Security: https://access.redhat.com/security/
- CVSS Calculator: https://www.first.org/cvss/calculator/3.1
- Source attribution: [../SOURCES.md](../SOURCES.md)

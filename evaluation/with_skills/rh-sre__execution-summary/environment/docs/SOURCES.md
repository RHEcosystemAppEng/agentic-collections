# Red Hat Documentation Sources

This document provides attribution for all official Red Hat documentation sources used in the Remediation Agent knowledge base.

## Source Attribution Table

| Category | Document Title | Official Source URL | Sections Referenced | Last Verified |
|----------|---------------|---------------------|-------------------|---------------|
| **RHEL Package Management** | Managing Software with the DNF Tool (RHEL 9) | [docs.redhat.com](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/managing_software_with_the_dnf_tool/index) | DNF commands, updating packages, repository management | 2026-01-20 |
| **RHEL Package Management** | Software Management in RHEL 9 Adoption Guide | [docs.redhat.com](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/considerations_in_adopting_rhel_9/assembly_software-management_considerations-in-adopting-rhel-9) | RHEL 7/8/9 compatibility, migration considerations | 2026-01-20 |
| **RHEL Package Management** | RHEL 9 Release Notes | [docs.redhat.com](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/9.4_release_notes/index) | Version-specific package management features | 2026-01-20 |
| **Ansible CVE Remediation** | Red Hat Lightspeed Remediations Guide | [docs.redhat.com](https://docs.redhat.com/en/documentation/red_hat_insights/1-latest/html-single/red_hat_insights_remediations_guide/index) | Creating remediation plans, playbook generation | 2026-01-20 |
| **Ansible CVE Remediation** | Creating and Managing Remediation Plans | [docs.redhat.com](https://docs.redhat.com/en/documentation/red_hat_insights/1-latest/html/red_hat_insights_remediations_guide/creating-managing-playbooks_red-hat-insights-remediation-guide) | Playbook templates, execution patterns | 2026-01-20 |
| **Ansible CVE Remediation** | Automation Controller User Guide (AAP 2.4) | [docs.redhat.com](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.4/html/automation_controller_user_guide/controller-setting-up-insights) | Setting up Lightspeed for AAP remediations | 2026-01-20 |
| **Ansible CVE Remediation** | Creating Remediation Playbooks (RHEL 7 Security Guide) | [docs.redhat.com](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/security_guide/creating-a-remediation-ansible-playbook-to-align-the-system-with-baseline_scanning-the-system-for-configuration-compliance-and-vulnerabilities) | Ansible playbook patterns for security compliance | 2026-01-20 |
| **OpenShift Pod Eviction** | Node Maintenance (OpenShift Virtualization 4.8-4.10) | [docs.redhat.com](https://docs.redhat.com/en/documentation/openshift_container_platform/4.10/html/virtualization/node-maintenance) | Node maintenance operator, draining nodes | 2026-01-20 |
| **OpenShift Pod Eviction** | Evicting Pods Using the Descheduler | [docs.openshift.com](https://docs.openshift.com/en/container-platform/4.8/nodes/scheduling/nodes-descheduler.html) | Pod eviction strategies, descheduler policies | 2026-01-20 |
| **OpenShift Pod Eviction** | How to Handle Evicted Pods in OpenShift | [access.redhat.com](https://access.redhat.com/solutions/3521071) | Troubleshooting evicted pods, remediation steps | 2026-01-20 |
| **OpenShift Pod Eviction** | OpenShift Container Platform 4.16 Nodes | [docs.redhat.com](https://docs.redhat.com/en/documentation/openshift_container_platform/4.16/pdf/nodes/OpenShift_Container_Platform-4.16-Nodes-en-US.pdf) | Node management, pod disruption budgets | 2026-01-20 |
| **Lightspeed CVE Assessment** | Assessing Security Vulnerabilities on RHEL Systems | [docs.redhat.com](https://docs.redhat.com/en/documentation/red_hat_insights/1-latest/html/assessing_and_monitoring_security_vulnerabilities_on_rhel_systems/vuln-cves_vuln-overview) | CVE identification, classification, threat intelligence | 2026-01-20 |
| **Lightspeed CVE Assessment** | Generating Vulnerability Service Reports | [access.redhat.com](https://access.redhat.com/documentation/en-us/red_hat_insights/1-latest/html-single/generating_vulnerability_service_reports/index) | Executive reports, CVE reports, data export | 2026-01-20 |
| **Lightspeed CVE Assessment** | Red Hat CVE Database | [access.redhat.com](https://access.redhat.com/security/security-updates/cve) | Official CVE entries, security updates | 2026-01-20 |
| **Lightspeed CVE Assessment** | A Complete View of System Vulnerabilities | [redhat.com/blog](https://www.redhat.com/en/blog/complete-view-system-vulnerabilities-using-red-hat-insights) | Vulnerability service overview, best practices | 2026-01-20 |
| **CVSS Scoring** | Severity Ratings | [access.redhat.com](https://access.redhat.com/security/updates/classification) | Four-point severity scale, CVSS v3.1 scoring | 2026-01-20 |
| **CVSS Scoring** | How We Classify Security Severity Levels | [access.redhat.com](https://access.redhat.com/solutions/725593) | CVSS metrics interpretation, severity guidelines | 2026-01-20 |
| **CVSS Scoring** | Security Update Policy | [access.redhat.com](https://access.redhat.com/security/lifecycle-security-update-policy) | Security lifecycle, update policies | 2026-01-20 |
| **CVSS Scoring** | Product Security Center | [access.redhat.com](https://access.redhat.com/security/) | Security advisories, bulletins, data feeds | 2026-01-20 |

## Documentation Categories

### RHEL (Red Hat Enterprise Linux)
- **Primary Source**: Red Hat Product Documentation (docs.redhat.com)
- **Focus**: Package management (DNF/YUM), systemd, SELinux, security hardening
- **Versions Covered**: RHEL 7, 8, 9
- **Update Frequency**: Continuous (latest release notes include 2026 updates)

### Ansible Automation Platform
- **Primary Source**: Red Hat Lightspeed Documentation + Ansible Automation Platform Documentation
- **Focus**: CVE remediation playbooks, automation patterns, AAP integration
- **Current Version**: Ansible Automation Platform 2.4
- **Update Frequency**: Regular security advisories and feature updates

### OpenShift Container Platform
- **Primary Source**: OpenShift Product Documentation (docs.redhat.com/openshift)
- **Focus**: Node maintenance, pod eviction, zero-downtime updates, security
- **Versions Covered**: OpenShift 4.7-4.16
- **Update Frequency**: Per-release documentation updates

### Red Hat Lightspeed
- **Primary Source**: Red Hat Lightspeed Documentation + Customer Portal
- **Focus**: Vulnerability assessment, CVE analysis, remediation planning, system inventory
- **Current Version**: 1-latest (continuously updated)
- **Update Frequency**: Real-time CVE database updates

### Security & CVSS
- **Primary Source**: Red Hat Customer Portal - Product Security Center
- **Focus**: CVSS v3.1 scoring, severity classification, security advisories
- **Update Frequency**: Daily security bulletins and advisories

## Attribution Format

All documentation files in this knowledge base include YAML frontmatter with source attribution:

```yaml
---
title: [Document Title]
category: rhel|ansible|openshift|insights|references
sources:
  - title: [Official Doc Title]
    url: [Official URL]
    sections: [Relevant sections]
    date_accessed: YYYY-MM-DD
tags: [keywords]
applies_to: [rhel7, rhel8, rhel9, openshift4.x]
last_updated: YYYY-MM-DD
---
```

## Verification

All sources listed above were verified as active and current as of January 20, 2026. The sources are:

1. **Official Red Hat Documentation** (docs.redhat.com) - Authoritative product documentation
2. **Red Hat Customer Portal** (access.redhat.com) - Knowledge base articles and security data
3. **Red Hat Corporate Website** (redhat.com) - Official blog posts and technical articles
4. **OpenShift Documentation** (docs.openshift.com) - OpenShift Container Platform guides

## License and Usage

This knowledge base is derived from official Red Hat documentation licensed under Creative Commons Attribution-ShareAlike 4.0 International License (CC BY-SA 4.0) or similar Red Hat documentation licenses. All credit for the original content belongs to Red Hat, Inc. and its contributors.

**Important**: This knowledge base is a derivative work for educational and operational purposes. For the most up-to-date and authoritative information, always consult the official Red Hat documentation at the URLs listed above.

## Source Maintenance

This source list is maintained as part of the Remediation Agent plugin. When documentation is updated or new sources are added:

1. Update this SOURCES.md file with new entries
2. Update the YAML frontmatter in affected documentation files
3. Regenerate the semantic index using `docs/.ai-index/generate-index.py`
4. Update the "Last Verified" date in the table above

## Contact

For questions about Red Hat documentation sources or to report broken links:
- Red Hat Customer Portal: https://access.redhat.com/support
- Red Hat Documentation Feedback: https://docs.redhat.com (feedback links on each page)

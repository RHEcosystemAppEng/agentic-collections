---
title: OpenShift Security Checklist
category: security
sources:
  - title: Managing security context constraints
    url: https://docs.openshift.com/container-platform/latest/authentication/managing-security-context-constraints.html
    date_accessed: 2026-03-31
  - title: Updating cluster certificates
    url: https://docs.openshift.com/container-platform/latest/security/certificate_types_descriptions/user-provided-certificates-for-api-server.html
    date_accessed: 2026-03-31
tags: [security, security-checklist, credentials, network-security, rbac, certificates]
semantic_keywords: [security verification, security checklist, cluster hardening, credentials management, network security, certificate security, rbac security]
use_cases: [cluster-validation, security-audit, compliance-verification]
related_docs: [rbac.md, idp.md, certificate-management.md, credentials-management.md]
last_updated: 2026-03-31
---

# OpenShift Security Checklist

Comprehensive security verification checklist for OpenShift clusters.

---

## Overview

This checklist provides security verification steps for OpenShift clusters across different lifecycle stages: installation, configuration, operation, and maintenance.

**Scope**: Practical security checks using MCP tools and verification procedures.

---

## Installation Security

### Credentials

- [ ] Kubeconfig stored with 600 permissions
- [ ] Kubeadmin password stored with 600 permissions
- [ ] Credentials stored in `/tmp/` for temporary use (default)
- [ ] OFFLINE_TOKEN environment variable not exposed in logs
- [ ] SSH private keys stored with 600 permissions
- [ ] No credentials committed to version control

### Network Configuration

- [ ] API VIP configured on isolated network segment (HA clusters)
- [ ] Ingress VIP configured on isolated network segment (HA clusters)
- [ ] Firewall rules restrict API access to authorized networks
- [ ] Static networking configured correctly (if applicable)
- [ ] DNS resolution working for cluster domains

### Platform Security

- [ ] Cluster deployed on secure infrastructure (trusted provider)
- [ ] Underlying VMs/hosts hardened according to CIS benchmarks
- [ ] Boot media (ISO) downloaded from official Red Hat sources only
- [ ] Cluster communication encrypted (default, verify enabled)

---

## Authentication & Authorization

### Identity Providers

- [ ] Kubeadmin user kept enabled (unless explicitly disabled by user request)
- [ ] Identity provider configured (LDAP/OAuth/HTPasswd)
- [ ] Alternative admin user tested before disabling kubeadmin
- [ ] LDAP configured with LDAPS (encrypted)
- [ ] OAuth client secrets stored in Secrets (not hardcoded)
- [ ] GitHub/OIDC restricted to specific organizations/groups

### RBAC Configuration

- [ ] No users granted cluster-admin unnecessarily
- [ ] Service accounts use principle of least privilege
- [ ] Default service account not used for applications
- [ ] RoleBindings scoped to namespaces (not ClusterRoleBindings unless needed)
- [ ] Custom roles reviewed and minimized
- [ ] Regular RBAC audit performed (quarterly)

### Security Context Constraints (SCCs)

- [ ] Applications use `restricted-v2` SCC by default
- [ ] No applications using `privileged` SCC unless required
- [ ] SCCs granted to service accounts, not users
- [ ] Custom SCCs reviewed and justified
- [ ] `anyuid` SCC only granted when necessary

---

## Network Security

### Ingress/Egress

- [ ] Network policies configured for pod-to-pod communication
- [ ] Default deny network policy considered for sensitive namespaces
- [ ] Ingress controllers configured with TLS
- [ ] Routes use secure edge termination (edge/reencrypt/passthrough)
- [ ] External traffic filtered at firewall/load balancer level

### Certificates

- [ ] Ingress using trusted certificates (not self-signed in production)
- [ ] Certificate expiration monitored (30-day warning minimum)
- [ ] Certificate rotation tested in non-production
- [ ] Custom certificates stored securely in Secrets
- [ ] Let's Encrypt or commercial CA used for public-facing routes

### Service Mesh (if applicable)

- [ ] mTLS enabled between services
- [ ] Service mesh policies enforce encryption
- [ ] Ingress gateways configured with proper certificates

---

## Data Security

### Secrets Management

- [ ] Secrets not stored in ConfigMaps
- [ ] Secrets encrypted at rest (etcd encryption enabled)
- [ ] Sealed Secrets or external secret management used for GitOps
- [ ] Secrets rotation policy defined
- [ ] No plaintext secrets in git repositories

### Storage

- [ ] Persistent volumes encrypted (if storing sensitive data)
- [ ] Storage classes configured with appropriate access modes
- [ ] Backup encryption enabled
- [ ] Snapshot retention policy defined

### etcd Security

- [ ] etcd encrypted at rest (default, verify enabled)
- [ ] etcd backup encryption enabled
- [ ] etcd accessible only from control plane
- [ ] Regular etcd backups performed and tested

---

## Container Security

### Image Security

- [ ] Images pulled from trusted registries only
- [ ] Image pull policies set to `Always` or `IfNotPresent` (not `Never`)
- [ ] Image scanning enabled (Red Hat Quay, Clair, or alternative)
- [ ] No images running as root unless necessary
- [ ] Base images updated regularly for security patches

### Pod Security

- [ ] SecurityContext configured for pods (runAsNonRoot, capabilities dropped)
- [ ] Resource limits defined (CPU, memory)
- [ ] Liveness/readiness probes configured
- [ ] No privileged pods unless absolutely required
- [ ] Pod Security Admission configured (optional but recommended)

### Runtime Security

- [ ] SELinux enabled on nodes (default, verify active)
- [ ] CRI-O/containerd configured securely
- [ ] Runtime monitoring enabled (Falco, Sysdig, or alternative - optional)

---

## Monitoring & Logging

### Audit Logging

- [ ] Audit logging enabled (default, verify)
- [ ] Audit logs forwarded to external system (SIEM)
- [ ] Audit log retention policy defined
- [ ] Sensitive data not logged in audit logs

### Monitoring

- [ ] Prometheus monitoring operational
- [ ] Alerts configured for security events
- [ ] Certificate expiration alerts enabled
- [ ] ClusterOperator status monitored
- [ ] Node resource usage monitored

### Logging

- [ ] Cluster logging operator deployed (optional)
- [ ] Application logs forwarded to centralized logging
- [ ] Log retention policy configured
- [ ] Logs reviewed regularly for security events

---

## Operational Security

### Updates & Patching

- [ ] Cluster update channel configured (stable recommended)
- [ ] Regular cluster updates scheduled
- [ ] Node updates tested in non-production first
- [ ] CVE monitoring enabled
- [ ] Security advisories reviewed (access.redhat.com)

### Backup & Recovery

- [ ] etcd backups automated and tested
- [ ] Application data backups configured
- [ ] Disaster recovery plan documented and tested
- [ ] Backup retention policy defined
- [ ] Backup restoration tested quarterly

### Access Control

- [ ] API server access restricted to authorized networks
- [ ] Console access protected (firewall, VPN, or private network)
- [ ] SSH access to nodes restricted (bastion host, jump server)
- [ ] MFA enabled for administrative access (when possible)
- [ ] Session timeout configured

---

## Compliance & Governance

### Policy Enforcement

- [ ] Admission webhooks configured for policy enforcement
- [ ] OPA Gatekeeper or Red Hat Advanced Cluster Security deployed (optional)
- [ ] ResourceQuotas configured per namespace
- [ ] LimitRanges configured per namespace
- [ ] Pod disruption budgets configured for critical workloads

### Compliance

- [ ] CIS benchmarks reviewed and applied
- [ ] Compliance operator deployed (optional)
- [ ] Regular security scans performed
- [ ] Vulnerability remediation tracked
- [ ] Security policies documented

### Documentation

- [ ] Cluster architecture documented
- [ ] Security configuration documented
- [ ] Incident response plan defined
- [ ] Contact information for security team maintained
- [ ] Runbooks for common security scenarios created

---

## Multi-Tenancy (if applicable)

### Namespace Isolation

- [ ] Namespaces created per team/project
- [ ] Network policies isolate namespaces
- [ ] ResourceQuotas prevent resource exhaustion
- [ ] RBAC limits cross-namespace access
- [ ] Pod Security Standards enforced per namespace

### Resource Sharing

- [ ] Shared services deployed in dedicated namespaces
- [ ] Service accounts scoped appropriately
- [ ] No cluster-admin granted to tenant users
- [ ] Tenant workloads cannot access platform namespaces

---

## Cloud Provider Security (if applicable)

### AWS (ROSA)

- [ ] IAM roles follow least privilege
- [ ] Security groups properly configured
- [ ] VPC configured with private subnets
- [ ] KMS encryption enabled for EBS volumes
- [ ] CloudTrail logging enabled

### Azure (ARO)

- [ ] Azure AD integrated
- [ ] NSGs properly configured
- [ ] Managed identities used instead of service principals
- [ ] Azure Key Vault used for secrets
- [ ] Azure Monitor enabled

### GCP (OSD)

- [ ] Cloud IAM roles minimized
- [ ] Firewall rules reviewed
- [ ] GKE security features enabled
- [ ] Cloud KMS for encryption
- [ ] Cloud Logging enabled

---

## Verification Commands

**Note**: These verification commands require direct cluster access via `oc` CLI or the `openshift-administration` MCP server when using Claude Code with KUBECONFIG set.

### Check ClusterOperators Status

```bash
oc get clusteroperators
# Expected: All operators available=true, degraded=false
```

### Check Node Security

```bash
oc get nodes
# Verify: All nodes Ready, SELinux enforcing
```

### List ServiceAccounts with Elevated Privileges

```bash
oc get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name=="cluster-admin") | .metadata.name'
# Review: Ensure only necessary accounts listed
```

### Check Certificate Expiration

```bash
oc get apiserver cluster -o yaml
# Review: Certificate dates in status
```

### Verify Audit Logging

```bash
oc get apiserver cluster -o yaml
# Verify: spec.audit configuration present
```

### List Privileged Pods

```bash
oc get pods --all-namespaces -o json | \
  jq '.items[] | select(.spec.containers[].securityContext.privileged==true) | .metadata.name'
# Review: Ensure privileged access is justified
```

---

## Incident Response

### Preparation

- [ ] Incident response plan documented
- [ ] Security contact information available
- [ ] Escalation procedures defined
- [ ] Communication channels established

### Detection

- [ ] Monitoring alerts configured
- [ ] Log analysis procedures defined
- [ ] Anomaly detection enabled (optional)
- [ ] Regular security audits scheduled

### Response

- [ ] Incident triage procedure defined
- [ ] Evidence collection process documented
- [ ] Containment strategies prepared
- [ ] Recovery procedures tested

### Post-Incident

- [ ] Post-mortem process defined
- [ ] Lessons learned documented
- [ ] Security improvements implemented
- [ ] Stakeholders notified

---

## Regular Review Schedule

### Daily

- [ ] Monitor ClusterOperator status
- [ ] Review security alerts
- [ ] Check backup completion

### Weekly

- [ ] Review audit logs for anomalies
- [ ] Check certificate expiration warnings
- [ ] Verify node health and security

### Monthly

- [ ] Review RBAC configurations
- [ ] Audit user access
- [ ] Review network policies
- [ ] Check for CVE advisories

### Quarterly

- [ ] Full security audit
- [ ] Test disaster recovery
- [ ] Review and update documentation
- [ ] Compliance assessment

### Annually

- [ ] Penetration testing (optional but recommended)
- [ ] Security architecture review
- [ ] Update security policies
- [ ] Review and renew certifications

---

## Related Documentation

- [Credentials Management](./credentials-management.md) - Authentication and secrets
- [RBAC](./rbac.md) - Access control
- [Certificate Rotation](./certificate-rotation.md) - Certificate management
- [Identity Providers](./idp.md) - User authentication

---

## Official References

- [OpenShift Security Guide](https://docs.openshift.com/container-platform/latest/security/index.html)
- [CIS Benchmarks](https://www.cisecurity.org/benchmark/kubernetes)
- [Red Hat Security Advisories](https://access.redhat.com/security/security-updates/)

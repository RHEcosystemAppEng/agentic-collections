# Documentation TODO List

Future documentation topics deferred from initial cluster-creator skill reorganization.

---

## Priority: High

### 1. Security & Compliance

**File**: `security-compliance.md`

**Topics to Cover**:
- **Security Context Constraints (SCC)**
  - Built-in SCCs (restricted, anyuid, privileged)
  - Custom SCC creation
  - SCC assignment to service accounts
  - Troubleshooting SCC denials

- **Pod Security Admission**
  - Pod Security Standards (privileged, baseline, restricted)
  - Namespace-level enforcement
  - Migration from PSP to PSA

- **Network Policies (Advanced)**
  - Multi-tier application isolation
  - Ingress/egress rule patterns
  - Default deny policies
  - Policy testing and validation

- **Secrets Management**
  - Sealed Secrets operator
  - External Secrets Operator (AWS Secrets Manager, Vault integration)
  - Best practices for credential rotation

**Rationale**: Critical for production security posture

---

### 2. Disaster Recovery & Business Continuity

**File**: `disaster-recovery.md`

**Topics to Cover**:
- **Application Backup with OADP/Velero**
  - Operator installation
  - Backup configuration (PVs, resources, schedules)
  - Restore procedures
  - Cross-cluster migration

- **Multi-Cluster Failover**
  - Active-passive cluster setup
  - DNS-based failover
  - Application state replication
  - Disaster recovery testing

**Rationale**: Essential for production availability requirements

---

## Priority: Medium

### 3. Advanced Networking

**File**: `advanced-networking.md` (or extend `networking.md`)

**Topics to Cover**:
- **Service Mesh (Red Hat OpenShift Service Mesh / Istio)**
  - Installation and configuration
  - Traffic management (routing, load balancing)
  - Security (mTLS, authorization policies)
  - Observability (tracing, metrics)
  - Multi-cluster service mesh

**Rationale**: Growing adoption for microservices architectures

---

### 4. Workload Management (Advanced)

**File**: `workload-management.md`

**Topics to Cover**:
- **Resource Quotas and Limits** (detailed)
  - Project-level quotas
  - Cluster-level resource allocation
  - Quota scopes and priority classes

- **Quality of Service (QoS) Classes**
  - Guaranteed, Burstable, BestEffort
  - QoS impact on scheduling and eviction

- **Pod Scheduling**
  - Node selectors and affinity/anti-affinity
  - Taints and tolerations
  - Pod topology spread constraints
  - Custom schedulers

- **Autoscaling**
  - Horizontal Pod Autoscaler (HPA) configuration
  - Vertical Pod Autoscaler (VPA) usage
  - Cluster Autoscaler (cloud providers)
  - KEDA (event-driven autoscaling)

**Rationale**: Optimizes resource utilization and application performance

---

## Priority: Low

### 5. CI/CD Integration

**File**: `cicd-integration.md`

**Topics to Cover**:
- OpenShift Pipelines (Tekton)
- GitOps with ArgoCD/Flux
- Image build strategies (S2I, Dockerfile, Buildah)
- Registry integration (Quay, external registries)

**Rationale**: DevOps workflows, lower priority for cluster admin persona

---

### 6. Multi-Tenancy Patterns

**File**: `multi-tenancy.md`

**Topics to Cover**:
- Namespace isolation strategies
- Project templates
- Tenant resource quotas
- Network segmentation
- RBAC patterns for multi-team environments

**Rationale**: Enterprise environments with multiple teams

---

## Completed Documentation

✅ `INDEX.md` - Master navigation
✅ `quick-reference.md` - Common commands and scenarios
✅ `input-validation-guide.md` - Parameter validation rules
✅ `providers.md` - Infrastructure provider details
✅ `platforms.md` - OpenShift platform types
✅ `networking.md` - Network configuration (includes Egress IP, Multus, SR-IOV, Dual-Stack)
✅ `host-requirements.md` - Hardware specifications
✅ `storage.md` - Storage options and CSI drivers
✅ `examples.md` - Real-world cluster configurations
✅ `credentials-management.md` - Authentication and authorization
✅ `day-2-operations.md` - Monitoring, logging, updates, scaling
✅ `certificate-management.md` - Certificate lifecycle
✅ `backup-restore.md` - etcd backup and restore
✅ `troubleshooting.md` - Common issues and resolutions

---

## Notes

- Keep all new documentation **concise** (optimize context usage)
- Include references to official Red Hat documentation
- Follow existing doc structure (YAML frontmatter, code examples, cross-references)
- Update `INDEX.md` when new docs are added

---

**Last Updated**: 2026-03-17

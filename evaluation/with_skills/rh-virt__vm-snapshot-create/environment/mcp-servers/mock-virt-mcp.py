#!/usr/bin/env python3
"""
Mock OpenShift MCP Server for OpenShift Virtualization.

Faithfully implements the tool interface of:
  https://github.com/openshift/openshift-mcp-server
Enabled toolsets: config, core, kubevirt

Simulated OpenShift cluster:
  Cluster:    ocp-virt-prod (OpenShift 4.15, K8s 1.28)
  Namespaces: virt-prod-dc1, virt-prod-dc2, virt-staging, virt-dev,
              openshift-cnv, openshift-compliance, openshift-monitoring, default
  Nodes:      8 workers (hypervisor-class)
  VMs:        32 KubeVirt VirtualMachines
  Security:   5 VulnerabilityReports in openshift-compliance
"""

import hashlib
import json
from typing import Optional

import yaml
from fastmcp import FastMCP

mcp = FastMCP("openshift-virtualization")

CLUSTER = "ocp-virt-prod"
API_URL = "https://api.ocp-virt-prod.example.com:6443"
K8S_VER = "v1.28.12+f26e58e"
OCP_VER = "4.15.8"
NOW = "2026-03-02T12:00:00Z"
CREATED = "2025-11-15T10:00:00Z"

# ═══════════════════════════════════════════════════════════════════════════
#  COMPACT DATA
# ═══════════════════════════════════════════════════════════════════════════

NAMESPACES = [
    ("virt-prod-dc1", {"env": "production", "dc": "dc1"}),
    ("virt-prod-dc2", {"env": "production", "dc": "dc2"}),
    ("virt-staging", {"env": "staging"}),
    ("virt-dev", {"env": "development"}),
    ("openshift-cnv", {"operator": "kubevirt-hyperconverged"}),
    ("openshift-compliance", {"operator": "compliance"}),
    ("openshift-monitoring", {}),
    ("default", {}),
    ("prod-vms", {"env": "production"}),
]


def _n(name, zone, status, unschedulable, cpu_cap, cpu_use, mem_cap, mem_use, pods,
       taints=None, maint=None, itype="m5.4xlarge"):
    return dict(name=name, zone=zone, status=status, unschedulable=unschedulable,
                cpu_cap=cpu_cap, cpu_use=cpu_use, mem_cap=mem_cap, mem_use=mem_use,
                pods=pods, taints=taints or [], maint=maint, itype=itype)


NODES = [
    _n("hv-prod-dc1-01", "dc1", "Ready", False, 16000, 11840, 65536, 44564, 12),
    _n("hv-prod-dc1-02", "dc1", "Ready", False, 16000, 14080, 65536, 53739, 14),
    _n("hv-prod-dc1-03", "dc1", "Ready,SchedulingDisabled", True, 16000, 1920, 65536, 9830, 6,
       taints=[{"key": "node.kubernetes.io/unschedulable", "effect": "NoSchedule"}],
       maint="Scheduled firmware update — ETA 6 hours"),
    _n("hv-prod-dc2-01", "dc2", "Ready", False, 16000, 11360, 65536, 41287, 12),
    _n("hv-prod-dc2-02", "dc2", "Ready", False, 16000, 12640, 65536, 49807, 15),
    _n("hv-staging-01", "staging", "Ready", False, 8000, 4160, 32768, 15728, 10, itype="m5.2xlarge"),
    _n("hv-staging-02", "staging", "Ready", False, 8000, 3040, 32768, 11468, 8, itype="m5.2xlarge"),
    _n("hv-dev-01", "dev", "Ready", False, 8000, 4880, 32768, 18022, 14, itype="m5.2xlarge"),
]


def _vm(name, ns, node, os, env, labels, cpu, mem, status, ready, last_seen,
        conds=None, pinned=False):
    return dict(name=name, ns=ns, node=node, os=os, env=env, labels=labels,
                cpu=cpu, mem=mem, status=status, ready=ready,
                last_seen=last_seen, conds=conds or [], pinned=pinned)


VMS = [
    # ── virt-prod-dc1 / hv-prod-dc1-01 (4) ──────────────────────────────
    _vm("vm-web-prod-01", "virt-prod-dc1", "hv-prod-dc1-01", "rhel-9.3", "production",
        {"app": "web", "compliance/pci-dss": "true", "compliance/soc2": "true",
         "criticality": "high", "customer-facing": "true"}, 4, 8, "Running", True, 1),
    _vm("vm-web-prod-02", "virt-prod-dc1", "hv-prod-dc1-01", "rhel-9.3", "production",
        {"app": "web", "compliance/pci-dss": "true"}, 4, 8, "Running", True, 1),
    _vm("vm-lb-prod-01", "virt-prod-dc1", "hv-prod-dc1-01", "rhel-8.8", "production",
        {"app": "lb", "criticality": "high", "ha": "true"}, 2, 4, "Running", True, 1),
    _vm("vm-monitor-prod-01", "virt-prod-dc1", "hv-prod-dc1-01", "rhel-9.3", "production",
        {"app": "monitoring"}, 2, 4, "Running", True, 1),

    # ── virt-prod-dc1 / hv-prod-dc1-02 (4 — CRITICAL utilization) ───────
    _vm("vm-web-prod-03", "virt-prod-dc1", "hv-prod-dc1-02", "rhel-9.2", "production",
        {"app": "web", "customer-facing": "true"}, 4, 8, "Running", True, 2),
    _vm("vm-api-prod-01", "virt-prod-dc1", "hv-prod-dc1-02", "rhel-9.2", "production",
        {"app": "api", "compliance/soc2": "true", "criticality": "high"}, 4, 8, "Running", True, 1),
    _vm("vm-cache-prod-01", "virt-prod-dc1", "hv-prod-dc1-02", "rhel-8.9", "production",
        {"app": "cache", "ha": "true"}, 2, 4, "Running", True, 1),
    _vm("vm-etl-prod-01", "virt-prod-dc1", "hv-prod-dc1-02", "rhel-8.9", "production",
        {"app": "etl", "compliance/hipaa": "true"},
        4, 8, "Running", True, 1,
        conds=[("Degraded", "True", "High I/O latency: avg write latency 45ms (threshold 20ms)")]),

    # ── virt-prod-dc1 / hv-prod-dc1-03 (2 — MAINTENANCE node) ───────────
    _vm("vm-backup-prod-01", "virt-prod-dc1", "hv-prod-dc1-03", "rhel-8.8", "production",
        {"app": "backup", "criticality": "low"}, 2, 4, "Stopped", False, 3, pinned=True),
    _vm("vm-legacy-auth-01", "virt-prod-dc1", "hv-prod-dc1-03", "rhel-7.9", None,
        {"app": "auth", "criticality": "high", "legacy": "true"},
        2, 4, "Running", True, 3,
        conds=[("Degraded", "True", "EOL operating system: RHEL 7.9 reached end of life")]),

    # ── virt-prod-dc2 / hv-prod-dc2-01 (4) ──────────────────────────────
    _vm("vm-api-prod-02", "virt-prod-dc2", "hv-prod-dc2-01", "rhel-9.2", "production",
        {"app": "api", "compliance/soc2": "true"}, 4, 8, "Running", True, 2),
    _vm("vm-db-prod-01", "virt-prod-dc2", "hv-prod-dc2-01", "rhel-9.3", "production",
        {"app": "db", "criticality": "high", "compliance/pci-dss": "true",
         "compliance/soc2": "true"}, 8, 16, "Running", True, 1),
    _vm("vm-queue-prod-01", "virt-prod-dc2", "hv-prod-dc2-01", "rhel-9.2", "production",
        {"app": "queue", "compliance/soc2": "true"}, 2, 4, "Running", True, 1),
    _vm("vm-legacy-pay-01", "virt-prod-dc2", "hv-prod-dc2-01", "rhel-8.7", None,
        {"app": "payment-gateway", "criticality": "high", "legacy": "true"},
        4, 8, "Running", True, 2),

    # ── virt-prod-dc2 / hv-prod-dc2-02 (5 — WARNING utilization) ────────
    _vm("vm-db-prod-02", "virt-prod-dc2", "hv-prod-dc2-02", "rhel-9.3", "production",
        {"app": "db", "criticality": "high", "compliance/soc2": "true"},
        8, 16, "Running", True, 1),
    _vm("vm-cache-prod-02", "virt-prod-dc2", "hv-prod-dc2-02", "rhel-8.9", "production",
        {"app": "cache"}, 2, 4, "Running", False, 12,
        conds=[("AgentConnected", "False",
                "Guest agent has not responded for 12 days")]),
    _vm("vm-batch-prod-01", "virt-prod-dc2", "hv-prod-dc2-02", "rhel-8.9", "production",
        {"app": "batch"}, 4, 8, "Stopped", False, 4),
    _vm("vm-legacy-reports-01", "virt-prod-dc2", "hv-prod-dc2-02", "rhel-8.6", None,
        {"app": "financial-reporting", "legacy": "true"},
        2, 4, "Running", True, 6),
    _vm("vm-log-prod-01", "virt-prod-dc2", "hv-prod-dc2-02", "rhel-9.2", "production",
        {"app": "logging", "compliance/soc2": "true"}, 2, 4, "Running", True, 1),

    # ── prod-vms (instruction-specific) ──────────────────────────────────
    _vm("production-db", "prod-vms", "hv-prod-dc2-01", "rhel-9.3", "production",
        {"app": "db", "criticality": "high", "compliance/pci-dss": "true"},
        8, 16, "Running", True, 1),

    # ── virt-staging / hv-staging-01 (4) ─────────────────────────────────
    _vm("vm-web-stg-01", "virt-staging", "hv-staging-01", "rhel-9.2", "staging",
        {"app": "web"}, 2, 4, "Running", True, 1),
    _vm("vm-web-stg-02", "virt-staging", "hv-staging-01", "rhel-9.2", "staging",
        {"app": "web"}, 2, 4, "Running", True, 2),
    _vm("vm-api-stg-01", "virt-staging", "hv-staging-01", "rhel-8.9", "staging",
        {"app": "api"}, 2, 4, "Running", True, 2),
    _vm("vm-perf-stg-01", "virt-staging", "hv-staging-01", "rhel-9.3", "staging",
        {"app": "perf-test"}, 4, 8, "Running", True, 1),

    # ── virt-staging / hv-staging-02 (3) ─────────────────────────────────
    _vm("vm-db-stg-01", "virt-staging", "hv-staging-02", "rhel-9.2", "staging",
        {"app": "db"}, 4, 8, "Running", True, 1),
    _vm("vm-db-stg-02", "virt-staging", "hv-staging-02", "rhel-9.2", "staging",
        {"app": "db"}, 4, 8, "Paused", False, 3),
    _vm("vm-qa-stg-01", "virt-staging", "hv-staging-02", "rhel-8.9", "staging",
        {"app": "qa"}, 2, 4, "Running", True, 1),

    # ── virt-dev / hv-dev-01 (6) ─────────────────────────────────────────
    _vm("vm-dev-01", "virt-dev", "hv-dev-01", "rhel-8.8", "development",
        {"app": "dev"}, 2, 4, "Running", True, 2),
    _vm("vm-dev-02", "virt-dev", "hv-dev-01", "rhel-8.8", "development",
        {"app": "dev"}, 2, 4, "Running", True, 2),
    _vm("vm-dev-03", "virt-dev", "hv-dev-01", "rhel-8.9", "development",
        {"app": "dev"}, 2, 4, "Stopped", False, 14,
        conds=[("AgentConnected", "False", "Guest agent not responding")]),
    _vm("vm-sandbox-01", "virt-dev", "hv-dev-01", "rhel-9.2", "development",
        {"app": "sandbox"}, 2, 4, "Running", True, 1),
    _vm("vm-test-01", "virt-dev", "hv-dev-01", "rhel-9.3", "development",
        {"app": "test"}, 2, 4, "Running", True, 1),
    _vm("vm-archive-01", "virt-dev", "hv-dev-01", "rhel-8.6", "development",
        {"app": "archive", "legacy": "true"},
        2, 4, "Running", False, 45,
        conds=[("AgentConnected", "False",
                "Guest agent has not responded for 45 days")]),
]


def _adv(adv_id, name, synopsis, severity, cvss, compliance, deadline,
         description, affected, remediation_available=True):
    return dict(id=adv_id, name=name, synopsis=synopsis, severity=severity,
                cvss=cvss, compliance=compliance, deadline=deadline,
                description=description, affected=affected,
                remediation_available=remediation_available)


ADVISORIES = [
    _adv("RHSA-2026:1234", "rhsa-2026-1234",
         "Critical: kernel security update", "Critical", 9.8,
         ["pci-dss", "soc2"], 30,
         "Remote code execution in kernel network stack allows unauthenticated "
         "attackers to execute arbitrary code via crafted packets.",
         [("vm-web-prod-01", "virt-prod-dc1", "Vulnerable"),
          ("vm-web-prod-02", "virt-prod-dc1", "Vulnerable"),
          ("vm-db-prod-01", "virt-prod-dc2", "Vulnerable"),
          ("vm-legacy-pay-01", "virt-prod-dc2", "Vulnerable"),
          ("vm-web-stg-01", "virt-staging", "Remediated"),
          ("vm-web-stg-02", "virt-staging", "Remediated")]),
    _adv("RHSA-2026:2345", "rhsa-2026-2345",
         "Important: openssl security update", "Important", 7.8,
         ["soc2"], 60,
         "Buffer overflow in OpenSSL TLS handshake processing allows "
         "authenticated attackers to escalate privileges.",
         [("vm-api-prod-01", "virt-prod-dc1", "Vulnerable"),
          ("vm-api-prod-02", "virt-prod-dc2", "Vulnerable"),
          ("vm-db-prod-02", "virt-prod-dc2", "Vulnerable"),
          ("vm-queue-prod-01", "virt-prod-dc2", "Vulnerable"),
          ("vm-log-prod-01", "virt-prod-dc2", "Vulnerable"),
          ("vm-api-stg-01", "virt-staging", "Remediated"),
          ("vm-legacy-reports-01", "virt-prod-dc2", "Remediated")]),
    _adv("RHSA-2026:3456", "rhsa-2026-3456",
         "Moderate: glibc security update", "Moderate", 5.4,
         ["hipaa"], 90,
         "Information disclosure in glibc DNS resolver allows adjacent "
         "network attackers to read portions of process memory.",
         [("vm-etl-prod-01", "virt-prod-dc1", "Vulnerable"),
          ("vm-monitor-prod-01", "virt-prod-dc1", "Vulnerable"),
          ("vm-cache-prod-02", "virt-prod-dc2", "Vulnerable"),
          ("vm-dev-01", "virt-dev", "Vulnerable"),
          ("vm-dev-02", "virt-dev", "Vulnerable"),
          ("vm-batch-prod-01", "virt-prod-dc2", "Vulnerable"),
          ("vm-dev-03", "virt-dev", "Remediated"),
          ("vm-archive-01", "virt-dev", "Remediated")]),
    _adv("RHSA-2026:4567", "rhsa-2026-4567",
         "Important: httpd security update", "Important", 7.2,
         ["pci-dss"], 90,
         "Request smuggling in Apache httpd allows attackers to bypass "
         "access controls on payment-processing endpoints.",
         [("vm-legacy-pay-01", "virt-prod-dc2", "Vulnerable"),
          ("vm-lb-prod-01", "virt-prod-dc1", "Vulnerable"),
          ("vm-legacy-auth-01", "virt-prod-dc1", "Vulnerable"),
          ("vm-web-prod-03", "virt-prod-dc1", "Vulnerable"),
          ("vm-legacy-reports-01", "virt-prod-dc2", "Remediated")]),
    _adv("RHSA-2026:5678", "rhsa-2026-5678",
         "Low: systemd information disclosure", "Low", 3.1,
         [], None,
         "Information disclosure in systemd-journald allows local users to "
         "read journal entries from other user sessions under specific "
         "SELinux configurations.",
         [("vm-monitor-prod-01", "virt-prod-dc1", "Vulnerable"),
          ("vm-batch-prod-01", "virt-prod-dc2", "Vulnerable"),
          ("vm-db-stg-02", "virt-staging", "Vulnerable"),
          ("vm-archive-01", "virt-dev", "Vulnerable")],
         remediation_available=False),
]

# Build per-VM advisory lookup
_VM_ADV = {}
for _a in ADVISORIES:
    for _vn, _vns, _vs in _a["affected"]:
        _VM_ADV.setdefault(_vn, []).append(
            {"id": _a["id"], "severity": _a["severity"], "status": _vs,
             "remediationAvailable": _a["remediation_available"]})

EVENTS = [
    ("virt-prod-dc1", "Warning", "NodeSchedulingDisabled",
     "Node/hv-prod-dc1-03",
     "Node cordoned for maintenance: Scheduled firmware update — ETA 6 hours"),
    ("virt-prod-dc2", "Warning", "GuestAgentNotResponding",
     "VirtualMachine/vm-cache-prod-02",
     "Guest agent has not responded for 12 days — last contact 2026-02-18"),
    ("virt-dev", "Warning", "GuestAgentNotResponding",
     "VirtualMachine/vm-archive-01",
     "Guest agent has not responded for 45 days — last contact 2026-01-16"),
    ("virt-dev", "Warning", "GuestAgentNotResponding",
     "VirtualMachine/vm-dev-03",
     "Guest agent not responding — VM stopped for 14 days"),
    ("virt-prod-dc1", "Warning", "HighIOLatency",
     "VirtualMachineInstance/vm-etl-prod-01",
     "Average write latency 45ms exceeds threshold 20ms"),
    ("virt-prod-dc1", "Warning", "EOLOperatingSystem",
     "VirtualMachine/vm-legacy-auth-01",
     "RHEL 7.9 has reached end of life — no further security updates"),
    ("virt-prod-dc2", "Normal", "GracefulShutdown",
     "VirtualMachine/vm-batch-prod-01",
     "VM stopped by scheduler after batch job completion"),
    ("virt-staging", "Normal", "UserPaused",
     "VirtualMachineInstance/vm-db-stg-02",
     "VM paused by user request"),
    ("openshift-compliance", "Normal", "ScanCompleted",
     "VulnerabilityReport/rhsa-2026-1234",
     "Vulnerability scan completed: 6 affected VMs, 4 vulnerable"),
    ("openshift-compliance", "Normal", "ScanCompleted",
     "VulnerabilityReport/rhsa-2026-2345",
     "Vulnerability scan completed: 7 affected VMs, 5 vulnerable"),
    ("openshift-compliance", "Normal", "ScanCompleted",
     "VulnerabilityReport/rhsa-2026-3456",
     "Vulnerability scan completed: 8 affected VMs, 6 vulnerable"),
    ("openshift-compliance", "Normal", "ScanCompleted",
     "VulnerabilityReport/rhsa-2026-4567",
     "Vulnerability scan completed: 5 affected VMs, 4 vulnerable"),
    ("openshift-compliance", "Warning", "NoRemediationAvailable",
     "VulnerabilityReport/rhsa-2026-5678",
     "Advisory RHSA-2026:5678 has no vendor remediation — "
     "compensating controls required for 4 vulnerable VMs"),
]


# ═══════════════════════════════════════════════════════════════════════════
#  RESOURCE BUILDERS
# ═══════════════════════════════════════════════════════════════════════════

def _os_parts(os_str):
    """Parse 'rhel-9.3' into (id, version, pretty)."""
    parts = os_str.split("-", 1)
    oid = parts[0]
    ver = parts[1] if len(parts) > 1 else ""
    major = ver.split(".")[0] if ver else ""
    pretty = f"Red Hat Enterprise Linux {major} ({ver})" if oid == "rhel" else os_str
    return oid, ver, pretty


def _uid(name):
    return hashlib.md5(name.encode()).hexdigest()[:8] + "-0000-0000-0000-" + \
           hashlib.md5(name.encode()).hexdigest()[:12]


def _pod_hash(name):
    return hashlib.md5(name.encode()).hexdigest()[:5]


def _firmware_uuid(name):
    h = hashlib.sha256(name.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-4{h[13:16]}-{h[16:20]}-{h[20:32]}"


def _firmware_serial(name):
    h = hashlib.sha256((name + "-serial").encode()).hexdigest()[:12]
    return f"sn-{h}"


def _build_vm(vm):
    """Build a kubevirt.io/v1 VirtualMachine resource dict."""
    labels = {"kubevirt.io/domain": vm["name"], "vm.kubevirt.io/name": vm["name"]}
    if vm["env"]:
        labels["env"] = vm["env"]
    labels.update(vm["labels"])

    annotations = {"vm.kubevirt.io/os": vm["os"]}
    adv_map = _VM_ADV.get(vm["name"])
    if adv_map:
        annotations["security.openshift.io/vulnerabilities"] = json.dumps(
            {a["id"]: a["status"] for a in adv_map})

    is_running = vm["status"] in ("Running", "Paused")
    conditions = [
        {"type": "Ready", "status": str(vm["ready"]),
         "lastTransitionTime": CREATED},
    ]
    agent_connected = True
    for ct, cs, cm in vm["conds"]:
        if ct == "AgentConnected":
            agent_connected = False
            conditions.append({"type": ct, "status": cs, "message": cm,
                               "lastTransitionTime": CREATED})
        else:
            conditions.append({"type": ct, "status": cs, "message": cm,
                               "lastTransitionTime": CREATED})
    if agent_connected and is_running:
        conditions.append({"type": "AgentConnected", "status": "True",
                           "lastTransitionTime": CREATED})

    res = {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "name": vm["name"],
            "namespace": vm["ns"],
            "uid": _uid(vm["name"]),
            "labels": labels,
            "annotations": annotations,
            "creationTimestamp": CREATED,
        },
        "spec": {
            "running": is_running,
            "template": {
                "metadata": {"labels": {
                    "kubevirt.io/domain": vm["name"],
                    "vm.kubevirt.io/name": vm["name"],
                }},
                "spec": {
                    "domain": {
                        "cpu": {"cores": vm["cpu"], "sockets": 1, "threads": 1},
                        "memory": {"guest": f"{vm['mem']}Gi"},
                        "resources": {
                            "requests": {"cpu": str(vm["cpu"]),
                                         "memory": f"{vm['mem']}Gi"},
                        },
                        "firmware": {
                            "uuid": _firmware_uuid(vm["name"]),
                            "serial": _firmware_serial(vm["name"]),
                        },
                    },
                    "volumes": [
                        {"name": "rootdisk",
                         "persistentVolumeClaim": {
                             "claimName": f"{vm['name']}-rootdisk"}},
                    ],
                },
            },
        },
        "status": {
            "printableStatus": vm["status"],
            "ready": vm["ready"],
            "created": True,
            "conditions": conditions,
        },
    }
    if vm.get("pinned"):
        res["spec"]["template"]["spec"]["nodeSelector"] = {
            "kubernetes.io/hostname": vm["node"]
        }
    return res


def _build_vmi(vm):
    """Build a kubevirt.io/v1 VirtualMachineInstance (only for running/paused VMs)."""
    if vm["status"] not in ("Running", "Paused"):
        return None
    oid, ver, pretty = _os_parts(vm["os"])
    phase = "Running" if vm["status"] == "Running" else "Paused"
    ip_hash = int(hashlib.md5(vm["name"].encode()).hexdigest()[:4], 16)
    ip = f"10.244.{(ip_hash >> 8) & 0xFF}.{ip_hash & 0xFF}"

    conditions = [{"type": "Ready", "status": str(vm["ready"])}]
    for ct, cs, cm in vm["conds"]:
        conditions.append({"type": ct, "status": cs, "message": cm})

    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachineInstance",
        "metadata": {
            "name": vm["name"],
            "namespace": vm["ns"],
            "uid": _uid(vm["name"] + "-vmi"),
            "labels": {"kubevirt.io/domain": vm["name"],
                        "vm.kubevirt.io/name": vm["name"]},
            "ownerReferences": [{
                "apiVersion": "kubevirt.io/v1", "kind": "VirtualMachine",
                "name": vm["name"], "uid": _uid(vm["name"]),
            }],
            "creationTimestamp": CREATED,
        },
        "status": {
            "phase": phase,
            "nodeName": vm["node"],
            "guestOSInfo": {"id": oid, "version": ver, "prettyName": pretty},
            "interfaces": [{"ipAddress": ip, "name": "default"}],
            "conditions": conditions,
            "migrationMethod": "LiveMigration",
            "activePods": {_uid(vm["name"] + "-pod"): vm["node"]},
        },
    }


def _build_node(n):
    """Build a v1/Node resource dict."""
    labels = {
        "kubernetes.io/hostname": n["name"],
        "node-role.kubernetes.io/worker": "",
        "topology.kubernetes.io/zone": n["zone"],
        "node.kubernetes.io/instance-type": n["itype"],
    }
    if not n["unschedulable"]:
        labels["kubevirt.io/schedulable"] = "true"
    annotations = {}
    if n["maint"]:
        annotations["machine.openshift.io/maintenance"] = n["maint"]

    conditions = [{"type": "Ready", "status": "True",
                   "lastTransitionTime": CREATED}]
    if n["unschedulable"]:
        conditions.append({"type": "MemoryPressure", "status": "False"})
        conditions.append({"type": "DiskPressure", "status": "False"})

    cpu_str = str(n["cpu_cap"] // 1000)
    mem_ki = n["mem_cap"] * 1024

    res = {
        "apiVersion": "v1",
        "kind": "Node",
        "metadata": {
            "name": n["name"],
            "uid": _uid(n["name"]),
            "labels": labels,
            "annotations": annotations,
            "creationTimestamp": CREATED,
        },
        "spec": {
            "unschedulable": n["unschedulable"],
        },
        "status": {
            "conditions": conditions,
            "capacity": {
                "cpu": cpu_str, "memory": f"{mem_ki}Ki", "pods": "250",
                "devices.kubevirt.io/kvm": "1",
                "devices.kubevirt.io/tun": "1",
                "devices.kubevirt.io/vhost-net": "1",
            },
            "allocatable": {
                "cpu": f"{n['cpu_cap'] - 200}m",
                "memory": f"{mem_ki - 1024}Ki", "pods": "250",
                "devices.kubevirt.io/kvm": "1",
                "devices.kubevirt.io/tun": "1",
                "devices.kubevirt.io/vhost-net": "1",
            },
            "nodeInfo": {
                "kubeletVersion": K8S_VER,
                "osImage": "Red Hat Enterprise Linux CoreOS 415.92.202402130034-0",
                "containerRuntimeVersion": "cri-o://1.28.4",
                "kernelVersion": "5.14.0-284.52.1.el9_2.x86_64",
                "architecture": "amd64",
                "operatingSystem": "linux",
            },
        },
    }
    if n["taints"]:
        res["spec"]["taints"] = n["taints"]
    return res


def _build_vuln_report(adv):
    """Build a security.openshift.io/v1 VulnerabilityReport resource."""
    vuln_count = sum(1 for _, _, s in adv["affected"] if s == "Vulnerable")
    rem_count = sum(1 for _, _, s in adv["affected"] if s == "Remediated")
    return {
        "apiVersion": "security.openshift.io/v1",
        "kind": "VulnerabilityReport",
        "metadata": {
            "name": adv["name"],
            "namespace": "openshift-compliance",
            "uid": _uid(adv["name"]),
            "labels": {
                "advisory-id": adv["id"],
                "severity": adv["severity"].lower(),
            },
            "creationTimestamp": CREATED,
        },
        "spec": {
            "advisoryId": adv["id"],
            "synopsis": adv["synopsis"],
            "severity": adv["severity"],
            "cvssScore": adv["cvss"],
            "complianceImpact": adv["compliance"],
            "remediationDeadlineDays": adv["deadline"],
            "remediationAvailable": adv["remediation_available"],
            "description": adv["description"],
            "affectedWorkloads": [
                {"name": vn, "namespace": vns, "kind": "VirtualMachine",
                 "status": vs, "remediationAvailable": adv["remediation_available"]}
                for vn, vns, vs in adv["affected"]
            ],
        },
        "status": {
            "phase": "Completed",
            "totalAffected": len(adv["affected"]),
            "totalVulnerable": vuln_count,
            "totalRemediated": rem_count,
            "lastScanTime": NOW,
        },
    }


def _build_ns(name, labels):
    return {
        "apiVersion": "v1", "kind": "Namespace",
        "metadata": {"name": name, "uid": _uid(name), "labels": labels,
                      "creationTimestamp": CREATED},
        "status": {"phase": "Active"},
    }


_STORAGE_SIZES = {
    "db": "100Gi", "web": "50Gi", "api": "50Gi", "cache": "30Gi",
    "queue": "30Gi", "monitoring": "30Gi", "logging": "30Gi",
}


_RWO_VMS = {"vm-backup-prod-01", "vm-batch-prod-01", "vm-archive-01"}

def _build_pvc(vm):
    """Build a v1/PersistentVolumeClaim for a VM's rootdisk."""
    app = vm["labels"].get("app", "")
    size = _STORAGE_SIZES.get(app, "30Gi")
    access = "ReadWriteOnce" if vm["name"] in _RWO_VMS else "ReadWriteMany"
    return {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": f"{vm['name']}-rootdisk",
            "namespace": vm["ns"],
            "uid": _uid(f"{vm['name']}-pvc"),
            "labels": {
                "vm.kubevirt.io/name": vm["name"],
                "app.kubernetes.io/managed-by": "cdi-controller",
            },
            "creationTimestamp": CREATED,
        },
        "spec": {
            "accessModes": [access],
            "resources": {"requests": {"storage": size}},
            "storageClassName": "ocs-storagecluster-ceph-rbd",
            "volumeMode": "Block",
        },
        "status": {
            "phase": "Bound",
            "capacity": {"storage": size},
            "accessModes": [access],
        },
    }


def _build_datavolume(vm):
    """Build a cdi.kubevirt.io/v1beta1 DataVolume for a VM's rootdisk."""
    app = vm["labels"].get("app", "")
    size = _STORAGE_SIZES.get(app, "30Gi")
    access = "ReadWriteOnce" if vm["name"] in _RWO_VMS else "ReadWriteMany"
    return {
        "apiVersion": "cdi.kubevirt.io/v1beta1",
        "kind": "DataVolume",
        "metadata": {
            "name": f"{vm['name']}-rootdisk",
            "namespace": vm["ns"],
            "uid": _uid(f"{vm['name']}-dv"),
            "labels": {
                "vm.kubevirt.io/name": vm["name"],
                "app.kubernetes.io/managed-by": "cdi-controller",
            },
            "creationTimestamp": CREATED,
        },
        "spec": {
            "source": {"pvc": {"namespace": vm["ns"],
                                "name": f"{vm['name']}-rootdisk-source"}},
            "pvc": {
                "accessModes": [access],
                "resources": {"requests": {"storage": size}},
                "storageClassName": "ocs-storagecluster-ceph-rbd",
                "volumeMode": "Block",
            },
        },
        "status": {
            "phase": "Succeeded",
            "progress": "100.0%",
            "conditions": [
                {"type": "Ready", "status": "True",
                 "lastTransitionTime": CREATED},
                {"type": "Bound", "status": "True",
                 "lastTransitionTime": CREATED},
            ],
        },
    }


SNAPSHOTS = [
    {
        "name": "vm-db-prod-01-backup-20260201",
        "namespace": "virt-prod-dc2",
        "vm_name": "vm-db-prod-01",
        "phase": "Succeeded",
        "ready_to_use": True,
        "creation": "2026-02-01T08:00:00Z",
        "indications": ["Online", "GuestAgent"],
        "volume_statuses": [
            {"name": "rootdisk", "volumeSnapshotName": "vsnap-db01-root-20260201"},
        ],
    },
    {
        "name": "vm-db-prod-01-backup-20260215",
        "namespace": "virt-prod-dc2",
        "vm_name": "vm-db-prod-01",
        "phase": "Succeeded",
        "ready_to_use": True,
        "creation": "2026-02-15T10:30:00Z",
        "indications": ["Online", "GuestAgent"],
        "volume_statuses": [
            {"name": "rootdisk", "volumeSnapshotName": "vsnap-db01-root-20260215"},
        ],
    },
    {
        "name": "vm-web-prod-01-snap-20260220",
        "namespace": "virt-prod-dc1",
        "vm_name": "vm-web-prod-01",
        "phase": "Succeeded",
        "ready_to_use": True,
        "creation": "2026-02-20T14:00:00Z",
        "indications": ["Online"],
        "volume_statuses": [
            {"name": "rootdisk", "volumeSnapshotName": "vsnap-web01-root-20260220"},
        ],
    },
    {
        "name": "vm-etl-prod-01-snap-failed",
        "namespace": "virt-prod-dc1",
        "vm_name": "vm-etl-prod-01",
        "phase": "Failed",
        "ready_to_use": False,
        "creation": "2026-02-25T09:00:00Z",
        "indications": [],
        "volume_statuses": [],
        "error": "VolumeSnapshot creation timed out for rootdisk",
    },
]

RESTORES = [
    {
        "name": "restore-vm-web-prod-01-20260220",
        "namespace": "virt-prod-dc1",
        "target_vm": "vm-web-prod-01",
        "snapshot_name": "vm-web-prod-01-snap-20260220",
        "complete": True,
        "creation": "2026-02-22T16:00:00Z",
    },
]

MIGRATIONS = [
    {
        "name": "migration-vm-web-prod-03",
        "namespace": "virt-prod-dc1",
        "vmi_name": "vm-web-prod-03",
        "phase": "Succeeded",
        "source_node": "hv-prod-dc1-02",
        "target_node": "hv-prod-dc1-01",
        "creation": "2026-02-28T11:00:00Z",
    },
]

STORAGE_CLASSES = [
    {
        "name": "ocs-storagecluster-ceph-rbd",
        "provisioner": "openshift-storage.rbd.csi.ceph.com",
        "reclaimPolicy": "Delete",
        "volumeBindingMode": "Immediate",
        "allowVolumeExpansion": True,
    },
    {
        "name": "ocs-storagecluster-cephfs",
        "provisioner": "openshift-storage.cephfs.csi.ceph.com",
        "reclaimPolicy": "Delete",
        "volumeBindingMode": "Immediate",
        "allowVolumeExpansion": False,
    },
]

VOLUME_SNAPSHOT_CLASSES = [
    {
        "name": "ocs-storagecluster-rbdplugin-snapclass",
        "driver": "openshift-storage.rbd.csi.ceph.com",
        "deletionPolicy": "Delete",
    },
]


def _build_storage_class(sc):
    """Build a storage.k8s.io/v1 StorageClass resource."""
    res = {
        "apiVersion": "storage.k8s.io/v1",
        "kind": "StorageClass",
        "metadata": {
            "name": sc["name"],
            "uid": _uid(sc["name"]),
            "creationTimestamp": CREATED,
        },
        "provisioner": sc["provisioner"],
        "reclaimPolicy": sc["reclaimPolicy"],
        "volumeBindingMode": sc["volumeBindingMode"],
    }
    if sc.get("allowVolumeExpansion"):
        res["allowVolumeExpansion"] = True
    return res


def _build_volume_snapshot_class(vsc):
    """Build a snapshot.storage.k8s.io/v1 VolumeSnapshotClass resource."""
    return {
        "apiVersion": "snapshot.storage.k8s.io/v1",
        "kind": "VolumeSnapshotClass",
        "metadata": {
            "name": vsc["name"],
            "uid": _uid(vsc["name"]),
            "creationTimestamp": CREATED,
        },
        "driver": vsc["driver"],
        "deletionPolicy": vsc["deletionPolicy"],
    }


def _build_snapshot(snap):
    """Build a snapshot.kubevirt.io/v1beta1 VirtualMachineSnapshot resource."""
    res = {
        "apiVersion": "snapshot.kubevirt.io/v1beta1",
        "kind": "VirtualMachineSnapshot",
        "metadata": {
            "name": snap["name"],
            "namespace": snap["namespace"],
            "uid": _uid(snap["name"]),
            "labels": {"vm.kubevirt.io/name": snap["vm_name"]},
            "creationTimestamp": snap["creation"],
        },
        "spec": {
            "source": {
                "apiGroup": "kubevirt.io",
                "kind": "VirtualMachine",
                "name": snap["vm_name"],
            },
        },
        "status": {
            "phase": snap["phase"],
            "readyToUse": snap["ready_to_use"],
            "creationTime": snap["creation"],
            "indications": snap["indications"],
            "volumeSnapshotStatus": snap["volume_statuses"],
        },
    }
    if snap.get("error"):
        res["status"]["error"] = {"message": snap["error"]}
    return res


def _build_restore(restore):
    """Build a snapshot.kubevirt.io/v1beta1 VirtualMachineRestore resource."""
    return {
        "apiVersion": "snapshot.kubevirt.io/v1beta1",
        "kind": "VirtualMachineRestore",
        "metadata": {
            "name": restore["name"],
            "namespace": restore["namespace"],
            "uid": _uid(restore["name"]),
            "creationTimestamp": restore["creation"],
        },
        "spec": {
            "target": {
                "apiGroup": "kubevirt.io",
                "kind": "VirtualMachine",
                "name": restore["target_vm"],
            },
            "virtualMachineSnapshotName": restore["snapshot_name"],
        },
        "status": {
            "complete": restore["complete"],
            "restoreTime": restore["creation"],
        },
    }


def _build_migration(mig):
    """Build a kubevirt.io/v1 VirtualMachineInstanceMigration resource."""
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachineInstanceMigration",
        "metadata": {
            "name": mig["name"],
            "namespace": mig["namespace"],
            "uid": _uid(mig["name"]),
            "creationTimestamp": mig["creation"],
        },
        "spec": {
            "vmiName": mig["vmi_name"],
        },
        "status": {
            "phase": mig["phase"],
            "migrationState": {
                "sourceNode": mig["source_node"],
                "targetNode": mig["target_node"],
                "completed": mig["phase"] == "Succeeded",
                "startTimestamp": mig["creation"],
            },
        },
    }


def _build_pod(vm):
    """Build a virt-launcher Pod for a running/paused VM."""
    if vm["status"] not in ("Running", "Paused"):
        return None
    pod_name = f"virt-launcher-{vm['name']}-{_pod_hash(vm['name'])}"
    return {
        "apiVersion": "v1", "kind": "Pod",
        "metadata": {
            "name": pod_name, "namespace": vm["ns"],
            "uid": _uid(pod_name),
            "labels": {"kubevirt.io/domain": vm["name"],
                        "vm.kubevirt.io/name": vm["name"]},
            "ownerReferences": [{
                "apiVersion": "kubevirt.io/v1",
                "kind": "VirtualMachineInstance",
                "name": vm["name"],
            }],
            "creationTimestamp": CREATED,
        },
        "spec": {"nodeName": vm["node"]},
        "status": {
            "phase": "Running",
            "containerStatuses": [{
                "name": "compute", "ready": True,
                "state": {"running": {"startedAt": CREATED}},
            }],
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _table(headers, rows):
    """Format as a kubectl-style table with dynamic column widths."""
    widths = [len(h) for h in headers]
    str_rows = [[str(c) for c in r] for r in rows]
    for r in str_rows:
        for i, c in enumerate(r):
            if i < len(widths):
                widths[i] = max(widths[i], len(c))
    lines = ["   ".join(h.ljust(widths[i]) for i, h in enumerate(headers))]
    for r in str_rows:
        lines.append("   ".join(c.ljust(widths[i]) for i, c in enumerate(r)))
    return "\n".join(lines)


def _to_yaml(resource):
    return yaml.dump(resource, default_flow_style=False, sort_keys=False)


def _match_labels(labels, selector_str):
    if not selector_str:
        return True
    for sel in selector_str.split(","):
        sel = sel.strip()
        if "!=" in sel:
            k, v = sel.split("!=", 1)
            if labels.get(k.strip()) == v.strip():
                return False
        elif "=" in sel:
            k, v = sel.split("=", 1)
            if labels.get(k.strip()) != v.strip():
                return False
        elif sel.startswith("!"):
            if sel[1:] in labels:
                return False
        elif sel not in labels:
            return False
    return True


def _filter_by_ns(resources, namespace):
    if namespace is None:
        return resources
    return [r for r in resources if r.get("metadata", {}).get("namespace") == namespace]


# ═══════════════════════════════════════════════════════════════════════════
#  RESOURCE DISPATCH
# ═══════════════════════════════════════════════════════════════════════════

def _all_resources(api_version, kind):
    """Return (resources_list, table_headers, row_extractor, is_namespaced)."""
    if api_version == "kubevirt.io/v1" and kind == "VirtualMachine":
        resources = [_build_vm(vm) for vm in VMS]
        headers = ["NAMESPACE", "NAME", "STATUS", "READY", "AGE"]
        def row(r):
            m = r["metadata"]
            s = r["status"]
            return [m["namespace"], m["name"], s["printableStatus"],
                    str(s["ready"]), "30d"]
        return resources, headers, row, True

    if api_version == "kubevirt.io/v1" and kind == "VirtualMachineInstance":
        resources = [_build_vmi(vm) for vm in VMS if vm["status"] in ("Running", "Paused")]
        headers = ["NAMESPACE", "NAME", "PHASE", "IP", "NODENAME", "READY", "AGE"]
        def row(r):
            m = r["metadata"]
            s = r["status"]
            ip = s.get("interfaces", [{}])[0].get("ipAddress", "")
            return [m["namespace"], m["name"], s["phase"], ip,
                    s.get("nodeName", ""), str(s.get("conditions", [{}])[0].get("status", "")), "30d"]
        return resources, headers, row, True

    if api_version == "v1" and kind == "Node":
        resources = [_build_node(n) for n in NODES]
        headers = ["NAME", "STATUS", "ROLES", "AGE", "VERSION"]
        def row(r):
            m = r["metadata"]
            s = r.get("spec", {})
            status = "Ready,SchedulingDisabled" if s.get("unschedulable") else "Ready"
            return [m["name"], status, "worker", "60d", K8S_VER]
        return resources, headers, row, False

    if api_version == "v1" and kind == "Namespace":
        resources = [_build_ns(n, lb) for n, lb in NAMESPACES]
        headers = ["NAME", "STATUS", "AGE"]
        def row(r):
            return [r["metadata"]["name"], r["status"]["phase"], "60d"]
        return resources, headers, row, False

    if api_version == "security.openshift.io/v1" and kind == "VulnerabilityReport":
        resources = [_build_vuln_report(a) for a in ADVISORIES]
        headers = ["NAMESPACE", "NAME", "SEVERITY", "CVSS", "AFFECTED", "VULNERABLE", "AGE"]
        def row(r):
            s = r["status"]
            sp = r["spec"]
            return [r["metadata"]["namespace"], r["metadata"]["name"],
                    sp["severity"], str(sp["cvssScore"]),
                    str(s["totalAffected"]), str(s["totalVulnerable"]), "5d"]
        return resources, headers, row, True

    if api_version == "v1" and kind == "Pod":
        resources = [_build_pod(vm) for vm in VMS if vm["status"] in ("Running", "Paused")]
        headers = ["NAMESPACE", "NAME", "READY", "STATUS", "RESTARTS", "AGE"]
        def row(r):
            m = r["metadata"]
            return [m["namespace"], m["name"], "1/1", "Running", "0", "30d"]
        return resources, headers, row, True

    if api_version == "v1" and kind == "PersistentVolumeClaim":
        resources = [_build_pvc(vm) for vm in VMS]
        headers = ["NAMESPACE", "NAME", "STATUS", "VOLUME", "CAPACITY", "ACCESS MODES", "STORAGECLASS", "AGE"]
        def row(r):
            m = r["metadata"]
            cap = r["status"].get("capacity", {}).get("storage", "")
            sc = r["spec"].get("storageClassName", "")
            am = ",".join(a.replace("ReadWriteMany", "RWX").replace("ReadWriteOnce", "RWO")
                          for a in r["spec"].get("accessModes", []))
            return [m["namespace"], m["name"], "Bound", _uid(m["name"]), cap, am, sc, "30d"]
        return resources, headers, row, True

    if api_version == "cdi.kubevirt.io/v1beta1" and kind == "DataVolume":
        resources = [_build_datavolume(vm) for vm in VMS]
        headers = ["NAMESPACE", "NAME", "PHASE", "PROGRESS", "AGE"]
        def row(r):
            m = r["metadata"]
            s = r["status"]
            return [m["namespace"], m["name"], s["phase"], s.get("progress", ""), "30d"]
        return resources, headers, row, True

    if api_version == "storage.k8s.io/v1" and kind == "StorageClass":
        resources = [_build_storage_class(sc) for sc in STORAGE_CLASSES]
        headers = ["NAME", "PROVISIONER", "RECLAIMPOLICY", "VOLUMEBINDINGMODE", "ALLOWVOLUMEEXPANSION", "AGE"]
        def row(r):
            return [r["metadata"]["name"], r["provisioner"],
                    r["reclaimPolicy"], r["volumeBindingMode"],
                    str(r.get("allowVolumeExpansion", False)), "90d"]
        return resources, headers, row, False

    if api_version == "snapshot.storage.k8s.io/v1" and kind == "VolumeSnapshotClass":
        resources = [_build_volume_snapshot_class(vsc) for vsc in VOLUME_SNAPSHOT_CLASSES]
        headers = ["NAME", "DRIVER", "DELETIONPOLICY", "AGE"]
        def row(r):
            return [r["metadata"]["name"], r["driver"], r["deletionPolicy"], "90d"]
        return resources, headers, row, False

    if api_version == "snapshot.kubevirt.io/v1beta1" and kind == "VirtualMachineSnapshot":
        resources = [_build_snapshot(s) for s in SNAPSHOTS]
        headers = ["NAMESPACE", "NAME", "PHASE", "READY", "VM", "AGE"]
        def row(r):
            m = r["metadata"]
            s = r["status"]
            vm_name = r["spec"]["source"]["name"]
            return [m["namespace"], m["name"], s["phase"],
                    str(s["readyToUse"]), vm_name, "5d"]
        return resources, headers, row, True

    if api_version == "snapshot.kubevirt.io/v1beta1" and kind == "VirtualMachineRestore":
        resources = [_build_restore(r) for r in RESTORES]
        headers = ["NAMESPACE", "NAME", "TARGET", "SNAPSHOT", "COMPLETE", "AGE"]
        def row(r):
            m = r["metadata"]
            s = r["status"]
            return [m["namespace"], m["name"],
                    r["spec"]["target"]["name"],
                    r["spec"]["virtualMachineSnapshotName"],
                    str(s["complete"]), "3d"]
        return resources, headers, row, True

    if api_version == "kubevirt.io/v1" and kind == "VirtualMachineInstanceMigration":
        resources = [_build_migration(m) for m in MIGRATIONS]
        headers = ["NAMESPACE", "NAME", "PHASE", "VMI", "AGE"]
        def row(r):
            m = r["metadata"]
            s = r["status"]
            return [m["namespace"], m["name"], s["phase"],
                    r["spec"]["vmiName"], "2d"]
        return resources, headers, row, True

    return [], [], None, True


# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG TOOLSET
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def configuration_view(minified: bool = True) -> str:
    """Get the current Kubernetes configuration content as a kubeconfig YAML."""
    cfg = {
        "apiVersion": "v1", "kind": "Config",
        "current-context": CLUSTER,
        "clusters": [{"name": CLUSTER, "cluster": {"server": API_URL}}],
        "contexts": [{"name": CLUSTER, "context": {
            "cluster": CLUSTER, "user": "admin", "namespace": "default"}}],
        "users": [{"name": "admin", "user": {
            "token": "[REDACTED]"}}],
    }
    return yaml.dump(cfg, default_flow_style=False, sort_keys=False)


@mcp.tool()
def configuration_contexts_list() -> str:
    """List all available context names and associated server urls from the kubeconfig file."""
    return _table(
        ["CURRENT", "NAME", "CLUSTER", "AUTHINFO", "NAMESPACE"],
        [["*", CLUSTER, CLUSTER, "admin", "default"]])


# ═══════════════════════════════════════════════════════════════════════════
#  CORE TOOLSET: RESOURCES
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def resources_list(
    apiVersion: str,
    kind: str,
    namespace: Optional[str] = None,
    labelSelector: Optional[str] = None,
    fieldSelector: Optional[str] = None,
) -> str:
    """List Kubernetes resources by apiVersion and kind, optionally filtered by namespace and label selector."""
    resources, headers, row_fn, is_namespaced = _all_resources(apiVersion, kind)
    if not resources and row_fn is None:
        return f"error: the server doesn't have a resource type \"{kind}\""

    if is_namespaced and namespace:
        resources = _filter_by_ns(resources, namespace)
    if labelSelector:
        resources = [r for r in resources
                     if _match_labels(r.get("metadata", {}).get("labels", {}),
                                      labelSelector)]
    if fieldSelector:
        for sel in fieldSelector.split(","):
            if "=" in sel:
                k, v = sel.split("=", 1)
                k, v = k.strip(), v.strip()
                if k == "status.printableStatus":
                    resources = [r for r in resources
                                 if r.get("status", {}).get("printableStatus") == v]
                elif k == "metadata.name":
                    resources = [r for r in resources
                                 if r.get("metadata", {}).get("name") == v]
                elif k == "spec.nodeName":
                    resources = [r for r in resources
                                 if r.get("spec", {}).get("nodeName") == v or
                                    r.get("status", {}).get("nodeName") == v or
                                    r.get("spec", {}).get("template", {}).get("spec", {})
                                     .get("nodeSelector", {}).get("kubernetes.io/hostname") == v]

    if not resources:
        ns_msg = f" in namespace \"{namespace}\"" if namespace else ""
        return f"No resources found{ns_msg}."

    show_ns = is_namespaced and namespace is None
    h = headers if show_ns else [h for h in headers if h != "NAMESPACE"]
    rows = []
    for r in resources:
        full_row = row_fn(r)
        if show_ns:
            rows.append(full_row)
        else:
            ns_idx = headers.index("NAMESPACE") if "NAMESPACE" in headers else -1
            rows.append([c for i, c in enumerate(full_row) if i != ns_idx])
    return _table(h, rows)


@mcp.tool()
def resources_get(
    apiVersion: str,
    kind: str,
    name: str,
    namespace: Optional[str] = None,
) -> str:
    """Get a Kubernetes resource by apiVersion, kind, and name, returned as YAML."""
    resources, _, _, is_namespaced = _all_resources(apiVersion, kind)
    for r in resources:
        m = r.get("metadata", {})
        if m.get("name") != name:
            continue
        if is_namespaced and namespace and m.get("namespace") != namespace:
            continue
        return _to_yaml(r)
    kind_lower = kind.lower() + "s"
    return f'Error from server (NotFound): {kind_lower}.{apiVersion.split("/")[0]} "{name}" not found'


@mcp.tool()
def resources_create_or_update(resource: str) -> str:
    """Create or update a Kubernetes resource (YAML or JSON)."""
    try:
        data = yaml.safe_load(resource)
        name = data.get("metadata", {}).get("name", "unknown")
        kind = data.get("kind", "unknown")
        return f'{kind} "{name}" configured'
    except Exception as e:
        return f"Error: invalid resource definition: {e}"


@mcp.tool()
def resources_delete(
    apiVersion: str,
    kind: str,
    name: str,
    namespace: Optional[str] = None,
    gracePeriodSeconds: Optional[int] = None,
) -> str:
    """Delete a Kubernetes resource."""
    return f'{kind} "{name}" deleted'


@mcp.tool()
def resources_scale(
    apiVersion: str,
    kind: str,
    name: str,
    namespace: Optional[str] = None,
    scale: Optional[int] = None,
) -> str:
    """Get or update the scale of a Kubernetes resource."""
    return f'Error: {kind} does not support scaling'


# ═══════════════════════════════════════════════════════════════════════════
#  CORE TOOLSET: NAMESPACES, EVENTS, NODES
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def namespaces_list() -> str:
    """List all Kubernetes namespaces in the current cluster."""
    headers = ["NAME", "STATUS", "AGE"]
    rows = [[n, "Active", "60d"] for n, _ in NAMESPACES]
    return _table(headers, rows)


@mcp.tool()
def projects_list() -> str:
    """List all OpenShift projects in the current cluster."""
    headers = ["NAME", "DISPLAY NAME", "STATUS"]
    rows = [[n, "", "Active"] for n, _ in NAMESPACES]
    return _table(headers, rows)


@mcp.tool()
def events_list(namespace: Optional[str] = None) -> str:
    """List Kubernetes events (warnings, errors, state changes)."""
    filtered = EVENTS
    if namespace:
        filtered = [e for e in filtered if e[0] == namespace]
    if not filtered:
        return "No events found."
    headers = ["NAMESPACE", "LAST SEEN", "TYPE", "REASON", "OBJECT", "MESSAGE"]
    rows = []
    for i, (ns, etype, reason, obj, msg) in enumerate(filtered):
        last_seen = f"{(i + 1) * 5}m"
        rows.append([ns, last_seen, etype, reason, obj, msg])
    return _table(headers, rows)


@mcp.tool()
def nodes_top(
    name: Optional[str] = None,
    label_selector: Optional[str] = None,
) -> str:
    """List node resource consumption (CPU and memory) from the Metrics Server."""
    nodes = NODES
    if name:
        nodes = [n for n in nodes if n["name"] == name]
    if label_selector:
        all_nodes = [_build_node(n) for n in nodes]
        matched = [n for n, r in zip(nodes, all_nodes)
                    if _match_labels(r["metadata"]["labels"], label_selector)]
        nodes = matched
    if not nodes:
        return "No metrics available for the requested node(s)."

    headers = ["NAME", "CPU(cores)", "CPU%", "MEMORY(bytes)", "MEMORY%"]
    rows = []
    for n in nodes:
        cpu_pct = round(n["cpu_use"] / n["cpu_cap"] * 100)
        mem_pct = round(n["mem_use"] / n["mem_cap"] * 100)
        rows.append([n["name"], f"{n['cpu_use']}m", f"{cpu_pct}%",
                      f"{n['mem_use']}Mi", f"{mem_pct}%"])
    return _table(headers, rows)


@mcp.tool()
def nodes_stats_summary(name: str) -> str:
    """Get detailed resource usage statistics from a node via the kubelet Summary API."""
    node = next((n for n in NODES if n["name"] == name), None)
    if not node:
        return f'Error: node "{name}" not found'

    cpu_nano = node["cpu_use"] * 1_000_000
    mem_bytes = node["mem_use"] * 1024 * 1024
    mem_avail = (node["mem_cap"] - node["mem_use"]) * 1024 * 1024

    vm_pods = [vm for vm in VMS
               if vm["node"] == name and vm["status"] in ("Running", "Paused")]
    pod_stats = []
    for vm in vm_pods:
        pod_stats.append({
            "podRef": {"name": f"virt-launcher-{vm['name']}-{_pod_hash(vm['name'])}",
                       "namespace": vm["ns"]},
            "cpu": {"usageNanoCores": vm["cpu"] * 250_000_000},
            "memory": {"usageBytes": vm["mem"] * 512 * 1024 * 1024,
                       "workingSetBytes": vm["mem"] * 400 * 1024 * 1024},
        })

    summary = {
        "node": {
            "nodeName": name,
            "cpu": {"usageNanoCores": cpu_nano,
                    "usageCoreNanoSeconds": cpu_nano * 3600},
            "memory": {"availableBytes": mem_avail,
                       "usageBytes": mem_bytes,
                       "workingSetBytes": int(mem_bytes * 0.95)},
            "fs": {"availableBytes": 200_000_000_000,
                   "capacityBytes": 500_000_000_000,
                   "usedBytes": 300_000_000_000},
            "network": {
                "interfaces": [{
                    "name": "eth0",
                    "rxBytes": 1_500_000_000_000,
                    "txBytes": 800_000_000_000,
                }],
            },
        },
        "pods": pod_stats,
    }
    return json.dumps(summary, indent=2)


@mcp.tool()
def nodes_log(name: str, query: str, tailLines: int = 100) -> str:
    """Get logs from a Kubernetes node."""
    node = next((n for n in NODES if n["name"] == name), None)
    if not node:
        return f'Error: node "{name}" not found'
    return (f"-- Logs begin for {name} ({query}) --\n"
            f"Mar 02 12:00:00 {name} kubelet[1234]: I0302 12:00:00.000000 "
            f"node_status.go:123] Node {name} status: Ready\n"
            f"-- End of logs --")


# ═══════════════════════════════════════════════════════════════════════════
#  CORE TOOLSET: PODS
# ═══════════════════════════════════════════════════════════════════════════

def _pod_list_filtered(namespace=None, fieldSelector=None, labelSelector=None):
    pods = [_build_pod(vm) for vm in VMS if vm["status"] in ("Running", "Paused")]
    if namespace:
        pods = _filter_by_ns(pods, namespace)
    if labelSelector:
        pods = [p for p in pods
                if _match_labels(p["metadata"]["labels"], labelSelector)]
    return pods


@mcp.tool()
def pods_list(
    fieldSelector: Optional[str] = None,
    labelSelector: Optional[str] = None,
) -> str:
    """List all pods in the cluster from all namespaces."""
    pods = _pod_list_filtered(None, fieldSelector, labelSelector)
    if not pods:
        return "No pods found."
    headers = ["NAMESPACE", "NAME", "READY", "STATUS", "RESTARTS", "AGE"]
    rows = [[p["metadata"]["namespace"], p["metadata"]["name"],
             "1/1", "Running", "0", "30d"] for p in pods]
    return _table(headers, rows)


@mcp.tool()
def pods_list_in_namespace(
    namespace: str,
    fieldSelector: Optional[str] = None,
    labelSelector: Optional[str] = None,
) -> str:
    """List all pods in the specified namespace."""
    pods = _pod_list_filtered(namespace, fieldSelector, labelSelector)
    if not pods:
        return f'No pods found in namespace "{namespace}".'
    headers = ["NAME", "READY", "STATUS", "RESTARTS", "AGE"]
    rows = [[p["metadata"]["name"], "1/1", "Running", "0", "30d"] for p in pods]
    return _table(headers, rows)


@mcp.tool()
def pods_get(name: str, namespace: Optional[str] = None) -> str:
    """Get a Pod by name, returned as YAML."""
    pods = [_build_pod(vm) for vm in VMS if vm["status"] in ("Running", "Paused")]
    for p in pods:
        if p["metadata"]["name"] == name:
            if namespace and p["metadata"]["namespace"] != namespace:
                continue
            return _to_yaml(p)
    return f'Error from server (NotFound): pods "{name}" not found'


@mcp.tool()
def pods_delete(name: str, namespace: Optional[str] = None) -> str:
    """Delete a Pod by name."""
    return f'pod "{name}" deleted'


@mcp.tool()
def pods_log(
    name: str,
    namespace: Optional[str] = None,
    container: Optional[str] = None,
    tail: int = 100,
    previous: bool = False,
) -> str:
    """Get the logs of a Pod."""
    vm_name = name.replace("virt-launcher-", "").rsplit("-", 1)[0]
    vm = next((v for v in VMS if v["name"] == vm_name), None)
    if not vm:
        return f'Error from server (NotFound): pods "{name}" not found'
    return (
        f'{{"component":"virt-launcher","level":"info","msg":"Configured with '
        f'VM {vm["name"]}","timestamp":"{CREATED}"}}\n'
        f'{{"component":"virt-launcher","level":"info","msg":"Domain started",'
        f'"timestamp":"{CREATED}"}}\n'
        f'{{"component":"virt-handler","level":"info","msg":"VM is running on '
        f'node {vm["node"]}","timestamp":"{CREATED}"}}'
    )


@mcp.tool()
def pods_exec(
    name: str,
    command: list,
    namespace: Optional[str] = None,
    container: Optional[str] = None,
) -> str:
    """Execute a command in a Pod."""
    cmd = " ".join(command)
    return f"command '{cmd}' executed successfully"


@mcp.tool()
def pods_run(
    image: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    port: Optional[int] = None,
) -> str:
    """Run a Pod with the provided container image."""
    pod_name = name or "run-" + _pod_hash(image)
    return f'pod/{pod_name} created'


@mcp.tool()
def pods_top(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    all_namespaces: bool = False,
    label_selector: Optional[str] = None,
) -> str:
    """List pod resource consumption from the Metrics Server."""
    pods_data = [(vm, _build_pod(vm)) for vm in VMS
                 if vm["status"] in ("Running", "Paused")]
    if namespace and not all_namespaces:
        pods_data = [(vm, p) for vm, p in pods_data
                     if p["metadata"]["namespace"] == namespace]
    if name:
        pods_data = [(vm, p) for vm, p in pods_data
                     if p["metadata"]["name"] == name]

    if not pods_data:
        return "No metrics available."

    show_ns = all_namespaces or (namespace is None and name is None)
    headers = (["NAMESPACE"] if show_ns else []) + ["NAME", "CPU(cores)", "MEMORY(bytes)"]
    rows = []
    for vm, p in pods_data:
        cpu_m = f"{vm['cpu'] * 250}m"
        mem_mi = f"{vm['mem'] * 512}Mi"
        row = ([p["metadata"]["namespace"]] if show_ns else []) + \
              [p["metadata"]["name"], cpu_m, mem_mi]
        rows.append(row)
    return _table(headers, rows)


# ═══════════════════════════════════════════════════════════════════════════
#  KUBEVIRT TOOLSET
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def vm_lifecycle(name: str, namespace: str, action: str) -> str:
    """Manage VirtualMachine lifecycle: start, stop, or restart a VM."""
    vm = next((v for v in VMS if v["name"] == name and v["ns"] == namespace), None)
    if not vm:
        return (f'Error from server (NotFound): virtualmachines.kubevirt.io '
                f'"{name}" not found in namespace "{namespace}"')
    if action not in ("start", "stop", "restart"):
        return f'Error: invalid action "{action}". Must be start, stop, or restart'
    return f'VirtualMachine "{name}" was scheduled to {action}'


@mcp.tool()
def vm_create(
    name: str,
    namespace: str,
    workload: str = "fedora",
    autostart: bool = False,
    instancetype: Optional[str] = None,
    preference: Optional[str] = None,
    size: Optional[str] = None,
    storage: Optional[str] = None,
    performance: Optional[str] = None,
    networks: Optional[list] = None,
) -> str:
    """Create a VirtualMachine in the cluster."""
    return f'VirtualMachine "{name}" created in namespace "{namespace}"'


@mcp.tool()
def vm_clone(name: str, namespace: str, targetName: str) -> str:
    """Clone a KubeVirt VirtualMachine."""
    vm = next((v for v in VMS if v["name"] == name and v["ns"] == namespace), None)
    if not vm:
        return (f'Error from server (NotFound): virtualmachines.kubevirt.io '
                f'"{name}" not found in namespace "{namespace}"')
    return f'VirtualMachineClone "{name}-to-{targetName}" created'


# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()

#!/usr/bin/env python3
"""
Mock Lightspeed MCP Server

Simulates the Red Hat Lightspeed MCP server for the rh-sre-fleet-inventory
benchmark task. Implements the MCP protocol via FastMCP so that agents can
call get_host_details, get_cve_systems, get_cves, get_cve, and
create_vulnerability_playbook as real MCP tools.

Fleet composition (63 systems total):
  - 30 production  (web, db, app, lb, monitoring, cache)
  - 15 staging
  - 10 development
  -  5 QA
  -  3 legacy      (ambiguous tags — no explicit environment)

CVE data (5 CVEs):
  - CVE-2024-12345  Critical  9.8   RCE in HTTP processing
  - CVE-2024-54321  Important 7.5   SQL injection in DB parser
  - CVE-2024-11111  Moderate  5.3   Info disclosure in logging
  - CVE-2024-98765  Important 8.1   DoS in load balancer
  - CVE-2024-22222  Low       3.1   Info disclosure in monitoring
"""

import os
import random
from datetime import datetime, timedelta
from typing import Optional

from fastmcp import FastMCP

random.seed(42)

REFERENCE_TIME = datetime(2026, 2, 15, 12, 0, 0)


# ---------------------------------------------------------------------------
# Mock fleet data
# ---------------------------------------------------------------------------

def _ts(delta: timedelta) -> str:
    """Return an ISO timestamp offset from REFERENCE_TIME."""
    return (REFERENCE_TIME - delta).isoformat() + "Z"


def _system_profile_for_host(host_type: str, rhel_version: str, sid: int) -> dict:
    """Generate system_profile fields for a host based on type and RHEL version."""
    el = "el9" if rhel_version.startswith("9") else "el8"
    kernel = f"5.14.0-362.24.1.{el}_3.x86_64" if "9" in rhel_version else f"4.18.0-477.27.1.{el}.x86_64"
    base_pkgs = [
        {"name": "kernel-core", "version": f"5.14.0-362.24.1.{el}.x86_64"},
        {"name": "httpd", "version": f"2.4.57-5.{el}"},
        {"name": "sshd", "version": f"8.9p1-23.{el}"},
        {"name": "firewalld", "version": f"1.2.5-4.{el}"},
        {"name": "systemd", "version": f"250-19.{el}"},
    ]
    if "web" in host_type or "lb" in host_type:
        base_pkgs.extend([
            {"name": "nginx", "version": f"1.24.1-3.{el}"},
            {"name": "openssl", "version": f"3.0.7-24.{el}"},
        ])
    elif "db" in host_type:
        base_pkgs.extend([
            {"name": "postgresql", "version": f"15.4-1.{el}"},
            {"name": "openssl", "version": f"3.0.7-24.{el}"},
        ])
    elif "mon" in host_type:
        base_pkgs.extend([
            {"name": "prometheus", "version": f"2.45.0-1.{el}"},
            {"name": "node_exporter", "version": f"1.6.1-2.{el}"},
        ])
    else:
        base_pkgs.extend([
            {"name": "java-17-openjdk", "version": f"17.0.8-4.{el}"},
            {"name": "openssl", "version": f"3.0.7-24.{el}"},
        ])
    services = ["sshd.service", "firewalld.service", "chronyd.service"]
    if "web" in host_type or "lb" in host_type:
        services.append("httpd.service")
    elif "db" in host_type:
        services.extend(["postgresql.service", "postgresql-15.service"])
    elif "mon" in host_type:
        services.extend(["prometheus.service", "node_exporter.service"])
    else:
        services.append("httpd.service")
    ip_octet = 10 + (sid % 245)
    mac_hex = f"{(sid % 256):02x}"
    return {
        "installed_packages": base_pkgs[:8],
        "running_services": services,
        "network_interfaces": [
            {"name": "eth0", "ipv4": [f"10.0.1.{ip_octet}"], "mac": f"52:54:00:a1:b2:{mac_hex}"},
            {"name": "lo", "ipv4": ["127.0.0.1"], "mac": "00:00:00:00:00:00"},
        ],
        "kernel_version": kernel,
    }


def generate_mock_systems() -> list[dict]:
    """Generate 63 mock systems with realistic distribution."""
    systems: list[dict] = []
    sid = 1

    # --- Production (30) ---------------------------------------------------

    # Web servers (8)
    for i in range(1, 9):
        rhel = "9.3" if i <= 5 else ("9.2" if i <= 7 else "8.9")
        stale = i == 7
        tags = ["production", "web-tier"]
        if i <= 4:
            tags.extend(["customer-facing", "pci-compliant", "high-availability"])
        if i <= 2:
            tags.append("critical")
        systems.append({
            "id": f"sys-{sid:03d}-web-prod-{i:02d}",
            "display_name": f"web-server-{i:02d}.prod.example.com",
            "fqdn": f"web-server-{i:02d}.prod.example.com",
            "rhel_version": rhel,
            "last_seen": _ts(timedelta(days=9) if stale else timedelta(hours=random.randint(1, 20))),
            "tags": tags,
            "stale": stale,
            "satellite_managed": False,
        })
        sid += 1

    # Database servers (6)
    for i in range(1, 7):
        rhel = "9.3" if i <= 4 else "9.2"
        stale = i == 5
        tags = ["production", "database-tier", "critical"]
        if i <= 4:
            tags.extend(["pci-compliant", "soc2-compliant", "high-availability"])
        if i <= 2:
            tags.append("customer-data")
        systems.append({
            "id": f"sys-{sid:03d}-db-prod-{i:02d}",
            "display_name": f"db-server-{i:02d}.prod.example.com",
            "fqdn": f"db-server-{i:02d}.prod.example.com",
            "rhel_version": rhel,
            "last_seen": _ts(timedelta(days=10) if stale else timedelta(hours=random.randint(1, 18))),
            "tags": tags,
            "stale": stale,
            "satellite_managed": False,
        })
        sid += 1

    # Application servers (10)
    for i in range(1, 11):
        rhel = "8.9" if i <= 6 else ("9.2" if i <= 8 else "9.3")
        stale = i == 9
        tags = ["production", "app-tier"]
        if i <= 3:
            tags.extend(["customer-facing", "pci-compliant", "soc2-compliant"])
        elif i <= 6:
            tags.extend(["hipaa-compliant", "soc2-compliant"])
        if i <= 5:
            tags.append("high-availability")
        systems.append({
            "id": f"sys-{sid:03d}-app-prod-{i:02d}",
            "display_name": f"app-server-{i:02d}.prod.example.com",
            "fqdn": f"app-server-{i:02d}.prod.example.com",
            "rhel_version": rhel,
            "last_seen": _ts(timedelta(days=8) if stale else timedelta(hours=random.randint(1, 22))),
            "tags": tags,
            "stale": stale,
            "satellite_managed": False,
        })
        sid += 1

    # Load balancers (3)
    for i in range(1, 4):
        tags = ["production", "loadbalancer", "critical", "high-availability"]
        if i <= 2:
            tags.append("customer-facing")
        systems.append({
            "id": f"sys-{sid:03d}-lb-prod-{i:02d}",
            "display_name": f"lb-server-{i:02d}.prod.example.com",
            "fqdn": f"lb-server-{i:02d}.prod.example.com",
            "rhel_version": "8.8",
            "last_seen": _ts(timedelta(hours=random.randint(1, 12))),
            "tags": tags,
            "stale": False,
            "satellite_managed": False,
        })
        sid += 1

    # Monitoring (2)
    for i in range(1, 3):
        systems.append({
            "id": f"sys-{sid:03d}-mon-prod-{i:02d}",
            "display_name": f"monitor-server-{i:02d}.prod.example.com",
            "fqdn": f"monitor-server-{i:02d}.prod.example.com",
            "rhel_version": "9.3",
            "last_seen": _ts(timedelta(hours=random.randint(1, 6))),
            "tags": ["production", "monitoring"],
            "stale": False,
            "satellite_managed": False,
        })
        sid += 1

    # Cache (1) — stale
    systems.append({
        "id": f"sys-{sid:03d}-cache-prod-01",
        "display_name": "cache-server-01.prod.example.com",
        "fqdn": "cache-server-01.prod.example.com",
        "rhel_version": "8.9",
        "last_seen": _ts(timedelta(days=11)),
        "tags": ["production", "cache-tier"],
        "stale": True,
        "satellite_managed": False,
    })
    sid += 1

    # --- Staging (15) ------------------------------------------------------

    for i in range(1, 5):
        rhel = "9.3" if i <= 2 else "9.2"
        stale = i == 3
        systems.append({
            "id": f"sys-{sid:03d}-web-stg-{i:02d}",
            "display_name": f"web-server-{i:02d}.staging.example.com",
            "fqdn": f"web-server-{i:02d}.staging.example.com",
            "rhel_version": rhel,
            "last_seen": _ts(timedelta(days=12) if stale else timedelta(hours=random.randint(2, 20))),
            "tags": ["staging", "web-tier"],
            "stale": stale,
            "satellite_managed": False,
        })
        sid += 1

    for i in range(1, 4):
        systems.append({
            "id": f"sys-{sid:03d}-db-stg-{i:02d}",
            "display_name": f"db-server-{i:02d}.staging.example.com",
            "fqdn": f"db-server-{i:02d}.staging.example.com",
            "rhel_version": "9.3" if i <= 2 else "9.2",
            "last_seen": _ts(timedelta(hours=random.randint(3, 18))),
            "tags": ["staging", "database-tier"],
            "stale": False,
            "satellite_managed": False,
        })
        sid += 1

    for i in range(1, 6):
        systems.append({
            "id": f"sys-{sid:03d}-app-stg-{i:02d}",
            "display_name": f"app-server-{i:02d}.staging.example.com",
            "fqdn": f"app-server-{i:02d}.staging.example.com",
            "rhel_version": "8.9" if i <= 3 else "9.2",
            "last_seen": _ts(timedelta(hours=random.randint(4, 22))),
            "tags": ["staging", "app-tier"],
            "stale": False,
            "satellite_managed": False,
        })
        sid += 1

    for i in range(1, 3):
        systems.append({
            "id": f"sys-{sid:03d}-lb-stg-{i:02d}",
            "display_name": f"lb-server-{i:02d}.staging.example.com",
            "fqdn": f"lb-server-{i:02d}.staging.example.com",
            "rhel_version": "8.8",
            "last_seen": _ts(timedelta(hours=random.randint(2, 16))),
            "tags": ["staging", "loadbalancer"],
            "stale": False,
            "satellite_managed": False,
        })
        sid += 1

    systems.append({
        "id": f"sys-{sid:03d}-mon-stg-01",
        "display_name": "monitor-server-01.staging.example.com",
        "fqdn": "monitor-server-01.staging.example.com",
        "rhel_version": "9.3",
        "last_seen": _ts(timedelta(hours=8)),
        "tags": ["staging", "monitoring"],
        "stale": False,
        "satellite_managed": False,
    })
    sid += 1

    # --- Development (10) --------------------------------------------------

    for i in range(1, 4):
        rhel = "9.2" if i == 1 else "8.9"
        stale = i == 2
        systems.append({
            "id": f"sys-{sid:03d}-web-dev-{i:02d}",
            "display_name": f"web-server-{i:02d}.dev.example.com",
            "fqdn": f"web-server-{i:02d}.dev.example.com",
            "rhel_version": rhel,
            "last_seen": _ts(timedelta(days=15) if stale else timedelta(hours=random.randint(5, 23))),
            "tags": ["development", "web-tier"],
            "stale": stale,
            "satellite_managed": False,
        })
        sid += 1

    for i in range(1, 3):
        systems.append({
            "id": f"sys-{sid:03d}-db-dev-{i:02d}",
            "display_name": f"db-server-{i:02d}.dev.example.com",
            "fqdn": f"db-server-{i:02d}.dev.example.com",
            "rhel_version": "9.3" if i == 1 else "9.2",
            "last_seen": _ts(timedelta(hours=random.randint(6, 20))),
            "tags": ["development", "database-tier"],
            "stale": False,
            "satellite_managed": False,
        })
        sid += 1

    for i in range(1, 5):
        systems.append({
            "id": f"sys-{sid:03d}-app-dev-{i:02d}",
            "display_name": f"app-server-{i:02d}.dev.example.com",
            "fqdn": f"app-server-{i:02d}.dev.example.com",
            "rhel_version": "8.9" if i <= 2 else "9.2",
            "last_seen": _ts(timedelta(hours=random.randint(8, 22))),
            "tags": ["development", "app-tier"],
            "stale": False,
            "satellite_managed": False,
        })
        sid += 1

    systems.append({
        "id": f"sys-{sid:03d}-mon-dev-01",
        "display_name": "monitor-server-01.dev.example.com",
        "fqdn": "monitor-server-01.dev.example.com",
        "rhel_version": "9.2",
        "last_seen": _ts(timedelta(hours=10)),
        "tags": ["development", "monitoring"],
        "stale": False,
        "satellite_managed": False,
    })
    sid += 1

    # --- QA (5) ------------------------------------------------------------

    for i in range(1, 3):
        stale = i == 2
        systems.append({
            "id": f"sys-{sid:03d}-web-qa-{i:02d}",
            "display_name": f"web-server-{i:02d}.qa.example.com",
            "fqdn": f"web-server-{i:02d}.qa.example.com",
            "rhel_version": "9.3",
            "last_seen": _ts(timedelta(days=14) if stale else timedelta(hours=random.randint(4, 18))),
            "tags": ["qa", "web-tier"],
            "stale": stale,
            "satellite_managed": False,
        })
        sid += 1

    systems.append({
        "id": f"sys-{sid:03d}-db-qa-01",
        "display_name": "db-server-01.qa.example.com",
        "fqdn": "db-server-01.qa.example.com",
        "rhel_version": "9.2",
        "last_seen": _ts(timedelta(hours=12)),
        "tags": ["qa", "database-tier"],
        "stale": False,
        "satellite_managed": False,
    })
    sid += 1

    for i in range(1, 3):
        systems.append({
            "id": f"sys-{sid:03d}-app-qa-{i:02d}",
            "display_name": f"app-server-{i:02d}.qa.example.com",
            "fqdn": f"app-server-{i:02d}.qa.example.com",
            "rhel_version": "9.2",
            "last_seen": _ts(timedelta(hours=random.randint(5, 19))),
            "tags": ["qa", "app-tier"],
            "stale": False,
            "satellite_managed": False,
        })
        sid += 1

    # --- Legacy (3) — ambiguous tags, no explicit environment --------------

    systems.append({
        "id": f"sys-{sid:03d}-legacy-payment-01",
        "display_name": "legacy-payment-gw.example.com",
        "fqdn": "legacy-payment-gw.example.com",
        "rhel_version": "8.7",
        "last_seen": _ts(timedelta(hours=3)),
        "tags": ["legacy-system", "payment-gateway", "critical"],
        "stale": False,
        "satellite_managed": True,
    })
    sid += 1

    systems.append({
        "id": f"sys-{sid:03d}-legacy-reports-01",
        "display_name": "reports-legacy.example.com",
        "fqdn": "reports-legacy.example.com",
        "rhel_version": "8.6",
        "last_seen": _ts(timedelta(days=6)),
        "tags": ["legacy-system", "reporting", "financial-data"],
        "stale": False,
        "satellite_managed": True,
    })
    sid += 1

    systems.append({
        "id": f"sys-{sid:03d}-legacy-archive-01",
        "display_name": "archive-01.legacy.example.com",
        "fqdn": "archive-01.legacy.example.com",
        "rhel_version": "8.5",
        "last_seen": _ts(timedelta(days=30)),
        "tags": ["legacy-system", "archive", "read-only"],
        "stale": True,
        "satellite_managed": True,
    })
    sid += 1

    # Add system_profile to each host
    for idx, s in enumerate(systems):
        host_type = "app"  # default
        for ht in ["web", "db", "app", "lb", "mon", "cache"]:
            if ht in s["id"]:
                host_type = ht
                break
        s["system_profile"] = _system_profile_for_host(
            host_type, s["rhel_version"], idx + 1
        )

    return systems


MOCK_SYSTEMS = generate_mock_systems()

# ---------------------------------------------------------------------------
# Mock CVE data
# ---------------------------------------------------------------------------

MOCK_CVE_DATA = {
    "CVE-2024-12345": {
        "cve_id": "CVE-2024-12345",
        "severity": "Critical",
        "cvss_score": 9.8,
        "description": "Remote code execution vulnerability in HTTP request processing",
        "pci_impact": True,
        "soc2_impact": True,
        "hipaa_impact": False,
        "compliance_deadline": "2024-03-15",
        "compliance_notes": (
            "PCI-DSS 6.2 requires critical vulnerabilities be patched within "
            "30 days for systems handling cardholder data"
        ),
        "affected_systems": [
            {"system_id": "sys-001-web-prod-01", "display_name": "web-server-01.prod.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-002-web-prod-02", "display_name": "web-server-02.prod.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-003-web-prod-03", "display_name": "web-server-03.prod.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-004-web-prod-04", "display_name": "web-server-04.prod.example.com", "status": "Patched", "remediation_available": True},
            {"system_id": "sys-031-web-stg-01", "display_name": "web-server-01.staging.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-032-web-stg-02", "display_name": "web-server-02.staging.example.com", "status": "Patched", "remediation_available": True},
        ],
        "total_affected": 6,
        "total_remediated": 2,
        "total_vulnerable": 4,
    },
    "CVE-2024-54321": {
        "cve_id": "CVE-2024-54321",
        "severity": "Important",
        "cvss_score": 7.5,
        "description": "SQL injection vulnerability in database query parser",
        "pci_impact": True,
        "soc2_impact": True,
        "hipaa_impact": False,
        "compliance_deadline": "2024-04-30",
        "compliance_notes": (
            "PCI-DSS 6.2 requires high-risk vulnerabilities be patched within "
            "90 days. Affects systems storing cardholder data."
        ),
        "affected_systems": [
            {"system_id": "sys-009-db-prod-01", "display_name": "db-server-01.prod.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-010-db-prod-02", "display_name": "db-server-02.prod.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-011-db-prod-03", "display_name": "db-server-03.prod.example.com", "status": "Patched", "remediation_available": True},
            {"system_id": "sys-012-db-prod-04", "display_name": "db-server-04.prod.example.com", "status": "Patched", "remediation_available": True},
            {"system_id": "sys-035-db-stg-01", "display_name": "db-server-01.staging.example.com", "status": "Vulnerable", "remediation_available": True},
        ],
        "total_affected": 5,
        "total_remediated": 2,
        "total_vulnerable": 3,
    },
    "CVE-2024-11111": {
        "cve_id": "CVE-2024-11111",
        "severity": "Moderate",
        "cvss_score": 5.3,
        "description": "Information disclosure in application logging",
        "pci_impact": True,
        "soc2_impact": True,
        "hipaa_impact": True,
        "compliance_deadline": "2024-06-30",
        "compliance_notes": (
            "HIPAA requires remediation of vulnerabilities exposing PHI. "
            "PCI-DSS allows longer timelines for moderate risks."
        ),
        "affected_systems": [
            # 6 vulnerable production app servers
            {"system_id": f"sys-{15+i:03d}-app-prod-{i:02d}", "display_name": f"app-server-{i:02d}.prod.example.com",
             "status": "Vulnerable", "remediation_available": True}
            for i in range(1, 7)
        ] + [
            # 2 affected-but-not-vulnerable production app servers
            {"system_id": "sys-022-app-prod-07", "display_name": "app-server-07.prod.example.com",
             "status": "Affected but not vulnerable", "remediation_available": True,
             "mitigation_reason": "SELinux policy prevents exploitation of logging vulnerability"},
            {"system_id": "sys-023-app-prod-08", "display_name": "app-server-08.prod.example.com",
             "status": "Affected but not vulnerable", "remediation_available": True,
             "mitigation_reason": "Application logging feature is disabled in configuration"},
        ] + [
            # 3 patched staging app servers
            {"system_id": f"sys-{40+i:03d}-app-stg-{i:02d}", "display_name": f"app-server-{i:02d}.staging.example.com",
             "status": "Patched", "remediation_available": True}
            for i in range(1, 4)
        ],
        "total_affected": 11,
        "total_remediated": 3,
        "total_vulnerable": 6,
    },
    "CVE-2024-98765": {
        "cve_id": "CVE-2024-98765",
        "severity": "Important",
        "cvss_score": 8.1,
        "description": "Denial of service vulnerability in load balancer traffic handling",
        "pci_impact": False,
        "soc2_impact": True,
        "hipaa_impact": False,
        "compliance_deadline": "2024-05-15",
        "compliance_notes": (
            "SOC2 CC7.1 requires protection of system availability. "
            "Critical infrastructure should be patched urgently."
        ),
        "affected_systems": [
            {"system_id": "sys-025-lb-prod-01", "display_name": "lb-server-01.prod.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-026-lb-prod-02", "display_name": "lb-server-02.prod.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-027-lb-prod-03", "display_name": "lb-server-03.prod.example.com", "status": "Vulnerable", "remediation_available": True},
            {"system_id": "sys-045-lb-stg-01", "display_name": "lb-server-01.staging.example.com", "status": "Patched", "remediation_available": True},
        ],
        "total_affected": 4,
        "total_remediated": 1,
        "total_vulnerable": 3,
    },
    "CVE-2024-22222": {
        "cve_id": "CVE-2024-22222",
        "severity": "Low",
        "cvss_score": 3.1,
        "description": "Minor information disclosure in monitoring agent error messages",
        "pci_impact": False,
        "soc2_impact": False,
        "hipaa_impact": False,
        "compliance_deadline": None,
        "compliance_notes": "Low severity, no immediate compliance impact. Patch during regular maintenance window.",
        "affected_systems": [
            {"system_id": "sys-028-mon-prod-01", "display_name": "monitor-server-01.prod.example.com", "status": "Vulnerable", "remediation_available": False},
            {"system_id": "sys-029-mon-prod-02", "display_name": "monitor-server-02.prod.example.com", "status": "Vulnerable", "remediation_available": False},
        ],
        "total_affected": 2,
        "total_remediated": 0,
        "total_vulnerable": 2,
    },
}


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("lightspeed-mcp")


@mcp.tool
def get_host_details(
    system_id: Optional[str] = None,
    hostname_pattern: Optional[str] = None,
    tags: Optional[list[str]] = None,
    rhel_version_prefix: Optional[str] = None,
) -> dict:
    """Retrieve registered system inventory from Red Hat Lightspeed.

    Returns all systems when called with no arguments. Supports filtering
    by system ID, hostname pattern, tags, and RHEL version prefix.

    Args:
        system_id: Return only the system matching this ID.
        hostname_pattern: Filter by hostname (supports * wildcards).
        tags: Filter to systems having at least one of these tags.
        rhel_version_prefix: Filter by RHEL version prefix (e.g. "8" or "9.3").
    """
    filtered = list(MOCK_SYSTEMS)

    if system_id:
        filtered = [s for s in filtered if s["id"] == system_id]

    if hostname_pattern:
        pattern = hostname_pattern.replace("*", "")
        filtered = [s for s in filtered if pattern in s["fqdn"]]

    if tags:
        filtered = [
            s for s in filtered
            if any(t in s.get("tags", []) for t in tags)
        ]

    if rhel_version_prefix:
        filtered = [
            s for s in filtered
            if s["rhel_version"].startswith(rhel_version_prefix)
        ]

    return {
        "systems": filtered,
        "total": len(MOCK_SYSTEMS),
        "count": len(filtered),
    }


@mcp.tool
def get_cve_systems(cve_id: str) -> dict:
    """Find systems affected by a specific CVE.

    Returns affected systems with their vulnerability status
    (Vulnerable, Patched, or Affected but not vulnerable) and
    whether automated remediation is available.

    Args:
        cve_id: CVE identifier in CVE-YYYY-NNNNN format.
    """
    if cve_id in MOCK_CVE_DATA:
        return MOCK_CVE_DATA[cve_id]

    return {
        "cve_id": cve_id,
        "affected_systems": [],
        "total_affected": 0,
        "total_remediated": 0,
    }


@mcp.tool
def get_cves() -> dict:
    """List all known CVEs affecting the fleet.

    Returns summary information for every CVE including severity,
    CVSS score, affected/vulnerable counts, and compliance impact.
    """
    summaries = []
    for cve in MOCK_CVE_DATA.values():
        entry = {
            "cve_id": cve["cve_id"],
            "severity": cve["severity"],
            "cvss_score": cve["cvss_score"],
            "description": cve["description"],
            "total_affected": cve["total_affected"],
            "total_remediated": cve["total_remediated"],
            "remediation_available": any(
                s.get("remediation_available", False)
                for s in cve["affected_systems"]
            ),
            "pci_impact": cve["pci_impact"],
            "soc2_impact": cve["soc2_impact"],
            "hipaa_impact": cve["hipaa_impact"],
            "compliance_deadline": cve["compliance_deadline"],
        }
        if "total_vulnerable" in cve:
            entry["total_vulnerable"] = cve["total_vulnerable"]
        summaries.append(entry)
    return {"cves": summaries, "total": len(summaries)}


@mcp.tool
def get_cve(cve_id: str) -> dict:
    """Get detailed information about a specific CVE.

    Returns full CVE metadata including severity, CVSS score, description,
    compliance impact, and deadline — but not the per-system breakdown.
    Use get_cve_systems for that.

    Args:
        cve_id: CVE identifier in CVE-YYYY-NNNNN format.
    """
    if cve_id not in MOCK_CVE_DATA:
        return {"error": f"CVE {cve_id} not found"}

    cve = MOCK_CVE_DATA[cve_id]
    result = {
        "cve_id": cve["cve_id"],
        "severity": cve["severity"],
        "cvss_score": cve["cvss_score"],
        "description": cve["description"],
        "pci_impact": cve["pci_impact"],
        "soc2_impact": cve["soc2_impact"],
        "hipaa_impact": cve["hipaa_impact"],
        "compliance_deadline": cve["compliance_deadline"],
        "compliance_notes": cve["compliance_notes"],
        "total_affected": cve["total_affected"],
        "total_remediated": cve["total_remediated"],
    }
    if "total_vulnerable" in cve:
        result["total_vulnerable"] = cve["total_vulnerable"]
    return result


@mcp.tool
def create_vulnerability_playbook(
    cve_id: str,
    system_ids: Optional[list[str]] = None,
) -> dict:
    """Generate an Ansible remediation playbook for a CVE.

    Creates a playbook targeting the specified systems (or all vulnerable
    systems if none specified). Returns the playbook content and metadata.

    Args:
        cve_id: CVE identifier to remediate.
        system_ids: Specific system IDs to target. Omit for all vulnerable.
    """
    if cve_id not in MOCK_CVE_DATA:
        return {"error": f"CVE {cve_id} not found"}

    cve = MOCK_CVE_DATA[cve_id]
    if not any(s.get("remediation_available") for s in cve["affected_systems"]):
        return {
            "error": "No automated remediation available for this CVE",
            "cve_id": cve_id,
        }

    targets = system_ids or [
        s["system_id"]
        for s in cve["affected_systems"]
        if s["status"] == "Vulnerable"
    ]

    return {
        "cve_id": cve_id,
        "playbook_id": f"playbook-{cve_id.lower()}-mock",
        "target_systems": targets,
        "target_count": len(targets),
        "status": "generated",
        "playbook_content": (
            f"# Auto-generated remediation playbook for {cve_id}\n"
            f"# Targets: {len(targets)} systems\n"
            f"---\n"
            f"- hosts: targeted_systems\n"
            f"  become: true\n"
            f"  tasks:\n"
            f"    - name: Apply patch for {cve_id}\n"
            f"      dnf:\n"
            f"        name: '*'\n"
            f"        state: latest\n"
            f"        security: true\n"
        ),
    }


if __name__ == "__main__":
    mcp.run()

#!/usr/bin/env python3
"""
Mock AAP (Ansible Automation Platform) MCP Server

Simulates the AAP MCP gateway for per-skill evaluation tasks. Implements
the full set of tools used by rh-sre skills:
  - job_templates_list / job_templates_retrieve
  - projects_list
  - job_templates_launch_retrieve
  - jobs_retrieve / jobs_stdout_retrieve
  - jobs_job_events_list / jobs_job_host_summaries_list
  - jobs_relaunch_retrieve
  - inventories_list / hosts_list

Data mirrors a realistic AAP deployment:
  - 6 job templates (3 remediation, 1 compliance, 1 patching, 1 reporting)
  - 3 projects (remediation, compliance, reporting)
  - 3 inventories (production 30 hosts, staging 15 hosts, all-managed 63 hosts)
  - 12 recent jobs with varied statuses

Follows the same mock-server pattern as mock-lightspeed-mcp.py.
"""

import os
import random
from datetime import datetime, timedelta
from typing import Optional

from fastmcp import FastMCP

random.seed(42)

mcp = FastMCP("aap-mcp")

REFERENCE_TIME = datetime(2026, 2, 15, 12, 0, 0)


def _ts(delta: timedelta) -> str:
    return (REFERENCE_TIME - delta).isoformat() + "Z"


# ---------------------------------------------------------------------------
# Mock data: Projects
# ---------------------------------------------------------------------------

MOCK_PROJECTS = [
    {
        "id": 6,
        "type": "project",
        "name": "Remediation Playbooks",
        "description": "CVE and security remediation playbooks managed via Git",
        "scm_type": "git",
        "scm_url": "https://github.com/org/remediation-playbooks.git",
        "scm_branch": "main",
        "scm_revision": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "status": "successful",
        "last_job_run": _ts(timedelta(hours=2)),
        "last_update_failed": False,
        "created": _ts(timedelta(days=90)),
        "modified": _ts(timedelta(hours=2)),
    },
    {
        "id": 7,
        "type": "project",
        "name": "Compliance Checks",
        "description": "STIG and CIS compliance scanning playbooks",
        "scm_type": "git",
        "scm_url": "https://github.com/org/compliance-playbooks.git",
        "scm_branch": "main",
        "scm_revision": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
        "status": "successful",
        "last_job_run": _ts(timedelta(days=1)),
        "last_update_failed": False,
        "created": _ts(timedelta(days=120)),
        "modified": _ts(timedelta(days=1)),
    },
    {
        "id": 8,
        "type": "project",
        "name": "Fleet Reporting",
        "description": "System inventory and health reporting playbooks",
        "scm_type": "git",
        "scm_url": "https://github.com/org/fleet-reports.git",
        "scm_branch": "main",
        "scm_revision": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        "status": "successful",
        "last_job_run": _ts(timedelta(days=3)),
        "last_update_failed": False,
        "created": _ts(timedelta(days=180)),
        "modified": _ts(timedelta(days=3)),
    },
]

# ---------------------------------------------------------------------------
# Mock data: Inventories & Hosts
# ---------------------------------------------------------------------------

MOCK_INVENTORIES = [
    {
        "id": 1,
        "type": "inventory",
        "name": "Production Systems",
        "description": "All production RHEL systems across data centers",
        "total_hosts": 30,
        "has_active_failures": False,
        "hosts_with_active_failures": 0,
        "total_groups": 5,
        "groups_with_active_failures": 0,
        "has_inventory_sources": True,
        "organization": 1,
        "created": _ts(timedelta(days=365)),
        "modified": _ts(timedelta(days=1)),
    },
    {
        "id": 2,
        "type": "inventory",
        "name": "Staging Systems",
        "description": "Pre-production staging environment",
        "total_hosts": 15,
        "has_active_failures": False,
        "hosts_with_active_failures": 0,
        "total_groups": 3,
        "groups_with_active_failures": 0,
        "has_inventory_sources": True,
        "organization": 1,
        "created": _ts(timedelta(days=300)),
        "modified": _ts(timedelta(days=7)),
    },
    {
        "id": 3,
        "type": "inventory",
        "name": "All Managed Systems",
        "description": "Complete fleet: production, staging, development, QA, legacy",
        "total_hosts": 63,
        "has_active_failures": True,
        "hosts_with_active_failures": 2,
        "total_groups": 8,
        "groups_with_active_failures": 1,
        "has_inventory_sources": True,
        "organization": 1,
        "created": _ts(timedelta(days=365)),
        "modified": _ts(timedelta(hours=6)),
    },
]


def _generate_hosts(inventory_id: int) -> list[dict]:
    """Generate realistic hosts for an inventory."""
    hosts: list[dict] = []
    if inventory_id == 1:
        roles = ["web", "db", "app", "lb", "monitoring", "cache"]
        for i, role in enumerate(roles):
            for j in range(5 if role in ("web", "app") else 4 if role == "db" else 3 if role == "monitoring" else 2):
                hosts.append({
                    "id": len(hosts) + 1,
                    "type": "host",
                    "name": f"{role}-{j+1:02d}.prod.example.com",
                    "inventory": inventory_id,
                    "enabled": True,
                    "has_active_failures": False,
                    "variables": f'{{"rhel_version": "9.3", "environment": "production", "role": "{role}"}}',
                })
                if len(hosts) >= 30:
                    break
            if len(hosts) >= 30:
                break
    elif inventory_id == 2:
        for i in range(15):
            role = ["web", "db", "app"][i % 3]
            hosts.append({
                "id": 100 + i,
                "type": "host",
                "name": f"{role}-{i+1:02d}.staging.example.com",
                "inventory": inventory_id,
                "enabled": True,
                "has_active_failures": False,
                "variables": f'{{"rhel_version": "9.3", "environment": "staging", "role": "{role}"}}',
            })
    elif inventory_id == 3:
        for i in range(30):
            hosts.append({
                "id": 200 + i,
                "type": "host",
                "name": f"host-{i+1:02d}.prod.example.com",
                "inventory": inventory_id,
                "enabled": True,
                "has_active_failures": i in (45, 58),
                "variables": f'{{"rhel_version": "9.3", "environment": "production"}}',
            })
        for i in range(15):
            hosts.append({
                "id": 230 + i,
                "type": "host",
                "name": f"host-{i+1:02d}.staging.example.com",
                "inventory": inventory_id,
                "enabled": True,
                "has_active_failures": False,
                "variables": f'{{"rhel_version": "9.3", "environment": "staging"}}',
            })
        for i in range(10):
            hosts.append({
                "id": 245 + i,
                "type": "host",
                "name": f"dev-{i+1:02d}.dev.example.com",
                "inventory": inventory_id,
                "enabled": True,
                "has_active_failures": False,
                "variables": f'{{"rhel_version": "8.9", "environment": "development"}}',
            })
        for i in range(5):
            hosts.append({
                "id": 255 + i,
                "type": "host",
                "name": f"qa-{i+1:02d}.qa.example.com",
                "inventory": inventory_id,
                "enabled": True,
                "has_active_failures": False,
                "variables": f'{{"rhel_version": "9.2", "environment": "qa"}}',
            })
        for i in range(3):
            hosts.append({
                "id": 260 + i,
                "type": "host",
                "name": f"legacy-{i+1:02d}.corp.example.com",
                "inventory": inventory_id,
                "enabled": i < 2,
                "has_active_failures": i == 2,
                "variables": f'{{"rhel_version": "7.9", "environment": "legacy"}}',
            })
    return hosts


# ---------------------------------------------------------------------------
# Mock data: Job Templates
# ---------------------------------------------------------------------------

MOCK_JOB_TEMPLATES = [
    {
        "id": 10,
        "type": "job_template",
        "name": "CVE Remediation - Kernel Update",
        "description": "Kernel update with boom snapshot for rollback safety",
        "inventory": 1,
        "project": 6,
        "playbook": "playbooks/remediation/cve-kernel-update.yml",
        "become_enabled": True,
        "ask_job_type_on_launch": True,
        "ask_variables_on_launch": True,
        "ask_limit_on_launch": True,
        "ask_inventory_on_launch": True,
        "job_type": "check",
        "verbosity": 1,
        "timeout": 3600,
        "forks": 5,
        "status": "successful",
        "last_job_run": _ts(timedelta(hours=4)),
        "summary_fields": {
            "project": {"id": 6, "name": "Remediation Playbooks", "status": "successful"},
            "inventory": {"id": 1, "name": "Production Systems", "total_hosts": 30},
            "credentials": [
                {"id": 1, "name": "machine-credential", "kind": "ssh"},
            ],
            "last_job": {"id": 1001, "status": "successful", "finished": _ts(timedelta(hours=4))},
        },
        "created": _ts(timedelta(days=60)),
        "modified": _ts(timedelta(days=2)),
    },
    {
        "id": 11,
        "type": "job_template",
        "name": "CVE Remediation - Package Update",
        "description": "General package update for CVE remediation with needs-restarting check",
        "inventory": 1,
        "project": 6,
        "playbook": "playbooks/remediation/cve-package-update.yml",
        "become_enabled": True,
        "ask_job_type_on_launch": True,
        "ask_variables_on_launch": True,
        "ask_limit_on_launch": True,
        "ask_inventory_on_launch": False,
        "job_type": "check",
        "verbosity": 1,
        "timeout": 1800,
        "forks": 10,
        "status": "successful",
        "last_job_run": _ts(timedelta(hours=12)),
        "summary_fields": {
            "project": {"id": 6, "name": "Remediation Playbooks", "status": "successful"},
            "inventory": {"id": 1, "name": "Production Systems", "total_hosts": 30},
            "credentials": [
                {"id": 1, "name": "machine-credential", "kind": "ssh"},
            ],
            "last_job": {"id": 1005, "status": "successful", "finished": _ts(timedelta(hours=12))},
        },
        "created": _ts(timedelta(days=45)),
        "modified": _ts(timedelta(days=5)),
    },
    {
        "id": 12,
        "type": "job_template",
        "name": "CVE Remediation - Generic",
        "description": "Generic CVE remediation template for ad-hoc patches",
        "inventory": 1,
        "project": 6,
        "playbook": "playbooks/remediation/cve-remediation.yml",
        "become_enabled": True,
        "ask_job_type_on_launch": True,
        "ask_variables_on_launch": True,
        "ask_limit_on_launch": True,
        "ask_inventory_on_launch": True,
        "job_type": "check",
        "verbosity": 1,
        "timeout": 3600,
        "forks": 5,
        "status": "never updated",
        "last_job_run": None,
        "summary_fields": {
            "project": {"id": 6, "name": "Remediation Playbooks", "status": "successful"},
            "inventory": {"id": 1, "name": "Production Systems", "total_hosts": 30},
            "credentials": [
                {"id": 1, "name": "machine-credential", "kind": "ssh"},
            ],
        },
        "created": _ts(timedelta(days=30)),
        "modified": _ts(timedelta(days=30)),
    },
    {
        "id": 20,
        "type": "job_template",
        "name": "Compliance Check - STIG",
        "description": "Run STIG compliance scan across fleet",
        "inventory": 3,
        "project": 7,
        "playbook": "playbooks/compliance/check-all.yml",
        "become_enabled": True,
        "ask_job_type_on_launch": True,
        "ask_variables_on_launch": False,
        "ask_limit_on_launch": True,
        "ask_inventory_on_launch": False,
        "job_type": "run",
        "verbosity": 0,
        "timeout": 7200,
        "forks": 20,
        "status": "successful",
        "last_job_run": _ts(timedelta(days=1)),
        "summary_fields": {
            "project": {"id": 7, "name": "Compliance Checks", "status": "successful"},
            "inventory": {"id": 3, "name": "All Managed Systems", "total_hosts": 63},
            "credentials": [
                {"id": 2, "name": "compliance-credential", "kind": "ssh"},
            ],
            "last_job": {"id": 1010, "status": "successful", "finished": _ts(timedelta(days=1))},
        },
        "created": _ts(timedelta(days=180)),
        "modified": _ts(timedelta(days=14)),
    },
    {
        "id": 25,
        "type": "job_template",
        "name": "Emergency Patching",
        "description": "Emergency patch application — NO become enabled (misconfigured)",
        "inventory": 1,
        "project": 6,
        "playbook": "playbooks/remediation/emergency-patch.yml",
        "become_enabled": False,
        "ask_job_type_on_launch": False,
        "ask_variables_on_launch": False,
        "ask_limit_on_launch": False,
        "ask_inventory_on_launch": False,
        "job_type": "run",
        "verbosity": 0,
        "timeout": 600,
        "forks": 25,
        "status": "failed",
        "last_job_run": _ts(timedelta(days=7)),
        "summary_fields": {
            "project": {"id": 6, "name": "Remediation Playbooks", "status": "successful"},
            "inventory": {"id": 1, "name": "Production Systems", "total_hosts": 30},
            "credentials": [
                {"id": 1, "name": "machine-credential", "kind": "ssh"},
            ],
            "last_job": {"id": 1020, "status": "failed", "finished": _ts(timedelta(days=7))},
        },
        "created": _ts(timedelta(days=200)),
        "modified": _ts(timedelta(days=200)),
    },
    {
        "id": 30,
        "type": "job_template",
        "name": "Fleet Health Report",
        "description": "Generate fleet health and inventory report",
        "inventory": 3,
        "project": 8,
        "playbook": "playbooks/reporting/fleet-health.yml",
        "become_enabled": False,
        "ask_job_type_on_launch": False,
        "ask_variables_on_launch": True,
        "ask_limit_on_launch": False,
        "ask_inventory_on_launch": False,
        "job_type": "run",
        "verbosity": 0,
        "timeout": 1800,
        "forks": 30,
        "status": "successful",
        "last_job_run": _ts(timedelta(hours=6)),
        "summary_fields": {
            "project": {"id": 8, "name": "Fleet Reporting", "status": "successful"},
            "inventory": {"id": 3, "name": "All Managed Systems", "total_hosts": 63},
            "credentials": [
                {"id": 1, "name": "machine-credential", "kind": "ssh"},
            ],
            "last_job": {"id": 1025, "status": "successful", "finished": _ts(timedelta(hours=6))},
        },
        "created": _ts(timedelta(days=120)),
        "modified": _ts(timedelta(days=14)),
    },
]

# ---------------------------------------------------------------------------
# Mock data: Jobs (recent runs)
# ---------------------------------------------------------------------------

PROD_HOSTS = [
    "web-01.prod.example.com",
    "web-02.prod.example.com",
    "db-01.prod.example.com",
    "db-02.prod.example.com",
    "app-01.prod.example.com",
    "app-02.prod.example.com",
]

MOCK_JOBS = [
    {
        "id": 1001,
        "type": "job",
        "name": "CVE Remediation - Kernel Update",
        "job_type": "check",
        "status": "successful",
        "failed": False,
        "started": _ts(timedelta(hours=4, minutes=30)),
        "finished": _ts(timedelta(hours=4)),
        "elapsed": 1800.0,
        "job_template": 10,
        "inventory": 1,
        "project": 6,
        "playbook": "playbooks/remediation/cve-kernel-update.yml",
        "limit": "web-01.prod.example.com,web-02.prod.example.com,db-01.prod.example.com",
        "extra_vars": '{"target_cve": "CVE-2024-12345", "remediation_mode": "automated", "verify_after": true}',
        "launch_type": "manual",
        "summary_fields": {
            "job_template": {"id": 10, "name": "CVE Remediation - Kernel Update"},
        },
    },
    {
        "id": 1002,
        "type": "job",
        "name": "CVE Remediation - Kernel Update",
        "job_type": "run",
        "status": "successful",
        "failed": False,
        "started": _ts(timedelta(hours=3, minutes=45)),
        "finished": _ts(timedelta(hours=3)),
        "elapsed": 2700.0,
        "job_template": 10,
        "inventory": 1,
        "project": 6,
        "playbook": "playbooks/remediation/cve-kernel-update.yml",
        "limit": "web-01.prod.example.com,web-02.prod.example.com,db-01.prod.example.com",
        "extra_vars": '{"target_cve": "CVE-2024-12345", "remediation_mode": "automated", "verify_after": true}',
        "launch_type": "manual",
        "summary_fields": {
            "job_template": {"id": 10, "name": "CVE Remediation - Kernel Update"},
        },
    },
    {
        "id": 1005,
        "type": "job",
        "name": "CVE Remediation - Package Update",
        "job_type": "run",
        "status": "successful",
        "failed": False,
        "started": _ts(timedelta(hours=12, minutes=20)),
        "finished": _ts(timedelta(hours=12)),
        "elapsed": 1200.0,
        "job_template": 11,
        "inventory": 1,
        "project": 6,
        "playbook": "playbooks/remediation/cve-package-update.yml",
        "limit": "",
        "extra_vars": '{"target_cve": "CVE-2024-54321"}',
        "launch_type": "manual",
        "summary_fields": {
            "job_template": {"id": 11, "name": "CVE Remediation - Package Update"},
        },
    },
    {
        "id": 1010,
        "type": "job",
        "name": "Compliance Check - STIG",
        "job_type": "run",
        "status": "successful",
        "failed": False,
        "started": _ts(timedelta(days=1, hours=2)),
        "finished": _ts(timedelta(days=1)),
        "elapsed": 7200.0,
        "job_template": 20,
        "inventory": 3,
        "project": 7,
        "playbook": "playbooks/compliance/check-all.yml",
        "limit": "",
        "extra_vars": "{}",
        "launch_type": "scheduled",
        "summary_fields": {
            "job_template": {"id": 20, "name": "Compliance Check - STIG"},
        },
    },
    {
        "id": 1020,
        "type": "job",
        "name": "Emergency Patching",
        "job_type": "run",
        "status": "failed",
        "failed": True,
        "started": _ts(timedelta(days=7, hours=1)),
        "finished": _ts(timedelta(days=7)),
        "elapsed": 3600.0,
        "job_template": 25,
        "inventory": 1,
        "project": 6,
        "playbook": "playbooks/remediation/emergency-patch.yml",
        "limit": "",
        "extra_vars": "{}",
        "launch_type": "manual",
        "summary_fields": {
            "job_template": {"id": 25, "name": "Emergency Patching"},
        },
    },
    {
        "id": 1025,
        "type": "job",
        "name": "Fleet Health Report",
        "job_type": "run",
        "status": "successful",
        "failed": False,
        "started": _ts(timedelta(hours=6, minutes=30)),
        "finished": _ts(timedelta(hours=6)),
        "elapsed": 1800.0,
        "job_template": 30,
        "inventory": 3,
        "project": 8,
        "playbook": "playbooks/reporting/fleet-health.yml",
        "limit": "",
        "extra_vars": "{}",
        "launch_type": "scheduled",
        "summary_fields": {
            "job_template": {"id": 30, "name": "Fleet Health Report"},
        },
    },
]

_next_job_id = 2000


# ---------------------------------------------------------------------------
# Mock stdout generators
# ---------------------------------------------------------------------------

def _generate_stdout(job: dict) -> str:
    """Generate realistic Ansible playbook stdout for a job."""
    playbook_name = job.get("name", "Unknown")
    job_type = job.get("job_type", "run")
    status = job.get("status", "successful")
    limit = job.get("limit", "")
    hosts = limit.split(",") if limit else PROD_HOSTS[:3]
    hosts = [h.strip() for h in hosts if h.strip()]
    extra_vars = job.get("extra_vars", "{}")
    mode = " (CHECK MODE)" if job_type == "check" else ""

    lines = []
    lines.append(f"PLAY [{playbook_name}] *****")
    lines.append("")

    lines.append(f"TASK [Gathering Facts{mode}] *****")
    for h in hosts:
        lines.append(f"ok: [{h}]")
    lines.append("")

    if "kernel" in playbook_name.lower():
        lines.append(f"TASK [Create boom snapshot for rollback{mode}] *****")
        for h in hosts:
            lines.append(f"changed: [{h}] => {{\"msg\": \"boom create --title pre-remediation-CVE-2024-12345\"}}")
        lines.append("")

        lines.append(f"TASK [Check disk space for kernel update{mode}] *****")
        for h in hosts:
            lines.append(f"ok: [{h}] => {{\"msg\": \"Disk space OK: 45% used\"}}")
        lines.append("")

        lines.append(f"TASK [Update kernel package{mode}] *****")
        for h in hosts:
            result = "changed" if status == "successful" else "fatal"
            if result == "changed":
                lines.append(f'changed: [{h}] => {{"msg": "kernel-5.14.0-362.24.1.el9_3 -> kernel-5.14.0-362.24.2.el9_3"}}')
            else:
                lines.append(f'fatal: [{h}]: FAILED! => {{"msg": "Permission denied", "rc": 1}}')
        lines.append("")

        lines.append(f"TASK [Check if reboot is needed (needs-restarting -r){mode}] *****")
        for h in hosts:
            lines.append(f'changed: [{h}] => {{"rc": 1, "msg": "Reboot is required to fully utilize updates."}}')
        lines.append("")

    elif "package" in playbook_name.lower():
        lines.append(f"TASK [Update target packages for CVE remediation{mode}] *****")
        for h in hosts:
            lines.append(f'changed: [{h}] => {{"msg": "httpd-2.4.53-7.el9 -> httpd-2.4.57-8.el9"}}')
        lines.append("")

        lines.append(f"TASK [Restart affected services{mode}] *****")
        for h in hosts:
            lines.append(f"changed: [{h}]")
        lines.append("")

        lines.append(f"TASK [Verify service health{mode}] *****")
        for h in hosts:
            lines.append(f'ok: [{h}] => {{"msg": "Service httpd is running"}}')
        lines.append("")

    elif "emergency" in playbook_name.lower() and status == "failed":
        lines.append(f"TASK [Apply emergency patch{mode}] *****")
        for h in hosts:
            lines.append(f'fatal: [{h}]: FAILED! => {{"msg": "Missing sudo password (become_enabled not set)", "rc": 1}}')
        lines.append("")
        lines.append("NO MORE HOSTS LEFT *****")
        lines.append("")

    else:
        lines.append(f"TASK [Execute playbook tasks{mode}] *****")
        for h in hosts:
            lines.append(f"changed: [{h}]")
        lines.append("")

    lines.append("PLAY RECAP *****")
    for h in hosts:
        if status == "successful":
            ok_count = random.randint(3, 6)
            changed_count = random.randint(1, 3)
            lines.append(f"{h:<45} : ok={ok_count}    changed={changed_count}    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0")
        elif status == "failed":
            lines.append(f"{h:<45} : ok=1    changed=0    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0")
    lines.append("")

    return "\n".join(lines)


def _generate_events(job: dict) -> list[dict]:
    """Generate realistic Ansible task events for a job."""
    hosts = (job.get("limit", "").split(",") if job.get("limit") else PROD_HOSTS[:3])
    hosts = [h.strip() for h in hosts if h.strip()]
    events: list[dict] = []
    eid = 1

    task_names = ["Gathering Facts"]
    if "kernel" in job.get("name", "").lower():
        task_names += [
            "Create boom snapshot for rollback",
            "Check disk space for kernel update",
            "Update kernel package",
            "Check if reboot is needed (needs-restarting -r)",
        ]
    elif "package" in job.get("name", "").lower():
        task_names += [
            "Update target packages for CVE remediation",
            "Restart affected services",
            "Verify service health",
        ]
    else:
        task_names += ["Execute playbook tasks"]

    for task_name in task_names:
        for host in hosts:
            is_failed = job.get("status") == "failed" and task_name != "Gathering Facts"
            events.append({
                "id": eid,
                "type": "job_event",
                "event": "runner_on_ok" if not is_failed else "runner_on_failed",
                "task": task_name,
                "host": host,
                "host_name": host,
                "play": job.get("name", ""),
                "changed": task_name != "Gathering Facts" and not is_failed,
                "failed": is_failed,
                "event_data": {
                    "task": task_name,
                    "host": host,
                    "res": {
                        "changed": task_name != "Gathering Facts" and not is_failed,
                        "msg": "Task completed" if not is_failed else "Permission denied",
                    },
                },
                "created": _ts(timedelta(hours=4, minutes=30 - eid)),
            })
            eid += 1

    return events


def _generate_host_summaries(job: dict) -> list[dict]:
    """Generate per-host summaries for a job."""
    hosts = (job.get("limit", "").split(",") if job.get("limit") else PROD_HOSTS[:3])
    hosts = [h.strip() for h in hosts if h.strip()]
    summaries: list[dict] = []

    for i, host in enumerate(hosts):
        is_failed = job.get("status") == "failed"
        summaries.append({
            "id": i + 1,
            "type": "job_host_summary",
            "host": i + 1,
            "host_name": host,
            "ok": 1 if is_failed else random.randint(3, 6),
            "changed": 0 if is_failed else random.randint(1, 3),
            "dark": 0,
            "failures": 1 if is_failed else 0,
            "skipped": 0,
            "processed": 1,
            "failed": is_failed,
        })

    return summaries


# ---------------------------------------------------------------------------
# MCP Tools: Job Management
# ---------------------------------------------------------------------------

@mcp.tool()
def job_templates_list(
    page_size: int = 10,
    search: Optional[str] = None,
) -> dict:
    """List available job templates in AAP.

    Args:
        page_size: Number of results per page (default 10, max 200).
        search: Optional search string to filter templates by name.
    """
    results = MOCK_JOB_TEMPLATES
    if search:
        s = search.lower()
        results = [t for t in results if s in t["name"].lower() or s in t.get("description", "").lower()]
    return {
        "count": len(results),
        "next": None,
        "previous": None,
        "results": results[:page_size],
    }


@mcp.tool()
def job_templates_retrieve(id: str) -> dict:
    """Retrieve detailed information about a specific job template.

    Args:
        id: Job template ID (as string).
    """
    tid = int(id)
    template = next((t for t in MOCK_JOB_TEMPLATES if t["id"] == tid), None)
    if not template:
        return {"detail": f"Not found. Job template {id} does not exist."}
    return template


@mcp.tool()
def projects_list(
    page_size: int = 50,
    search: Optional[str] = None,
) -> dict:
    """List available projects in AAP.

    Args:
        page_size: Number of results per page.
        search: Optional search string to filter projects by name.
    """
    results = MOCK_PROJECTS
    if search:
        s = search.lower()
        results = [p for p in results if s in p["name"].lower() or s in p.get("description", "").lower()]
    return {
        "count": len(results),
        "next": None,
        "previous": None,
        "results": results[:page_size],
    }


@mcp.tool()
def job_templates_launch_retrieve(
    id: str,
    requestBody: Optional[dict] = None,
) -> dict:
    """Launch a job from a job template.

    Args:
        id: Job template ID to launch.
        requestBody: Optional launch parameters including job_type ('run' or 'check'),
                      extra_vars (dict), and limit (comma-separated host list).
    """
    global _next_job_id
    tid = int(id)
    template = next((t for t in MOCK_JOB_TEMPLATES if t["id"] == tid), None)
    if not template:
        return {"detail": f"Not found. Job template {id} does not exist."}

    body = requestBody or {}
    job_type = body.get("job_type", template.get("job_type", "run"))

    if not template.get("ask_job_type_on_launch") and job_type != template.get("job_type"):
        return {
            "error": f"Cannot override job_type: ask_job_type_on_launch is disabled on template {id}",
        }

    job_id = _next_job_id
    _next_job_id += 1

    new_job = {
        "id": job_id,
        "type": "job",
        "name": template["name"],
        "job_type": job_type,
        "status": "pending",
        "failed": False,
        "started": _ts(timedelta(seconds=0)),
        "finished": None,
        "elapsed": 0.0,
        "job_template": tid,
        "inventory": template["inventory"],
        "project": template["project"],
        "playbook": template["playbook"],
        "limit": body.get("limit", ""),
        "extra_vars": str(body.get("extra_vars", {})),
        "launch_type": "manual",
        "summary_fields": {
            "job_template": {"id": tid, "name": template["name"]},
        },
    }
    MOCK_JOBS.append(new_job)

    # Simulate job completion after launch
    new_job["status"] = "successful"
    new_job["finished"] = _ts(timedelta(seconds=-300))
    new_job["elapsed"] = 300.0

    return {
        "job": job_id,
        "status": "pending",
        "type": "job",
        "url": f"/api/controller/v2/jobs/{job_id}/",
        "related": {
            "stdout": f"/api/controller/v2/jobs/{job_id}/stdout/",
            "job_events": f"/api/controller/v2/jobs/{job_id}/job_events/",
            "job_host_summaries": f"/api/controller/v2/jobs/{job_id}/job_host_summaries/",
        },
    }


@mcp.tool()
def jobs_retrieve(id: int) -> dict:
    """Get the status and details of a job run.

    Args:
        id: Job ID to retrieve.
    """
    job = next((j for j in MOCK_JOBS if j["id"] == id), None)
    if not job:
        return {"detail": f"Not found. Job {id} does not exist."}
    return job


@mcp.tool()
def jobs_list(page_size: int = 10) -> dict:
    """List recent job runs.

    Args:
        page_size: Number of results to return.
    """
    results = sorted(MOCK_JOBS, key=lambda j: j.get("started", ""), reverse=True)
    return {
        "count": len(results),
        "next": None,
        "previous": None,
        "results": results[:page_size],
    }


@mcp.tool()
def jobs_stdout_retrieve(id: int, format: str = "txt") -> dict:
    """Get the stdout (console output) from a job run.

    Args:
        id: Job ID.
        format: Output format ('txt' or 'json'). Default 'txt'.
    """
    job = next((j for j in MOCK_JOBS if j["id"] == id), None)
    if not job:
        return {"detail": f"Not found. Job {id} does not exist."}
    return {
        "content": _generate_stdout(job),
        "range": {"start": 0, "end": 1},
    }


@mcp.tool()
def jobs_job_events_list(id: int, page_size: int = 50) -> dict:
    """Get task-level events for a job run.

    Args:
        id: Job ID.
        page_size: Number of events to return.
    """
    job = next((j for j in MOCK_JOBS if j["id"] == id), None)
    if not job:
        return {"detail": f"Not found. Job {id} does not exist."}
    events = _generate_events(job)
    return {
        "count": len(events),
        "next": None,
        "previous": None,
        "results": events[:page_size],
    }


@mcp.tool()
def jobs_job_host_summaries_list(id: int) -> dict:
    """Get per-host execution summaries for a job run.

    Args:
        id: Job ID.
    """
    job = next((j for j in MOCK_JOBS if j["id"] == id), None)
    if not job:
        return {"detail": f"Not found. Job {id} does not exist."}
    summaries = _generate_host_summaries(job)
    return {
        "count": len(summaries),
        "next": None,
        "previous": None,
        "results": summaries,
    }


@mcp.tool()
def jobs_relaunch_retrieve(
    id: int,
    hosts: str = "all",
    job_type: str = "run",
) -> dict:
    """Relaunch a previously completed or failed job.

    Args:
        id: Original job ID to relaunch.
        hosts: Which hosts to target ('all' or 'failed').
        job_type: Job type for relaunch ('run' or 'check').
    """
    global _next_job_id
    original = next((j for j in MOCK_JOBS if j["id"] == id), None)
    if not original:
        return {"detail": f"Not found. Job {id} does not exist."}

    new_id = _next_job_id
    _next_job_id += 1

    new_job = {
        **original,
        "id": new_id,
        "job_type": job_type,
        "status": "successful",
        "failed": False,
        "started": _ts(timedelta(seconds=0)),
        "finished": _ts(timedelta(seconds=-300)),
        "elapsed": 300.0,
        "launch_type": "relaunch",
    }
    MOCK_JOBS.append(new_job)

    return {
        "job": new_id,
        "status": "pending",
        "type": "job",
        "url": f"/api/controller/v2/jobs/{new_id}/",
    }


# ---------------------------------------------------------------------------
# MCP Tools: Inventory Management
# ---------------------------------------------------------------------------

@mcp.tool()
def inventories_list(
    page_size: int = 10,
    search: Optional[str] = None,
) -> dict:
    """List available inventories in AAP.

    Args:
        page_size: Number of results per page.
        search: Optional search string to filter inventories.
    """
    results = MOCK_INVENTORIES
    if search:
        s = search.lower()
        results = [inv for inv in results if s in inv["name"].lower() or s in inv.get("description", "").lower()]
    return {
        "count": len(results),
        "next": None,
        "previous": None,
        "results": results[:page_size],
    }


@mcp.tool()
def hosts_list(
    inventory_id: Optional[int] = None,
    page_size: int = 50,
    search: Optional[str] = None,
) -> dict:
    """List hosts in an inventory.

    Args:
        inventory_id: Filter by inventory ID. If not provided, lists hosts from all inventories.
        page_size: Number of results per page.
        search: Optional search string to filter hosts by name.
    """
    inv_id = inventory_id or 1
    hosts = _generate_hosts(inv_id)
    if search:
        s = search.lower()
        hosts = [h for h in hosts if s in h["name"].lower()]
    return {
        "count": len(hosts),
        "next": None if len(hosts) <= page_size else f"/api/controller/v2/hosts/?page=2",
        "previous": None,
        "results": hosts[:page_size],
    }


if __name__ == "__main__":
    mcp.run()

#!/usr/bin/env python3
"""Mock RHEL System MCP Server for RHEL debugging evaluation.

Simulates a RHEL 9 host with a failing service. Exposes system-level
diagnostic tools (systemctl, journalctl, getenforce, firewall-cmd, ausearch)
as MCP tools so the agent can diagnose the issue.

Scenario:
  Host: app-server-01.example.com (RHEL 9.3)
  Failing service: myapp.service
  Root causes:
    1. SELinux denial: httpd_t cannot bind to port 9090
    2. Firewall: port 9090/tcp is not open
    3. Service configuration references correct binary but SELinux blocks it
"""

import json
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("rhel-system")

HOST = "app-server-01.example.com"
RHEL_VER = "9.3"

SERVICES = {
    "myapp.service": {
        "loaded": True,
        "enabled": True,
        "active": "failed",
        "sub": "failed",
        "description": "My Application Service",
        "main_pid": 0,
        "exit_code": "exited",
        "exit_status": 1,
        "exec_start": "/opt/myapp/bin/myapp-server --port 9090 --config /etc/myapp/config.yaml",
        "user": "myapp",
        "group": "myapp",
        "working_directory": "/opt/myapp",
        "environment": "APP_ENV=production DB_HOST=localhost DB_PORT=5432",
        "restart": "on-failure",
        "restart_sec": 5,
        "status_output": (
            "● myapp.service - My Application Service\n"
            "     Loaded: loaded (/etc/systemd/system/myapp.service; enabled; preset: disabled)\n"
            "     Active: failed (Result: exit-code) since Sun 2026-03-01 18:30:45 UTC; 17h ago\n"
            "    Process: 45678 ExecStart=/opt/myapp/bin/myapp-server --port 9090 --config /etc/myapp/config.yaml (code=exited, status=1/FAILURE)\n"
            "   Main PID: 45678 (code=exited, status=1/FAILURE)\n"
            "        CPU: 125ms\n"
            "\n"
            "Mar 01 18:30:44 app-server-01 systemd[1]: Starting My Application Service...\n"
            "Mar 01 18:30:44 app-server-01 myapp-server[45678]: Starting myapp-server v2.1.0\n"
            "Mar 01 18:30:44 app-server-01 myapp-server[45678]: Loading configuration from /etc/myapp/config.yaml\n"
            "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Configuration loaded successfully\n"
            "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Attempting to bind to 0.0.0.0:9090\n"
            "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Error: Permission denied: bind to 0.0.0.0:9090\n"
            "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Fatal: Cannot start server, exiting\n"
            "Mar 01 18:30:45 app-server-01 systemd[1]: myapp.service: Main process exited, code=exited, status=1/FAILURE\n"
            "Mar 01 18:30:45 app-server-01 systemd[1]: myapp.service: Failed with result 'exit-code'.\n"
        ),
    },
    "sshd.service": {
        "loaded": True,
        "enabled": True,
        "active": "active",
        "sub": "running",
        "description": "OpenSSH server daemon",
        "main_pid": 1234,
        "exit_code": "",
        "exit_status": 0,
    },
    "firewalld.service": {
        "loaded": True,
        "enabled": True,
        "active": "active",
        "sub": "running",
        "description": "firewalld - dynamic firewall daemon",
        "main_pid": 2345,
        "exit_code": "",
        "exit_status": 0,
    },
    "postgresql.service": {
        "loaded": True,
        "enabled": True,
        "active": "active",
        "sub": "running",
        "description": "PostgreSQL database server",
        "main_pid": 3456,
        "exit_code": "",
        "exit_status": 0,
    },
}

JOURNAL_LOGS = {
    "myapp.service": (
        "-- Journal begins at Sat 2026-02-28 00:00:00 UTC, ends at Sun 2026-03-02 12:00:00 UTC. --\n"
        "Mar 01 18:30:44 app-server-01 systemd[1]: Starting My Application Service...\n"
        "Mar 01 18:30:44 app-server-01 myapp-server[45678]: Starting myapp-server v2.1.0\n"
        "Mar 01 18:30:44 app-server-01 myapp-server[45678]: Loading configuration from /etc/myapp/config.yaml\n"
        "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Configuration loaded successfully\n"
        "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Connecting to database at localhost:5432... OK\n"
        "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Attempting to bind to 0.0.0.0:9090\n"
        "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Error: Permission denied: bind to 0.0.0.0:9090\n"
        "Mar 01 18:30:45 app-server-01 myapp-server[45678]: Fatal: Cannot start server, exiting\n"
        "Mar 01 18:30:45 app-server-01 systemd[1]: myapp.service: Main process exited, code=exited, status=1/FAILURE\n"
        "Mar 01 18:30:45 app-server-01 systemd[1]: myapp.service: Failed with result 'exit-code'.\n"
        "Mar 01 18:30:50 app-server-01 systemd[1]: myapp.service: Scheduled restart job, restart counter is at 1.\n"
        "Mar 01 18:30:50 app-server-01 systemd[1]: Starting My Application Service...\n"
        "Mar 01 18:30:50 app-server-01 myapp-server[45690]: Starting myapp-server v2.1.0\n"
        "Mar 01 18:30:51 app-server-01 myapp-server[45690]: Loading configuration from /etc/myapp/config.yaml\n"
        "Mar 01 18:30:51 app-server-01 myapp-server[45690]: Configuration loaded successfully\n"
        "Mar 01 18:30:51 app-server-01 myapp-server[45690]: Connecting to database at localhost:5432... OK\n"
        "Mar 01 18:30:51 app-server-01 myapp-server[45690]: Attempting to bind to 0.0.0.0:9090\n"
        "Mar 01 18:30:51 app-server-01 myapp-server[45690]: Error: Permission denied: bind to 0.0.0.0:9090\n"
        "Mar 01 18:30:51 app-server-01 myapp-server[45690]: Fatal: Cannot start server, exiting\n"
        "Mar 01 18:30:51 app-server-01 systemd[1]: myapp.service: Main process exited, code=exited, status=1/FAILURE\n"
        "Mar 01 18:30:51 app-server-01 systemd[1]: myapp.service: Failed with result 'exit-code'.\n"
        "Mar 01 18:30:56 app-server-01 systemd[1]: myapp.service: Scheduled restart job, restart counter is at 2.\n"
        "Mar 01 18:30:56 app-server-01 systemd[1]: Starting My Application Service...\n"
        "Mar 01 18:30:56 app-server-01 myapp-server[45705]: Starting myapp-server v2.1.0\n"
        "Mar 01 18:30:57 app-server-01 myapp-server[45705]: Error: Permission denied: bind to 0.0.0.0:9090\n"
        "Mar 01 18:30:57 app-server-01 myapp-server[45705]: Fatal: Cannot start server, exiting\n"
        "Mar 01 18:30:57 app-server-01 systemd[1]: myapp.service: Main process exited, code=exited, status=1/FAILURE\n"
        "Mar 01 18:30:57 app-server-01 systemd[1]: myapp.service: Failed with result 'exit-code'.\n"
        "Mar 01 18:30:57 app-server-01 systemd[1]: myapp.service: Start request repeated too quickly.\n"
        "Mar 01 18:30:57 app-server-01 systemd[1]: myapp.service: Failed with result 'exit-code'.\n"
    ),
}


@mcp.tool()
def systemctl_status(service: str) -> str:
    """Get the status of a systemd service (equivalent to 'systemctl status <service>')."""
    svc = SERVICES.get(service)
    if not svc:
        return f"Unit {service} could not be found."

    if svc.get("status_output"):
        return svc["status_output"]

    state = "active (running)" if svc["active"] == "active" else "failed"
    return (
        f"● {service} - {svc['description']}\n"
        f"     Loaded: loaded (/usr/lib/systemd/system/{service}; "
        f"{'enabled' if svc['enabled'] else 'disabled'}; preset: disabled)\n"
        f"     Active: {state}\n"
        f"   Main PID: {svc['main_pid']}\n"
    )


@mcp.tool()
def systemctl_list_failed() -> str:
    """List all failed systemd services (equivalent to 'systemctl --failed')."""
    failed = [(name, svc) for name, svc in SERVICES.items() if svc["active"] == "failed"]
    if not failed:
        return "0 loaded units listed."

    lines = ["  UNIT                    LOAD   ACTIVE SUB    DESCRIPTION"]
    for name, svc in failed:
        lines.append(
            f"  {name:<24s} loaded failed failed {svc['description']}"
        )
    lines.append(f"\n{len(failed)} loaded units listed.")
    return "\n".join(lines)


@mcp.tool()
def journalctl(unit: Optional[str] = None, lines: int = 100, priority: Optional[str] = None) -> str:
    """Get journal logs, optionally filtered by unit or priority."""
    if unit and unit in JOURNAL_LOGS:
        log = JOURNAL_LOGS[unit]
        if priority and priority in ("err", "3"):
            return "\n".join(
                line for line in log.split("\n")
                if "Error" in line or "Fatal" in line or "FAILURE" in line or "failed" in line.lower()
            )
        return log

    if unit:
        return f"-- No entries for unit {unit} --"

    return (
        "-- Journal begins at Sat 2026-02-28 00:00:00 UTC --\n"
        "Mar 02 12:00:00 app-server-01 kernel: Linux version 5.14.0-362.el9.x86_64\n"
        "Mar 02 12:00:00 app-server-01 systemd[1]: Started system.\n"
    )


@mcp.tool()
def getenforce() -> str:
    """Get SELinux enforcement mode (equivalent to 'getenforce')."""
    return "Enforcing"


@mcp.tool()
def ausearch_avc(recent: bool = True, comm: Optional[str] = None) -> str:
    """Search for SELinux AVC denial messages (equivalent to 'ausearch -m AVC')."""
    denials = [
        {
            "timestamp": "Mar 01 18:30:45",
            "type": "AVC",
            "result": "denied",
            "permission": "name_bind",
            "scontext": "system_u:system_r:httpd_t:s0",
            "tcontext": "system_u:object_r:unreserved_port_t:s0",
            "tclass": "tcp_socket",
            "comm": "myapp-server",
            "port": 9090,
        },
        {
            "timestamp": "Mar 01 18:30:50",
            "type": "AVC",
            "result": "denied",
            "permission": "name_bind",
            "scontext": "system_u:system_r:httpd_t:s0",
            "tcontext": "system_u:object_r:unreserved_port_t:s0",
            "tclass": "tcp_socket",
            "comm": "myapp-server",
            "port": 9090,
        },
        {
            "timestamp": "Mar 01 18:30:56",
            "type": "AVC",
            "result": "denied",
            "permission": "name_bind",
            "scontext": "system_u:system_r:httpd_t:s0",
            "tcontext": "system_u:object_r:unreserved_port_t:s0",
            "tclass": "tcp_socket",
            "comm": "myapp-server",
            "port": 9090,
        },
    ]

    if comm:
        denials = [d for d in denials if d["comm"] == comm]

    if not denials:
        return "No AVC denials found."

    lines = []
    for d in denials:
        lines.append(
            f"----\n"
            f"time->{d['timestamp']}\n"
            f"type=AVC msg=audit: avc:  denied  {{ {d['permission']} }} for  "
            f"comm=\"{d['comm']}\" "
            f"src={d['port']} "
            f"scontext={d['scontext']} "
            f"tcontext={d['tcontext']} "
            f"tclass={d['tclass']} permissive=0"
        )
    return "\n".join(lines)


@mcp.tool()
def firewall_cmd_state() -> str:
    """Check if firewalld is running (equivalent to 'firewall-cmd --state')."""
    return "running"


@mcp.tool()
def firewall_cmd_list_all() -> str:
    """List all firewall rules for the default zone (equivalent to 'firewall-cmd --list-all')."""
    return (
        "public (active)\n"
        "  target: default\n"
        "  icmp-block-inversion: no\n"
        "  interfaces: eth0\n"
        "  sources: \n"
        "  services: cockpit dhcpv6-client ssh\n"
        "  ports: 5432/tcp\n"
        "  protocols: \n"
        "  forward: yes\n"
        "  masquerade: no\n"
        "  forward-ports: \n"
        "  source-ports: \n"
        "  icmp-blocks: \n"
        "  rich rules: \n"
    )


@mcp.tool()
def firewall_cmd_query_port(port: str) -> str:
    """Check if a specific port is open in the firewall (e.g. '9090/tcp')."""
    open_ports = {"5432/tcp", "22/tcp"}
    if port in open_ports:
        return "yes"
    return "no"


@mcp.tool()
def semanage_port_list(port_type: Optional[str] = None) -> str:
    """List SELinux port type assignments (equivalent to 'semanage port -l')."""
    entries = [
        ("http_port_t", "tcp", "80, 81, 443, 488, 8008, 8009, 8443, 9000"),
        ("ssh_port_t", "tcp", "22"),
        ("postgresql_port_t", "tcp", "5432"),
        ("unreserved_port_t", "tcp", "1024-32767"),
        ("unreserved_port_t", "udp", "1024-32767"),
    ]
    if port_type:
        entries = [(t, p, ports) for t, p, ports in entries if t == port_type]

    lines = ["SELinux Port Type          Proto    Port Number"]
    for t, p, ports in entries:
        lines.append(f"{t:<26s} {p:<8s} {ports}")
    return "\n".join(lines)


@mcp.tool()
def system_info() -> str:
    """Get basic system information (hostname, OS, kernel, uptime)."""
    return json.dumps({
        "hostname": HOST,
        "os": f"Red Hat Enterprise Linux {RHEL_VER}",
        "kernel": "5.14.0-362.el9.x86_64",
        "arch": "x86_64",
        "uptime": "15 days, 3:42",
        "load_average": "0.45, 0.38, 0.32",
        "memory": {
            "total": "16384 MB",
            "used": "5120 MB",
            "free": "8192 MB",
            "available": "11264 MB",
        },
        "disk": {
            "/": {"total": "50G", "used": "18G", "available": "32G", "use_percent": "36%"},
            "/var": {"total": "100G", "used": "45G", "available": "55G", "use_percent": "45%"},
        },
    }, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")

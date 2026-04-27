#!/usr/bin/env python3
"""
Mock RHEL Host MCP Server for rh-developer rhel-deploy benchmark task.

Simulates a RHEL 9.3 host with Podman 4.9.4 for container deployment planning.
Scenario: Deploy a Flask app container as a systemd service on port 8080.
"""

from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("rhel-host")

# Mock state
MOCK_SYSTEM_INFO = {
    "os": "Red Hat Enterprise Linux 9.3 (Plow)",
    "kernel": "5.14.0-362.18.1.el9_3.x86_64",
    "architecture": "x86_64",
    "podman_version": "podman version 4.9.4",
    "selinux": "Enforcing",
    "firewall": "running",
}

MOCK_OPEN_PORTS = {8080}  # Port 8080 opened for Flask app
MOCK_SERVICES = {
    "flask-app": {
        "name": "flask-app",
        "active": "active",
        "state": "running",
        "enabled": True,
        "description": "Flask application container",
    },
    "container-flask-app": {
        "name": "container-flask-app",
        "active": "active",
        "state": "running",
        "enabled": True,
        "description": "Podman container flask-app.service",
    },
}

MOCK_PODMAN_PS = """CONTAINER ID  IMAGE                              COMMAND     CREATED     STATUS         PORTS                   NAMES
a1b2c3d4e5f6  quay.io/ubi9/python-311:latest  flask run   2 hours ago  Up 2 hours ago  0.0.0.0:8080->8080/tcp  flask-app
"""

MOCK_PODMAN_INSPECT = """[
    {
        "Id": "a1b2c3d4e5f6",
        "Name": "flask-app",
        "State": {
            "Status": "running",
            "Running": true
        },
        "Config": {
            "Image": "quay.io/ubi9/python-311:latest",
            "Cmd": ["flask", "run", "--host=0.0.0.0", "--port=8080"]
        },
        "HostConfig": {
            "PortBindings": {
                "8080/tcp": [{"HostPort": "8080"}]
            }
        }
    }
]
"""


def _match_command(cmd: str) -> Optional[str]:
    """Return a command category for pattern matching."""
    cmd_lower = cmd.strip().lower()
    if "podman pull" in cmd_lower:
        return "podman_pull"
    if "podman run" in cmd_lower:
        return "podman_run"
    if "podman ps" in cmd_lower or cmd_lower == "podman ps":
        return "podman_ps"
    if "podman inspect" in cmd_lower:
        return "podman_inspect"
    if "systemctl enable" in cmd_lower:
        return "systemctl_enable"
    if "systemctl start" in cmd_lower:
        return "systemctl_start"
    if "systemctl status" in cmd_lower:
        return "systemctl_status"
    if "firewall-cmd" in cmd_lower:
        return "firewall_cmd"
    if "semanage fcontext" in cmd_lower:
        return "semanage_fcontext"
    if "restorecon" in cmd_lower:
        return "restorecon"
    return None


@mcp.tool
def run_command(command: str) -> dict:
    """Simulate running a shell command on a RHEL host.

    Supports common deployment patterns: podman, systemctl, firewall-cmd, semanage.
    Returns realistic output for supported commands; error for unknown commands.

    Args:
        command: The shell command to execute (e.g. 'podman ps', 'systemctl status flask-app').
    """
    kind = _match_command(command)
    if kind == "podman_pull":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": "Trying to pull quay.io/ubi9/python-311:latest...\nGetting image source signatures\nCopying blob sha256:...\nCopying config sha256:...\nWriting manifest to image destination\nStoring signatures\n",
            "stderr": "",
        }
    if kind == "podman_run":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": "a1b2c3d4e5f6",
            "stderr": "",
        }
    if kind == "podman_ps":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": MOCK_PODMAN_PS,
            "stderr": "",
        }
    if kind == "podman_inspect":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": MOCK_PODMAN_INSPECT,
            "stderr": "",
        }
    if kind == "systemctl_enable":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
        }
    if kind == "systemctl_start":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
        }
    if kind == "systemctl_status":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": """● flask-app.service - Flask application container
   Loaded: loaded (/etc/systemd/system/flask-app.service; enabled)
   Active: active (running) since Tue 2026-03-17 10:00:00 UTC; 2h ago
 Main PID: 1234 (conmon)
    Tasks: 8
   Memory: 128.0M
   CGroup: /system.slice/flask-app.service
""",
            "stderr": "",
        }
    if kind == "firewall_cmd":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": "success\n",
            "stderr": "",
        }
    if kind == "semanage_fcontext":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
        }
    if kind == "restorecon":
        return {
            "command": command,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
        }
    return {
        "command": command,
        "exit_code": 1,
        "stdout": "",
        "stderr": f"Error: Unknown or unsupported command. Supported: podman pull/run/ps/inspect, systemctl enable/start/status, firewall-cmd, semanage fcontext, restorecon.",
    }


@mcp.tool
def get_system_info() -> dict:
    """Return RHEL version, architecture, and Podman version for the target host."""
    return MOCK_SYSTEM_INFO.copy()


@mcp.tool
def check_service(name: str) -> dict:
    """Return systemd service status for a given service name.

    Args:
        name: Service name (e.g. 'flask-app', 'container-flask-app').
    """
    svc = MOCK_SERVICES.get(name)
    if svc:
        return {"service": name, "status": svc, "found": True}
    return {
        "service": name,
        "found": False,
        "error": f"Service '{name}' not found. Known services: {list(MOCK_SERVICES.keys())}",
    }


@mcp.tool
def check_port(port: int) -> dict:
    """Return whether a port is open in the firewall.

    Args:
        port: Port number to check (e.g. 8080).
    """
    open_port = port in MOCK_OPEN_PORTS
    return {
        "port": port,
        "open": open_port,
        "message": f"Port {port} is {'open' if open_port else 'closed'} in firewall.",
    }


if __name__ == "__main__":
    mcp.run()

#!/usr/bin/env python3
"""Mock Podman MCP Server for container debugging evaluation.

Simulates a local Podman environment with several containers, including
one that is crashing (OOMKilled) and one that has an entrypoint error.

Scenario:
  - myapp-web: Exited (137) - OOMKilled, memory limit 256m too low
  - myapp-worker: Exited (1) - missing Python dependency 'celery'
  - nginx-proxy: Running, healthy
  - postgres-db: Running, healthy
"""

import json
from typing import Optional

from fastmcp import FastMCP

mcp = FastMCP("podman")

NOW = "2026-03-02T12:00:00Z"

CONTAINERS = {
    "a1b2c3d4e5f6": {
        "Id": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
        "Names": ["myapp-web"],
        "Image": "myapp:latest",
        "ImageID": "sha256:abc123def456789012345678901234567890abcdef1234567890abcdef123456",
        "Created": "2026-03-01T10:00:00Z",
        "State": {
            "Status": "exited",
            "Running": False,
            "Paused": False,
            "Restarting": False,
            "OOMKilled": True,
            "Dead": False,
            "Pid": 0,
            "ExitCode": 137,
            "Error": "",
            "StartedAt": "2026-03-01T10:00:05Z",
            "FinishedAt": "2026-03-02T08:45:12Z",
        },
        "Config": {
            "Entrypoint": ["python3"],
            "Cmd": ["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"],
            "WorkingDir": "/app",
            "User": "1001",
            "Env": [
                "APP_ENV=production",
                "DATABASE_URL=postgresql://db:5432/myapp",
                "WORKERS=4",
                "MAX_REQUESTS=1000",
            ],
            "ExposedPorts": {"8080/tcp": {}},
        },
        "HostConfig": {
            "Memory": 268435456,
            "MemorySwap": 268435456,
            "CpuQuota": 100000,
            "CpuPeriod": 100000,
            "PortBindings": {"8080/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]},
            "Binds": ["/data/myapp:/app/data:rw"],
        },
        "Mounts": [
            {"Type": "bind", "Source": "/data/myapp", "Destination": "/app/data", "Mode": "rw"},
        ],
    },
    "b2c3d4e5f6a7": {
        "Id": "b2c3d4e5f6a7890123456789abcdef1234567890abcdef1234567890abcdef12",
        "Names": ["myapp-worker"],
        "Image": "myapp:latest",
        "ImageID": "sha256:abc123def456789012345678901234567890abcdef1234567890abcdef123456",
        "Created": "2026-03-01T10:00:00Z",
        "State": {
            "Status": "exited",
            "Running": False,
            "Paused": False,
            "Restarting": False,
            "OOMKilled": False,
            "Dead": False,
            "Pid": 0,
            "ExitCode": 1,
            "Error": "",
            "StartedAt": "2026-03-01T10:00:08Z",
            "FinishedAt": "2026-03-01T10:00:12Z",
        },
        "Config": {
            "Entrypoint": ["python3"],
            "Cmd": ["-m", "celery", "-A", "tasks", "worker", "--loglevel=info"],
            "WorkingDir": "/app",
            "User": "1001",
            "Env": [
                "APP_ENV=production",
                "DATABASE_URL=postgresql://db:5432/myapp",
                "CELERY_BROKER_URL=redis://redis:6379/0",
            ],
        },
        "HostConfig": {
            "Memory": 536870912,
            "MemorySwap": 1073741824,
            "CpuQuota": 0,
            "CpuPeriod": 0,
        },
        "Mounts": [],
    },
    "c3d4e5f6a7b8": {
        "Id": "c3d4e5f6a7b8901234567890abcdef1234567890abcdef1234567890abcdef12",
        "Names": ["nginx-proxy"],
        "Image": "nginx:1.25",
        "ImageID": "sha256:def456789012345678901234567890abcdef1234567890abcdef1234567890ab",
        "Created": "2026-02-28T08:00:00Z",
        "State": {
            "Status": "running",
            "Running": True,
            "Paused": False,
            "Restarting": False,
            "OOMKilled": False,
            "Dead": False,
            "Pid": 12345,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2026-02-28T08:00:05Z",
            "FinishedAt": "0001-01-01T00:00:00Z",
        },
        "Config": {
            "Entrypoint": ["/docker-entrypoint.sh"],
            "Cmd": ["nginx", "-g", "daemon off;"],
            "WorkingDir": "",
            "User": "",
            "Env": ["NGINX_PORT=80"],
            "ExposedPorts": {"80/tcp": {}, "443/tcp": {}},
        },
        "HostConfig": {
            "Memory": 0,
            "MemorySwap": 0,
            "CpuQuota": 0,
            "CpuPeriod": 0,
            "PortBindings": {
                "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "80"}],
                "443/tcp": [{"HostIp": "0.0.0.0", "HostPort": "443"}],
            },
        },
        "Mounts": [
            {"Type": "bind", "Source": "/etc/nginx/conf.d", "Destination": "/etc/nginx/conf.d", "Mode": "ro"},
        ],
    },
    "d4e5f6a7b8c9": {
        "Id": "d4e5f6a7b8c9012345678901abcdef1234567890abcdef1234567890abcdef12",
        "Names": ["postgres-db"],
        "Image": "postgres:15",
        "ImageID": "sha256:789012345678901234567890abcdef1234567890abcdef1234567890abcdef12",
        "Created": "2026-02-25T12:00:00Z",
        "State": {
            "Status": "running",
            "Running": True,
            "Paused": False,
            "Restarting": False,
            "OOMKilled": False,
            "Dead": False,
            "Pid": 23456,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2026-02-25T12:00:10Z",
            "FinishedAt": "0001-01-01T00:00:00Z",
        },
        "Config": {
            "Entrypoint": ["docker-entrypoint.sh"],
            "Cmd": ["postgres"],
            "WorkingDir": "",
            "User": "postgres",
            "Env": [
                "POSTGRES_DB=myapp",
                "POSTGRES_USER=app",
                "PGDATA=/var/lib/postgresql/data",
            ],
            "ExposedPorts": {"5432/tcp": {}},
        },
        "HostConfig": {
            "Memory": 1073741824,
            "MemorySwap": 2147483648,
            "CpuQuota": 0,
            "CpuPeriod": 0,
            "PortBindings": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "5432"}]},
        },
        "Mounts": [
            {"Type": "volume", "Source": "pgdata", "Destination": "/var/lib/postgresql/data", "Mode": "rw"},
        ],
    },
}

LOGS = {
    "myapp-web": (
        "INFO:     Started server process [1]\n"
        "INFO:     Waiting for application startup.\n"
        "INFO:     Application startup complete.\n"
        "INFO:     Uvicorn running on http://0.0.0.0:8080\n"
        "INFO:     Loading ML model into memory...\n"
        "INFO:     Model size: 1.2GB\n"
        "WARNING:  Memory usage at 89% of limit (237MB/256MB)\n"
        "INFO:     Processing request batch (32 items)\n"
        "WARNING:  Memory usage at 95% of limit (248MB/256MB)\n"
        "WARNING:  Memory pressure detected, attempting GC\n"
        "INFO:     GC freed 12MB, usage now at 92%\n"
        "INFO:     Processing request batch (64 items)\n"
        "CRITICAL: Memory usage exceeded limit\n"
        "Killed\n"
    ),
    "myapp-worker": (
        "Traceback (most recent call last):\n"
        '  File "/usr/lib/python3.11/runpy.py", line 198, in _run_module_as_main\n'
        '    return _run_code(code, main_globals, None,\n'
        '  File "/usr/lib/python3.11/runpy.py", line 88, in _run_code\n'
        '    exec(code, run_globals)\n'
        "ModuleNotFoundError: No module named 'celery'\n"
    ),
    "nginx-proxy": (
        "2026/02/28 08:00:05 [notice] 1#1: nginx/1.25.4\n"
        "2026/02/28 08:00:05 [notice] 1#1: built by gcc 12.2.0\n"
        "2026/02/28 08:00:05 [notice] 1#1: OS: Linux 5.14.0-362.el9.x86_64\n"
        "2026/02/28 08:00:05 [notice] 1#1: start worker processes\n"
        "2026/02/28 08:00:05 [notice] 1#1: start worker process 29\n"
        "2026/02/28 08:00:05 [notice] 1#1: start worker process 30\n"
    ),
    "postgres-db": (
        "PostgreSQL init process complete; ready for start up.\n"
        '2026-02-25 12:00:10.123 UTC [1] LOG:  starting PostgreSQL 15.5\n'
        '2026-02-25 12:00:10.456 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432\n'
        '2026-02-25 12:00:10.789 UTC [1] LOG:  database system is ready to accept connections\n'
    ),
}

IMAGES = [
    {
        "Id": "sha256:abc123def456789012345678901234567890abcdef1234567890abcdef123456",
        "RepoTags": ["myapp:latest"],
        "Created": "2026-02-28T15:30:00Z",
        "Size": 1345678901,
        "VirtualSize": 1345678901,
        "Labels": {"maintainer": "dev@myapp.io", "version": "2.1.0"},
        "Config": {
            "Entrypoint": ["python3"],
            "Cmd": ["-m", "uvicorn", "main:app"],
            "WorkingDir": "/app",
            "ExposedPorts": {"8080/tcp": {}},
            "Env": ["PYTHONDONTWRITEBYTECODE=1", "PYTHONUNBUFFERED=1"],
        },
    },
    {
        "Id": "sha256:def456789012345678901234567890abcdef1234567890abcdef1234567890ab",
        "RepoTags": ["nginx:1.25"],
        "Created": "2026-01-15T10:00:00Z",
        "Size": 187654321,
        "VirtualSize": 187654321,
        "Labels": {"maintainer": "NGINX Docker Maintainers"},
        "Config": {
            "Entrypoint": ["/docker-entrypoint.sh"],
            "Cmd": ["nginx", "-g", "daemon off;"],
            "ExposedPorts": {"80/tcp": {}},
        },
    },
    {
        "Id": "sha256:789012345678901234567890abcdef1234567890abcdef1234567890abcdef12",
        "RepoTags": ["postgres:15"],
        "Created": "2026-01-20T12:00:00Z",
        "Size": 412345678,
        "VirtualSize": 412345678,
        "Labels": {"maintainer": "PostgreSQL Docker Maintainers"},
        "Config": {
            "Entrypoint": ["docker-entrypoint.sh"],
            "Cmd": ["postgres"],
            "ExposedPorts": {"5432/tcp": {}},
        },
    },
]


def _find_container(name_or_id: str):
    for cid, c in CONTAINERS.items():
        if name_or_id in (cid, c["Id"]):
            return c
        if name_or_id in c["Names"]:
            return c
    return None


@mcp.tool()
def container_list(all: bool = True) -> str:
    """List containers. Set all=True to include stopped containers."""
    results = []
    for cid, c in CONTAINERS.items():
        if not all and not c["State"]["Running"]:
            continue
        status = c["State"]["Status"]
        if c["State"]["OOMKilled"]:
            status = f"Exited (137) OOMKilled"
        elif c["State"]["ExitCode"] != 0 and not c["State"]["Running"]:
            status = f"Exited ({c['State']['ExitCode']})"
        elif c["State"]["Running"]:
            status = "Up 2 days"
        results.append({
            "Id": cid,
            "Names": c["Names"],
            "Image": c["Image"],
            "Status": status,
            "Created": c["Created"],
            "Ports": list(c["Config"].get("ExposedPorts", {}).keys()),
        })
    return json.dumps(results, indent=2)


@mcp.tool()
def container_inspect(name: str) -> str:
    """Inspect a container by name or ID. Returns detailed configuration and state."""
    c = _find_container(name)
    if not c:
        raise ValueError(f"no container with name or ID \"{name}\": no such container")
    return json.dumps(c, indent=2)


@mcp.tool()
def container_logs(name: str, tail: int = 100) -> str:
    """Get logs from a container by name or ID."""
    c = _find_container(name)
    if not c:
        raise ValueError(f"no container with name or ID \"{name}\": no such container")
    cname = c["Names"][0]
    log = LOGS.get(cname, f"No logs available for {cname}")
    return log


@mcp.tool()
def container_stats(name: Optional[str] = None) -> str:
    """Get resource usage statistics for running containers."""
    results = []
    for cid, c in CONTAINERS.items():
        if name and name not in c["Names"] and name != cid:
            continue
        if not c["State"]["Running"]:
            continue
        mem_limit = c["HostConfig"]["Memory"] or 8589934592
        results.append({
            "Id": cid,
            "Name": c["Names"][0],
            "CPUPerc": "12.5%",
            "MemUsage": f"{mem_limit // 4} / {mem_limit}",
            "MemPerc": "25.0%",
            "NetIO": "1.2MB / 500KB",
            "BlockIO": "50MB / 10MB",
            "PIDs": 15,
        })
    if not results:
        return "No running containers found" + (f" matching '{name}'" if name else "")
    return json.dumps(results, indent=2)


@mcp.tool()
def container_top(name: str) -> str:
    """Display the running processes of a container."""
    c = _find_container(name)
    if not c:
        raise ValueError(f"no container with name or ID \"{name}\": no such container")
    if not c["State"]["Running"]:
        raise ValueError(f"container {c['Names'][0]} is not running")
    return (
        "UID        PID   PPID  C STIME TTY          TIME CMD\n"
        f"1001     12345      1  0 08:00 ?        00:05:00 {' '.join(c['Config'].get('Cmd', ['']))}\n"
    )


@mcp.tool()
def image_list() -> str:
    """List all container images."""
    results = []
    for img in IMAGES:
        size_mb = img["Size"] // (1024 * 1024)
        results.append({
            "Id": img["Id"][:19],
            "RepoTags": img["RepoTags"],
            "Created": img["Created"],
            "Size": f"{size_mb}MB",
            "Labels": img.get("Labels", {}),
        })
    return json.dumps(results, indent=2)


@mcp.tool()
def image_inspect(name: str) -> str:
    """Inspect a container image by name or ID."""
    for img in IMAGES:
        if name in img["RepoTags"] or name == img["Id"] or img["Id"].startswith(f"sha256:{name}"):
            return json.dumps(img, indent=2)
    raise ValueError(f"image \"{name}\" not found")


if __name__ == "__main__":
    mcp.run(transport="stdio")

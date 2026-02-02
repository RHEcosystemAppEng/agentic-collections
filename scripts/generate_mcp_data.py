#!/usr/bin/env python3
"""
Parse .mcp.json files and extract MCP server configurations.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

# List of agentic packs to parse
PACK_DIRS = ['rh-sre', 'rh-developer', 'ocp-admin', 'rh-support-engineer', 'rh-virt']


def extract_env_vars(env_dict: Dict[str, str]) -> List[str]:
    """
    Extract environment variable names from ${VAR} format.

    Args:
        env_dict: Dictionary of environment variable configurations

    Returns:
        List of environment variable names
    """
    env_vars = []

    for key, value in env_dict.items():
        # Check if value is in ${VAR} format
        if isinstance(value, str):
            match = re.match(r'^\$\{([A-Z_][A-Z0-9_]*)\}$', value)
            if match:
                # Extract the variable name
                env_vars.append(match.group(1))
            else:
                # If it's a literal value (not ${VAR}), use the key name
                env_vars.append(key)
        else:
            # For non-string values, use the key name
            env_vars.append(key)

    return sorted(set(env_vars))


def parse_mcp_file(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse .mcp.json file from a pack directory.

    Args:
        pack_dir: Name of the pack directory

    Returns:
        List of MCP server configurations
    """
    mcp_file = Path(pack_dir) / '.mcp.json'

    if not mcp_file.exists():
        return []

    try:
        with open(mcp_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        servers = []

        # Extract each MCP server
        for server_name, server_config in config.get('mcpServers', {}).items():
            server = {
                'name': server_name,
                'pack': pack_dir,
                'command': server_config.get('command', ''),
                'args': server_config.get('args', []),
                'env': extract_env_vars(server_config.get('env', {})),
                'description': server_config.get('description', ''),
                'security': server_config.get('security', {})
            }
            servers.append(server)

        return servers

    except Exception as e:
        print(f"Warning: Failed to parse {mcp_file}: {e}")
        return []


def generate_mcp_data() -> List[Dict[str, Any]]:
    """
    Generate MCP server data for all agentic packs.

    Returns:
        List of MCP server dictionaries
    """
    mcp_servers = []

    for pack_dir in PACK_DIRS:
        pack_path = Path(pack_dir)

        if not pack_path.exists():
            continue

        servers = parse_mcp_file(pack_dir)
        mcp_servers.extend(servers)

        if servers:
            print(f"✓ Parsed {pack_dir}: {len(servers)} MCP server(s)")

    return mcp_servers


if __name__ == '__main__':
    # Test the script
    print("Parsing MCP server configurations...")
    print()

    servers = generate_mcp_data()

    print()
    print(f"Found {len(servers)} MCP servers total")
    print()
    print("Summary:")
    for server in servers:
        print(f"  • {server['name']} (from {server['pack']})")
        print(f"    Command: {server['command']}")
        if server['env']:
            print(f"    Env vars: {', '.join(server['env'])}")
        print(f"    Security: {server['security'].get('isolation', 'N/A')}")
        print()

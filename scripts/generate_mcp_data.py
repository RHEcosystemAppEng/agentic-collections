#!/usr/bin/env python3
"""
Parse .mcp.json files and extract MCP server configurations.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

# List of agentic packs to parse
PACK_DIRS = ['rh-sre', 'rh-developer', 'ocp-admin', 'rh-support-engineer', 'rh-virt', 'rh-ai-engineer']


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


def extract_header_env_vars(headers: Dict[str, str]) -> List[str]:
    """
    Extract environment variable names from header values.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        List of environment variable names found in headers
    """
    env_vars = []
    for key, value in headers.items():
        if isinstance(value, str):
            # Extract ${VAR} patterns from header values
            matches = re.findall(r'\$\{([A-Z_][A-Z0-9_]*)\}', value)
            env_vars.extend(matches)
    return env_vars


def parse_mcp_file(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse .mcp.json file from a pack directory.
    Supports both command-based and HTTP-based MCP servers.

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
            # Detect server type
            server_type = server_config.get('type', 'command')

            # Base server configuration
            server = {
                'name': server_name,
                'pack': pack_dir,
                'type': server_type,
                'description': server_config.get('description', ''),
                'security': server_config.get('security', {})
            }

            # Extract type-specific fields
            if server_type == 'http':
                # HTTP-based remote server
                server['url'] = server_config.get('url', '')
                server['headers'] = server_config.get('headers', {})

                # Extract env vars from both env dict and headers
                env_vars = extract_env_vars(server_config.get('env', {}))
                header_env_vars = extract_header_env_vars(server_config.get('headers', {}))
                server['env'] = sorted(set(env_vars + header_env_vars))

                # Command and args are not applicable for HTTP servers
                server['command'] = ''
                server['args'] = []
            else:
                # Command-based server (default)
                server['command'] = server_config.get('command', '')
                server['args'] = server_config.get('args', [])
                server['env'] = extract_env_vars(server_config.get('env', {}))

                # URL and headers are not applicable for command servers
                server['url'] = ''
                server['headers'] = {}

            servers.append(server)

        return servers

    except Exception as e:
        print(f"Warning: Failed to parse {mcp_file}: {e}")
        return []


def load_custom_mcp_data() -> Dict[str, Any]:
    """
    Load custom MCP data from docs/mcp.json.

    Returns:
        Dictionary mapping server names to custom data (repository, tools)
    """
    custom_data_file = Path('docs/mcp.json')

    if not custom_data_file.exists():
        print("Warning: docs/mcp.json not found, skipping custom data")
        return {}

    try:
        with open(custom_data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load docs/mcp.json: {e}")
        return {}


def generate_mcp_data() -> List[Dict[str, Any]]:
    """
    Generate MCP server data for all agentic packs.
    Merges data from .mcp.json files with custom data from docs/mcp.json.

    Returns:
        List of MCP server dictionaries
    """
    mcp_servers = []

    # Load custom data (repository URLs and tool descriptions)
    custom_data = load_custom_mcp_data()

    for pack_dir in PACK_DIRS:
        pack_path = Path(pack_dir)

        if not pack_path.exists():
            continue

        servers = parse_mcp_file(pack_dir)

        # Merge custom data for each server
        for server in servers:
            server_name = server['name']
            if server_name in custom_data:
                # Add custom metadata from docs/mcp.json
                server['repository'] = custom_data[server_name].get('repository', '')
                server['tools'] = custom_data[server_name].get('tools', [])
                server['title'] = custom_data[server_name].get('title', server_name)
                server['tier'] = custom_data[server_name].get('tier', 'Official')
                server['owner'] = custom_data[server_name].get('owner', 'Red Hat')
            else:
                # No custom data available - use defaults
                server['repository'] = ''
                server['tools'] = []
                server['title'] = server_name
                server['tier'] = 'Official'
                server['owner'] = 'Red Hat'

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
        print(f"    Type: {server['type']}")

        if server['type'] == 'http':
            print(f"    URL: {server['url']}")
            if server['headers']:
                print(f"    Headers: {', '.join(server['headers'].keys())}")
        else:
            print(f"    Command: {server['command']}")

        if server['env']:
            print(f"    Env vars: {', '.join(server['env'])}")

        if server['security']:
            print(f"    Security: {server['security'].get('isolation', 'N/A')}")
        print()

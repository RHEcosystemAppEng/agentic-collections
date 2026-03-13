# MCP Server Pack Configuration

Create the MCP server configuration file for an agentic pack that integrates with an external container-based service requiring authentication credentials. The configuration must follow secure credential handling practices and include metadata about the server's security posture.

## Capabilities

### Secure credential handling

The MCP server configuration uses environment variable references for all sensitive values rather than hardcoding credentials.

- A configuration entry with `"API_KEY": "${API_KEY}"` passes security validation; a configuration with `"API_KEY": "sk-abc123"` fails [@test](./tests/test_credential_security.md)
- All `env` values in the mcpServers block use the `${VARIABLE_NAME}` reference format [@test](./tests/test_env_var_format.md)

### Complete server entry structure

Each MCP server entry contains all required fields including command, args array, env object, description, and a security metadata block.

- A server entry specifying `"isolation": "container"`, `"network": "local"`, and `"credentials": "env-only"` is valid [@test](./tests/test_security_block.md)
- A server entry using `"command": "podman"` with a `run --rm -i` args array and `--env VARNAME` argument entries is a valid container-based server [@test](./tests/test_container_command.md)

## Implementation

[@generates](./.mcp.json)

## API

```json { #api }
{
  "mcpServers": {
    "<server-name>": {
      "command": "podman | docker | npx",
      "args": ["run", "--rm", "-i", "--env", "VAR_NAME", "<image>"],
      "env": {
        "VAR_NAME": "${VAR_NAME}"
      },
      "description": "<brief description>",
      "security": {
        "isolation": "container | process | none",
        "network": "local | internet | none",
        "credentials": "env-only | none"
      }
    }
  }
}
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing conventions for MCP server configuration, credential security standards, and pack structure for AI-native agentic packs targeting Red Hat platforms.

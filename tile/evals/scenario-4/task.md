# Skill Dependencies Declaration

Create the Dependencies section for a skill that invokes two other skills and uses one MCP server with two tools. The section must explicitly enumerate all runtime requirements so that consumers can understand what is needed before invoking the skill.

## Capabilities

### Required MCP servers subsection

The Dependencies section includes a subsection listing each required MCP server with a short description and optional setup link.

- A skill using an MCP server named `openshift-virtualization` lists it under "Required MCP Servers" with a description [@test](./tests/test_mcp_server_listed.md)
- Each MCP server entry includes a setup or documentation link [@test](./tests/test_mcp_server_link.md)

### Required MCP tools subsection

The Dependencies section includes a subsection listing each MCP tool by name, which server it comes from, and what it does, along with its key parameters.

- A tool entry includes the tool name, the server it belongs to (in parentheses), and a description of its purpose [@test](./tests/test_tool_entry_format.md)
- A tool entry specifies the key parameters the tool accepts [@test](./tests/test_tool_parameters.md)

### Related skills subsection

The Dependencies section lists other skills that this skill invokes or delegates to, with context on when each is used.

- Skills invoked by this skill are listed under "Related Skills" with a note on when they are called [@test](./tests/test_related_skills.md)

### Reference documentation subsection

The Dependencies section lists internal and official reference documents that are consulted during execution.

- Internal reference docs are listed with relative markdown links [@test](./tests/test_internal_docs.md)

## Implementation

[@generates](./skills/cluster-auditor/SKILL.md)

## API

```markdown { #api }
## Dependencies

### Required MCP Servers
- `<server-name>` - <description> ([setup guide](<url>))

### Required MCP Tools
- `<tool_name>` (from <server-name>) - <what it does>
  - Parameters: <param1>, <param2>

### Related Skills
- `<skill-name>` - <when/why this skill uses it>

### Reference Documentation
**Internal:** [doc-name.md](path/to/doc.md) - <purpose>
**Official:** [Title](https://docs.example.com/...)
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing Design Principle 4 (Dependencies Declaration) standards and skill structure conventions for AI-native agentic collection authoring.

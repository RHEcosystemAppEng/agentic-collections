# Skill with Document Consultation Steps

Create a skill workflow step that looks up scoring information from a reference document before making a determination. The step must follow the transparency pattern where the agent actually reads the reference file and then explicitly informs the user of the consultation before proceeding.

## Capabilities

### Document consultation declaration

The workflow step includes both an action to read the reference document and a statement to output to the user confirming the consultation.

- A workflow step with a "Document Consultation" block contains both an `Action` instruction to read a named file and an `Output to user` instruction quoting the consultation message [@test](./tests/test_consultation_both_parts.md)
- A workflow step that only claims "I consulted file.md" without an `Action` to read the file is flagged as transparency theater [@test](./tests/test_no_read_action.md)

### Correct consultation ordering

Document consultation occurs before any MCP tool invocation in the same workflow step.

- In a step with both document consultation and an MCP tool call, the `Document Consultation` block appears before the `MCP Tool` specification [@test](./tests/test_consultation_before_tool.md)
- A step labeled `CRITICAL: Document consultation MUST happen BEFORE tool invocation` correctly places consultation first [@test](./tests/test_critical_ordering.md)

## Implementation

[@generates](./skills/risk-classifier/SKILL.md)

## API

```markdown { #api }
### Step N: [Action Name]

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [reference-doc.md](path/to/reference-doc.md) using the Read tool to understand [topic]
2. **Output to user**: "I consulted [reference-doc.md](path/to/reference-doc.md) to understand [topic]."

**MCP Tool**: `tool_name` (from server-name)

**Parameters**:
- `param`: "value" (type, format details)

**Expected Output**: [description]
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing Design Principle 1 (Document Consultation Transparency) and skill workflow step structure standards for AI-native skill authoring.

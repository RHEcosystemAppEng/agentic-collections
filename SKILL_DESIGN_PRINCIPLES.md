# Design Principles for Skills and Agents

This document defines the design principles for creating skills and agents in agentic collections. It is referenced from [CLAUDE.md](CLAUDE.md). Validate compliance with `make validate-skill-design` (see [README.md](README.md#skill-design-validation)).

## 1. Document Consultation Transparency

When a skill or agent consults documentation (from `docs/` or skill/agent files), it **MUST**:
1. **Actually read the file** using the Read tool to load it into context
2. **Then declare** the consultation to the user

**CRITICAL**: Document consultation means READING the file, not just claiming to have read it.

**Required Implementation**:
```markdown
**Document Consultation** (REQUIRED):
1. **Action**: Read [filename.md](path/to/filename.md) using the Read tool to understand [specific topic]
2. **Output to user**: "I consulted [filename.md](path/to/filename.md) to understand [specific topic]."
```

**❌ WRONG - Transparency Theater** (just claims, no actual reading):
```markdown
**Document Consultation** (output to user):
```
I consulted [filename.md](path/to/filename.md) to understand [topic].
```
```

**✅ CORRECT - Actual Consultation** (reads first, then declares):
```markdown
**Document Consultation** (REQUIRED):
1. **Action**: Read [cvss-scoring.md](../../docs/references/cvss-scoring.md) using the Read tool to understand CVSS severity mapping
2. **Output to user**: "I consulted [cvss-scoring.md](../../docs/references/cvss-scoring.md) to understand CVSS severity mapping."
```

**Examples in execution**:
- Read `docs/references/cvss-scoring.md` → "I consulted [cvss-scoring.md](rh-sre/docs/references/cvss-scoring.md) to verify the CVSS severity mapping."
- Read `skills/playbook-generator/SKILL.md` → "I consulted [playbook-generator/SKILL.md](rh-sre/skills/playbook-generator/SKILL.md) to understand playbook generation parameters."

**Rationale**:
- **Substance**: Ensures AI actually enriches its context with domain knowledge
- **Transparency**: Users understand the AI's knowledge sources
- **Auditability**: The execution-summary skill can track actual Read tool calls

## 2. Precise Parameter Specification

Skills MUST specify **exact parameters** when instructing agents to use tools, ensuring first-attempt success.

**CRITICAL**: Document consultation must be specified BEFORE tool parameters to ensure it happens first.

**❌ Bad Example - Vague parameters**:
```
Use get_cve tool with the CVE ID
```

**❌ Bad Example - Wrong parameters**:
```
**MCP Tool**: get_cves

**Parameters**:
- severity: ["Critical", "Important"]
- sort_by: "cvss_score"
```
(Actual tool uses `impact: "7,6"` and `sort: "-cvss_score"`)

**✅ Good Example - Correct structure with document consultation first**:
```
**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [vulnerability-logic.md](../../docs/insights/vulnerability-logic.md) using the Read tool
2. **Output to user**: "I consulted [vulnerability-logic.md]..."

**MCP Tool**: `get_cves` or `vulnerability__get_cves` (from lightspeed-mcp)

**Parameters**:
- impact: "7,6" (string with comma-separated impact levels: 7=Important, 6=Moderate, 5=Low)
- sort: "-cvss_score" (use - prefix for descending; valid fields: "cvss_score", "public_date")
- limit: 20 (maximum number of CVEs to return)
```

**Rationale**:
- **Ordering**: Document consultation before parameters ensures it's executed first
- **Precision**: Exact parameter names and formats prevent tool errors
- **Examples**: Value examples (e.g., "7,6") show correct format
- **Determinism**: First-attempt success reduces wasted cycles

## 3. Skill Precedence and Conciseness

**Precedence Rule**: Skills > Tools (always invoke skills, not raw MCP tools)

**Conciseness Requirement**: Skill descriptions (loaded at agent start time) must be:
- **Under 500 tokens** for the YAML frontmatter description field
- **Focus on "when to use"** with 3-5 concrete examples
- **Defer implementation details** to the skill body (not frontmatter)

**Example**:
```yaml
---
name: cve-impact
description: |
  Analyze CVE impact across the fleet without immediate remediation.

  Use when:
  - "What are the most critical vulnerabilities?"
  - "Show CVEs affecting my systems"
  - "List high-severity CVEs"

  NOT for remediation actions (use remediator agent instead).
  model: inherit        # Root: Runtime configuration required before skill execution
  color: blue           # Root: UX - IDE sidebar/terminal theme
---
```

**Rationale**: Minimizes token usage at agent initialization while maintaining clarity.

### Root-Level Frontmatter (2026 Agentic Skills Standard)

Primary UI and runtime configuration fields belong at the **root level** of YAML frontmatter so the IDE or Agent Host can parse them without traversing nested blocks.

| Field Type | Location | Examples |
|------------|----------|----------|
| Runtime | Root | `model`, `allowed-tools` |
| UX/UI | Root | `color`, `icon`, `version` |
| Custom | `metadata` | `author`, `priority`, `compliance` |

**Standard Color Values** (Cursor, Claude Code):

| Color | Use Case |
|-------|----------|
| blue, cyan | Analysis, read-only |
| green | Success, deployment |
| yellow | Caution, validation |
| red | Critical, security, remediation |
| magenta | Creative, generation |

## 4. Dependencies Declaration

Every skill MUST include a **Dependencies** section listing:
- **Skills**: Other skills this skill may invoke
- **MCP Tools**: Specific tools from MCP servers
- **MCP Servers**: Required MCP server names
- **Documentation**: Reference docs for context

**Required Format**:
```markdown
## Dependencies

### Required MCP Servers
- `lightspeed-mcp` - Red Hat Lightspeed platform access

### Required MCP Tools
- `vulnerability__get_cves` (from lightspeed-mcp) - List CVEs
- `vulnerability__get_cve` (from lightspeed-mcp) - Get CVE details

### Related Skills
- `cve-validation` - Validate CVEs before impact analysis
- `fleet-inventory` - Identify affected systems

### Reference Documentation
- [cvss-scoring.md](docs/references/cvss-scoring.md) - CVSS severity mappings
- [insights-api.md](docs/insights/insights-api.md) - API usage patterns
```

**Rationale**: Makes dependencies explicit for debugging and ensures proper error handling.

## 5. Human-in-the-Loop Requirements

Skills performing **critical operations** MUST include this section:

**Required Section**:
```markdown
## Critical: Human-in-the-Loop Requirements

This skill requires explicit user confirmation at the following steps:

1. **Before Tool Invocation** [if applicable]
   - Ask: "Should I proceed with [specific action]?"
   - Wait for user confirmation

2. **Before Destructive Actions** [if applicable]
   - Display preview of changes
   - Ask: "Review the changes above. Should I execute this?"
   - Wait for explicit "yes" or "proceed"

3. **After Each Major Step** [if applicable]
   - Report results
   - Ask: "Continue to next step?"

**Never assume approval** - always wait for explicit user confirmation.
```

**When to Use**:
- Playbook execution (ansible-mcp-server)
- System modifications (package updates, config changes)
- Multi-system operations (batch remediation)
- Data deletion or irreversible actions

**Rationale**: Prevents unintended automation; maintains user control over critical operations.

## 6. Mandatory Skill Sections

Every skill MUST include these sections in order:

### Template Structure:

```markdown
---
name: skill-name
description: |
  [Concise when-to-use with 3-5 examples]
model: inherit|sonnet|haiku
color: red|blue|green|yellow|cyan|magenta
version: 1.0.0
metadata:
  author: "team-name"
  priority: "high"
---

# [Skill Name]

## Prerequisites

**Required MCP Servers**: `server-name` ([setup guide](link))
**Required MCP Tools**: `tool_name` (from server-name)
**Environment Variables**: `VAR_NAME` (if applicable)

**Verification**:
Before executing, verify MCP server availability:
1. Check `server-name` is configured in `.mcp.json`
2. Verify environment variables are set
3. If missing: Report to user with setup instructions

**Human Notification on Failure**:
If prerequisites are not met:
- ❌ "Cannot proceed: MCP server `server-name` is not available"
- 📋 "Setup required: [link to setup guide]"
- ❓ "How would you like to proceed? (setup now / skip / abort)"
- ⏸️ Wait for user decision

## When to Use This Skill

Use this skill when:
- [Specific scenario 1]
- [Specific scenario 2]
- [Specific scenario 3]

Do NOT use when:
- [Anti-pattern 1] → Use [alternative] instead
- [Anti-pattern 2] → Use [alternative] instead

## Workflow

### Step 1: [Action Name]

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [doc.md](../../docs/category/doc.md) using the Read tool to understand [specific topic]
2. **Output to user**: "I consulted [doc.md](../../docs/category/doc.md) to understand [specific topic]."

**MCP Tool**: `tool_name` or `toolset__tool_name` (from server-name)

**Parameters**:
- `param1`: [exact specification with example - see Design Principle #2]
  - Example: `"CVE-2024-1234"`
- `param2`: [exact specification with example]
  - Example: `true` (description of what this does)

**Expected Output**: [describe what the tool returns]

**Error Handling**:
- If [error condition]: [how to handle]

### Step 2: [Next Action]

[Continue pattern...]

## Dependencies

[As specified in principle #4]

## Critical: Human-in-the-Loop Requirements

[As specified in principle #5, if applicable]

## Example Usage

[Concrete example with user query and skill response]
```

**Rationale**: Standardizes skill structure for consistency and completeness.

## 7. MCP Server Availability Verification

The **Prerequisites** section MUST include verification logic:

**CRITICAL SECURITY CONSTRAINT**:
- **NEVER print environment variable values in user-visible output**
- When checking if env vars are set, only report presence/absence
- Do NOT use `echo $VAR_NAME` or display actual credential values
- Protect sensitive data like API keys, tokens, secrets, passwords

**❌ WRONG - Exposes credentials**:
```bash
echo $LIGHTSPEED_CLIENT_SECRET  # Shows actual secret value
```

**✅ CORRECT - Check without exposing**:
```bash
# Check if set (exit code only, no output)
test -n "$LIGHTSPEED_CLIENT_SECRET"

# Or check and report boolean result
if [ -n "$LIGHTSPEED_CLIENT_SECRET" ]; then
    echo "✓ LIGHTSPEED_CLIENT_SECRET is set"
else
    echo "✗ LIGHTSPEED_CLIENT_SECRET is not set"
fi
```

**In User-Visible Messages**:
```
✓ Environment variable LIGHTSPEED_CLIENT_ID is set
✓ Environment variable LIGHTSPEED_CLIENT_SECRET is set
```

**NEVER show**:
```
LIGHTSPEED_CLIENT_SECRET=sk-abc123-xyz789-...  ❌ SECURITY VIOLATION
```

**Rationale**: Prevents accidental credential exposure in conversation history, logs, or screenshots.

---

**Required Pattern**:
```markdown
## Prerequisites

**Required MCP Servers**: `lightspeed-mcp` ([setup guide](https://console.redhat.com/))
**Required MCP Tools**:
- `vulnerability__get_cves`
- `vulnerability__get_cve`

**Verification Steps**:
1. **Check MCP Server Configuration**
   - Verify `lightspeed-mcp` exists in `.mcp.json`
   - If missing → Proceed to Human Notification

2. **Check Environment Variables**
   - Verify `LIGHTSPEED_CLIENT_ID` is set
   - Verify `LIGHTSPEED_CLIENT_SECRET` is set
   - If missing → Proceed to Human Notification

3. **Test MCP Server Connection** (optional, for critical skills)
   - Attempt simple tool call (e.g., `get_mcp_version`)
   - If fails → Proceed to Human Notification

**Human Notification Protocol**:

When prerequisites fail, the skill MUST:

1. **Stop Execution Immediately** - Do not attempt tool calls
2. **Report Clear Error**:
   ```
   ❌ Cannot execute [skill-name]: MCP server `lightspeed-mcp` is not available

   📋 Setup Instructions:
   1. Add lightspeed-mcp to `.mcp.json` (see: [setup guide])
   2. Set environment variables:
      export LIGHTSPEED_CLIENT_ID="your-id"
      export LIGHTSPEED_CLIENT_SECRET="your-secret"
   3. Restart Claude Code to reload MCP servers

   🔗 Documentation: [link to MCP server docs]
   ```

3. **Request User Decision**:
   ```
   ❓ How would you like to proceed?

   Options:
   - "setup" - I'll help you configure the MCP server now
   - "skip" - Skip this skill and continue with alternative approach
   - "abort" - Stop the workflow entirely

   Please respond with your choice.
   ```

4. **Wait for Explicit User Input** - Do not proceed automatically

**Error Message Templates**:

- Missing MCP Server:
  ```
  ❌ MCP server `{server_name}` not configured in .mcp.json
  📋 Add server configuration: [setup guide link]
  ```

- Missing Environment Variable:
  ```
  ❌ Environment variable `{VAR_NAME}` not set
  📋 Set variable: export {VAR_NAME}="your-value"

  ⚠️ SECURITY: Never expose actual values in output or logs
  ```

- Connection Failure:
  ```
  ❌ Cannot connect to `{server_name}` MCP server
  📋 Possible causes:
     - Container not running (run: podman ps)
     - Network issues (check: podman logs)
     - Invalid credentials (verify env vars)
  ```
```

**Rationale**: Provides graceful degradation and clear user guidance when dependencies are missing.

## Skill File Format

Skills MUST follow the structure defined in **Design Principle #6** above. Here's a minimal template:

```yaml
---
name: skill-name
description: |
  [Concise when-to-use with 3-5 examples - under 500 tokens]
model: inherit|sonnet|haiku
color: red|blue|green|yellow|cyan|magenta
version: 1.0.0
metadata:
  author: "team-name"
  priority: "high"
---

# [Skill Name]

## Prerequisites
[As defined in Design Principle #7 - with verification and human notification]

## When to Use This Skill
[Clear use cases and anti-patterns]

## Workflow
### Step 1: [Action]

**CRITICAL**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [doc.md](path/to/doc.md) using the Read tool to understand [topic]
2. **Output to user**: "I consulted [doc.md](path/to/doc.md) to understand [topic]."

**MCP Tool**: `tool_name` or `toolset__tool_name` (from server-name)

**Parameters**:
- param1: "value" (exact format with example - Design Principle #2)
- param2: true (description of what this does)

[Implementation details]

## Dependencies
[As defined in Design Principle #4]

## Critical: Human-in-the-Loop Requirements
[If applicable - Design Principle #5]
```

**Important**: See this document for complete requirements and rationale.

## Agent File Format

Agents MUST follow similar principles as skills, with focus on skill orchestration:

```yaml
---
name: agent-name
description: |
  When to use this agent vs skills
  [Concise with 3-5 examples - under 500 tokens]
model: inherit
color: red
version: 1.0.0
metadata:
  author: "team-name"
tools: ["All"]
---

# [Agent Name]

## Prerequisites
[MCP servers and skills this agent depends on - Design Principle #7]

## When to Use This Agent
[Multi-step workflows requiring orchestration]

## Workflow

### 1. Step Name
**Invoke the skill-name skill**:
```
Skill: skill-name
Args: [Precise parameters - Design Principle #2]
```

**Document Consultation** (if needed):
I consulted [filename.md](path/to/filename.md) to understand [topic].
[Design Principle #1]

**Human Confirmation** (if critical):
Ask: "Should I proceed with [action]?"
Wait for confirmation.
[Design Principle #5]

### 2. Next Step
[Continue orchestration pattern...]

## Dependencies
[Skills, tools, docs this agent uses - Design Principle #4]

## Critical: Human-in-the-Loop Requirements
[For agents performing critical operations - Design Principle #5]
```

**Important**: Agents inherit the same design principles as skills. See this document for complete requirements.

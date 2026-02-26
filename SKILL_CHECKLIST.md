# Skill Quality Checklist

**Universal requirements for all skills across all agentic collections.**

This checklist is organized in two tiers:
- **Tier 1: agentskills.io specification** (Sections 0-9) - MANDATORY for all skills
- **Tier 2: CLAUDE.md enhancements** (Sections 10-36) - Additional requirements

**References:**
- [agentskills.io specification](https://agentskills.io/specification) - Base format specification
- [CLAUDE.md](./CLAUDE.md) - Repository architecture and patterns

---

# TIER 1: agentskills.io Specification

## Section 0: Directory Structure

- [ ] Skill is in a directory (e.g., `skills/skill-name/`)
- [ ] Directory contains `SKILL.md` file (uppercase filename)
- [ ] Directory name matches `name` field in frontmatter exactly

**Valid structure:**
```
skills/pdf-processing/
└── SKILL.md
```

**Optional directories (agentskills.io):**
```
skills/pdf-processing/
├── SKILL.md
├── scripts/         # Executable code (Python, Bash, JavaScript)
├── references/      # Additional documentation files
└── assets/          # Templates, images, data files
```

---

## Section 1: Name Field (agentskills.io)

- [ ] `name` field present
- [ ] Name is 1-64 characters
- [ ] Name uses only lowercase letters, numbers, and hyphens (`a-z0-9-`)
- [ ] Name does not start or end with hyphen
- [ ] Name does not have consecutive hyphens (`--`)
- [ ] Name matches parent directory name exactly

**✅ Valid examples:**
```yaml
name: pdf-processing
name: data-analysis
name: vm-create
```

**❌ Invalid examples:**
```yaml
name: PDF-Processing    # Uppercase not allowed
name: -pdf              # Cannot start with hyphen
name: pdf--processing   # Consecutive hyphens not allowed
name: pdf_processing    # Underscores not allowed
```

---

## Section 2: Description Field (agentskills.io)

- [ ] `description` field present
- [ ] Description is 1-1024 characters
- [ ] Description describes what the skill does and when to use it
- [ ] Description includes specific keywords for agent discovery

**✅ Good example:**
```yaml
description: |
  Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs.
  Use when working with PDF documents or when the user mentions PDFs, forms, or
  document extraction.
```

**❌ Poor example:**
```yaml
description: Helps with PDFs.  # Too vague, no when-to-use guidance
```

---

## Section 3: License Field (agentskills.io)

- [ ] `license` field is optional
- [ ] If present, contains license name or reference to bundled license file
- [ ] If present, is kept short (recommended)

**Examples:**
```yaml
license: Apache-2.0
license: MIT
license: Proprietary. LICENSE.txt has complete terms
```

---

## Section 4: Compatibility Field (agentskills.io)

- [ ] `compatibility` field is optional
- [ ] If present, is 1-500 characters
- [ ] If present, indicates environment requirements
- [ ] Only included if skill has specific environment requirements

**Examples:**
```yaml
compatibility: Designed for Claude Code (or similar products)
compatibility: Requires git, docker, jq, and access to the internet
compatibility: Requires Python 3.8+, pip, and network access to PyPI
```

**Note:** Most skills do not need this field.

---

## Section 5: Metadata Field (agentskills.io)

- [ ] `metadata` field is optional
- [ ] If present, is a map from string keys to string values
- [ ] If present, keys are reasonably unique to avoid conflicts

**Example:**
```yaml
metadata:
  author: example-org
  version: "1.0"
  category: data-processing
```

---

## Section 6: Allowed-Tools Field (agentskills.io)

- [ ] `allowed-tools` field is optional (experimental)
- [ ] If present, is a space-delimited list of pre-approved tools

**Example:**
```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read Write
```

**Note:** Support for this field may vary between agent implementations.

---

## Section 7: YAML Frontmatter Format (agentskills.io)

- [ ] SKILL.md contains YAML frontmatter
- [ ] Frontmatter is delimited by `---` markers (opening and closing)
- [ ] Frontmatter appears at start of file
- [ ] Frontmatter contains required fields: `name` and `description`

**Correct format:**
```yaml
---
name: pdf-processing
description: |
  Extract text and tables from PDF files.
---

# PDF Processing Skill

[Rest of skill content]
```

**❌ Missing delimiters:**
```yaml
name: pdf-processing
description: PDF processing

# PDF Processing Skill
```

---

## Section 8: Body Content (agentskills.io)

- [ ] Markdown body follows frontmatter
- [ ] Body has no format restrictions (write what helps agents)
- [ ] Body includes step-by-step instructions (recommended)
- [ ] Body includes examples of inputs and outputs (recommended)
- [ ] Body includes common edge cases (recommended)

**Recommended body structure:**
```markdown
---
name: skill-name
description: |
  Skill description here
---

# Skill Name

## Overview
Brief description of what this skill does.

## Step-by-step Instructions
1. First, do this...
2. Then, do that...

## Examples
**Input:** Example input
**Output:** Example output

## Common Edge Cases
- Edge case 1: How to handle
- Edge case 2: How to handle
```

---

## Section 9: Progressive Disclosure (agentskills.io)

- [ ] Main `SKILL.md` is under 500 lines (recommended)
- [ ] Main `SKILL.md` is under 5000 tokens (recommended)
- [ ] Detailed reference material moved to separate files
- [ ] File references use relative paths from skill root
- [ ] File references kept one level deep (avoid nested chains)

**Progressive loading model:**
- **Metadata (~100 tokens):** `name` and `description` loaded at startup for all skills
- **Instructions (<5000 tokens):** Full `SKILL.md` loaded when skill is activated
- **Resources (as needed):** Files in `scripts/`, `references/`, `assets/` loaded only when required

**✅ Good file references:**
```markdown
See [the reference guide](references/REFERENCE.md) for details.
Run the extraction script: scripts/extract.py
Use template: assets/template.json
```

**❌ Deeply nested references:**
```markdown
See references/advanced/subsection/details.md  # Too deep
```

---

# TIER 2: CLAUDE.md Enhancements

## Section 10: Description Field - CLAUDE.md Enhancements

- [ ] Description is under 500 tokens (CLAUDE.md optimization)
- [ ] Description has 3-5 "Use when" examples
- [ ] Description includes "NOT for" with alternative skill reference

**✅ Complete example:**
```yaml
description: |
  Analyze CVE impact across the fleet without immediate remediation.

  Use when:
  - "What are the most critical vulnerabilities?"
  - "Show CVEs affecting my systems"
  - "List high-severity CVEs"

  NOT for remediation actions (use remediator agent instead).
```

**❌ Missing anti-patterns:**
```yaml
description: |
  Analyze CVE impact across the fleet.

  Use when:
  - "What are the most critical vulnerabilities?"
  # Missing "NOT for" section
```

---

## Section 11: YAML Frontmatter - Mandatory Fields (model and color)

- [ ] `model` field present (MANDATORY)
- [ ] `model` value is one of: `inherit`, `sonnet`, or `haiku`
- [ ] `color` field present (MANDATORY)
- [ ] `color` value is one of: `cyan`, `green`, `blue`, `yellow`, or `red`

**Model field (MANDATORY):**
```yaml
model: inherit    # Use parent context's model (recommended default)
model: sonnet     # Force Sonnet for complex reasoning
model: haiku      # Force Haiku for simple, fast operations
```

**Color field (MANDATORY) - Standard values only:**
```yaml
color: cyan       # Read-only operations (list, view, get, inventory)
color: green      # Additive operations (create, clone, snapshot-create)
color: blue       # Reversible changes (start, stop, restart, update)
color: yellow     # Destructive but recoverable (snapshot-delete, scale-down)
color: red        # Irreversible/critical (delete, restore, factory-reset)
```

**❌ Invalid color values:**
```yaml
color: purple     # Not a standard value
color: orange     # Not a standard value
color: custom     # Not a standard value
```

---

## Section 12: SKILL.md Header - Standard Format (MANDATORY)

- [ ] First heading is level 1 (`#`)
- [ ] Heading follows standard format: `# /<skill-name> Skill` or `# [Skill Name]`
- [ ] Heading matches the skill name from frontmatter
- [ ] Overview paragraph appears immediately after heading
- [ ] Overview is 1-2 sentences describing what the skill does

**✅ Standard heading formats:**
```markdown
# /vm-create Skill                    # Preferred format (slash prefix)
# VM Create Skill                     # Alternative format (title case)
# PDF Processing Skill                # Alternative format (title case)
```

**❌ Invalid heading formats:**
```markdown
## vm-create                          # Wrong level (##)
# vm-create                           # Missing "Skill" suffix
# Vm-create Skill                     # Wrong capitalization
# Create VM                           # Doesn't match skill name
```

**Complete header example:**
```markdown
---
name: vm-create
description: |
  Create virtual machines...
model: inherit
color: green
---

# /vm-create Skill

Create virtual machines in OpenShift Virtualization using automated instance type resolution.

## Prerequisites
[Content]
```

---

## Section 13: Mandatory Sections - Presence

- [ ] `## Prerequisites` section present
- [ ] `## When to Use This Skill` section present
- [ ] `## Workflow` section present
- [ ] `## Dependencies` section present

## Workflow
[Content]

## Dependencies
[Content]
```

---

## Section 14: Mandatory Sections - Ordering

- [ ] YAML frontmatter appears first
- [ ] `# [Skill Name]` heading appears after frontmatter
- [ ] Overview paragraph appears after heading
- [ ] `## Critical: Human-in-the-Loop Requirements` appears before `## Prerequisites` (if present)
- [ ] `## Prerequisites` appears before `## When to Use This Skill`
- [ ] `## When to Use This Skill` appears before `## Workflow`
- [ ] `## Workflow` appears before `## Dependencies`

**Correct order:**
```markdown
---
[frontmatter]
---

# Skill Name

Overview paragraph.

## Critical: Human-in-the-Loop Requirements
[If applicable]

## Prerequisites
[Content]

## When to Use This Skill
[Content]

## Workflow
[Content]

## Dependencies
[Content]
```

---

## Section 15: Prerequisites Section - Content

- [ ] Lists **Required MCP Servers** with setup links
- [ ] Lists **Required MCP Tools** with descriptions
- [ ] Lists **Environment Variables** (if any)
- [ ] Contains **Verification Steps** subsection
- [ ] Contains **Human Notification Protocol** subsection
- [ ] Contains security warning about credential values

**Complete example:**
```markdown
## Prerequisites

**Required MCP Servers:** `openshift-virtualization` ([setup guide](https://example.com/setup))

**Required MCP Tools:**
- `vm_create` (from openshift-virtualization) - Creates virtual machines
- `resources_get` (from openshift-virtualization) - Retrieves VM status

**Environment Variables:**
- `KUBECONFIG` - Path to Kubernetes configuration file

**Verification Steps:**
1. Check `openshift-virtualization` is configured in `.mcp.json`
2. Verify `KUBECONFIG` environment variable is set (without exposing value)
3. If missing → Proceed to Human Notification Protocol

**Human Notification Protocol:**
When prerequisites fail:
1. Stop execution immediately
2. Report clear error: "❌ Cannot execute vm-create: MCP server not available"
3. Provide setup instructions with links
4. Request user decision: setup/skip/abort
5. Wait for explicit user input

**Security:** Never display actual KUBECONFIG path or credential values.
```

---

## Section 16: Prerequisites Section - Verification Steps

- [ ] Verification includes check for MCP server in `.mcp.json`
- [ ] Verification includes check for environment variables
- [ ] Verification does not expose credential values
- [ ] Defines behavior when prerequisites fail

**✅ Correct verification:**
```bash
# Check if environment variable is set
test -n "$LIGHTSPEED_CLIENT_SECRET"

# Report boolean status only
if [ -n "$LIGHTSPEED_CLIENT_SECRET" ]; then
    echo "✓ LIGHTSPEED_CLIENT_SECRET is set"
else
    echo "✗ LIGHTSPEED_CLIENT_SECRET is not set"
fi
```

**❌ SECURITY VIOLATION - Exposes credentials:**
```bash
echo $LIGHTSPEED_CLIENT_SECRET              # Shows actual secret value
echo "SECRET=$LIGHTSPEED_CLIENT_SECRET"     # Exposes value in output
```

---

## Section 17: Prerequisites Section - Human Notification Protocol

- [ ] Specifies to stop execution immediately on failure
- [ ] Provides clear error message with setup instructions
- [ ] Requests user decision (setup/skip/abort)
- [ ] Waits for explicit user input

**Example protocol:**
```markdown
**Human Notification Protocol:**

When prerequisites fail, the skill MUST:

1. **Stop Execution Immediately** - Do not attempt tool calls

2. **Report Clear Error:**
   ```
   ❌ Cannot execute vm-create: MCP server `openshift-virtualization` is not available

   📋 Setup Instructions:
   1. Add openshift-virtualization to `.mcp.json`
   2. Set environment variable: export KUBECONFIG="/path/to/config"
   3. Restart Claude Code to reload MCP servers

   🔗 Documentation: https://example.com/setup
   ```

3. **Request User Decision:**
   ```
   ❓ How would you like to proceed?

   Options:
   - "setup" - I'll help you configure the MCP server now
   - "skip" - Skip this skill and use alternative approach
   - "abort" - Stop the workflow entirely
   ```

4. **Wait for Explicit User Input** - Do not proceed automatically
```

---

## Section 18: When to Use This Skill Section

- [ ] Contains "Use when" with 3+ specific scenarios
- [ ] Contains "Do NOT use when" with alternatives
- [ ] Every anti-pattern references alternative skill by name

**✅ Complete example:**
```markdown
## When to Use This Skill

Use this skill when:
- "Create a new VM in production namespace"
- "Deploy a Fedora virtual machine"
- "Set up a VM with 4 CPUs and 8GB RAM"
- User mentions "new VM", "create VM", "provision VM"

Do NOT use when:
- Managing existing VMs → Use `vm-lifecycle-manager` skill instead
- Deleting VMs → Use `vm-delete` skill instead
- Cloning VMs → Use `vm-clone` skill instead
- Viewing VM status → Use `vm-inventory` skill instead
```

**❌ Vague anti-patterns:**
```markdown
Do NOT use when:
- User wants other operations    # Too vague, no alternative specified
```

---

## Section 19: Workflow Section - Structure

- [ ] Each step has heading: `### Step N: [Action Name]`
- [ ] Each step specifies **MCP Tool** name with source server
- [ ] Each step specifies **Parameters** with exact format
- [ ] Each step includes **Expected Output** description
- [ ] Each step includes **Error Handling** with 2+ conditions

**Complete workflow step example:**
```markdown
### Step 1: Create Virtual Machine

**MCP Tool:** `vm_create` or `virtualization__vm_create` (from openshift-virtualization)

**Parameters:**
- `namespace`: "production" (namespace where VM will be created)
- `name`: "fedora-web-01" (name of the virtual machine)
- `workload`: "fedora" (OS image: fedora, ubuntu, centos, rhel)
- `size`: "medium" (VM size: small=2CPU/4GB, medium=4CPU/8GB, large=8CPU/16GB)
- `autostart`: true (automatically start VM after creation)

**Expected Output:**
```json
{
  "status": "success",
  "vm_name": "fedora-web-01",
  "namespace": "production",
  "phase": "Provisioning"
}
```

**Error Handling:**
- If namespace not found: Report error and list available namespaces using `namespaces_list` tool
- If name already exists: Suggest alternative names with incremental suffix (fedora-web-02, etc.)
- If quota exceeded: Display current quota usage and recommend cleanup or quota increase
- If invalid workload: List supported OS images (fedora, ubuntu, centos, rhel, opensuse)
```

---

## Section 20: Workflow Section - Tool Parameters

- [ ] Parameters use exact names (not placeholders like `<namespace>`)
- [ ] Parameters include example values
- [ ] Parameters show format specification and constraints
- [ ] Tool names shown in both formats: `tool_name` and `category__tool_name`

**✅ Precise parameters:**
```markdown
**Parameters:**
- `impact`: "7,6" (comma-separated impact levels: 7=Important, 6=Moderate, 5=Low)
- `sort`: "-cvss_score" (use - prefix for descending; valid: "cvss_score", "public_date")
- `limit`: 20 (integer, maximum CVEs to return, range: 1-100)
```

**❌ Vague parameters:**
```markdown
**Parameters:**
- Use the CVE ID              # No parameter name, no format
- severity: Critical          # Wrong parameter name or format
```

---

## Section 21: Document Consultation - Design Principle #1

**When skill consults documentation:**

- [ ] Uses Read tool to load file into context
- [ ] Declares consultation to user with file path
- [ ] Document consultation happens BEFORE tool invocation
- [ ] Does not claim consultation without actually reading

**✅ CORRECT - Actual consultation (reads first, then declares):**
```markdown
### Step 1: Analyze CVE Impact

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [cvss-scoring.md](../../docs/references/cvss-scoring.md) using the Read tool to understand CVSS severity mapping
2. **Output to user**: "I consulted [cvss-scoring.md](../../docs/references/cvss-scoring.md) to understand CVSS severity mapping."

**MCP Tool:** `vulnerability__get_cves` (from lightspeed-mcp)

**Parameters:**
- `impact`: "7,6" (Important and Moderate severity levels)
```

**❌ WRONG - Transparency theater (claims without reading):**
```markdown
### Step 1: Analyze CVE Impact

I consulted cvss-scoring.md to understand severity levels.

**MCP Tool:** `vulnerability__get_cves` (from lightspeed-mcp)
```

**Rationale:**
- **Substance:** Ensures AI actually enriches its context with domain knowledge
- **Transparency:** Users understand the AI's knowledge sources
- **Auditability:** Read tool calls can be tracked in execution logs

---

## Section 22: Dependencies Section - Structure

- [ ] Contains **Required MCP Servers** subsection
- [ ] Contains **Required MCP Tools** subsection
- [ ] Contains **Related Skills** subsection
- [ ] Contains **Reference Documentation** subsection

**Complete dependencies example:**
```markdown
## Dependencies

### Required MCP Servers
- `openshift-virtualization` - OpenShift Virtualization MCP integration
  - Setup: https://example.com/mcp-setup

### Required MCP Tools
- `vm_create` (from openshift-virtualization) - Creates virtual machines
  - Source: https://github.com/example/openshift-virt-mcp
- `resources_get` (from openshift-virtualization) - Retrieves VM status
- `namespaces_list` (from openshift-virtualization) - Lists available namespaces

### Related Skills
- `vm-lifecycle-manager` - Manages VM power state (start, stop, restart)
- `vm-delete` - Removes VMs and associated resources
- `vm-inventory` - Lists and views VM status across namespaces

### Reference Documentation

**Internal Documentation:**
- [VM Creation Guide](../../docs/vm-creation.md) - Detailed VM creation patterns
- [Instance Types](../../docs/instance-types.md) - Available VM sizes and configurations

**Official Red Hat Documentation:**
- [Creating VMs - OpenShift 4.20](https://docs.redhat.com/en/openshift-virtualization/4.20/creating-vms)
- [VM Templates - OpenShift 4.20](https://docs.redhat.com/en/openshift-virtualization/4.20/templates)
```

---

## Section 23: Dependencies Section - MCP Tools

- [ ] Each tool lists name and source server
- [ ] Each tool has brief description of what it does
- [ ] Each tool has link to source (GitHub, docs)

**Example:**
```markdown
### Required MCP Tools
- `vm_create` (from openshift-virtualization) - Creates virtual machines with specified configuration
  - Source: https://github.com/example/openshift-virt-mcp
  - Parameters: namespace, name, workload, size, networks
- `resources_get` (from openshift-virtualization) - Retrieves Kubernetes resource details
  - Source: https://github.com/example/openshift-virt-mcp
  - Parameters: apiVersion, kind, name, namespace
```

---

## Section 24: Human-in-the-Loop - Design Principle #5

**Required for skills that:**
- Create, delete, modify, or restore resources
- Execute playbooks or commands
- Affect multiple systems
- Perform irreversible actions

**Content requirements:**
- [ ] Section `## Critical: Human-in-the-Loop Requirements` present
- [ ] Lists when confirmation is required (numbered steps)
- [ ] Specifies what user must confirm
- [ ] Includes "Never assume approval" statement
- [ ] Specifies confirmation format (yes/no, typed verification)

**Complete example:**
```markdown
## Critical: Human-in-the-Loop Requirements

This skill requires explicit user confirmation at the following steps:

1. **Before VM Creation**
   - Display VM configuration preview:
     ```
     VM Configuration:
     - Name: fedora-web-01
     - Namespace: production
     - OS: Fedora
     - Size: medium (4 CPU, 8GB RAM)
     - Auto-start: true
     ```
   - Ask: "Should I create this VM with the configuration above?"
   - Wait for user confirmation (yes/no)

2. **After Configuration Validation**
   - If quota warnings exist, display quota usage
   - Ask: "Quota is at 80% capacity. Continue with VM creation?"
   - Wait for explicit user approval

3. **On Error Conditions**
   - Report error details and suggested resolution
   - Ask: "How would you like to proceed? (retry/modify/abort)"
   - Wait for explicit user decision

**Never assume approval** - always wait for explicit user confirmation before executing actions.
```

**When NOT required:**
- Read-only skills (list, view, get, inventory)

---

## Section 25: Human-in-the-Loop - Critical Operations

**For destructive operations (delete, restore):**
- [ ] Requires typed confirmation (user must type exact name)
- [ ] Displays preview before action
- [ ] Waits for explicit "yes" or "proceed"

**Example for vm-delete:**
```markdown
## Critical: Human-in-the-Loop Requirements

**CRITICAL SAFETY REQUIREMENT - Typed Confirmation:**

1. **Before VM Deletion**
   - Display VM details to be deleted:
     ```
     VM to be deleted:
     - Name: database-vm-01
     - Namespace: production
     - Status: Running
     - Storage: 100GB PVC will also be deleted
     - This action is IRREVERSIBLE
     ```

2. **Require Typed Confirmation**
   - Ask: "To confirm deletion, type the exact VM name: database-vm-01"
   - Verify user types exact name character-for-character
   - If mismatch: "Name does not match. Deletion cancelled."
   - If match: Proceed with deletion

3. **Final Confirmation**
   - Ask: "Type 'DELETE' to proceed with irreversible deletion."
   - Wait for user to type: DELETE
   - Only proceed if exact match

**Never proceed without explicit typed confirmation of the resource name.**
```

---

## Section 26: Security - Credential Protection - Design Principle #7

- [ ] No environment variable VALUES in output
- [ ] Only reports if variable is set/unset (boolean status)
- [ ] Uses placeholders for sensitive paths
- [ ] No API keys, tokens, secrets, passwords in examples
- [ ] Does not use `echo $VAR` pattern for credentials

**✅ CORRECT - Secure verification:**
```bash
# Check if set (exit code only, no output)
test -n "$LIGHTSPEED_CLIENT_SECRET"

# Report boolean status
if [ -n "$LIGHTSPEED_CLIENT_SECRET" ]; then
    echo "✓ LIGHTSPEED_CLIENT_SECRET is set"
else
    echo "✗ LIGHTSPEED_CLIENT_SECRET is not set"
fi

# Check multiple variables
test -n "$KUBECONFIG" && test -n "$LIGHTSPEED_CLIENT_ID"
```

**✅ User-visible messages:**
```
✓ Environment variable LIGHTSPEED_CLIENT_ID is set
✓ Environment variable LIGHTSPEED_CLIENT_SECRET is set
✓ Environment variable KUBECONFIG is set
```

**❌ SECURITY VIOLATION - Exposes credentials:**
```bash
echo $LIGHTSPEED_CLIENT_SECRET                    # Shows actual secret
echo "SECRET=$LIGHTSPEED_CLIENT_SECRET"           # Exposes in output
export LIGHTSPEED_CLIENT_SECRET=sk-abc123...      # Hardcoded credential
echo "KUBECONFIG=/home/user/.kube/config"         # Exposes actual path
```

**❌ NEVER show:**
```
LIGHTSPEED_CLIENT_SECRET=sk-abc123-xyz789-...
KUBECONFIG=/home/alice/.kube/my-cluster-config
API_KEY=ghp_abc123xyz789...
```

**Rationale:**
Prevents accidental credential exposure in:
- Conversation history
- Log files
- Screenshots shared with support
- Copied output pasted in public forums

---

## Section 27: Content Quality

- [ ] No hardcoded values (uses placeholders)
- [ ] No broken links (all references resolve)
- [ ] No spelling errors
- [ ] Technical terms explained on first use
- [ ] Clear, concise language

**✅ Good placeholders:**
```markdown
- namespace: "<namespace>"
- vm-name: "<vm-name>"
- kubeconfig: "<path-to-kubeconfig>"
```

**❌ Hardcoded values:**
```markdown
- namespace: "production"       # Don't hardcode specific namespaces
- vm-name: "my-vm"              # Use placeholder instead
- kubeconfig: "/home/user/.kube/config"  # Never hardcode paths
```

---

## Section 28: Naming Conventions

- [ ] Skill name uses kebab-case
- [ ] Folder name matches skill name exactly
- [ ] File is named `SKILL.md` (uppercase)
- [ ] No spaces in folder or file names

**✅ Correct:**
```
skills/vm-create/SKILL.md
skills/pdf-processing/SKILL.md
skills/data-analysis/SKILL.md
```

**❌ Incorrect:**
```
skills/VM-Create/skill.md         # Wrong case
skills/vm_create/SKILL.md         # Underscores not allowed
skills/vm create/SKILL.md         # Spaces not allowed
skills/vmCreate/SKILL.md          # camelCase not allowed
```

---

## Section 29: Design Principle #1 - Document Consultation Transparency

- [ ] Actually reads files before claiming consultation
- [ ] Uses Read tool to load files into context
- [ ] Declares consultation transparently to user

**Implementation pattern:**
```markdown
**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [filename.md](path/to/filename.md) using the Read tool to understand [topic]
2. **Output to user**: "I consulted [filename.md](path/to/filename.md) to understand [topic]."
```

**Execution examples:**
- Read `docs/references/cvss-scoring.md` → "I consulted cvss-scoring.md to verify CVSS severity mapping."
- Read `skills/playbook-generator/SKILL.md` → "I consulted playbook-generator skill to understand Ansible generation parameters."

---

## Section 30: Design Principle #2 - Precise Parameter Specification

- [ ] Tool parameters are exact (not vague or generic)
- [ ] Parameters include format specification and examples
- [ ] Parameters enable first-attempt success without trial-and-error

**✅ Precise specification:**
```markdown
**Parameters:**
- `impact`: "7,6" (string with comma-separated impact levels: 7=Important, 6=Moderate, 5=Low)
- `sort`: "-cvss_score" (use - prefix for descending; valid fields: "cvss_score", "public_date")
- `limit`: 20 (integer, maximum CVEs to return, range: 1-100)
- `published_after`: "2024-01-01" (ISO date format: YYYY-MM-DD)
```

**❌ Vague specification:**
```markdown
**Parameters:**
- Use the CVE ID
- Set severity to high
- Sort by score
```

**Rationale:**
- **Precision:** Exact names and formats prevent tool errors
- **Examples:** Value examples show correct usage
- **Determinism:** First-attempt success reduces wasted cycles

---

## Section 31: Design Principle #3 - Concise Description

- [ ] YAML frontmatter description is under 500 tokens
- [ ] Description focuses on "when to use" scenarios
- [ ] Implementation details deferred to skill body (not in frontmatter)

**✅ Concise frontmatter:**
```yaml
description: |
  Analyze CVE impact across the fleet without immediate remediation.

  Use when:
  - "What are the most critical vulnerabilities?"
  - "Show CVEs affecting my systems"
  - "List high-severity CVEs"

  NOT for remediation actions (use remediator agent instead).
```

**❌ Too detailed in frontmatter:**
```yaml
description: |
  This skill uses the lightspeed-mcp server to query CVEs from Red Hat Insights.
  It first reads the cvss-scoring.md documentation, then calls get_cves with
  impact levels 7 and 6, sorts by CVSS score descending, and formats the output
  as a table. The skill also checks system inventory...
  # [500+ tokens of implementation details]
```

**Rationale:** Minimizes token usage when all skill descriptions are loaded at agent initialization.

---

## Section 32: Design Principle #4 - Dependencies Declared

- [ ] All skill dependencies listed
- [ ] All MCP tools listed with source servers
- [ ] All MCP servers listed with setup links
- [ ] All reference documentation listed

**Complete dependencies section:**
```markdown
## Dependencies

### Required MCP Servers
- `lightspeed-mcp` - Red Hat Lightspeed platform
- `ansible-mcp` - Ansible automation execution

### Required MCP Tools
- `vulnerability__get_cves` (from lightspeed-mcp) - List CVEs with filters
- `vulnerability__get_cve` (from lightspeed-mcp) - Get specific CVE details
- `playbook__execute` (from ansible-mcp) - Execute Ansible playbooks

### Related Skills
- `cve-validation` - Validate CVE IDs before querying
- `fleet-inventory` - Identify systems affected by CVEs
- `playbook-generator` - Generate remediation playbooks

### Reference Documentation
- [cvss-scoring.md](docs/references/cvss-scoring.md) - CVSS severity mappings
- [insights-api.md](docs/insights/insights-api.md) - API usage patterns
```

---

## Section 33: Design Principle #5 - Human-in-the-Loop

- [ ] Confirmations required for critical operations
- [ ] User approval required before destructive actions
- [ ] Preview shown before modifications

See Section 23 for complete implementation requirements.

---

## Section 34: Design Principle #6 - Mandatory Sections

- [ ] All required sections are present
- [ ] Sections appear in correct order
- [ ] Section headings use exact format

**Required sections in order:**
1. YAML frontmatter
2. `# [Skill Name]` heading
3. Overview paragraph
4. `## Critical: Human-in-the-Loop Requirements` (if applicable)
5. `## Prerequisites`
6. `## When to Use This Skill`
7. `## Workflow`
8. `## Dependencies`

---

## Section 35: Design Principle #7 - Prerequisites Verified

- [ ] MCP server availability is checked before execution
- [ ] Environment variables are verified without exposing values
- [ ] Human notification protocol defined for prerequisite failures

See Sections 14-16 for complete verification requirements.

---

## Section 36: Single Responsibility

- [ ] Skill does ONE thing well
- [ ] Skill has clear, focused purpose
- [ ] Skill does not overlap with other skills

**✅ Single responsibility:**
- `vm-create` - Only creates VMs
- `vm-delete` - Only deletes VMs
- `vm-inventory` - Only lists/views VMs

**❌ Multiple responsibilities:**
- `vm-manager` - Creates, deletes, lists, starts, stops VMs (too broad, split into separate skills)

---

## Section 37: Skills Over Tools - Design Principle #3

- [ ] Never calls MCP tools directly in skill instructions
- [ ] Always invokes other skills instead of raw tools
- [ ] Delegates to specialized skills appropriately

**✅ Correct - Delegates to skills:**
```markdown
If user wants to view VM status after creation, invoke the `vm-inventory` skill.
If user wants to start the VM, invoke the `vm-lifecycle-manager` skill with action: start.
```

**❌ Wrong - Calls tools directly:**
```markdown
Use the resources_list tool to view VMs.
Call vm_lifecycle with action: start to start the VM.
```

**Key Pattern:** Agents orchestrate skills; skills encapsulate tools. Never call MCP tools directly - always go through skills.

---

## Validation Levels

**Level 1 - agentskills.io Compliance (MANDATORY):**
- Sections 0-9

**Level 2 - Repository Standards (Required to Commit):**
- Sections 0-9 (agentskills.io)
- Sections 10-14, 18-20, 27-28 (Repository core requirements)

**Level 3 - Production Ready (Recommended):**
- All sections 0-37

---

**Last Updated**: 2026-02-26
**Version**: 3.1
**Applies To**: All agentic collections
**Specification Compliance**: agentskills.io v1.0

# End-to-End CVE Remediation Orchestration Skill

Create an orchestration skill that manages a complete, multi-step security vulnerability remediation workflow. The skill must present a planned task list for user approval before starting, invoke specialized sub-skills in a strict sequential order, and require explicit user confirmation at two critical checkpoints before any system changes occur.

## Capabilities

### Upfront planned task list with user approval

Before executing any step, the skill presents a numbered list of all planned tasks to the user and waits for explicit approval ("yes" or "proceed") before starting.

- The skill displays all 7 planned tasks in workflow order before invoking any sub-skill [@test](./tests/test_upfront_task_list.md)
- The skill does NOT invoke any sub-skill until the user responds with approval or "proceed" [@test](./tests/test_no_execution_before_approval.md)

### Sequential sub-skill invocation

Each sub-skill is invoked one at a time using the slash-format invocation standard, and the next step does not begin until the current step returns its result.

- Sub-skills are invoked using the `/skill-name` slash format, not direct MCP tool calls [@test](./tests/test_slash_invocation_format.md)
- The workflow includes invocations for: prerequisite validation, impact analysis, CVE validation, system context, playbook generation, playbook execution, and verification [@test](./tests/test_all_sub_skills_present.md)

### Remediatable gate

After CVE validation, the skill checks whether automated remediation is available. If not available, it explains the situation, suggests alternatives, and asks the user whether to continue before proceeding.

- When remediation is unavailable, the skill offers to continue with a warning rather than silently proceeding or hard-stopping [@test](./tests/test_remediatable_gate.md)

### Remediation plan validation before execution

Before invoking playbook execution, the skill presents a summary, table, and checklist and waits for user confirmation ("yes"/"proceed"/"dry-run only"/"abort").

- The remediation plan is presented with: 1-2 sentence summary, CVE/system/action table, and ordered checklist steps [@test](./tests/test_remediation_plan_format.md)
- Playbook execution is NOT invoked until the user explicitly confirms the plan [@test](./tests/test_execution_gate.md)

## Implementation

[@generates](./skills/cve-remediation-orchestrator/SKILL.md)

## API

```markdown { #api }
## Workflow

### Upfront: Planned Tasks (Before Step 0)
- Present 7-task list in workflow order
- Ask "Proceed with this plan?"
- WAIT for "yes" or "proceed" — do NOT start Step 0 until confirmed

### Step 0: Validate MCP Prerequisites
Execute /mcp-prerequisite-validator

### Step 1: Impact Analysis
Execute /cve-impact-analyzer

### Step 2: Validate CVE (Remediatable Gate)
Execute /cve-validator
- If NOT remediatable: explain → suggest alternatives → "Continue? (yes/no)" → wait

### Step 3: Gather Context
Execute /system-context-gatherer

### Step 4: Generate Playbook
Execute /playbook-generator  [generates only, does NOT execute]

### Remediation Plan — MANDATORY before Step 5
Present: Summary + CVE/Systems/Action table + ordered checklist
Ask confirmation ("yes"/"proceed"/"dry-run only"/"abort") — WAIT

### Step 5: Execute Playbook (with dry-run recommendation)
Execute /playbook-executor  [only after plan confirmed]

### Step 6: Verify (Optional)
Execute /remediation-verifier
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing the rh-sre orchestration skill patterns, sub-skill invocation standards, human-in-the-loop checkpoint conventions, and CVE remediation workflow structure.

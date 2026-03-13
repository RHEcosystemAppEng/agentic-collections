# Skill with Human-in-the-Loop Confirmation

Create a skill that performs a destructive operation on a cloud resource. The skill must include a mandatory human confirmation section that prevents automatic execution without explicit user approval, including a typed confirmation for irreversible actions.

## Capabilities

### HITL section for critical operations

The skill includes a dedicated section for human-in-the-loop requirements that specifies what confirmation is required before executing the operation.

- A skill that deletes a resource includes a "Critical: Human-in-the-Loop Requirements" section [@test](./tests/test_hitl_section_present.md)
- The HITL section specifies displaying a preview of what will happen, asking a confirmation question, and waiting for user response before proceeding [@test](./tests/test_hitl_preview_ask_wait.md)

### Typed confirmation for destructive operations

Irreversible destructive operations require the user to type a specific string to confirm, not just "yes".

- A delete operation asks the user to type the exact resource name or the word "DELETE" before proceeding [@test](./tests/test_typed_confirmation.md)
- A read-only skill (list/view/get) does NOT include a typed confirmation requirement [@test](./tests/test_no_hitl_for_readonly.md)

### Never assume approval

The HITL implementation explicitly states that it will never assume or auto-infer approval.

- The HITL section includes a "Never assume approval" statement or equivalent [@test](./tests/test_never_assume.md)

## Implementation

[@generates](./skills/resource-delete/SKILL.md)

## API

```markdown { #api }
## Critical: Human-in-the-Loop Requirements

**IMPORTANT:** This skill performs irreversible operations. You MUST:

1. **Before [Destructive Action]**
   - Display preview: [description of what will be deleted/changed]
   - Ask: "Should I [action]? This cannot be undone."
   - Wait for confirmation (yes/no)

2. **Typed Confirmation**
   - Ask: "Type the resource name to confirm: <resource-name>"
   - Verify exact match; cancel if mismatch
   - Only proceed on exact match

**Never assume approval** — always wait for explicit confirmation.
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing Design Principle 5 (Human-in-the-Loop Requirements) and skill safety patterns for destructive operations in AI-native agentic packs.

# Human-in-the-Loop Requirements

This document defines mandatory checkpoint behavior for all rh-developer skills.

## Critical Requirements

**IMPORTANT:** All skills require explicit user confirmation at each step. You MUST:

1. **Wait for user confirmation** before executing any actions
2. **Do NOT proceed** to the next step until the user explicitly approves
3. **Present options clearly** (yes/no/modify) and wait for response
4. **Never auto-execute** resource creation, builds, or deployments
5. **Never skip configuration questions** even if user seems to know what they want

If the user says "no" or wants modifications, address their concerns before proceeding.

## Anti-Patterns to Avoid

**CRITICAL - DO NOT DO THIS:**

| Anti-Pattern | Why It's Wrong |
|--------------|----------------|
| User says "yes do X to namespace Y" → Skip config questions | Strategy ≠ Configuration. User chose WHAT, not HOW |
| User seems experienced → Assume they've considered all options | Even experts benefit from checklists |
| User provides multiple answers at once → Skip individual confirmations | Each checkpoint exists for a reason |
| User is in a hurry → Rush through phases | Speed causes mistakes in production |

## When User Provides Multiple Answers

If user says: "yes do helm deployment to test-app namespace"

**DO NOT** skip phases. Instead:

1. Acknowledge: "Great, you've chosen Helm strategy and test-app namespace."
2. Continue: "Let me confirm the configuration details..."
3. Still ask: Environment type, config approach, resources, etc.
4. Get explicit confirmation for each phase

**The user specifying WHAT to deploy does not mean they've decided HOW to configure it.**

## Standard Checkpoint Language

Use this exact pattern after EVERY step/phase:

```markdown
**WAIT for user confirmation before proceeding.** Do NOT continue to the next phase until user explicitly confirms.

- If user says "yes" → Proceed to next phase
- If user says "no" → Ask what they would like to change
- If user says "modify" → Update configuration and show again for confirmation
- If user gives multiple answers at once → Still confirm each remaining checkpoint individually
```

## Mandatory Configuration Questions

Before ANY resource creation, these questions should be asked:

| Question | Why It Matters |
|----------|----------------|
| Environment type (dev/staging/prod) | Affects image tags, resources, replicas |
| Runtime vs build-time config | Affects flexibility and rebuild frequency |
| Resource limits | Prevents OOM, ensures fair scheduling |
| Replicas | Affects availability and cost |

## Include in Your Skill

Add this section after Prerequisites in your SKILL.md:

```markdown
## Critical: Human-in-the-Loop Requirements

See [Human-in-the-Loop Requirements](../docs/human-in-the-loop.md) for mandatory checkpoint behavior.

**Key Rules:**
1. WAIT for explicit user confirmation at each phase
2. Never skip configuration questions, even if user specifies strategy upfront
3. Strategy choice ≠ Configuration approval
```

## Phase Execution Rules

**MANDATORY:** Execute phases in order. Each phase MUST:

1. Display the phase information to the user
2. Ask the specific question for that phase
3. Wait for user response
4. Only then proceed to next phase

**Even if user provides information for multiple phases at once:**
- Acknowledge what they said
- But still display each phase's confirmation prompt
- Get explicit "yes" for each phase before executing

Example:
- User: "yes do helm to test-app namespace"
- AI: "Great, you've chosen Helm strategy and test-app namespace. Let me confirm the configuration details..."
- [Still show Configuration Review phase]
- [Still ask environment type, config approach, etc.]

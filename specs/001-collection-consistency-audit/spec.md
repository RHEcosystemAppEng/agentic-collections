# Feature Specification: Collection Consistency Audit

**Feature Branch**: `001-collection-consistency-audit`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Create a \"collection-consistency-audit\" feature for this repository."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Produce a Cross-Collection Consistency Baseline (Priority: P1)

As a maintainer, I can run a structured audit across all listed collections so I can see where metadata, versioning, style, and documentation claims are inconsistent and prioritize fixes by severity.

**Why this priority**: Without a shared baseline, remediation effort is reactive and inconsistent, and teams cannot agree on what is currently broken.

**Independent Test**: Can be fully tested by auditing the specified repository artifacts and producing a report that includes findings categorized as blocking, high, medium, and informational.

**Acceptance Scenarios**:

1. **Given** the repository contains multiple pack and documentation artifacts, **When** an audit is executed, **Then** the system produces one baseline report covering version metadata, model metadata, visual/style rules, and claim-to-reality alignment.
2. **Given** at least one inconsistency exists, **When** the report is generated, **Then** each issue includes severity, affected artifacts, and rationale for classification.

---

### User Story 2 - Establish Explicit Consistency Policies (Priority: P2)

As a collection owner, I can rely on a documented rule set defining canonical sources, valid metadata values, style tokens, and exception handling so that future changes follow one policy model.

**Why this priority**: A baseline report alone does not prevent recurring drift; teams need explicit decisions that define expected state and exceptions.

**Independent Test**: Can be fully tested by reviewing the generated policy decision set and confirming each target domain has explicit, unambiguous rules.

**Acceptance Scenarios**:

1. **Given** multiple possible sources for collection versions, **When** policy decisions are documented, **Then** one canonical source-of-truth is defined with precedence and reconciliation expectations.
2. **Given** skill model frontmatter values vary or are undocumented, **When** policy decisions are documented, **Then** valid values and required presence rules are explicitly defined.
3. **Given** visual conventions are spread across multiple docs artifacts, **When** policy decisions are documented, **Then** canonical style tokens and conflict-resolution rules are defined.

---

### User Story 3 - Plan and Enforce Drift Prevention (Priority: P3)

As a repository maintainer, I can apply a remediation plan and validation guardrails so that inconsistencies are fixed in a controlled order and prevented from reappearing.

**Why this priority**: Lasting consistency requires both one-time cleanup and recurring checks that block regressions.

**Independent Test**: Can be fully tested by validating that the output includes prioritized remediation actions and guardrail definitions tied to policy checks.

**Acceptance Scenarios**:

1. **Given** baseline findings and policy decisions exist, **When** remediation planning is completed, **Then** actions are prioritized and mapped to owners or responsibility areas with dependency order.
2. **Given** policy rules are defined, **When** guardrails are proposed, **Then** the plan defines validation checks and CI integration points that detect drift before merge.

---

### Edge Cases

- A collection listed in scope has partial, placeholder, or missing metadata files.
- A pack exists in repository content but is not present in marketplace listing or root documentation.
- Claimed skill, agent, or orchestration counts in README files include generated, deprecated, or non-discoverable artifacts.
- Style declarations conflict between shared docs files and pack-specific presentation assets.
- Existing artifacts use legacy model declarations that no longer match current policy vocabulary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST audit the following collections as one scope set: `rh-sre`, `rh-developer`, `ocp-admin`, `rh-support-engineer`, `rh-virt`, `rh-ai-engineer`, and `rh-automation`.
- **FR-002**: System MUST compare collection version values across `marketplace/rh-agentic-collection.yml`, root `README.md`, each pack `README.md`, and any pack-level plugin metadata file when present.
- **FR-003**: System MUST define and document a canonical source-of-truth policy for collection version values, including precedence when conflicts are detected.
- **FR-004**: System MUST define and document handling rules for placeholder, missing, or non-listed packs (including packs that exist in repository but are absent from marketplace listing).
- **FR-005**: System MUST audit every `skills/*/SKILL.md` frontmatter declaration in scope collections for model metadata consistency.
- **FR-006**: System MUST enforce a documented model metadata policy that defines valid values and required presence rules.
- **FR-007**: System MUST align repository documentation and validation behavior with the enforced model metadata policy.
- **FR-008**: System MUST audit visual/style consistency for collection presentation using `docs/styles.css`, `docs/app.js`, `docs/icons.json`, `docs/plugins.json`, and `docs/mcp.json`.
- **FR-009**: System MUST define canonical style tokens for iconography, color usage, and size conventions used in docs site and pack presentation artifacts.
- **FR-010**: System MUST identify and flag hardcoded or conflicting style values that violate canonical tokens.
- **FR-011**: System MUST audit README claims for skill counts, orchestration wording, and agent references against repository reality.
- **FR-012**: System MUST produce a baseline consistency report that classifies findings as blocking, high, medium, or informational.
- **FR-013**: System MUST produce a policy decision set that captures adopted metadata and style consistency rules.
- **FR-014**: System MUST produce a remediation plan that includes prioritized actions and validation/CI guardrail recommendations to prevent future drift.

### Key Entities *(include if feature involves data)*

- **Collection Scope Entry**: Represents one target collection and its expected presence across marketplace, documentation, and pack artifacts.
- **Consistency Finding**: Represents a detected mismatch, missing value, or policy violation with severity, rationale, and affected artifacts.
- **Policy Decision**: Represents an approved rule (version precedence, valid model values, style token definitions, exception handling) that determines compliant state.
- **Claim Assertion**: Represents a human-readable claim in documentation (counts, references, wording) that must be reconciled against discovered repository facts.
- **Remediation Action**: Represents a prioritized fix task tied to one or more findings and policy decisions, including guardrail follow-up expectations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of in-scope collections receive coverage in a single baseline report with at least one explicit status per audit domain (version, model metadata, style, claim-to-reality).
- **SC-002**: 100% of detected inconsistencies are severity-labeled and include enough context for maintainers to reproduce and verify the issue.
- **SC-003**: 100% of required policy areas (version source-of-truth, model metadata rules, style token rules, claim validation rules) are documented with explicit pass/fail expectations.
- **SC-004**: At least 90% of blocking and high-severity findings have an assigned remediation action in the initial plan.
- **SC-005**: Drift-prevention guardrails are defined such that every policy area has at least one pre-merge validation check proposal.

## Assumptions

- Repository maintainers can access and inspect all in-scope collection artifacts during the audit.
- Existing documentation and metadata files are considered authoritative inputs unless superseded by newly adopted canonical policy decisions.
- Collections with incomplete assets are still included in the audit and reported as findings rather than excluded from scope.
- The initial remediation plan may phase implementation over multiple pull requests while still defining complete guardrail intent.

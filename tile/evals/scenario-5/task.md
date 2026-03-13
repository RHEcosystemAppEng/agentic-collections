# CVE Impact Analysis Skill

Create a skill that analyzes the impact of a known security vulnerability on an infrastructure fleet. The skill must follow a multi-step workflow that validates prerequisites, retrieves vulnerability data, identifies affected systems, classifies them by environment, and produces a risk assessment.

## Capabilities

### MCP prerequisite validation step

Before querying vulnerability data, the skill invokes a prerequisite validator sub-skill and handles each possible outcome (passed, partial, failed).

- The workflow begins with a step that invokes the MCP prerequisite validator and stops if validation fails [@test](./tests/test_prereq_validation.md)
- The validation step handles three outcomes: PASSED (continue), PARTIAL (warn and ask), FAILED (stop with setup instructions) [@test](./tests/test_validation_outcomes.md)

### Vulnerability data retrieval with correct parameters

The skill retrieves specific vulnerability details using the correct MCP tool and parameters.

- The CVE detail retrieval step specifies the CVE identifier in the format `"CVE-YYYY-NNNNN"` and requests full metadata [@test](./tests/test_cve_id_format.md)
- The affected systems retrieval uses the correct parameter name for the unique system identifier (not a generic `id` field) [@test](./tests/test_system_uuid_param.md)

### Risk assessment output format

The skill produces a structured risk assessment summary with overall risk level, contributing factors, and a prioritized recommendation.

- The output includes an "Overall Risk Level" (Critical/High/Medium/Low) field [@test](./tests/test_risk_level_field.md)
- The output includes a priority tier (P0/P1/P2) with time-based remediation guidance [@test](./tests/test_priority_tier.md)

## Implementation

[@generates](./skills/vuln-impact/SKILL.md)

## API

```markdown { #api }
## Workflow

### Step 0: Validate MCP Prerequisites
**Action**: Execute the /<validator-skill>

### Step 1: Select Analysis Flow
Choose account-level or system-level flow based on user request scope.

### Step 2: Retrieve CVE Details
**MCP Tool**: `get_cve` (from lightspeed-mcp)
**Parameters**:
- `cve_id`: "CVE-YYYY-NNNNN"
- `include_details`: true

### Step 3: Identify Affected Systems
**MCP Tool**: `get_cve_systems` (from lightspeed-mcp)
**Parameters**:
- `cve_id`: "CVE-YYYY-NNNNN"
- `include_patched`: false

### Step 4: System Classification
Classify by environment (production/staging/development) and type.

### Step 5: Risk Assessment
Output:
- Overall Risk Level: Critical/High/Medium/Low
- Priority: P0 (24h) / P1 (7d) / P2 (30d)
```

## Dependencies { .dependencies }

### agentic-collections 0.1.0 { .dependency }

Agentic collections framework providing the rh-sre CVE impact analysis patterns, lightspeed-mcp tool conventions, and risk assessment workflow structure for security-focused agentic skills.

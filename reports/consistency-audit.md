# Consistency Audit Report

- Generated: `2026-04-16T13:11:01.180415+00:00`
- Branch: `001-collection-consistency-audit`
- Total packs: `7`
- Total findings: `2`

## Severity Summary

- blocking: `0`
- high: `1`
- medium: `0`
- informational: `1`

## Matrix

| Pack | Registration | Version | Model | Claims | Style | Overall |
|---|---|---|---|---|---|---|
| rh-sre | registered | pass | pass | pass | warn | none |
| rh-developer | registered | pass | pass | pass | warn | none |
| ocp-admin | registered | pass | pass | pass | warn | none |
| rh-support-engineer | excluded-by-policy | pass | pass | pass | warn | informational |
| rh-virt | registered | pass | pass | pass | warn | none |
| rh-ai-engineer | registered | pass | pass | pass | warn | none |
| rh-automation | registered | pass | pass | pass | warn | none |

## Findings

- [informational] `VER-001` Pack 'rh-support-engineer' is not listed in marketplace modules (marketplace/rh-agentic-collection.yml)
- [high] `VIS-003` Documentation site data file is missing or has not yet been generated (docs/data.json)
